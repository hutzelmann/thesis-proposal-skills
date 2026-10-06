"""L0: the harness login commands, `host_login.main(argv)` (testing-harness
spec: Harness-owned host logins).

The client binary is faked at the module's runner seam (`host_login.run_client`),
never started: each fake records the argv and environment it was handed, and
answers `auth status` with a synthetic status that carries a placeholder email
and organization, so a test can show neither reaches the output. The state
root lives in `tmp_path`.
"""

from __future__ import annotations

import json
import os
import signal
import sys
import time
from pathlib import Path

import copilot_cli
import host_login
import pytest
from account_surfaces import CONNECTORS_OFF, PINNED_SETTINGS, PROFILE_DIR
from helpers import COPILOT_STREAMS, COPILOT_TOKEN, copilot_reply
from host_login import (
    AGENT_MARKERS,
    CLAIM_NAME,
    CLAUDE,
    CREDENTIALS,
    LONG_LIVED_TOKEN,
    MARKER,
    STATE_VAR,
    login_env,
    main,
)

PRIVATE = {"email": "erika.musterfrau@example.org", "orgName": "Example Org", "orgId": "org-0000"}
STATUS_KEYS = ["home", "marker", "logged_in", "auth_method", "api_provider",
               "config_dir_matches", "clean", "access_expires", "runs_use"]
L3_NOTE = "whether this logs out your other Claude sessions is unverified (L3)"
# what an operator's shell may carry; none of it may reach a login or logout
STEERING = {
    "ANTHROPIC_API_KEY": "placeholder-not-a-key",
    LONG_LIVED_TOKEN: "placeholder-not-a-token",
    "ANTHROPIC_CONFIG_DIR": "/fake/home/.config/anthropic",
    "CLAUDE_CONFIG_DIR": "/fake/home/.claude-other",
    "ANTHROPIC_BASE_URL": "https://gateway.invalid",
    "ANTHROPIC_AUTH_TOKEN": "placeholder-auth-token",
    "CLAUDE_CODE_USE_BEDROCK": "placeholder-provider-switch",
}


class FakeClient:
    """`host_login.run_client`: records each call and answers `auth status`."""

    def __init__(self, home: Path, *, logged_in: bool = True):
        self.home, self.logged_in = home, logged_in
        self.calls: list[dict] = []
        self.on_logout = None

    def __call__(self, argv, env, *, interactive, cwd, stop_signal=None):
        verb = " ".join(argv[1:3])
        self.calls.append({"verb": verb, "argv": list(argv), "env": dict(env),
                           "interactive": interactive, "cwd": cwd, "stop_signal": stop_signal})
        if verb == "auth logout" and self.on_logout:
            self.on_logout()
        if verb == "auth status":
            return 0, json.dumps({"loggedIn": self.logged_in, "authMethod": "claude.ai",
                                  "apiProvider": "firstParty",
                                  "configDirectory": str(self.home), **PRIVATE})
        return 0, ""

    def verbs(self) -> list[str]:
        return [call["verb"] for call in self.calls]


@pytest.fixture
def state(tmp_path, monkeypatch):
    """A state root of the test's own; no agent marker; a terminal on stdin;
    an empty default Anthropic profile directory, never the operator's."""
    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path / "xdg"))
    for name in (*AGENT_MARKERS, LONG_LIVED_TOKEN, "CLAUDE_REAL_CONFIG_DIR"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: True)
    return host_login.home(CLAUDE)


@pytest.fixture
def client(state, monkeypatch):
    fake = FakeClient(state)
    monkeypatch.setattr(host_login, "run_client", fake)
    return fake


def no_client(monkeypatch):
    def refuse(*_args, **_kwargs):
        pytest.fail("the client binary was started")

    monkeypatch.setattr(host_login, "run_client", refuse)


def logged_in(home: Path) -> None:
    """A login the host would have written: a placeholder, never a credential."""
    home.mkdir(parents=True, exist_ok=True)
    (home / CREDENTIALS).write_text(json.dumps({"claudeAiOauth": {
        "accessToken": "placeholder", "refreshToken": "placeholder",
        "expiresAt": int(time.time() * 1000) + 5 * 3_600_000 + 60_000}}), encoding="utf-8")


# ---------- the two speed bumps ---------------------------------------------------


def test_login_refuses_without_a_terminal(state, monkeypatch, capsys):
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: False)
    no_client(monkeypatch)
    assert main(["login", "claude"]) != 0
    assert "terminal" in capsys.readouterr().err
    assert not state.exists()
    assert not state.parent.exists()


@pytest.mark.parametrize("marker", AGENT_MARKERS)
def test_login_refuses_inside_an_agent_session(marker, state, monkeypatch, capsys):
    """testing-harness spec: Login refused inside an agent session."""
    value = f"synthetic-marker-value-{len(marker)}"
    monkeypatch.setenv(marker, value)
    no_client(monkeypatch)
    assert main(["login", "claude"]) != 0
    out, err = capsys.readouterr()
    assert marker in err
    assert value not in out + err
    assert not state.exists()


def test_the_agent_markers_are_the_known_session_variables():
    assert set(AGENT_MARKERS) == {"CLAUDECODE", "CLAUDE_CODE_ENTRYPOINT",
                                  "CLAUDE_CODE_SESSION_ID", "CODEX_SANDBOX",
                                  "CODEX_SANDBOX_NETWORK_DISABLED"}


@pytest.mark.usefixtures("state")
def test_login_proceeds_without_a_marker(client):
    assert main(["login", "claude"]) == 0
    assert client.verbs() == ["auth login", "auth status"]
    [login] = [call for call in client.calls if call["verb"] == "auth login"]
    assert login["interactive"]


# ---------- the login environment and argv ------------------------------------


# what a desktop-app session exports to bind a child to itself
SESSION_BINDING = {"CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "claude-desktop",
                   "CLAUDE_CODE_SESSION_ID": "synthetic-session",
                   "CLAUDE_CODE_MESSAGING_TOKEN": "placeholder-messaging-token",
                   "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH": "1", "CLAUDE_PID": "1"}


def test_login_env_strips_steering_and_keeps_the_browser(tmp_path):
    home = tmp_path / "home"
    environ = {**STEERING, **SESSION_BINDING,
               "DISPLAY": ":0", "WAYLAND_DISPLAY": "wayland-0", "PATH": "/usr/bin"}
    env = login_env(CLAUDE, home, environ)
    assert env["DISPLAY"] == ":0"
    assert env["WAYLAND_DISPLAY"] == "wayland-0"
    assert env["CLAUDE_CONFIG_DIR"] == str(home)
    assert env["ANTHROPIC_CONFIG_DIR"] == str(home / PROFILE_DIR)
    for name, value in CONNECTORS_OFF.items():
        assert env[name] == value
    for name in ("ANTHROPIC_API_KEY", "ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN",
                 LONG_LIVED_TOKEN, "CLAUDE_CODE_USE_BEDROCK", *SESSION_BINDING):
        assert name not in env, name
    assert set(STEERING.values()).isdisjoint(env.values())


def test_the_login_is_the_subscription_login():
    assert "--claudeai" in CLAUDE.login_argv
    assert "--console" not in CLAUDE.login_argv


def test_the_login_runs_in_the_login_environment(state, client, monkeypatch):
    """testing-harness spec: Login never bills per token — the call itself,
    not only the builder: no steering value reaches it, and its argv is the
    subscription login."""
    for name, value in {**STEERING, **SESSION_BINDING}.items():
        monkeypatch.setenv(name, value)
    monkeypatch.setattr(host_login, "_speed_bumps", lambda _environ: None)
    assert main(["login", "claude"]) == 0
    [login] = [call for call in client.calls if call["verb"] == "auth login"]
    assert login["env"] == login_env(CLAUDE, state, os.environ)
    assert login["argv"] == ["claude", *CLAUDE.login_argv]
    assert login["env"]["CLAUDE_CONFIG_DIR"] == str(state)
    assert set(STEERING.values()).isdisjoint(login["env"].values())


def test_seeding_happens_before_the_login_starts(state, client, monkeypatch):
    """testing-harness spec: Opt-outs seeded before the login."""
    seen = {}

    def recording(argv, env, **seam):
        if " ".join(argv[1:3]) == "auth login":
            settings = json.loads((state / "settings.json").read_text(encoding="utf-8"))
            seen.update(settings=settings, profile=(state / PROFILE_DIR).is_dir(),
                        marker=(state / MARKER).is_file())
        return client(argv, env, **seam)

    monkeypatch.setattr(host_login, "run_client", recording)
    main(["login", "claude"])
    assert seen == {"settings": dict(PINNED_SETTINGS), "profile": True, "marker": True}


# ---------- logout before login, reset, and the claim ---------------------------


def test_an_existing_login_is_logged_out_first_under_the_claim(state, client):
    host_login.seed(CLAUDE, state)
    logged_in(state)
    held = []
    client.on_logout = lambda: held.append((state / CLAIM_NAME).exists())
    assert main(["login", "claude"]) == 0
    verbs = client.verbs()
    assert verbs.index("auth logout") < verbs.index("auth login")
    assert held == [True]
    assert not (state / CLAIM_NAME).exists()


def test_reset_wipes_the_marked_home_and_seeds_it_again(state, client):
    host_login.seed(CLAUDE, state)
    logged_in(state)
    stray = state / "skills" / "synced" / "x"
    stray.parent.mkdir(parents=True)
    stray.write_text("synthetic\n", encoding="utf-8")
    assert main(["login", "claude", "--reset"]) == 0
    assert not stray.exists()
    assert not (state / CREDENTIALS).exists()
    assert (state / MARKER).is_file()
    settings = json.loads((state / "settings.json").read_text(encoding="utf-8"))
    assert settings == dict(PINNED_SETTINGS)
    assert client.verbs().count("auth logout") == 1


def test_reset_refuses_an_unmarked_home(state, client, capsys):
    state.mkdir(parents=True)
    (state / "keep-me").write_text("synthetic\n", encoding="utf-8")
    assert main(["login", "claude", "--reset"]) == 3
    assert (state / "keep-me").is_file()
    assert "auth logout" not in client.verbs()
    assert str(state) in capsys.readouterr().err


@pytest.mark.parametrize("held", [False, True], ids=["foreign-files", "foreign-login"])
def test_a_plain_login_never_adopts_an_unmarked_directory(held, state, monkeypatch, capsys):
    """Only a home the harness created is logged into: a directory at the
    home's path without the marker is refused, not marked, reseeded or logged
    out — or a later reset would delete content the harness never made."""
    state.mkdir(parents=True)
    (state / "keep-me").write_text("synthetic\n", encoding="utf-8")
    (state / "settings.json").write_text('{"model": "opus"}', encoding="utf-8")
    if held:
        logged_in(state)
    no_client(monkeypatch)
    assert main(["login", "claude"]) == 3
    err = capsys.readouterr().err
    assert str(state) in err
    assert "Move it aside" in err
    assert not (state / MARKER).exists()
    assert (state / "keep-me").is_file()
    assert json.loads((state / "settings.json").read_text(encoding="utf-8")) == {"model": "opus"}


def test_a_login_refuses_a_symlinked_home(state, tmp_path, monkeypatch, capsys):
    target = tmp_path / "elsewhere"
    host_login.seed(CLAUDE, target)
    state.parent.mkdir(parents=True)
    state.symlink_to(target)
    no_client(monkeypatch)
    assert main(["login", "claude"]) == 3
    assert "symbolic link" in capsys.readouterr().err


@pytest.mark.parametrize("reset", [False, True], ids=["re-login", "reset"])
def test_a_failed_logout_replaces_and_wipes_nothing(reset, state, client, monkeypatch, capsys):
    """A logout that did not go through leaves its login in place: logging in
    over it, or wiping it, could orphan a live grant."""
    host_login.seed(CLAUDE, state)
    logged_in(state)
    stray = state / "projects" / "p.jsonl"
    stray.parent.mkdir()
    stray.write_text("{}\n", encoding="utf-8")

    def failing(argv, env, **seam):
        client(argv, env, **seam)
        return (1, "") if " ".join(argv[1:3]) == "auth logout" else (0, "")

    monkeypatch.setattr(host_login, "run_client", failing)
    assert main(["login", "claude", *(["--reset"] if reset else [])]) == 3
    assert "auth login" not in client.verbs()
    assert (state / CREDENTIALS).is_file()
    assert stray.is_file()
    err = capsys.readouterr().err
    assert "exited 1" in err
    assert ("--reset" in err) is reset


def test_a_login_held_outside_a_file_is_logged_out_first(state, client):
    """Where the login is no file (the macOS Keychain), the host's own status
    says whether the home holds one."""
    host_login.seed(CLAUDE, state)
    assert main(["login", "claude"]) == 0
    verbs = client.verbs()
    assert verbs[:2] == ["auth status", "auth logout"]
    assert verbs.index("auth logout") < verbs.index("auth login")


def test_a_reset_of_a_home_without_a_login_logs_nothing_out(state, monkeypatch, capsys):
    fake = FakeClient(state, logged_in=False)
    monkeypatch.setattr(host_login, "run_client", fake)
    host_login.seed(CLAUDE, state)
    (state / "CLAUDE.md").write_text("synthetic\n", encoding="utf-8")
    main(["login", "claude", "--reset"])
    assert "auth logout" not in fake.verbs()
    assert "auth login" in fake.verbs()
    assert not (state / "CLAUDE.md").exists()
    assert L3_NOTE not in capsys.readouterr().out


def test_a_reset_that_cannot_wipe_stops_before_the_login(state, client, monkeypatch, capsys):
    host_login.seed(CLAUDE, state)
    logged_in(state)
    problem = host_login.LoginProblem(f"{state} vanished", "run it again")
    monkeypatch.setattr(host_login, "wipe", lambda _home, _record: problem)
    assert main(["login", "claude", "--reset"]) == 3
    assert "auth login" not in client.verbs()
    assert f"{state} vanished" in capsys.readouterr().err


@pytest.mark.usefixtures("state")
def test_a_login_refuses_an_overlapping_state_root(monkeypatch, capsys):
    monkeypatch.setenv(STATE_VAR, str(Path.home()))
    no_client(monkeypatch)
    assert main(["login", "claude"]) == 3
    assert STATE_VAR in capsys.readouterr().err


@pytest.mark.parametrize("argv", [["login", "claude"], ["logout", "claude"], ["status"]])
def test_a_profile_in_the_default_directory_refuses_every_command(argv, state, tmp_path,
                                                                 monkeypatch, capsys):
    """Fallback F8 for the harness login's own host processes: whether the
    host ignores the default profile directory when the profile variable
    names the home's empty one is unverified (L8), so no login, logout or
    status check starts beside a profile there — token or not."""
    host_login.seed(CLAUDE, state)
    logged_in(state)
    (tmp_path / "xdg" / "anthropic" / "work-profile-name").mkdir(parents=True)
    monkeypatch.setenv(LONG_LIVED_TOKEN, "placeholder-not-a-token")
    no_client(monkeypatch)
    assert main(argv) == 3
    err = capsys.readouterr().err
    assert str(tmp_path / "xdg" / "anthropic") in err
    assert "work-profile-name" not in err
    assert "Move the profiles aside" in err


@pytest.mark.parametrize("path", ["logout", "login-over-a-login", "reset"])
def test_every_logout_runs_in_the_login_environment(path, state, client, monkeypatch):
    """testing-harness spec: Logout stays in the home."""
    host_login.seed(CLAUDE, state)
    logged_in(state)
    for name, value in STEERING.items():
        monkeypatch.setenv(name, value)
    argv = {"logout": ["logout", "claude"], "login-over-a-login": ["login", "claude"],
            "reset": ["login", "claude", "--reset"]}[path]
    main(argv)
    [logout] = [call for call in client.calls if call["verb"] == "auth logout"]
    assert logout["env"] == login_env(CLAUDE, state, os.environ)
    assert set(STEERING.values()).isdisjoint(logout["env"].values())
    assert logout["env"]["CLAUDE_CONFIG_DIR"] == str(state)


@pytest.mark.parametrize("passed", [False, True], ids=["L3-open", "L3-passed"])
@pytest.mark.parametrize("path", ["logout", "login-over-a-login", "reset"])
def test_the_logout_note_comes_first_until_l3(path, passed, state, client, monkeypatch,
                                              capsys):
    """testing-harness spec: Logout caveat until L3."""
    monkeypatch.setattr(host_login, "L3_PASSED", passed)
    host_login.seed(CLAUDE, state)
    logged_in(state)
    printed = []
    client.on_logout = lambda: printed.append(capsys.readouterr().out)
    argv = {"logout": ["logout", "claude"], "login-over-a-login": ["login", "claude"],
            "reset": ["login", "claude", "--reset"]}[path]
    main(argv)
    assert len(printed) == 1
    assert (L3_NOTE in printed[0]) is not passed
    assert "auth logout" in client.verbs()


def test_logout_keeps_the_marker_and_settings(state, client):
    host_login.seed(CLAUDE, state)
    logged_in(state)
    assert main(["logout", "claude"]) == 0
    assert (state / MARKER).is_file()
    assert (state / "settings.json").is_file()
    assert client.verbs() == ["auth logout"]


def test_logout_without_a_home_has_nothing_to_log_out(state, monkeypatch, capsys):
    no_client(monkeypatch)
    assert main(["logout", "claude"]) == 0
    assert "nothing to log out" in capsys.readouterr().out
    assert not state.exists()


@pytest.mark.parametrize("held", [False, True], ids=["foreign-files", "foreign-login"])
def test_logout_refuses_an_unmarked_directory(held, state, monkeypatch, capsys):
    """A directory at the home's path without the marker is refused with the
    move-aside remedy, as every command refuses it: nothing in it is logged
    out, and the refusal is no "nothing to log out"."""
    state.mkdir(parents=True)
    (state / "keep-me").write_text("synthetic\n", encoding="utf-8")
    if held:
        logged_in(state)
    no_client(monkeypatch)
    assert main(["logout", "claude"]) == 3
    captured = capsys.readouterr()
    assert str(state) in captured.err
    assert "Move it aside" in captured.err
    assert "nothing to log out" not in captured.out
    assert not (state / MARKER).exists()
    assert (state / "keep-me").is_file()
    assert (state / CREDENTIALS).is_file() is held


@pytest.mark.usefixtures("state")
def test_logout_refuses_an_overlapping_state_root(monkeypatch, capsys):
    monkeypatch.setenv(STATE_VAR, str(Path.home()))
    no_client(monkeypatch)
    assert main(["logout", "claude"]) == 3
    assert STATE_VAR in capsys.readouterr().err


def test_a_failed_standalone_logout_is_not_ready(state, monkeypatch, capsys):
    host_login.seed(CLAUDE, state)
    logged_in(state)
    monkeypatch.setattr(host_login, "run_client", lambda *_a, **_k: (124, ""))
    assert main(["logout", "claude"]) == 3
    assert "exited 124" in capsys.readouterr().out


# ---------- status -------------------------------------------------------------


def status_lines(out: str) -> dict[str, str]:
    lines = [line for line in out.splitlines() if line]
    pairs = dict(line.split(": ", 1) for line in lines)
    assert list(pairs) == STATUS_KEYS
    return pairs


def test_status_of_a_ready_home(state, client, capsys):
    """testing-harness spec: Status reveals no account details."""
    host_login.seed(CLAUDE, state)
    logged_in(state)
    assert main(["status"]) == 0
    out, err = capsys.readouterr()
    pairs = status_lines(out)
    assert pairs["home"] == str(state)
    assert (pairs["marker"], pairs["logged_in"], pairs["auth_method"]) == (
        "yes", "yes", "claude.ai")
    assert (pairs["api_provider"], pairs["config_dir_matches"], pairs["clean"]) == (
        "firstParty", "yes", "yes")
    assert pairs["access_expires"] == "in 5h"
    assert pairs["runs_use"] == "harness"
    for value in PRIVATE.values():
        assert value not in out + err
    assert client.verbs() == ["auth status"]


@pytest.mark.usefixtures("client")
def test_status_names_what_is_unclean_and_exits_not_ready(state, capsys):
    host_login.seed(CLAUDE, state)
    logged_in(state)
    (state / "CLAUDE.md").write_text("synthetic\n", encoding="utf-8")
    assert main(["status", "claude"]) == 3
    out, err = capsys.readouterr()
    assert status_lines(out)["clean"] == "CLAUDE.md"
    assert err.startswith("untested: ")


def test_status_of_a_missing_home_creates_nothing_and_starts_nothing(state, monkeypatch,
                                                                     capsys):
    no_client(monkeypatch)
    assert main(["status"]) == 3
    out, err = capsys.readouterr()
    pairs = status_lines(out)
    assert (pairs["marker"], pairs["logged_in"]) == ("no", "no")
    assert "uv run poe host-login claude" in err
    assert not state.exists()


@pytest.mark.usefixtures("client")
def test_status_reports_token_mode(state, monkeypatch, capsys):
    monkeypatch.setenv(LONG_LIVED_TOKEN, "placeholder-not-a-token")
    host_login.seed(CLAUDE, state)
    main(["status"])
    assert status_lines(capsys.readouterr().out)["runs_use"].startswith("token")


def test_status_refuses_an_overlapping_state_root(monkeypatch, capsys):
    """testing-harness spec: Override overlapping the operator's configuration."""
    monkeypatch.setenv(STATE_VAR, str(Path.home()))
    no_client(monkeypatch)
    assert main(["status"]) == 3
    assert STATE_VAR in capsys.readouterr().err


def test_an_unknown_client_is_a_usage_error(state, capsys):
    with pytest.raises(SystemExit) as usage:
        main(["login", "gemini"])
    assert usage.value.code == 2
    assert not state.exists()
    assert "gemini" in capsys.readouterr().err


# ---------- Codex: login, logout, status (add-codex-dev-runner) ----------------------
#
# The Codex binary is never started: `host_login.run_client` stands in for the
# login and the logouts, `codex_cli.probe` for `--version`, `login status` and
# `features list`, and `codex_cli.read_quota` for the app-server's quota read.
# The state root lives in `tmp_path`, which lies inside the system temporary
# directory, so `host_login.system_tempdir` names a directory of its own.

CODEX_STREAMS = Path(__file__).resolve().parent / "data" / "codex_streams"
CODEX_STATUS_KEYS = ["home", "marker", "logged_in", "auth_method", "config_pinned", "clean",
                     "last_written", "cli_version", "min_version", "features_ok", "last_quota",
                     "stop", "runs_use"]
X8_NOTE = "whether this logs out your other ChatGPT sessions is unverified (X8)"
POSIX_LOCKS = pytest.mark.skipif(host_login.fcntl is None,
                                 reason="the run lock is a POSIX file lock")
MASKED_KEY = "sk-proj-***SYNTH"
CODEX_STEERING = {
    "CODEX_API_KEY": "placeholder-codex-key",
    "CODEX_ACCESS_TOKEN": "placeholder-codex-token",
    "CODEX_FOO": "placeholder-unknown",
    "OPENAI_API_KEY": "placeholder-openai-key",
    "OPENAI_BASE_URL": "https://gateway.invalid/v1",
    "OPENROUTER_API_KEY": "placeholder-openrouter-key",
    "SOME_SERVICE_API_KEY": "placeholder-other-key",
}


class FakeCodexClient:
    """`host_login.run_client` for Codex: records the login and the logouts."""

    def __init__(self):
        self.calls: list[dict] = []
        self.on_login = None
        self.on_logout = None
        self.home: Path | None = None

    def __call__(self, argv, env, *, interactive, cwd, stop_signal=None):
        verb = argv[1]
        self.calls.append({"verb": verb, "argv": list(argv), "env": dict(env),
                           "interactive": interactive, "cwd": cwd, "stop_signal": stop_signal})
        hook = {"login": self.on_login, "logout": self.on_logout}.get(verb)
        if hook:
            hook()
        return 0, ""

    def verbs(self) -> list[str]:
        return [call["verb"] for call in self.calls]


class FakeProbe:
    """`codex_cli.probe`: answers like a logged-in 0.160 CLI unless told otherwise."""

    def __init__(self, version="codex-cli 0.160.0\n", login="Logged in using ChatGPT\n",
                 features=None):
        self.version, self.login = version, login
        self.features = features if features is not None else (
            CODEX_STREAMS / "features-ok.txt").read_text(encoding="utf-8")
        self.calls: list[list[str]] = []

    def __call__(self, args, _home, _environ=None):
        self.calls.append(list(args))
        if list(args) == ["--version"]:
            return 0, self.version, ""
        if list(args) == ["login", "status"]:
            return 0, "", self.login
        if list(args[:2]) == ["features", "list"]:
            return 0, self.features, ""
        raise AssertionError(f"unexpected probe {args}")


@pytest.fixture
def codex_state(tmp_path, monkeypatch):
    import codex_cli

    monkeypatch.setenv(STATE_VAR, str(tmp_path / "state"))
    monkeypatch.setattr(host_login, "system_tempdir", lambda: str(tmp_path / "system-tmp"))
    for name in (*AGENT_MARKERS, LONG_LIVED_TOKEN, "CODEX_HOME"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: True)
    monkeypatch.setattr(host_login, "LOCK_WAIT_S", 0.2)
    probe = FakeProbe()
    monkeypatch.setattr(codex_cli, "probe", probe)
    return host_login.home(host_login.CODEX)


@pytest.fixture
def codex_client(codex_state, monkeypatch):
    fake = FakeCodexClient()
    fake.home = codex_state
    monkeypatch.setattr(host_login, "run_client", fake)
    return fake


def codex_logged_in(home: Path) -> Path:
    """The file a Codex login writes, as a placeholder: never a credential."""
    auth = home / "auth.json"
    auth.write_text('{"placeholder": true}\n', encoding="utf-8")
    return auth


def lock_held(home: Path) -> bool:
    """Whether another open file description holds the run lock."""
    import fcntl

    with (home / host_login.LOCK_NAME).open("ab") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
    return False


def test_the_codex_login_env_strips_every_billing_family(tmp_path):
    """testing-harness spec: Codex login never by API key."""
    home = tmp_path / "codex-home"
    environ = {**CODEX_STEERING, "CODEX_HOME": "/fake/home/.codex", "DISPLAY": ":0",
               "PATH": "/usr/bin"}
    env = login_env(host_login.CODEX, home, environ)
    assert env["DISPLAY"] == ":0"
    assert env["CODEX_HOME"] == str(home)
    for name in CODEX_STEERING:
        assert name not in env, name
    assert [name for name in env if name.startswith("CODEX_")] == ["CODEX_HOME"]
    assert set(CODEX_STEERING.values()).isdisjoint(env.values())


@POSIX_LOCKS
@pytest.mark.parametrize("device", [False, True], ids=["browser", "device-code"])
def test_the_codex_login_is_the_chatgpt_login(device, codex_state, codex_client, monkeypatch):
    for name, value in CODEX_STEERING.items():
        monkeypatch.setenv(name, value)
    assert host_login.CODEX.login_argv == ("login",)
    main(["login", "codex", *(["--device-auth"] if device else [])])
    [login] = [call for call in codex_client.calls if call["verb"] == "login"]
    assert login["argv"] == ["codex", "login", *(["--device-auth"] if device else [])]
    assert login["interactive"]
    assert not {"--with-api-key", "--with-access-token"} & set(login["argv"])
    assert login["env"] == login_env(host_login.CODEX, codex_state, os.environ)
    assert set(CODEX_STEERING.values()).isdisjoint(login["env"].values())


@POSIX_LOCKS
def test_the_codex_configuration_is_seeded_before_the_login(codex_state, codex_client):
    """testing-harness spec: Codex configuration seeded before the login."""
    import tomllib

    seen = {}
    codex_client.on_login = lambda: seen.update(
        config=tomllib.loads((codex_state / "config.toml").read_text(encoding="utf-8")),
        marker=(codex_state / MARKER).is_file())
    main(["login", "codex"])
    assert seen == {"config": host_login.PINNED_CONFIG, "marker": True}


@POSIX_LOCKS
def test_an_existing_codex_login_is_logged_out_first_under_the_run_lock(codex_state,
                                                                       codex_client):
    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    held = []
    codex_client.on_logout = lambda: held.append(lock_held(codex_state))
    codex_client.on_login = lambda: held.append(lock_held(codex_state))
    assert main(["login", "codex"]) == 0
    verbs = codex_client.verbs()
    assert verbs.index("logout") < verbs.index("login")
    assert held == [True, True]
    assert not lock_held(codex_state)


@POSIX_LOCKS
def test_a_codex_reset_wipes_the_marked_home_and_seeds_it_again(codex_state, codex_client):
    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    (codex_state / "AGENTS.md").write_text("synthetic\n", encoding="utf-8")
    assert main(["login", "codex", "--reset"]) == 0
    assert not (codex_state / "AGENTS.md").exists()
    assert not (codex_state / "auth.json").exists()
    assert (codex_state / MARKER).is_file()
    assert host_login.check_codex_home(codex_state) is None
    assert codex_client.verbs().count("logout") == 1


@POSIX_LOCKS
@pytest.mark.parametrize("passed", [False, True], ids=["X8-open", "X8-passed"])
@pytest.mark.parametrize("path", ["logout", "login-over-a-login", "reset"])
def test_the_codex_logout_note_comes_first_until_x8(path, passed, codex_state, codex_client,
                                                   monkeypatch, capsys):
    """testing-harness spec: Codex login note until X8."""
    monkeypatch.setattr(host_login, "X8_PASSED", passed)
    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    printed = []
    codex_client.on_logout = lambda: printed.append(capsys.readouterr().out)
    argv = {"logout": ["logout", "codex"], "login-over-a-login": ["login", "codex"],
            "reset": ["login", "codex", "--reset"]}[path]
    main(argv)
    assert len(printed) == 1
    assert (X8_NOTE in printed[0]) is not passed
    [logout] = [call for call in codex_client.calls if call["verb"] == "logout"]
    assert logout["env"] == login_env(host_login.CODEX, codex_state, os.environ)
    assert logout["stop_signal"] == signal.SIGINT  # the client's own stop request


SLOW_LOGOUT = """
import pathlib, signal, sys, time
here = pathlib.Path(__file__).parent
def done(*_):
    (here / "interrupted").write_text("interrupted", encoding="utf-8")
    sys.exit(0)
signal.signal(signal.SIGINT, done)
(here / "argv").write_text(" ".join(sys.argv[1:]), encoding="utf-8")
time.sleep(60)
"""


@POSIX_LOCKS
def test_a_codex_logout_at_its_limit_is_interrupted_not_terminated(codex_state, tmp_path,
                                                                   monkeypatch, capsys):
    """testing-harness spec: Stopping a host child — the harness login's logout
    at its limit gets the client's own stop request, an interrupt for Codex.
    The real `run_client` starts a fake `codex` that traps SIGINT."""
    bindir = tmp_path / "bin"
    bindir.mkdir()
    script = bindir / "codex"
    script.write_text(f"#!{sys.executable}\n{SLOW_LOGOUT}", encoding="utf-8")
    script.chmod(0o755)
    monkeypatch.setenv("PATH", f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}")
    monkeypatch.setattr(host_login, "CLIENT_TIMEOUT_S", 1.5)
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    assert main(["logout", "codex"]) == 3
    assert (bindir / "argv").read_text(encoding="utf-8") == "logout"
    assert (bindir / "interrupted").read_text(encoding="utf-8") == "interrupted"
    assert "exited 124" in capsys.readouterr().out
    assert not lock_held(codex_state)


def codex_status_lines(out: str, keys: list[str] = CODEX_STATUS_KEYS) -> dict[str, str]:
    pairs = dict(line.split(": ", 1) for line in out.splitlines() if line)
    assert list(pairs) == keys
    return pairs


@pytest.mark.usefixtures("codex_client")
def test_codex_status_of_a_ready_home(codex_state, capsys):
    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    assert main(["status", "codex"]) == 0
    out, err = capsys.readouterr()
    pairs = codex_status_lines(out)
    assert pairs["home"] == str(codex_state)
    assert (pairs["marker"], pairs["logged_in"], pairs["auth_method"]) == ("yes", "yes", "chatgpt")
    assert (pairs["config_pinned"], pairs["clean"], pairs["features_ok"]) == ("yes", "yes", "yes")
    assert (pairs["cli_version"], pairs["min_version"]) == ("0.160.0", "0.160.0")
    assert pairs["last_quota"] == "none"
    assert pairs["runs_use"] == "harness"
    assert pairs["last_written"].endswith(" ago")
    assert err == ""


@POSIX_LOCKS
def test_codex_clear_stop_removes_the_isolation_stop_and_nothing_else(codex_client, codex_state,
                                                                     monkeypatch, capsys):
    """add-codex-dev-runner Decision 16 (D-d): the same terminal and
    agent-marker refusals as the login, the run lock, the stop removed and
    nothing else touched; no client login runs."""
    import codex_cli

    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    codex_cli.record_stop(codex_state, "the workspace held entries the harness must not follow")
    assert main(["status", "codex"]) == 0  # reported, never a refusal of the status command
    assert codex_status_lines(capsys.readouterr().out)["stop"].startswith("isolation (the "
                                                                         "workspace held")
    before = {p.name: p.read_bytes() for p in codex_state.iterdir()
              if p.is_file() and p.name != "stop.json"}
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: False)
    assert main(["login", "codex", "--clear-stop"]) == host_login.EXIT_USAGE
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: True)
    monkeypatch.setenv("CLAUDECODE", "1")
    assert main(["login", "codex", "--clear-stop"]) == host_login.EXIT_USAGE
    monkeypatch.delenv("CLAUDECODE")
    assert codex_cli.read_stop(codex_state) is not None
    capsys.readouterr()
    assert main(["login", "codex", "--clear-stop"]) == 0
    assert "cleared the isolation stop" in capsys.readouterr().out
    assert codex_cli.read_stop(codex_state) is None
    after = {p.name: p.read_bytes() for p in codex_state.iterdir()
             if p.is_file() and p.name != host_login.LOCK_NAME}  # the lock it took
    assert after == {name: data for name, data in before.items() if name != host_login.LOCK_NAME}
    assert codex_client.calls == []  # no client login or logout ran
    assert main(["status", "codex"]) == 0
    assert codex_status_lines(capsys.readouterr().out)["stop"] == "none"


@pytest.mark.usefixtures("codex_client")
def test_codex_status_reports_an_api_key_login_without_the_key(codex_state, monkeypatch,
                                                               capsys):
    """testing-harness spec: Codex status reveals no key."""
    import codex_cli

    monkeypatch.setattr(codex_cli, "probe",
                        FakeProbe(login=f"Logged in using an API key - {MASKED_KEY}\n"))
    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    assert main(["status", "codex"]) == 3
    out, err = capsys.readouterr()
    assert codex_status_lines(out)["auth_method"] == "api-key"
    assert MASKED_KEY not in out + err
    assert "uv run poe host-login codex" in err


@pytest.mark.usefixtures("codex_client")
@pytest.mark.parametrize(("probe", "named"), [
    (FakeProbe(version="codex-cli 0.133.0\n"), "0.133.0"),
    (FakeProbe(login="Not logged in\n"), "holds no ChatGPT login"),
    (FakeProbe(features=(CODEX_STREAMS / "features-extra-on.txt").read_text(encoding="utf-8")),
     "realtime_conversation"),
])
def test_codex_status_exits_not_ready_naming_the_cause(probe, named, codex_state, monkeypatch,
                                                       capsys):
    import codex_cli

    monkeypatch.setattr(codex_cli, "probe", probe)
    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    assert main(["status", "codex"]) == 3
    out, err = capsys.readouterr()
    codex_status_lines(out)
    assert err.startswith("untested: ")
    assert named in err


def test_codex_status_of_a_missing_home_creates_nothing(codex_state, monkeypatch, capsys):
    no_client(monkeypatch)
    assert main(["status", "codex"]) == 3
    out, err = capsys.readouterr()
    pairs = codex_status_lines(out)
    assert (pairs["marker"], pairs["logged_in"], pairs["last_written"]) == ("no", "no", "never")
    assert "uv run poe host-login codex" in err
    assert not codex_state.exists()


@pytest.mark.usefixtures("codex_client")
def test_codex_status_never_opens_the_stored_login(codex_state, monkeypatch, capsys):
    """testing-harness spec: Codex stored login never opened."""
    import builtins
    import io

    host_login.seed(host_login.CODEX, codex_state)
    auth = codex_logged_in(codex_state)
    written = time.time() - 3 * 3600 - 60
    os.utime(auth, (written, written))
    opened = []

    def guard(original):
        def wrapper(target, *args, **kwargs):
            if Path(str(target)).name == "auth.json":
                opened.append(str(target))
                raise AssertionError("auth.json was opened")
            return original(target, *args, **kwargs)
        return wrapper

    def guard_method(original):
        def wrapper(self, *args, **kwargs):
            if self.name == "auth.json":
                opened.append(str(self))
                raise AssertionError("auth.json was read")
            return original(self, *args, **kwargs)
        return wrapper

    monkeypatch.setattr(builtins, "open", guard(builtins.open))
    monkeypatch.setattr(io, "open", guard(io.open))
    monkeypatch.setattr(Path, "read_text", guard_method(Path.read_text))
    monkeypatch.setattr(Path, "read_bytes", guard_method(Path.read_bytes))
    assert main(["status", "codex"]) == 0
    pairs = codex_status_lines(capsys.readouterr().out)
    assert pairs["last_written"] == "3h ago"
    assert opened == []


@POSIX_LOCKS
@pytest.mark.usefixtures("codex_client")
@pytest.mark.parametrize(("answer", "code"), [("quota-ok.json", 0), ("quota-free.json", 3)])
def test_codex_status_quota_reads_under_the_run_lock(answer, code, codex_state, monkeypatch,
                                                     capsys):
    import codex_cli

    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    snapshot = {"primary": {"used_percent": 10.0, "window_minutes": 300, "resets_at": 1791300000},
                "secondary": None, "plan_type": "plus"}
    (codex_state / "quota.json").write_text(json.dumps(snapshot), encoding="utf-8")
    held = []

    def fake_read(home, _environ=None):
        held.append(lock_held(home))
        return codex_cli.parse_quota(json.loads((CODEX_STREAMS / answer).read_text(
            encoding="utf-8")))

    monkeypatch.setattr(codex_cli, "read_quota", fake_read)
    assert main(["status", "codex", "--quota"]) == code
    out, err = capsys.readouterr()
    pairs = codex_status_lines(out, [*CODEX_STATUS_KEYS, "quota"])
    assert held == [True]
    assert "10%" in pairs["last_quota"]
    assert "12%" in pairs["quota"]
    assert "5-hour" in pairs["quota"]
    if code:
        assert "free" in err
    else:
        assert "plus" in pairs["quota"]


def test_the_codex_only_options_are_refused_for_claude(state, monkeypatch, capsys):
    no_client(monkeypatch)
    with pytest.raises(SystemExit) as usage:
        main(["login", "claude", "--device-auth"])
    assert usage.value.code == 2
    with pytest.raises(SystemExit) as usage:
        main(["status", "claude", "--quota"])
    assert usage.value.code == 2
    assert not state.exists()
    assert "codex" in capsys.readouterr().err


@POSIX_LOCKS
def test_a_held_run_lock_makes_a_codex_logout_not_ready(codex_state, codex_client, capsys):
    """testing-harness spec: Serial Codex runs — the commands wait the bounded
    time, then refuse with the one template and exit 3."""
    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    with host_login.run_lock(codex_state):
        assert main(["logout", "codex"]) == 3
    assert "logout" not in codex_client.verbs()
    err = capsys.readouterr().err
    assert err.startswith("untested: another Codex run holds the harness home")
    assert host_login.LOCK_NAME in err


def refused_location(home: Path, tmp_path: Path, monkeypatch) -> str:
    """A marked, logged-in home whose state root lies in the (faked) system
    temporary directory: `check_location` refuses it."""
    host_login.seed(host_login.CODEX, home)
    codex_logged_in(home)
    monkeypatch.setattr(host_login, "system_tempdir", lambda: str(tmp_path))
    return "temporary directory"


def unmarked_copy(home: Path, _tmp_path: Path, _monkeypatch) -> str:
    """An operator's `~/.codex` copied to the harness path: a login, no marker."""
    home.mkdir(parents=True)
    (home / "config.toml").write_text(host_login.PINNED_CONFIG_TOML, encoding="utf-8")
    codex_logged_in(home)
    return host_login.MARKER


def unpinned_config(home: Path, _tmp_path: Path, _monkeypatch) -> str:
    host_login.seed(host_login.CODEX, home)
    codex_logged_in(home)
    with (home / "config.toml").open("a", encoding="utf-8") as fh:
        fh.write('model_provider_override = "openrouter"\n')
    return "config.toml"


@pytest.mark.parametrize("arrange", [refused_location, unmarked_copy, unpinned_config],
                         ids=["refused-location", "unmarked-home", "unpinned-config"])
def test_codex_status_probes_no_home_the_harness_does_not_adopt(arrange, codex_state, tmp_path,
                                                                monkeypatch, capsys):
    """testing-harness spec: Codex home in the temporary directory; Unmarked
    directory never adopted — `status codex --quota` runs neither `login
    status`, `features list` nor the quota read against such a home, and
    creates no lock file in it."""
    import codex_cli

    named = arrange(codex_state, tmp_path, monkeypatch)
    no_client(monkeypatch)

    def no_read(*_args, **_kwargs):
        pytest.fail("the quota read started")

    monkeypatch.setattr(codex_cli, "read_quota", no_read)
    assert main(["status", "codex", "--quota"]) == 3
    assert [call for call in codex_cli.probe.calls if call != ["--version"]] == []
    assert not (codex_state / host_login.LOCK_NAME).exists()
    out, err = capsys.readouterr()
    pairs = codex_status_lines(out, [*CODEX_STATUS_KEYS, "quota"])
    assert pairs["quota"].startswith("not read")
    assert (pairs["logged_in"], pairs["features_ok"]) == ("unknown", "unknown")
    assert named in err


@pytest.mark.parametrize("argv", [["login", "codex"], ["logout", "codex"],
                                  ["status", "codex", "--quota"]])
def test_without_posix_file_locks_the_codex_commands_refuse_cleanly(argv, codex_state,
                                                                    codex_client, monkeypatch,
                                                                    capsys):
    """Windows: no traceback, exit 3 in the one template, and a login or logout
    creates nothing and starts no client."""
    monkeypatch.setattr(host_login, "fcntl", None)
    if argv[0] != "login":
        host_login.seed(host_login.CODEX, codex_state)
        codex_logged_in(codex_state)
    assert main(argv) == 3
    assert codex_client.calls == []
    err = capsys.readouterr().err
    assert err.startswith("untested: this platform lacks POSIX file locks")
    assert argv[0] != "login" or not codex_state.exists()


# ---------- the Copilot token-file commands (add-copilot-dev-runner) ------------------

COPILOT_STATUS_KEYS = ["home", "marker", "token_present", "auth_type", "host_ok", "plan_class",
                       "token_based_billing", "overage_permitted", "overage_count",
                       "overage_entitlement", "remaining_pct", "reset_date", "stop", "go",
                       "clean", "cli_version", "pinned_version", "sandbox", "runs_use"]
SANDBOX_PROBLEM = copilot_cli.sandbox_problem  # the real one, before a fixture stubs it
VERSION_READ = copilot_cli.installed_version  # the real one: it starts `copilot --version`
POSIX_LOCKS = pytest.mark.skipif(host_login.fcntl is None, reason="the run lock needs fcntl")


class FakeStatusRead:
    """`copilot_cli.read_status`: answers from a status fixture, records the token it
    was handed and whether the run lock was held, never starts a client."""

    def __init__(self, home: Path, fixture: str = "status-ok"):
        self.home, self.fixture = home, fixture
        self.calls: list[dict] = []
        self.writes: dict[str, str] = {}  # what the client writes into the home, by path

    def __call__(self, home, _environ=None, *, token, models=False):
        import fcntl

        for rel, text in self.writes.items():
            (home / rel).parent.mkdir(parents=True, exist_ok=True)
            (home / rel).write_text(text, encoding="utf-8")
        with (home / host_login.LOCK_NAME).open("ab") as handle:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                held = False
            except BlockingIOError:
                held = True
        self.calls.append({"token": token, "models": models, "lock_held": held})
        replies = dict(copilot_reply(self.fixture if token else "status-auth-error"))
        if models:
            replies["models"] = copilot_reply("models")
        return copilot_cli.parse_status(replies)


@pytest.fixture
def copilot_state(state, copilot_account, monkeypatch):
    """The state root of `state`, an account home of the test's own
    (`copilot_account`), no real client: the version and the status read are
    faked."""
    assert not state.is_relative_to(copilot_account)
    monkeypatch.setattr(copilot_cli, "installed_version", lambda *_a: (1, 0, 91))
    monkeypatch.setattr(copilot_cli, "managed_problem", lambda *_a: None)
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda *_a, **_k: None)
    home = host_login.home(host_login.COPILOT)
    assert home.parent == state.parent  # beside the Claude home of `state`
    fake = FakeStatusRead(home)
    monkeypatch.setattr(copilot_cli, "read_status", fake)
    no_client(monkeypatch)
    return home


def enter_token(monkeypatch, value: str = COPILOT_TOKEN, order: list | None = None) -> list:
    prompts: list[str] = order if order is not None else []

    def getpass(prompt):
        prompts.append(prompt)
        return value

    monkeypatch.setattr(host_login.getpass, "getpass", getpass)
    return prompts


def status_pairs(out: str) -> dict[str, str]:
    return dict(line.split(": ", 1) for line in out.splitlines() if ": " in line)


@POSIX_LOCKS
def test_the_copilot_login_writes_the_token_file_beside_the_home(copilot_state, monkeypatch,
                                                                capsys):
    """testing-harness spec: Token stored only in the token file."""
    order: list = []
    real_seed = host_login.seed
    monkeypatch.setattr(host_login, "seed", lambda record, home: (
        order.append("seed"), real_seed(record, home))[1])
    enter_token(monkeypatch, order=order)
    assert main(["login", "copilot"]) == 0
    assert order == ["seed", host_login.TOKEN_PROMPT]
    path = host_login.token_path(copilot_state)
    assert path.read_text(encoding="utf-8") == COPILOT_TOKEN + "\n"
    assert path.stat().st_mode & 0o777 == 0o600
    assert path.parent == copilot_state.parent
    inside = [p for p in copilot_state.rglob("*") if p.is_file()
              and COPILOT_TOKEN in p.read_text(encoding="utf-8", errors="replace")]
    assert inside == []
    assert copilot_cli.read_stop(copilot_state)["kind"] == "approval"
    out, err = capsys.readouterr()
    assert COPILOT_TOKEN not in out + err
    assert status_pairs(out)["stop"].startswith("approval")
    assert "--clear-stop" in out


@POSIX_LOCKS
@pytest.mark.usefixtures("copilot_state")
def test_the_copilot_login_exits_3_when_the_token_is_rejected(monkeypatch, capsys):
    copilot_cli.read_status.fixture = "status-auth-error"
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 3
    assert "fine-grained token" in capsys.readouterr().err


@POSIX_LOCKS
@pytest.mark.parametrize("value", ["ghp_CLASSIC_PLACEHOLDER", "gho_OTHER_PLACEHOLDER",
                                   "plain-text"])
def test_the_copilot_login_refuses_anything_but_a_fine_grained_token(value, copilot_state,
                                                                     monkeypatch, capsys):
    """testing-harness spec: Classic token refused."""
    enter_token(monkeypatch, value)
    assert main(["login", "copilot"]) == host_login.EXIT_USAGE
    assert not host_login.token_path(copilot_state).exists()
    out, err = capsys.readouterr()
    assert value not in out + err
    assert "fine-grained" in err
    assert copilot_cli.read_stop(copilot_state) is None


def test_the_copilot_login_refuses_without_a_terminal_or_inside_an_agent(copilot_state,
                                                                        monkeypatch, capsys):
    prompts = enter_token(monkeypatch)
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: False)
    assert main(["login", "copilot"]) == host_login.EXIT_USAGE
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: True)
    monkeypatch.setenv("CLAUDECODE", "1")
    assert main(["login", "copilot"]) == host_login.EXIT_USAGE
    assert prompts == []
    assert not copilot_state.exists()
    assert "CLAUDECODE" in capsys.readouterr().err


@POSIX_LOCKS
@pytest.mark.usefixtures("copilot_state")
def test_after_a_login_a_live_run_waits_for_the_approval(monkeypatch):
    """testing-harness spec: First run after a login waits for approval — before
    any Copilot process starts: the real version read is back in place, so a
    `copilot --version` before the stop row would reach the conftest sentinel."""
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 0
    monkeypatch.setattr(copilot_cli, "installed_version", VERSION_READ)
    popen: list = []
    monkeypatch.setattr(copilot_cli.subprocess, "Popen", lambda *a, **_k: popen.append(a))
    with pytest.raises(copilot_cli.CopilotRefused) as refused:
        copilot_cli.isolated_home(None, None)
    assert "approval stop" in refused.value.message
    assert host_login.CLEAR_STOP_COMMAND in refused.value.message
    assert refused.value.kind == "precondition"
    assert popen == []


@POSIX_LOCKS
@pytest.mark.usefixtures("codex_client")
def test_a_codex_reset_keeps_the_isolation_stop(codex_state):
    """testing-harness spec: Codex reset keeps the isolation stop — read
    before the wipe, recorded again in the reseeded home with its cause and
    time, so the next Codex run is still refused until a clear."""
    import codex_cli

    host_login.seed(host_login.CODEX, codex_state)
    codex_logged_in(codex_state)
    codex_cli.record_stop(codex_state, "the workspace held entries the harness must not follow")
    before = codex_cli.read_stop(codex_state)
    (codex_state / "AGENTS.md").write_text("synthetic\n", encoding="utf-8")
    assert main(["login", "codex", "--reset"]) == 0
    assert not (codex_state / "AGENTS.md").exists()  # wiped and seeded again
    assert codex_cli.read_stop(codex_state) == before
    assert codex_cli.stop_problem(codex_cli.read_stop(codex_state)).kind == "isolation"
    assert host_login.check_codex_home(codex_state) is None
    # a reset with no stop recorded leaves none
    codex_cli.clear_stop(codex_state)
    assert main(["login", "codex", "--reset"]) == 0
    assert codex_cli.read_stop(codex_state) is None


@POSIX_LOCKS
def test_a_copilot_reset_deletes_the_token_wipes_and_asks_again(copilot_state, monkeypatch):
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 0
    (copilot_state / "skills").mkdir()  # a synced entry the reset clears
    copilot_cli.clear_stop(copilot_state)
    prompts = enter_token(monkeypatch, "github_pat_SECOND_SYNTHETIC")
    assert main(["login", "copilot", "--reset"]) == 0
    assert prompts == [host_login.TOKEN_PROMPT]
    assert not (copilot_state / "skills").exists()
    assert host_login.token_path(copilot_state).read_text(encoding="utf-8") == (
        "github_pat_SECOND_SYNTHETIC\n")
    assert copilot_cli.read_stop(copilot_state)["kind"] == "approval"


@POSIX_LOCKS
@pytest.mark.parametrize("kind", ["billing", "isolation", "approval"])
def test_clear_stop_removes_any_stop_and_nothing_else(kind, copilot_state, monkeypatch, capsys):
    """testing-harness spec: Only the operator clears a stop."""
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 0
    copilot_cli.clear_stop(copilot_state)
    copilot_cli.record_stop(copilot_state, kind, f"synthetic {kind}")
    settings = (copilot_state / "settings.json").read_text(encoding="utf-8")
    token = host_login.token_path(copilot_state).read_text(encoding="utf-8")
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: False)
    assert main(["login", "copilot", "--clear-stop"]) == host_login.EXIT_USAGE
    assert copilot_cli.read_stop(copilot_state)["kind"] == kind
    monkeypatch.setattr(host_login, "stdin_is_tty", lambda: True)
    monkeypatch.setenv("CODEX_SANDBOX", "seatbelt")
    assert main(["login", "copilot", "--clear-stop"]) == host_login.EXIT_USAGE
    monkeypatch.delenv("CODEX_SANDBOX")
    assert copilot_cli.read_go(copilot_state) is None  # the stop ended the go
    capsys.readouterr()
    assert main(["login", "copilot", "--clear-stop"]) == 0
    out = capsys.readouterr().out
    assert f"cleared the {kind} stop" in out
    assert "recorded the go: it covers one canary" in out
    assert copilot_cli.read_stop(copilot_state) is None
    assert copilot_cli.read_go(copilot_state)["canary"] is None  # the canary comes first
    assert (copilot_state / "settings.json").read_text(encoding="utf-8") == settings
    assert host_login.token_path(copilot_state).read_text(encoding="utf-8") == token


@POSIX_LOCKS
def test_clear_stop_without_a_stop_records_the_go_alone(copilot_state, monkeypatch, capsys):
    """testing-harness spec: the clear option records the go with no stop
    recorded too, and the status command prints what it covers."""
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 0
    copilot_cli.clear_stop(copilot_state)
    copilot_cli.record_canary_pass(copilot_state, "00000000-0000-4000-8000-000000000000")
    capsys.readouterr()
    assert main(["login", "copilot", "--clear-stop"]) == 0
    out = capsys.readouterr().out
    assert "no stop is recorded in the Copilot harness home; recorded the go" in out
    assert copilot_cli.read_go(copilot_state)["canary"] is None  # a new go: a canary first
    main(["status", "copilot"])
    assert "go: canary (go given " in capsys.readouterr().out


def test_clear_stop_and_reset_are_separate_and_copilot_or_codex_only(capsys):
    """`--clear-stop` serves the clients that record stops: Copilot, and Codex
    since add-codex-dev-runner Decision 16 (D-d)."""
    for argv in (["login", "copilot", "--clear-stop", "--reset"],
                 ["login", "codex", "--clear-stop", "--reset"],
                 ["login", "claude", "--clear-stop"], ["status", "claude", "--models"],
                 ["status", "codex", "--no-token"]):
        with pytest.raises(SystemExit):
            main(argv)
        assert "--" in capsys.readouterr().err  # the usage error names the option


@POSIX_LOCKS
def test_the_copilot_logout_deletes_only_the_token_file(copilot_state, monkeypatch, capsys):
    """testing-harness spec: Copilot logout deletes only the token file."""
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 0
    before = sorted(p.name for p in copilot_state.iterdir())
    capsys.readouterr()
    assert main(["logout", "copilot"]) == 0
    out, err = capsys.readouterr()
    assert not host_login.token_path(copilot_state).exists()
    assert sorted(p.name for p in copilot_state.iterdir()) == before
    assert "github.com/settings/personal-access-tokens" in out
    assert "unverified" not in out + err


@POSIX_LOCKS
@pytest.mark.usefixtures("copilot_state")
def test_the_copilot_status_prints_exactly_its_keys_and_no_account_detail(monkeypatch, capsys):
    """testing-harness spec: Copilot status reveals no account details; the status
    read holds the run lock; a recorded stop does not refuse the status command."""
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 0
    capsys.readouterr()
    assert main(["status", "copilot"]) == 0  # the approval stop is reported, not refused
    out, err = capsys.readouterr()
    pairs = status_pairs(out)
    assert list(pairs) == COPILOT_STATUS_KEYS
    assert (pairs["marker"], pairs["token_present"], pairs["auth_type"], pairs["host_ok"]) == (
        "yes", "yes", "token", "yes")
    assert (pairs["overage_permitted"], pairs["overage_count"], pairs["overage_entitlement"],
            pairs["remaining_pct"]) == ("false", "0", "0", "80.0")
    assert pairs["stop"].startswith("approval")
    assert (pairs["cli_version"], pairs["pinned_version"], pairs["clean"]) == (
        "1.0.91", "1.0.91", "yes")
    for secret in ("fixture-login-octocat", "fixture-org", "FIXTURE_REPLY_ONLY", COPILOT_TOKEN):
        assert secret not in out + err
    reads = copilot_cli.read_status.calls
    assert reads
    assert all(call["lock_held"] for call in reads)


@POSIX_LOCKS
@pytest.mark.usefixtures("copilot_state")
def test_the_copilot_status_options_add_the_models_and_the_tokenless_read(monkeypatch, capsys):
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 0
    capsys.readouterr()
    assert main(["status", "copilot", "--models", "--no-token"]) == 0
    pairs = status_pairs(capsys.readouterr().out)
    assert pairs["model copilot-fixture-a"] == "policy enabled; efforts low, medium, high"
    assert pairs["model copilot-fixture-c"].startswith("policy disabled")
    assert pairs["logged_in"] == "no"
    tokens = [call["token"] for call in copilot_cli.read_status.calls[-2:]]
    assert tokens == [COPILOT_TOKEN, None]


@POSIX_LOCKS
@pytest.mark.usefixtures("copilot_state")
def test_a_missing_sandbox_tool_makes_the_copilot_login_not_ready(monkeypatch, capsys):
    """The login reports ready only when the status read passes the preflight,
    the approval stop apart: a missing sandbox tool fails it, naming the tool."""
    monkeypatch.setattr(copilot_cli, "sandbox_problem", lambda _which, **_k: SANDBOX_PROBLEM(
        lambda name: None if name == "slirp4netns" else f"/usr/bin/{name}", platform="linux"))
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == host_login.EXIT_NOT_READY
    out, err = capsys.readouterr()
    assert "slirp4netns" in status_pairs(out)["sandbox"]
    assert "needs slirp4netns on PATH" in err
    assert "install slirp4netns" in err.lower()


@POSIX_LOCKS
@pytest.mark.usefixtures("copilot_state")
def test_the_state_file_the_status_read_writes_keeps_the_login_ready(monkeypatch, capsys):
    """testing-harness spec: Copilot state file written by the client — the first
    login's own read wrote it and an empty process log (2026-10-06), and the
    home stays clean without a reset."""
    copilot_cli.read_status.writes = {
        "config.json": (COPILOT_STREAMS / "client-config.jsonc").read_text(encoding="utf-8"),
        "logs/process-1791308979893-4242.log": ""}
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == 0
    out, err = capsys.readouterr()
    assert status_pairs(out)["clean"] == "yes"
    assert "not clean" not in err


@POSIX_LOCKS
@pytest.mark.usefixtures("copilot_state")
def test_a_log_the_status_read_left_in_the_home_is_reported_on_the_clean_line(monkeypatch,
                                                                              capsys):
    """The `clean` line names the home as the reads left it, the same entry the
    refusal names — not the state before the reads."""
    copilot_cli.read_status.writes = {"logs/process-1791308979893-4242.log": "fixture-log-line\n"}
    enter_token(monkeypatch)
    assert main(["login", "copilot"]) == host_login.EXIT_NOT_READY
    out, err = capsys.readouterr()
    assert status_pairs(out)["clean"].startswith("logs/ (client process logs")
    assert "is not clean: it holds logs/" in err
    for value in ("process-1791308979893", "fixture-log-line"):
        assert value not in out + err


@pytest.mark.usefixtures("copilot_state")
def test_the_copilot_status_without_a_home_reads_nothing(capsys):
    assert main(["status", "copilot"]) == 3
    pairs = status_pairs(capsys.readouterr().out)
    assert (pairs["marker"], pairs["token_present"], pairs["auth_type"]) == ("no", "no", "unknown")
    assert copilot_cli.read_status.calls == []
