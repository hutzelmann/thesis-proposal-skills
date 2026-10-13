"""Text-only calls to the official `claude` binary on the operator's subscription.

The dev runner's rubric judge (`harness/claude_runner.py --judge/--rejudge`) is
one single-turn text call per criterion through the unmodified host CLI, under
the subscription login. Nothing here handles a token: the host reads its own
login, and the one credential the child may inherit — the subscription's
long-lived `CLAUDE_CODE_OAUTH_TOKEN` — is passed through by name, unread. The
child and its `auth status` preflight run in the isolated configuration, with
the environment `host_login.allowlisted_env` builds for every isolated Claude
child (testing-harness spec: Isolated child environment): no second allowlist.
A login that no longer serves is named with the one remedy for the login the
run linked (`host_login.login_remedy`): the harness login command, `/login`
under the operator's opt-in, or a new long-lived token. The stream's billing
checks (`billing_problem`, `billing_signals`, `rate_refusal`) live in `routing`,
which the rig shares, and are re-exported here for the dev runner. The stream
readers both instruments share (`served_model`, `host_cli_version`,
`output_tokens`) live there too.

The call fails closed (testing-harness spec: Subscription text roles). A stream
that shows an error, no output, no notional cost, billing other than the
subscription, overage, a refused or unknown rate-limit status, no rate-limit
report or overage flag at all, or a model other than the requested one raises
`SubscriptionUnavailable`: the criterion is untested, never a failing grade,
and no later call is made.

Everything above the async section is pure and L0-tested against synthetic
streams (`tests/unit/data/claude_cli_streams/`); the async section spawns the
child, bounded by a process-wide limiter and a time limit at which the child
is asked to terminate and killed only after the grace.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path

import anyio
import host_login
from host_login import LONG_LIVED_TOKEN, LoginSource, login_remedy, relogin
from l2_rubrics import read_grade
from routing import (
    billing_problem,
    error_result_reason,
    host_cli_version,
    model_usage,
    output_tokens,
    rate_limit_infos,
    result_event,
    version_label,
)
from routing import billing_signals as billing_signals  # re-exported for the dev runner
from routing import rate_refusal as rate_refusal  # re-exported for the dev runner
from support import EFFORT_LEVELS

CLI = "claude"
CONCURRENCY = 4
CALL_TIMEOUT_S = 300.0  # judgment: a medium-effort grade of a full draft took well under this
AUTH_TIMEOUT_S = 30.0
# one fixed directory, never written into: it keeps the host's injected
# environment block stable between runs and outside every measured workspace
WORKDIR = Path(tempfile.gettempdir()) / "thesis-proposal-devjudge"

# module-level, so every child process in this process shares the bound; anyio 4
# creates the backend limiter lazily on first use inside an event loop
LIMITER = anyio.CapacityLimiter(CONCURRENCY)


class SubscriptionUnavailable(Exception):
    """The subscription could not serve the call: untested, never a FAIL.
    `billing` carries the reason when the stream showed billing other than the
    subscription, so the dev runner can stop a smoke sequence on it."""

    def __init__(self, reason: str, billing: str | None = None):
        super().__init__(reason)
        self.reason = reason
        self.billing = billing


@dataclass(frozen=True)
class RateLimit:
    status: str
    window: str | None
    utilization: float | None


@dataclass(frozen=True)
class JudgeCall:
    text: str
    model: str
    cli_version: str | None
    effort: str
    thinking_tokens: int
    notional_usd: float
    rate_limit: RateLimit


@dataclass(frozen=True)
class Criterion:
    name: str
    prompt: str


@dataclass(frozen=True)
class Grade:
    """One criterion's outcome: `passed` is None when it is untested."""

    name: str
    passed: bool | None
    reason: str
    call: JudgeCall | None = None


@dataclass(frozen=True)
class JudgeRun:
    grades: tuple[Grade, ...]
    spent: float
    projection: float | None = None
    billing: str | None = None


# ---------- pure parts ---------------------------------------------------------


def build_command(model: str, effort: str, system_prompt: str) -> list[str]:
    """The judge invocation (design D2). The prompt goes on stdin, never into
    argv; `--bare` is never passed, because it bypasses the subscription login."""
    if effort not in EFFORT_LEVELS:
        raise ValueError(f"effort {effort!r} is not one of {', '.join(EFFORT_LEVELS)}")
    return [
        CLI, "-p", "--model", model, "--safe-mode", "--system-prompt", system_prompt,
        "--tools", "", "--effort", effort, "--output-format", "stream-json", "--verbose",
        "--no-session-persistence", "--max-turns", "1",
    ]


def parse_events(stdout: str) -> list[dict]:
    """One JSON object per non-empty line; lines that are not JSON are skipped."""
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def rate_limit(events: list[dict]) -> RateLimit | None:
    """The last rate-limit report: its status, window and utilization."""
    infos = rate_limit_infos(events)
    if not infos:
        return None
    last = infos[-1]
    return RateLimit(str(last.get("status")), last.get("rateLimitType"), last.get("utilization"))


def _notional_cost(result: Mapping) -> float | None:
    """The result's notional cost, or None when it is absent or not a number."""
    cost = result.get("total_cost_usd")
    if isinstance(cost, bool) or not isinstance(cost, (int, float)):
        return None
    return float(cost)


def _result_problem(events: list[dict]) -> str | None:
    """Check 2: a result exists, has text, produced output, lists its models,
    and reports its notional cost — without it the cap and the batch
    projection would count the call as $0, so its absence fails closed."""
    result = result_event(events)
    if not result:
        return "claude emitted no result event"
    text = result.get("result")
    if not isinstance(text, str) or not text.strip():
        return "the result carries no text"
    usage = model_usage(events)
    if not usage:
        return "the result carries no per-model usage"
    if sum(output_tokens(u) for u in usage.values()) <= 0:
        return "the result reports zero output tokens"
    if _notional_cost(result) is None:
        return (f"notional cost not reported, the cap cannot be enforced "
                f"(Claude Code {version_label(events)})")
    return None


def _model_problem(events: list[dict], requested: str) -> str | None:
    """Check 5: the requested model, and only it, produced output. An auxiliary
    model listed with zero output tokens is the host's own business."""
    usage = model_usage(events)
    others = [m for m, u in usage.items() if m != requested and output_tokens(u) > 0]
    if others:
        return f"served model {', '.join(others)} differs from the requested {requested}"
    if requested not in usage:
        return f"the requested model {requested} is absent from the usage ({', '.join(usage)})"
    return None


def parse_stream(events: list[dict], requested: str, effort: str,
                 source: LoginSource) -> JudgeCall:
    """The judge call a stream records, or `SubscriptionUnavailable` — checks in
    the order of design D5, so an expired login (which carries no rate-limit
    report) still names the remedy for the login in use (`source`) rather
    than overage. An explicit billing signal beside the error is still named,
    and carried as `billing`, so a judged smoke step stops the later ones."""
    reason = error_result_reason(events)
    if reason:
        signals = billing_signals(events)
        message = login_remedy(reason, source)
        if signals:
            message += f" (not a subscription result: {signals[0]})"
        raise SubscriptionUnavailable(message, billing=signals[0] if signals else None)
    problem = _result_problem(events)
    if problem:
        raise SubscriptionUnavailable(problem)
    billing = billing_problem(events)
    if billing:
        raise SubscriptionUnavailable(billing, billing=billing)
    problem = _model_problem(events, requested)
    if problem:
        raise SubscriptionUnavailable(problem)
    result = result_event(events)
    usage = model_usage(events)[requested]
    return JudgeCall(
        text=result["result"],
        model=requested,
        cli_version=host_cli_version(events),
        effort=effort,
        thinking_tokens=int(usage.get("thinkingTokens") or 0),
        notional_usd=_notional_cost(result) or 0.0,  # check 2 ensured a number
        rate_limit=rate_limit(events),  # type: ignore[arg-type]  # check 4 ensured one
    )


def check_auth_status(status: Mapping, environ: Mapping[str, str],
                      source: LoginSource) -> None:
    """Refuse anything but the subscription login, from `claude auth status
    --json`, naming the one remedy for the login in use (`source`). Only
    `loggedIn`, `authMethod` and `apiProvider` are read; the account's email
    and organization never reach a message."""
    if not status.get("loggedIn"):
        raise SubscriptionUnavailable(f"the host is not logged in: {relogin(source)}")
    method = status.get("authMethod")
    subscription = method == "claude.ai" or (
        method == "oauth_token" and bool(environ.get(LONG_LIVED_TOKEN)))
    if not subscription:
        raise SubscriptionUnavailable(
            f"the host is logged in by {method!r}, not the subscription login (the remedy "
            f"is never an API key): {relogin(source)}")
    provider = status.get("apiProvider")
    if provider != "firstParty":
        raise SubscriptionUnavailable(
            f"the host routes calls through {provider!r}, not Anthropic's own API: unset the "
            f"provider switch, then {relogin(source)}")


def workdir() -> Path:
    """The fixed working directory, created on first use."""
    WORKDIR.mkdir(parents=True, exist_ok=True)
    return WORKDIR


# ---------- async parts ----------------------------------------------------------


async def _drain(stream, sink: list[bytes]) -> None:
    async for chunk in stream:
        sink.append(chunk)


async def _feed(stdin, text: str) -> None:
    """Write the prompt and close stdin. A child that exits without reading it
    (a login failure at start-up) breaks the pipe; its own output says why."""
    try:
        if text:
            await stdin.send(text.encode("utf-8"))
        await stdin.aclose()
    except (anyio.BrokenResourceError, anyio.ClosedResourceError, BrokenPipeError):
        pass


async def _stop(process) -> None:
    """Ask the child to terminate, give it the grace, then kill it, and reap
    it — shielded, so a cancellation cannot leave it running."""
    with anyio.CancelScope(shield=True):
        with suppress(ProcessLookupError):
            process.terminate()
        with anyio.move_on_after(host_login.TERM_GRACE_S):
            await process.wait()
        if process.returncode is None:
            with suppress(ProcessLookupError):
                process.kill()
            await process.wait()


async def run_child(command: Sequence[str], stdin_text: str, env: Mapping[str, str],
                    cwd: Path, timeout: float) -> tuple[int, str, str]:
    """Run one child to completion: write `stdin_text`, read both streams. On
    the time limit, or on cancellation, the child is first asked to terminate
    and killed only after the grace, then reaped (testing-harness spec:
    Harness-owned host logins).

    The process is closed on every path, after it is reaped, so its pipes
    are closed here rather than left to the garbage collector. A stopped
    child's reads can still be pending when the event loop closes — on Windows
    after a plain termination, anywhere while a grandchild holds the pipes —
    and an unclosed pipe then outlives the loop as an open descriptor and an
    "unclosed transport" ResourceWarning (Windows CI run 38388692453)."""
    process = await anyio.open_process(
        list(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=cwd, env=dict(env))
    out: list[bytes] = []
    err: list[bytes] = []
    async with process:
        try:
            with anyio.fail_after(timeout):
                async with anyio.create_task_group() as tg:
                    tg.start_soon(_drain, process.stdout, out)
                    tg.start_soon(_drain, process.stderr, err)
                    await _feed(process.stdin, stdin_text)
                await process.wait()
        except TimeoutError:
            raise SubscriptionUnavailable(
                f"the call timed out after {timeout:g}s; the child was stopped") from None
        finally:
            if process.returncode is None:
                await _stop(process)
    return (process.returncode or 0, b"".join(out).decode("utf-8", "replace"),
            b"".join(err).decode("utf-8", "replace"))


async def call(prompt: str, *, model: str, effort: str, system_prompt: str,
               config: Path, source: LoginSource, timeout: float = CALL_TIMEOUT_S,
               environ: Mapping[str, str] | None = None) -> JudgeCall:
    """One single-turn text call on the subscription, bounded by `LIMITER`,
    in the isolated configuration `config` and its allowlisted environment."""
    command = build_command(model, effort, system_prompt)
    env = host_login.allowlisted_env(host_login.CLAUDE, config, environ)
    async with LIMITER:
        code, stdout, stderr = await run_child(command, prompt, env, workdir(), timeout)
    events = parse_events(stdout)
    if code != 0 and not result_event(events):
        raise SubscriptionUnavailable(
            login_remedy(f"claude failed: {stderr.strip()[-800:] or 'no stderr'}", source))
    return parse_stream(events, model, effort, source)


async def preflight(config: Path, source: LoginSource,
                    environ: Mapping[str, str] | None = None) -> None:
    """Confirm the subscription login before the first call: `claude auth
    status --json` under the judge's own environment and config directory.
    Its output carries account details, so it is parsed, never printed."""
    environ = os.environ if environ is None else environ
    env = host_login.allowlisted_env(host_login.CLAUDE, config, environ)
    code, stdout, _ = await run_child([CLI, "auth", "status", "--json"], "", env, workdir(),
                                      AUTH_TIMEOUT_S)
    try:
        status = json.loads(stdout)
    except ValueError:
        raise SubscriptionUnavailable(
            f"`claude auth status` reported no login state (exit {code}): "
            f"{relogin(source)}") from None
    check_auth_status(status if isinstance(status, dict) else {}, environ, source)


@dataclass
class _Session:
    """Mutable state of one judge invocation: the cap and why calls stopped."""

    cap: float
    spent: float = 0.0
    stop: str | None = None
    billing: str | None = None


async def _grade_one(criterion: Criterion, session: _Session, options: dict) -> Grade:
    if session.stop:
        return Grade(criterion.name, None, f"not judged: {session.stop}")
    if session.spent >= session.cap:
        session.stop = (f"notional cap ${session.cap:.2f} reached "
                        f"(${session.spent:.4f} spent)")
        return Grade(criterion.name, None, f"not judged: {session.stop}")
    try:
        result = await call(criterion.prompt, **options)
    except SubscriptionUnavailable as exc:
        session.stop = f"an earlier judge call was unavailable: {exc.reason}"
        session.billing = session.billing or exc.billing
        return Grade(criterion.name, None, exc.reason)
    session.spent += result.notional_usd
    grade = read_grade(result.text)
    if grade is None:
        session.stop = "an earlier judge response carried no GRADE line"
        return Grade(criterion.name, None, "the judge's response carries no GRADE line "
                     f"(…{result.text[-200:]})", result)
    return Grade(criterion.name, grade, result.text[-400:], result)


def _projection_stop(session: _Session, first: Grade, total: int,
                     notify: Callable[[str], None]) -> float | None:
    """After the warm-up: project the batch from its measured cost, print it,
    and stop the batch when it would exceed the cap."""
    if first.call is None or session.stop:
        return None
    projected = first.call.notional_usd * total
    notify(f"notional projection: {total} judge call(s) × ${first.call.notional_usd:.4f} "
           f"≈ ${projected:.2f} (cap ${session.cap:.2f})")
    if projected > session.cap:
        session.stop = (f"projected notional ${projected:.2f} for {total} calls exceeds "
                        f"the cap ${session.cap:.2f}")
    return projected


async def judge_all(criteria: Sequence[Criterion], *, model: str, effort: str,
                    system_prompt: str, config: Path, source: LoginSource, cap: float,
                    projection: bool = False, timeout: float = CALL_TIMEOUT_S,
                    environ: Mapping[str, str] | None = None,
                    notify: Callable[[str], None] = print) -> JudgeRun:
    """Grade every criterion: preflight, then the first call alone — it is the
    warm-up, during which the isolated config's `keep_login` writes back a due
    refresh before any fan-out — then at most `CONCURRENCY` at a time. The
    first unavailable call, a missing grade line, the notional cap and (with
    `projection`) an over-cap batch projection each stop further calls; the
    criteria left over are untested, in input order. `source` is the login
    the configuration links, which picks the remedy a login failure names."""
    if not criteria:
        return JudgeRun((), 0.0)
    try:
        await preflight(config, source, environ)
    except SubscriptionUnavailable as exc:
        return JudgeRun(tuple(Grade(c.name, None, exc.reason) for c in criteria), 0.0)
    session = _Session(cap)
    options = {"model": model, "effort": effort, "system_prompt": system_prompt,
               "config": config, "source": source, "timeout": timeout, "environ": environ}
    grades: list[Grade | None] = [None] * len(criteria)
    grades[0] = await _grade_one(criteria[0], session, options)
    projected = (_projection_stop(session, grades[0], len(criteria), notify)
                 if projection else None)
    pending = iter(range(1, len(criteria)))

    async def worker() -> None:
        for index in pending:  # shared: each index is taken by exactly one worker
            grades[index] = await _grade_one(criteria[index], session, options)

    async with anyio.create_task_group() as tg:
        for _ in range(min(CONCURRENCY, len(criteria) - 1)):
            tg.start_soon(worker)
    return JudgeRun(tuple(g for g in grades if g is not None), session.spent, projected,
                    session.billing)
