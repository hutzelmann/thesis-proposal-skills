"""L0: the isolated host child's environment (testing-harness spec: Isolated
child environment).

The child of an isolated run gets an allowlisted environment, not the
launcher's with CLAUDE_CONFIG_DIR swapped. The synthetic environment below
has the shape of a desktop-app session as observed on 2026-10-04 — every value
a fake marker, so no test can print or compare a real secret.
"""

import json
import os
from pathlib import PurePosixPath

import claude_runner
import pytest
import routing
from account_surfaces import CONNECTORS_OFF, PROFILE_DIR
from claude_cli import parse_events
from helpers import followed
from routing import ADMITTED_ENV, isolated_env

# never created: the function only names the directory to the child
CONFIG = PurePosixPath("/fake/devrun-config/config")
PROFILE = str(CONFIG / PROFILE_DIR)
TOKEN = "fake-messaging-token-0000"
# set by the harness, never admitted (testing-harness spec: Isolated child environment)
ACCOUNT_SURFACE_NAMES = {"ENABLE_CLAUDEAI_MCP_SERVERS", "ANTHROPIC_CONFIG_DIR"}

SESSION_BINDING = {
    "CLAUDECODE": "1",
    "CLAUDE_CODE_ENTRYPOINT": "claude-desktop",
    "CLAUDE_CODE_SESSION_ID": "fake-session",
    "CLAUDE_CODE_HOST_SESSION_ID": "fake-host-session",
    "CLAUDE_CODE_CHILD_SESSION": "1",
    "CLAUDE_CODE_MESSAGING_SOCKET": "/tmp/fake.sock",
    "CLAUDE_CODE_MESSAGING_TOKEN": TOKEN,
    "CLAUDE_PID": "1",
}
AUTH_PATH = {
    "CLAUDE_CODE_SDK_HAS_HOST_AUTH_REFRESH": "1",
    "CLAUDE_CODE_OAUTH_SCOPES": "fake-scopes",
    "CLAUDE_CODE_ACCOUNT_UUID": "fake-account",
    "CLAUDE_CODE_ORGANIZATION_UUID": "fake-org",
}
HOST_TUNING = {
    "CLAUDE_EFFORT": "fake-effort",
    "CLAUDE_CODE_ENABLE_ASK_USER_QUESTION_TOOL": "1",
    "CLAUDE_CODE_REPORT_FINDINGS": "1",
    "CLAUDE_CODE_DISABLE_CRON": "1",
    # none of these carries the host's prefix — a CLAUDE* filter keeps them
    "ANTHROPIC_BASE_URL": "http://127.0.0.1:1/fake",
    "ANTHROPIC_API_KEY": "fake-api-key",
    "API_TIMEOUT_MS": "1",
    "DISABLE_MICROCOMPACT": "1",
    "DISABLE_AUTOUPDATER": "1",
    "MCP_CONNECTION_NONBLOCKING": "1",
    "MCP_SERVER_CONNECTION_BATCH_SIZE": "1",
    "AI_AGENT": "fake-agent",
}
MACHINE = {
    "PATH": "/fake/bin",
    "HOME": "/fake/home",
    "CLAUDE_CODE_OAUTH_TOKEN": "fake-oauth-token",
    "USER": "erika",
    "SHELL": "/bin/fake-sh",
    "LANG": "de_DE.UTF-8",
    "LC_TIME": "de_DE.UTF-8",
    "TMPDIR": "/fake/tmp",
    "XDG_CACHE_HOME": "/fake/home/.cache",
    "HTTPS_PROXY": "http://proxy.invalid:3128",
    "https_proxy": "http://proxy.invalid:3128",
    "SSL_CERT_FILE": "/fake/ca.pem",
    "NIX_SSL_CERT_FILE": "/fake/ca.pem",
    "SYSTEMROOT": "C:\\FakeWindows",
}
# inherited values the harness must replace, not pass on
ACCOUNT = {
    "ENABLE_CLAUDEAI_MCP_SERVERS": "true",
    "ANTHROPIC_CONFIG_DIR": "/fake/home/.config/anthropic",
}
DESKTOP = {**SESSION_BINDING, **AUTH_PATH, **HOST_TUNING, **MACHINE, **ACCOUNT,
           "CLAUDE_CONFIG_DIR": "/fake/home/.claude",
           "TERM": "xterm-256color", "XDG_SESSION_TYPE": "wayland",
           "SOME_FUTURE_HOST_KNOB": "1"}


@pytest.fixture
def desktop_session(monkeypatch):
    """The process environment replaced by the synthetic one, so a failing
    comparison can only ever print fake values. pytest's own variables stay:
    it pops them itself after the test."""
    for name in list(os.environ):
        if not name.startswith("PYTEST"):
            monkeypatch.delenv(name)
    for name, value in DESKTOP.items():
        monkeypatch.setenv(name, value)


# ---------- the allowlist ----------------------------------------------------


def test_session_binding_and_auth_path_are_dropped():
    env = isolated_env(CONFIG, DESKTOP)
    leaked = sorted(set(env) & (set(SESSION_BINDING) | set(AUTH_PATH)))
    assert leaked == []


def test_host_tuning_outside_the_prefix_is_dropped():
    env = isolated_env(CONFIG, DESKTOP)
    assert sorted(set(env) & set(HOST_TUNING)) == []


def test_unknown_and_session_variables_are_dropped():
    """An allowlist: a variable no one reviewed never reaches the child."""
    env = isolated_env(CONFIG, DESKTOP)
    for name in ("SOME_FUTURE_HOST_KNOB", "TERM", "XDG_SESSION_TYPE"):
        assert name not in env


def test_machine_plumbing_and_the_long_lived_token_pass_unchanged():
    env = isolated_env(CONFIG, DESKTOP)
    for name, value in MACHINE.items():
        assert env.get(name) == value, name


def test_config_dir_is_the_isolated_one_and_only_the_surface_switches_are_added():
    env = isolated_env(CONFIG, DESKTOP)
    assert env["CLAUDE_CONFIG_DIR"] == str(CONFIG)
    assert set(env) == set(MACHINE) | {"CLAUDE_CONFIG_DIR"} | ACCOUNT_SURFACE_NAMES


def test_inherited_account_surface_variables_are_replaced():
    """The connector switch is off and the profile directory is the
    configuration's empty one, whatever the launching session set."""
    env = isolated_env(CONFIG, DESKTOP)
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert env["ANTHROPIC_CONFIG_DIR"] == PROFILE
    assert ACCOUNT["ANTHROPIC_CONFIG_DIR"] not in env.values()


def test_the_profile_directory_is_the_only_anthropic_name():
    names = [name for name in isolated_env(CONFIG, DESKTOP) if name.startswith("ANTHROPIC_")]
    assert names == ["ANTHROPIC_CONFIG_DIR"]


def test_absent_variables_are_not_invented():
    assert isolated_env(CONFIG, {"PATH": "/fake/bin"}) == {
        "PATH": "/fake/bin", "CLAUDE_CONFIG_DIR": str(CONFIG), **CONNECTORS_OFF,
        "ANTHROPIC_CONFIG_DIR": PROFILE}


def test_the_launching_environment_is_left_alone():
    source = dict(DESKTOP)
    isolated_env(CONFIG, source)
    assert source == DESKTOP


@pytest.mark.usefixtures("desktop_session")
def test_defaults_to_the_process_environment():
    assert isolated_env(CONFIG) == isolated_env(CONFIG, DESKTOP)


def test_admitted_names_stay_reviewed():
    """Every admission is a reviewed line in routing.py; nothing the host
    owns or a desktop session binds may slip into the list."""
    assert {"PATH", "HOME", "CLAUDE_CODE_OAUTH_TOKEN"} <= ADMITTED_ENV
    owned = {n for n in ADMITTED_ENV
             if n.startswith(("ANTHROPIC_", "MCP_", "DISABLE_"))
             or (n.startswith("CLAUDE") and n != "CLAUDE_CODE_OAUTH_TOKEN")}
    assert owned == set()


def test_building_the_environment_prints_nothing(capsys):
    isolated_env(CONFIG, DESKTOP)
    out, err = capsys.readouterr()
    assert (out, err) == ("", "")
    assert TOKEN not in out + err


# ---------- both callers -----------------------------------------------------

# a subscription result as run_claude accepts it: init without an API-key
# source, an allowed rate-limit report, the result
RESULT = "\n".join(json.dumps(event) for event in (
    {"type": "system", "subtype": "init", "model": "claude-fixture-1-0", "apiKeySource": "none"},
    {"type": "rate_limit_event", "rate_limit_info": {"status": "allowed",
                                                     "isUsingOverage": False}},
    {"type": "result", "subtype": "success", "is_error": False, "result": "done",
     "num_turns": 1},
))


def capture_run(monkeypatch) -> dict:
    """The dev runner's host replaced at its stream reader."""
    seen: dict = {}

    def fake_follow(_command, **kwargs):
        seen["env"] = kwargs["env"]
        return followed(parse_events(RESULT), kwargs["stop"])

    monkeypatch.setattr(claude_runner, "follow_stream", fake_follow)
    return seen


@pytest.mark.usefixtures("desktop_session")
def test_isolated_runner_hands_the_child_the_allowlisted_environment(monkeypatch, tmp_path):
    seen = capture_run(monkeypatch)
    # a configuration on disk: the runner checks it for synced content afterwards
    claude_runner.run_claude(tmp_path, "request", "haiku", 5, config=tmp_path)
    env = seen["env"]
    assert env["CLAUDE_CONFIG_DIR"] == str(tmp_path)
    assert "CLAUDE_CODE_ENTRYPOINT" not in env
    assert "CLAUDE_CODE_MESSAGING_TOKEN" not in env
    assert "ANTHROPIC_BASE_URL" not in env
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "fake-oauth-token"
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert env["ANTHROPIC_CONFIG_DIR"] == str(tmp_path / PROFILE_DIR)


@pytest.mark.usefixtures("desktop_session")
def test_ambient_runner_inherits_the_operator_environment_minus_billing(monkeypatch, tmp_path):
    """Ambient measures the operator's session: everything but the billing
    variables, with the connector switch off (testing-harness spec: Billing
    variables never reach the model run; Connector switch on every host child)."""
    seen = capture_run(monkeypatch)
    claude_runner.run_claude(tmp_path, "request", "haiku", 5)
    billing = {n for n in DESKTOP if n.startswith(("ANTHROPIC_", "CLAUDE_CODE_USE_"))}
    assert billing
    inherited = {n: v for n, v in seen["env"].items() if not n.startswith("PYTEST")}
    assert inherited == {**{n: v for n, v in DESKTOP.items() if n not in billing},
                         **CONNECTORS_OFF}
    assert not [n for n in inherited if n.startswith("ANTHROPIC_")]


def capture_popen(monkeypatch) -> dict:
    seen: dict = {}

    class FakePopen:
        """Enough of Popen for stream_events: one non-routing event, then EOF."""

        def __init__(self, _command, **kwargs):
            seen["env"] = kwargs.get("env")
            self.stdout = iter([json.dumps({"type": "system"}) + "\n"])
            self.stderr = None

        def terminate(self):
            pass

        def wait(self, **_kwargs):
            return 0

        def kill(self):
            pass

    monkeypatch.setattr(routing.subprocess, "Popen", FakePopen)
    return seen


@pytest.mark.usefixtures("desktop_session")
def test_routing_rig_hands_the_child_the_allowlisted_environment(monkeypatch, tmp_path):
    seen = capture_popen(monkeypatch)
    routing.stream_events(tmp_path, CONFIG, "utterance", "haiku", 5)
    env = seen["env"]
    assert env == isolated_env(CONFIG)
    assert "CLAUDE_CODE_SESSION_ID" not in env
    assert "DISABLE_MICROCOMPACT" not in env
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert env["ANTHROPIC_CONFIG_DIR"] == PROFILE
