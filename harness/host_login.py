#!/usr/bin/env python3
"""Host logins the harness drives: its own login home, and a linked login kept current.

**The harness login.** Every isolated Claude run links a login into its
temporary configuration. Until 2026-10-05 that was the operator's own
`~/.claude/.credentials.json`, so the harness and the operator shared one
rotating refresh token: a concurrent refresh, or a run stopped part-way through
one, could log the operator out of their own CLI. The harness now keeps a
login of its own in a home it owns, described per client by a `HostLogin`
record (testing-harness spec: Harness-owned host logins):

- **Where.** `state_root()/hosts/<client>` — the XDG state directory on Linux,
  Application Support on macOS, the local application data on Windows, or the
  test override `THESIS_PROPOSAL_DEV_STATE`. `check_location` refuses a root
  that is not absolute, equals or contains the user's home, overlaps a
  client's own configuration directory, or lies inside the repository.
- **What.** A `.harness-home` marker, mode 0700, and before the first login
  the account-surface opt-outs and an empty profile directory (`seed`). Only a
  marked, unlinked home is ever deleted (`wipe`) or logged into: a login
  seeds only a home that does not exist, and refuses any other directory at
  its path (`not_harness_made`).
- **Preflight.** `preflight` checks, without a model call, that the home is in
  place, clean, logged in with the subscription, in the right directory and
  through Anthropic's own API. Each failure is a `LoginProblem` with one
  remedy, rendered by `refusal` as "untested: <cause>. <remedy>. <login note>."
  The login note says the operator's own login is unaffected — except that,
  while live check L3 has not passed (`L3_PASSED`), a remedy naming
  `host-login` closes with the caveat that whether it logs out the operator's
  other sessions is unverified.
- **Commands.** `main(argv)`: `login <client> [--reset]` (the operator only:
  refused without a terminal and inside an agent session — speed bumps; the
  AGENTS.md rule is the guard), `status [client]` (no model call, no account
  details; agents may run it) and `logout <client>`. Every login and logout
  runs in `login_env`, so no inherited token, key or profile directory can
  steer it at another login, and none of them, nor the status check, starts
  while the default Anthropic profile directory holds an entry
  (`profile_problem`, fallback F8). A logout that fails stops a re-login or
  a reset before anything is replaced or wiped.

**One child environment.** `allowlisted_env(record, config)` builds the
environment of every host child that runs in an isolated configuration — the
routing rig's, the isolated dev run's, the judge's and its preflight, and the
harness login's status checks — from the record's allowlist, plus the
configuration directory, the connector switch and the empty profile directory.

**Stopping a child.** `stop_child` asks a host to terminate and kills it only
after `TERM_GRACE_S`, so a host part-way through writing a refreshed login can
finish (whether Claude Code does is live check L9).

**The linked login.** An isolated configuration holds a symlink to the
`.credentials.json` it uses: the harness home's by default, the directory
`CLAUDE_REAL_CONFIG_DIR` names under the explicit opt-in. When the host
refreshes an expired access token it writes a new file by atomic rename, which
replaces the symlink and rotates the refresh token (recorded 2026-10-04 on
2.1.284). `keep_login` writes such a refresh back to the link's target and
restores the link, and serializes refreshes across concurrent isolated runs
with a claim beside that target. Credential values are copied byte for byte
and never printed; only `expiresAt` is ever read out of them.

Usage:
  uv run poe host-login claude [--reset]   # the operator, in a terminal
  uv run poe host-status [claude]          # anyone; no model call
  uv run poe host-logout claude            # the operator
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager, suppress
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePath

from account_surfaces import (
    CONNECTORS_OFF,
    LONG_LIVED_TOKEN,
    PINNED_SETTINGS,
    PROFILE_DIR,
    PROFILE_VARIABLE,
    SETTINGS_FILE,
    default_profile_store,
    profile_store_problem,
)

REPO = Path(__file__).resolve().parent.parent
CREDENTIALS = ".credentials.json"
CLAIM_NAME = ".devrun-refresh.claim"
RELOGIN = "run `claude` and enter `/login`"
OPT_IN_VAR = "CLAUDE_REAL_CONFIG_DIR"

# Judgment, not host constants (the host's own refresh margin is not
# documented). A run whose stored token expires within the margin is about to
# refresh. The host refreshes on its first request, seconds after start, so a
# holder that has not written back after CLAIM_HOLD_S is not going to; a claim
# twice that old was left by a run that died; waiters outlast one hold.
POLL_S = 0.5
CLAIM_POLL_S = 1.0
REFRESH_MARGIN_S = 300
CLAIM_HOLD_S = 60
CLAIM_STALE_S = 120
CLAIM_WAIT_S = 90

# How long a host asked to terminate gets before it is killed: judgment, the
# same grace the Codex brief uses; it bounds the worst case only.
TERM_GRACE_S = 10
# `auth status` and `auth logout` answer in about a second
CLIENT_TIMEOUT_S = 60

STATE_VAR = "THESIS_PROPOSAL_DEV_STATE"
STATE_NAME = "thesis-proposal-dev"
MARKER = ".harness-home"
MARKER_TEXT = ("This directory is a harness login home of thesis-proposal-skills "
               "(harness/host_login.py). It is safe to delete with "
               "`uv run poe host-login <client> --reset`.\n")
LOGIN_COMMAND = "uv run poe host-login claude"
RESET_COMMAND = f"{LOGIN_COMMAND} --reset"

# Live check L3: does the harness logout leave the operator's other Claude
# sessions working? Flipped by add-harness-claude-login task 5.4, which passed
# on 2026-10-05; while it is False, no message claims the operator's login is
# unaffected by a command that logs out.
L3_PASSED = True
NOT_AFFECTED = "Your own Claude login is not affected"
L3_CAVEAT = "Whether this logs out your other Claude sessions is unverified (L3)"

# Variables a Claude Code session, or Codex's sandboxed shell, exports to the
# commands it runs. Their presence refuses `login` (a speed bump, not a guard:
# a marker can be unset). Whether the Codex pair is complete is unverified;
# add-codex-dev-runner pins it with the Codex record.
AGENT_MARKERS = ("CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT", "CLAUDE_CODE_SESSION_ID",
                 "CODEX_SANDBOX", "CODEX_SANDBOX_NETWORK_DISABLED")

# The only fields of `claude auth status --json` the harness reads; the email
# and organization it also reports never leave `read_status`.
STATUS_FIELDS = ("loggedIn", "authMethod", "apiProvider", "configDirectory")

EXIT_READY, EXIT_USAGE, EXIT_NOT_READY = 0, 2, 3


@dataclass(frozen=True)
class HostLogin:
    """What the harness needs to know about one host client's login.

    `seed` maps a path inside the home to its content (a trailing `/` makes a
    directory); `forbidden` lists globs whose matches make a home unclean;
    `fixed_env` and `profile` are what `allowlisted_env` sets beside the
    admitted names; `failure` is the host's wording for a login it cannot use."""

    name: str
    binary: str
    home_var: str
    login_argv: tuple[str, ...]
    status_argv: tuple[str, ...]
    logout_argv: tuple[str, ...]
    admitted: frozenset[str]
    admitted_prefixes: tuple[str, ...]
    login_strip_prefixes: tuple[str, ...]
    seed: Mapping[str, str]
    forbidden: tuple[str, ...]
    plugin_record: str | None
    fixed_env: Mapping[str, str]
    profile: tuple[str, str] | None
    credentials: str
    failure: re.Pattern


# What an isolated Claude child inherits: the machine, never the launching
# session. An allowlist, because the host and the desktop app keep adding
# variables — DISABLE_MICROCOMPACT, API_TIMEOUT_MS, ANTHROPIC_BASE_URL — that
# no `CLAUDE*` filter catches; a desktop-launched child recorded `entrypoint:
# claude-desktop` on 2026-10-04. A name missing here fails a run loudly; a name
# leaking past a denylist changes the measurement silently. Add one only with
# its reason. The account-surface variables (the connector switch, the
# Anthropic profile directory) are never admitted: `allowlisted_env` sets them.
CLAUDE_ADMITTED = frozenset({
    "PATH", "HOME",
    "CLAUDE_CODE_OAUTH_TOKEN",  # long-lived login: nothing is linked when it is set
    "USER", "LOGNAME", "SHELL",  # identity; the host's Bash tool picks SHELL
    "LANG", "LANGUAGE",  # with every LC_*: script I/O as on the student's machine
    "TMPDIR", "TMP", "TEMP",
    "XDG_CONFIG_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME", "XDG_CACHE_HOME",
    "XDG_RUNTIME_DIR", "XDG_CONFIG_DIRS", "XDG_DATA_DIRS",
    "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "ALL_PROXY",
    "http_proxy", "https_proxy", "no_proxy", "all_proxy",
    "SSL_CERT_FILE", "SSL_CERT_DIR", "NIX_SSL_CERT_FILE", "NODE_EXTRA_CA_CERTS",
    "NODE_USE_SYSTEM_CA", "REQUESTS_CA_BUNDLE", "CURL_CA_BUNDLE",
    "SYSTEMROOT", "COMSPEC", "PATHEXT", "USERPROFILE", "APPDATA", "LOCALAPPDATA",
})

CLAUDE = HostLogin(
    name="claude",
    binary="claude",
    home_var="CLAUDE_CONFIG_DIR",
    # --claudeai explicitly: a changed host default must never make the harness
    # login a console (API-billing) login
    login_argv=("auth", "login", "--claudeai"),
    status_argv=("auth", "status", "--json"),
    logout_argv=("auth", "logout"),
    admitted=CLAUDE_ADMITTED,
    admitted_prefixes=("LC_",),
    # the billing switches, the long-lived token, the desktop session's
    # entrypoint, session-binding and auth-refresh variables (CLAUDE_PID among
    # them), and any inherited config directory
    login_strip_prefixes=("ANTHROPIC_", "CLAUDE_CODE_", "CLAUDECODE", "CLAUDE_PID",
                          "CLAUDE_CONFIG_DIR"),
    seed={SETTINGS_FILE: json.dumps(dict(PINNED_SETTINGS), indent=2) + "\n",
          f"{PROFILE_DIR}/": ""},
    # host state, marketplace caches and projects are allowed: the host creates
    # state freely, and only these would be measured or synced content
    forbidden=("skills/*", "agents/*", "commands/*", "output-styles/*", "CLAUDE.md",
               "plugins/synced"),
    # shape recorded on 2.1.284: {"version": 2, "plugins": {...}}
    plugin_record="plugins/installed_plugins.json",
    fixed_env=CONNECTORS_OFF,
    profile=(PROFILE_VARIABLE, PROFILE_DIR),
    credentials=CREDENTIALS,
    # the host's wording for a login it cannot use: an expired one that could not
    # be refreshed (recorded 2026-10-03 and 2026-10-04), or none at all
    failure=re.compile(r"Failed to authenticate|OAuth session|Not logged in"),
)
RECORDS: Mapping[str, HostLogin] = {"claude": CLAUDE}
LOGIN_FAILURE = CLAUDE.failure


@dataclass(frozen=True)
class LoginProblem:
    """Why the harness login cannot serve a run: the cause and its one remedy."""

    cause: str
    remedy: str


class LoginSource(Enum):
    """Which login a run used — it decides the remedy and the label."""

    AMBIENT = "ambient"
    HARNESS = "harness"
    OPERATOR = "operator"
    TOKEN = "token"


# ---------- one environment builder --------------------------------------------


def allowlisted_env(record: HostLogin, config: PurePath,
                    environ: Mapping[str, str] | None = None) -> dict[str, str]:
    """The environment of a host child that runs in the isolated configuration
    `config`: the record's admitted names from `environ` (default: this
    process's) plus what the harness sets, each replacing any inherited value —
    the configuration directory, the record's fixed variables (for Claude the
    connector switch off) and its profile variable naming the configuration's
    empty profile directory. For Claude that profile directory is the only
    `ANTHROPIC_` name the child carries, and it routes no billing.

    Prints nothing — the dropped set holds the desktop session's messaging
    token (testing-harness spec: Isolated child environment)."""
    source = os.environ if environ is None else environ
    env = {name: value for name, value in source.items()
           if name in record.admitted or name.startswith(record.admitted_prefixes)}
    env[record.home_var] = str(config)
    env.update(record.fixed_env)
    if record.profile:
        variable, directory = record.profile
        env[variable] = str(config / directory)
    return env


def login_env(record: HostLogin, home: Path, environ: Mapping[str, str]) -> dict[str, str]:
    """The environment of every login and logout: the operator's own, so that
    a browser can open, less every billing and host-session variable, with the
    configuration directory set to the home and the profile directory to the
    home's empty one. `environ` is not modified."""
    env = {name: value for name, value in environ.items()
           if not name.startswith(record.login_strip_prefixes)}
    env[record.home_var] = str(home)
    env.update(record.fixed_env)
    if record.profile:
        variable, directory = record.profile
        env[variable] = str(home / directory)
    return env


# ---------- stopping a child ------------------------------------------------------


def stop_child(proc: subprocess.Popen) -> int:
    """Stop a host: ask it to terminate, give it TERM_GRACE_S, then kill it.
    On Windows `terminate()` is TerminateProcess, so the kill is the request.
    The exit status is the harness's own, not the host's verdict on its run."""
    with suppress(ProcessLookupError):
        proc.terminate()
    try:
        return proc.wait(timeout=TERM_GRACE_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait()


# ---------- the harness home ---------------------------------------------------------


def state_root(environ: Mapping[str, str], platform: str = sys.platform,
               home: Path | None = None) -> Path:
    """Where the harness keeps its per-user state, following the platform's
    convention; the test override comes first. A relative XDG_STATE_HOME is
    ignored, as the XDG specification says."""
    user = Path.home() if home is None else home
    if environ.get(STATE_VAR):
        return Path(environ[STATE_VAR])
    if platform == "darwin":
        return user / "Library" / "Application Support" / STATE_NAME
    if platform == "win32":
        local = environ.get("LOCALAPPDATA")
        return Path(local) / STATE_NAME if local else user / "AppData" / "Local" / STATE_NAME
    xdg = environ.get("XDG_STATE_HOME")
    if xdg and Path(xdg).is_absolute():
        return Path(xdg) / STATE_NAME
    return user / ".local" / "state" / STATE_NAME


def home(record: HostLogin, environ: Mapping[str, str] | None = None) -> Path:
    """The record's login home under the state root."""
    return state_root(os.environ if environ is None else environ) / "hosts" / record.name


def _within(path: Path, other: Path) -> bool:
    """`path` equals `other` or lies inside it."""
    return path == other or other in path.parents


def _client_dirs(environ: Mapping[str, str], user: Path) -> list[Path]:
    dirs = [user / ".claude", user / ".codex"]
    return dirs + [Path(environ[name]) for name in ("CLAUDE_CONFIG_DIR", "CODEX_HOME")
                   if environ.get(name)]


def check_location(root: Path, environ: Mapping[str, str], repo: Path = REPO,
                   user_home: Path | None = None) -> LoginProblem | None:
    """Refuse a state root that is not absolute, that equals or contains the
    user's home, that equals, contains or lies inside a client's own
    configuration directory, or that lies inside the repository. Applied to
    every resolved root, the default included; containment is tested on
    resolved paths, so a symlink cannot route around it. A relative root would
    resolve against whichever directory a command runs in — the home itself,
    for a login — and a link to it would dangle."""
    remedy = (f"point {STATE_VAR} at a directory of its own, outside the repository and every "
              f"client's configuration directory, or unset it")
    if not root.is_absolute():
        return LoginProblem(f"the harness state directory {root} is not an absolute path",
                            f"give {STATE_VAR} an absolute path, or unset it")
    user = (Path.home() if user_home is None else user_home).resolve()
    resolved = root.resolve()
    if _within(user, resolved):
        return LoginProblem(f"the harness state directory {root} equals or contains your home "
                            f"directory {user}", remedy)
    for client in _client_dirs(environ, user):
        target = client.resolve()
        if _within(resolved, target) or _within(target, resolved):
            return LoginProblem(f"the harness state directory {root} overlaps the client "
                                f"configuration directory {client}", remedy)
    if _within(resolved, repo.resolve()):
        return LoginProblem(f"the harness state directory {root} lies inside the repository "
                            f"{repo}", remedy)
    return None


def profile_problem(environ: Mapping[str, str]) -> LoginProblem | None:
    """Fallback F8 for the harness login's own host processes — the login,
    every logout and the status check: whether the host ignores the default
    Anthropic profile directory when the profile variable names the home's
    empty one is unverified (live check L8), so a profile there could become
    the login such a process acts on. They run without the long-lived token,
    so token mode does not lift it here. The directory is named, never its
    contents."""
    without_token = {name: value for name, value in environ.items()
                     if name != LONG_LIVED_TOKEN}
    if profile_store_problem(without_token) is None:
        return None
    return LoginProblem(f"the default Anthropic profile directory "
                        f"{default_profile_store(without_token)} is not empty, and whether the "
                        f"host ignores it when {PROFILE_VARIABLE} names the harness login "
                        "home's empty one is unverified, so the client could act on a profile "
                        "there instead of the harness login", "move the profiles aside")


def seed(record: HostLogin, home_dir: Path) -> None:
    """Create the home owner-only, mark it, and write the record's seed: for
    Claude the pinned opt-out settings and an empty profile directory. It runs
    before the first login, because account content synced once stays."""
    home_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    if os.name == "posix":
        home_dir.chmod(0o700)
    (home_dir / MARKER).write_text(MARKER_TEXT, encoding="utf-8")
    for rel, content in record.seed.items():
        path = home_dir / rel
        if rel.endswith("/"):
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


def not_harness_made(home_dir: Path) -> LoginProblem | None:
    """Why `home_dir` is no home the harness created: a symbolic link, or a
    path without the marker. The harness neither deletes nor adopts it."""
    if home_dir.is_symlink():
        return LoginProblem(f"{home_dir} is a symbolic link, not a harness login home",
                            f"remove the link, then run `{LOGIN_COMMAND}`")
    if not (home_dir / MARKER).is_file():
        return LoginProblem(f"{home_dir} carries no {MARKER} marker, so the harness did not "
                            "create it", f"move it aside, then run `{LOGIN_COMMAND}`")
    return None


def wipe(home_dir: Path) -> LoginProblem | None:
    """Delete the home — only a marked home that is not a symbolic link.
    Otherwise refuse, naming the directory, and delete nothing."""
    problem = not_harness_made(home_dir)
    if problem:
        return problem
    shutil.rmtree(home_dir)
    return None


def check_presence(home_dir: Path) -> LoginProblem | None:
    """The home exists, carries its marker and is owner-only (POSIX). A
    directory without the marker is not adopted, so its remedy is the same
    as `wipe`'s: move it aside."""
    remedy = f"run `{LOGIN_COMMAND}`"
    if not home_dir.is_dir():
        return LoginProblem(f"the harness login home {home_dir} does not exist", remedy)
    if not (home_dir / MARKER).is_file():
        return not_harness_made(home_dir)
    mode = home_dir.stat().st_mode & 0o777
    if os.name == "posix" and mode & 0o077:
        return LoginProblem(f"the harness login home {home_dir} has mode {mode:04o}, wider "
                            "than owner-only (0700)", remedy)
    return None


def _same_json(path: Path, expected: str) -> bool:
    """Compared as JSON text, so `0` never passes for `false`."""
    try:
        actual = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False
    return json.dumps(actual, sort_keys=True) == json.dumps(json.loads(expected), sort_keys=True)


def _plugins_installed(path: Path) -> bool:
    """A non-empty installed-plugins record; an unreadable one counts too."""
    if not path.exists():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return True
    return not isinstance(record, dict) or bool(record.get("plugins"))


def home_offenders(record: HostLogin, home_dir: Path) -> list[str]:
    """What makes the home unclean, by path inside it: a seeded file that no
    longer holds its seed, a forbidden entry, or an installed plugin."""
    found = [f"{rel} (not exactly the pinned opt-outs)" for rel, content in record.seed.items()
             if not rel.endswith("/") and not _same_json(home_dir / rel, content)]
    for pattern in record.forbidden:
        found += sorted(path.relative_to(home_dir).as_posix() for path in home_dir.glob(pattern))
    if record.plugin_record and _plugins_installed(home_dir / record.plugin_record):
        found.append(record.plugin_record)
    return found


def check_home(record: HostLogin, home_dir: Path) -> LoginProblem | None:
    """The home is clean. A dirty home means the opt-outs failed under this
    account, so the remedy is to remove the entry or start over."""
    offenders = home_offenders(record, home_dir)
    if not offenders:
        return None
    return LoginProblem(f"the harness login home {home_dir} is not clean: it holds "
                        f"{', '.join(offenders)}",
                        f"remove {'it' if len(offenders) == 1 else 'them'}, or run "
                        f"`{RESET_COMMAND}`")


def check_status(status: Mapping, home_dir: Path) -> LoginProblem | None:
    """The host reports the subscription login, through Anthropic's own API,
    in the home itself. A configuration directory the host stops reporting
    must not read as "matches"."""
    if not status.get("loggedIn"):
        return LoginProblem(f"the harness login home {home_dir} holds no login",
                            f"run `{LOGIN_COMMAND}`")
    method = status.get("authMethod")
    if method != "claude.ai":
        return LoginProblem(f"the harness login uses auth method {method!r}, not the "
                            "subscription login (claude.ai)", f"run `{RESET_COMMAND}`")
    provider = status.get("apiProvider")
    if provider != "firstParty":
        return LoginProblem(f"the harness login routes calls through {provider!r}, not "
                            "Anthropic's own API (firstParty)", f"run `{RESET_COMMAND}`")
    reported = status.get("configDirectory")
    if not reported:
        return LoginProblem("the host reports no configuration directory for the harness "
                            "login home", "update Claude Code to a version that reports "
                            "`configDirectory` in `claude auth status --json` (2.1.268 or later)")
    if Path(str(reported)).resolve() != home_dir.resolve():
        return LoginProblem(f"the host reports the configuration directory {reported}, not the "
                            f"harness login home {home_dir}, so something redirects it",
                            "remove the wrapper or managed setting that redirects the "
                            "configuration directory")
    return None


def login_note(remedy: str) -> str:
    """The closing sentence of a refusal: the operator's own login is not
    affected — unless the remedy runs the harness login command while L3 is
    unverified, because that command logs out first."""
    if not L3_PASSED and "host-login" in remedy:
        return L3_CAVEAT
    return NOT_AFFECTED


def refusal(problem: LoginProblem) -> str:
    """The one template: untested, the cause, the one remedy, the login note."""
    remedy = problem.remedy[:1].upper() + problem.remedy[1:]
    return (f"untested: {problem.cause.rstrip('.')}. {remedy.rstrip('.')}. "
            f"{login_note(problem.remedy)}.")


def run_client(argv: Sequence[str], env: Mapping[str, str], *, interactive: bool,
               cwd: Path) -> tuple[int, str]:
    """Start the client binary: interactively on the operator's terminal (the
    login), or quietly with its stdout captured and bounded by
    CLIENT_TIMEOUT_S. The runner seam the L0 tests fake."""
    try:
        if interactive:
            return subprocess.run(list(argv), env=dict(env), cwd=cwd, check=False).returncode, ""
        proc = subprocess.Popen(list(argv), env=dict(env), cwd=cwd, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True,
                                encoding="utf-8", errors="replace")
    except OSError:
        return 127, ""
    try:
        out, _ = proc.communicate(timeout=CLIENT_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        stop_child(proc)
        return 124, ""
    return proc.returncode, out or ""


def read_status(record: HostLogin, home_dir: Path) -> dict:
    """The host's status for the home, reduced to STATUS_FIELDS; {} when it
    yields no login state. Runs in the allowlisted environment, without an
    exported long-lived token, so it reports the home's own login."""
    env = allowlisted_env(record, home_dir)
    env.pop(LONG_LIVED_TOKEN, None)
    _, out = run_client([record.binary, *record.status_argv], env, interactive=False,
                        cwd=home_dir)
    try:
        data = json.loads(out)
    except ValueError:
        return {}
    return {key: data[key] for key in STATUS_FIELDS if key in data} if isinstance(
        data, dict) else {}


def preflight(record: HostLogin, environ: Mapping[str, str] | None = None) -> LoginProblem | None:
    """The first reason the harness login cannot serve a run, or None —
    checked without a model call, in the order of the requirement; a missing
    home starts no client."""
    environ = os.environ if environ is None else environ
    root = state_root(environ)
    problem = check_location(root, environ) or profile_problem(environ)
    if problem:
        return problem
    home_dir = root / "hosts" / record.name
    return (check_presence(home_dir) or check_home(record, home_dir)
            or check_status(read_status(record, home_dir), home_dir))


# ---------- which login a run used -----------------------------------------------


def link_target(link: Path) -> Path | None:
    """Where a credentials link points, unresolved; None when it is no link."""
    if not link.is_symlink():
        return None
    target = link.readlink()
    return target if target.is_absolute() else link.parent / target


def writeback_target(link: Path) -> Path | None:
    """The one file `keep_login` writes a refresh to: the link's resolved target."""
    target = link_target(link)
    return target.resolve() if target is not None else None


def planned_source(environ: Mapping[str, str]) -> LoginSource:
    """The login an isolated run started from `environ` would link."""
    if environ.get(LONG_LIVED_TOKEN):
        return LoginSource.TOKEN
    if environ.get(OPT_IN_VAR):
        return LoginSource.OPERATOR
    return LoginSource.HARNESS


def login_source(config: Path | None, environ: Mapping[str, str]) -> LoginSource:
    """Which login a run on `config` uses: none linked (ambient), else the one
    `routing.prepare_config` linked for `environ` (`planned_source`). Decided
    from how the configuration was prepared, never from the link's current
    state: while the host refreshes, its own file stands where the link was
    until the keeper restores it."""
    return LoginSource.AMBIENT if config is None else planned_source(environ)


def login_dir(config: Path | None, environ: Mapping[str, str]) -> Path | None:
    """The directory of the linked login — the one place a refresh is written
    back — or None for an ambient run and a token: the link's resolved target,
    or, while the host's refreshed file stands in its place, the resolved
    login the configuration was prepared to link."""
    source = login_source(config, environ)
    if source in (LoginSource.AMBIENT, LoginSource.TOKEN):
        return None
    target = writeback_target(Path(config) / CREDENTIALS)  # type: ignore[arg-type]
    if target is not None:
        return target.parent
    planned = home(CLAUDE, environ) if source is LoginSource.HARNESS else Path(environ[OPT_IN_VAR])
    return (planned / CREDENTIALS).resolve().parent


def relogin(source: LoginSource) -> str:
    """The one remedy for a login that no longer serves, as a clause; the
    harness login's closes with the login note."""
    if source is LoginSource.HARNESS:
        remedy = f"run `{LOGIN_COMMAND}`"
        return f"{remedy}, then rerun. {login_note(remedy)}"
    if source is LoginSource.TOKEN:
        return ("run `claude setup-token` and export the new token as "
                f"{LONG_LIVED_TOKEN}, then rerun")
    return f"{RELOGIN}, then rerun"


def login_remedy(message: str, source: LoginSource) -> str:
    """`message`, plus the one remedy for the login the run used when the
    reason is that login — which no rerun repairs. Shared by the dev runner,
    the judge and the routing rig."""
    if not LOGIN_FAILURE.search(message):
        return message
    return f"{message}\nThe {source.value} login is no longer valid: {relogin(source)}."


# ---------- the linked login, kept current ---------------------------------------------


def expires_at(path: Path) -> int | None:
    """The access token's expiry in epoch milliseconds; None when absent or unreadable."""
    try:
        value = json.loads(path.read_text(encoding="utf-8"))["claudeAiOauth"]["expiresAt"]
    except (OSError, ValueError, KeyError, TypeError):
        return None
    return value if isinstance(value, int) else None


def needs_refresh(source: Path) -> bool:
    expiry = expires_at(source)
    return expiry is not None and expiry < (time.time() + REFRESH_MARGIN_S) * 1000


def _write_private(path: Path, data: bytes) -> None:
    """Atomic replace through an owner-only temporary file beside `path`
    (`mkstemp` creates it exclusively with mode 0600)."""
    fd, name = tempfile.mkstemp(dir=path.parent, prefix=f"{path.name}.", suffix=".tmp")
    tmp = Path(name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)


def _relink(link: Path, target: Path) -> None:
    tmp = link.with_name(f"{link.name}.relink")
    tmp.unlink(missing_ok=True)
    tmp.symlink_to(target)
    tmp.replace(link)


def settle(link: Path, target: Path) -> bool:
    """If the host replaced `link`, write a newer login back to `target` and
    restore the link. True when something was written back.

    A replacement that does not expire later is discarded rather than written —
    the stored login may have been renewed meanwhile. When either side is
    unreadable both are left for the next look: the host may not be done with
    its file, and a stored login that vanished was logged out on purpose.
    """
    if link.is_symlink() or not link.exists():
        return False
    fresh, stored = expires_at(link), expires_at(target)
    if fresh is None or stored is None:
        return False
    written = fresh > stored
    if written:
        _write_private(target.resolve(), link.read_bytes())
    _relink(link, target)
    return written


def take_claim(claim: Path, mark: str) -> bool:
    """Create the claim exclusively; an abandoned one is removed for the next try."""
    try:
        with claim.open("x", encoding="utf-8") as fh:
            fh.write(mark)
    except FileExistsError:
        with suppress(FileNotFoundError):
            if time.time() - claim.stat().st_mtime > CLAIM_STALE_S:
                claim.unlink()
        return False
    return True


def release_claim(claim: Path, mark: str) -> None:
    """Remove the claim only while it still carries this run's mark."""
    with suppress(OSError):
        if claim.read_text(encoding="utf-8") == mark:
            claim.unlink()


def _target_source(target: Path) -> LoginSource:
    inside = _within(target.resolve(), home(CLAUDE).resolve())
    return LoginSource.HARNESS if inside else LoginSource.OPERATOR


def acquire_claim(source: Path, mark: str) -> Path | None:
    """The refresh claim when this run is about to refresh the linked login,
    None when no refresh is due. Waits a bounded time on another run's claim
    and refuses when that run's refresh never arrives."""
    claim = source.parent / CLAIM_NAME
    deadline = time.monotonic() + CLAIM_WAIT_S
    while needs_refresh(source):
        if take_claim(claim, mark):
            return claim
        if time.monotonic() > deadline:
            sys.exit(
                f"the linked login at {source} has expired and another isolated run "
                f"holds the refresh ({claim}); no refreshed login arrived within "
                f"{CLAIM_WAIT_S}s. Rerun once that run has started; if it keeps "
                f"happening, {relogin(_target_source(source))}."
            )
        time.sleep(CLAIM_POLL_S)
    return None


@contextmanager
def held_claim(directory: Path) -> Iterator[Path]:
    """The refresh claim in `directory`, held unconditionally — logout and
    wipe must not interleave with a run writing a refresh back."""
    claim = directory / CLAIM_NAME
    mark = f"{os.getpid()}-{uuid.uuid4().hex}"
    deadline = time.monotonic() + CLAIM_WAIT_S
    while not take_claim(claim, mark):
        if time.monotonic() > deadline:
            sys.exit(f"an isolated run holds the refresh claim {claim}; rerun once it ends")
        time.sleep(CLAIM_POLL_S)
    try:
        yield claim
    finally:
        release_claim(claim, mark)


class _Keeper(threading.Thread):
    """Polls the link while the configuration is in use; releases the claim once
    the refresh is written back or the hold has passed."""

    def __init__(self, link: Path, target: Path, claim: Path | None, mark: str):
        super().__init__(name="keep-login", daemon=True)
        self.link, self.target, self.claim, self.mark = link, target, claim, mark
        self.stopped = threading.Event()
        self.release_at = time.monotonic() + CLAIM_HOLD_S

    def run(self) -> None:
        while not self.stopped.wait(POLL_S):
            try:
                written = settle(self.link, self.target)
            except OSError:
                written = False  # the next look, or the exit check, retries
            if self.claim and (written or time.monotonic() > self.release_at):
                release_claim(self.claim, self.mark)
                self.claim = None


@contextmanager
def keep_login(link: Path) -> Iterator[None]:
    """Keep the login behind `link` current while the configuration is in
    use; a refresh is written only to `writeback_target(link)`. A
    configuration without a link (a long-lived token) has nothing to keep."""
    target = link_target(link)
    if target is None:
        yield
        return
    mark = f"{os.getpid()}-{uuid.uuid4().hex}"
    keeper = _Keeper(link, target, acquire_claim(target.resolve(), mark), mark)
    keeper.start()
    try:
        yield
    finally:
        keeper.stopped.set()
        keeper.join()
        try:
            settle(link, target)
        except OSError as exc:
            print(f"could not write the refreshed login back to {target}: "
                  f"{exc.strerror}; if the next run cannot authenticate, "
                  f"{relogin(_target_source(target))}", file=sys.stderr)
        if keeper.claim:
            release_claim(keeper.claim, mark)


# ---------- the commands -------------------------------------------------------------


def stdin_is_tty() -> bool:
    return sys.stdin is not None and sys.stdin.isatty()


def agent_session_markers(environ: Mapping[str, str]) -> list[str]:
    """The agent-session marker variables `environ` carries, by name only."""
    return [name for name in AGENT_MARKERS if name in environ]


def logout_note() -> None:
    """Printed before every logout until L3 has passed."""
    if not L3_PASSED:
        print(f"host-login: {L3_CAVEAT[:1].lower()}{L3_CAVEAT[1:]}.", flush=True)


def _logout(record: HostLogin, home_dir: Path, environ: Mapping[str, str]) -> int:
    code, _ = run_client([record.binary, *record.logout_argv],
                         login_env(record, home_dir, environ), interactive=False, cwd=home_dir)
    return code


def _speed_bumps(environ: Mapping[str, str]) -> str | None:
    if not stdin_is_tty():
        return ("host-login is interactive and needs a terminal: run it yourself, in a "
                "terminal outside any agent session")
    markers = agent_session_markers(environ)
    if markers:
        return (f"host-login refuses inside an agent session ({', '.join(markers)} set): run "
                "it yourself, in a terminal outside any agent session")
    return None


def _start_over(record: HostLogin, home_dir: Path, environ: Mapping[str, str], *,
                reset: bool, logged_in: bool) -> LoginProblem | None:
    """Under the claim: log out of the home's login, if it holds one, and
    with `reset` wipe and reseed the home. A logout that fails stops here:
    wiping or logging in over a login whose logout did not go through could
    orphan a live grant."""
    if logged_in:
        logout_note()
    with held_claim(home_dir):
        code = _logout(record, home_dir, environ) if logged_in else 0
        if code != 0:
            again = RESET_COMMAND if reset else LOGIN_COMMAND
            return LoginProblem(f"the client's logout in {home_dir} exited {code}, so the "
                                "login there was neither replaced nor wiped",
                                f"rerun `{again}` once the client can log out")
        if reset:
            problem = wipe(home_dir)
            if problem:
                return problem
            seed(record, home_dir)
    return None


def _home_or_problem(record: HostLogin, environ: Mapping[str, str]) -> Path | LoginProblem:
    root = state_root(environ)
    return (check_location(root, environ) or profile_problem(environ)
            or root / "hosts" / record.name)


def _holds_login(record: HostLogin, home_dir: Path) -> bool:
    """An existing home's login: its credentials file (Linux), or the host's
    own status, where the login is no file (the macOS Keychain)."""
    return ((home_dir / record.credentials).exists()
            or bool(read_status(record, home_dir).get("loggedIn")))


def cmd_login(record: HostLogin, args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    """Seed a missing home; refuse an existing one the harness did not make,
    with or without `--reset`; log out first over an existing login."""
    bump = _speed_bumps(environ)
    if bump:
        print(bump, file=sys.stderr)
        return EXIT_USAGE
    home_dir = _home_or_problem(record, environ)
    if isinstance(home_dir, LoginProblem):
        print(refusal(home_dir), file=sys.stderr)
        return EXIT_NOT_READY
    existed = home_dir.exists() or home_dir.is_symlink()
    foreign = not_harness_made(home_dir) if existed else None
    if foreign:
        print(refusal(foreign), file=sys.stderr)
        return EXIT_NOT_READY
    if not existed:
        seed(record, home_dir)
    logged_in = existed and _holds_login(record, home_dir)
    if logged_in or (existed and args.reset):
        problem = _start_over(record, home_dir, environ, reset=args.reset, logged_in=logged_in)
        if problem:
            print(refusal(problem), file=sys.stderr)
            return EXIT_NOT_READY
    run_client([record.binary, *record.login_argv], login_env(record, home_dir, environ),
               interactive=True, cwd=home_dir)
    return cmd_status(record, args, environ)


def cmd_logout(record: HostLogin, _args: argparse.Namespace,
               environ: Mapping[str, str]) -> int:
    """Log the client out of the home. A missing home has nothing to log out;
    an existing path the harness did not make is refused like every command
    refuses it, so a foreign login there is never logged out."""
    home_dir = _home_or_problem(record, environ)
    if isinstance(home_dir, LoginProblem):
        print(refusal(home_dir), file=sys.stderr)
        return EXIT_NOT_READY
    if not (home_dir.exists() or home_dir.is_symlink()):
        print(f"no harness login home at {home_dir}: nothing to log out")
        return EXIT_READY
    foreign = not_harness_made(home_dir)
    if foreign:
        print(refusal(foreign), file=sys.stderr)
        return EXIT_NOT_READY
    logout_note()
    with held_claim(home_dir):
        code = _logout(record, home_dir, environ)
    print(f"host-logout: the client's logout exited {code}; the home keeps its marker and "
          "settings")
    return EXIT_READY if code == 0 else EXIT_NOT_READY


def _span(seconds: float) -> str:
    if seconds >= 2 * 86400:
        return f"{int(seconds // 86400)}d"
    if seconds >= 3600:
        return f"{int(seconds // 3600)}h"
    return f"{int(seconds // 60)}m"


def access_expires(home_dir: Path, now: float | None = None) -> str:
    """How long the home's access token remains valid, from `expiresAt` only."""
    expiry = expires_at(home_dir / CREDENTIALS)
    if expiry is None:
        return "unknown"
    delta = expiry / 1000 - (time.time() if now is None else now)
    return f"in {_span(delta)}" if delta >= 0 else f"expired {_span(-delta)} ago"


RUNS_USE = {LoginSource.HARNESS: "harness",
            LoginSource.TOKEN: f"token ({LONG_LIVED_TOKEN} exported)",
            LoginSource.OPERATOR: f"operator ({OPT_IN_VAR})"}


def _yes(flag: bool) -> str:
    return "yes" if flag else "no"


def status_report(record: HostLogin, home_dir: Path, status: Mapping,
                  environ: Mapping[str, str]) -> dict[str, str]:
    """The status lines: booleans, enums, names and a duration — never a
    credential, an email address or an organization."""
    reported = status.get("configDirectory")
    offenders = home_offenders(record, home_dir) if home_dir.is_dir() else []
    return {
        "home": str(home_dir),
        "marker": _yes((home_dir / MARKER).is_file()),
        "logged_in": _yes(bool(status.get("loggedIn"))),
        "auth_method": str(status.get("authMethod") or "-"),
        "api_provider": str(status.get("apiProvider") or "-"),
        "config_dir_matches": _yes(bool(reported) and Path(str(reported)).resolve()
                                   == home_dir.resolve()),
        "clean": ", ".join(offenders) if offenders else _yes(home_dir.is_dir()),
        "access_expires": access_expires(home_dir),
        "runs_use": RUNS_USE[planned_source(environ)],
    }


def cmd_status(record: HostLogin, _args: argparse.Namespace,
               environ: Mapping[str, str]) -> int:
    root = state_root(environ)
    home_dir = root / "hosts" / record.name
    problem = check_location(root, environ) or profile_problem(environ)
    status = read_status(record, home_dir) if not problem and home_dir.is_dir() else {}
    for key, value in status_report(record, home_dir, status, environ).items():
        print(f"{key}: {value}")
    problem = problem or (check_presence(home_dir) or check_home(record, home_dir)
                          or check_status(status, home_dir))
    if problem:
        print(refusal(problem), file=sys.stderr)
        return EXIT_NOT_READY
    return EXIT_READY


COMMANDS = {"login": cmd_login, "status": cmd_status, "logout": cmd_logout}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="host_login", description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)
    login = sub.add_parser("login", help="log the harness home in (the operator, interactive)")
    login.add_argument("client", choices=sorted(RECORDS))
    login.add_argument("--reset", action="store_true",
                       help="log out, wipe the marked home, seed it again, then log in")
    status = sub.add_parser("status", help="report the harness home; no model call")
    status.add_argument("client", nargs="?", default="claude", choices=sorted(RECORDS))
    logout = sub.add_parser("logout", help="run the client's logout in the harness home")
    logout.add_argument("client", choices=sorted(RECORDS))
    return parser


def main(argv: list[str] | None = None) -> int:
    """Exit 0 ready, 2 usage or refused to start, 3 not ready (untested)."""
    args = build_parser().parse_args(argv)
    return COMMANDS[args.command](RECORDS[args.client], args, os.environ)


if __name__ == "__main__":
    sys.exit(main())
