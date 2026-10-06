"""The Codex host of the dev runner: invocation, plan billing guard, readers.

A Codex run executes `codex exec --json` in the harness's own Codex login home
(`host_login.CODEX`, `…/thesis-proposal-dev/hosts/codex`), never in the
operator's `~/.codex`, and bills the operator's ChatGPT plan quota and nothing
else (testing-harness spec: Dev-runner host adapters; Codex plan billing
guard). The account keeps money out — the operator holds the Codex credit
balance at zero with automatic reload off — and every check here is the
backstop, failing closed:

- **Environment.** Every Codex child (the run, `login status`, `features list`,
  the quota read) gets `host_login.allowlisted_env(CODEX, …)`: the machine
  plumbing, `CODEX_HOME` set to the harness home, and for a run a scratch
  `HOME` and XDG directories (`run_env`), which hide `~/.agents/skills`, shell
  start-up files and key files. `start` checks the final environment right
  before `Popen` and refuses one that still carries a `CODEX_*`, `OPENAI_*`,
  `OPENROUTER_*` or `*_API_KEY` variable other than `CODEX_HOME`, or whose
  `CODEX_HOME` does not name the harness home (`BillingEnvError`): `exec`
  honours `CODEX_API_KEY` above every stored login, its login restriction
  would then log the harness home out, and another home routes elsewhere.
  The login and the logouts are no such child: they run in
  `host_login.login_env`, which drops the same families by construction.
- **Before the run**, under the run lock (`host_login.run_lock`), the plan
  quota is read through `codex app-server`'s `account/rateLimits/read`, a GET
  of plan usage and not a model call (`read_quota`). The run is refused when
  the read is unavailable or carries no credits state, when any credits exist,
  when the plan is not Plus or Pro (so the free-plan rehearsal's login refuses
  every run), when a window is at 90 % or more, or when a limit is reached
  (`quota_problem`). Then `codex features list` must show nothing enabled
  outside the allowlist (`features_problem`).
- **After the run**, the session record (`$CODEX_HOME/sessions/…`) is reduced
  into `codex.*` records beside the exec events and deleted
  (`capture_rollout`); its provider, plan report, credits, limit state and
  reroutes are checked (`billing_problem`), with the refresh failures and the
  login restriction (`failure_reason`), the isolation (`isolation_problem`:
  a skill outside the workspace, a cloud-skill tool, any MCP call) and the
  served effort (`effort_problem`). Before any of that, right after the
  child, the workspace is checked (`workspace_breach`, design Decision 16,
  shared with Copilot through `workspace_guard`): the sandbox lets the run
  write it, so a link, FIFO, socket, device or hard link left there, or the
  workspace replaced, is removed unfollowed, makes the run untested for
  isolation (`planted_problem`) and records an isolation stop in the home
  (`stop.json`), which refuses every later run before any Codex process
  starts until the operator runs `uv run poe host-login codex --clear-stop`.

Every refusal is untested and uses the one refusal template
(`host_login.refusal`). Codex items map to the canonical tool names
(`codex_tool_calls`: `Bash`, `Skill` for a shell read of a `proposal-*`
`SKILL.md`, `Edit`, `Agent`, `mcp__<server>__<tool>`, `WebSearch`), so the
shared verdicts and the route reader work unchanged. Codex reports no cost:
the summary's cost is absent, with a notional figure only where the roster
prices the same name under OpenAI's provider (`codex_read`).

Imports `host_login`, the shape module `hosts` and `workspace_guard` only —
never `routing` or `claude_cli` — so `routing.tool_calls` can use it without a
cycle. The L0
tests run every pure part over the synthetic streams in
`tests/unit/data/codex_streams/` (derived from the 0.160 sources) and never
start the real `codex`. Verified on Linux only; on macOS there is no
parent-death signal, and Windows lacks the POSIX file lock the runner needs.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import queue
import re
import shutil
import subprocess
import tempfile
import threading
import time
from collections.abc import Callable, Iterable, Mapping, Sequence
from contextlib import ExitStack, suppress
from dataclasses import dataclass
from functools import partial
from pathlib import Path, PurePath

import host_login
import workspace_guard
from host_login import CODEX, MARKER, LoginProblem, LoginSource, login_remedy, refusal
from hosts import RunView, needs_network

# ---------- the command (design Decisions 5 and 6) ---------------------------------------

# Pinned from `codex features list` at CODEX_MIN_VERSION, starting from 0.133's
# default-on set; live check X7 confirms it. Each is passed as `--disable`,
# which rejects an unknown name, so a renamed feature fails the run loudly.
DISABLED_FEATURES = (
    "browser_use_external", "in_app_browser", "plugin_hooks", "plugin_sharing", "tool_suggest",
    "skill_mcp_dependency_install", "workspace_dependencies", "guardian_approval", "goals",
    "fast_mode", "apps", "plugins", "hooks", "memories", "image_generation", "browser_use",
    "computer_use",
)
# the subagent feature, enabled only for scenarios that declare `helpers`
SUBAGENT_FEATURE = "multi_agent"
# what may read enabled; anything else refuses the run until a reviewed change
# updates DISABLED_FEATURES
ALLOWED_FEATURES = ("shell_tool", "unified_exec")
# the host's explicit levels, without `ultra`, which hands work to subagents
EFFORTS = ("low", "medium", "high", "xhigh", "max")
# D4(a), network only where a scenario needs it: `needs_network` and
# NETWORK_SKILLS live in `hosts`, shared with the Copilot host


def allowed_features(scenario: Mapping) -> tuple[str, ...]:
    return ALLOWED_FEATURES + ((SUBAGENT_FEATURE,) if scenario.get("helpers") else ())


def feature_flags(scenario: Mapping) -> list[str]:
    """`--disable` for every pinned feature, and for subagents unless the
    scenario allows helpers. The same flags go to `codex features list`."""
    disabled = [*DISABLED_FEATURES, *(() if scenario.get("helpers") else (SUBAGENT_FEATURE,))]
    return [arg for name in disabled for arg in ("--disable", name)]


def command(scenario: Mapping, ws: Path, model: str, effort: str | None = None) -> list[str]:
    """The `codex exec` invocation: the JSON event stream, strict configuration,
    the workspace as root (it lies outside any git repository), writes confined
    to it, the model verbatim, and the prompt on stdin (`-`). Never
    `--ephemeral` (the session record is the only source of the provider, the
    CLI version, the served effort and the quota), `--ignore-user-config` (the
    home's configuration is the harness's own) or a sandbox bypass. The two
    `-c` keys are harmless if dropped: the effort is checked after the run, and
    a dropped network grant fails a network scenario visibly."""
    argv = [CODEX.binary, "exec", "--json", "--strict-config", "--skip-git-repo-check",
            "-C", str(ws), "-s", "workspace-write", "-m", model]
    if effort:
        argv += ["-c", f'model_reasoning_effort="{effort}"']
    if needs_network(scenario):
        argv += ["-c", "sandbox_workspace_write.network_access=true"]
    return [*argv, *feature_flags(scenario), "-"]


# ---------- refusals ------------------------------------------------------------------


class CodexRefused(Exception):
    """A Codex run that is untested: `message` in the one refusal template,
    `kind` one of `subscription`, `isolation` or `precondition` (the
    `LoginProblem`'s own, set where it was built), `billing` the billing
    cause where that is the reason."""

    def __init__(self, message: str, kind: str, events: list[dict] | None = None,
                 billing: str | None = None):
        super().__init__(message)
        self.message, self.kind, self.events, self.billing = message, kind, events or [], billing

    @classmethod
    def of(cls, problem: LoginProblem, billing: str | None = None) -> CodexRefused:
        return cls(refusal(problem), problem.kind, billing=billing)


class BillingEnvError(CodexRefused):
    """A Codex child's final environment still carries a variable of the
    stripped families, or a `CODEX_HOME` that is not the harness home; names
    the variables, never their values."""

    def __init__(self, names: Sequence[str], wrong_home: bool = False):
        causes = [f"still carries {', '.join(names)}, which could bill the run per token or "
                  "log the harness home out"] if names else []
        causes += ["does not set CODEX_HOME to the harness home, so the child could run in "
                   "another login"] if wrong_home else []
        problem = LoginProblem(f"the Codex child's environment {' and '.join(causes)}",
                               "report it: the harness's environment builder let it through",
                               CODEX.name)
        super().__init__(refusal(problem), "subscription", billing=problem.cause)
        self.names = list(names)


class CodexRunFailed(Exception):
    """A Codex run that ended without a verdict for another reason: a runner failure."""

    def __init__(self, message: str, events: list[dict] | None = None):
        super().__init__(message)
        self.message, self.events = message, events or []


@dataclass(frozen=True)
class RunProblem:
    """Why a finished Codex run has no verdict: untested (with its kind and,
    for billing, the cause the smoke gate reads) or a runner failure."""

    message: str
    untested: bool
    kind: str | None = None
    billing: str | None = None


# ---------- the child environment and the one place a child starts -----------------------

# the names the harness itself sets: the pre-spawn assertion's exact exemption
CODEX_EXEMPT = frozenset(CODEX.child_vars(PurePath("/")))


def run_env(env: Mapping[str, str], scratch: Path) -> dict[str, str]:
    """A run's scratch `HOME` (and `USERPROFILE`) and XDG base directories,
    beside the workspace under the system temporary directory, as the install
    probe has its own `HOME`."""
    return {**env, "HOME": str(scratch), "USERPROFILE": str(scratch),
            "XDG_CONFIG_HOME": str(scratch / ".config"),
            "XDG_CACHE_HOME": str(scratch / ".cache"),
            "XDG_DATA_HOME": str(scratch / ".local" / "share"),
            "XDG_STATE_HOME": str(scratch / ".local" / "state")}


def child_env(home: Path, environ: Mapping[str, str] | None = None,
              scratch: Path | None = None) -> dict[str, str]:
    """The final environment of a Codex child: the one builder's (change 2's
    `allowlisted_env`, with the Codex record), plus the run's scratch homes."""
    env = host_login.allowlisted_env(CODEX, home, environ)
    return run_env(env, scratch) if scratch is not None else env


def ignored_env(environ: Mapping[str, str]) -> list[str]:
    """The inherited variables of the stripped families, by name, for the
    summary's `ignored_env`; their values appear nowhere."""
    return sorted(name for name in environ if CODEX.stripped(name))


def assert_codex_env(env: Mapping[str, str], home: Path) -> None:
    """Refuse a final child environment that carries a stripped-family name
    other than the one the harness sets (`CODEX_HOME`), or whose `CODEX_HOME`
    is missing or names another directory than the harness home `home`."""
    leaks = sorted(name for name in env if CODEX.stripped(name) and name not in CODEX_EXEMPT)
    wrong_home = env.get(CODEX.home_var) != str(home)
    if leaks or wrong_home:
        raise BillingEnvError(leaks, wrong_home)


def start(argv: Sequence[str], *, home: Path, cwd: Path, env: Mapping[str, str],
          stdin: int = subprocess.DEVNULL, pass_fds: Sequence[int] = ()) -> subprocess.Popen:
    """The single place the Codex children the billing guard covers are
    started — the run, `login status`, `features list`, `--version` and the
    quota read: the final environment is checked against the harness home
    immediately before `Popen`; on Linux the child gets the parent-death
    interrupt."""
    assert_codex_env(env, home)
    return subprocess.Popen(list(argv), cwd=cwd, env=dict(env), stdin=stdin,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            encoding="utf-8", errors="replace", pass_fds=tuple(pass_fds),
                            preexec_fn=host_login.child_preexec(CODEX))


def spawn(argv: Sequence[str], *, home: Path, cwd: Path,
          environ: Mapping[str, str] | None = None, scratch: Path | None = None,
          stdin: int = subprocess.DEVNULL, pass_fds: Sequence[int] = ()) -> subprocess.Popen:
    """Start a Codex child in the harness home's environment and leave it running."""
    return start(argv, home=home, cwd=cwd, env=child_env(home, environ, scratch), stdin=stdin,
                 pass_fds=pass_fds)


def run(argv: Sequence[str], *, home: Path, cwd: Path, timeout: float,
        environ: Mapping[str, str] | None = None, scratch: Path | None = None,
        input: str | None = None, pass_fds: Sequence[int] = ()) -> tuple[int, str, str]:
    """Run a Codex child to completion (`host_login.run_host`, stopped with an
    interrupt at `timeout`), started through `start`."""
    return host_login.run_host(CODEX, argv, cwd=cwd, env=child_env(home, environ, scratch),
                               timeout=timeout, input=input, pass_fds=pass_fds,
                               start=partial(start, home=home))


def _cwd(home: Path) -> Path:
    return home if home.is_dir() else Path(tempfile.gettempdir())


def probe(args: Sequence[str], home: Path,
          environ: Mapping[str, str] | None = None) -> tuple[int, str, str]:
    """A short, model-free Codex command — `--version`, `login status`,
    `features list` — in the harness home's environment. The seam the CLI
    tests replace. A binary that cannot start answers 127, a hung one 124."""
    try:
        return run([CODEX.binary, *args], home=home, cwd=_cwd(home),
                   timeout=host_login.CLIENT_TIMEOUT_S, environ=environ)
    except OSError:
        return 127, "", ""
    except subprocess.TimeoutExpired:
        return 124, "", ""


# ---------- the plan quota (design Decision 9) -----------------------------------------------

QUOTA_STOP_PERCENT = 90
QUOTA_TIMEOUT_S = 20
# the personal plans whose included Codex quota this runner is meant to spend;
# a Business or Edu seat may draw on workspace credits, so adding one is a
# reviewed change
ALLOWED_PLANS = ("plus", "pro")
QUOTA_FILE = "quota.json"
CLIENT_INFO = {"name": "thesis-proposal-dev-runner", "title": "thesis-proposal-skills dev runner",
               "version": "1"}
WINDOW_NAMES = {300: "5-hour", 10080: "weekly"}


@dataclass(frozen=True)
class Window:
    used_percent: float | None
    window_minutes: int | None
    resets_at: int | None

    def snapshot(self) -> dict:
        return {"used_percent": self.used_percent, "window_minutes": self.window_minutes,
                "resets_at": self.resets_at}

    @property
    def name(self) -> str:
        minutes = self.window_minutes
        return WINDOW_NAMES.get(minutes or 0, f"{minutes}-minute" if minutes else "unnamed")


@dataclass(frozen=True)
class Credits:
    has_credits: bool
    unlimited: bool
    balance: float | None

    @property
    def present(self) -> bool:
        return self.has_credits or self.unlimited or (self.balance or 0) > 0

    @property
    def detail(self) -> str:
        parts = [f"balance {self.balance:g}" if (self.balance or 0) > 0 else "",
                 "credits available" if self.has_credits else "",
                 "unlimited credits" if self.unlimited else ""]
        return ", ".join(part for part in parts if part) or "none"


@dataclass(frozen=True)
class Quota:
    """One quota report, from the app-server's answer or a session record's
    `rate_limits`: `error` says why the read is unavailable, None when it
    answered; `unrecognised` says why a credits block that is present has
    a shape the guard does not read (then `credits` is None)."""

    error: str | None = None
    primary: Window | None = None
    secondary: Window | None = None
    credits: Credits | None = None
    plan_type: str | None = None
    reached_type: str | None = None
    unrecognised: str | None = None

    def snapshot(self) -> dict:
        """What the harness home keeps: window usage, reset times and the plan
        type — never a token, an email address or an account identifier."""
        return {"primary": self.primary.snapshot() if self.primary else None,
                "secondary": self.secondary.snapshot() if self.secondary else None,
                "plan_type": self.plan_type}


def _pick(data: Mapping, *names: str) -> object:
    return next((data[name] for name in names if name in data), None)


def _number(value: object) -> float | None:
    """A finite number, or a string that parses as one; None otherwise (a
    boolean, `nan`, `12,50`, `$12.50`)."""
    try:
        number = float(value) if value is not None and not isinstance(value, bool) else None
    except (TypeError, ValueError):
        return None
    return number if number is not None and math.isfinite(number) else None


def _integer(value: object) -> int | None:
    number = _number(value)
    return int(number) if number is not None else None


def _window(data: object) -> Window | None:
    """A quota window; one that is present but not an object reads as a
    window without a used percentage, which the guard refuses."""
    if data is None:
        return None
    if not isinstance(data, dict):
        return Window(None, None, None)
    return Window(_number(_pick(data, "used_percent", "usedPercent")),
                  _integer(_pick(data, "window_minutes", "windowDurationMins", "windowMinutes")),
                  _integer(_pick(data, "resets_at", "resetsAt")))


def _credits(data: object) -> tuple[Credits | None, str | None]:
    """The credits block, or why its shape is not recognised (D2(a): strictly
    fail-closed, so a renamed field or a changed format never reads as "no
    credits"): `hasCredits` and `unlimited` must be booleans, and the balance
    absent, null or a number. An absent or null block is no credits state."""
    if data is None:
        return None, None
    if not isinstance(data, dict):
        return None, "the credits state is not an object"
    has, unlimited = _pick(data, "has_credits", "hasCredits"), data.get("unlimited")
    if not (isinstance(has, bool) and isinstance(unlimited, bool)):
        return None, "the credits state carries no boolean hasCredits and unlimited"
    balance = _number(data.get("balance"))
    if data.get("balance") is not None and balance is None:
        return None, "the credits balance is not a number"
    return Credits(has, unlimited, balance), None


def quota_from_limits(limits: object) -> Quota:
    """A rate-limit snapshot in either spelling — the app-server's camel case
    or the session record's snake case — as one `Quota`."""
    if not isinstance(limits, dict):
        return Quota(error="the answer carries no rate limits")
    plan = _pick(limits, "plan_type", "planType")
    reached = _pick(limits, "rate_limit_reached_type", "rateLimitReachedType")
    credits, unrecognised = _credits(limits.get("credits"))
    return Quota(None, _window(limits.get("primary")), _window(limits.get("secondary")),
                 credits, str(plan) if plan else None, str(reached) if reached else None,
                 unrecognised)


def parse_quota(answer: object) -> Quota:
    """The `account/rateLimits/read` answer, preferring the `codex` entry of
    `rateLimitsByLimitId` over `rateLimits`."""
    if not isinstance(answer, dict):
        return Quota(error="the reader gave no answer in time")
    if answer.get("error") is not None:
        error = answer["error"]
        message = error.get("message") if isinstance(error, dict) else error
        return Quota(error=f"the read failed: {message}")
    result = answer.get("result") if isinstance(answer.get("result"), dict) else {}
    by_id = result.get("rateLimitsByLimitId")
    limits = by_id.get("codex") if isinstance(by_id, dict) and by_id.get("codex") else None
    return quota_from_limits(limits or result.get("rateLimits"))


def _when(epoch: int | None) -> str:
    return time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime(epoch)) if epoch else "unknown"


def _percent(window: Window) -> str:
    return f"{window.used_percent:g}%" if window.used_percent is not None else "?%"


QUOTA_UNAVAILABLE_REMEDY = "rerun once `uv run poe host-status codex --quota` reports the quota"
EMPTY_CREDITS = ("empty the Codex credit balance and turn automatic reload off in the ChatGPT "
                 "settings, then rerun")


def _unmeasured(quota: Quota) -> str | None:
    window = next((w for w in (quota.primary, quota.secondary)
                   if w is not None and w.used_percent is None), None)
    return f"the {window.name} window carries no used percentage" if window else None


def _unavailable(quota: Quota) -> LoginProblem | None:
    why = quota.error or (
        "the answer carries no primary quota window" if quota.primary is None else
        _unmeasured(quota) or (
            f"its credits state is not recognised ({quota.unrecognised}), so a credit draw "
            "cannot be ruled out" if quota.unrecognised else
            "the answer carries no credits state, so a credit draw cannot be ruled out"
            if quota.credits is None else None))
    if why is None:
        return None
    return LoginProblem(f"the plan quota read is unavailable: {why}", QUOTA_UNAVAILABLE_REMEDY,
                        CODEX.name)


def _credits_problem(quota: Quota, whose: str = "the ChatGPT account holds") -> LoginProblem | None:
    if quota.credits is None or not quota.credits.present:
        return None
    return LoginProblem(f"{whose} Codex credits ({quota.credits.detail})", EMPTY_CREDITS,
                        CODEX.name)


def _plan_problem(quota: Quota, whose: str = "the harness login's") -> LoginProblem | None:
    if quota.plan_type in ALLOWED_PLANS:
        return None
    return LoginProblem(f"{whose} plan is {quota.plan_type or 'not reported'}, not Plus or Pro",
                        f"log the harness home in with a Plus or Pro account: run "
                        f"`{CODEX.reset_command}`", CODEX.name)


def _window_problem(quota: Quota) -> LoginProblem | None:
    for window in (quota.primary, quota.secondary):
        if window and (window.used_percent or 0) >= QUOTA_STOP_PERCENT:
            return LoginProblem(f"the {window.name} plan window is {_percent(window)} used "
                                f"(resets {_when(window.resets_at)})",
                                "rerun after the window resets", CODEX.name)
    return None


def _reached_problem(quota: Quota) -> LoginProblem | None:
    if not quota.reached_type:
        return None
    return LoginProblem(f"the plan reports a reached limit ({quota.reached_type})",
                        "rerun after the limit resets", CODEX.name)


QUOTA_CHECKS: tuple[Callable[[Quota], LoginProblem | None], ...] = (
    _unavailable, _credits_problem, _plan_problem, _window_problem, _reached_problem)


def quota_problem(quota: Quota) -> LoginProblem | None:
    """The first reason the plan quota cannot serve a run, or None (D2(a):
    strictly fail-closed — an answer without a credits state is unavailable)."""
    return next((problem for check in QUOTA_CHECKS if (problem := check(quota))), None)


def describe(quota: Quota) -> str:
    """One status line for a quota report: plan, windows, credits."""
    if quota.error:
        return f"unavailable ({quota.error})"
    parts = [f"plan {quota.plan_type or 'unreported'}"]
    parts += [f"{w.name} {_percent(w)} used (resets {_when(w.resets_at)})"
              for w in (quota.primary, quota.secondary) if w]
    if quota.credits is not None:
        parts.append(f"credits {quota.credits.detail}")
    if quota.unrecognised:
        parts.append(f"credits unrecognised ({quota.unrecognised})")
    return "; ".join(parts)


def last_quota(home: Path) -> str:
    """The snapshot the home keeps, described; `none` before the first run."""
    try:
        snapshot = json.loads((home / QUOTA_FILE).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return "none"
    return describe(quota_from_limits(snapshot))


def _pump(stream: Iterable[str], lines: queue.Queue) -> None:
    for line in stream:
        lines.put(line)
    lines.put(None)


def _await(lines: queue.Queue, ident: int, deadline: float) -> dict | None:
    """The response with `ident`, skipping notifications, before `deadline`."""
    while (remaining := deadline - time.monotonic()) > 0:
        try:
            line = lines.get(timeout=remaining)
        except queue.Empty:
            return None
        if line is None:
            return None
        with suppress(ValueError):
            message = json.loads(line)
            if isinstance(message, dict) and message.get("id") == ident:
                return message
    return None


def _send(proc: subprocess.Popen, message: dict) -> None:
    proc.stdin.write(json.dumps(message) + "\n")  # type: ignore[union-attr]
    proc.stdin.flush()  # type: ignore[union-attr]


def _exchange(proc: subprocess.Popen) -> dict | None:
    """`initialize`, the `initialized` notification, then the read with id 1,
    within QUOTA_TIMEOUT_S."""
    lines: queue.Queue = queue.Queue()
    threading.Thread(target=_pump, args=(proc.stdout, lines), daemon=True).start()
    deadline = time.monotonic() + QUOTA_TIMEOUT_S
    try:
        _send(proc, {"method": "initialize", "id": 0, "params": {"clientInfo": CLIENT_INFO}})
        if _await(lines, 0, deadline) is None:
            return None
        _send(proc, {"method": "initialized"})
        _send(proc, {"method": "account/rateLimits/read", "id": 1})
    except OSError:
        return None
    return _await(lines, 1, deadline)


def read_quota(home: Path, environ: Mapping[str, str] | None = None) -> Quota:
    """The plan quota through `codex app-server` (JSONL over stdio), which
    GETs plan usage and makes no model call. The child is stopped with an
    interrupt and the grace afterwards, answered or not. Callers hold the run
    lock."""
    try:
        proc = spawn([CODEX.binary, "app-server"], home=home, cwd=_cwd(home), environ=environ,
                     stdin=subprocess.PIPE)
    except OSError as exc:
        return Quota(error=f"the reader could not start ({exc.strerror or exc})")
    try:
        return parse_quota(_exchange(proc))
    finally:
        host_login.stop_child(proc, CODEX.stop_signal)
        for stream in (proc.stdin, proc.stdout, proc.stderr):
            with suppress(OSError, AttributeError):
                stream.close()  # type: ignore[union-attr]


# ---------- the feature allowlist -------------------------------------------------------------

_ON, _OFF = {"true", "on", "enabled", "yes"}, {"false", "off", "disabled", "no"}


def parse_features(listing: str) -> tuple[dict[str, bool], list[str]]:
    """`codex features list` as (states, unparsed lines): every non-blank line
    must be one `name stage state` row whose state is a known word. Anything
    else is returned as unparsed, so a format change refuses rather than
    hides an enabled feature (fail-closed). Shaped after 0.133's local
    output; X7 confirms the 0.160 format."""
    states, unparsed = {}, []
    for line in listing.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2].lower() in _ON | _OFF:
            states[parts[0]] = parts[2].lower() in _ON
        elif parts:
            unparsed.append(line.strip())
    return states, unparsed


FEATURES_PARSER = "report it: the feature listing does not match the parser"


def features_problem(listing: str, allowed: Sequence[str]) -> LoginProblem | None:
    """Refuse when a line of the listing does not parse, when the listing
    shows no feature state at all, or when anything outside `allowed` reads
    enabled: a precondition of the run."""
    states, unparsed = parse_features(listing)
    if unparsed:
        return LoginProblem(f"`codex features list` printed a line the parser does not read: "
                            f"{unparsed[0]!r}", FEATURES_PARSER, CODEX.name, "precondition")
    if not states:
        return LoginProblem("`codex features list` reported no feature states", FEATURES_PARSER,
                            CODEX.name, "precondition")
    extra = sorted(name for name, enabled in states.items() if enabled and name not in allowed)
    if extra:
        return LoginProblem(f"features outside the allowlist read enabled: {', '.join(extra)}",
                            "report it: the pinned feature list does not match this CLI",
                            CODEX.name, "precondition")
    return None


# ---------- the session record (design Decision 10) -------------------------------------------

SESSIONS = "sessions"
_SKILL_FILE = re.compile(r"\(file: ([^)\n]+?SKILL\.md)\)")
CLOUD_SKILLS = "skills."


def _session(payload: dict) -> list[dict]:
    return [{"type": "codex.session", "id": payload.get("id"),
             "cli_version": payload.get("cli_version"),
             "model_provider": payload.get("model_provider")}]


def _turn_context(payload: dict) -> list[dict]:
    return [{"type": "codex.turn_context", "model": payload.get("model"),
             "effort": payload.get("effort")}]


def _event_msg(payload: dict) -> list[dict]:
    if payload.get("type") == "token_count":
        info = payload.get("info") if isinstance(payload.get("info"), dict) else {}
        return [{"type": "codex.token_count", "usage": info.get("total_token_usage"),
                 "rate_limits": payload.get("rate_limits")}]
    if payload.get("type") == "error":
        return [{"type": "codex.error", "message": payload.get("message")}]
    return []


def _response_item(payload: dict) -> list[dict]:
    if payload.get("type") == "message":
        texts = [block.get("text", "") for block in payload.get("content") or []
                 if isinstance(block, dict)]
        files = [match for text in texts for match in _SKILL_FILE.findall(text)]
        return [{"type": "codex.skills", "files": files}] if files else []
    if payload.get("type") == "function_call":
        name = str(payload.get("name") or "")
        namespace = payload.get("namespace")
        full = f"{namespace}.{name}" if namespace else name
        return [{"type": "codex.tool", "name": full}] if "." in full else []
    return []


_REDUCERS: dict[str, Callable[[dict], list[dict]]] = {
    "session_meta": _session, "turn_context": _turn_context, "event_msg": _event_msg,
    "response_item": _response_item}


def reduce_rollout(lines: Iterable[str]) -> list[dict]:
    """Only the fields the readers use: a kept workspace never holds base
    instructions, environment details or messages from the session record."""
    records = []
    for line in lines:
        with suppress(ValueError):
            record = json.loads(line)
            if isinstance(record, dict) and isinstance(record.get("payload"), dict):
                reducer = _REDUCERS.get(str(record.get("type")))
                records += reducer(record["payload"]) if reducer else []
    return records


def _session_id(path: Path) -> str | None:
    with suppress(OSError, ValueError, StopIteration):
        with path.open(encoding="utf-8") as fh:
            first = json.loads(next(fh))
        return (first.get("payload") or {}).get("id")
    return None


def _session_files(sessions: Path, thread_id: str | None) -> list[Path]:
    """The run's record: by the thread id in its name, else by the id its
    `session_meta` carries (the path pattern is unverified at 0.160)."""
    found = sorted(sessions.glob("**/rollout-*.jsonl"))
    if thread_id is None:
        return found if len(found) == 1 else []
    named = [path for path in found if thread_id in path.name]
    return named or [path for path in found if _session_id(path) == thread_id]


def _write_snapshot(home: Path, records: list[dict]) -> None:
    limits = next((r.get("rate_limits") for r in reversed(records)
                   if r["type"] == "codex.token_count" and r.get("rate_limits")), None)
    if limits is None:
        return
    target = home / QUOTA_FILE
    temporary = target.with_name(f".{QUOTA_FILE}.tmp")
    temporary.write_text(json.dumps(quota_from_limits(limits).snapshot()), encoding="utf-8")
    temporary.replace(target)  # os.replace: atomic


def capture_rollout(home: Path, thread_id: str | None) -> list[dict]:
    """Reduce the run's session record into `codex.*` records, write the quota
    snapshot, and delete the whole `sessions/` subtree. No record: no
    records, and the billing guard reports that plan use cannot be confirmed."""
    sessions = home / SESSIONS
    try:
        records = [record for path in _session_files(sessions, thread_id)
                   for record in reduce_rollout(path.read_text(encoding="utf-8").splitlines())]
        _write_snapshot(home, records)
        return records
    finally:
        shutil.rmtree(sessions, ignore_errors=True)


# ---------- canonical tool calls (design Decision 11) -----------------------------------------

# a reader applied to a proposal-* SKILL.md under .agents/skills, as Codex's
# own invocation heuristic reads it (`core-skills/src/invocation_utils.rs`)
_SKILL_READ = re.compile(r"\b(?:cat|sed|head|tail|less|more|bat|awk|nl)\b[^|;&\n]*?"
                         r"\.agents/skills/(proposal-[a-z-]+)/SKILL\.md")


def _command_calls(item: dict) -> list[tuple[str, dict]]:
    command = item.get("command")
    text = " ".join(map(str, command)) if isinstance(command, list) else str(command or "")
    read = _SKILL_READ.search(text)
    return [*([("Skill", {"skill": read[1]})] if read else []), ("Bash", {"command": text})]


def _collab_calls(item: dict) -> list[tuple[str, dict]]:
    tool = item.get("tool")
    if tool == "spawn_agent":
        return [("Agent", {"prompt": item.get("prompt") or ""})]
    return [(f"collab:{tool}", {})]


ITEM_CALLS: dict[str, Callable[[dict], list[tuple[str, dict]]]] = {
    "command_execution": _command_calls,
    "file_change": lambda item: [("Edit", {"changes": item.get("changes") or []})],
    "collab_tool_call": _collab_calls,
    "mcp_tool_call": lambda item: [(f"mcp__{item.get('server')}__{item.get('tool')}",
                                    item.get("arguments") or {})],
    "web_search": lambda item: [("WebSearch", {"query": item.get("query") or ""})],
}


def codex_tool_calls(events: list[dict]) -> list[tuple[str, dict]]:
    """(canonical tool name, input) per completed Codex item, in order, each
    item once. A Claude stream gives none (its shape is `assistant` events)."""
    calls: list[tuple[str, dict]] = []
    seen: set[str] = set()
    for event in events:
        item = event.get("item") if event.get("type") == "item.completed" else None
        reader = ITEM_CALLS.get(item.get("type")) if isinstance(item, dict) else None
        if reader is None or item.get("id") in seen:
            continue
        if item.get("id") is not None:
            seen.add(item["id"])
        calls += reader(item)
    return calls


# ---------- readers and telemetry (design Decision 12) -------------------------------------------

_REROUTE = re.compile(r"model rerouted: (\S+) -> (\S+)")


@dataclass(frozen=True)
class Rates:
    """$/Mtok for a roster row priced under OpenAI's provider (claude_runner
    reads the registry; this module does not import it)."""

    input_price: float
    cache_read_price: float
    output_price: float


def _last(events: list[dict], kind: str) -> dict:
    return next((e for e in reversed(events) if e.get("type") == kind), {})


def _items(events: list[dict], kind: str) -> list[dict]:
    return [e["item"] for e in events if e.get("type") == "item.completed"
            and isinstance(e.get("item"), dict) and e["item"].get("type") == kind]


def final_text(events: list[dict]) -> str:
    """The chat the verdicts read: the last completed agent message."""
    messages = _items(events, "agent_message")
    text = messages[-1].get("text") if messages else ""
    return text if isinstance(text, str) else ""


def _messages(events: list[dict]) -> list[str]:
    """Every error text a run carries: failed turns, error events and items,
    and the session record's errors."""
    texts = [str((e.get("error") or {}).get("message") or "") for e in events
             if e.get("type") == "turn.failed"]
    texts += [str(e.get("message") or "") for e in events
              if e.get("type") in ("error", "codex.error")]
    texts += [str(item.get("message") or "") for item in _items(events, "error")]
    return [text for text in texts if text]


def rerouted(events: list[dict]) -> tuple[str, str] | None:
    """(requested, served) when the host rerouted the model; only the error
    item counts — `turn_context.model` is the requested model."""
    for text in _messages(events):
        match = _REROUTE.search(text)
        if match:
            return match[1], match[2]
    return None


def harness_record(events: list[dict]) -> dict:
    """The runner's own record: duration, exit status, stderr tail, quota before."""
    return _last(events, "codex.harness")


USAGE_KEYS = ("input_tokens", "cached_input_tokens", "output_tokens", "reasoning_output_tokens",
              "cache_write_input_tokens")


def _usage(events: list[dict]) -> dict[str, int]:
    totals = dict.fromkeys(USAGE_KEYS, 0)
    for event in events:
        usage = event.get("usage") if event.get("type") == "turn.completed" else None
        for key in USAGE_KEYS if isinstance(usage, dict) else ():
            totals[key] += int(usage.get(key) or 0)
    return totals


def _notional(usage: Mapping[str, int], rates: Rates | None) -> float | None:
    if rates is None:
        return None
    uncached = usage["input_tokens"] - usage["cached_input_tokens"]
    return round((uncached * rates.input_price + usage["cached_input_tokens"] *
                  rates.cache_read_price + usage["output_tokens"] * rates.output_price)
                 / 1_000_000, 6)


def _quota_after(events: list[dict]) -> dict | None:
    limits = _last(events, "codex.token_count").get("rate_limits")
    return quota_from_limits(limits).snapshot() if isinstance(limits, dict) else None


def codex_telemetry(events: list[dict], args: argparse.Namespace,
                    rates: Rates | None = None) -> dict:
    """Codex reports no cost: `cost_usd` is None, never zero, and a notional
    figure exists only for a roster-priced name. `tokens_in` is the uncached
    input (`input_tokens` includes the cached part)."""
    usage = _usage(events)
    notional = _notional(usage, rates)
    harness = harness_record(events)
    return {
        "cost_usd": None,
        "notional_usd": notional,
        "notional_basis": "roster" if notional is not None else "unpriced",
        "num_turns": sum(1 for e in events if e.get("type") == "turn.completed"),
        "duration_ms": harness.get("duration_ms"),
        "tokens_in": usage["input_tokens"] - usage["cached_input_tokens"],
        "tokens_out": usage["output_tokens"],
        "tokens_cache_read": usage["cached_input_tokens"],
        "tokens_cache_write": usage["cache_write_input_tokens"],
        "tokens_reasoning": usage["reasoning_output_tokens"],
        "effort_requested": getattr(args, "effort", None),
        "effort_served": _last(events, "codex.turn_context").get("effort"),
        "quota_before": harness.get("quota_before"),
        "quota_after": _quota_after(events),
        "ignored_env": ignored_env(os.environ),
    }


def codex_read(events: list[dict], args: argparse.Namespace,
               rates: Rates | None = None) -> RunView:
    """The Codex host's `RunView`: the last agent message, the requested model
    beside the served one ("unreported" unless a reroute names it), the CLI
    version from the session record, and the telemetry."""
    reroute = rerouted(events)
    return RunView(final_text(events), getattr(args, "model", None),
                   reroute[1] if reroute else "unreported",
                   _last(events, "codex.session").get("cli_version"),
                   codex_telemetry(events, args, rates))


# ---------- failures, the billing guard after the run, isolation, effort --------------------------

_USAGE_LIMIT = re.compile(r"usage limit|hit your limit", re.IGNORECASE)


def failure_reason(events: list[dict], returncode: int, stderr: str) -> RunProblem | None:
    """Why a run ended without a verdict, in this order: a login Codex can no
    longer use (untested, with the Codex harness login's remedy and note), a
    usage limit (untested), a failed turn or a fatal error event (Codex's own
    message), a non-zero exit (the stderr tail), and no completed turn."""
    texts = [*_messages(events), *([stderr.strip()] if stderr.strip() else [])]
    login = next((t for t in texts if CODEX.failure.search(t)), None)
    if login:
        return RunProblem(login_remedy(f"codex failed: {login}", LoginSource.HARNESS, CODEX),
                          True, "subscription")
    limit = next((t for t in texts if _USAGE_LIMIT.search(t)), None)
    if limit:
        return RunProblem(f"untested: codex reported a usage limit: {limit}. Rerun after the "
                          "limit resets", True, "subscription", billing=f"usage limit: {limit}")
    fatal = [str((e.get("error") or {}).get("message") or e.get("message") or "") for e in events
             if e.get("type") in ("turn.failed", "error")]
    if fatal:
        return RunProblem(f"codex failed: {fatal[-1] or 'no message'}", False)
    if returncode != 0:
        return RunProblem(f"codex failed: {stderr.strip()[-800:] or 'no stderr'}", False)
    if not any(e.get("type") == "turn.completed" for e in events):
        return RunProblem("codex emitted no completed turn", False)
    return None


def _provider_problem(events: list[dict]) -> LoginProblem | None:
    session = _last(events, "codex.session")
    provider = session.get("model_provider")
    if not session or provider == "openai":
        return None
    return LoginProblem(f"the run was served through provider {provider!r} (Codex CLI "
                        f"{session.get('cli_version') or 'unknown'}), not OpenAI's own",
                        f"run `{CODEX.reset_command}` to restore the pinned configuration",
                        CODEX.name)


def _unconfirmed_problem(events: list[dict]) -> LoginProblem | None:
    report = _last(events, "codex.token_count")
    limits = report.get("rate_limits")
    quota = quota_from_limits(limits)
    why = ("no session record was read" if not report and not _last(events, "codex.session")
           else "the session record carries no quota report" if not report
           else "its quota report carries no rate limits" if not isinstance(limits, dict)
           else f"its quota report's credits state is not recognised ({quota.unrecognised})"
           if quota.unrecognised
           else "its quota report carries no credits state" if quota.credits is None
           else "its quota report carries no plan type" if not quota.plan_type else None)
    if why is None:
        return None
    return LoginProblem(f"plan use cannot be confirmed: {why}",
                        "rerun; if it repeats, report it, because the session record no longer "
                        "carries what the billing guard reads", CODEX.name)


def _reported(check: Callable[[Quota], LoginProblem | None]
              ) -> Callable[[list[dict]], LoginProblem | None]:
    """A quota check over the session record's last report, silent when there
    is none (that is `_unconfirmed_problem`'s finding, not an explicit signal)."""
    def after(events: list[dict]) -> LoginProblem | None:
        limits = _last(events, "codex.token_count").get("rate_limits")
        return check(quota_from_limits(limits)) if isinstance(limits, dict) else None

    return after


def _reroute_problem(events: list[dict]) -> LoginProblem | None:
    reroute = rerouted(events)
    if reroute is None:
        return None
    return LoginProblem(f"the model was rerouted: requested {reroute[0]}, served {reroute[1]}",
                        f"rerun with `--model {reroute[1]}`", CODEX.name)


# in the order of the spec's after-run list; all but the second are explicit signals
EXPLICIT_BILLING: tuple[Callable[[list[dict]], LoginProblem | None], ...] = (
    _provider_problem,
    _reported(lambda quota: _plan_problem(quota, "the run's")),
    _reported(lambda quota: _credits_problem(quota, "the run drew")),
    _reported(_reached_problem),
    _reroute_problem,
)


def billing_problem(events: list[dict]) -> LoginProblem | None:
    """The first billing reason a finished run's session record shows: another
    provider, plan use unconfirmed, a plan outside the allowed set, credits
    drawn, a reached limit, a reroute."""
    checks = (EXPLICIT_BILLING[0], _unconfirmed_problem, *EXPLICIT_BILLING[1:])
    return next((problem for check in checks if (problem := check(events))), None)


def explicit_billing(events: list[dict]) -> LoginProblem | None:
    return next((problem for check in EXPLICIT_BILLING if (problem := check(events))), None)


def _inside(path: str, root: Path) -> bool:
    return Path(path).resolve().is_relative_to(root.resolve())


def isolation_problem(events: list[dict], skill_root: Path) -> RunProblem | None:
    """A skill offered from outside the workspace's skill directory, a call of
    the host's cloud-skill tools, or any MCP call (the home configures no MCP
    server): untested for isolation."""
    foreign = [path for record in events if record.get("type") == "codex.skills"
               for path in record.get("files") or [] if not _inside(path, skill_root)]
    cloud = [str(r.get("name")) for r in events if r.get("type") == "codex.tool"
             and str(r.get("name")).startswith(CLOUD_SKILLS)]
    mcp = [name for name, _ in codex_tool_calls(events) if name.startswith("mcp__")]
    parts = [*([f"the run offered skills outside {skill_root}: {', '.join(foreign)}"]
               if foreign else []),
             *([f"the run called the host's cloud-skill tools: {', '.join(cloud)}"]
               if cloud else []),
             *([f"the run made MCP tool calls, and the home configures no MCP server: "
                f"{', '.join(_mcp_label(name) for name in mcp)}"] if mcp else [])]
    if not parts:
        return None
    return RunProblem(f"untested: {'; '.join(parts)}. The run's isolation did not hold", True,
                      "isolation")


def _mcp_label(name: str) -> str:
    _, server, tool = [*name.split("__", 2), "", ""][:3]
    return f"{name} (server {server}, tool {tool})"


def effort_problem(events: list[dict], effort: str | None) -> RunProblem | None:
    """A requested effort the host did not serve, by the session record's
    `turn_context.effort`: untested for a precondition."""
    if not effort:
        return None
    served = _last(events, "codex.turn_context").get("effort")
    if served == effort:
        return None
    return RunProblem(f"untested: the host served effort {served or 'unreported'!r}, not the "
                      f"requested {effort!r}. Rerun without --effort, or with an effort this "
                      "model serves", True, "precondition")


def _untested_failure(failure: RunProblem, events: list[dict], skill_root: Path) -> RunProblem:
    """A failed or timed-out run whose saved events also show an explicit
    billing signal is untested for billing, and one that shows a broken
    isolation (a foreign skill, a cloud-skill tool, an MCP call) is untested
    for isolation, naming both. A missing quota report is no explicit signal
    here: a run that failed or hit its limit stays a runner failure naming
    why (testing-harness spec: Codex interrupted before kill)."""
    if failure.untested:
        return failure
    signal = explicit_billing(events)
    if signal is not None:
        return RunProblem(f"{failure.message} (not a plan result: {refusal(signal)})", True,
                          "subscription", billing=signal.cause)
    isolation = isolation_problem(events, skill_root)
    if isolation is not None:
        return RunProblem(f"{failure.message} ({isolation.message})", True, "isolation")
    return failure


def planted_problem(events: list[dict]) -> RunProblem | None:
    """A run that left the workspace replaced, or holding a link, FIFO,
    socket, device or hard link (`workspace_breach` in the runner's record;
    Decision 16): untested for isolation, before anything else, since no
    verdict may read the run's files. The stop it recorded holds every later
    run."""
    planted = harness_record(events).get("workspace_breach")
    if not planted:
        return None
    return RunProblem(refusal(LoginProblem(
        f"{planted}; no verdict read the run's files", STOP_REMEDY, CODEX.name, "isolation")),
        True, "isolation")


def run_problem(events: list[dict], *, skill_root: Path, effort: str | None) -> RunProblem | None:
    """Everything a finished run's saved events say against a verdict, in
    order: a workspace the run left unsafe to read, a failure (with any
    explicit billing signal or broken isolation), the billing guard, the
    isolation, the served effort."""
    planted = planted_problem(events)
    if planted:
        return planted
    harness = harness_record(events)
    failure = failure_reason(events, int(harness.get("exit_code") or 0),
                             str(harness.get("stderr_tail") or ""))
    if failure:
        return _untested_failure(failure, events, skill_root)
    billing = billing_problem(events)
    if billing:
        return RunProblem(refusal(billing), True, "subscription", billing=billing.cause)
    return isolation_problem(events, skill_root) or effort_problem(events, effort)


def timeout_problem(failed: CodexRunFailed, *, skill_root: Path) -> RunProblem:
    """A run stopped at its time limit: a runner failure naming the limit,
    unless its workspace was left unsafe to read, or the session record
    captured before the raise shows an explicit billing signal or a broken
    isolation."""
    return planted_problem(failed.events) or _untested_failure(
        RunProblem(failed.message, False), failed.events, skill_root)


# ---------- the isolation stop (Decision 16, the user's decision D-d) ---------------------------

STOP_FILE = "stop.json"
CLEAR_STOP_COMMAND = "uv run poe host-login codex --clear-stop"
STOP_REMEDY = f"read the run's findings, then run `{CLEAR_STOP_COMMAND}`"


def read_stop(home: Path) -> dict | None:
    """The isolation stop recorded in the Codex home, or None without one. A
    stop file that cannot be read, is no JSON object or holds no non-empty
    `stop` object reads as a recorded stop saying so: the stop is the
    fail-closed backstop, so damage refuses rather than reads as none."""
    try:
        text = (home / STOP_FILE).read_text(encoding="utf-8")
    except FileNotFoundError:
        return None
    except OSError:
        text = ""
    with suppress(ValueError):
        data = json.loads(text)
        stop = data.get("stop") if isinstance(data, dict) else None
        if isinstance(stop, dict) and stop:
            return stop
    return {"kind": "isolation", "cause": f"the stop record in {STOP_FILE} cannot be read",
            "at": "unknown"}


def record_stop(home: Path, cause: str) -> None:
    """Record an isolation stop with its cause and time; a second cause is
    appended to the first, which keeps its time."""
    old = read_stop(home)
    at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    stop = ({"kind": "isolation", "cause": f"{old.get('cause')}; {cause}",
             "at": old.get("at", at)} if old else {"kind": "isolation", "cause": cause, "at": at})
    target = home / STOP_FILE
    temporary = target.with_name(f".{STOP_FILE}.tmp")
    temporary.write_text(json.dumps({"stop": stop}, indent=2), encoding="utf-8")
    temporary.replace(target)  # os.replace: atomic


def clear_stop(home: Path) -> dict | None:
    """Remove a recorded stop, a damaged record included, and nothing else;
    the removed stop."""
    stop = read_stop(home)
    if stop is not None:
        (home / STOP_FILE).unlink(missing_ok=True)
    return stop


def stop_problem(stop: Mapping | None) -> LoginProblem | None:
    """A recorded stop as a refusal: its cause, and its one remedy."""
    if not stop:
        return None
    return LoginProblem(f"an isolation stop is recorded in the Codex harness home "
                        f"({stop.get('cause')}, {stop.get('at')})", STOP_REMEDY, CODEX.name,
                        "isolation")


def workspace_breach(ws: Path, identity: tuple[int, int] | None, home: Path) -> str | None:
    """The workspace right after the Codex child (Decision 16), before the
    session capture, the event file and any verdict: `workspace_guard.breach`
    (the workspace replaced, or a link, FIFO, socket, device or hard link,
    each unlinked without being followed). A breach records an isolation
    stop at once."""
    planted = workspace_guard.breach(ws, identity)
    if planted:
        record_stop(home, planted)
    return planted


# ---------- the run ---------------------------------------------------------------------------


def login_method(home: Path, environ: Mapping[str, str]) -> str:
    """`codex login status`, reduced to the method at once: the line goes to
    stderr (0.160), read together with stdout in case a release moves it; the
    masked key fragment of an API-key line never leaves `codex_status`."""
    _, out, err = probe(list(CODEX.status_argv), home, environ)
    return host_login.codex_status(f"{err}\n{out}")


def preflight(environ: Mapping[str, str] | None = None) -> LoginProblem | None:
    """The harness home's conditions, without a model call and before any run,
    in the order of the requirement: its location, a recorded isolation stop
    (a file read, so it refuses before the first Codex child; Decision 16),
    the CLI version, the home and its marker, the ChatGPT login, and its
    cleanliness. The feature allowlist and the stop once more are checked
    under the run lock, just before the run."""
    environ = os.environ if environ is None else environ
    root = host_login.state_root(environ)
    home = root / "hosts" / CODEX.name
    return (host_login.check_location(root, environ, record=CODEX,
                                      tempdir=host_login.system_tempdir())
            or stop_problem(read_stop(home))  # a file read, before the first Codex child
            or host_login.check_codex_version(host_login.codex_version(
                probe(["--version"], home, environ)[1]))
            or host_login.check_presence(home, CODEX)
            or host_login.check_codex_login(login_method(home, environ), home)
            or host_login.check_codex_home(home))


def isolated_home(_stack: ExitStack, _args: argparse.Namespace,
                  environ: Mapping[str, str] | None = None) -> Path:
    """The Codex home a run executes in, after its preflight; refused as
    untested otherwise. Every Codex run is isolated: Codex has no ambient mode."""
    problem = preflight(environ)
    if problem:
        raise CodexRefused.of(problem)
    return host_login.home(CODEX, os.environ if environ is None else environ)


def parse_lines(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        with suppress(ValueError):
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
    return events


def thread_id(events: list[dict]) -> str | None:
    return _last(events, "thread.started").get("thread_id")


def _closing(home: Path, events: list[dict], quota: Quota, begun: float, code: int | None,
             stderr: str, planted: str | None = None) -> list[dict]:
    records = capture_rollout(home, thread_id(events))
    return [*events, *records, {
        "type": "codex.harness", "duration_ms": int((time.monotonic() - begun) * 1000),
        "exit_code": code, "stderr_tail": stderr.strip()[-800:],
        "quota_before": quota.snapshot(), "workspace_breach": planted}]


def _exec(ws: Path, request: str, argv: list[str], *, home: Path, timeout: float,
          environ: Mapping[str, str], fd: int, quota: Quota,
          ws_id: tuple[int, int] | None = None) -> list[dict]:
    """The run itself, holding the lock through `pass_fds`, with a scratch
    HOME; then, first, the workspace check (`workspace_breach`, Decision 16,
    against the identity taken before the child), and the session record,
    captured and deleted whatever happens."""
    shutil.rmtree(home / SESSIONS, ignore_errors=True)  # a crashed run's record is not this one
    scratch = Path(tempfile.mkdtemp(prefix="devrun-codex-home-"))
    try:
        for name in ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME"):
            Path(run_env({}, scratch)[name]).mkdir(parents=True, exist_ok=True)
        begun = time.monotonic()
        try:
            code, out, err = run(argv, home=home, cwd=ws, timeout=timeout, environ=environ,
                                 scratch=scratch, input=request, pass_fds=(fd,))
        except subprocess.TimeoutExpired as late:
            planted = workspace_breach(ws, ws_id, home)
            events = _closing(home, parse_lines(str(late.output or "")), quota, begun, None,
                              str(late.stderr or ""), planted)
            raise CodexRunFailed(f"codex did not finish within {timeout:g}s", events) from None
        planted = workspace_breach(ws, ws_id, home)
        return _closing(home, parse_lines(out), quota, begun, code, err, planted)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def run_codex(ws: Path, request: str, *, model: str, effort: str | None, timeout: float,
              home: Path, scenario: Mapping, environ: Mapping[str, str] | None = None
              ) -> list[dict]:
    """One Codex run under a single hold of the run lock: a recorded stop read
    again (another run may have recorded one while this one waited), the
    quota read, the feature allowlist, the run (whose child holds the lock
    too), the workspace check, the capture. The workspace's identity is taken
    before any Codex child starts in it. Raises `host_login.RunLockRefused`,
    `CodexRefused` (untested) or `CodexRunFailed` (checked by
    `timeout_problem`); the events it returns are checked afterwards by
    `run_problem`."""
    environ = os.environ if environ is None else environ
    ws_id = workspace_guard.workspace_identity(ws)
    with host_login.run_lock(home) as fd:
        stopped = stop_problem(read_stop(home))
        if stopped:
            raise CodexRefused.of(stopped)
        quota = read_quota(home, environ)
        problem = quota_problem(quota)
        if problem:
            raise CodexRefused.of(problem, billing=problem.cause)
        _, listing, _ = probe(["features", "list", *feature_flags(scenario)], home, environ)
        problem = features_problem(listing, allowed_features(scenario))
        if problem:
            raise CodexRefused.of(problem)
        return _exec(ws, request, command(scenario, ws, model, effort), home=home,
                     timeout=timeout, environ=environ, fd=fd, quota=quota, ws_id=ws_id)


# ---------- `host-status codex` ---------------------------------------------------------------


def _yes(flag: bool) -> str:
    return "yes" if flag else "no"


def _stop_line(home: Path) -> str:
    """The `stop` line: none, or the recorded isolation stop and its cause
    (reported, never a refusal of the status command)."""
    stop = read_stop(home) if home.is_dir() else None
    return f"{stop.get('kind')} ({stop.get('cause')})" if stop else "none"


def _logged_in(home: Path, method: str | None) -> str:
    if method is None:
        return "unknown" if home.is_dir() else "no"
    return _yes(method != "none")


def status(home: Path, environ: Mapping[str, str], *, live_quota: bool = False,
           run_probes: bool = True) -> tuple[dict[str, str], LoginProblem | None]:
    """The lines of `host-status codex` — only the keys of the spec's status
    list, booleans, enums, versions, an age and the quota windows — and the
    first reason the home is not ready. `auth.json` is never opened.

    Only `--version` runs before the home is known to be the harness's own:
    `login status`, `features list` and the `--quota` read (with its run
    lock file) run only when `run_probes` holds (the location was not
    refused) and the home is present, marked, owner-only and clean, so a
    status never points `CODEX_HOME` at a directory the harness does not
    adopt — a copied `~/.codex` among them — and never creates a file there."""
    version = (host_login.codex_version(probe(["--version"], home, environ)[1])
               if run_probes else None)
    presence = host_login.check_presence(home, CODEX)
    unclean = host_login.check_codex_home(home) if presence is None else None
    adopted = run_probes and presence is None and unclean is None
    method = login_method(home, environ) if adopted else None
    listing = probe(["features", "list", *feature_flags({})], home, environ)[1] if adopted else None
    features = features_problem(listing, ALLOWED_FEATURES) if listing is not None else None
    offenders = host_login.codex_offenders(home) if home.is_dir() else []
    lines = {
        "home": str(home),
        "marker": _yes((home / MARKER).is_file()),
        "logged_in": _logged_in(home, method),
        "auth_method": method if method not in (None, "none") else "-",
        "config_pinned": _yes(home.is_dir() and host_login.config_difference(home) is None),
        "clean": ", ".join(offenders) if offenders else _yes(home.is_dir()),
        "last_written": host_login.auth_age(home),
        "cli_version": host_login.version_text(version),
        "min_version": host_login.version_text(host_login.CODEX_MIN_VERSION),
        "features_ok": "unknown" if listing is None else _yes(features is None),
        "last_quota": last_quota(home),
        "stop": _stop_line(home),
        "runs_use": "harness",
    }
    problem = ((host_login.check_codex_version(version) if run_probes else None) or presence
               or (host_login.check_codex_login(method, home) if method is not None else None)
               or unclean or features)
    if live_quota:
        lines["quota"] = "not read: the harness home is not ready"
        if adopted:
            with host_login.run_lock(home):
                quota = read_quota(home, environ)
            lines["quota"] = describe(quota)
            problem = problem or quota_problem(quota)
    return lines, problem
