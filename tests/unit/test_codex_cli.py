"""L0: the Codex host of the dev runner (`harness/codex_cli.py`; testing-harness
spec: Dev-runner host adapters, Codex plan billing guard, Harness-owned host
logins).

No test starts the real `codex`. The pure readers run over the synthetic
streams in `data/codex_streams/` (README there: every file is synthetic, derived
from the 0.160 sources). Where a child process is needed — the run lock held by a
child, the stop signal, the quota read's handshake and timeout — it is a Python
script written under `tmp_path`: started directly, or named `codex` on a `PATH`
handed to the module, never the installed CLI.
"""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from argparse import Namespace
from pathlib import Path

import claude_runner
import codex_cli
import host_login
import pytest
import routing
from helpers import REGISTRY_PATH
from host_login import CODEX, LoginProblem, refusal
from l1_checks import verdict_single_context, verdict_supervise_verifier

STREAMS = Path(__file__).resolve().parent / "data" / "codex_streams"
WS = Path(tempfile.gettempdir()) / "devrun-check_report-fixture"  # never created
SKILL_ROOT = WS / ".agents" / "skills"
POSIX = pytest.mark.skipif(os.name != "posix", reason="POSIX signals and file locks")
LINUX = pytest.mark.skipif(not sys.platform.startswith("linux"), reason="prctl is Linux-only")
X8_NOTE = "Whether this logs out your other ChatGPT sessions is unverified (X8)"
CODEX_NOTE = "Your own Codex login is not affected"


def stream(name: str, ws: Path = WS) -> list[dict]:
    text = (STREAMS / f"{name}.jsonl").read_text(encoding="utf-8").replace("__WS__", str(ws))
    return [json.loads(line) for line in text.splitlines() if line.strip()]


def answer(name: str) -> dict:
    return json.loads((STREAMS / f"{name}.json").read_text(encoding="utf-8"))


def listing(name: str) -> str:
    return (STREAMS / f"features-{name}.txt").read_text(encoding="utf-8")


def wait_for(condition, timeout: float = 10.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if condition():
            return True
        time.sleep(0.02)
    return condition()


def lock_held(home: Path) -> bool:
    import fcntl

    with (home / host_login.LOCK_NAME).open("ab") as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
    return False


def fake_codex(tmp_path: Path, body: str) -> dict[str, str]:
    """A `codex` script on a PATH of its own; returns the environ to hand over."""
    bindir = tmp_path / "bin"
    bindir.mkdir(exist_ok=True)
    script = bindir / "codex"
    script.write_text(f"#!{sys.executable}\n" + textwrap.dedent(body), encoding="utf-8")
    script.chmod(0o755)
    return {"PATH": f"{bindir}{os.pathsep}{os.environ.get('PATH', '')}", "LANG": "C.UTF-8"}


# ---------- 2.3: the run lock and stopping a child ------------------------------------


@POSIX
def test_a_second_run_lock_waits_then_refuses(tmp_path, monkeypatch):
    """testing-harness spec: Serial Codex runs."""
    monkeypatch.setattr(host_login, "LOCK_WAIT_S", 0.3)
    with host_login.run_lock(tmp_path):
        started = time.monotonic()
        with pytest.raises(host_login.RunLockBusy) as busy, host_login.run_lock(tmp_path):
            pass
        assert time.monotonic() - started >= 0.3
    problem = busy.value.problem
    assert isinstance(problem, LoginProblem)
    assert problem.client == "codex"
    assert str(tmp_path / host_login.LOCK_NAME) in problem.cause
    message = refusal(problem)
    assert message.startswith("untested: another Codex run holds the harness home")
    assert message.endswith(f"{CODEX_NOTE}.")
    with host_login.run_lock(tmp_path):  # released once its holder is gone
        pass


HOLDS_UNTIL_RELEASED = """
import pathlib, sys, time
ready, release = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
ready.write_text("ready", encoding="utf-8")
while not release.exists():
    time.sleep(0.02)
"""


@POSIX
def test_a_child_holds_the_run_lock_after_the_harness_lets_go(tmp_path):
    """testing-harness spec: Lock outlives a killed harness — `flock` binds to the
    open file description, which the child shares through `pass_fds`."""
    ready, release = tmp_path / "ready", tmp_path / "release"
    argv = [sys.executable, "-c", HOLDS_UNTIL_RELEASED, str(ready), str(release)]
    done: dict = {}
    with host_login.run_lock(tmp_path) as fd:
        worker = threading.Thread(target=lambda: done.update(result=host_login.run_host(
            CODEX, argv, cwd=tmp_path, env=dict(os.environ), timeout=30, pass_fds=(fd,))))
        worker.start()
        assert wait_for(ready.exists)
    assert lock_held(tmp_path)  # the harness's descriptor is closed; the child's is not
    release.write_text("go", encoding="utf-8")
    worker.join(timeout=30)
    assert done["result"][0] == 0
    assert not lock_held(tmp_path)


TRAPS_SIGINT = """
import pathlib, signal, sys, time
def done(*_):
    pathlib.Path(sys.argv[1]).write_text("interrupted", encoding="utf-8")
    sys.exit(0)
signal.signal(signal.SIGINT, done)
pathlib.Path(sys.argv[2]).write_text("ready", encoding="utf-8")
time.sleep(60)
"""
IGNORES_SIGINT = """
import pathlib, signal, sys, time
signal.signal(signal.SIGINT, signal.SIG_IGN)
pathlib.Path(sys.argv[2]).write_text("ready", encoding="utf-8")
time.sleep(60)
"""


def started(tmp_path: Path, script: str) -> tuple[subprocess.Popen, Path]:
    marker, ready = tmp_path / "interrupted", tmp_path / "ready"
    proc = subprocess.Popen([sys.executable, "-c", script, str(marker), str(ready)])
    assert wait_for(ready.exists), "the child never installed its handler"
    return proc, marker


@POSIX
def test_a_codex_child_is_interrupted_and_never_killed(tmp_path, monkeypatch):
    """testing-harness spec: Codex interrupted before kill."""
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    proc, marker = started(tmp_path, TRAPS_SIGINT)
    assert host_login.stop_child(proc, CODEX.stop_signal) == 0
    assert marker.read_text(encoding="utf-8") == "interrupted"


@POSIX
def test_a_codex_child_that_ignores_the_interrupt_is_killed_after_the_grace(tmp_path,
                                                                           monkeypatch):
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 0.3)
    proc, marker = started(tmp_path, IGNORES_SIGINT)
    begun = time.monotonic()
    assert host_login.stop_child(proc, signal.SIGINT) == -signal.SIGKILL
    assert time.monotonic() - begun >= 0.3
    assert not marker.exists()


@POSIX
def test_run_host_interrupts_at_its_limit_and_reraises(tmp_path, monkeypatch):
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    marker, ready = tmp_path / "interrupted", tmp_path / "ready"
    argv = [sys.executable, "-c", TRAPS_SIGINT, str(marker), str(ready)]
    with pytest.raises(subprocess.TimeoutExpired):
        host_login.run_host(CODEX, argv, cwd=tmp_path, env=dict(os.environ), timeout=1.5)
    assert marker.read_text(encoding="utf-8") == "interrupted"


def test_stop_child_without_a_signal_still_terminates():
    class Recorder:
        def __init__(self):
            self.calls: list[str] = []

        def terminate(self):
            self.calls.append("terminate")

        def send_signal(self, sig):
            self.calls.append(f"signal {sig}")

        def wait(self, **_kwargs):
            return 0

    proc = Recorder()
    host_login.stop_child(proc)
    assert proc.calls == ["terminate"]
    assert CODEX.stop_signal == signal.SIGINT
    assert host_login.CLAUDE.stop_signal == signal.SIGTERM


READS_PDEATHSIG = """
import ctypes
libc = ctypes.CDLL(None, use_errno=True)
value = ctypes.c_int(0)
libc.prctl(2, ctypes.byref(value), 0, 0, 0)  # PR_GET_PDEATHSIG
print(value.value)
"""


@LINUX
def test_a_codex_child_gets_the_parent_death_signal(tmp_path):
    code, out, _ = host_login.run_host(CODEX, [sys.executable, "-c", READS_PDEATHSIG],
                                       cwd=tmp_path, env=dict(os.environ), timeout=30)
    assert code == 0
    assert out.strip() == str(int(signal.SIGINT))


def test_without_posix_file_locks_the_codex_runner_is_a_usage_error(monkeypatch, capsys):
    monkeypatch.setattr(host_login, "fcntl", None)

    def no_workspace(*_args, **_kwargs):
        raise AssertionError("staged before the usage error")

    monkeypatch.setattr(claude_runner.tempfile, "mkdtemp", no_workspace)
    with pytest.raises(SystemExit) as usage:
        claude_runner.main(["check_report", "--host", "codex", "--model", "gpt-fixture-a"])
    assert usage.value.code == claude_runner.EXIT_USAGE
    assert "POSIX file locks" in capsys.readouterr().err


# ---------- 2.4: the billing guard ------------------------------------------------------

LAUNCH = {
    "PATH": "/usr/bin", "HOME": "/fake/home", "LANG": "C.UTF-8",
    "CODEX_API_KEY": "placeholder-codex-key", "CODEX_ACCESS_TOKEN": "placeholder-token",
    "CODEX_HOME": "/fake/home/.codex", "OPENAI_API_KEY": "placeholder-openai-key",
    "OPENAI_BASE_URL": "https://gateway.invalid/v1", "OPENROUTER_API_KEY": "placeholder-or-key",
    "SOME_SERVICE_API_KEY": "placeholder-other", "CLAUDE_CODE_OAUTH_TOKEN": "placeholder-claude",
    "XDG_CONFIG_HOME": "/fake/home/.config",
}
XDG = ("XDG_CONFIG_HOME", "XDG_CACHE_HOME", "XDG_DATA_HOME", "XDG_STATE_HOME")


def test_the_codex_child_environment_is_the_allowlist_plus_the_scratch_home(tmp_path):
    """testing-harness spec: API keys in the launching environment."""
    home, scratch = tmp_path / "codex-home", tmp_path / "scratch"
    env = codex_cli.child_env(home, LAUNCH, scratch)
    assert env["CODEX_HOME"] == str(home)
    assert env["HOME"] == env["USERPROFILE"] == str(scratch)
    for name in XDG:
        assert env[name].startswith(str(scratch)), name
    assert "CLAUDE_CODE_OAUTH_TOKEN" not in env
    strip = [n for n in env if n.startswith(("CODEX_", "OPENAI_", "OPENROUTER_"))
             or n.endswith("_API_KEY")]
    assert strip == ["CODEX_HOME"]
    assert not set(LAUNCH.values()) - {"/usr/bin", "C.UTF-8"} & set(env.values())
    assert codex_cli.ignored_env(LAUNCH) == sorted([
        "CODEX_ACCESS_TOKEN", "CODEX_API_KEY", "CODEX_HOME", "OPENAI_API_KEY",
        "OPENAI_BASE_URL", "OPENROUTER_API_KEY", "SOME_SERVICE_API_KEY"])
    assert codex_cli.child_env(home, LAUNCH)["HOME"] == "/fake/home"  # probes: no scratch


@pytest.fixture
def popen_calls(monkeypatch):
    calls: list[dict] = []

    class Recorded:
        def __init__(self, argv, **kwargs):
            calls.append({"argv": argv, **kwargs})
            self.stdin = self.stdout = self.stderr = None
            self.returncode = 0

    monkeypatch.setattr(subprocess, "Popen", Recorded)
    return calls


@pytest.mark.parametrize("leak", ["CODEX_API_KEY", "CODEX_ACCESS_TOKEN", "CODEX_FOO"])
def test_a_leaking_builder_is_stopped_before_any_child_starts(leak, tmp_path, monkeypatch,
                                                             popen_calls):
    """testing-harness spec: Leaking builder stopped before the spawn; Only the
    Codex home variable is exempt."""
    real = host_login.allowlisted_env
    monkeypatch.setattr(host_login, "allowlisted_env", lambda record, config, environ=None: {
        **real(record, config, environ), leak: "placeholder-leaked-value"})
    with pytest.raises(codex_cli.BillingEnvError) as refused:
        codex_cli.spawn(["codex", "app-server"], home=tmp_path, cwd=tmp_path, environ=LAUNCH)
    assert leak in str(refused.value)
    assert "placeholder-leaked-value" not in str(refused.value)
    assert isinstance(refused.value, codex_cli.CodexRefused)
    assert popen_calls == []


def test_only_the_codex_home_reaches_the_child(tmp_path, popen_calls):
    codex_cli.spawn(["codex", "app-server"], home=tmp_path, cwd=tmp_path, environ=LAUNCH)
    [call] = popen_calls
    env = call["env"]
    assert env["CODEX_HOME"] == str(tmp_path)
    assert [n for n in env if n.startswith("CODEX_") or n.endswith("_API_KEY")
            or n.startswith(("OPENAI_", "OPENROUTER_"))] == ["CODEX_HOME"]
    assert set(codex_cli.CODEX_EXEMPT) == set(CODEX.child_vars(tmp_path)) == {"CODEX_HOME"}


def test_the_assertion_checks_the_final_environment(tmp_path, monkeypatch, popen_calls):
    real = codex_cli.run_env
    monkeypatch.setattr(codex_cli, "run_env", lambda env, scratch: {
        **real(env, scratch), "OPENAI_API_KEY": "placeholder-late"})
    with pytest.raises(codex_cli.BillingEnvError, match="OPENAI_API_KEY"):
        codex_cli.spawn(["codex", "exec"], home=tmp_path, cwd=tmp_path, environ=LAUNCH,
                        scratch=tmp_path / "scratch")
    with pytest.raises(codex_cli.BillingEnvError, match="OPENAI_API_KEY"):
        codex_cli.run(["codex", "exec"], home=tmp_path, cwd=tmp_path, timeout=5,
                      environ=LAUNCH, scratch=tmp_path / "scratch")
    assert popen_calls == []


@POSIX
def test_run_codex_refuses_a_leak_before_the_quota_read(tmp_path, monkeypatch, popen_calls):
    real = host_login.allowlisted_env
    monkeypatch.setattr(host_login, "allowlisted_env", lambda record, config, environ=None: {
        **real(record, config, environ), "CODEX_API_KEY": "placeholder"})
    with pytest.raises(codex_cli.BillingEnvError):
        codex_cli.run_codex(tmp_path, "request", model="gpt-fixture-a", effort=None,
                            timeout=5, home=tmp_path, scenario=claude_runner.SCENARIOS[
                                "check_report"], environ=LAUNCH)
    assert popen_calls == []


@pytest.mark.parametrize(("name", "fragments"), [
    ("quota-no-credits", ["unavailable", "credits"]),
    ("quota-credits", ["12.5", "empty the Codex credit balance"]),
    ("quota-free", ["free", "Plus or Pro"]),
    ("quota-92", ["5-hour", "92%", "resets"]),
    ("quota-reached", ["reached"]),
    ("quota-no-window", ["unavailable", "window"]),
    ("quota-error", ["unavailable", "synthetic upstream error"]),
])
def test_quota_problem_refuses_each_unsafe_answer(name, fragments):
    """testing-harness spec: Quota read unavailable; Credits state missing; Credit
    balance present; Plan outside the allowed set; Window near its limit."""
    problem = codex_cli.quota_problem(codex_cli.parse_quota(answer(name)))
    assert problem is not None
    assert problem.client == "codex"
    message = refusal(problem)
    for fragment in fragments:
        assert fragment.lower() in message.lower(), (fragment, message)  # remedies capitalize


def test_quota_ok_passes_and_no_answer_is_unavailable():
    quota = codex_cli.parse_quota(answer("quota-ok"))
    assert codex_cli.quota_problem(quota) is None
    assert quota.plan_type == "plus"
    assert quota.primary.used_percent == 12
    assert quota.primary.window_minutes == 300
    assert codex_cli.quota_problem(codex_cli.parse_quota(None)) is not None
    credits = codex_cli.quota_problem(codex_cli.parse_quota(answer("quota-credits")))
    assert credits.remedy.count("empty") == 1  # emptying the balance is the one remedy
    assert codex_cli.QUOTA_STOP_PERCENT == 90
    assert codex_cli.ALLOWED_PLANS == ("plus", "pro")


def test_the_quota_snapshot_holds_no_secret():
    """testing-harness spec: Quota snapshot holds no secret."""
    snapshot = codex_cli.parse_quota(answer("quota-ok")).snapshot()
    assert set(snapshot) == {"primary", "secondary", "plan_type"}
    assert set(snapshot["primary"]) == {"used_percent", "window_minutes", "resets_at"}


APP_SERVER = """
import json, os, pathlib, sys, time
here = pathlib.Path(__file__).parent
(here / "pid").write_text(str(os.getpid()), encoding="utf-8")
assert sys.argv[1:] == ["app-server"], sys.argv
seen = []
for line in sys.stdin:
    message = json.loads(line)
    seen.append(message)
    (here / "seen.json").write_text(json.dumps(seen), encoding="utf-8")
    if message.get("method") == "initialize":
        print(json.dumps({"id": message["id"], "result": {"userAgent": "fixture"}}), flush=True)
    if message.get("method") == "account/rateLimits/read":
        answer = here / "answer.json"
        if not answer.exists():
            time.sleep(60)
        print(json.dumps({"method": "account/rateLimits/updated", "params": {}}), flush=True)
        reply = json.loads(answer.read_text(encoding="utf-8"))
        reply["id"] = message["id"]
        print(json.dumps(reply), flush=True)
"""


@POSIX
def test_read_quota_speaks_the_handshake(tmp_path):
    environ = fake_codex(tmp_path, APP_SERVER)
    (tmp_path / "bin" / "answer.json").write_text(json.dumps(answer("quota-ok")),
                                                  encoding="utf-8")
    quota = codex_cli.read_quota(tmp_path, environ)
    assert codex_cli.quota_problem(quota) is None
    seen = json.loads((tmp_path / "bin" / "seen.json").read_text(encoding="utf-8"))
    assert [m.get("method") for m in seen] == ["initialize", "initialized",
                                               "account/rateLimits/read"]
    assert seen[0]["params"]["clientInfo"]["name"] == "thesis-proposal-dev-runner"
    assert seen[2]["id"] == 1


@POSIX
def test_a_quota_read_that_never_answers_is_unavailable_and_stopped(tmp_path, monkeypatch):
    monkeypatch.setattr(codex_cli, "QUOTA_TIMEOUT_S", 0.8)
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 2)
    environ = fake_codex(tmp_path, APP_SERVER)
    begun = time.monotonic()
    quota = codex_cli.read_quota(tmp_path, environ)
    assert time.monotonic() - begun < 10
    problem = codex_cli.quota_problem(quota)
    assert problem is not None
    assert "unavailable" in problem.cause
    pid = int((tmp_path / "bin" / "pid").read_text(encoding="utf-8"))
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)


def test_a_reader_that_cannot_start_is_unavailable(tmp_path):
    quota = codex_cli.read_quota(tmp_path, {"PATH": str(tmp_path / "empty")})
    assert "unavailable" in codex_cli.quota_problem(quota).cause


@pytest.mark.parametrize(("name", "fragments"), [
    ("provider-leak", ["openrouter", "0.160.0"]),
    ("no-rate-limits", ["plan use cannot be confirmed"]),
    ("credits-unreported", ["plan use cannot be confirmed", "credits"]),
    ("plan-free", ["free", "Plus or Pro"]),
    ("credits-drawn", ["credits", "4.2", "empty the Codex credit balance"]),
    ("limit-reached", ["reached", "primary"]),
    ("model-rerouted", ["gpt-fixture-a", "gpt-fixture-b"]),
])
def test_billing_problem_reads_the_session_record(name, fragments):
    """testing-harness spec: Provider leak; Plan use unconfirmed; Credits drawn
    during a run; Model rerouted."""
    problem = codex_cli.billing_problem(stream(name))
    assert problem is not None
    message = refusal(problem)
    for fragment in fragments:
        assert fragment.lower() in message.lower(), (fragment, message)  # remedies capitalize
    assert codex_cli.billing_problem(stream("success")) is None


def test_no_session_record_means_plan_use_cannot_be_confirmed():
    exec_only = [e for e in stream("success") if not e["type"].startswith("codex.")]
    assert "plan use cannot be confirmed" in codex_cli.billing_problem(exec_only).cause


@pytest.mark.parametrize("passed", [False, True], ids=["X8-open", "X8-passed"])
@pytest.mark.parametrize("name", ["refresh-reused", "restriction-logout"])
def test_a_login_failure_names_the_codex_login(name, passed, monkeypatch):
    """testing-harness spec: Refresh token reused; Logged out by the login restriction."""
    monkeypatch.setattr(host_login, "X8_PASSED", passed)
    problem = codex_cli.failure_reason(stream(name), 1, "")
    assert problem is not None
    assert problem.untested
    assert "uv run poe host-login codex" in problem.message
    assert problem.message.rstrip(".").endswith(CODEX_NOTE if passed else X8_NOTE)


def test_failure_reason_carries_codex_message_or_the_missing_turn():
    failed = codex_cli.failure_reason(stream("turn-failed"), 1, "")
    assert failed is not None
    assert not failed.untested
    assert "synthetic transport error" in failed.message
    missing = codex_cli.failure_reason(stream("no-turn-completed"), 0, "")
    assert missing is not None
    assert not missing.untested
    assert missing.message == "codex emitted no completed turn"
    crashed = codex_cli.failure_reason([], 2, "synthetic stderr tail")
    assert "synthetic stderr tail" in crashed.message
    assert codex_cli.failure_reason(stream("success"), 0, "") is None


# ---------- 2.5: the command, the readers and the canonical tool calls -------------------

NETWORK_SCENARIOS = {"import_messy", "supervise_feedback", "supervise_literature",
                     "supervise_scope", "ideate_scoped", "ideate_scoped_adjacent",
                     "ideate_scoped_partial"}


def test_the_command_template():
    scenario = claude_runner.SCENARIOS["check_report"]
    argv = codex_cli.command(scenario, WS, "gpt-fixture-a")
    assert argv[:2] == ["codex", "exec"]
    for flag in ("--json", "--strict-config", "--skip-git-repo-check"):
        assert flag in argv
    assert argv[argv.index("-C") + 1] == str(WS)
    assert argv[argv.index("-s") + 1] == "workspace-write"
    assert argv[argv.index("-m") + 1] == "gpt-fixture-a"
    assert argv[-1] == "-"  # the prompt on stdin
    disabled = [argv[i + 1] for i, a in enumerate(argv) if a == "--disable"]
    assert set(codex_cli.DISABLED_FEATURES) <= set(disabled)
    assert "multi_agent" in disabled
    for forbidden in ("--ephemeral", "--ignore-user-config",
                      "--dangerously-bypass-approvals-and-sandbox"):
        assert forbidden not in argv
    assert not [a for a in argv if "model_reasoning_effort" in a]
    assert not [a for a in argv if "network_access" in a]
    with_effort = codex_cli.command(scenario, WS, "gpt-fixture-a", effort="high")
    assert 'model_reasoning_effort="high"' in with_effort


@pytest.mark.parametrize("name", sorted(claude_runner.SCENARIOS))
def test_network_only_where_a_scenario_needs_it(name):
    """testing-harness spec: Network only where needed."""
    scenario = claude_runner.SCENARIOS[name]
    assert codex_cli.needs_network(scenario) is (name in NETWORK_SCENARIOS)
    if scenario.get("install"):
        return
    argv = codex_cli.command(scenario, WS, "gpt-fixture-a")
    granted = "sandbox_workspace_write.network_access=true" in argv
    assert granted is (name in NETWORK_SCENARIOS)
    assert argv[argv.index("-s") + 1] == "workspace-write"


def test_subagents_only_where_allowed():
    """testing-harness spec: Subagents only where allowed."""
    plain = codex_cli.command(claude_runner.SCENARIOS["check_report"], WS, "gpt-fixture-a")
    supervise = codex_cli.command(claude_runner.SCENARIOS["supervise_scope"], WS,
                                  "gpt-fixture-a")
    def disabled(argv):
        return [argv[i + 1] for i, a in enumerate(argv) if a == "--disable"]
    assert "multi_agent" in disabled(plain)
    assert "multi_agent" not in disabled(supervise)


def test_features_problem_refuses_a_feature_outside_the_allowlist():
    """testing-harness spec: Feature outside the allowlist."""
    assert codex_cli.features_problem(listing("ok"), codex_cli.ALLOWED_FEATURES) is None
    problem = codex_cli.features_problem(listing("extra-on"), codex_cli.ALLOWED_FEATURES)
    assert problem is not None
    assert "realtime_conversation" in problem.cause
    assert problem.client == "codex"
    assert "host-login" not in problem.remedy
    helpers = codex_cli.allowed_features(claude_runner.SCENARIOS["supervise_scope"])
    on = listing("ok").replace("multi_agent                    stable          false",
                               "multi_agent                    stable          true")
    assert codex_cli.features_problem(on, helpers) is None
    assert codex_cli.features_problem(on, codex_cli.ALLOWED_FEATURES) is not None
    assert codex_cli.features_problem("", codex_cli.ALLOWED_FEATURES) is not None


def test_codex_tool_calls_map_each_item_to_its_canonical_name():
    """design Decision 11, each row."""
    calls = codex_cli.codex_tool_calls(stream("skill-read"))
    assert [name for name, _ in calls] == ["Bash", "Skill", "Bash", "Skill", "Bash"]
    assert calls[1] == ("Skill", {"skill": "proposal-check"})
    assert calls[3] == ("Skill", {"skill": "proposal-write"})
    spawned = codex_cli.codex_tool_calls(stream("helper-spawn"))
    assert [name for name, _ in spawned] == ["Edit", "Agent", "collab:wait"]
    assert "verifier-brief" in spawned[1][1]["prompt"]
    assert codex_cli.codex_tool_calls(stream("mcp-call")) == [
        ("mcp__docs__publish", {"title": "synthetic"})]
    searched = codex_cli.codex_tool_calls([{"type": "item.completed", "item": {
        "id": "w", "type": "web_search", "query": "synthetic query"}}])
    assert searched == [("WebSearch", {"query": "synthetic query"})]


def test_the_canonical_calls_reach_the_shared_verdicts():
    """testing-harness spec: Skill read through the shell; Codex subagent spawn;
    Codex helper spawn counted."""
    assert routing.route_from_events(stream("skill-read")) == "proposal-check"
    calls = routing.tool_calls(stream("helper-spawn"))
    assert verdict_supervise_verifier(calls)[0]
    single, why = verdict_single_context([name for name, _ in calls], 0)
    assert not single
    assert "Agent" in why
    assert verdict_single_context([name for name, _ in calls], 1)[0]


def test_claude_streams_give_the_same_calls_as_before():
    claude = [json.loads(line) for line in (
        Path(__file__).resolve().parent / "data" / "routing_streams" / "helper-fanout.jsonl"
    ).read_text(encoding="utf-8").splitlines() if line.strip()]
    assert codex_cli.codex_tool_calls(claude) == []
    assert [name for name, _ in routing.tool_calls(claude)] == [
        name for event in claude if event.get("type") == "assistant"
        for block in event["message"]["content"] if block.get("type") == "tool_use"
        for name in [block["name"]]]


def args_for(model="gpt-fixture-a", effort=None) -> Namespace:
    return Namespace(scenario="check_report", model=model, effort=effort, host="codex")


def test_codex_read_reports_the_run_without_a_cost(monkeypatch):
    """testing-harness spec: Codex run reports no cost."""
    monkeypatch.setenv("OPENAI_API_KEY", "placeholder-not-a-key")
    view = codex_cli.codex_read(stream("success"), args_for())
    assert view.final_text == ("The check reports errors in broken-format.md "
                               "(synthetic final answer).")
    assert (view.model_requested, view.model, view.cli_version) == (
        "gpt-fixture-a", "unreported", "0.160.0")
    t = view.telemetry
    assert t["cost_usd"] is None
    assert (t["notional_usd"], t["notional_basis"]) == (None, "unpriced")
    assert (t["tokens_in"], t["tokens_cache_read"], t["tokens_out"]) == (8000, 16000, 1200)
    assert (t["tokens_reasoning"], t["tokens_cache_write"]) == (400, 2000)
    assert (t["num_turns"], t["duration_ms"]) == (1, 41000)
    assert t["effort_served"] == "medium"
    assert t["quota_before"]["primary"]["used_percent"] == 12.0
    assert t["quota_after"]["primary"]["used_percent"] == 14.0
    assert "OPENAI_API_KEY" in t["ignored_env"]
    assert "placeholder-not-a-key" not in json.dumps(t)
    rerouted = codex_cli.codex_read(stream("model-rerouted"), args_for())
    assert rerouted.model == "gpt-fixture-b"
    assert codex_cli.codex_read([], args_for()).final_text == ""


def test_a_roster_priced_name_gets_a_notional_figure():
    synthetic = REGISTRY_PATH.read_text(encoding="utf-8") + textwrap.dedent("""
        [[models]]
        id = "openrouter/openai/gpt-fixture-a"
        family = "openai"
        tier = "cheap"
        input_price = 1.0
        output_price = 8.0
        cache_read_price = 0.1
        enabled = false
        """)
    rates = claude_runner.codex_rates("gpt-fixture-a", synthetic)
    assert rates is not None
    view = codex_cli.codex_read(stream("success"), args_for(), rates)
    assert view.telemetry["notional_basis"] == "roster"
    assert view.telemetry["notional_usd"] == pytest.approx(
        (8000 * 1.0 + 16000 * 0.1 + 1200 * 8.0) / 1_000_000)
    assert claude_runner.codex_rates("gpt-fixture-b", synthetic) is None


@pytest.mark.parametrize(("name", "kind", "fragments"), [
    ("effort-dropped", "precondition", ["medium", "xhigh"]),
    ("foreign-skill", "isolation", ["/home/fixture-user/.agents/skills/grill-me/SKILL.md"]),
    ("cloud-skill-tool", "isolation", ["skills.load"]),
    ("mcp-call", "isolation", ["docs", "publish"]),
    ("provider-leak", "subscription", ["openrouter"]),
    ("refresh-reused", "subscription", ["uv run poe host-login codex"]),
])
def test_run_problem_marks_each_untested_kind(name, kind, fragments):
    """testing-harness spec: Effort not served; Foreign skill offered; MCP tool call in
    a Codex run; Codex precondition is untested, not a runner failure."""
    problem = codex_cli.run_problem(stream(name), skill_root=SKILL_ROOT, effort="xhigh")
    assert problem is not None
    assert problem.untested
    assert problem.kind == kind
    for fragment in fragments:
        assert fragment in problem.message
    assert codex_cli.run_problem(stream("success"), skill_root=SKILL_ROOT,
                                 effort="medium") is None
    assert codex_cli.run_problem(stream("success"), skill_root=SKILL_ROOT, effort=None) is None


def test_a_failed_turn_is_a_runner_failure():
    problem = codex_cli.run_problem(stream("turn-failed"), skill_root=SKILL_ROOT, effort=None)
    assert problem is not None
    assert not problem.untested


def test_capture_rollout_reduces_and_deletes_the_session_record(tmp_path):
    home = tmp_path / "codex-home"
    day = home / "sessions" / "2026" / "10" / "06"
    day.mkdir(parents=True)
    thread = "0199a0f0-0000-7000-8000-000000000001"
    (day / f"rollout-2026-10-06T10-00-00-{thread}.jsonl").write_text(
        (STREAMS / "rollout-success.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    records = codex_cli.capture_rollout(home, thread)
    assert [r["type"] for r in records] == [
        "codex.session", "codex.skills", "codex.turn_context", "codex.tool", "codex.error",
        "codex.token_count"]
    assert records[0] == {"type": "codex.session", "id": thread, "cli_version": "0.160.0",
                          "model_provider": "openai"}
    assert records[1]["files"] == [
        "/tmp/devrun-check_report-fixture/.agents/skills/proposal-check/SKILL.md"]
    assert records[3] == {"type": "codex.tool", "name": "skills.load"}
    text = json.dumps(records)
    assert "SYNTHETIC" not in text
    assert set(records[-1]) == {"type", "usage", "rate_limits"}
    snapshot = json.loads((home / "quota.json").read_text(encoding="utf-8"))
    assert set(snapshot) == {"primary", "secondary", "plan_type"}
    assert snapshot["primary"]["used_percent"] == 14.0
    assert not (home / "sessions").exists()


def test_capture_rollout_finds_the_record_by_its_session_id(tmp_path):
    home = tmp_path / "codex-home"
    day = home / "sessions" / "2026" / "10" / "06"
    day.mkdir(parents=True)
    (day / "rollout-renamed.jsonl").write_text(
        (STREAMS / "rollout-success.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    records = codex_cli.capture_rollout(home, "0199a0f0-0000-7000-8000-000000000001")
    assert records
    assert records[0]["type"] == "codex.session"


def test_without_a_session_record_plan_use_cannot_be_confirmed(tmp_path):
    home = tmp_path / "codex-home"
    home.mkdir()
    assert codex_cli.capture_rollout(home, "0199a0f0-missing") == []
    events = [e for e in stream("success") if not e["type"].startswith("codex.")]
    problem = codex_cli.run_problem(events, skill_root=SKILL_ROOT, effort=None)
    assert problem is not None
    assert problem.untested
    assert "plan use cannot be confirmed" in problem.message


FAKE_CODEX = """
import json, os, pathlib, sys
here = pathlib.Path(__file__).parent
verb = sys.argv[1]
if verb == "app-server":
    for line in sys.stdin:
        message = json.loads(line)
        if message.get("method") == "initialize":
            print(json.dumps({"id": message["id"], "result": {}}), flush=True)
        if message.get("method") == "account/rateLimits/read":
            reply = json.loads((here / "answer.json").read_text(encoding="utf-8"))
            reply["id"] = message["id"]
            print(json.dumps(reply), flush=True)
elif verb == "features":
    print((here / "features.txt").read_text(encoding="utf-8"), end="")
elif verb == "exec":
    prompt = sys.stdin.read()
    (here / "exec.json").write_text(json.dumps({
        "argv": sys.argv[1:], "prompt": prompt, "env": sorted(os.environ),
        "home": os.environ.get("HOME"), "codex_home": os.environ.get("CODEX_HOME")}),
        encoding="utf-8")
    day = pathlib.Path(os.environ["CODEX_HOME"]) / "sessions" / "2026" / "10" / "06"
    day.mkdir(parents=True, exist_ok=True)
    thread = "0199a0f0-0000-7000-8000-000000000001"
    (day / f"rollout-2026-10-06T10-00-00-{thread}.jsonl").write_text(
        (here / "rollout.jsonl").read_text(encoding="utf-8"), encoding="utf-8")
    for line in (here / "events.jsonl").read_text(encoding="utf-8").splitlines():
        print(line, flush=True)
"""


@POSIX
def test_run_codex_holds_the_lock_reads_the_quota_runs_and_captures(tmp_path):
    """The whole run against a fake `codex`: quota read, feature listing, the
    exec with its scratch HOME and the stripped environment, the capture."""
    environ = {**fake_codex(tmp_path, FAKE_CODEX), "CODEX_API_KEY": "placeholder-key",
               "HOME": str(tmp_path / "operator-home")}
    bindir = tmp_path / "bin"
    (bindir / "answer.json").write_text(json.dumps(answer("quota-ok")), encoding="utf-8")
    (bindir / "features.txt").write_text(listing("ok"), encoding="utf-8")
    home, ws = tmp_path / "codex-home", tmp_path / "ws"
    (bindir / "rollout.jsonl").write_text(
        (STREAMS / "rollout-success.jsonl").read_text(encoding="utf-8").replace(
            "/tmp/devrun-check_report-fixture", str(ws)), encoding="utf-8")
    exec_events = [e for e in stream("success") if not e["type"].startswith("codex.")]
    (bindir / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in exec_events),
                                         encoding="utf-8")
    host_login.seed(CODEX, home)
    ws.mkdir()
    events = codex_cli.run_codex(ws, "Please check broken-format.md.", model="gpt-fixture-a",
                                 effort=None, timeout=60, home=home,
                                 scenario=claude_runner.SCENARIOS["check_report"],
                                 environ=environ)
    seen = json.loads((bindir / "exec.json").read_text(encoding="utf-8"))
    assert seen["prompt"] == "Please check broken-format.md."
    assert seen["codex_home"] == str(home)
    assert seen["home"] not in (str(tmp_path / "operator-home"), None)
    assert "CODEX_API_KEY" not in seen["env"]
    assert seen["argv"][-1] == "-"
    kinds = [e["type"] for e in events]
    assert kinds[:len(exec_events)] == [e["type"] for e in exec_events]
    assert "codex.session" in kinds
    assert kinds[-1] == "codex.harness"
    harness = events[-1]
    assert harness["exit_code"] == 0
    assert harness["quota_before"]["plan_type"] == "plus"
    assert not (home / "sessions").exists()
    assert json.loads((home / "quota.json").read_text(encoding="utf-8"))["plan_type"] == "plus"
    problem = codex_cli.run_problem(events, skill_root=ws / ".agents" / "skills", effort=None)
    assert problem is not None  # the synthetic record's `skills.load` call
    assert problem.kind == "isolation"
    assert "skills.load" in problem.message
    assert str(ws) not in problem.message  # the workspace's own skill passes
    assert not lock_held(home)


@POSIX
@pytest.mark.parametrize(("answer_name", "features", "kind", "named"), [
    ("quota-free", "ok", "subscription", "free"),
    ("quota-ok", "extra-on", "precondition", "realtime_conversation"),
])
def test_run_codex_refuses_before_any_exec(answer_name, features, kind, named, tmp_path):
    environ = fake_codex(tmp_path, FAKE_CODEX)
    bindir = tmp_path / "bin"
    (bindir / "answer.json").write_text(json.dumps(answer(answer_name)), encoding="utf-8")
    (bindir / "features.txt").write_text(listing(features), encoding="utf-8")
    home = tmp_path / "codex-home"
    host_login.seed(CODEX, home)
    with pytest.raises(codex_cli.CodexRefused) as refused:
        codex_cli.run_codex(tmp_path, "request", model="gpt-fixture-a", effort=None, timeout=60,
                            home=home, scenario=claude_runner.SCENARIOS["check_report"],
                            environ=environ)
    assert refused.value.kind == kind
    assert named in refused.value.message
    assert not (bindir / "exec.json").exists()
