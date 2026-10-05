"""Text-only calls to the official `claude` binary on the operator's subscription.

The dev runner's rubric judge (`harness/claude_runner.py --judge/--rejudge`) is
one single-turn text call per criterion through the unmodified host CLI, under
the subscription login. Nothing here handles a token: the host reads its own
login, and the one credential the child may inherit — the subscription's
long-lived `CLAUDE_CODE_OAUTH_TOKEN` — is passed through by name, unread.

The call fails closed (testing-harness spec: Subscription text roles). A stream
that shows an error, no output, no notional cost, billing other than the
subscription, overage, a refused or unknown rate-limit status, no rate-limit
report or overage flag at all, or a model other than the requested one raises
`SubscriptionUnavailable`: the criterion is untested, never a failing grade,
and no later call is made.

Everything above the async section is pure and L0-tested against synthetic
streams (`tests/unit/data/claude_cli_streams/`); the async section spawns the
child, bounded by a process-wide limiter and a time limit that kills it.
"""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

import anyio
from host_login import LONG_LIVED_TOKEN, RELOGIN, login_remedy
from l2_rubrics import read_grade
from routing import error_result_reason, result_event
from support import EFFORT_LEVELS

CLI = "claude"
# rate-limit statuses that mean the call stayed inside the plan: `allowed_warning`
# was recorded at 0.82 weekly utilization (2026-10-04) and is a legitimate state
ALLOWED_RATE_STATUS = ("allowed", "allowed_warning")
CONCURRENCY = 4
CALL_TIMEOUT_S = 300.0  # judgment: a medium-effort grade of a full draft took well under this
AUTH_TIMEOUT_S = 30.0
# one fixed directory, never written into: it keeps the host's injected
# environment block stable between runs and outside every measured workspace
WORKDIR = Path(tempfile.gettempdir()) / "thesis-proposal-devjudge"

# the judge child's environment is built from this allowlist (design D3)
ENV_KEEP = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "TMPDIR", "CLAUDE_CONFIG_DIR",
            # Windows needs these to start a process at all; they carry no credential
            "SYSTEMROOT", "COMSPEC", "PATHEXT", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
            "TEMP", "TMP")
ENV_KEEP_PREFIXES = ("LC_", "XDG_")

# module-level, so every child process in this process shares the bound; anyio 4
# creates the backend limiter lazily on first use inside an event loop
LIMITER = anyio.CapacityLimiter(CONCURRENCY)


class SubscriptionUnavailable(Exception):
    """The subscription could not serve the call: untested, never a FAIL."""

    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


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


def child_env(environ: Mapping[str, str], config: Path | None = None) -> dict[str, str]:
    """The judge child's environment: the allowlist, the subscription's own
    long-lived token when exported, and the isolated config directory. No API
    key, gateway or provider switch, inherited effort or host-session variable
    reaches the child. `environ` is not modified."""
    env = {
        name: value for name, value in environ.items()
        if name in ENV_KEEP or name.startswith(ENV_KEEP_PREFIXES) or name == LONG_LIVED_TOKEN
    }
    if config is not None:
        env["CLAUDE_CONFIG_DIR"] = str(config)
    return env


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


def init_event(events: list[dict]) -> dict:
    """The host's `system/init` event, or {} when the stream carries none."""
    return next((e for e in events
                 if e.get("type") == "system" and e.get("subtype") == "init"), {})


def model_usage(events: list[dict]) -> dict[str, dict]:
    """The result event's per-model usage, keyed by served model ID."""
    usage = result_event(events).get("modelUsage")
    return usage if isinstance(usage, dict) else {}


def output_tokens(usage: Mapping | None) -> int:
    """One `modelUsage` entry's output tokens; 0 when the entry or count is absent."""
    return int((usage or {}).get("outputTokens") or 0)


def _version_label(events: list[dict]) -> str:
    """The CLI version for a fail-closed reason: a host change is the usual cause."""
    return init_event(events).get("claude_code_version") or "unknown"


def _rate_limit_infos(events: list[dict]) -> list[dict]:
    return [e.get("rate_limit_info") or {} for e in events if e.get("type") == "rate_limit_event"]


def rate_limit(events: list[dict]) -> RateLimit | None:
    """The last rate-limit report: its status, window and utilization."""
    infos = _rate_limit_infos(events)
    if not infos:
        return None
    last = infos[-1]
    return RateLimit(str(last.get("status")), last.get("rateLimitType"), last.get("utilization"))


def _source_problem(events: list[dict]) -> str | None:
    """Check 3: the session billed the subscription login through Anthropic's own API."""
    source = init_event(events).get("apiKeySource")
    if source != "none":
        return (f"the session used API-key source {source!r}, not the subscription login "
                f"({RELOGIN} to restore it — never an API key)")
    for model_id, usage in model_usage(events).items():
        provider = (usage or {}).get("provider")
        if provider != "firstParty":
            return (f"{model_id} was served through provider {provider!r}, not Anthropic's "
                    "own API (firstParty)")
    return None


def rate_refusal(events: list[dict]) -> str | None:
    """A rate-limit report that rules the subscription out: overage in use, or
    a status the plan does not allow. Reads only the reports present, so it
    also classifies a run the host ended with an error — a run refused at the
    limit ends that way and is untested, not a runner failure."""
    for info in _rate_limit_infos(events):
        if info.get("isUsingOverage"):
            return f"overage in use (rate limit {info.get('rateLimitType')})"
        status = info.get("status")
        if status not in ALLOWED_RATE_STATUS:
            return (f"rate-limit status {status!r} is not one of "
                    f"{', '.join(ALLOWED_RATE_STATUS)}")
    return None


def _rate_problem(events: list[dict]) -> str | None:
    """Check 4: a rate-limit report exists, none shows overage, every one
    carries its overage flag, and every status is one the plan allows. Without
    a report or a flag, "$0" would rest on the account setting alone, so their
    absence fails closed too — a renamed field must not read as "no overage"."""
    infos = _rate_limit_infos(events)
    if not infos:
        return (f"rate limit not reported, overage cannot be ruled out "
                f"(Claude Code {_version_label(events)})")
    refusal = rate_refusal(events)
    if refusal:
        return refusal
    if any(not isinstance(info.get("isUsingOverage"), bool) for info in infos):
        return (f"rate limit reported without an overage flag, overage cannot be ruled out "
                f"(Claude Code {_version_label(events)})")
    return None


def billing_problem(events: list[dict]) -> str | None:
    """Why a stream may not count as a subscription result — checks 3 and 4 of
    design D5, shared by the judge and the dev runner's model-under-test run."""
    return _source_problem(events) or _rate_problem(events)


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
                f"(Claude Code {_version_label(events)})")
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


def parse_stream(events: list[dict], requested: str, effort: str) -> JudgeCall:
    """The judge call a stream records, or `SubscriptionUnavailable` — checks in
    the order of design D5, so an expired login (which carries no rate-limit
    report) still names `/login` rather than overage."""
    reason = error_result_reason(events)
    if reason:
        raise SubscriptionUnavailable(login_remedy(reason))
    problem = (_result_problem(events) or billing_problem(events)
               or _model_problem(events, requested))
    if problem:
        raise SubscriptionUnavailable(problem)
    result = result_event(events)
    usage = model_usage(events)[requested]
    return JudgeCall(
        text=result["result"],
        model=requested,
        cli_version=init_event(events).get("claude_code_version"),
        effort=effort,
        thinking_tokens=int(usage.get("thinkingTokens") or 0),
        notional_usd=_notional_cost(result) or 0.0,  # check 2 ensured a number
        rate_limit=rate_limit(events),  # type: ignore[arg-type]  # check 4 ensured one
    )


def check_auth_status(status: Mapping, environ: Mapping[str, str]) -> None:
    """Refuse anything but the subscription login, from `claude auth status
    --json`. Only `loggedIn`, `authMethod` and `apiProvider` are read; the
    account's email and organization never reach a message."""
    if not status.get("loggedIn"):
        raise SubscriptionUnavailable(f"the host is not logged in: {RELOGIN}, then rerun")
    method = status.get("authMethod")
    subscription = method == "claude.ai" or (
        method == "oauth_token" and bool(environ.get(LONG_LIVED_TOKEN)))
    if not subscription:
        raise SubscriptionUnavailable(
            f"the host is logged in by {method!r}, not the subscription login: {RELOGIN} "
            "(the remedy is never an API key)")
    provider = status.get("apiProvider")
    if provider != "firstParty":
        raise SubscriptionUnavailable(
            f"the host routes calls through {provider!r}, not Anthropic's own API: unset the "
            f"provider switch, {RELOGIN}, then rerun")


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


async def run_child(command: Sequence[str], stdin_text: str, env: Mapping[str, str],
                    cwd: Path, timeout: float) -> tuple[int, str, str]:
    """Run one child to completion: write `stdin_text`, read both streams. On
    the time limit, or on cancellation, the child is killed and reaped."""
    process = await anyio.open_process(
        list(command), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        cwd=cwd, env=dict(env))
    out: list[bytes] = []
    err: list[bytes] = []
    try:
        with anyio.fail_after(timeout):
            async with anyio.create_task_group() as tg:
                tg.start_soon(_drain, process.stdout, out)
                tg.start_soon(_drain, process.stderr, err)
                await _feed(process.stdin, stdin_text)
            await process.wait()
    except TimeoutError:
        raise SubscriptionUnavailable(
            f"the call timed out after {timeout:g}s; the child was killed") from None
    finally:
        if process.returncode is None:
            process.kill()
            with anyio.CancelScope(shield=True):
                await process.wait()
    return (process.returncode or 0, b"".join(out).decode("utf-8", "replace"),
            b"".join(err).decode("utf-8", "replace"))


async def call(prompt: str, *, model: str, effort: str, system_prompt: str,
               config: Path | None, timeout: float = CALL_TIMEOUT_S,
               environ: Mapping[str, str] | None = None) -> JudgeCall:
    """One single-turn text call on the subscription, bounded by `LIMITER`."""
    command = build_command(model, effort, system_prompt)
    env = child_env(os.environ if environ is None else environ, config)
    async with LIMITER:
        code, stdout, stderr = await run_child(command, prompt, env, workdir(), timeout)
    events = parse_events(stdout)
    if code != 0 and not result_event(events):
        raise SubscriptionUnavailable(
            login_remedy(f"claude failed: {stderr.strip()[-800:] or 'no stderr'}"))
    return parse_stream(events, model, effort)


async def preflight(config: Path | None, environ: Mapping[str, str] | None = None) -> None:
    """Confirm the subscription login before the first call: `claude auth
    status --json` under the judge's own environment and config directory.
    Its output carries account details, so it is parsed, never printed."""
    environ = os.environ if environ is None else environ
    code, stdout, _ = await run_child([CLI, "auth", "status", "--json"], "",
                                      child_env(environ, config), workdir(), AUTH_TIMEOUT_S)
    try:
        status = json.loads(stdout)
    except ValueError:
        raise SubscriptionUnavailable(
            f"`claude auth status` reported no login state (exit {code}): {RELOGIN}, "
            "then rerun") from None
    check_auth_status(status if isinstance(status, dict) else {}, environ)


@dataclass
class _Session:
    """Mutable state of one judge invocation: the cap and why calls stopped."""

    cap: float
    spent: float = 0.0
    stop: str | None = None


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
                    system_prompt: str, config: Path | None, cap: float,
                    projection: bool = False, timeout: float = CALL_TIMEOUT_S,
                    environ: Mapping[str, str] | None = None,
                    notify: Callable[[str], None] = print) -> JudgeRun:
    """Grade every criterion: preflight, then the first call alone — it is the
    warm-up, during which the isolated config's `keep_login` writes back a due
    refresh before any fan-out — then at most `CONCURRENCY` at a time. The
    first unavailable call, a missing grade line, the notional cap and (with
    `projection`) an over-cap batch projection each stop further calls; the
    criteria left over are untested, in input order."""
    if not criteria:
        return JudgeRun((), 0.0)
    try:
        await preflight(config, environ)
    except SubscriptionUnavailable as exc:
        return JudgeRun(tuple(Grade(c.name, None, exc.reason) for c in criteria), 0.0)
    session = _Session(cap)
    options = {"model": model, "effort": effort, "system_prompt": system_prompt,
               "config": config, "timeout": timeout, "environ": environ}
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
    return JudgeRun(tuple(g for g in grades if g is not None), session.spent, projected)
