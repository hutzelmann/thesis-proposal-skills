"""The GitHub Copilot host of the dev runner: invocation, plan billing guard, readers.

A Copilot run executes `copilot -p … --output-format json` in the harness's own
Copilot home (`host_login.COPILOT`, `…/thesis-proposal-dev/hosts/copilot`),
never in the operator's `~/.copilot`, and draws only on the included AI
credits of the operator's Copilot plan (testing-harness spec: Dev-runner host
adapters; Copilot plan billing guard). It is a dev loop only, labelled
"dev-runner (copilot), not comparable to matrix": no registry role, no matrix
cell, nothing written where the support report reads. The account keeps money
out — the operator keeps a $0 budget with "Stop usage" on "All AI Credit SKUs"
and never deletes it, since a product with no budget has unlimited usage —
and every check here is the backstop, failing closed:

- **The credential.** A fine-grained token carrying only "Copilot Requests",
  in the token file beside the home (`host_login.token_path`). `token_env` is
  the one reader: it hands the value to Copilot children only, as
  `COPILOT_GITHUB_TOKEN`, after the one environment builder
  (`host_login.allowlisted_env`) and the scratch homes (`run_env`); `spawn`
  checks the final environment right before `Popen` (`assert_copilot_env`).
  The value is never in an argv or a log line, and `scrub` replaces it in
  everything a child produced — stderr, the stdout events, the session
  records, the workspace files — before anything is saved, printed or judged;
  a hit makes the run untested for isolation and records an isolation stop.
  The client's own session store in the home keeps every transcript
  unscrubbed, so a hit's remedy is a new token and a reset.
  Every child carries `--no-auto-login`, so no stored or `gh` login is used,
  and every child that carries the token names it (`TOKEN_FLAGS`), because at
  1.0.91 that flag leaves an unnamed environment token unread too; the short
  commands (`--version`, the two listings) take both before the subcommand
  (`login_flags`), where the client parses them as global options.
  Every child that writes a process log (the run, the status read, the
  probe) writes it under its scratch directory (`--log-dir`), never into the
  home, and the scratch is deleted with the call.
- **Before the run** (`preflight_checks`, then `LOCKED` and `gate_checks`
  under the run lock): the location, the home's marker and mode, the
  clean-home allow-list, the token's prefix, a recorded stop (before the
  first child starts), `copilot --version` against COPILOT_PINNED_VERSION, the
  machine-wide managed settings, the sandbox tools, the workspace's parent
  folders (`scan_parents`); then, holding the lock, the stop and the token
  file once more (another run or a login may have changed them while this
  one waited), the model-free status read through the headless server
  (`read_status`: raw `quota_snapshots`, never the client's mapped `getQuota`
  values), the billing guard (`status_problem`), the model listing, the skill
  and MCP rosters (`roster_problem`) and the confinement probe
  (`confinement_probe`, `probe_problem`). The headless server never puts a
  session it creates in the sandbox, so the probe reads the sandbox block the
  client reads from the home (`user.settings.get`), refuses unless it is the
  pinned one, applies it to its session with `session.options.update` as
  prompt mode does, and only then runs fixed commands through
  `session.shell.executeUserRequested`; it refuses unless the sandboxed shell
  is denied the token file, the client's and the harness's own process
  environments, `~/.ssh`, `~/.config/gh`, `gh` and git authentication and the
  host's shared /tmp (reading it, or writing a file the host then sees),
  still runs the skills, and reports every command as sandboxed; last, the
  clean-home check once more, on the home as those reads left it.
- **The work directory** (`work_root`): the workspace and every scratch home
  are made owner-only under the harness state directory where it lies
  outside the operator's home, the repository and the temporary
  directories, otherwise under the per-user runtime directory, never in the
  system temporary directory, which the sandbox denies (the user's decision
  D-b); without either, the run is refused as a precondition.
- **During the run** (`ConfinementWatch`): prompt mode applies the home's
  sandbox itself, which nothing before the run can observe, so the child's
  output is read as it arrives and the child is stopped at the first shell
  completion not reported `sandboxed`, the first sandbox warning, or the
  first file tool pointed outside the workspace (links resolved), rather than
  left to go on with the skill prompt; the stop names the breach. Every child
  leads its own process group, and whatever ended it, the group is killed
  (`stop_group`).
- **The workspace after the run** (`workspace_breach`), before the harness
  reads, scrubs or writes anything in it: the sandboxed shell may write the
  workspace, so a link, a FIFO, socket or device, or a hard link it left
  there, or the workspace itself replaced, would make the unsandboxed harness
  act on another file; each such entry is unlinked unread, and the run is
  untested for isolation with an isolation stop. The event file is created
  afresh without following a link (`claude_runner.save_events`).
- **After the run** (`assess`): the session file is reduced into `copilot.*`
  records (`reduce_session`) and deleted; the status is read again; overage
  growth, an unavailable read, unreadable consumption, more than twice the
  credit cap, zero nano-AIU with tokens and a reached soft cap or session
  limit record a billing stop; a run the watch stopped, a workspace breach, a
  sandbox warning, a shell completion not reported `sandboxed`, or no shell
  completion at all records an isolation stop. The steps after the child's
  start fail closed (`_execute`): one that
  raises still scrubs the workspace and records a billing stop. A stop — a
  damaged stop record included — refuses every later run until the operator
  clears it with `uv run poe host-login copilot --clear-stop`; so does the
  approval stop every login records, which makes the first model call after
  a login the operator's explicit go.

Copilot tool events map to the canonical tool names (`copilot_tool_calls`), so
the shared verdicts and the route reader work unchanged. Copilot reports AI
credits, not money: the summary's cost is absent, with the credits at one cent
each as a notional figure labelled as not billed (`copilot_read`).

Imports `host_login` and the shape module `hosts` only — never `routing` or
`claude_cli` — so `routing.tool_calls` can use it without a cycle. Facts are
pinned to CLI 1.0.91 by the V-pass (change design, "Facts at 1.0.91"). The L0
tests run every pure part over the synthetic fixtures in
`tests/unit/data/copilot_streams/` and never start the real `copilot`: an
autouse fixture points the binary seam (`binary`) at a sentinel that raises.
Verified on Linux only; Windows is refused (the sandbox cannot enforce its
deny list there), macOS is allowed and unverified.

Usage (the operator only; K1's `gh` cut-off check, never used by a run):
  uv run python harness/copilot_cli.py run-env -- <command> [args...]
"""

from __future__ import annotations

import argparse
import json
import os
import queue
import re
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Callable, Iterable, Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass, field
from functools import partial
from pathlib import Path, PurePath

import host_login
from host_login import COPILOT, MARKER, LoginProblem, refusal
from hosts import RunView, needs_network

REPO = Path(__file__).resolve().parent.parent

# ---------- pinned facts (design, Facts at 1.0.91) ----------------------------------------

COPILOT_PINNED_VERSION = (1, 0, 91)
# the headless read and the probe: judgment, as the Codex quota read's bound
STATUS_TIMEOUT_S = 20
PROBE_TIMEOUT_S = 60
# the bundled skills `copilot skill list --json` lists at 1.0.91 (measured)
BUILTIN_SKILLS = ("customize-cloud-agent", "github-pr-media")
# the built-in MCP servers `--disable-builtin-mcps` names at 1.0.91
BUILTIN_MCP = ("github-mcp-server", "githubiq")
# what the Linux sandbox needs on PATH at 1.0.91 (runtime.node and changelog 1.0.83)
SANDBOX_TOOLS = ("bwrap", "unshare", "slirp4netns", "nsenter", "iptables", "ip6tables",
                 "iptables-restore", "ip6tables-restore")
MANAGED_SETTINGS = ("/etc/github-copilot/managed-settings.json", "/etc/github-copilot/policy.d")
# the client's warnings that the sandbox did not engage: 1.0.91 runtime.node
# 6939584, 6997010 and 7013801, and the 1.0.70 wording
SANDBOX_WARNINGS = ("Sandboxing is enabled but is not supported",
                    "Sandboxing is enabled but not supported on this platform",
                    "sandbox enforcement unavailable", "was ignored")
# the origin prompt mode records for a sandbox the home's settings enable, with
# the gated `--sandbox` flag dropped (`m2`, app.js 4735387, called at 4952692);
# the confinement probe applies the home's block with the same origin
SANDBOX_SOURCE = "user_enabled"
# how often the run's watch checks for a breach while the child runs (seconds)
WATCH_POLL_S = 0.2
# 1.0.91 runtime.node 7688290
EFFORT_UNAPPLIED = re.compile(r"does not support reasoning effort configuration")
EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "max")
MIN_AI_CREDITS = 30
LOW_QUOTA_PERCENT = 10
NOTIONAL_USD_PER_CREDIT = 0.01
NANO = 1_000_000_000
GITHUB_TOKEN_PREFIXES = host_login.GITHUB_TOKEN_PREFIXES
SCRUBBED = "[copilot-token]"
QUOTA_FILE = "quota.json"
SESSION_STATE = "session-state"
HEADLESS = ("--headless", "--stdio", "--no-auto-login", "--no-auto-update", "--log-level", "none")
# the one credential a child that carries the token may read: at 1.0.91
# `--no-auto-login` drops the unnamed environment token too (task 7.4b), so it
# is named, as the bundled SDK names its own (`startCLIServer`)
TOKEN_FLAGS = ("--auth-token-env", COPILOT.token_env)
# the auth type the client reports for the token read from that variable: at
# 1.0.91 an SDK-configured token (`TokenAuthInfo`), as K1 recorded live (task
# 7.5). `env` (`EnvAuthInfo`, automatic detection of an environment token) is
# what `--no-auto-login` rules out, so it now refuses like any other source.
# The schema's other `token` variant, `SettableTokenAuthInfo`, comes only from
# the RPC `session.gitHubAuth.setCredentials`, which the harness never sends
TOKEN_AUTH_TYPES = ("token",)
TASK_KINDS = ["agent", "client", "shell"]
STOP_KINDS = {"approval": 0, "isolation": 1, "billing": 2}

# Where each network skill's scripts send requests: a `--allow-url` per host
# for a scenario that stages the skill. A host an L0 test finds in a script
# but that no request reaches sits in NOT_CONTACTED with its reason.
SKILL_HOSTS: Mapping[str, tuple[str, ...]] = {
    "proposal-import": ("api.crossref.org",),
    "proposal-lit-search": ("api.crossref.org", "api.openalex.org", "api.opencitations.net",
                            "api.semanticscholar.org", "dblp.org", "export.arxiv.org"),
    "proposal-reverse": ("api.crossref.org",),
}
NOT_CONTACTED: Mapping[str, str] = {
    "github.com": "the User-Agent string names the repository",
    "openalex.org": "the API-key help text",
    "arxiv.org": "an XML namespace of the arXiv feed",
    "www.w3.org": "the Atom XML namespace",
}
LOCAL_FIXTURE_HOST = "127.0.0.1"  # where claude_runner binds its fixture server

# the tool set of design Decision 8 (`--available-tools`)
BASE_TOOLS = ("bash", "read_bash", "write_bash", "stop_bash", "list_bash", "view", "create",
              "edit", "apply_patch", "glob", "grep", "rg", "skill", "report_intent",
              "update_todo")
HELPER_TOOLS = ("task", "read_agent", "list_agents", "write_agent")
NETWORK_TOOLS = ("web_fetch",)
DENIED_TOOLS = ("memory", "github-mcp-server", "shell(gh:*)", "shell(git push)")
# `--sandbox` is gated behind experimental mode at 1.0.91, which the pinned
# settings keep off: the client drops the flag with the notice "--sandbox/
# --no-sandbox requires the sandbox feature … Ignoring for this session." (app.js
# 4994855, `cbe`), and the run's sandbox comes from the home's `sandbox.enabled`
# alone, recorded as source `user_enabled`. The notice is expected; it matches
# no SANDBOX_WARNINGS phrase (design Decision 13)
SWITCHES = ("--disable-builtin-mcps", "--no-custom-instructions", "--no-ask-user", "--no-remote",
            "--no-remote-export", "--no-auto-login", *TOKEN_FLAGS, "--no-auto-update",
            "--no-bash-env",
            "--disallow-temp-dir", f"--secret-env-vars={COPILOT.token_env}", "--sandbox")


def binary() -> str:
    """The Copilot executable every child starts. The seam the L0 conftest
    points at a sentinel that raises, so no test can start the real client."""
    return COPILOT.binary


# ---------- refusals ---------------------------------------------------------------------


class CopilotRefused(Exception):
    """A Copilot run that is untested: `message` in the one refusal template,
    `kind` one of `subscription`, `isolation` or `precondition`, `billing` the
    billing cause where that is the reason."""

    def __init__(self, message: str, kind: str, events: list[dict] | None = None,
                 billing: str | None = None, problem: LoginProblem | None = None):
        super().__init__(message)
        self.message, self.kind, self.events, self.billing = message, kind, events or [], billing
        self.problem = problem

    @classmethod
    def of(cls, problem: LoginProblem, billing: str | None = None) -> CopilotRefused:
        return cls(refusal(problem), problem.kind, billing=billing, problem=problem)


class BillingEnvError(CopilotRefused):
    """A Copilot child's final environment carries a variable of the dropped
    families, a second token-shaped variable, or a `COPILOT_HOME` that is not
    the harness home; names the variables, never their values."""

    def __init__(self, names: Sequence[str], wrong_home: bool = False):
        causes = [f"still carries {', '.join(names)}, which could bill or act as another "
                  "account, or route the run to another provider"] if names else []
        causes += ["does not set COPILOT_HOME to the harness home"] if wrong_home else []
        problem = LoginProblem(f"the Copilot child's environment {' and '.join(causes)}",
                               "report it: the harness's environment builder let it through",
                               COPILOT.name)
        super().__init__(refusal(problem), "subscription", billing=problem.cause)
        self.names = list(names)


class CopilotRunFailed(Exception):
    """A Copilot run that ended without a verdict for another reason: a
    runner failure, unless `assess` finds an untested cause in its events."""

    def __init__(self, message: str, events: list[dict] | None = None):
        super().__init__(message)
        self.message, self.events = message, events or []


@dataclass(frozen=True)
class RunProblem:
    """Why a finished Copilot run has no verdict: untested (with its kind and,
    for billing, the cause) or a runner failure. `final` marks the one runner
    failure no later finding turns into untested: a session without a
    shutdown record, whose consumption cannot be read."""

    message: str
    untested: bool
    kind: str | None = None
    billing: str | None = None
    final: bool = False


def _problem(cause: str, remedy: str, kind: str = "subscription") -> LoginProblem:
    return LoginProblem(cause, remedy, COPILOT.name, kind)


# ---------- the child environment and the one place a child starts ------------------------

# the names the record sets itself: the pre-spawn assertion's exemption
COPILOT_EXEMPT = frozenset(COPILOT.child_vars(PurePath("/state/hosts/copilot")))
SCRATCH_VARS = ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME",
                "XDG_RUNTIME_DIR")


def run_env(env: Mapping[str, str], scratch: Path) -> dict[str, str]:
    """A run's or a call's scratch `HOME` (and `USERPROFILE`) and XDG base
    directories, the runtime directory among them, beside the workspace."""
    return {**env, "HOME": str(scratch), "USERPROFILE": str(scratch),
            "XDG_CONFIG_HOME": str(scratch / ".config"),
            "XDG_CACHE_HOME": str(scratch / ".cache"),
            "XDG_DATA_HOME": str(scratch / ".local" / "share"),
            "XDG_STATE_HOME": str(scratch / ".local" / "state"),
            "XDG_RUNTIME_DIR": str(scratch / "run")}


# ---------- the work directory (Decision 7, the user's decision D-b) ------------------------

WORK_PARTS = ("work", "copilot")
NO_WORK_REMEDY = (f"point {host_login.STATE_VAR} at a directory of its own outside your home, the "
                  "repository and the system temporary directory, or log in through a session "
                  "that provides the per-user runtime directory /run/user/<uid> (systemd-logind)")


def runtime_dir(uid: int | None = None) -> Path | None:
    """The per-user runtime directory, `/run/user/<uid>`, where it is a real
    directory the user owns and nobody else may enter (systemd-logind's);
    None elsewhere. The seam L0 tests replace, so no test writes there."""
    if not hasattr(os, "getuid"):
        return None
    uid = os.getuid() if uid is None else uid
    path = Path(f"/run/user/{uid}")
    try:
        info = os.lstat(path)
    except OSError:
        return None
    private = stat.S_ISDIR(info.st_mode) and info.st_uid == uid and not info.st_mode & 0o077
    return path if private else None


def choose_work_root(state: PurePath, runtime: PurePath | None, *,
                     avoid: Iterable[PurePath]) -> PurePath | None:
    """Where every Copilot workspace and scratch directory lives (Decision 7):
    under the harness state directory where it lies outside every directory
    of `avoid` — the operator's home, whose own skills the client's
    parent-folder walk would list, the repository, and the temporary
    directories the sandbox denies; otherwise under the per-user runtime
    directory; otherwise nowhere. Pure."""
    if not any(state == root or root in state.parents for root in avoid):
        return state.joinpath(*WORK_PARTS)
    if runtime is not None:
        return runtime.joinpath(host_login.STATE_NAME, *WORK_PARTS)
    return None


def _private_dirs(root: Path) -> bool:
    """Create the missing levels of `root` owner-only, top down; whether it is
    then a real directory (never a link)."""
    missing = []
    level = root
    while not level.exists() and not level.is_symlink() and level != level.parent:
        missing.append(level)
        level = level.parent
    for path in reversed(missing):
        path.mkdir(mode=0o700)
        path.chmod(0o700)  # whatever the umask
    return root.is_dir() and not root.is_symlink()


def work_root(environ: Mapping[str, str] | None = None) -> Path:
    """The Copilot work directory (`choose_work_root`), created owner-only:
    never the system temporary directory, which the sandbox denies and where
    the operator's other processes keep their files (D-b). The state root's
    location check comes first, so a refused override gets nothing created;
    without either location the run is refused as untested for a
    precondition (`CopilotRefused`), and nothing is created."""
    environ = os.environ if environ is None else environ
    state = host_login.state_root(environ)
    problem = host_login.check_location(state, environ, record=COPILOT)
    if problem:
        raise CopilotRefused.of(problem)
    avoid = [host_login.account_home().resolve(), REPO.resolve(),
             *(Path(tmp).resolve() for tmp in host_login.temp_dirs())]
    root = choose_work_root(state.resolve(), runtime_dir(), avoid=avoid)
    if root is None or not _private_dirs(Path(root)):
        raise CopilotRefused.of(_problem(
            f"the Copilot workspace has no place outside the system temporary directory and "
            f"your home: the harness state directory {state} lies inside your home, the "
            f"repository or a temporary directory, and no private per-user runtime directory "
            f"exists{'' if root is None else f' ({root} is not a directory)'}",
            NO_WORK_REMEDY, "precondition"))
    return Path(root)


def work_problem(environ: Mapping[str, str] | None = None) -> LoginProblem | None:
    """Why no Copilot work directory can be had (`work_root`), or None."""
    try:
        work_root(environ)
    except CopilotRefused as refused:
        return refused.problem
    return None


def make_scratch(prefix: str, environ: Mapping[str, str] | None = None) -> Path:
    """A fresh scratch home with its XDG directories, owner-only, in the
    Copilot work directory (`work_root`): outside the operator's home, the
    repository and the system temporary directory."""
    scratch = Path(tempfile.mkdtemp(prefix=prefix, dir=work_root(environ)))
    for name in SCRATCH_VARS:
        Path(run_env({}, scratch)[name]).mkdir(mode=0o700, parents=True, exist_ok=True)
    return scratch


@contextmanager
def call_scratch(environ: Mapping[str, str] | None = None) -> Iterator[Path]:
    """A scratch home for one short call, removed afterwards."""
    scratch = make_scratch("devrun-copilot-call-", environ)
    try:
        yield scratch
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


def _token_file(home: Path) -> tuple[str, LoginProblem | None]:
    """The token file's value and why it cannot be used — the one reader of
    that file outside the login and the logout (Decision 4). One trailing
    newline is stripped and the prefix re-checked. An empty value means the
    file is missing or empty; a problem with a value means it is not a
    fine-grained token."""
    path = host_login.token_path(home)
    try:
        value = path.read_text(encoding="utf-8").removesuffix("\n")
    except OSError:
        value = ""
    problem = (_problem(f"the token file {path} is missing or empty",
                        "run `uv run poe host-login copilot`") if not value else
               _problem(f"the token in {path} is not a fine-grained token",
                        host_login.COPILOT_TOKEN_REMEDY)
               if host_login.token_problem(value) else None)
    return value, problem


def token_env(home: Path, *, strict: bool = True) -> dict[str, str] | LoginProblem:
    """`{COPILOT_GITHUB_TOKEN: <token>}` from the token file (`_token_file`). A
    missing, empty or classic token refuses the run as untested
    (`CopilotRefused`), or with `strict=False` comes back as the
    `LoginProblem`. The value goes nowhere else: never an argv, a log line or
    a message."""
    value, problem = _token_file(home)
    if problem and strict:
        raise CopilotRefused.of(problem)
    return problem or {COPILOT.token_env: value}  # type: ignore[dict-item]


def scrub(text: str, token: str | None) -> tuple[str, bool]:
    """Replace every occurrence of the token's value; report whether one was
    found. The client's own redaction is not the only guard (Decision 4)."""
    if not token or token not in text:
        return text, False
    return text.replace(token, SCRUBBED), True


def scrub_events(events: list[dict], token: str | None) -> tuple[list[dict], bool]:
    """`scrub` over every event, field values and keys alike."""
    cleaned, hit = [], False
    for event in events:
        text, found = scrub(json.dumps(event, ensure_ascii=False), token)
        cleaned.append(json.loads(text) if found else event)
        hit = hit or found
    return cleaned, hit


def _unsafe_entry(mode: int, links: int) -> str | None:
    """Why the harness must not follow, read or write a workspace entry: a
    link (it would act on the link's target), a FIFO, socket or device, or a
    regular file with another name elsewhere (a hard link, whose content is
    another file's). A directory or a singly linked regular file is safe."""
    if stat.S_ISDIR(mode):
        return None
    if stat.S_ISLNK(mode):
        return "a link"
    if not stat.S_ISREG(mode):
        return "not a regular file"
    return "a hard link" if links > 1 else None


def workspace_entries(root: Path) -> Iterator[tuple[Path, os.stat_result]]:
    """Every entry under `root`, by `lstat`, without following a link: a link
    to a directory is listed, never descended into."""
    for top, dirs, files in os.walk(root, followlinks=False):
        for name in sorted((*dirs, *files)):
            path = Path(top, name)
            with suppress(OSError):
                yield path, os.lstat(path)


def unsafe_entries(root: Path) -> list[tuple[Path, str]]:
    """The entries under `root` the harness must not follow (`_unsafe_entry`),
    each with why; nothing is read."""
    found = []
    for path, info in workspace_entries(root):
        why = _unsafe_entry(info.st_mode, info.st_nlink)
        if why:
            found.append((path, why))
    return found


def _scrub_file(path: Path, needle: bytes) -> bool:
    """Replace the token's value in one regular file, opened without following
    a link at its name; whether it held the value."""
    nofollow = getattr(os, "O_NOFOLLOW", 0)
    with os.fdopen(os.open(path, os.O_RDONLY | nofollow), "rb") as fh:
        data = fh.read()
    if needle not in data:
        return False
    with os.fdopen(os.open(path, os.O_WRONLY | os.O_TRUNC | nofollow), "wb") as fh:
        fh.write(data.replace(needle, SCRUBBED.encode("utf-8")))
    return True


def scrub_tree(root: Path, token: str | None) -> list[str]:
    """Scrub the token's value from every regular file under `root` (the
    workspace a verdict, the judge and a kept run read); the relative names of
    the files that held it. Nothing is followed: a root that is no longer a
    directory, a link, and any other entry `_unsafe_entry` names are passed
    over, unread and unwritten — `workspace_breach`, which runs first, reports
    and removes them (Decision 13, the workspace after the run)."""
    if not token or root.is_symlink() or not root.is_dir():
        return []
    needle, hits = token.encode("utf-8"), []
    for path, info in workspace_entries(root):
        if stat.S_ISDIR(info.st_mode) or _unsafe_entry(info.st_mode, info.st_nlink):
            continue
        with suppress(OSError):
            if _scrub_file(path, needle):
                hits.append(path.relative_to(root).as_posix())
    return sorted(hits)


def ignored_env(environ: Mapping[str, str]) -> list[str]:
    """The inherited variables of the dropped families, by name only, for the
    summary's `ignored_env`; their values appear nowhere."""
    return sorted(name for name in environ if COPILOT.stripped(name))


def _leaks(name: str, value: str) -> bool:
    if name == COPILOT.token_env or name in COPILOT_EXEMPT:
        return False
    return COPILOT.stripped(name) or str(value).startswith(GITHUB_TOKEN_PREFIXES)


def assert_copilot_env(env: Mapping[str, str], home: Path | None = None) -> None:
    """Refuse a final child environment that carries a dropped-family name the
    record does not set and that is not the token variable, or a token-shaped
    value under another name (Decision 5), or — given `home` — a
    `COPILOT_HOME` other than the harness home."""
    leaks = sorted(name for name, value in env.items() if _leaks(name, value))
    wrong_home = home is not None and env.get(COPILOT.home_var) != str(home)
    if leaks or wrong_home:
        raise BillingEnvError(leaks, wrong_home)


def child_env(home: Path, environ: Mapping[str, str] | None = None, scratch: Path | None = None,
              token: str | None = None) -> dict[str, str]:
    """The final environment of a Copilot child: the one builder's
    (`allowlisted_env` with the Copilot record), the scratch homes, and the
    token variable added last — never by the builder, which reads no
    credential."""
    env = host_login.allowlisted_env(COPILOT, home, environ)
    if scratch is not None:
        env = run_env(env, scratch)
    if token is not None:
        env[COPILOT.token_env] = token  # type: ignore[index]
    return env


def start(argv: Sequence[str], *, home: Path, cwd: Path, env: Mapping[str, str],
          stdin: int = subprocess.DEVNULL, pass_fds: Sequence[int] = (),
          text: bool = True) -> subprocess.Popen:
    """The single place a Copilot child starts — the run, `--version`, the
    headless status read and probe, `skill list` and `mcp list`: the final
    environment is checked immediately before `Popen`, on Linux the child gets
    the parent-death termination request, and every child leads a process
    group of its own, so that `stop_group` reaches what it started."""
    assert_copilot_env(env, home)
    command = [binary(), *argv[1:]]
    options = {"encoding": "utf-8", "errors": "replace"} if text else {}
    return subprocess.Popen(command, cwd=cwd, env=dict(env), stdin=stdin,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=text,
                            pass_fds=tuple(pass_fds), start_new_session=os.name == "posix",
                            preexec_fn=host_login.child_preexec(COPILOT), **options)


def stop_group(proc: subprocess.Popen, sig: int = signal.SIGTERM) -> None:
    """Stop a Copilot child and whatever it started (Decision 13): the child's
    own stop request, a kill after TERM_GRACE_S (`host_login.stop_child`), then
    a kill to every process left in its process group, which `start` made the
    child lead. A shell command the sandbox did not confine has no bwrap
    `--die-with-parent` over it, so a process it put in the background would
    otherwise outlive the stop. One that left the group (`setsid`) is not
    reached: the residual risk the design records."""
    if proc.poll() is None:
        host_login.stop_child(proc, sig)
    if hasattr(os, "killpg"):
        with suppress(OSError):
            os.killpg(proc.pid, signal.SIGKILL)


def spawn(argv: Sequence[str], *, home: Path, cwd: Path, scratch: Path | None,
          token: str | None, environ: Mapping[str, str] | None = None,
          stdin: int = subprocess.DEVNULL, pass_fds: Sequence[int] = (),
          text: bool = True) -> subprocess.Popen:
    """Start a Copilot child in the harness home's environment and leave it running."""
    return start(argv, home=home, cwd=cwd, env=child_env(home, environ, scratch, token),
                 stdin=stdin, pass_fds=pass_fds, text=text)


def login_flags(token: str | None) -> tuple[str, ...]:
    """The credential flags of a child: automatic login off, and the token
    variable named exactly when the child carries the token. A short command
    takes them before its subcommand: at 1.0.91 they are global options there,
    and after `skill list` or `mcp list` a usage error (measured offline
    2026-10-06; `--version` accepts them too)."""
    return ("--no-auto-login", *(TOKEN_FLAGS if token else ()))


def short(args: Sequence[str], *, home: Path, scratch: Path, token: str | None,
          environ: Mapping[str, str] | None = None, cwd: Path | None = None
          ) -> tuple[int, str, str]:
    """A short, model-free Copilot command (`--version`, `skill list --json`,
    `mcp list --json`) to completion, behind the credential flags
    (`login_flags`), stopped at CLIENT_TIMEOUT_S. A binary that cannot start
    answers 127, a hung one 124."""
    env = child_env(home, environ, scratch, token)
    argv = [COPILOT.binary, *login_flags(token), *args]
    try:
        return host_login.run_host(COPILOT, argv, cwd=cwd or scratch, env=env,
                                   timeout=host_login.CLIENT_TIMEOUT_S,
                                   start=partial(start, home=home))
    except OSError:
        return 127, "", ""
    except subprocess.TimeoutExpired:
        return 124, "", ""


# ---------- the version ------------------------------------------------------------------------

_VERSION = re.compile(r"GitHub Copilot CLI (\d+)\.(\d+)\.(\d+)")


def copilot_version(stdout: str) -> tuple[int, int, int] | None:
    """The version `copilot --version` prints (`GitHub Copilot CLI X.Y.Z.`)."""
    match = _VERSION.search(stdout)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def installed_version(home: Path, environ: Mapping[str, str] | None,
                      token: str | None) -> tuple[int, int, int] | None:
    with call_scratch(environ) as scratch:
        return copilot_version(short(["--version"], home=home, scratch=scratch, token=token,
                                     environ=environ)[1])


def check_copilot_version(version: tuple[int, int, int] | None) -> LoginProblem | None:
    """The installed CLI is exactly the pinned version, read with auto-update off."""
    pinned = host_login.version_text(COPILOT_PINNED_VERSION)
    remedy = (f"install the Copilot CLI {pinned} through your package manager, or bump "
              "COPILOT_PINNED_VERSION in a change of its own")
    if version is None:
        return _problem("the Copilot CLI reported no version (is `copilot` installed and on "
                        "PATH?)", remedy, "precondition")
    if version != COPILOT_PINNED_VERSION:
        return _problem(f"the installed Copilot CLI is {host_login.version_text(version)}, not "
                        f"the pinned {pinned}", remedy, "precondition")
    return None


# ---------- the status read (design Decision 6) ------------------------------------------------


@dataclass(frozen=True)
class Snapshot:
    """The chosen raw quota snapshot: the values as the reply carries them, a
    missing field as None — never the client's coerced values."""

    name: str
    overage_permitted: object = None
    overage_count: object = None
    overage_entitlement: object = None
    percent_remaining: object = None
    has_quota: object = None
    unlimited: object = None


@dataclass(frozen=True)
class ModelEntry:
    id: str
    policy: str | None
    efforts: tuple[str, ...]


@dataclass(frozen=True)
class Status:
    """What the harness keeps of the status read — and nothing else: the raw
    reply, with its token, login and organization list, is dropped at the
    parse. `error` says why the read is unavailable."""

    error: str | None = None
    logged_in: bool = False
    auth_type: str | None = None
    host: str | None = None
    auth_errors: int = 0
    has_user: bool = False
    plan: str | None = None
    sku: str | None = None
    token_based_billing: object = None
    reset_date: str | None = None
    snapshot: Snapshot | None = None
    models: tuple[ModelEntry, ...] | None = None


def choose_snapshot(user: Mapping) -> str:
    """The snapshot the client reads (1.0.67 bytes 2314646 and 7175749): `chat`
    for the free limited plan, `premium_interactions` otherwise."""
    return "chat" if user.get("access_type_sku") == "free_limited_copilot" else (
        "premium_interactions")


def _snapshot(user: Mapping) -> Snapshot | None:
    name = choose_snapshot(user)
    snapshots = user.get("quota_snapshots")
    data = snapshots.get(name) if isinstance(snapshots, dict) else None
    if not isinstance(data, dict):
        return None
    return Snapshot(name, *(data.get(key) for key in (
        "overage_permitted", "overage_count", "overage_entitlement", "percent_remaining",
        "has_quota", "unlimited")))


def _text(value: object) -> str | None:
    return str(value) if isinstance(value, (str, int, float)) and str(value) else None


def _user_fields(user: object) -> dict:
    if not isinstance(user, dict):
        return {"has_user": False}
    return {"has_user": True, "plan": _text(user.get("copilot_plan")),
            "sku": _text(user.get("access_type_sku")),
            "token_based_billing": user.get("token_based_billing"),
            "reset_date": _text(user.get("quota_reset_date_utc") or user.get("quota_reset_date")),
            "snapshot": _snapshot(user)}


def _models(reply: object) -> tuple[ModelEntry, ...] | None:
    result = reply.get("result") if isinstance(reply, dict) else None
    entries = result.get("models") if isinstance(result, dict) else None
    if not isinstance(entries, list):
        return None
    models = []
    for entry in (e for e in entries if isinstance(e, dict) and _text(e.get("id"))):
        policy = entry.get("policy") if isinstance(entry.get("policy"), dict) else {}
        efforts = entry.get("supportedReasoningEfforts")
        models.append(ModelEntry(str(entry["id"]), _text(policy.get("state")),
                                 tuple(str(e) for e in efforts if isinstance(e, str))
                                 if isinstance(efforts, list) else ()))
    return tuple(models)


def _reply_failure(reply: object, method: str) -> str | None:
    """Why one JSON-RPC answer is unusable — by the method and the error code
    only, since an error message can carry the login or the token."""
    if not isinstance(reply, dict):
        return f"{method} gave no answer in time"
    if reply.get("error") is not None:
        error = reply["error"]
        code = error.get("code") if isinstance(error, dict) else None
        return f"{method} failed (JSON-RPC error {code})"
    return None


def parse_status(replies: Mapping | None) -> Status:
    """The status read's answers (`connect`, `account.getCurrentAuth` and, when
    asked, `models.list`) reduced to `Status`. Pure."""
    replies = replies or {}
    failure = (_reply_failure(replies.get("connect"), "connect")
               or _reply_failure(replies.get("auth"), "account.getCurrentAuth"))
    if failure:
        return Status(error=failure)
    result = replies["auth"].get("result")
    if not isinstance(result, dict):
        return Status(error="account.getCurrentAuth answered without a result")
    errors = result.get("authErrors")
    count = len(errors) if isinstance(errors, list) else 0
    models = _models(replies.get("models")) if "models" in replies else None
    info = result.get("authInfo")
    if not isinstance(info, dict):
        return Status(auth_errors=count, models=models)
    return Status(logged_in=True, auth_type=_text(info.get("type")), host=_text(info.get("host")),
                  auth_errors=count, models=models, **_user_fields(info.get("copilotUser")))


# -- the headless server: Content-Length framed JSON-RPC over stdio (1.0.91 SDK) --


def _frames(stream, out: queue.Queue) -> None:
    """Read Content-Length framed JSON messages until the stream ends."""
    with suppress(OSError, ValueError):
        while True:
            headers: dict[str, str] = {}
            line = stream.readline()
            while line not in (b"\r\n", b"\n", b""):
                name, _, value = line.decode("ascii", "replace").partition(":")
                headers[name.strip().lower()] = value.strip()
                line = stream.readline()
            if not line:
                break
            body = stream.read(int(headers.get("content-length") or 0))
            with suppress(ValueError):
                message = json.loads(body)
                if isinstance(message, dict):
                    out.put(message)
    out.put(None)


class Rpc:
    """A minimal JSON-RPC client for the headless server: requests with ids,
    notifications collected, and any request from the server answered with
    "method not found" so it never waits on the harness."""

    def __init__(self, proc: subprocess.Popen):
        self.proc = proc
        self.inbox: queue.Queue = queue.Queue()
        self.notes: list[dict] = []
        self.ident = 0
        threading.Thread(target=_frames, args=(proc.stdout, self.inbox), daemon=True).start()

    def send(self, message: dict) -> None:
        body = json.dumps({"jsonrpc": "2.0", **message}).encode("utf-8")
        self.proc.stdin.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)  # type: ignore[union-attr]
        self.proc.stdin.flush()  # type: ignore[union-attr]

    def _next(self, deadline: float) -> dict | None:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return None
        try:
            return self.inbox.get(timeout=remaining)
        except queue.Empty:
            return None

    def _route(self, message: dict) -> None:
        if "method" not in message:
            return
        if "id" in message:  # a request from the server; a closed input leaves it unanswered
            with suppress(OSError, ValueError):
                self.send({"id": message["id"], "error": {"code": -32601,
                                                          "message": "not supported"}})
        else:
            self.notes.append(message)

    def call(self, method: str, params: object, deadline: float) -> dict | None:
        """The answer to one request, or None when the server gave none in time."""
        ident, self.ident = self.ident, self.ident + 1
        try:
            self.send({"id": ident, "method": method, "params": params})
        except (OSError, ValueError):  # a broken pipe, or an input already closed
            return None
        while (message := self._next(deadline)) is not None:
            if message.get("id") == ident and "method" not in message:
                return message
            self._route(message)
        return None

    def drain(self, done: Callable[[], bool], deadline: float) -> None:
        """Collect notifications until `done()` or the deadline."""
        while not done() and (message := self._next(deadline)) is not None:
            self._route(message)


def _method_missing(reply: dict | None) -> bool:
    error = reply.get("error") if isinstance(reply, dict) else None
    return isinstance(error, dict) and error.get("code") == -32601


def handshake(rpc: Rpc, deadline: float) -> dict | None:
    """`connect` (the SDK's handshake), or `ping` against a server without it."""
    reply = rpc.call("connect", {"supportedTaskKinds": TASK_KINDS}, deadline)
    return rpc.call("ping", {}, deadline) if _method_missing(reply) else reply


def _status_exchange(rpc: Rpc, models: bool) -> dict:
    deadline = time.monotonic() + STATUS_TIMEOUT_S
    replies: dict = {"connect": handshake(rpc, deadline)}
    if _reply_failure(replies["connect"], "connect"):
        return replies
    replies["auth"] = rpc.call("account.getCurrentAuth", {}, deadline)
    if models and replies["auth"] is not None:
        replies["models"] = rpc.call("models.list", {}, deadline)
    return replies


def _close(proc: subprocess.Popen) -> None:
    stop_group(proc, COPILOT.stop_signal)
    for stream in (proc.stdin, proc.stdout, proc.stderr):
        with suppress(OSError, AttributeError):
            stream.close()  # type: ignore[union-attr]


def headless(scratch: Path, token: str | None) -> list[str]:
    """The headless server's argv: HEADLESS; the token variable named
    (TOKEN_FLAGS) exactly when the child carries the token — under
    `--no-auto-login` the 1.0.91 server reads no unnamed environment token, and
    `account.getCurrentAuth` answers `{}` (task 7.4b, measured); and the
    process log under the call's or the run's scratch directory — the server
    writes `process-<ms>-<pid>.log` into `<COPILOT_HOME>/logs` otherwise, even
    at log level none (task 7.4a, measured), and that scratch is deleted with
    the call."""
    return [COPILOT.binary, *HEADLESS, *(TOKEN_FLAGS if token else ()),
            "--log-dir", str(scratch / "logs")]


def read_status(home: Path, environ: Mapping[str, str] | None = None, *, token: str | None,
                models: bool = False) -> Status:
    """The account's state through the client's headless server: `connect`,
    `account.getCurrentAuth` and, when asked, `models.list` — the auth manager
    and the model listing, never a prompt, so no model call. The child is
    stopped afterwards, answered or not, at STATUS_TIMEOUT_S at the latest.
    `token=None` reads without the token (`host-status copilot --no-token`).
    Callers hold the run lock."""
    with call_scratch(environ) as scratch:
        try:
            proc = spawn(headless(scratch, token), home=home, cwd=scratch, scratch=scratch,
                         token=token, environ=environ, stdin=subprocess.PIPE, text=False)
        except OSError as exc:
            why = exc.strerror or type(exc).__name__
            return Status(error=f"the reader could not start ({why})")
        try:
            return parse_status(_status_exchange(Rpc(proc), models))
        finally:
            _close(proc)


# -- the billing guard over a status (spec: Copilot plan billing guard) --

UNAVAILABLE_REMEDY = ("report it: the client's server interface does not match the pinned "
                      f"version {host_login.version_text(COPILOT_PINNED_VERSION)}")
# GitHub's Budgets page: "If no budget is set, usage for that product is
# unlimited." So the remedy is a $0 budget that stops usage, never a deleted
# one: with every budget deleted, K2 read `overage_permitted: true` (task 7.6;
# the user's decision D-a, 2026-10-06)
STOP_BUDGET = ('set a $0 budget with "Stop usage" on "All AI Credit SKUs" at '
               "github.com/settings/billing (Budgets and alerts), never deleting it, since no "
               "budget means unlimited usage; or, on an organization seat, ask its administrator")
MODEL_REMEDY = ("enable the model in the account's Copilot settings (github.com/settings/copilot), "
                "or name another model with --model")


def _is_number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _read_failed(status: Status) -> LoginProblem | None:
    if status.error is None:
        return None
    return _problem(f"the Copilot status read is unavailable: {status.error}", UNAVAILABLE_REMEDY)


def _no_login(status: Status) -> LoginProblem | None:
    if status.logged_in and not status.auth_errors:
        return None
    why = (f"{status.auth_errors} auth error(s)" if status.auth_errors else "no login")
    return _problem(f"the status read reports {why}: the token was rejected, has expired or was "
                    "revoked", host_login.COPILOT_TOKEN_REMEDY)


def _auth_type(status: Status) -> LoginProblem | None:
    if status.auth_type in TOKEN_AUTH_TYPES:
        return None
    return _problem(f"the status read reports auth type {status.auth_type or 'none'!r}, not the "
                    "token the harness named", "report it, because another credential reached "
                    "the client")


def _auth_host(status: Status) -> LoginProblem | None:
    if status.host == "https://github.com":
        return None
    return _problem(f"the status read reports the host {status.host or 'none'!r}, not GitHub's "
                    "public host", "report it")


def _no_user(status: Status) -> LoginProblem | None:
    why = ("answers without a Copilot user record" if not status.has_user else
           f"carries no {choose_snapshot({'access_type_sku': status.sku})} snapshot"
           if status.snapshot is None else None)
    if why is None:
        return None
    return _problem(f"the Copilot status read is unavailable: it {why}", UNAVAILABLE_REMEDY)


def _budget(status: Status) -> LoginProblem | None:
    snap = status.snapshot
    permitted, entitlement = snap.overage_permitted, snap.overage_entitlement  # type: ignore[union-attr]
    why = ("the overage permission is missing" if permitted is None else
           "the overage permission is not a boolean" if not isinstance(permitted, bool) else
           "overage is permitted" if permitted else
           "the overage entitlement is missing" if entitlement is None else
           "the overage entitlement is not a number" if not _is_number(entitlement) else
           f"the overage entitlement is {entitlement}" if entitlement > 0 else None)  # type: ignore[operator]
    if why is None:
        return None
    return _problem(f"a Copilot budget is possible: {why}", STOP_BUDGET)


def _overage(status: Status) -> LoginProblem | None:
    count = status.snapshot.overage_count  # type: ignore[union-attr]
    if _is_number(count) and count == 0:
        return None
    why = "missing" if count is None else f"{count}"
    return _problem(f"overage was already drawn (overage count {why})",
                    f"check github.com/settings/billing, and rerun after the reset date "
                    f"{status.reset_date or 'unknown'}")


def _legacy(status: Status) -> LoginProblem | None:
    if status.token_based_billing is True:
        return None
    return _problem("billing is not token based: a legacy plan reports no consumption in "
                    "credits, so the credit cap would go unenforced", "report it")


def _low(status: Status) -> LoginProblem | None:
    snap = status.snapshot
    left = snap.percent_remaining  # type: ignore[union-attr]
    if _is_number(left) and left >= LOW_QUOTA_PERCENT and snap.has_quota is not False:  # type: ignore[union-attr,operator]
        return None
    why = ("the snapshot reports no quota" if snap.has_quota is False else  # type: ignore[union-attr]
           f"{left if _is_number(left) else 'an unreported share'}% remaining")
    return _problem(f"the Copilot quota is low: {why}",
                    f"rerun after the reset date {status.reset_date or 'unknown'}")


# the rows in order; the billing guard's rows carry the billing cause
STATUS_ROWS: tuple[Callable[[Status], LoginProblem | None], ...] = (
    _read_failed, _no_login, _auth_type, _auth_host, _no_user, _budget, _overage, _legacy, _low)
BILLING_ROWS = frozenset({_budget, _overage, _legacy, _low})


def _model_problem(status: Status, model: str | None, effort: str | None) -> LoginProblem | None:
    if model is None:
        return None
    if status.models is None:
        return _problem("the Copilot status read is unavailable: it carries no model listing",
                        UNAVAILABLE_REMEDY)
    entry = next((m for m in status.models if m.id == model), None)
    if entry is None or entry.policy != "enabled":
        why = "does not offer" if entry is None else f"offers under the policy {entry.policy!r}"
        return _problem(f"the client's model listing {why} {model}", MODEL_REMEDY, "precondition")
    if effort and effort not in entry.efforts:
        return _problem(f"the model listing reports no effort {effort!r} for {model} (it reports "
                        f"{', '.join(entry.efforts) or 'none'})",
                        "rerun without --effort, or with an effort the listing reports",
                        "precondition")
    return None


def status_rows(status: Status) -> tuple[LoginProblem | None, bool]:
    """The first status row that refuses, and whether it is a billing row."""
    for row in STATUS_ROWS:
        problem = row(status)
        if problem:
            return problem, row in BILLING_ROWS
    return None, False


def status_problem(status: Status, model: str | None = None,
                   effort: str | None = None) -> LoginProblem | None:
    """The first reason the status refuses a run (Decision 6): the read, the
    auth rows, the five rows of the billing guard, then the model and the
    effort. Pure; a table of rows."""
    return status_rows(status)[0] or _model_problem(status, model, effort)


# -- the status snapshot and the stops in the harness home (Decision 9) --


def snapshot_record(status: Status | None) -> dict | None:
    """What the harness home keeps of a status: the plan class, whether billing
    is token based, the chosen snapshot's overage and remaining values and the
    reset date — never a token, a login or an organization."""
    if status is None or status.error or status.snapshot is None:
        return None
    snap = status.snapshot
    return {"plan_class": f"{status.plan or 'unknown'} ({status.sku or 'unknown'})",
            "token_based_billing": status.token_based_billing, "snapshot": snap.name,
            "overage_permitted": snap.overage_permitted, "overage_count": snap.overage_count,
            "overage_entitlement": snap.overage_entitlement,
            "remaining_pct": snap.percent_remaining, "reset_date": status.reset_date}


_DAMAGED = object()  # a status snapshot file that exists but cannot be read


def _quota_file(home: Path) -> dict | object:
    """The status snapshot file's content: {} when there is none, `_DAMAGED`
    when it exists but is not readable JSON holding an object."""
    try:
        text = (home / QUOTA_FILE).read_text(encoding="utf-8")
    except FileNotFoundError:
        return {}
    except OSError:
        return _DAMAGED
    with suppress(ValueError):
        data = json.loads(text)
        if isinstance(data, dict):
            return data
    return _DAMAGED


def _quota_data(home: Path) -> dict:
    data = _quota_file(home)
    return data if isinstance(data, dict) else {}


def _write_quota(home: Path, data: dict) -> None:
    target = home / QUOTA_FILE
    temporary = target.with_name(f".{QUOTA_FILE}.tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(target)  # atomic, as os.replace


def write_snapshot(home: Path, status: Status | None) -> None:
    """Keep the last status snapshot, and any recorded stop with it — a
    damaged stop record among them, which is kept as the stop it reads as."""
    record = snapshot_record(status)
    if record is None:
        return
    stop = read_stop(home)
    _write_quota(home, {**record, **({"stop": stop} if stop else {})})


def read_stop(home: Path) -> dict | None:
    """The recorded stop, or None when the snapshot file holds none. A record
    that cannot be read — an unreadable file, invalid JSON, a `stop` that is
    not a non-empty object — is a billing stop saying so: stops are the
    fail-closed backstop, so damage refuses rather than reads as none."""
    data = _quota_file(home)
    if isinstance(data, dict) and "stop" not in data:
        return None
    stop = data.get("stop") if isinstance(data, dict) else None
    if isinstance(stop, dict) and stop:
        return stop
    return {"kind": "billing", "cause": f"the stop record in {QUOTA_FILE} cannot be read",
            "at": "unknown"}


def record_stop(home: Path, kind: str, cause: str) -> None:
    """Record a stop (billing, isolation or approval) with its cause and time.
    A second cause is appended; the stronger kind stays (an approval stop
    gives way to an isolation or a billing stop)."""
    data = _quota_data(home)
    old = read_stop(home)
    at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    if old:
        stronger = kind if STOP_KINDS.get(kind, 0) > STOP_KINDS.get(old.get("kind"), 0) else (
            old.get("kind"))
        data["stop"] = {"kind": stronger, "cause": f"{old.get('cause')}; {cause}",
                        "at": old.get("at", at)}
    else:
        data["stop"] = {"kind": kind, "cause": cause, "at": at}
    _write_quota(home, data)


def clear_stop(home: Path) -> dict | None:
    """Remove a recorded stop of any kind, a damaged record included, and
    change nothing else readable; the removed stop."""
    stop = read_stop(home)
    if stop is None:
        return None
    data = _quota_data(home)
    data.pop("stop", None)
    _write_quota(home, data)
    return stop


STOP_REMEDIES = {
    "billing": ("subscription",
                f"check github.com/settings/billing, then run `{host_login.CLEAR_STOP_COMMAND}`"),
    "isolation": ("isolation",
                  f"read the run's findings, then run `{host_login.CLEAR_STOP_COMMAND}`"),
    "approval": ("precondition",
                 f"run `{host_login.CLEAR_STOP_COMMAND}` in a terminal outside any agent "
                 "session to approve the next run"),
}


def stop_problem(stop: Mapping | None) -> LoginProblem | None:
    """A recorded stop as a refusal: its cause, and its kind's one remedy."""
    if not stop:
        return None
    kind, remedy = STOP_REMEDIES.get(str(stop.get("kind")), STOP_REMEDIES["billing"])
    article = "an" if str(stop.get("kind")).startswith(("a", "e", "i", "o", "u")) else "a"
    return _problem(f"{article} {stop.get('kind')} stop is recorded in the Copilot harness home "
                    f"({stop.get('cause')}, {stop.get('at')})", remedy, kind)


# ---------- the preflight (Decisions 6, 7 and 13) -----------------------------------------------


@dataclass(frozen=True)
class Check:
    """One preflight row: its name, what refuses (None when it passes), a short
    detail for `--preflight-only`, and whether the refusal is a billing row."""

    name: str
    problem: LoginProblem | None = None
    detail: str = "ok"
    billing: bool = False


@dataclass
class Run:
    """What one run's preflight and run share. `token` is filled by the token
    check, `before` and `roster` under the lock."""

    environ: Mapping[str, str]
    root: Path
    home: Path
    token: str | None = None
    ws: Path | None = None
    scratch: Path | None = None
    scenario: Mapping = field(default_factory=dict)
    model: str | None = None
    effort: str | None = None
    cap: int = MIN_AI_CREDITS
    before: Status | None = None
    roster: list[str] = field(default_factory=list)
    # the workspace directory's device and inode before any child starts in it
    ws_id: tuple[int, int] | None = None


def new_run(environ: Mapping[str, str] | None = None, **fields) -> Run:
    environ = os.environ if environ is None else environ
    root = host_login.state_root(environ)
    return Run(environ, root, root / "hosts" / COPILOT.name, **fields)


def _location_check(run: Run) -> Check:
    return Check("location", host_login.check_location(run.root, run.environ, record=COPILOT))


def _presence_check(run: Run) -> Check:
    return Check("home", host_login.check_presence(run.home, COPILOT))


def _clean_check(run: Run) -> Check:
    return Check("clean", host_login.check_copilot_home(run.home))


def _token_check(run: Run) -> Check:
    found = token_env(run.home, strict=False)
    if isinstance(found, LoginProblem):
        return Check("token", found)
    run.token = found[COPILOT.token_env]  # type: ignore[index]
    return Check("token", detail="present, fine-grained")


def _version_check(run: Run) -> Check:
    version = installed_version(run.home, run.environ, run.token)
    return Check("version", check_copilot_version(version), host_login.version_text(version))


def _stop_check(run: Run) -> Check:
    """A recorded stop of any kind. It reads only the status snapshot file and
    starts nothing, so it comes before the first Copilot child (the version
    check), and runs again under the run lock (`run_copilot`)."""
    stop = read_stop(run.home)
    problem = stop_problem(stop)
    return Check("stop", problem, f"{stop.get('kind')} ({stop.get('cause')})" if stop else "none",
                 billing=bool(stop) and stop.get("kind") == "billing")


def managed_problem(paths: Sequence[str | Path] = MANAGED_SETTINGS) -> LoginProblem | None:
    """A machine-wide managed settings source of the client exists."""
    found = [str(p) for p in paths if Path(p).exists()]
    if not found:
        return None
    return _problem(f"a machine-wide managed settings source of the client exists: "
                    f"{', '.join(found)}", "report it: a managed policy can override the "
                    "harness's pinned settings", "isolation")


def _managed_check(_run: Run) -> Check:
    return Check("managed_settings", managed_problem())


def sandbox_problem(which: Callable[[str], str | None] = shutil.which,
                    platform: str = sys.platform) -> LoginProblem | None:
    """Every tool the platform's sandbox needs is installed (Linux:
    SANDBOX_TOOLS). macOS is allowed and unverified; Windows never reaches
    here (a usage error)."""
    if not platform.startswith("linux"):
        return None
    missing = [tool for tool in SANDBOX_TOOLS if which(tool) is None]
    if not missing:
        return None
    return _problem(f"the Copilot sandbox needs {', '.join(missing)} on PATH, which is not "
                    "installed", f"install {', '.join(missing)} through your package manager",
                    "precondition")


def _sandbox_check(run: Run) -> Check:
    path = run.environ.get("PATH")
    return Check("sandbox_tools", sandbox_problem(partial(shutil.which, path=path)))


def machine_problem(environ: Mapping[str, str]) -> LoginProblem | None:
    """The preflight rows that need neither the home nor a scenario: a
    machine-wide managed settings source, then the sandbox tools on the
    environment's `PATH`. The status command (and so the login) reports
    ready only when they pass, as a run's preflight would."""
    return managed_problem() or sandbox_problem(partial(shutil.which, path=environ.get("PATH")))


PREFLIGHT: tuple[Callable[[Run], Check], ...] = (
    _location_check, _presence_check, _clean_check, _token_check, _stop_check, _version_check,
    _managed_check, _sandbox_check)
# The rows whose refusal leaves every later read safe to start: `--preflight-only`
# prints them and goes on, so every check that can run does (spec: Copilot
# preflight only). Any other refusal makes a later start unsafe — a child under
# a refused location or in an unclean home, without the token, on another CLI
# version, under a managed policy or beside the parent folders' files — and
# ends the report. A run (`_require`) stops at the first refusal of any row.
REPORTED = frozenset({"stop", "sandbox_tools", "status", "model", "rosters"})


def preflight_checks(run: Run) -> Iterator[Check]:
    """The checks before the lock, in order (Decision 6). Nothing spawns before
    the location, the marker and the mode pass: `--version` unpacks the
    package under the state root. The token check comes before the version
    check, so that every Copilot child, the version check included, carries
    the token, and a recorded stop refuses before that first child starts.
    A failing row ends the sequence unless it is one `--preflight-only`
    prints and passes (REPORTED)."""
    for step in PREFLIGHT:
        check = step(run)
        yield check
        if check.problem and check.name not in REPORTED:
            return


# -- the workspace and its parent folders (Decision 7) --

STAGED_DIR = ".agents/skills"
SCAN_PATHS = (
    ".agents/skills", ".github/skills", ".claude/skills",
    "AGENTS.md", "CLAUDE.md", ".claude/CLAUDE.md", "GEMINI.md",
    ".github/copilot-instructions.md", ".github/instructions",
    ".github/agents", ".claude/agents", ".claude/rules",
    ".github/hooks", ".github/copilot/settings.json", ".github/copilot/settings.local.json",
    ".github/allowed_models.txt",
    ".claude/settings.json", ".mcp.json", ".github/mcp.json", ".github/extensions",
)


def scan_parents(ws: PurePath, exists: Callable[[PurePath], bool], *, account: PurePath,
                 repo: PurePath, temps: Iterable[PurePath] = ()) -> list[str]:
    """Pure over `exists`: every skill directory other than the staged one, and
    every instruction, agent, rule, hook, MCP or client settings file the
    client reads, in the workspace or any parent folder up to `/` — and a
    workspace inside the operator's home, the repository or a temporary
    directory the sandbox denies (`temps`; the work directory keeps it out,
    Decision 7)."""
    found = [f"the workspace {ws} lies inside {root}" for root in (account, repo, *temps)
             if ws == root or root in ws.parents]
    for level in (ws, *ws.parents):
        found += [str(level / rel) for rel in SCAN_PATHS
                  if not (level == ws and rel == STAGED_DIR) and exists(level / rel)]
    return found


def scan_problem(ws: Path, account: Path | None = None, repo: Path = REPO,
                 temps: Iterable[str | Path] | None = None) -> LoginProblem | None:
    account = host_login.account_home() if account is None else account
    temps = host_login.temp_dirs() if temps is None else temps
    found = scan_parents(ws.resolve(), lambda p: Path(p).exists(), account=account.resolve(),
                         repo=repo.resolve(), temps=[Path(t).resolve() for t in temps])
    if not found:
        return None
    return _problem(f"the workspace is not isolated: {'; '.join(found)}",
                    "report it: the runner placed the workspace where the client reads files "
                    "it must not", "isolation")


# -- the rosters --


def _source(entry: object) -> str | None:
    if not isinstance(entry, dict):
        return None
    value = entry.get("source") or entry.get("sourceType") or entry.get("kind")
    return str(value).lower() if value else None


def _skill_extras(skills: list, staged: set[str]) -> list[str]:
    extras = []
    for entry in skills:
        name = str(entry.get("name")) if isinstance(entry, dict) else repr(entry)
        source = _source(entry)
        if (name in staged and source == "project") or (
                name in BUILTIN_SKILLS and source == "builtin"):
            continue
        extras.append(f"{name} (source {source or 'unreported'})")
    return extras


def roster_problem(skills: object, mcps: object, staged: Iterable[str]) -> LoginProblem | None:
    """The client's listings, taken in the run's environment and working
    directory, name exactly the staged skills (source `project`) and bundled
    ones, and no MCP server beyond the built-in ones (source `builtin`). Pure."""
    staged = set(staged)
    if not isinstance(skills, list):
        return _problem("the client's skill listing is not a JSON list", UNAVAILABLE_REMEDY,
                        "precondition")
    extras = _skill_extras(skills, staged)
    if extras:
        return _problem(f"the client's skill listing names skills beyond the staged and bundled "
                        f"ones: {', '.join(extras)}", "report it: a skill outside the "
                        "workspace's skill directory reached the run", "isolation")
    listed = {str(e.get("name")) for e in skills if isinstance(e, dict)}
    if staged - listed:
        return _problem(f"the client's skill listing omits the staged "
                        f"{', '.join(sorted(staged - listed))}", UNAVAILABLE_REMEDY, "precondition")
    servers = mcps.get("mcpServers") if isinstance(mcps, dict) else None
    if not isinstance(servers, dict):
        return _problem("the client's MCP listing carries no server map", UNAVAILABLE_REMEDY,
                        "precondition")
    foreign = sorted(name for name, entry in servers.items()
                     if name not in BUILTIN_MCP or _source(entry) != "builtin")
    if foreign:
        return _problem(f"the client's MCP listing names servers outside the built-in ones: "
                        f"{', '.join(foreign)}", "report it: the home configures no MCP server",
                        "isolation")
    return None


def _listing(args: Sequence[str], run: Run) -> object:
    _, out, _ = short([*args, "--json"], home=run.home, scratch=run.scratch,  # type: ignore[arg-type]
                      token=run.token, environ=run.environ, cwd=run.ws)
    with suppress(ValueError):
        return json.loads(out)
    return None


def staged_names(ws: Path) -> list[str]:
    root = ws / ".agents" / "skills"
    return sorted(p.name for p in root.iterdir() if p.is_dir()) if root.is_dir() else []


# -- the confinement probe (Decision 13) --

# `harness_environ` reads the harness's own process, which keeps every inherited
# variable the child builder drops (GH_TOKEN and the like, if exported): denied
# only when the sandbox hides the host's processes, whatever the client
# process's own dumpability says about `client_environ`
READ_TARGETS = {"token_file": "the token file",
                "client_environ": "the client process's environment",
                "harness_environ": "the harness process's environment",
                "ssh_dir": "the operator's ~/.ssh", "gh_config": "the operator's ~/.config/gh"}
AUTH_TARGETS = {"gh_token": "the GitHub CLI's token over the session bus",
                "git_credential": "git's stored credential for github.com"}
RUN_TARGETS = {"python": "the skills' interpreter (python3)",
               "skill_script": "a staged skill script"}
# The host's shared /tmp, refused since the user's decision D-b (2026-10-06;
# K6 had read them `readable` and `writable`): a file the harness put there
# must read `denied`, and a file the shell writes there must not reach the
# host — `tmp_write` is judged on the host after the probe (`_row_output`),
# because a write into a denied directory lands in the sandbox's own throwaway
# layer and exits 0 (measured), so only the host can tell.
TMP_TARGETS = {"host_tmp": "a file in the host's /tmp",
               "tmp_write": "a write into the host's /tmp"}
REQUIRED_PROBES = (*READ_TARGETS, *AUTH_TARGETS, "python", *TMP_TARGETS)
# Measured and printed, not yet refused (Decision 13, network): whether the
# sandboxed shell shares the harness's network namespace (`shared` or
# `private`). K6 read `private`; a rule on it is a change of its own.
MEASURED_TARGETS = {"net_ns": "the harness's network namespace"}
# the host's own /tmp and the harness's network namespace (Linux paths, read on
# the host; the probe runs only where the client's sandbox does)
PROBE_TMP = "/tmp"
NET_NS = "/proc/self/ns/net"


@dataclass(frozen=True)
class ProbeResult:
    """One probe command's one-word output (`denied`, `readable`, or an exit
    code) and whether the client reported it as sandboxed."""

    name: str
    output: str | None
    sandboxed: bool | None


@dataclass(frozen=True)
class ProbeHost:
    """What the probe's measured rows compare against on the host: the
    harness's own network namespace (`/proc/self/ns/net`), a file the harness
    wrote into the host's /tmp, and the name the `tmp_write` row writes to.
    Each is None where it cannot be had, and its row is then left out."""

    net_ns: str | None = None
    sentinel: Path | None = None
    marker: Path | None = None


def _measured_commands(host: ProbeHost) -> list[tuple[str, str]]:
    q = shlex.quote
    commands = []
    if host.net_ns:
        commands.append(("net_ns", "n=$(readlink /proc/self/ns/net 2>/dev/null); "
                                   f"if [ -z \"$n\" ]; then echo unknown; elif [ \"$n\" = "
                                   f"{q(host.net_ns)} ]; then echo shared; else echo private; fi"))
    if host.sentinel:
        commands.append(("host_tmp", f"cat {q(str(host.sentinel))} >/dev/null 2>&1 && echo "
                                     "readable || echo denied"))
    if host.marker:
        commands.append(("tmp_write", f": > {q(str(host.marker))} 2>/dev/null; echo $?"))
    return commands


def probe_commands(*, token_file: Path, server_pid: int, harness_pid: int, account: Path,
                   uid: int, script: Path | None,
                   host: ProbeHost | None = None) -> list[tuple[str, str]]:
    """The probe's fixed commands. Each discards its own output and prints one
    word or its exit code, so no output of the target ever leaves the sandbox.
    `git credential fill` runs with the operator's real home, configuration,
    GitHub CLI directory and session bus, as a command in the sandbox could
    set them, so that a credential helper the operator configured (such as
    `gh auth git-credential`) is reached unless the sandbox denies it; the
    child's own scratch home holds no helper and would prove nothing."""
    readable = "{} >/dev/null 2>&1 && echo readable || echo denied"
    q = shlex.quote
    bus = f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus"
    operator = (f"HOME={q(str(account))} XDG_CONFIG_HOME={q(str(account / '.config'))} "
                f"GH_CONFIG_DIR={q(str(account / '.config' / 'gh'))} {bus}")
    commands = [
        ("token_file", readable.format(f"cat {q(str(token_file))}")),
        ("client_environ", readable.format(f"cat /proc/{server_pid}/environ")),
        ("harness_environ", readable.format(f"cat /proc/{harness_pid}/environ")),
        ("ssh_dir", readable.format(f"ls -A {q(str(account / '.ssh'))}")),
        ("gh_config", readable.format(f"ls -A {q(str(account / '.config' / 'gh'))}")),
        ("gh_token", f"{bus} gh auth token --hostname github.com >/dev/null 2>&1; echo $?"),
        ("git_credential", "printf 'protocol=https\\nhost=github.com\\n\\n' | "
                           f"{operator} GIT_TERMINAL_PROMPT=0 GIT_ASKPASS=/bin/false "
                           "GCM_INTERACTIVE=never git credential fill >/dev/null 2>&1; echo $?"),
        ("python", "python3 -c 'print(1)' >/dev/null 2>&1; echo $?"),
    ]
    if script is not None:
        commands.append(("skill_script", f"python3 {q(str(script))} --help >/dev/null 2>&1; "
                                         "echo $?"))
    return commands + _measured_commands(host or ProbeHost())


def _exit_code(output: str | None) -> int | None:
    with suppress(TypeError, ValueError):
        return int(str(output).strip())
    return None


PROBE_REPORT = ("report it, and leave every Copilot run refused: the sandbox's deny list does "
                "not hold (a deny-list change goes through openspec-update-change)")
UNAPPLIED_REPORT = ("report it, and leave every Copilot run refused: the client's sandbox for its "
                    "sessions is not the pinned one (a change goes through openspec-update-change)")


@dataclass(frozen=True)
class Probe:
    """What the confinement probe found (Decision 13): the host's sandbox
    support, why the pinned sandbox block was not applied to the probe's
    session (None when it was), and each command's result."""

    supported: object = None
    unapplied: str | None = None
    results: tuple[ProbeResult, ...] = ()


def probe_problem(results: Sequence[ProbeResult], supported: object = True,
                  unapplied: str | None = None) -> LoginProblem | None:
    """Pure over the probe's results (Decision 13). A session the pinned
    sandbox block was not applied to refuses for isolation, before any row;
    so does any target readable, a host /tmp row other than `denied`,
    `gh`/`git` authentication that exits 0, or a command the client did not
    report as sandboxed. A probe that could not run, or a skill line that
    fails, refuses as a precondition. The message names the targets, never
    any output."""
    if supported is not True:
        return _problem("the client reports that this host cannot run its sandbox",
                        f"install {', '.join(SANDBOX_TOOLS)} and check that `bwrap --ro-bind / "
                        "/ --dev /dev true` works", "precondition")
    if unapplied:
        return _problem(f"the confinement probe could not put its session in the pinned sandbox: "
                        f"{unapplied}", UNAPPLIED_REPORT, "isolation")
    by = {r.name: r for r in results}
    missing = [name for name in REQUIRED_PROBES if by.get(name) is None or by[name].output is None]
    if missing:
        return _problem(f"the confinement probe gave no answer for {', '.join(missing)}",
                        UNAVAILABLE_REMEDY, "precondition")
    reached = [label for name, label in {**READ_TARGETS, **TMP_TARGETS}.items()
               if by[name].output != "denied"]
    reached += [label for name, label in AUTH_TARGETS.items() if _exit_code(by[name].output) in (
        None, 0)]
    if reached:
        return _problem(f"the confinement probe reached {', '.join(reached)} from the sandboxed "
                        "shell", PROBE_REPORT, "isolation")
    loose = sorted(name for name, r in by.items() if r.sandboxed is not True)
    if loose:
        return _problem(f"the client did not report the probe's commands as sandboxed "
                        f"({', '.join(loose)})", PROBE_REPORT, "isolation")
    failed = [label for name, label in RUN_TARGETS.items()
              if name in by and _exit_code(by[name].output) != 0]
    if failed:
        return _problem(f"the confinement probe could not run {', '.join(failed)} inside the "
                        "sandbox", "report it: the deny list would fail the skills rather than "
                        "confine them (a deny-list change goes through openspec-update-change)",
                        "precondition")
    return None


def _probe_script(ws: Path) -> Path | None:
    scripts = sorted((ws / ".agents" / "skills").glob("*/scripts/*.py"))
    return scripts[0] if scripts else None


def _completions(notes: Iterable[dict]) -> dict[str, dict]:
    done = {}
    for note in notes:
        params = note.get("params") if note.get("method") == "session.event" else None
        event = params.get("event") if isinstance(params, dict) else None
        if isinstance(event, dict) and event.get("type") == "tool.execution_complete":
            data = event.get("data") if isinstance(event.get("data"), dict) else {}
            done[str(data.get("toolCallId"))] = data
    return done


def _client_sandbox(rpc: Rpc, run: Run, deadline: float) -> tuple[object, str | None]:
    """The sandbox block the client itself reads from the home
    (`user.settings.get`: `settings.sandbox.value`, `settings.json` overlaid
    with `config.json`), and why it cannot be applied: no answer, or a block
    other than the pinned one. Compared, never printed."""
    reply = rpc.call("user.settings.get", {}, deadline)
    failure = _reply_failure(reply, "user.settings.get")
    if failure:
        return None, failure
    found: object = reply.get("result")  # type: ignore[union-attr]
    for key in ("settings", "sandbox", "value"):
        found = found.get(key) if isinstance(found, dict) else None
    pinned = host_login.pinned_settings(run.home, host_login.account_home())["sandbox"]
    return found, (None if found == pinned else
                   "the client reads a sandbox block other than the pinned one")


def _apply_sandbox(rpc: Rpc, session_id: str, block: object, deadline: float) -> str | None:
    """Put the session in the sandbox the way prompt mode does: the headless
    server never applies the home's `sandbox` block to a session it creates,
    and `--sandbox` on the server changes nothing (K6, 2026-10-06); prompt mode
    loads the block and sends it with `session.options.update` (`Njt`, app.js
    4947448). Why it was not applied, or None."""
    reply = rpc.call("session.options.update",
                     {"sessionId": session_id, "sandboxConfig": block,
                      "sandboxConfigSource": SANDBOX_SOURCE}, deadline)
    failure = _reply_failure(reply, "session.options.update")
    if failure:
        return failure
    result = reply.get("result")  # type: ignore[union-attr]
    if not isinstance(result, dict) or result.get("success") is not True:
        return "session.options.update did not report success"
    return None


def _own_net_ns() -> str | None:
    with suppress(OSError):
        return str(Path(NET_NS).readlink())
    return None


@contextmanager
def probe_host(tmp: Path | str | None = None) -> Iterator[ProbeHost]:
    """The host side of the probe's host rows: the harness's own network
    namespace (`net_ns`, measured), a file written into the host's /tmp
    (PROBE_TMP) for `host_tmp`, and a free name beside it for `tmp_write`
    (both refusing since D-b); both files removed afterwards. Without a /tmp
    the two rows are left out, which `probe_problem` reads as no answer."""
    tmp = Path(PROBE_TMP if tmp is None else tmp)
    if not tmp.is_dir():
        yield ProbeHost(_own_net_ns())
        return
    fd, name = tempfile.mkstemp(prefix="devrun-probe-tmp-", dir=tmp)
    os.close(fd)
    sentinel = Path(name)
    marker = sentinel.with_name(sentinel.name.replace("devrun-probe-tmp-", "devrun-probe-write-"))
    try:
        yield ProbeHost(_own_net_ns(), sentinel, marker)
    finally:
        for path in (sentinel, marker):
            with suppress(OSError):
                path.unlink()


def _row_output(name: str, result: dict, host: ProbeHost) -> str | None:
    """A probe row's one word: the last line of its output — except
    `tmp_write`, which the harness judges on the host, since a write into the
    sandbox's own overlay succeeds and reaches nothing."""
    if name == "tmp_write" and host.marker is not None:
        return "writable" if os.path.lexists(host.marker) else "denied"
    text = str(result.get("output") or "").strip()
    return text.splitlines()[-1] if text else None


def _probe_rows(rpc: Rpc, run: Run, session_id: str, pid: int, deadline: float,
                host: ProbeHost | None = None) -> tuple[ProbeResult, ...]:
    host = host or ProbeHost()
    uid = os.getuid() if hasattr(os, "getuid") else 0
    calls = []
    for name, command in probe_commands(token_file=host_login.token_path(run.home),
                                        server_pid=pid, harness_pid=os.getpid(),
                                        account=host_login.account_home(),
                                        uid=uid, script=_probe_script(run.ws),  # type: ignore[arg-type]
                                        host=host):
        reply = rpc.call("session.shell.executeUserRequested",
                         {"sessionId": session_id, "requestId": uuid.uuid4().hex,
                          "command": command}, deadline)
        result = reply.get("result") if isinstance(reply, dict) else None
        calls.append((name, result if isinstance(result, dict) else {}))
    ids = {str(result.get("toolCallId")) for _, result in calls if result.get("toolCallId")}
    rpc.drain(lambda: ids <= set(_completions(rpc.notes)), min(deadline, time.monotonic() + 5))
    done = _completions(rpc.notes)
    return tuple(ProbeResult(name, _row_output(name, result, host),
                             done.get(str(result.get("toolCallId")), {}).get("sandboxed"))
                 for name, result in calls)


def _probe_session(rpc: Rpc, run: Run, session_id: str, pid: int, deadline: float) -> Probe:
    """The block the client reads, which must be the pinned one, before any
    session exists; then the session, the block applied to it, and the fixed
    commands. A block that was not applied runs no command; the session is
    deleted whatever happened after its creation."""
    block, why = _client_sandbox(rpc, run, deadline)
    if why:
        return Probe(True, why)
    created = rpc.call("session.create", {"sessionId": session_id,
                                          "workingDirectory": str(run.ws), "model": run.model},
                       deadline)
    if _reply_failure(created, "session.create"):
        return Probe(True)
    try:
        why = _apply_sandbox(rpc, session_id, block, deadline)
        if why:
            return Probe(True, why)
        with probe_host() as host:
            return Probe(True, None, _probe_rows(rpc, run, session_id, pid, deadline, host))
    finally:
        rpc.call("session.delete", {"sessionId": session_id}, deadline)


def confinement_probe(run: Run) -> Probe:
    """Under the lock and after the rosters: a headless server in the run's
    environment; `sandbox.getHostSupport`; the sandbox block the client reads
    from the home, which must equal the pinned one; a session with the
    workspace as its working directory, put in that sandbox with
    `session.options.update` as prompt mode does; and the fixed commands
    through `session.shell.executeUserRequested` — model-free. The probe's
    session folder is deleted afterwards."""
    session_id = str(uuid.uuid4())
    proc = spawn(headless(run.scratch, run.token), home=run.home,  # type: ignore[arg-type]
                 cwd=run.ws, scratch=run.scratch, token=run.token,  # type: ignore[arg-type]
                 environ=run.environ,
                 stdin=subprocess.PIPE, text=False)
    try:
        rpc = Rpc(proc)
        deadline = time.monotonic() + PROBE_TIMEOUT_S
        if _reply_failure(handshake(rpc, deadline), "connect"):
            return Probe(True)
        support = rpc.call("sandbox.getHostSupport", {}, deadline)
        result = support.get("result") if isinstance(support, dict) else None
        supported = result.get("supported") if isinstance(result, dict) else None
        if supported is not True:
            return Probe(supported)
        return _probe_session(rpc, run, session_id, proc.pid, deadline)
    finally:
        _close(proc)
        shutil.rmtree(run.home / SESSION_STATE / session_id, ignore_errors=True)


# -- the checks under the lock --


def _status_check(run: Run) -> Check:
    run.before = read_status(run.home, run.environ, token=run.token, models=True)
    write_snapshot(run.home, run.before)
    problem, billing = status_rows(run.before)
    snap = run.before.snapshot
    detail = (f"overage count {snap.overage_count}, {snap.percent_remaining}% remaining"
              if snap else run.before.error or "no snapshot")
    return Check("status", problem, detail, billing=billing and problem is not None)


def _model_check(run: Run) -> Check:
    return Check("model", _model_problem(run.before, run.model, run.effort),  # type: ignore[arg-type]
                 f"{run.model} {run.effort or ''}".strip())


def _roster_check(run: Run) -> Check:
    skills = _listing(["skill", "list"], run)
    mcps = _listing(["mcp", "list"], run)
    run.roster = sorted(str(e.get("name")) for e in skills if isinstance(e, dict)) if isinstance(
        skills, list) else []
    return Check("rosters", roster_problem(skills, mcps, staged_names(run.ws)),  # type: ignore[arg-type]
                 ", ".join(run.roster))


def _probe_check(run: Run) -> Check:
    probe = confinement_probe(run)
    detail = ", ".join(f"{r.name} {r.output}{'' if r.sandboxed else ' (not sandboxed)'}"
                       for r in probe.results) or probe.unapplied or "no results"
    return Check("confinement_probe",
                 probe_problem(probe.results, probe.supported, probe.unapplied), detail)


def _reads_clean_check(run: Run) -> Check:
    """The clean-home check on the home as the gate's reads left it: the status
    read, the listings and the probe now run authenticated, and where the
    client's caches land is not derivable from the package (design, facts
    measured after the first login), so an entry or a state key one of them
    wrote refuses this run, not only the next one."""
    return Check("clean_after_reads", host_login.check_copilot_home(run.home))


GATE: tuple[Callable[[Run], Check], ...] = (_status_check, _model_check, _roster_check,
                                           _probe_check)
# what a run reads again once it holds the lock, before any child: the rows the
# lock's other holders change (a stop recorded by another run or a login, the
# token a login replaced)
LOCKED: tuple[Callable[[Run], Check], ...] = (_stop_check, _token_check)


def gate_checks(run: Run) -> Iterator[Check]:
    """Under one hold of the run lock: the status read and its billing guard,
    the model listing, the rosters, then the confinement probe (Decision 6).
    A refusal ends those reads unless `--preflight-only` prints and passes it
    (REPORTED): each of these is model-free. Whatever ended them, the last row
    is the clean-home check on the home as they left it (`_reads_clean_check`),
    which starts nothing and is never passed over: a run stops at it before
    its prompt-mode child, and `--preflight-only` prints it for K3."""
    for step in GATE:
        check = step(run)
        yield check
        if check.problem and check.name not in REPORTED:
            break
    yield _reads_clean_check(run)


def _require(checks: Iterable[Check]) -> None:
    for check in checks:
        if check.problem:
            raise CopilotRefused.of(check.problem,
                                    billing=check.problem.cause if check.billing else None)


def isolated_home(_stack, _args: argparse.Namespace,
                  environ: Mapping[str, str] | None = None) -> Path:
    """The Copilot home a run executes in, after the checks before the lock;
    refused as untested otherwise. Every Copilot run is isolated."""
    run = new_run(environ)
    _require(preflight_checks(run))
    return run.home


# ---------- the command (design Decision 8) -----------------------------------------------------


def available_tools(helpers: bool, network: bool) -> tuple[str, ...]:
    return (*BASE_TOOLS, *(HELPER_TOOLS if helpers else ()), *(NETWORK_TOOLS if network else ()))


def url_hosts(scenario: Mapping) -> list[str]:
    """The URL approvals of a network scenario: a served fixture's local host,
    and the hosts its skills' scripts contact (SKILL_HOSTS). Pure."""
    if not needs_network(scenario):
        return []
    skills = [scenario.get("skill"), *scenario.get("siblings", ())]
    hosts = {host for skill in skills for host in SKILL_HOSTS.get(str(skill), ())}
    return sorted(hosts | ({LOCAL_FIXTURE_HOST} if scenario.get("serve") else set()))


def command(scenario: Mapping, prompt: str, *, model: str, effort: str | None, session_id: str,
            log_dir: Path, cap: int) -> list[str]:
    """The prompt-mode invocation (Decision 8): the JSON event stream, streaming
    and colour off, a session the harness names, the model verbatim, an
    allowlisted tool set per scenario, the denials, every disabling switch,
    the sandbox, the secret token variable, scratch logs and the credit cap.
    Never `--allow-all-urls`, `--add-dir`, `--plugin-dir`, `--allow-all-paths`,
    `--enable-memory`, `--share`, `--agent`, `--resume` or `--continue`."""
    network = needs_network(scenario)
    argv = [COPILOT.binary, "-p", prompt, "--output-format", "json", "--stream", "off",
            "--no-color", f"--session-id={session_id}", "--model", model]
    if effort:
        argv += ["--reasoning-effort", effort]  # `--effort` at 1.0.67
    tools = available_tools(bool(scenario.get("helpers")), network)
    argv += ["--allow-all-tools", f"--available-tools={','.join(tools)}"]
    argv += [f"--deny-tool={tool}" for tool in DENIED_TOOLS]
    argv += [f"--allow-url={host}" for host in url_hosts(scenario)]
    return [*argv, *SWITCHES, "--log-level", "warning", "--log-dir", str(log_dir),
            "--max-ai-credits", str(cap)]


# ---------- the session file (Decision 9) -------------------------------------------------------

SHUTDOWN_KEYS = ("shutdownType", "errorReason", "totalPremiumRequests", "totalNanoAiu",
                 "modelMetrics")


def sandbox_warned(text: str) -> bool:
    """A client message saying the sandbox did not engage: one of the V-pass's
    phrases, in a message about the sandbox."""
    lowered = text.lower()
    return "sandbox" in lowered and any(phrase.lower() in lowered for phrase in SANDBOX_WARNINGS)


def _notice_kind(message: str) -> str | None:
    if EFFORT_UNAPPLIED.search(message):
        return "effort_unapplied"
    return "sandbox" if sandbox_warned(message) else None


def _reduce_notice(kind_: str, data: dict) -> list[dict]:
    message = str(data.get("message") or "")
    notice = _notice_kind(message)
    return [{"type": "copilot.notice", "kind": notice, "event": kind_,
             "message": message[:300]}] if notice else []


SESSION_REDUCERS: dict[str, Callable[[str, dict], list[dict]]] = {
    "session.start": lambda _k, d: [{"type": "copilot.session_start",
                                     "copilotVersion": d.get("copilotVersion")}],
    "skill.invoked": lambda _k, d: [{"type": "copilot.skill_invoked",
                                     **{key: d.get(key) for key in ("name", "path", "source",
                                                                    "trigger")}}],
    "session.shutdown": lambda _k, d: [{"type": "copilot.shutdown",
                                        **{key: d.get(key) for key in SHUTDOWN_KEYS}}],
    "session.model_change": lambda _k, d: [{"type": "copilot.model_change",
                                            **{key: d.get(key) for key in (
                                                "cause", "previousModel", "newModel")}}],
    "session.warning": _reduce_notice, "session.error": _reduce_notice,
    "session.info": _reduce_notice,
}


def reduce_session(lines: Iterable[str]) -> list[dict]:
    """Only the fields the readers use (Decision 9): the CLI version, each skill
    invocation's name, path, source and trigger (never its SKILL.md text),
    the shutdown's consumption, model changes, the type alone of each hook
    event, and the sandbox and effort notices. `system.message`, prompts and
    unknown fields are dropped; a torn line is skipped."""
    records = []
    for line in lines:
        with suppress(ValueError):
            event = json.loads(line)
            if not isinstance(event, dict):
                continue
            kind_ = str(event.get("type"))
            data = event.get("data") if isinstance(event.get("data"), dict) else {}
            if kind_.startswith("hook."):
                records.append({"type": "copilot.hook", "event": kind_})
            elif kind_ in SESSION_REDUCERS:
                records += SESSION_REDUCERS[kind_](kind_, data)
    return records


def capture_session(home: Path, session_id: str, token: str | None) -> tuple[list[dict], bool]:
    """Reduce `session-state/<uuid>/events.jsonl` (its path is known even after
    a timeout), scrubbed first, and delete the session's folder."""
    folder = home / SESSION_STATE / session_id
    try:
        text = (folder / "events.jsonl").read_text(encoding="utf-8", errors="replace")
    except OSError:
        text = ""
    finally:
        shutil.rmtree(folder, ignore_errors=True)
    text, hit = scrub(text, token)
    return reduce_session(text.splitlines()), hit


# ---------- canonical tool calls (Decision 10) ---------------------------------------------------

SHELL_TOOLS = frozenset({"bash", "read_bash", "write_bash", "stop_bash", "list_bash",
                         "local_shell", "powershell", "read_powershell", "write_powershell",
                         "stop_powershell", "list_powershell"})
EDIT_TOOLS = frozenset({"edit", "create", "apply_patch", "str_replace", "insert"})
INTERNAL_TOOLS = frozenset({"report_intent", "update_todo", "task_complete", "store_memory",
                            "ask_user", "sql", "fetch_copilot_cli_documentation"})
UNKNOWN = "copilot:"
_SKILL_FILE = re.compile(r"\.agents/skills/(proposal-[a-z-]+)/SKILL\.md$")


def _skill_call(args: dict, done: dict | None) -> tuple[str, dict]:
    name = str(args.get("skill") or "").split(":")[-1]
    failed = done is not None and done.get("success") is False
    return ("SkillAttempt" if failed else "Skill", {"skill": name})


def _view_call(args: dict, _done: dict | None) -> tuple[str, dict]:
    path = str(args.get("path") or "")
    read = _SKILL_FILE.search(path)
    return ("Read", {"file_path": path, **({"skill_file_read": read[1]} if read else {})})


CALLS: dict[str, Callable[[dict, dict | None], tuple[str, dict]]] = {
    **{name: lambda a, _d: ("Bash", {"command": str(a.get("command") or "")})
       for name in SHELL_TOOLS},
    **{name: lambda a, _d: ("Edit", a) for name in EDIT_TOOLS},
    "view": _view_call,
    "glob": lambda a, _d: ("Glob", {"pattern": a.get("pattern")}),
    "grep": lambda a, _d: ("Grep", {"pattern": a.get("pattern")}),
    "rg": lambda a, _d: ("Grep", {"pattern": a.get("pattern")}),
    "skill": _skill_call,
    "task": lambda a, _d: ("Agent", {"prompt": str(a.get("prompt") or "")}),
    "web_fetch": lambda a, _d: ("WebFetch", {"url": a.get("url")}),
    "web_search": lambda a, _d: ("WebSearch", {"query": a.get("query")}),
}


def _data(event: dict) -> dict:
    data = event.get("data")
    return data if isinstance(data, dict) else {}


def _starts(events: list[dict], top_level: bool) -> list[dict]:
    return [_data(e) for e in events if e.get("type") == "tool.execution_start"
            and not (top_level and _data(e).get("parentToolCallId"))]


def _done(events: list[dict]) -> dict[str, dict]:
    return {str(_data(e).get("toolCallId")): _data(e) for e in events
            if e.get("type") == "tool.execution_complete"}


def _canonical(start: dict, done: dict | None) -> tuple[str, dict] | None:
    name = str(start.get("toolName") or "")
    args = start.get("arguments") if isinstance(start.get("arguments"), dict) else {}
    if start.get("mcpServerName"):
        return (f"mcp__{start['mcpServerName']}__{start.get('mcpToolName') or name}", args)
    if name in CALLS:
        return CALLS[name](args, done)
    return None if name in INTERNAL_TOOLS else (f"{UNKNOWN}{name}", {})


def copilot_tool_calls(events: list[dict]) -> list[tuple[str, dict]]:
    """(canonical tool name, input) per top-level Copilot tool call, in order,
    paired with its completion by `toolCallId`. A Claude or Codex stream gives
    none (their shapes are `assistant` and `item.completed` events)."""
    done = _done(events)
    calls = (_canonical(start, done.get(str(start.get("toolCallId"))))
             for start in _starts(events, top_level=True))
    return [call for call in calls if call is not None]


def unknown_tools(events: list[dict], offered: Iterable[str]) -> list[str]:
    """Tool names neither offered to the run nor internal, at any level."""
    allowed = set(offered) | INTERNAL_TOOLS
    return sorted({str(s.get("toolName")) for s in _starts(events, top_level=False)
                   if not s.get("mcpServerName") and str(s.get("toolName")) not in allowed})


# ---------- readers and telemetry ---------------------------------------------------------------


def _last(events: list[dict], kind: str) -> dict:
    return next((e for e in reversed(events) if e.get("type") == kind), {})


def harness_record(events: list[dict]) -> dict:
    return _last(events, "copilot.harness")


def _messages(events: list[dict], top_level: bool = True) -> list[dict]:
    return [_data(e) for e in events if e.get("type") == "assistant.message"
            and not (top_level and _data(e).get("parentToolCallId"))]


def final_text(events: list[dict]) -> str:
    """The chat the verdicts read: the last top-level assistant message's text."""
    texts = [m.get("content") for m in _messages(events)]
    return next((t for t in reversed(texts) if isinstance(t, str) and t.strip()), "")


def _metrics(events: list[dict]) -> dict:
    metrics = _last(events, "copilot.shutdown").get("modelMetrics")
    return metrics if isinstance(metrics, dict) else {}


def served_models(events: list[dict]) -> list[str]:
    """The models the top-level messages and the per-model usage name. The
    session's creation options are never evidence (Decision 10)."""
    named = {str(m.get("model")) for m in _messages(events) if m.get("model")}
    return sorted(named | set(_metrics(events)))


USAGE_KEYS = {"tokens_in": "inputTokens", "tokens_out": "outputTokens",
              "tokens_cache_read": "cacheReadTokens", "tokens_cache_write": "cacheWriteTokens",
              "tokens_reasoning": "reasoningTokens"}


def _usage(events: list[dict]) -> dict[str, int]:
    totals = dict.fromkeys(USAGE_KEYS, 0)
    for metric in _metrics(events).values():
        usage = metric.get("usage") if isinstance(metric, dict) else None
        for key, name in USAGE_KEYS.items() if isinstance(usage, dict) else ():
            totals[key] += int(usage.get(name) or 0)
    return totals


def credits_used(events: list[dict]) -> float | None:
    """The run's consumption in AI credits: `totalNanoAiu / 1e9`; None without
    a shutdown record, or with one whose `totalNanoAiu` is not a number —
    consumption that cannot be read is never zero (`billing_after` stops on
    it)."""
    nano = _last(events, "copilot.shutdown").get("totalNanoAiu")
    return round(nano / NANO, 4) if _is_number(nano) else None


NOTICE_TYPES = ("session.warning", "session.error", "session.info")


def _notices(events: list[dict], kind: str) -> list[str]:
    """The sandbox or effort notices of a run, from stdout and the session file."""
    texts = [str(_data(e).get("message") or "") for e in events
             if e.get("type") in NOTICE_TYPES]
    found = [t for t in texts if _notice_kind(t) == kind]
    return found + [str(r.get("message")) for r in events
                    if r.get("type") == "copilot.notice" and r.get("kind") == kind]


def effort_served(events: list[dict], effort: str | None) -> str | None:
    if not effort:
        return None
    return "reported unapplied" if _notices(events, "effort_unapplied") else (
        "requested, not verified")


def _snapshot_value(record: object, key: str) -> object:
    return record.get(key) if isinstance(record, dict) else None


def copilot_telemetry(events: list[dict], args: argparse.Namespace) -> dict:
    """Copilot reports AI credits, not money: `cost_usd` is None, never zero,
    and the notional figure is the credits at one cent each, labelled."""
    harness = harness_record(events)
    credits = credits_used(events)
    effort = harness.get("effort") or getattr(args, "effort", None)
    return {
        "cost_usd": None,
        "ai_credits": credits,
        "notional_usd": round(credits * NOTIONAL_USD_PER_CREDIT, 4) if credits is not None
        else None,
        "notional_basis": "copilot credits, not billed",
        "num_turns": sum(1 for e in events if e.get("type") == "assistant.turn_end"),
        "duration_ms": harness.get("duration_ms"),
        **_usage(events),
        "premium_requests": _last(events, "copilot.shutdown").get("totalPremiumRequests"),
        "cap_credits": harness.get("cap") or getattr(args, "max_ai_credits", None),
        "overage_before": _snapshot_value(harness.get("before"), "overage_count"),
        "overage_after": _snapshot_value(harness.get("after"), "overage_count"),
        "remaining_before": _snapshot_value(harness.get("before"), "remaining_pct"),
        "remaining_after": _snapshot_value(harness.get("after"), "remaining_pct"),
        "effort_requested": effort,
        "effort_served": effort_served(events, effort),
        "models_used": served_models(events),
        "ignored_env": ignored_env(os.environ),
    }


def copilot_read(events: list[dict], args: argparse.Namespace) -> RunView:
    """The Copilot host's `RunView`: the last top-level assistant message, the
    requested model beside the served ones ("unreported" when none is named),
    the CLI version from the session file, and the telemetry."""
    models = served_models(events)
    requested = getattr(args, "model", None)
    check = (f"served {', '.join(models)}, requested {requested}"
             if requested and models and models != [requested] else None)
    return RunView(final_text(events), requested, ", ".join(models) or "unreported",
                   _last(events, "copilot.session_start").get("copilotVersion"),
                   copilot_telemetry(events, args), check)


# ---------- the checks after the run (spec: billing guard, host adapters) ------------------------

AUTH_ERRORS = ("authentication", "authorization")
LIMIT_ERRORS = ("quota", "rate_limit")
SOFT_CAP = "ai_credit_soft_cap_exhausted"


def _errors(events: list[dict]) -> list[dict]:
    return [_data(e) for e in events if e.get("type") == "session.error"]


def _error_text(error: dict) -> str:
    code = f" ({error['errorCode']})" if error.get("errorCode") else ""
    return f"{error.get('errorType') or 'error'}{code}: {error.get('message') or 'no message'}"


def soft_cap_reached(events: list[dict], cap: float) -> str | None:
    """The stream reports that the credit cap or the session limit was reached:
    the client's error, the run's credit cap, and the credits used and allowed
    where the client reports them."""
    error = next((e for e in _errors(events) if e.get("errorCode") == SOFT_CAP
                  or e.get("errorType") == "session_limits"), None)
    exhausted = _data(_last(events, "session_limits_exhausted.requested"))
    if error is None and not exhausted:
        return None
    used = (f", {exhausted.get('usedAiCredits')} of {exhausted.get('maxAiCredits')} credits "
            "used" if exhausted else "")
    what = _error_text(error) if error else "the session limit was reached"
    return f"{what} (the run's credit cap {cap:g}{used})"


def failure_reason(events: list[dict], returncode: int, stderr: str,
                   cap: float) -> RunProblem | None:
    """Why a run ended without a verdict, in this order: a token Copilot
    rejected (untested, the token remedy), a quota or rate limit (untested, a
    limit reached), the credit cap or session limit (untested; `billing_after`
    records the stop), any other session error (the event decides, not the
    exit code), a non-zero exit (the scrubbed stderr tail), and no closing
    result line. The untested ones read in the one refusal template, the
    not-affected note included."""
    errors = _errors(events)
    auth = next((e for e in errors if e.get("errorType") in AUTH_ERRORS), None)
    if auth:
        return RunProblem(refusal(_problem(f"copilot rejected the token ({_error_text(auth)})",
                                           host_login.COPILOT_TOKEN_REMEDY)), True, "subscription")
    limit = next((e for e in errors if e.get("errorType") in LIMIT_ERRORS), None)
    if limit:
        return RunProblem(refusal(_problem(
            f"copilot reported {_error_text(limit)}: limit reached, not a result",
            "rerun after the limit resets")), True, "subscription",
            billing=f"limit reached: {_error_text(limit)}")
    reached = soft_cap_reached(events, cap)
    if reached:
        return RunProblem(refusal(_problem(
            f"{reached}: limit reached, not a result",
            f"check github.com/settings/billing, run `{host_login.CLEAR_STOP_COMMAND}`, then "
            "rerun with a higher --max-ai-credits")), True, "subscription",
            billing=f"credit cap reached: {reached}")
    if errors:
        return RunProblem(f"copilot failed: {_error_text(errors[-1])}", False)
    if returncode != 0:
        return RunProblem(f"copilot failed: {stderr.strip()[-800:] or 'no stderr'}", False)
    if not _last(events, "result"):
        return RunProblem("copilot emitted no closing result line", False)
    return None


def session_problem(events: list[dict]) -> RunProblem | None:
    """The closing `result` line names the session the harness chose with
    `--session-id` (Decision 9): a line naming another session belongs to
    another run, so nothing read beside it is this run's. A runner failure."""
    expected = harness_record(events).get("session_id")
    found = _last(events, "result").get("sessionId")
    if not expected or not found or found == expected:
        return None
    return RunProblem(f"copilot's result line names the session {found}, not the run's "
                      f"{expected}", False)


def _overage_grew(before: object, after: object) -> bool:
    old, new = _snapshot_value(before, "overage_count"), _snapshot_value(after, "overage_count")
    if not _is_number(new):
        return True
    return new > (old if _is_number(old) else 0)  # type: ignore[operator]


def _consumption_reasons(events: list[dict], cap: float) -> list[str]:
    credits = credits_used(events)
    if credits is None:
        return ["the shutdown record carries no readable consumption (totalNanoAiu), so the "
                "run's draw on the plan cannot be read"]
    if credits > 2 * cap:
        return [f"the run consumed {credits:g} credits, more than twice its cap of {cap:g}"]
    if credits == 0 and sum(_usage(events).values()) > 0:
        return ["the shutdown record reports zero consumption while the per-model usage "
                "reports tokens"]
    return []


def _billing_reasons(before: object, after: object, events: list[dict], cap: float
                     ) -> list[str]:
    reasons = []
    if after is None:
        reasons.append("the status read after the run is unavailable, so overage growth cannot "
                       "be ruled out")
    elif _overage_grew(before, after):
        reasons.append(f"the overage count grew from {_snapshot_value(before, 'overage_count')} "
                       f"to {_snapshot_value(after, 'overage_count')}")
    reasons += _consumption_reasons(events, cap)
    reached = soft_cap_reached(events, cap)
    return reasons + ([f"the stream reports a reached limit ({reached})"] if reached else [])


def billing_after(before: object, after: object, events: list[dict], cap: float
                  ) -> tuple[RunProblem | None, bool]:
    """The billing guard after a run (spec: After every run) and whether it
    records a billing stop: no shutdown record (a runner failure, consumption
    unreadable), overage grown or appeared, the read after unavailable
    (`after is None`), a shutdown record without a readable `totalNanoAiu`,
    more than twice the cap, zero nano-AIU with tokens, or a reached soft cap
    or session limit. Pure."""
    if not _last(events, "copilot.shutdown"):
        return RunProblem("copilot recorded no session shutdown, so the run's consumption cannot "
                          "be read; a billing stop is recorded", False, final=True), True
    reasons = _billing_reasons(before, after, events, cap)
    if not reasons:
        return None, False
    cause = "; ".join(reasons)
    return RunProblem(refusal(_problem(cause, "check github.com/settings/billing, then run "
                                       f"`{host_login.CLEAR_STOP_COMMAND}`")), True,
                      "subscription", billing=cause), True


def _shell_reports(events: list[dict]) -> list[object]:
    done = _done(events)
    return [done.get(str(s.get("toolCallId")), {}).get("sandboxed")
            for s in _starts(events, top_level=False) if s.get("toolName") in SHELL_TOOLS]


def sandbox_after(events: list[dict], stderr: str = "") -> RunProblem | None:
    """The client's warning that the sandbox did not engage (stream, session
    file or stderr), or no report that it did: a shell completion whose
    `sandboxed` is not true, or no shell completion at all — whatever ended
    the run, a session error included (design Decision 13: until a recorded
    run confirms the report, its absence stops). Untested for isolation; the
    caller records an isolation stop."""
    warnings = _notices(events, "sandbox") + [line for line in stderr.splitlines()
                                              if sandbox_warned(line)]
    reports = _shell_reports(events)
    why = ("the client warned that the sandbox did not engage" if warnings else
           "the stream carries no report that the sandbox is active (no shell call)"
           if not reports else
           "a shell call was not reported as sandboxed" if any(r is not True for r in reports)
           else None)
    if why is None:
        return None
    return RunProblem(refusal(_problem(f"{why}; the sandbox's confinement is not confirmed",
                                       f"read the run's findings, then run "
                                       f"`{host_login.CLEAR_STOP_COMMAND}`", "isolation")),
                      True, "isolation")


UNCONFINED_CALL ="a shell call the client did not report as sandboxed"
SANDBOX_NOTICE = "the client's warning that the sandbox did not engage"
OUTSIDE_FILE = "a file tool call on a path outside the workspace"
# The client's file tools run in its own process, outside the sandbox, so the
# watch checks where they point (Decision 13, the workspace after the run).
FILE_TOOLS = frozenset({"view", "glob", "grep", "rg", "str_replace_editor", *EDIT_TOOLS})
# the file headers of a patch in the format `apply_patch` takes
PATCH_FILE = re.compile(r"^\*\*\* (?:(?:Add|Update|Delete) File|Move to): (.+)$", re.MULTILINE)


def tool_paths(data: Mapping) -> list[str]:
    """The paths a file tool's start names: its `path` argument and, for a
    patch, every file the patch's headers name. Pure."""
    args = data.get("arguments") if isinstance(data.get("arguments"), dict) else {}
    paths = [args["path"]] if isinstance(args.get("path"), str) and args["path"] else []
    if data.get("toolName") == "apply_patch":
        paths += [found.strip() for value in args.values() if isinstance(value, str)
                  for found in PATCH_FILE.findall(value)]
    return paths


def leaves_workspace(path: str, ws: Path) -> bool:
    """Whether a file tool's path, resolved as the harness's own process sees
    it — relative to the workspace, every link followed — lies outside the
    workspace: a link the sandboxed shell planted there resolves to its
    target. A `~` path counts as outside, since the client resolves it against
    a home that is not the workspace."""
    if path.startswith("~"):
        return True
    root = os.path.realpath(ws)
    target = os.path.realpath(Path(ws, path))  # an absolute `path` replaces `ws`
    return target != root and not target.startswith(root.rstrip(os.sep) + os.sep)


def _start_breach(data: Mapping, shells: set[str], ws: Path | None) -> str | None:
    name = data.get("toolName")
    if name in SHELL_TOOLS:
        shells.add(str(data.get("toolCallId")))
    elif (ws is not None and name in FILE_TOOLS and not data.get("mcpServerName")
          and any(leaves_workspace(path, ws) for path in tool_paths(data))):
        return OUTSIDE_FILE
    return None


def breach_of(event: object, shells: set[str], ws: Path | None = None) -> str | None:
    """One step of the run's live watch over its stdout events (Decision 13):
    a shell tool's start is noted in `shells`; the completion of a noted call
    whose `sandboxed` is not true, or a sandbox warning, is a breach; given the
    workspace, so is a file tool's start whose path leaves it
    (`leaves_workspace`, which resolves links on the harness's side). Pure but
    for `shells` and that resolution."""
    if not isinstance(event, dict):
        return None
    kind, data = event.get("type"), _data(event)
    if kind == "tool.execution_start":
        return _start_breach(data, shells, ws)
    call = str(data.get("toolCallId"))
    if kind == "tool.execution_complete" and call in shells and data.get("sandboxed") is not True:
        return UNCONFINED_CALL
    if kind in NOTICE_TYPES and sandbox_warned(str(data.get("message") or "")):
        return SANDBOX_NOTICE
    return None


class ConfinementWatch:
    """The run's live confinement check (Decision 13): the prompt-mode path
    applies the home's sandbox itself, which no check before the run can
    observe, so the run is watched while it lasts and stopped at the first
    breach (`breach_of` over stdout, a sandbox warning on stderr) rather than
    left to go on with the skill prompt. Given the workspace, a file tool
    pointed outside it is a breach too. `breach` keeps the first one."""

    def __init__(self, ws: Path | None = None) -> None:
        self.ws = ws
        self.shells: set[str] = set()
        self.breach: str | None = None

    def _found(self, reason: str | None) -> bool:
        if reason and self.breach is None:
            self.breach = reason
        return reason is not None

    def event_line(self, line: str) -> bool:
        try:
            event = json.loads(line)
        except ValueError:
            return False
        return self._found(breach_of(event, self.shells, self.ws))

    def stderr_line(self, line: str) -> bool:
        return self._found(SANDBOX_NOTICE if sandbox_warned(line) else None)


def stopped_after(breach: object) -> RunProblem | None:
    """A run the live watch stopped: untested for isolation (the caller records
    an isolation stop), naming the breach."""
    if not breach:
        return None
    return RunProblem(refusal(_problem(f"the run was stopped at {breach}; the sandbox's "
                                       "confinement is not confirmed",
                                       f"read the run's findings, then run "
                                       f"`{host_login.CLEAR_STOP_COMMAND}`", "isolation")),
                      True, "isolation")


def planted_after(planted: object) -> RunProblem | None:
    """A run that left the workspace replaced, or holding entries the harness
    must not follow (`workspace_breach`): untested for isolation (the caller
    records an isolation stop), naming them; no verdict reads the run's
    files."""
    if not planted:
        return None
    return RunProblem(refusal(_problem(f"{planted}; no verdict read the run's files, and the "
                                       "sandbox's confinement is not confirmed",
                                       f"read the run's findings, then run "
                                       f"`{host_login.CLEAR_STOP_COMMAND}`", "isolation")),
                      True, "isolation")


def _inside(path: str, root: str) -> bool:
    return bool(root) and (path == root or path.startswith(root.rstrip("/") + "/"))


def isolation_findings(events: list[dict], roster: Iterable[str], skill_root: str) -> list[str]:
    """Loaded skills unconfirmed or off the roster, a foreign skill, an MCP call
    or connected server, a hook event (Decision 10)."""
    loaded = _last(events, "session.skills_loaded")
    names = sorted(str(s.get("name")) for s in _data(loaded).get("skills") or []
                   if isinstance(s, dict))
    found = (["the loaded skills could not be confirmed (no loaded-skills report)"] if not loaded
             else [f"the loaded skills {', '.join(names)} differ from the listing "
                   f"{', '.join(sorted(roster))}"] if set(names) != set(roster) else [])
    found += [f"skill {r.get('name')} invoked from source {r.get('source')} ({r.get('path')})"
              for r in events if r.get("type") == "copilot.skill_invoked"
              and not (r.get("source") == "builtin" or (
                  r.get("source") == "project" and _inside(str(r.get("path")), skill_root)))]
    found += [f"an MCP tool call {name}" for name, _ in copilot_tool_calls(events)
              if name.startswith("mcp__")]
    found += [f"an MCP tool call on server {s.get('mcpServerName')}"
              for s in _starts(events, top_level=False)
              if s.get("mcpServerName") and s.get("parentToolCallId")]
    servers = _data(_last(events, "session.mcp_servers_loaded")).get("servers") or []
    found += [f"MCP server {s.get('name')} connected" for s in servers
              if isinstance(s, dict) and s.get("status") == "connected"]
    return found + [f"a hook event ({r.get('event')})" for r in events
                    if r.get("type") == "copilot.hook"]


def isolation_after(events: list[dict], roster: Iterable[str], skill_root: str
                    ) -> RunProblem | None:
    found = isolation_findings(events, roster, skill_root)
    if not found:
        return None
    return RunProblem(f"untested: {'; '.join(found)}. The run's isolation did not hold", True,
                      "isolation")


def model_after(events: list[dict], model: str | None, helpers: bool,
                effort: str | None) -> RunProblem | None:
    """A top-level message served by another model, another model's usage in a
    scenario without helpers, a rate-limit model switch, an effort left
    unapplied: untested for a precondition, both models named."""
    top = sorted({str(m.get("model")) for m in _messages(events) if m.get("model")} - {model})
    used = sorted(set(_metrics(events)) - {model}) if not helpers else []
    switch = [r for r in events if r.get("type") == "copilot.model_change"
              and r.get("cause") == "rate_limit_auto_switch"]
    why = (f"a top-level message was served by {', '.join(top)}, not the requested {model}"
           if top else f"the session reports usage by {', '.join(used)} beside the requested "
           f"{model}" if used else
           f"the client switched from {switch[0].get('previousModel')} to "
           f"{switch[0].get('newModel')} because of a rate limit" if switch else
           f"the client reported the requested effort {effort!r} as left unapplied"
           if effort and _notices(events, "effort_unapplied") else None)
    if why is None:
        return None
    return RunProblem(f"untested: {why}. Rerun with a model and an effort the plan serves as "
                      "requested", True, "precondition")


def unknown_after(events: list[dict], offered: Iterable[str]) -> RunProblem | None:
    names = unknown_tools(events, offered)
    if not names:
        return None
    return RunProblem(f"untested: the run called tools that were neither offered nor internal: "
                      f"{', '.join(names)}", True, "precondition")


def helper_after(events: list[dict]) -> RunProblem | None:
    """Each `task` call (read as `Agent`) cross-checked with `subagent.started`
    by `toolCallId`, both ways (Decision 10): a task call that started no
    subagent, or a subagent no task call shows, leaves the helper count the
    verdicts read unconfirmed. Untested for a precondition."""
    tasks = {str(s.get("toolCallId")) for s in _starts(events, top_level=False)
             if s.get("toolName") == "task"}
    started = {str(_data(e).get("toolCallId")) for e in events
               if e.get("type") == "subagent.started"}
    why = (f"the task call {', '.join(sorted(tasks - started))} started no subagent"
           if tasks - started else
           f"a subagent started without a task call ({', '.join(sorted(started - tasks))})"
           if started - tasks else None)
    if why is None:
        return None
    return RunProblem(f"untested: {why}, so the helper count cannot be confirmed", True,
                      "precondition")


def version_after(events: list[dict]) -> RunProblem | None:
    """The CLI version the session file reports, cross-checked with the one
    the preflight checked (Decision 10). A session record without a version
    is left to the other findings."""
    reported = _last(events, "copilot.session_start").get("copilotVersion")
    checked = harness_record(events).get("cli_version")
    if not reported or not checked or str(reported) == str(checked):
        return None
    return RunProblem(f"untested: the session reports CLI {reported}, not the {checked} the "
                      "preflight checked", True, "precondition")


@dataclass(frozen=True)
class Assessment:
    problem: RunProblem | None
    stops: tuple[tuple[str, str], ...] = ()


def combine(problems: Iterable[RunProblem | None]) -> RunProblem | None:
    """The outcome of several findings: a final runner failure stays one (a
    missing shutdown); otherwise the first finding, and a runner failure that
    a later untested finding explains becomes untested, naming both."""
    found = [p for p in problems if p is not None]
    final = next((p for p in found if p.final), None)
    if final:
        return final if found[0] is final else replace_message(final, found[0])
    if not found or found[0].untested:
        return found[0] if found else None
    later = next((p for p in found[1:] if p.untested), None)
    if later is None:
        return found[0]
    return RunProblem(f"{found[0].message} (not a result: {later.message})", True, later.kind,
                      later.billing)


def replace_message(final: RunProblem, first: RunProblem) -> RunProblem:
    return RunProblem(f"{first.message}; {final.message}", False, final=True)


def assess(events: list[dict], timed_out: str | None = None) -> Assessment:
    """Everything a finished (or timed-out) run's saved events say against a
    verdict, and the stops it records — pure over the events and the
    runner's own record (Decision 11)."""
    harness = harness_record(events)
    cap = float(harness.get("cap") or MIN_AI_CREDITS)
    model, effort = harness.get("model"), harness.get("effort")
    helpers = bool(harness.get("helpers"))
    scrubbed = RunProblem(refusal(_problem(
        "the token's value appeared in the Copilot child's output; it was scrubbed from "
        "everything the harness saved, but the client's session store in the harness home "
        "keeps the transcript unscrubbed", f"read the run's findings, revoke the token at "
        f"{host_login.TOKEN_PAGE}, create a new one ({host_login.TOKEN_PAGE}/new) and run "
        f"`{COPILOT.reset_command}`, which deletes the session store with the rest of the home",
        "isolation")),
        True, "isolation") if harness.get("scrub_hit") else None
    failure = (RunProblem(timed_out, False) if timed_out else
               failure_reason(events, int(harness.get("exit_code") or 0),
                              str(harness.get("stderr_tail") or ""), cap))
    billing, billing_stop = billing_after(harness.get("before"), harness.get("after"), events, cap)
    sandbox = sandbox_after(events, str(harness.get("stderr_tail") or ""))
    breach = harness.get("confinement_breach")
    planted = harness.get("workspace_breach")
    problems = [scrubbed, stopped_after(breach), planted_after(planted), failure,
                session_problem(events), billing, sandbox,
                isolation_after(events, harness.get("roster") or [],
                                str(harness.get("skill_root") or "")),
                model_after(events, model, helpers, effort),
                unknown_after(events, available_tools(helpers, bool(harness.get("network")))),
                helper_after(events), version_after(events)]
    stops = ([("isolation", "the token's value appeared in a child's output")] if scrubbed else [])
    stops += [("isolation", f"the run was stopped at {breach}")] if breach else []
    stops += [("isolation", str(planted))] if planted else []
    stops += [("billing", billing.billing or billing.message)] if billing_stop and billing else []
    stops += [("isolation", "the sandbox was ignored or not reported active")] if sandbox else []
    return Assessment(combine(problems), tuple(stops))


def run_problem(events: list[dict]) -> RunProblem | None:
    return assess(events).problem


def timeout_problem(failed: CopilotRunFailed) -> RunProblem:
    """A run stopped at its time limit: a runner failure naming the limit,
    unless its captured events show an untested cause."""
    return assess(failed.events, timed_out=failed.message).problem or RunProblem(
        failed.message, False)


# ---------- the run --------------------------------------------------------------------------


def parse_lines(text: str) -> list[dict]:
    events = []
    for line in text.splitlines():
        with suppress(ValueError):
            event = json.loads(line)
            if isinstance(event, dict):
                events.append(event)
    return events


def _pump(stream, sink: list[str], feed: Callable[[str], bool], tripped: threading.Event) -> None:
    """Collect one output stream line by line as the child writes it (the
    client writes each event as one line when it happens: `aQt`, app.js
    4739624), feeding each line to the watch."""
    with suppress(OSError, ValueError):
        for line in stream:
            sink.append(line)
            if feed(line):
                tripped.set()


def _watch_child(proc: subprocess.Popen, timeout: float,
                 ws: Path | None = None) -> tuple[str, str, bool, str | None]:
    """Wait for the prompt-mode child while `ConfinementWatch` reads its
    output (Decision 13): the first breach stops the child there, so a run
    whose shell is not confined does not go on with the skill prompt; the time
    limit stops it as before. Whatever ended it, every process left in its
    process group is killed (`stop_group`). A stream is closed only once its
    reader has finished: one still blocked on a pipe that a process outside
    the group holds is left to the daemon thread rather than closed under it.
    Returns stdout, stderr, whether the limit was reached, and the breach."""
    watch, tripped = ConfinementWatch(ws), threading.Event()
    out: list[str] = []
    err: list[str] = []
    pumps = [threading.Thread(target=_pump, args=(proc.stdout, out, watch.event_line, tripped),
                              daemon=True),
             threading.Thread(target=_pump, args=(proc.stderr, err, watch.stderr_line, tripped),
                              daemon=True)]
    for pump in pumps:
        pump.start()
    deadline, timed_out = time.monotonic() + timeout, False
    while proc.poll() is None and not tripped.is_set():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            timed_out = True
            break
        tripped.wait(min(WATCH_POLL_S, remaining))
    stop_group(proc, signal.SIGTERM)
    for pump, stream in zip(pumps, (proc.stdout, proc.stderr), strict=True):
        pump.join(timeout=host_login.TERM_GRACE_S)
        if not pump.is_alive():
            with suppress(OSError, AttributeError):
                stream.close()  # type: ignore[union-attr]
    return "".join(out), "".join(err), timed_out, watch.breach


def _after_status(run: Run) -> Status | None:
    """The read after the run; None when it is unavailable, a read that raised
    included (a broken pipe, a scratch home that could not be made), which
    `billing_after` turns into a billing stop."""
    try:
        after = read_status(run.home, run.environ, token=run.token)
    except Exception:  # fail closed: an after-read that raised is an unavailable one
        return None
    return None if after.error or after.snapshot is None else after


def _harness(run: Run, session_id: str, *, code: int | None, stderr: str, begun: float,
             after: Status | None, hit: bool, timed_out: bool, breach: str | None,
             planted: str | None = None) -> dict:
    return {"type": "copilot.harness", "duration_ms": int((time.monotonic() - begun) * 1000),
            "exit_code": code, "stderr_tail": stderr.strip()[-800:], "timed_out": timed_out,
            "confinement_breach": breach, "workspace_breach": planted,
            "session_id": session_id, "cap": run.cap, "model": run.model, "effort": run.effort,
            "helpers": int(run.scenario.get("helpers") or 0),
            "network": needs_network(run.scenario), "roster": run.roster,
            "skill_root": str(run.ws / ".agents" / "skills"),  # type: ignore[operator]
            "scrub_hit": hit, "before": snapshot_record(run.before),
            "after": snapshot_record(after), "cli_version": host_login.version_text(
                COPILOT_PINNED_VERSION)}


AFTER_INCOMPLETE = ("the checks after the run did not complete, so its draw on the plan and its "
                    "output were not checked")
WORKSPACE_REPLACED = ("the workspace itself was replaced (by a link or another directory), so "
                      "the harness read nothing in it")
SHOWN_ENTRIES = 5


def workspace_identity(ws: Path) -> tuple[int, int]:
    """The workspace directory's device and inode, taken before any Copilot
    child starts in it."""
    info = os.lstat(ws)
    return info.st_dev, info.st_ino


def _replaced(ws: Path, identity: tuple[int, int] | None) -> bool:
    """Whether `ws` is no longer the directory the run started in; a link left
    in its place is removed, never followed."""
    try:
        info = os.lstat(ws)
    except OSError:
        return True
    if stat.S_ISDIR(info.st_mode) and (info.st_dev, info.st_ino) == identity:
        return False
    if stat.S_ISLNK(info.st_mode):
        with suppress(OSError):
            ws.unlink()  # the link itself, never its target
    return True


def workspace_breach(ws: Path, identity: tuple[int, int] | None,
                     token: str | None) -> str | None:
    """The workspace after the run (Decision 13), before the harness reads,
    scrubs or writes anything in it. The sandboxed shell may write the
    workspace, and making a link never touches its target, so a run whose
    every shell call was sandboxed can still leave a link that the harness —
    unsandboxed — would follow: into the judge's prompt, the event file, the
    scrub. Why it cannot be read, or None: the workspace replaced (`_replaced`),
    or entries `_unsafe_entry` names, each unlinked without being followed
    (the link goes, its target stays untouched). Names at most SHOWN_ENTRIES
    entries, scrubbed; never reads one."""
    if _replaced(ws, identity):
        return WORKSPACE_REPLACED
    found = unsafe_entries(ws)
    for path, _why in found:
        with suppress(OSError):
            path.unlink()  # the entry itself, never a link's target
    if not found:
        return None
    named = ", ".join(f"{path.relative_to(ws).as_posix()} ({why})"
                      for path, why in found[:SHOWN_ENTRIES])
    more = f" and {len(found) - SHOWN_ENTRIES} more" if len(found) > SHOWN_ENTRIES else ""
    return scrub(f"the workspace held entries the harness must not follow, removed unread: "
                 f"{named}{more}", token)[0]


def _settle(run: Run, proc: subprocess.Popen, session_id: str, *, begun: float,
            timeout: float) -> tuple[list[dict], str | None]:
    """Wait for the child under the live watch, then the workspace check (the
    first thing after the child, before anything in the workspace is read or
    written), the session file, the read after, the scrub, the snapshot and
    the stops; the events and the time-limit message."""
    out, err, timed_out, breach = _watch_child(proc, timeout, run.ws)
    planted = workspace_breach(run.ws, run.ws_id, run.token)  # type: ignore[arg-type]
    records, file_hit = capture_session(run.home, session_id, run.token)
    after = _after_status(run)
    out, out_hit = scrub(out, run.token)
    err, err_hit = scrub(err, run.token)
    tree_hits = scrub_tree(run.ws, run.token)  # type: ignore[arg-type]
    hit = file_hit or out_hit or err_hit or bool(tree_hits)
    events = [*parse_lines(out), *records,
              _harness(run, session_id, code=proc.returncode, stderr=err, begun=begun,
                       after=after, hit=hit, timed_out=timed_out, breach=breach,
                       planted=planted)]
    write_snapshot(run.home, after)
    limit = f"copilot did not finish within {timeout:g}s" if timed_out else None
    for kind, cause in assess(events, timed_out=limit).stops:
        record_stop(run.home, kind, cause)
    return events, limit


def _execute(run: Run, request: str, fd: int, timeout: float) -> list[dict]:
    """The prompt-mode child, holding the lock through `pass_fds`, then
    `_settle`. The steps after the start fail closed: whatever raises among
    them, the child and its process group are stopped, the workspace checked
    and scrubbed, and a billing stop recorded (an isolation stop too, for a
    workspace breach) before the exception goes on."""
    session_id = str(uuid.uuid4())
    log_dir = run.scratch / "logs"  # type: ignore[operator]
    argv = command(run.scenario, request, model=run.model, effort=run.effort,  # type: ignore[arg-type]
                   session_id=session_id, log_dir=log_dir, cap=run.cap)
    begun = time.monotonic()
    proc = spawn(argv, home=run.home, cwd=run.ws, scratch=run.scratch, token=run.token,  # type: ignore[arg-type]
                 environ=run.environ, pass_fds=(fd,))
    try:
        events, limit = _settle(run, proc, session_id, begun=begun, timeout=timeout)
    except BaseException:
        stop_group(proc, signal.SIGTERM)
        planted = workspace_breach(run.ws, run.ws_id, run.token)  # type: ignore[arg-type]
        scrub_tree(run.ws, run.token)  # type: ignore[arg-type]
        record_stop(run.home, "billing", AFTER_INCOMPLETE)
        if planted:
            record_stop(run.home, "isolation", planted)
        raise
    if limit:
        raise CopilotRunFailed(limit, events)
    return events


def run_copilot(ws: Path, request: str, *, model: str, effort: str | None, cap: int,
                timeout: float, home: Path, scenario: Mapping,
                environ: Mapping[str, str] | None = None) -> list[dict]:
    """One Copilot run under a single hold of the run lock (Decision 9): the
    parent-folder scan, then under the lock the recorded stop and the token
    file read again (`LOCKED`: a run waits up to LOCK_WAIT_S for the lock,
    during which another run may record a stop or a login may replace the
    token and record the approval stop), the status read before, the model
    listing, the rosters and the confinement probe, the run (whose child holds
    the lock too), the session file, the read after, the scrub and the stops.
    Raises `host_login.RunLockRefused`, `CopilotRefused` (untested) or
    `CopilotRunFailed` (checked by `timeout_problem`); the events it returns
    are checked afterwards by `run_problem`."""
    problem = scan_problem(ws)
    if problem:
        raise CopilotRefused.of(problem)
    run = new_run(environ, ws=ws, scenario=scenario, model=model, effort=effort, cap=cap,
                  ws_id=workspace_identity(ws))
    run.home = home
    run.scratch = make_scratch("devrun-copilot-home-", run.environ)
    try:
        with host_login.run_lock(home, record=COPILOT) as fd:
            _require(step(run) for step in LOCKED)
            _require(gate_checks(run))
            return _execute(run, request, fd, timeout)
    finally:
        shutil.rmtree(run.scratch, ignore_errors=True)


def preflight_report(ws: Path, scenario: Mapping, *, model: str, effort: str | None,
                     environ: Mapping[str, str] | None = None) -> tuple[list[Check], bool]:
    """`--preflight-only` (Decision 7): every check that comes before the run,
    staging, the rosters and the confinement probe included, each recorded.
    A refused row in REPORTED (the stop, the sandbox tools, the status, the
    model, the rosters) is printed and the report goes on; any other refusal
    makes a later start unsafe and ends it. A recorded stop does not decide
    the outcome. No prompt-mode child starts, and the probe's session folder
    is deleted."""
    run = new_run(environ, ws=ws, scenario=scenario, model=model, effort=effort)
    checks = list(preflight_checks(run))
    if any(c.problem and c.name not in REPORTED for c in checks):
        return checks, False
    checks.append(Check("workspace", scan_problem(ws)))
    if checks[-1].problem:
        return checks, False
    run.scratch = make_scratch("devrun-copilot-home-", run.environ)
    try:
        with host_login.run_lock(run.home, record=COPILOT):
            checks += list(gate_checks(run))
    finally:
        shutil.rmtree(run.scratch, ignore_errors=True)
    return checks, not any(c.problem and c.name != "stop" for c in checks)


# ---------- `host-status copilot` -----------------------------------------------------------


def _yes(flag: bool) -> str:
    return "yes" if flag else "no"


def _show(value: object) -> str:
    if value is None:
        return "missing"
    return json.dumps(value) if isinstance(value, bool) else str(value)


def _token_state(home: Path) -> tuple[str | None, LoginProblem | None, str]:
    """The token, why it cannot be used, and the `token_present` line — read
    from the file's state (no value, or a value that is not fine-grained),
    never from the wording of the refusal."""
    value, problem = _token_file(home)
    if problem:
        return None, problem, "not fine-grained" if value else "no"
    return value, None, "yes"


def _sandbox_line(environ: Mapping[str, str]) -> str:
    if sys.platform == "win32":
        return "unsupported (Windows)"
    path = environ.get("PATH")
    return ", ".join(f"{tool} {'found' if shutil.which(tool, path=path) else 'missing'}"
                     for tool in SANDBOX_TOOLS)


def _auth_line(st: Status | None) -> str:
    """The `auth_type` line (task 7.4b): no read, a failed read, a read that
    found no login, and the reported type are told apart."""
    if st is None:
        return "unknown"
    if st.error:
        return "unavailable"
    if not st.logged_in:
        return "none"
    return st.auth_type or "unreported"


def _status_lines(home: Path, environ: Mapping[str, str], st: Status | None, *,
                  token_line: str, version: tuple[int, int, int] | None,
                  offenders: list[str]) -> dict[str, str]:
    snap = st.snapshot if st else None
    stop = read_stop(home) if home.is_dir() else None
    return {
        "home": str(home),
        "marker": _yes((home / MARKER).is_file()),
        "token_present": token_line,
        "auth_type": _auth_line(st),
        "host_ok": _yes(st.host == "https://github.com") if st else "unknown",
        "plan_class": f"{st.plan or 'unknown'} ({st.sku or 'unknown'})" if st else "unknown",
        "token_based_billing": _show(st.token_based_billing) if st else "unknown",
        "overage_permitted": _show(snap.overage_permitted) if snap else "unknown",
        "overage_count": _show(snap.overage_count) if snap else "unknown",
        "overage_entitlement": _show(snap.overage_entitlement) if snap else "unknown",
        "remaining_pct": _show(snap.percent_remaining) if snap else "unknown",
        "reset_date": (st.reset_date or "unknown") if st else "unknown",
        "stop": f"{stop.get('kind')} ({stop.get('cause')})" if stop else "none",
        "clean": ", ".join(offenders) if offenders else _yes(home.is_dir()),
        "cli_version": host_login.version_text(version),
        "pinned_version": host_login.version_text(COPILOT_PINNED_VERSION),
        "sandbox": _sandbox_line(environ),
        "runs_use": "harness (token file)",
    }


def _model_lines(st: Status | None) -> dict[str, str]:
    if st is None or st.models is None:
        return {"models": "unavailable"}
    return {f"model {m.id}": f"policy {m.policy or 'unreported'}; efforts "
            f"{', '.join(m.efforts) or 'none'}" for m in st.models}


def status(home: Path, environ: Mapping[str, str], *, models: bool = False,
           no_token: bool = False, run_probes: bool = True
           ) -> tuple[dict[str, str], LoginProblem | None]:
    """The lines of `host-status copilot` — only the keys of the spec's status
    list: booleans, enums, numbers, versions, the stop — and the first reason
    the home is not ready: the version, the home, the token, the managed
    settings and sandbox tools (`machine_problem`), then the status read's
    auth and billing rows. A recorded stop is reported, never a refusal here.
    The reads run only when the location was not refused (`run_probes`) and
    the home is present, marked, owner-only and clean, under the run lock.
    The `clean` line and the refusal both name the home as the reads left it:
    a read whose child wrote into the home is reported, not hidden. Without a
    Copilot work directory for the reads' scratch homes (`work_problem`), no
    child starts and that is the first reason."""
    token, token_gap, token_line = _token_state(home)
    work_gap = work_problem(environ) if run_probes else None
    run_probes = run_probes and work_gap is None
    version = installed_version(home, environ, token) if run_probes else None
    presence = host_login.check_presence(home, COPILOT)
    adopted = run_probes and presence is None and not host_login.copilot_offenders(home)
    st = bare = None
    if adopted:
        with host_login.run_lock(home, record=COPILOT):
            st = read_status(home, environ, token=token, models=models) if token else None
            bare = read_status(home, environ, token=None) if no_token else None
            if st is not None:
                write_snapshot(home, st)
    offenders = host_login.copilot_offenders(home)  # after the reads
    lines = _status_lines(home, environ, st, token_line=token_line, version=version,
                          offenders=offenders)
    lines.update(_model_lines(st) if models else {})
    lines.update({"logged_in": "unknown" if bare is None else _yes(bare.logged_in)}
                 if no_token else {})
    problem = (work_gap or (check_copilot_version(version) if run_probes else None) or presence
               or host_login.check_copilot_home(home, offenders=offenders))
    return lines, (problem or token_gap or machine_problem(environ)
                   or (status_problem(st) if st else None))


# ---------- `run-env` (K1, the operator only; design Decision 15) ------------------------------


def main(argv: list[str] | None = None) -> int:
    """`run-env -- <command…>`: run a command in a Copilot child's environment
    (scratch HOME, the disabled session bus, the empty GitHub CLI directory),
    without the token variable. Never used by a run; the operator runs it for
    K1's `gh` cut-off check, because a cut-off that fails would hand the
    operator's `gh` token to the command. Exit: the command's own status; 2
    usage; 3 when the harness home is not ready."""
    parser = argparse.ArgumentParser(prog="copilot_cli", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)
    run_env_parser = sub.add_parser("run-env", help="run a command in a Copilot child's "
                                                    "environment, without the token")
    run_env_parser.add_argument("argv", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    cmd = args.argv[1:] if args.argv[:1] == ["--"] else args.argv
    if not cmd:
        parser.error("run-env needs a command after --")
    environ = os.environ
    run = new_run(environ)
    problem = (host_login.check_location(run.root, environ, record=COPILOT)
               or host_login.check_presence(run.home, COPILOT) or work_problem(environ))
    if problem:
        print(refusal(problem), file=sys.stderr)
        return host_login.EXIT_NOT_READY
    with call_scratch(environ) as scratch:
        env = child_env(run.home, environ, scratch, token=None)
        assert_copilot_env(env, run.home)
        return subprocess.run(cmd, env=env, cwd=scratch, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
