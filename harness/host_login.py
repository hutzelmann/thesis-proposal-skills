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
harness login's status checks — from the record's allowlist, plus what the
record sets (`HostLogin.child_vars`): for Claude the configuration directory,
the connector switch and the empty profile directory; for Codex `CODEX_HOME`
alone.

**The Codex record** (`CODEX`, add-codex-dev-runner). Its home,
`state_root()/hosts/codex`, must also lie outside the system temporary
directory (`check_location(..., tempdir=)`), where Codex refuses to place its
helper binaries. Before the first login it is seeded with `PINNED_CONFIG_TOML`
(OpenAI's provider, the ChatGPT login required, a file credential store, and
web search, the update check, history, analytics, feedback and bundled skills
off), which every run compares key by key (`check_codex_home`). Its login is
`codex login [--device-auth]`, never an API-key or access-token login, in a
login environment without any `CODEX_*`, `OPENAI_*`, `OPENROUTER_*` or
`*_API_KEY` variable. Its `auth.json` is never opened: `auth_age` reads only
its modification time. Until live check X8 passes (`X8_PASSED`), every message
whose remedy is `host-login codex` says that its effect on the operator's
other ChatGPT sessions is unverified (`NOTES`, `login_note(remedy, client)`).

**The Copilot record** (`COPILOT`, add-copilot-dev-runner). Its credential is a
token file, not a client login (`HostLogin.credential`): a fine-grained
personal access token carrying only "Copilot Requests", which `host-login
copilot` reads at a hidden prompt, refuses unless it begins with `github_pat_`
(`token_problem`; the message never echoes it), and writes to
`<state>/hosts/copilot.token` at 0600 (`token_path`) — beside the home, never
inside it, so no grant the client gives its sandbox on its own home covers it.
Only that login, `host-logout copilot` (which deletes the file and names the
page where the token is revoked) and `copilot_cli.token_env` touch the file;
no Copilot client login ever runs, and the operator's keyring, `~/.copilot`,
`~/.config/github-copilot` and `~/.config/gh` are never read. Every login
records an approval stop (`copilot_cli.record_stop`), and only `host-login
copilot --clear-stop`, run by the operator in a terminal, clears it: that is
the go for the next model call. Before the token prompt the home is seeded
with `pinned_settings` — auto-update, auto-model switching, hooks, memory,
editor auto-connect and experimental features off, custom agents local, and
the OS sandbox pinned (no bypass, no git or gh credentials, no developer-tool
grants) with a deny list built by construction from the password database:
the operator's whole real home, `/run/user/<uid>`, the state root where it
lies outside that home, and the token file. `check_copilot_home` holds the
home to an allow-list, because the client's `config.json` overrides
`settings.json` key by key. The child environment adds `TERM=dumb`,
`NO_COLOR=1`, `DBUS_SESSION_BUS_ADDRESS=disabled:`, `COPILOT_AUTO_UPDATE=false`,
`COPILOT_CACHE_HOME=<state>/cache/copilot` and an empty `GH_CONFIG_DIR` to the
admitted plumbing; the token is added after the builder, by the caller.
`status copilot [--models] [--no-token]` runs the model-free status read
(`copilot_cli.status`).

**The Codex run lock.** `run_lock` takes an exclusive `flock` on
`<home>/.harness-run.lock` within `LOCK_WAIT_S`, else raises `RunLockBusy`
(untested, exit 3); on a platform without POSIX file locks it raises
`RunLockUnsupported`, and the Codex login and logout refuse before creating
anything. Runs, the quota read, logins, logouts, resets and `status codex
--quota` take it; a run's child receives the descriptor and holds the lock
for as long as it lives (`run_host(..., pass_fds=)`), and on Linux gets a
parent-death interrupt (`child_preexec`).

**Stopping a child.** `stop_child` sends the client's own stop request — a
termination request to Claude, an interrupt to Codex (`HostLogin.stop_signal`),
which ends its turn — and kills only after `TERM_GRACE_S`, so a host part-way
through writing a refreshed login can finish (whether Claude Code does is live
check L9). `run_host` and `run_client` (the logouts and the status check at
`CLIENT_TIMEOUT_S`) both pass the record's stop signal.

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
  uv run poe host-login claude [--reset]                 # the operator, in a terminal
  uv run poe host-login codex [--reset] [--device-auth]  # the operator, in a terminal
  uv run poe host-login copilot [--reset | --clear-stop] # the operator, in a terminal
  uv run poe host-status [claude]                        # anyone; no model call
  uv run poe host-status codex [--quota]                 # anyone; no model call
  uv run poe host-status copilot [--models] [--no-token] # anyone; no model call
  uv run poe host-logout claude|codex|copilot            # the operator
"""

from __future__ import annotations

import argparse
import ctypes
import getpass
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
import tomllib
import uuid
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import ExitStack, contextmanager, nullcontext, suppress
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePath

try:  # POSIX file locks: the Codex run lock; the Codex runner refuses without them
    import fcntl
except ImportError:  # Windows
    fcntl = None  # type: ignore[assignment]
try:  # the password database: the Copilot deny list's account home
    import pwd
except ImportError:  # Windows, where the Copilot runner refuses to start
    pwd = None  # type: ignore[assignment]

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
# Live check X8, the same question for Codex, whose logout revokes the home's
# refresh token and whose login revokes the previous one held there
# (`cli_login.rs:122-153` @0.160). add-codex-dev-runner task 6.4 flips it once
# the user has observed it pass; the L0 tests cover both values.
X8_PASSED = False
CODEX_NOT_AFFECTED = "Your own Codex login is not affected"
X8_CAVEAT = "Whether this logs out your other ChatGPT sessions is unverified (X8)"
# A token-file client has no revocation check: its login and logout touch only
# the token file, never a client login (add-copilot-dev-runner Decision 3).
NO_REVOCATION_CHECK = True
COPILOT_NOT_AFFECTED = "Your own Copilot login is not affected"
# per client: the not-affected sentence, the caveat, and the name of its pass
# flag (read at call time, so a flip or a test's monkeypatch takes effect)
NOTES = {"claude": (NOT_AFFECTED, L3_CAVEAT, "L3_PASSED"),
         "codex": (CODEX_NOT_AFFECTED, X8_CAVEAT, "X8_PASSED"),
         "copilot": (COPILOT_NOT_AFFECTED, None, "NO_REVOCATION_CHECK")}

# The Codex run lock (design Decision 7): judgment, not a host constant. Runs
# are serial by design, and a waiter is a second invocation the operator
# started, which should fail fast rather than queue behind a ten-minute run.
LOCK_NAME = ".harness-run.lock"
LOCK_WAIT_S = 30
LOCK_POLL_S = 0.2
PR_SET_PDEATHSIG = 1

# Variables a Claude Code session, or Codex's sandboxed shell, exports to the
# commands it runs. Their presence refuses `login` (a speed bump, not a guard:
# a marker can be unset). Whether the Codex pair is complete is unverified:
# observing an unsandboxed Codex shell's exports would take a model call, so
# add-codex-dev-runner keeps the pair (design, Open Questions); the AGENTS.md
# rule that agents never log in is the guard.
# The 1.0.91 V-pass found no variable the Copilot shell tool exports to its
# commands (add-copilot-dev-runner design, Facts at 1.0.91), so the set is
# unchanged for Copilot.
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
    directory); `forbidden` lists globs whose matches make a home unclean,
    `allowed` the matches that stay allowed; `fixed_env` and `profile` are
    what `allowlisted_env` sets beside the admitted names; `failure` is the
    host's wording for a login it cannot use. The defaulted fields came with
    the Codex record and leave Claude's behaviour as it was: `strip_suffixes`
    widens the stripped families, `stop_signal` is the client's own stop
    request, and `outside_tempdir` bars a home inside the system temporary
    directory. The per-client behaviour of the commands is data too:
    `run_locked` (the client's runs, logins, logouts and resets take the run
    lock, not the refresh claim), `login_in_status` (where the login is no
    file in the home, the client's own status decides whether it holds one),
    `offenders` (what makes the home unclean, in place of `home_offenders`)
    and `status_command` (the client's own `status`). A client that reads an
    Anthropic profile directory is one with a `profile`.

    The Copilot record added the rest, again with defaults that leave Claude
    and Codex as they were: `credential` is the kind of harness login —
    `client-login` (the client's own login, run in the home) or `token-file`
    (a token in one file beside the home, handed to the client's children
    under `token_env` only); `strip_names` are exact names stripped beside the
    prefix and suffix families; `home_env` adds variables derived from the
    home to `child_vars`; `dynamic_seed` adds seed files whose content depends
    on the home (Copilot's settings carry the deny list's absolute paths)."""

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
    strip_suffixes: tuple[str, ...] = ()
    stop_signal: int = signal.SIGTERM
    outside_tempdir: bool = False
    allowed: tuple[str, ...] = ()
    run_locked: bool = False
    login_in_status: bool = True
    offenders: Callable[[Path], list[str]] | None = None
    status_command: Callable[[argparse.Namespace, Mapping[str, str]], int] | None = None
    credential: str = "client-login"
    token_env: str | None = None
    strip_names: frozenset[str] = frozenset()
    home_env: Callable[[PurePath], Mapping[str, str]] | None = None
    dynamic_seed: Callable[[Path], Mapping[str, str]] | None = None

    def child_vars(self, config: PurePath) -> dict[str, str]:
        """What the harness itself sets in every child of this client, replacing
        any inherited value: the configuration directory, the fixed variables,
        the profile directory and the variables derived from the home. For
        Codex that is `CODEX_HOME` alone, which makes it the pre-spawn
        assertion's exact exemption set; for Copilot it is the home, the cache,
        the update switch, the disabled session bus and the empty GitHub CLI
        directory (never a scratch directory, never the token)."""
        env = {self.home_var: str(config), **self.fixed_env}
        if self.profile:
            variable, directory = self.profile
            env[variable] = str(config / directory)
        if self.home_env:
            env.update(self.home_env(config))
        return env

    def stripped(self, name: str) -> bool:
        """Whether an inherited variable belongs to the families every login,
        logout and (for Codex and Copilot) child drops."""
        return name in self.strip_names or name.startswith(self.login_strip_prefixes) or (
            bool(self.strip_suffixes) and name.endswith(self.strip_suffixes))

    @property
    def login_command(self) -> str:
        return f"uv run poe host-login {self.name}"

    @property
    def reset_command(self) -> str:
        return f"{self.login_command} --reset"


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

# The Codex home's configuration (design Decision 5), written before the first
# login and compared key by key on every run. The stdlib has no TOML writer, so
# this is one fixed text and one parse, and an L0 test holds them equal. The key
# names are unverified for 0.160 until live check X7; every run also passes
# `--strict-config`, which fails a misspelled key visibly.
PINNED_CONFIG_TOML = """\
model_provider = "openai"
forced_login_method = "chatgpt"
cli_auth_credentials_store = "file"
web_search = "disabled"
check_for_update_on_startup = false

[history]
persistence = "none"

[analytics]
enabled = false

[feedback]
enabled = false

[skills.bundled]
enabled = false
"""
PINNED_CONFIG = {
    "model_provider": "openai",
    "forced_login_method": "chatgpt",
    "cli_auth_credentials_store": "file",
    "web_search": "disabled",
    "check_for_update_on_startup": False,
    "history": {"persistence": "none"},
    "analytics": {"enabled": False},
    "feedback": {"enabled": False},
    "skills": {"bundled": {"enabled": False}},
}
CODEX_CONFIG = "config.toml"
CODEX_AUTH = "auth.json"
# the first catalog that serves the current Plus models
CODEX_MIN_VERSION = (0, 160, 0)
CODEX_UPDATE = "update the Codex CLI through your package manager to {} or later"

CODEX = HostLogin(
    name="codex",
    binary="codex",
    home_var="CODEX_HOME",
    # the ChatGPT login only: never `--with-api-key` or `--with-access-token`;
    # `--device-auth` is appended on request
    login_argv=("login",),
    status_argv=("login", "status"),
    logout_argv=("logout",),
    # the same machine plumbing, without Claude's long-lived token
    admitted=CLAUDE_ADMITTED - {LONG_LIVED_TOKEN},
    admitted_prefixes=("LC_",),
    # every variable that could bill a run per token or steer it at another
    # login: `exec` honours CODEX_API_KEY above every stored login
    login_strip_prefixes=("CODEX_", "OPENAI_", "OPENROUTER_"),
    seed={CODEX_CONFIG: PINNED_CONFIG_TOML},
    # an instruction file, a start-up environment file, hooks, skills other
    # than the client's bundled system skills, and memories
    forbidden=("AGENTS.md", "AGENTS.override.md", ".env", "hooks.json", "skills/*",
               "memories/*"),
    plugin_record=None,
    fixed_env={},
    profile=None,
    credentials=CODEX_AUTH,
    # the refresh failures (`manager.rs:206-208` @0.160), the login
    # restriction's logout line, and no login at all
    failure=re.compile(r"refresh token (?:has expired|was already used|was revoked)"
                       r"|ChatGPT login is required, but an API key is currently being used"
                       r"|Not logged in"),
    strip_suffixes=("_API_KEY",),
    # an interrupt ends the turn, so a pending auth.json write can finish
    stop_signal=signal.SIGINT,
    outside_tempdir=True,
    allowed=("skills/.system",),
    run_locked=True,
    # the pinned configuration keeps the login in `auth.json`, never opened
    login_in_status=False,
    offenders=lambda home_dir: codex_offenders(home_dir),
    status_command=lambda args, environ: cmd_status_codex(args, environ),
)
# ---------- the Copilot record (add-copilot-dev-runner Decisions 3 to 6) ------------------

COPILOT_SETTINGS = "settings.json"
COPILOT_CONFIG = "config.json"
TOKEN_FILE = "copilot.token"
TOKEN_PREFIX = "github_pat_"
CLASSIC_PREFIX = "ghp_"
TOKEN_PROMPT = "Fine-grained token (Copilot Requests only): "
TOKEN_PAGE = "github.com/settings/personal-access-tokens"
# the one remedy for a token Copilot rejects, a missing or classic one included
COPILOT_TOKEN_REMEDY = (f"create a fine-grained token that carries only Copilot Requests "
                        f"({TOKEN_PAGE}/new), then run `uv run poe host-login copilot --reset`")
CLEAR_STOP_COMMAND = "uv run poe host-login copilot --clear-stop"
# The top-level keys of the client's own state file a token-mode home may
# develop. Starts from the operator's home; live check K3 fixes it at the pin,
# and widening it is a reviewed change (design Decision 6).
MANAGED_STATE_KEYS = frozenset({"expAssignmentsCache", "firstLaunchAt", "lastLoggedInUser",
                                "loggedInUsers"})
# the only entries a clean Copilot home holds, besides `session-store.db*`;
# `session-state/` and `gh/` must also be empty (Decision 6)
COPILOT_ALLOWED = frozenset({COPILOT_SETTINGS, COPILOT_CONFIG, "session-state", "gh", MARKER,
                             LOCK_NAME, "quota.json"})
COPILOT_EMPTY_DIRS = ("session-state", "gh")


def token_path(home_dir: Path) -> Path:
    """The token file: `<state>/hosts/copilot.token`, a sibling of the home and
    never inside it (Decision 4). Read only by `copilot_cli.token_env`, written
    only by the login, deleted only by the login and the logout."""
    return home_dir.parent / TOKEN_FILE


def account_home(uid: int | None = None) -> Path:
    """The operator's real home from the password database, never `$HOME`: a
    child's `HOME` is a scratch directory, so a deny list built from it would
    leave the real home readable. Windows (refused by the runner) falls back
    to the profile directory."""
    if pwd is None:
        return Path.home()
    return Path(pwd.getpwuid(os.getuid() if uid is None else uid).pw_dir)


def deny_list(home_dir: Path, account: Path, uid: int | None = None) -> list[str]:
    """The sandbox deny list, built by construction (Decision 3): the whole
    account home, the per-user runtime directory (the session bus and the
    agent sockets), the state root where it lies outside the account home,
    and the token file — absolute paths, so no `~` resolves under scratch."""
    uid = (os.getuid() if hasattr(os, "getuid") else 0) if uid is None else uid
    state = home_dir.parent.parent
    deny = [str(account), f"/run/user/{uid}"]
    if not _within(state.resolve(), account.resolve()):
        deny.append(str(state))
    return [*deny, str(token_path(home_dir))]


def pinned_settings(home_dir: Path, account: Path, uid: int | None = None) -> dict:
    """The Copilot home's `settings.json` (Decision 3): auto-update, the switch
    to automatic model selection, hooks, memory, editor auto-connect and
    experimental features off, custom agents local, a file token store, and
    the OS sandbox pinned — enabled, no bypass, no developer-tool grants, no
    git or gh credentials — with the deny list at the key path the 1.0.91
    package reads, `sandbox.userPolicy.filesystem.deniedPaths`."""
    return {
        "autoUpdate": False, "continueOnAutoMode": False,
        "customAgents": {"defaultLocalOnly": True}, "disableAllHooks": True,
        "experimental": False, "ide": {"autoConnect": False}, "memory": False,
        "storeTokenPlaintext": True,
        "sandbox": {"enabled": True, "allowBypass": False, "allowDevToolAccess": False,
                    "auth": {"git": False, "gh": False},
                    "userPolicy": {"filesystem": {
                        "deniedPaths": deny_list(home_dir, account, uid)}}},
    }


def copilot_home_env(home_dir: PurePath) -> dict[str, str]:
    """The variables a Copilot child gets from its home (Decision 5): the
    persistent package cache outside the home, and the empty GitHub CLI
    configuration directory inside it."""
    return {"COPILOT_CACHE_HOME": str(home_dir.parent.parent / "cache" / "copilot"),
            "GH_CONFIG_DIR": str(home_dir / "gh")}


def _settings_seed(home_dir: Path) -> dict[str, str]:
    return {COPILOT_SETTINGS: json.dumps(pinned_settings(home_dir, account_home()), indent=2)
            + "\n"}


COPILOT = HostLogin(
    name="copilot",
    binary="copilot",
    home_var="COPILOT_HOME",
    # a token-file record runs no client login, logout or status command
    login_argv=(),
    status_argv=(),
    logout_argv=(),
    admitted=CLAUDE_ADMITTED - {LONG_LIVED_TOKEN},
    admitted_prefixes=("LC_",),
    # every variable that could bill a run elsewhere, act as another account
    # or route it to a third-party provider: an environment token outranks
    # every other credential in the client
    login_strip_prefixes=("COPILOT_", "GITHUB_", "GH_", "CAPI_", "OTEL_", "OPENAI_",
                          "ANTHROPIC_", "AZURE_OPENAI_"),
    seed={"gh/": ""},
    forbidden=(),
    plugin_record=None,
    fixed_env={"TERM": "dumb", "NO_COLOR": "1",
               # set, not dropped: the GitHub CLI's bus library falls back to
               # /run/user/<uid>/bus when the variable is empty
               "DBUS_SESSION_BUS_ADDRESS": "disabled:",
               "COPILOT_AUTO_UPDATE": "false"},
    profile=None,
    credentials=TOKEN_FILE,
    # the session errors that mean the token no longer serves
    failure=re.compile(r"\b(?:authentication|authorization)\b"),
    strip_suffixes=("_TOKEN", "_API_KEY"),
    run_locked=True,
    login_in_status=False,
    offenders=lambda home_dir: copilot_offenders(home_dir),
    status_command=lambda args, environ: cmd_status_copilot(args, environ),
    credential="token-file",
    token_env="COPILOT_GITHUB_TOKEN",
    strip_names=frozenset({"BASH_ENV", "SSH_AUTH_SOCK"}),
    home_env=copilot_home_env,
    dynamic_seed=_settings_seed,
)
RECORDS: Mapping[str, HostLogin] = {"claude": CLAUDE, "codex": CODEX, "copilot": COPILOT}
LOGIN_FAILURE = CLAUDE.failure


@dataclass(frozen=True)
class LoginProblem:
    """Why the harness login cannot serve a run: the cause, its one remedy,
    the client whose login note closes the refusal, and which of the three
    kinds of untested it is (`subscription`, `isolation` or `precondition`;
    add-codex-dev-runner design Decision 12), set where the problem is built."""

    cause: str
    remedy: str
    client: str = "claude"
    kind: str = "subscription"


class RunLockRefused(Exception):
    """The Codex run lock could not be taken. Carries the `LoginProblem` that
    `refusal` renders; the runner maps it to untested and `main` to exit 3."""

    def __init__(self, problem: LoginProblem):
        super().__init__(problem.cause)
        self.problem = problem


class RunLockBusy(RunLockRefused):
    """The Codex run lock stayed held past `LOCK_WAIT_S`."""


class RunLockUnsupported(RunLockRefused):
    """This platform has no POSIX file locks (Windows), so no run lock."""


NO_FILE_LOCKS = LoginProblem(
    "this platform lacks POSIX file locks (fcntl), which the Codex run lock needs",
    "run the Codex harness commands on Linux or macOS", "codex", "precondition")


def no_file_locks(record: HostLogin) -> LoginProblem:
    """`NO_FILE_LOCKS`, worded for the record whose run lock it concerns."""
    if record is CODEX:
        return NO_FILE_LOCKS
    title = record.name.capitalize()
    return LoginProblem(f"this platform lacks POSIX file locks (fcntl), which the {title} run "
                        "lock needs", f"run the {title} harness commands on Linux or macOS",
                        record.name, "precondition")


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
    token (testing-harness spec: Isolated child environment). For Codex, the
    record's own allowlist and `CODEX_HOME` make the base of every Codex
    child's environment (testing-harness spec: Codex plan billing guard)."""
    source = os.environ if environ is None else environ
    env = {name: value for name, value in source.items()
           if name in record.admitted or name.startswith(record.admitted_prefixes)}
    env.update(record.child_vars(config))
    return env


def login_env(record: HostLogin, home: Path, environ: Mapping[str, str]) -> dict[str, str]:
    """The environment of every login and logout: the operator's own, so that
    a browser can open, less every billing and host-session variable of the
    client, with the configuration directory set to the home (and for Claude
    the profile directory to the home's empty one). `environ` is not
    modified."""
    env = {name: value for name, value in environ.items() if not record.stripped(name)}
    env.update(record.child_vars(home))
    return env


# ---------- stopping a child, and running one to completion ---------------------------


def stop_child(proc: subprocess.Popen, sig: int = signal.SIGTERM) -> int:
    """Stop a host: send the client's own stop request — a termination request
    by default, the record's `stop_signal` where a caller passes it (an
    interrupt for Codex, which ends its turn) — give it TERM_GRACE_S, then kill
    it. On Windows `terminate()` is TerminateProcess, so the kill is the
    request. The exit status is the harness's own, not the host's verdict."""
    with suppress(ProcessLookupError):
        if sig == signal.SIGTERM or os.name != "posix":
            proc.terminate()
        else:
            proc.send_signal(sig)
    try:
        return proc.wait(timeout=TERM_GRACE_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        return proc.wait()


def child_preexec(record: HostLogin) -> Callable[[], None] | None:
    """On Linux, a `preexec_fn` that makes the kernel send the child the
    record's stop signal when the harness dies (`prctl(PR_SET_PDEATHSIG)`):
    an interrupt for Codex, not a kill, so a pending login write can finish.
    None elsewhere — macOS has no such signal, which the README states."""
    if not sys.platform.startswith("linux"):
        return None
    libc = ctypes.CDLL(None, use_errno=True)  # loaded before the fork
    stop = int(record.stop_signal)

    def set_parent_death_signal() -> None:
        libc.prctl(PR_SET_PDEATHSIG, stop, 0, 0, 0)

    return set_parent_death_signal


Starter = Callable[..., subprocess.Popen]


def _popen(argv: Sequence[str], *, cwd: Path, env: Mapping[str, str], stdin: int,
           pass_fds: Sequence[int], record: HostLogin) -> subprocess.Popen:
    return subprocess.Popen(list(argv), cwd=cwd, env=dict(env), stdin=stdin,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                            encoding="utf-8", errors="replace", pass_fds=tuple(pass_fds),
                            preexec_fn=child_preexec(record))


def run_host(record: HostLogin, argv: Sequence[str], *, cwd: Path, env: Mapping[str, str],
             timeout: float, input: str | None = None, pass_fds: Sequence[int] = (),
             start: Starter | None = None) -> tuple[int, str, str]:
    """Run a host child to completion and return its exit status, stdout and
    stderr. At `timeout` the child gets the record's stop request
    (`stop_child`), and `TimeoutExpired` is re-raised carrying what the child
    wrote. `pass_fds` hands it descriptors — the Codex run lock, which it then
    holds for as long as it lives. `start` replaces the plain `Popen`: the
    Codex runner passes the starter that checks the final environment first."""
    starter = start or partial_popen(record)
    proc = starter(argv, cwd=cwd, env=env,
                   stdin=subprocess.PIPE if input is not None else subprocess.DEVNULL,
                   pass_fds=pass_fds)
    try:
        out, err = proc.communicate(input, timeout=timeout)
    except subprocess.TimeoutExpired as late:
        stop_child(proc, record.stop_signal)
        late.output, late.stderr = proc.communicate()
        raise
    return proc.returncode, out or "", err or ""


def partial_popen(record: HostLogin) -> Starter:
    def start(argv: Sequence[str], **kwargs) -> subprocess.Popen:
        return _popen(argv, record=record, **kwargs)

    return start


@contextmanager
def run_lock(home_dir: Path, wait: float | None = None,
             record: HostLogin | None = None) -> Iterator[int]:
    """The run lock of a client whose runs are serial — Codex by default,
    Copilot with `record=COPILOT`: an exclusive `flock` on
    `<home>/.harness-run.lock`, taken within `wait` (default LOCK_WAIT_S) or
    refused with `RunLockBusy`.
    Yields the descriptor, which a child receives through `pass_fds`: `flock`
    binds to the open file description, so the lock stays held while that
    child lives, even after the harness is killed. The harness never unlocks
    explicitly — that would release the child's hold too; it only closes.

    The descriptor is inheritable, so a process the model starts inside
    `codex exec` and leaves running may hold the lock too (unverified until
    the first live run); the refusal therefore names `fuser`, which shows
    the holder. Without POSIX file locks it raises `RunLockUnsupported`."""
    record = record or CODEX
    if fcntl is None:
        raise RunLockUnsupported(no_file_locks(record))
    path = home_dir / LOCK_NAME
    handle = path.open("ab")  # binary: the lock file holds nothing
    with suppress(OSError):
        path.chmod(0o600)
    deadline = time.monotonic() + (LOCK_WAIT_S if wait is None else wait)
    while True:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            if time.monotonic() >= deadline:
                handle.close()
                raise RunLockBusy(LoginProblem(
                    f"another {record.name.capitalize()} run holds the harness home ({path}), "
                    f"or a process a run left behind does (`fuser -v {path}` names it)",
                    "rerun after it ends", record.name, "precondition")) from None
            time.sleep(LOCK_POLL_S)
    try:
        yield handle.fileno()
    finally:
        handle.close()


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
    """Every client's own configuration directory: Claude's, Codex's and
    Copilot's (`~/.copilot`, `~/.config/github-copilot`), and those an
    inherited configuration variable names."""
    dirs = [user / ".claude", user / ".codex", user / ".copilot",
            user / ".config" / "github-copilot"]
    return dirs + [Path(environ[name]) for name in ("CLAUDE_CONFIG_DIR", "CODEX_HOME",
                                                    "COPILOT_HOME") if environ.get(name)]


def system_tempdir() -> str:
    """The system temporary directory, which a Codex home may not lie in; the
    seam L0 tests replace, since their own `tmp_path` lies inside it."""
    return tempfile.gettempdir()


def check_location(root: Path, environ: Mapping[str, str], repo: Path = REPO,
                   user_home: Path | None = None, *, record: HostLogin | None = None,
                   tempdir: str | Path | None = None) -> LoginProblem | None:
    """Refuse a state root that is not absolute, that equals or contains the
    user's home, that equals, contains or lies inside a client's own
    configuration directory, or that lies inside the repository — and, for a
    record that must live `outside_tempdir` (Codex, which refuses to place its
    helper binaries there), one at or inside `tempdir`. Applied to every
    resolved root, the default included; containment is tested on resolved
    paths, so a symlink cannot route around it. A relative root would resolve
    against whichever directory a command runs in — the home itself, for a
    login — and a link to it would dangle. The pure check takes the temporary
    directory as an argument; callers fill it from `system_tempdir()`."""
    record = record or CLAUDE
    remedy = (f"point {STATE_VAR} at a directory of its own, outside the repository and every "
              f"client's configuration directory, or unset it")
    if not root.is_absolute():
        return LoginProblem(f"the harness state directory {root} is not an absolute path",
                            f"give {STATE_VAR} an absolute path, or unset it", record.name)
    user = (Path.home() if user_home is None else user_home).resolve()
    resolved = root.resolve()
    if _within(user, resolved):
        return LoginProblem(f"the harness state directory {root} equals or contains your home "
                            f"directory {user}", remedy, record.name)
    for client in _client_dirs(environ, user):
        target = client.resolve()
        if _within(resolved, target) or _within(target, resolved):
            return LoginProblem(f"the harness state directory {root} overlaps the client "
                                f"configuration directory {client}", remedy, record.name)
    if _within(resolved, repo.resolve()):
        return LoginProblem(f"the harness state directory {root} lies inside the repository "
                            f"{repo}", remedy, record.name)
    if record.outside_tempdir and tempdir is not None and _within(resolved,
                                                                  Path(tempdir).resolve()):
        return LoginProblem(f"the harness state directory {root} lies inside the system "
                            f"temporary directory {tempdir}, where {record.binary} refuses to "
                            "place its helper binaries",
                            f"point {STATE_VAR} or XDG_STATE_HOME at a directory outside "
                            f"{tempdir}, or unset it", record.name)
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
    files = {**record.seed, **(record.dynamic_seed(home_dir) if record.dynamic_seed else {})}
    for rel, content in files.items():
        path = home_dir / rel
        if rel.endswith("/"):
            path.mkdir(mode=0o700, parents=True, exist_ok=True)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")


def not_harness_made(home_dir: Path, record: HostLogin | None = None) -> LoginProblem | None:
    """Why `home_dir` is no home the harness created: a symbolic link, or a
    path without the marker. The harness neither deletes nor adopts it."""
    record = record or CLAUDE
    if home_dir.is_symlink():
        return LoginProblem(f"{home_dir} is a symbolic link, not a harness login home",
                            f"remove the link, then run `{record.login_command}`", record.name)
    if not (home_dir / MARKER).is_file():
        return LoginProblem(f"{home_dir} carries no {MARKER} marker, so the harness did not "
                            "create it", f"move it aside, then run `{record.login_command}`",
                            record.name)
    return None


def wipe(home_dir: Path, record: HostLogin | None = None) -> LoginProblem | None:
    """Delete the home — only a marked home that is not a symbolic link.
    Otherwise refuse, naming the directory, and delete nothing."""
    problem = not_harness_made(home_dir, record)
    if problem:
        return problem
    shutil.rmtree(home_dir)
    return None


def check_presence(home_dir: Path, record: HostLogin | None = None) -> LoginProblem | None:
    """The home exists, carries its marker and is owner-only (POSIX). A
    directory without the marker is not adopted, so its remedy is the same
    as `wipe`'s: move it aside."""
    record = record or CLAUDE
    remedy = f"run `{record.login_command}`"
    if not home_dir.is_dir():
        return LoginProblem(f"the harness login home {home_dir} does not exist", remedy,
                            record.name)
    if not (home_dir / MARKER).is_file():
        return not_harness_made(home_dir, record)
    mode = home_dir.stat().st_mode & 0o777
    if os.name == "posix" and mode & 0o077:
        return LoginProblem(f"the harness login home {home_dir} has mode {mode:04o}, wider "
                            "than owner-only (0700)", remedy, record.name)
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
    offenders = (record.offenders(home_dir) if record.offenders
                 else home_offenders(record, home_dir))
    if not offenders:
        return None
    return LoginProblem(f"the harness login home {home_dir} is not clean: it holds "
                        f"{', '.join(offenders)}",
                        f"remove {'it' if len(offenders) == 1 else 'them'}, or run "
                        f"`{record.reset_command}`", record.name)


def _first_difference(actual: object, pinned: object, path: str = "") -> str | None:
    """The first key path at which a parsed configuration departs from the
    pinned one: a changed value (compared with its type, so `0` never passes
    for `false`), a missing key or an extra key."""
    if isinstance(actual, dict) and isinstance(pinned, dict):
        for key in sorted(set(actual) | set(pinned)):
            where = f"{path}.{key}" if path else key
            if key not in pinned:
                return f"extra key {where}"
            if key not in actual:
                return f"missing key {where}"
            found = _first_difference(actual[key], pinned[key], where)
            if found:
                return found
        return None
    if type(actual) is not type(pinned) or actual != pinned:
        return f"{path} differs from the pinned value"
    return None


def config_difference(home_dir: Path) -> str | None:
    """Why the Codex home's `config.toml` is not exactly the pinned one, by
    key path, or None when it is."""
    try:
        actual = tomllib.loads((home_dir / CODEX_CONFIG).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "missing"
    except (OSError, ValueError):
        return "unreadable"
    return _first_difference(actual, PINNED_CONFIG)


def codex_offenders(home_dir: Path) -> list[str]:
    """What makes the Codex home unclean, by path inside it: a configuration
    that departs from the pinned one, or a forbidden entry. Host state —
    plugin caches, `log/`, `*.sqlite`, `installation_id`, the models cache,
    `shell_snapshots/`, `skills/.system`, the run lock and the quota
    snapshot — is allowed."""
    found = []
    difference = config_difference(home_dir)
    if difference:
        found.append(f"{CODEX_CONFIG} ({difference})")
    for pattern in CODEX.forbidden:
        found += sorted(rel for rel in (path.relative_to(home_dir).as_posix()
                                        for path in home_dir.glob(pattern))
                        if rel not in CODEX.allowed)
    return found


def check_codex_home(home_dir: Path) -> LoginProblem | None:
    """The Codex home's configuration equals the pinned one key by key — the
    backstop should `--strict-config` miss a nested key — and it holds nothing
    forbidden."""
    return check_home(CODEX, home_dir)


def _json_object(path: Path) -> dict | str:
    """A JSON object read from `path`, or why it is none: `missing`,
    `unreadable` or `not an object`."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return "missing"
    except (OSError, ValueError):
        return "unreadable"
    return data if isinstance(data, dict) else "not an object"


def _settings_offender(home_dir: Path, account: Path) -> list[str]:
    actual = _json_object(home_dir / COPILOT_SETTINGS)
    difference = (actual if isinstance(actual, str)
                  else _first_difference(actual, pinned_settings(home_dir, account)))
    return [f"{COPILOT_SETTINGS} ({difference})"] if difference else []


def _state_offenders(home_dir: Path) -> list[str]:
    state = _json_object(home_dir / COPILOT_CONFIG)
    if state == "missing":
        return []
    if isinstance(state, str):
        return [f"{COPILOT_CONFIG} ({state})"]
    return [f"{COPILOT_CONFIG} (key {key} outside the managed-state set)"
            for key in sorted(set(state) - MANAGED_STATE_KEYS)]


def _entry_offenders(home_dir: Path) -> list[str]:
    found = []
    for entry in sorted(home_dir.iterdir()):
        name = entry.name
        if name in COPILOT_EMPTY_DIRS:
            if entry.is_dir() and not entry.is_symlink() and not any(entry.iterdir()):
                continue
            found.append(f"{name}/ (not an empty directory)")
        elif name not in COPILOT_ALLOWED and not name.startswith("session-store.db"):
            found.append(name)
    return found


def copilot_offenders(home_dir: Path, account: Path | None = None) -> list[str]:
    """What makes the Copilot home unclean, by key path or entry (Decision 6):
    settings that differ from `pinned_settings` in any key, a key of the
    client's state file outside MANAGED_STATE_KEYS — `config.json` overrides
    `settings.json` key by key, so this is an allow-list — and any entry
    outside the allow-list: a custom-instructions file, `skills/`,
    `mcp-config.json`, `pkg/`, a token file, a non-empty `session-state/` or
    `gh/`."""
    if not home_dir.is_dir():
        return []
    account = account_home() if account is None else account
    return (_settings_offender(home_dir, account) + _state_offenders(home_dir)
            + _entry_offenders(home_dir))


def check_copilot_home(home_dir: Path, account: Path | None = None) -> LoginProblem | None:
    """The Copilot home is clean (`copilot_offenders`); refused naming the first
    offending key path or entry, with the reset remedy."""
    offenders = copilot_offenders(home_dir, account)
    if not offenders:
        return None
    return LoginProblem(f"the harness login home {home_dir} is not clean: it holds "
                        f"{', '.join(offenders)}",
                        f"remove {'it' if len(offenders) == 1 else 'them'}, or run "
                        f"`{COPILOT.reset_command}`", COPILOT.name)


def token_problem(value: str) -> LoginProblem | None:
    """Whether a token is a fine-grained personal access token, judged by its
    prefix alone (the first 11 characters): a classic `ghp_` token is refused
    by name — the client rejects it in prompt mode — and so is any other
    prefix. The message never echoes any part of the value."""
    head = value[:len(TOKEN_PREFIX)]
    if head == TOKEN_PREFIX:
        return None
    kind = ("a classic personal access token" if head.startswith(CLASSIC_PREFIX)
            else "not a fine-grained personal access token")
    return LoginProblem(f"the token entered is {kind}; the harness takes only a fine-grained "
                        f"token (it begins with {TOKEN_PREFIX})", COPILOT_TOKEN_REMEDY,
                        COPILOT.name)


def codex_status(stderr: str) -> str:
    """The login method `codex login status` reports (on stderr): `chatgpt`,
    `api-key`, `access-token`, `other` or `none`. Only the method is kept, so
    the masked key fragment of an API-key line is dropped at the parse."""
    if "Logged in using ChatGPT" in stderr:
        return "chatgpt"
    if "Logged in using an API key" in stderr:
        return "api-key"
    if "access token" in stderr and "Logged in" in stderr:
        return "access-token"
    if "Logged in" in stderr:
        return "other"
    return "none"


def check_codex_login(method: str, home_dir: Path) -> LoginProblem | None:
    """The home holds the ChatGPT login. The pinned configuration requires it,
    so an API-key login reads as no login, and its remedy is a new login."""
    if method == "chatgpt":
        return None
    held = "no login" if method == "none" else f"a {method} login, not the ChatGPT login"
    return LoginProblem(f"the harness login home {home_dir} holds no ChatGPT login ({held})",
                        f"run `{CODEX.login_command}`", CODEX.name)


_CODEX_VERSION = re.compile(r"codex-cli\s+(\d+)\.(\d+)\.(\d+)")


def codex_version(stdout: str) -> tuple[int, int, int] | None:
    """The version `codex --version` prints (`codex-cli X.Y.Z`), or None."""
    match = _CODEX_VERSION.search(stdout)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def version_text(version: tuple[int, int, int] | None) -> str:
    return ".".join(map(str, version)) if version else "unknown"


def check_codex_version(version: tuple[int, int, int] | None) -> LoginProblem | None:
    """The installed CLI is at least CODEX_MIN_VERSION."""
    minimum = version_text(CODEX_MIN_VERSION)
    if version is None:
        return LoginProblem("the Codex CLI reported no version (is `codex` installed and on "
                            "PATH?)", f"install the Codex CLI {minimum} or later", CODEX.name,
                            "precondition")
    if version < CODEX_MIN_VERSION:
        return LoginProblem(f"the installed Codex CLI is {version_text(version)}, older than "
                            f"the pinned minimum {minimum}", CODEX_UPDATE.format(minimum),
                            CODEX.name, "precondition")
    return None


def auth_age(home_dir: Path, now: float | None = None) -> str:
    """How long ago the Codex login was last written, by login or refresh:
    the modification time of `auth.json`, which Codex rewrites on both
    (`storage.rs:206-223` @0.160). The file is never opened."""
    try:
        written = (home_dir / CODEX_AUTH).stat().st_mtime
    except OSError:
        return "never"
    return f"{_span(max(0.0, (time.time() if now is None else now) - written))} ago"


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


def login_note(remedy: str, client: str = "claude") -> str:
    """The closing sentence of a refusal: the operator's own login of that
    client is not affected — unless the remedy runs that client's harness
    login command (with or without `--reset`) while its revocation check is
    unverified (L3 for Claude, X8 for Codex), because that command logs out
    first, and a Codex login revokes the refresh token the home held."""
    affected, caveat, flag = NOTES[client]
    if not globals()[flag] and f"host-login {client}" in remedy:
        return caveat
    return affected


def refusal(problem: LoginProblem) -> str:
    """The one template: untested, the cause, the one remedy, the login note."""
    remedy = problem.remedy[:1].upper() + problem.remedy[1:]
    return (f"untested: {problem.cause.rstrip('.')}. {remedy.rstrip('.')}. "
            f"{login_note(problem.remedy, problem.client)}.")


def run_client(argv: Sequence[str], env: Mapping[str, str], *, interactive: bool,
               cwd: Path, stop_signal: int = signal.SIGTERM) -> tuple[int, str]:
    """Start the client binary: interactively on the operator's terminal (the
    login), or quietly with its stdout captured and bounded by
    CLIENT_TIMEOUT_S, at which it gets the client's own stop request
    (`stop_signal`: the record's — an interrupt for Codex). The runner seam
    the L0 tests fake. It starts the login, the logouts and Claude's status
    check, in the environment its caller built (`login_env`, which drops the
    client's billing families by construction); the Codex children the
    billing guard covers start through `codex_cli.start` instead."""
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
        stop_child(proc, stop_signal)
        proc.communicate()  # drains and closes the pipe
        return 124, ""
    return proc.returncode, out or ""


def read_status(record: HostLogin, home_dir: Path) -> dict:
    """The host's status for the home, reduced to STATUS_FIELDS; {} when it
    yields no login state. Runs in the allowlisted environment, without an
    exported long-lived token, so it reports the home's own login."""
    env = allowlisted_env(record, home_dir)
    env.pop(LONG_LIVED_TOKEN, None)
    _, out = run_client([record.binary, *record.status_argv], env, interactive=False,
                        cwd=home_dir, stop_signal=record.stop_signal)
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


def relogin(source: LoginSource, record: HostLogin | None = None) -> str:
    """The one remedy for a login that no longer serves, as a clause; the
    harness login's closes with that client's login note."""
    record = record or CLAUDE
    if source is LoginSource.HARNESS:
        remedy = f"run `{record.login_command}`"
        return f"{remedy}, then rerun. {login_note(remedy, record.name)}"
    if source is LoginSource.TOKEN:
        return ("run `claude setup-token` and export the new token as "
                f"{LONG_LIVED_TOKEN}, then rerun")
    return f"{RELOGIN}, then rerun"


def login_remedy(message: str, source: LoginSource, record: HostLogin | None = None) -> str:
    """`message`, plus the one remedy for the login the run used when the
    reason is that login — which no rerun repairs. Shared by the dev runner
    (on each host: `record` picks the client's wording and remedy), the judge
    and the routing rig."""
    record = record or CLAUDE
    if not record.failure.search(message):
        return message
    return (f"{message}\nThe {source.value} login is no longer valid: "
            f"{relogin(source, record)}.")


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


def logout_note(client: str = "claude") -> None:
    """Printed before every logout of that client until its revocation check
    (L3 for Claude, X8 for Codex) has passed."""
    _, caveat, flag = NOTES[client]
    if not globals()[flag]:
        print(f"host-login: {caveat[:1].lower()}{caveat[1:]}.", flush=True)


@contextmanager
def client_lock(record: HostLogin, home_dir: Path) -> Iterator[None]:
    """What a logout, a reset or a login over a login holds: the lock the
    client's runs take — Claude's refresh claim, the Codex run lock."""
    with run_lock(home_dir) if record.run_locked else held_claim(home_dir):
        yield


def _logout(record: HostLogin, home_dir: Path, environ: Mapping[str, str]) -> int:
    code, _ = run_client([record.binary, *record.logout_argv],
                         login_env(record, home_dir, environ), interactive=False, cwd=home_dir,
                         stop_signal=record.stop_signal)
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
    """Under the client's lock: log out of the home's login, if it holds one,
    and with `reset` wipe and reseed the home. A logout that fails stops here:
    wiping or logging in over a login whose logout did not go through could
    orphan a live grant. Claude takes its refresh claim here; a Codex login
    already holds the run lock for its whole sequence (`cmd_login`)."""
    if logged_in:
        logout_note(record.name)
    with nullcontext() if record.run_locked else held_claim(home_dir):
        code = _logout(record, home_dir, environ) if logged_in else 0
        if code != 0:
            again = record.reset_command if reset else record.login_command
            return LoginProblem(f"the client's logout in {home_dir} exited {code}, so the "
                                "login there was neither replaced nor wiped",
                                f"rerun `{again}` once the client can log out", record.name)
        if reset:
            problem = wipe(home_dir, record)
            if problem:
                return problem
            seed(record, home_dir)
    return None


def _home_or_problem(record: HostLogin, environ: Mapping[str, str]) -> Path | LoginProblem:
    """The record's home, or why no command may touch it: its location, the
    default Anthropic profile directory for a client that reads one (a Codex
    client reads no Anthropic profile), and for a client whose commands take
    the run lock a platform without POSIX file locks — checked before
    anything is created."""
    root = state_root(environ)
    profile = profile_problem(environ) if record.profile else None
    locks = no_file_locks(record) if record.run_locked and fcntl is None else None
    return (check_location(root, environ, record=record, tempdir=system_tempdir())
            or profile or locks or root / "hosts" / record.name)


def _holds_login(record: HostLogin, home_dir: Path) -> bool:
    """An existing home's login: its credentials file (Linux; for Codex, whose
    pinned configuration keeps it in a file, only that — never opened), or,
    for a client whose status decides (`login_in_status`), its own status,
    where the login is no file (Claude in the macOS Keychain)."""
    if (home_dir / record.credentials).exists():
        return True
    return record.login_in_status and bool(read_status(record, home_dir).get("loggedIn"))


def _login_argv(record: HostLogin, args: argparse.Namespace) -> list[str]:
    device = ["--device-auth"] if getattr(args, "device_auth", False) else []
    return [record.binary, *record.login_argv, *device]


def cmd_login(record: HostLogin, args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    """Seed a missing home; refuse an existing one the harness did not make,
    with or without `--reset`; log out first over an existing login. A Codex
    login holds the run lock from the logout to the end of the login, and
    takes it again on the reseeded home after a reset. A token-file record
    (Copilot) takes `cmd_login_token` instead: no client login runs."""
    if record.credential == "token-file":
        return cmd_login_token(record, args, environ)
    bump = _speed_bumps(environ)
    if bump:
        print(bump, file=sys.stderr)
        return EXIT_USAGE
    home_dir = _home_or_problem(record, environ)
    if isinstance(home_dir, LoginProblem):
        print(refusal(home_dir), file=sys.stderr)
        return EXIT_NOT_READY
    existed = home_dir.exists() or home_dir.is_symlink()
    foreign = not_harness_made(home_dir, record) if existed else None
    if foreign:
        print(refusal(foreign), file=sys.stderr)
        return EXIT_NOT_READY
    if not existed:
        seed(record, home_dir)
    logged_in = existed and _holds_login(record, home_dir)
    with ExitStack() as hold:
        if record.run_locked:
            hold.enter_context(run_lock(home_dir))
        if logged_in or (existed and args.reset):
            problem = _start_over(record, home_dir, environ, reset=args.reset,
                                  logged_in=logged_in)
            if problem:
                print(refusal(problem), file=sys.stderr)
                return EXIT_NOT_READY
            if record.run_locked and args.reset:  # the wipe took the lock file with it
                hold.enter_context(run_lock(home_dir))
        run_client(_login_argv(record, args), login_env(record, home_dir, environ),
                   interactive=True, cwd=home_dir)
    return cmd_status(record, args, environ)


def cmd_logout(record: HostLogin, _args: argparse.Namespace,
               environ: Mapping[str, str]) -> int:
    """Log the client out of the home. A missing home has nothing to log out;
    an existing path the harness did not make is refused like every command
    refuses it, so a foreign login there is never logged out. A token-file
    record deletes its token file instead (`cmd_logout_token`)."""
    if record.credential == "token-file":
        return cmd_logout_token(record, environ)
    home_dir = _home_or_problem(record, environ)
    if isinstance(home_dir, LoginProblem):
        print(refusal(home_dir), file=sys.stderr)
        return EXIT_NOT_READY
    if not (home_dir.exists() or home_dir.is_symlink()):
        print(f"no harness login home at {home_dir}: nothing to log out")
        return EXIT_READY
    foreign = not_harness_made(home_dir, record)
    if foreign:
        print(refusal(foreign), file=sys.stderr)
        return EXIT_NOT_READY
    with client_lock(record, home_dir):
        logout_note(record.name)
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


def cmd_status_codex(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    """`status codex [--quota]`: the keys of the spec's status list, from the
    home, `codex --version`, `codex login status` and `codex features list`
    (no model call; `auth.json` is never opened), and with `--quota` a fresh
    plan quota read under the run lock. Exit 0 ready, 3 not ready."""
    import codex_cli  # deferred: codex_cli imports this module

    root = state_root(environ)
    home_dir = root / "hosts" / CODEX.name
    problem = check_location(root, environ, record=CODEX, tempdir=system_tempdir())
    lines, found = codex_cli.status(home_dir, environ, live_quota=getattr(args, "quota", False),
                                    run_probes=problem is None)
    for key, value in lines.items():
        print(f"{key}: {value}")
    problem = problem or found
    if problem:
        print(refusal(problem), file=sys.stderr)
        return EXIT_NOT_READY
    return EXIT_READY


def cmd_status(record: HostLogin, args: argparse.Namespace,
               environ: Mapping[str, str]) -> int:
    if record.status_command:
        return record.status_command(args, environ)
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


# ---------- the token-file commands (Copilot; add-copilot-dev-runner Decision 4) -------------

APPROVAL_CAUSE = "first run not yet approved"


def _token_home(record: HostLogin, environ: Mapping[str, str]) -> Path | LoginProblem:
    """The token-file record's home, or why no command may touch it: its
    location, a platform without file locks, or a path the harness did not
    make (never adopted, never deleted)."""
    home_dir = _home_or_problem(record, environ)
    if isinstance(home_dir, LoginProblem):
        return home_dir
    if home_dir.exists() or home_dir.is_symlink():
        return not_harness_made(home_dir, record) or home_dir
    return home_dir


def _read_token() -> str | None:
    """The token from the terminal, without echo; None when nothing came."""
    try:
        value = getpass.getpass(TOKEN_PROMPT)
    except (EOFError, KeyboardInterrupt):
        return None
    return value.strip() or None


def _write_token(home_dir: Path, value: str) -> None:
    """The token file beside the home: created exclusively and owner-only
    (`touch(mode=0o600, exist_ok=False)` is `os.open` with `O_WRONLY | O_CREAT
    | O_EXCL` and mode 0600, so an existing file or link at the path fails the
    login), then written as bytes — never readable by anyone else, not even
    while empty."""
    path = token_path(home_dir)
    path.touch(mode=0o600, exist_ok=False)
    with path.open("wb") as handle:
        handle.write(value.encode("utf-8") + b"\n")


def _take_token(home_dir: Path) -> LoginProblem | None:
    """Prompt, refuse anything but a fine-grained token before writing, write
    the token file and record the approval stop. Under the run lock."""
    import copilot_cli  # deferred: copilot_cli imports this module

    value = _read_token()
    if value is None:
        return LoginProblem("no token was entered", "run the login again and paste the token",
                            COPILOT.name)
    problem = token_problem(value)
    if problem:
        return problem
    _write_token(home_dir, value)
    copilot_cli.record_stop(home_dir, "approval", APPROVAL_CAUSE)
    return None


def _clear_stop(record: HostLogin, home_dir: Path) -> int:
    """`--clear-stop`: under the run lock, remove a recorded stop of any kind
    from the status snapshot, and change nothing else in the home."""
    import copilot_cli  # deferred: copilot_cli imports this module

    absent = check_presence(home_dir, record)
    if absent:
        print(refusal(absent), file=sys.stderr)
        return EXIT_NOT_READY
    with run_lock(home_dir, record=record):
        removed = copilot_cli.clear_stop(home_dir)
    if removed is None:
        print("host-login: no stop is recorded in the Copilot harness home")
    else:
        print(f"host-login: cleared the {removed.get('kind')} stop ({removed.get('cause')}); "
              "the next Copilot run may start")
    return EXIT_READY


def cmd_login_token(record: HostLogin, args: argparse.Namespace,
                    environ: Mapping[str, str]) -> int:
    """The token-file login: the same speed bumps, the location, the seed
    before the prompt, then under the run lock the logout (deleting the token
    file), with `--reset` the wipe and reseed, the hidden prompt, the prefix
    check, the 0600 file and the approval stop; then the status read. No
    client login ever runs. `--clear-stop` removes a recorded stop instead."""
    bump = _speed_bumps(environ)
    if bump:
        print(bump, file=sys.stderr)
        return EXIT_USAGE
    home_dir = _token_home(record, environ)
    if isinstance(home_dir, LoginProblem):
        print(refusal(home_dir), file=sys.stderr)
        return EXIT_NOT_READY
    if getattr(args, "clear_stop", False):
        return _clear_stop(record, home_dir)
    existed = home_dir.exists()
    if not existed:
        seed(record, home_dir)
    with ExitStack() as hold:
        hold.enter_context(run_lock(home_dir, record=record))
        token_path(home_dir).unlink(missing_ok=True)
        if existed and args.reset:
            wipe(home_dir, record)  # a marked home: `_token_home` refused anything else
            seed(record, home_dir)
            hold.enter_context(run_lock(home_dir, record=record))
        problem = _take_token(home_dir)
    if problem:
        print(f"host-login: {problem.cause}. {problem.remedy[:1].upper()}{problem.remedy[1:]}.",
              file=sys.stderr)
        return EXIT_USAGE
    print(f"host-login: wrote {token_path(home_dir)} (owner-only) and recorded the approval "
          f"stop: the first Copilot run waits until you run `{CLEAR_STOP_COMMAND}` in a "
          "terminal outside any agent session.")
    return cmd_status(record, args, environ)


def cmd_logout_token(record: HostLogin, environ: Mapping[str, str]) -> int:
    """The token-file logout: under the run lock, delete the token file and
    nothing else, run no client logout, and name the page where the operator
    revokes the token. No unverified-logout caveat: no client login is
    touched."""
    home_dir = _token_home(record, environ)
    if isinstance(home_dir, LoginProblem):
        print(refusal(home_dir), file=sys.stderr)
        return EXIT_NOT_READY
    path = token_path(home_dir)
    with run_lock(home_dir, record=record) if home_dir.is_dir() else nullcontext():
        existed = path.exists()
        path.unlink(missing_ok=True)
    done = f"deleted the token file {path}" if existed else f"no token file at {path}"
    print(f"host-logout: {done}. Revoke the token at {TOKEN_PAGE}.")
    return EXIT_READY


def cmd_status_copilot(args: argparse.Namespace, environ: Mapping[str, str]) -> int:
    """`status copilot [--models] [--no-token]`: the keys of the spec's status
    list (`copilot_cli.status`), with no model call, under the run lock. A
    recorded stop is reported and does not decide the exit status. Exit 0
    ready, 3 not ready."""
    import copilot_cli  # deferred: copilot_cli imports this module

    root = state_root(environ)
    home_dir = root / "hosts" / COPILOT.name
    problem = check_location(root, environ, record=COPILOT)
    lines, found = copilot_cli.status(home_dir, environ, models=getattr(args, "models", False),
                                      no_token=getattr(args, "no_token", False),
                                      run_probes=problem is None)
    for key, value in lines.items():
        print(f"{key}: {value}")
    problem = problem or found
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
    login.add_argument("--device-auth", action="store_true",
                       help="codex only: the client's device-code login instead of a browser")
    login.add_argument("--clear-stop", action="store_true",
                       help="copilot only: remove a recorded stop (billing, isolation or "
                            "approval); clearing the approval stop approves the next run")
    status = sub.add_parser("status", help="report the harness home; no model call")
    status.add_argument("client", nargs="?", default="claude", choices=sorted(RECORDS))
    status.add_argument("--quota", action="store_true",
                        help="codex only: also read the plan quota now (under the run lock; "
                             "a GET of plan usage, not a model call)")
    status.add_argument("--models", action="store_true",
                        help="copilot only: also list the models (id, policy, efforts)")
    status.add_argument("--no-token", action="store_true",
                        help="copilot only: also repeat the read without the token, to show "
                             "the client finds no other credential")
    logout = sub.add_parser("logout", help="run the client's logout in the harness home")
    logout.add_argument("client", choices=sorted(RECORDS))
    return parser


def main(argv: list[str] | None = None) -> int:
    """Exit 0 ready, 2 usage or refused to start, 3 not ready (untested) —
    a Codex run lock that is held or that this platform cannot take
    included."""
    parser = build_parser()
    args = parser.parse_args(argv)
    for option, given, client in (
            ("--device-auth", getattr(args, "device_auth", False), CODEX.name),
            ("--quota", getattr(args, "quota", False), CODEX.name),
            ("--clear-stop", getattr(args, "clear_stop", False), COPILOT.name),
            ("--models", getattr(args, "models", False), COPILOT.name),
            ("--no-token", getattr(args, "no_token", False), COPILOT.name)):
        if given and args.client != client:
            parser.error(f"{option} applies to the {client} client only")
    if getattr(args, "clear_stop", False) and args.reset:
        parser.error("--clear-stop and --reset are separate commands: pass one")
    try:
        return COMMANDS[args.command](RECORDS[args.client], args, os.environ)
    except RunLockRefused as refused:
        print(refusal(refused.problem), file=sys.stderr)
        return EXIT_NOT_READY


if __name__ == "__main__":
    sys.exit(main())
