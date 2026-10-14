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
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
from argparse import Namespace
from contextlib import ExitStack
from pathlib import Path

import claude_runner
import codex_cli
import host_login
import pytest
import routing
import workspace_guard
from helpers import PROC_FDS, REGISTRY_PATH, json_path, reusing_lstat, saved_stream
from host_login import CODEX, LoginProblem, refusal
from l1_checks import verdict_single_context, verdict_supervise_verifier

STREAMS = Path(__file__).resolve().parent / "data" / "codex_streams"
WS = Path(tempfile.gettempdir()) / "devrun-check_report-fixture"  # never created
SKILL_ROOT = WS / ".agents" / "skills"
# a user-scope skill directory outside the workspace, native on every platform; never created
HOME_ROOT = str(Path(tempfile.gettempdir()) / "devrun-home-fixture" / ".agents" / "skills")
GRILL = "grill-me/SKILL.md"
POSIX = pytest.mark.skipif(os.name != "posix" or host_login.fcntl is None,
                           reason="POSIX signals and file locks")
# a directory's mode keeps its owner out only when the owner is not root
ROOTLESS = pytest.mark.skipif(os.name != "posix" or host_login.fcntl is None
                              or os.geteuid() == 0, reason="POSIX modes, a non-root owner")
LINUX =pytest.mark.skipif(not sys.platform.startswith("linux"), reason="prctl is Linux-only")
X8_NOTE = "Whether this logs out your other ChatGPT sessions is unverified (X8)"
CODEX_NOTE = "Your own Codex login is not affected"


def stream(name: str, ws: Path = WS) -> list[dict]:
    return saved_stream(STREAMS / f"{name}.jsonl", ws, home_skills=HOME_ROOT)


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
    assert (problem.client, problem.kind) == ("codex", "precondition")
    assert str(tmp_path / host_login.LOCK_NAME) in problem.cause
    assert f"fuser -v {tmp_path / host_login.LOCK_NAME}" in problem.cause  # a lingering holder
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


def test_without_posix_file_locks_the_run_lock_refuses_cleanly(tmp_path, monkeypatch):
    monkeypatch.setattr(host_login, "fcntl", None)
    with pytest.raises(host_login.RunLockUnsupported) as refused, host_login.run_lock(tmp_path):
        pass
    assert isinstance(refused.value, host_login.RunLockRefused)
    assert refused.value.problem.kind == "precondition"
    assert refusal(refused.value.problem).startswith("untested: this platform lacks POSIX")
    assert not (tmp_path / host_login.LOCK_NAME).exists()


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


@pytest.mark.parametrize("value", ["/fake/home/.codex", None], ids=["inherited", "missing"])
def test_a_codex_home_other_than_the_harness_home_is_refused(value, tmp_path, monkeypatch,
                                                            popen_calls):
    """A builder that let an inherited CODEX_HOME win (or dropped it, so Codex
    would fall back to `~/.codex`) is stopped before any child starts; the
    variable is named, its value never."""
    real = host_login.allowlisted_env

    def leaking(record, config, environ=None):
        env = real(record, config, environ)
        if value is None:
            del env["CODEX_HOME"]
        else:
            env["CODEX_HOME"] = value
        return env

    monkeypatch.setattr(host_login, "allowlisted_env", leaking)
    with pytest.raises(codex_cli.BillingEnvError) as refused:
        codex_cli.spawn(["codex", "app-server"], home=tmp_path, cwd=tmp_path, environ=LAUNCH)
    message = str(refused.value)
    assert "does not set CODEX_HOME to the harness home" in message
    assert "/fake/home/.codex" not in message
    assert refused.value.kind == "subscription"
    with pytest.raises(codex_cli.BillingEnvError):
        codex_cli.run(["codex", "exec"], home=tmp_path, cwd=tmp_path, timeout=5, environ=LAUNCH)
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


CREDITS_EMPTY = {"hasCredits": False, "unlimited": False, "balance": "0"}


def with_credits(credits: object) -> dict:
    """`quota-ok.json` with its credits block replaced in both places."""
    data = answer("quota-ok")
    for limits in (data["result"]["rateLimits"], data["result"]["rateLimitsByLimitId"]["codex"]):
        limits["credits"] = credits
    return data


def with_record_credits(credits: object) -> list[dict]:
    """`success.jsonl` with the session record's credits block replaced."""
    events = stream("success")
    next(e for e in reversed(events) if e["type"] == "codex.token_count")[
        "rate_limits"]["credits"] = credits
    return events


@pytest.mark.parametrize(("credits", "named"), [
    ({}, "boolean"),
    ({"available": True, "amount": "25.00"}, "boolean"),
    ({"hasCredits": "false", "unlimited": False, "balance": "0"}, "boolean"),
    ({**CREDITS_EMPTY, "balance": "12,50"}, "not a number"),
    ({**CREDITS_EMPTY, "balance": "$12.50"}, "not a number"),
    ({**CREDITS_EMPTY, "balance": "12.50 USD"}, "not a number"),
    ({**CREDITS_EMPTY, "balance": "nan"}, "not a number"),
    ("none", "not an object"),
])
def test_an_unrecognised_credits_state_fails_closed_before_and_after_the_run(credits, named):
    """D2(a): a renamed field or a changed balance format never reads as "no
    credits" — before the run the read is unavailable, after it plan use
    cannot be confirmed."""
    before = codex_cli.quota_problem(codex_cli.parse_quota(with_credits(credits)))
    assert before is not None
    assert "unavailable" in before.cause
    assert named in before.cause
    after = codex_cli.billing_problem(with_record_credits(credits))
    assert after is not None
    assert "plan use cannot be confirmed" in after.cause
    assert named in after.cause


@pytest.mark.parametrize("credits", [
    CREDITS_EMPTY, {"hasCredits": False, "unlimited": False},
    {"has_credits": False, "unlimited": False, "balance": None}, {**CREDITS_EMPTY, "balance": 0},
])
def test_a_recognised_empty_credits_state_passes(credits):
    assert codex_cli.quota_problem(codex_cli.parse_quota(with_credits(credits))) is None
    assert codex_cli.billing_problem(with_record_credits(credits)) is None


@pytest.mark.parametrize(("window", "named"), [
    ({"windowDurationMins": 300, "resetsAt": 1791300000}, "5-hour window"),
    ({"usedPercent": "most", "windowDurationMins": 300}, "5-hour window"),
    ("full", "unnamed window"),
])
def test_a_window_without_a_used_percentage_is_unavailable(window, named):
    data = answer("quota-ok")
    data["result"]["rateLimitsByLimitId"]["codex"]["primary"] = window
    problem = codex_cli.quota_problem(codex_cli.parse_quota(data))
    assert problem is not None
    assert "unavailable" in problem.cause
    assert f"the {named} carries no used percentage" in problem.cause
    data = answer("quota-ok")
    data["result"]["rateLimitsByLimitId"]["codex"]["secondary"] = window
    assert "unavailable" in codex_cli.quota_problem(codex_cli.parse_quota(data)).cause


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


REFRESH = ("Your access token could not be refreshed because your refresh token {}. Please log "
           "out and sign in again.")


@pytest.mark.parametrize("passed", [False, True], ids=["X8-open", "X8-passed"])
@pytest.mark.parametrize("wording", ["has expired", "was revoked", "was already used"])
@pytest.mark.parametrize("kind", ["turn.failed", "error"])
def test_every_refresh_failure_wording_names_the_codex_login(kind, wording, passed,
                                                            monkeypatch):
    """testing-harness spec: Codex plan billing guard, Refresh failed — the
    already used, expired and revoked wordings (`manager.rs` @0.160)."""
    monkeypatch.setattr(host_login, "X8_PASSED", passed)
    message = REFRESH.format(wording)
    event = ({"type": kind, "error": {"message": message}} if kind == "turn.failed"
             else {"type": kind, "message": message})
    problem = codex_cli.failure_reason([{"type": "turn.started"}, event], 1, "")
    assert problem is not None
    assert (problem.untested, problem.kind, problem.billing) == (True, "subscription", None)
    assert wording in problem.message
    assert "uv run poe host-login codex" in problem.message
    assert problem.message.rstrip(".").endswith(CODEX_NOTE if passed else X8_NOTE)


@pytest.mark.parametrize("event", [
    {"type": "turn.failed", "error": {"message": "You've hit your usage limit (synthetic)."}},
    {"type": "error", "message": "synthetic: usage limit reached for the 5-hour window"},
    {"type": "item.completed", "item": {"id": "e", "type": "error",
                                        "message": "Synthetic: you hit your limit."}},
])
def test_a_usage_limit_error_is_untested_for_billing(event):
    """testing-harness spec: Codex plan billing guard, Limit reached — a
    usage-limit error makes the run untested, and `billing` carries it for the
    summary-log gate."""
    events = [*stream("success")[:2], event]
    problem = codex_cli.failure_reason(events, 1, "")
    assert problem is not None
    assert (problem.untested, problem.kind) == (True, "subscription")
    assert problem.billing is not None
    assert problem.billing.startswith("usage limit: ")
    assert "Rerun after the limit resets" in problem.message
    assert "host-login" not in problem.message
    through = codex_cli.run_problem([*events, {"type": "codex.harness", "exit_code": 1}],
                                    skill_root=SKILL_ROOT, effort=None)
    assert through == problem


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

# the handoff scenarios install every shipped skill (`all_but`), import,
# literature search and reverse among them, so each needs the network; derived
# from that install rather than listed, so a new handoff scenario needs no edit
FULL_INSTALL = {name for name, scenario in claude_runner.SCENARIOS.items()
                if scenario.get("siblings") == claude_runner.all_but(scenario.get("skill", ""))}
NETWORK_SCENARIOS = {"import_messy", "supervise_feedback", "supervise_literature",
                     "supervise_scope", "ideate_scoped", "ideate_scoped_adjacent",
                     "ideate_scoped_partial", "litsearch_snowball"} | FULL_INSTALL


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
    assert "code_mode_host" not in disabled  # the tool host (task 7.3 attempt 1)
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


@pytest.mark.parametrize("line", [
    "realtime_conversation          experimental    true (default)",  # annotated
    "realtime_conversation          true",  # no stage column
    "NAME                           STAGE           STATE",  # a header the parser lacks
])
def test_a_feature_line_the_parser_does_not_read_refuses(line):
    """Fail-closed on format drift: a listing where only enabled lines carry an
    annotation must not hide the enabled feature."""
    problem = codex_cli.features_problem(f"{listing('ok')}{line}\n", codex_cli.ALLOWED_FEATURES)
    assert problem is not None
    assert line.strip() in problem.cause
    assert problem.remedy == codex_cli.FEATURES_PARSER
    assert problem.kind == "precondition"
    assert codex_cli.features_problem(f"\n{listing('ok')}\n\n", codex_cli.ALLOWED_FEATURES) is None


def test_a_multi_word_stage_parses():
    """testing-harness spec: Multi-word feature stage (codex-cli 0.160 prints
    `under development`)."""
    rows, unparsed = codex_cli.parse_features(
        "agent_message_board                      under development  false\n"
        "multi_agent                              stable             true\n")
    assert unparsed == []
    assert rows == {"agent_message_board": ("under development", False),
                    "multi_agent": ("stable", True)}


def test_a_pinned_removed_feature_reading_true_passes(monkeypatch):
    """testing-harness spec: Removed feature reading enabled. `tui_app_server`
    passes because REMOVED_ENABLED pins it, not because of its stage: without
    the pin the same listing refuses."""
    line = "tui_app_server                           removed            true\n"
    assert "tui_app_server" in codex_cli.REMOVED_ENABLED
    assert codex_cli.features_problem(f"{listing('0160-ok')}{line}",
                                      codex_cli.ALLOWED_FEATURES) is None
    monkeypatch.setattr(codex_cli, "REMOVED_ENABLED",
                        codex_cli.REMOVED_ENABLED - {"tui_app_server"})
    problem = codex_cli.features_problem(f"{listing('0160-ok')}{line}",
                                         codex_cli.ALLOWED_FEATURES)
    assert problem is not None
    assert "tui_app_server" in problem.cause


@pytest.mark.parametrize("name", ["x7_fixture_feature", "apps"])
def test_an_unpinned_removed_feature_reading_true_refuses(name):
    """testing-harness spec: Removed feature reading enabled. A feature that
    graduates to `removed` while still on, a surface feature the run disables
    (`apps`) included, refuses and is named."""
    line = f"{name:<40} removed            true\n"
    problem = codex_cli.features_problem(f"{listing('0160-ok')}{line}",
                                         codex_cli.ALLOWED_FEATURES)
    assert problem is not None
    assert name in problem.cause
    assert problem.remedy != codex_cli.FEATURES_PARSER


def test_the_removed_pin_holds_no_disabled_or_allowed_feature():
    """A disabled feature reading true refuses at any stage, so the pin of
    removed features reading true never names one; nor does it shadow the
    allowlist or the subagent feature."""
    pinned = codex_cli.REMOVED_ENABLED
    assert not pinned & set(codex_cli.DISABLED_FEATURES)
    assert not pinned & set(codex_cli.ALLOWED_FEATURES)
    assert codex_cli.SUBAGENT_FEATURE not in pinned


def test_an_unknown_enabled_feature_at_another_stage_refuses():
    """testing-harness spec: Feature outside the allowlist, at each stage but `removed`."""
    for stage in ("under development", "experimental", "stable", "deprecated"):
        line = f"x7_fixture_feature                       {stage:<18} true\n"
        problem = codex_cli.features_problem(f"{listing('0160-ok')}{line}",
                                             codex_cli.ALLOWED_FEATURES)
        assert problem is not None
        assert "x7_fixture_feature" in problem.cause
        assert problem.remedy != codex_cli.FEATURES_PARSER


@pytest.mark.parametrize("line", [
    "x7_fixture_feature  under development  pending  false",  # five fields, junk stage
    "x7_fixture_feature  stable  stable  stable  true",  # five fields, repeated stage
    "x7_fixture_feature  beta  true",  # a stage 0.160 does not print
    "under development  true",  # a stage with no name
])
def test_a_garbage_feature_row_refuses(line):
    """testing-harness spec: Feature listing line the parser does not read. A
    row is a name, a known stage and a known state, nothing else."""
    problem = codex_cli.features_problem(f"{listing('0160-ok')}{line}\n",
                                         codex_cli.ALLOWED_FEATURES)
    assert problem is not None
    assert problem.remedy == codex_cli.FEATURES_PARSER
    assert line.strip() in problem.cause


def test_the_0160_listing_after_the_run_flags_passes():
    """The X7 listing (codex-cli 0.160.0, reduced) under the run's `--disable`
    flags: passes without helpers; with `multi_agent` enabled it passes only
    for a scenario that allows helpers."""
    plain = listing("0160-ok")
    rows, unparsed = codex_cli.parse_features(plain)
    assert unparsed == []
    assert rows["multi_agent"] == ("stable", False)
    assert {name for name, (_, on) in rows.items() if on} >= set(codex_cli.ALLOWED_FEATURES)
    assert not {name for name, (_, on) in rows.items() if on} & set(codex_cli.DISABLED_FEATURES)
    removed_on = {name for name, (stage, on) in rows.items()
                  if on and stage == codex_cli.REMOVED_STAGE}
    assert removed_on == codex_cli.REMOVED_ENABLED  # the pin is exactly what X7 measured
    check_report = claude_runner.SCENARIOS["check_report"]
    assert codex_cli.features_problem(plain, codex_cli.allowed_features(check_report)) is None
    helpers = plain.replace("multi_agent                              stable             false",
                            "multi_agent                              stable             true")
    assert helpers != plain
    supervise = claude_runner.SCENARIOS["supervise_scope"]
    assert codex_cli.features_problem(helpers, codex_cli.allowed_features(supervise)) is None
    refused = codex_cli.features_problem(helpers, codex_cli.allowed_features(check_report))
    assert refused is not None
    assert "multi_agent" in refused.cause


OTHER_CODE_MODE = ("code_mode", "code_mode_only", "code_mode_interrupt", "code_mode_prewarm")


def test_the_code_mode_host_is_allowed_and_nothing_else_of_code_mode():
    """Task 7.3 attempt 1 (2026-10-13): 0.160 serves the plan's models
    code-mode-only, so with `code_mode_host` disabled every tool call failed
    closed. The host moves to the allowlist; the code-mode features that are
    off by default stay outside it, so one reading enabled still refuses."""
    assert "code_mode_host" in codex_cli.ALLOWED_FEATURES
    assert "code_mode_host" not in codex_cli.DISABLED_FEATURES
    assert "code_mode_host" not in codex_cli.feature_flags(claude_runner.SCENARIOS["check_report"])
    plain = listing("0160-ok")
    rows, _ = codex_cli.parse_features(plain)
    assert rows["code_mode_host"] == ("stable", True)
    code_mode = {name: on for name, (_, on) in rows.items() if name.startswith("code_mode")}
    assert code_mode == {"code_mode_host": True, "code_mode_buffered_exec": False,
                         **dict.fromkeys(OTHER_CODE_MODE, False)}
    assert codex_cli.features_problem(plain, codex_cli.ALLOWED_FEATURES) is None
    for name in OTHER_CODE_MODE:
        assert name not in codex_cli.ALLOWED_FEATURES
        row = next(line for line in plain.splitlines() if line.split()[0] == name)
        problem = codex_cli.features_problem(plain.replace(row, row.replace("false", "true")),
                                             codex_cli.ALLOWED_FEATURES)
        assert problem is not None
        assert name in problem.cause


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
        "gpt-fixture-a", "gpt-fixture-a", "0.160.0")
    assert view.model_check is None
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
    assert rerouted.model_check == "served gpt-fixture-b, requested gpt-fixture-a"
    assert codex_cli.codex_read([], args_for()).final_text == ""


def test_the_served_model_and_effort_come_from_the_turn_context():
    """Task 7.3 attempt 1 (2026-10-13): the session record carried
    `turn_context` with the model and a null effort, and the summary read
    "unreported". The turn context fills both; "unreported" is left only
    where it names none, and a turn model other than the requested name is
    noted."""
    harness = {"type": "codex.harness", "duration_ms": 30022, "exit_code": 0}
    attempt = [{"type": "codex.turn_context", "model": "gpt-fixture-a", "effort": None},
               harness]
    view = codex_cli.codex_read(attempt, args_for())
    assert (view.model, view.model_check) == ("gpt-fixture-a", None)
    assert view.telemetry["effort_served"] == "unreported"
    assert view.telemetry["effort_requested"] is None
    bare = codex_cli.codex_read([harness], args_for())
    assert (bare.model, bare.model_check) == ("unreported", None)
    assert bare.telemetry["effort_served"] == "unreported"
    other = [{"type": "codex.turn_context", "model": "gpt-fixture-b", "effort": "high"}]
    view = codex_cli.codex_read(other, args_for(effort="high"))
    assert view.model == "gpt-fixture-b"
    assert view.model_check == "served gpt-fixture-b, requested gpt-fixture-a"
    assert view.telemetry["effort_served"] == "high"
    # the last turn context counts, as for the effort check
    later = [*attempt, {"type": "codex.turn_context", "model": "gpt-fixture-b", "effort": "low"}]
    assert codex_cli.served_model(later) == "gpt-fixture-b"
    assert codex_cli.codex_read(later, args_for()).telemetry["effort_served"] == "low"


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
    ("foreign-skill", "isolation", [f"{Path(HOME_ROOT, GRILL)} (r0/{GRILL})"]),
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


FAILED_TURN = {"type": "turn.failed", "error": {"message": "synthetic transport error"}}


@pytest.mark.parametrize(("name", "kind", "fragments"), [
    ("mcp-call", "isolation", ["mcp__docs__publish", "isolation did not hold"]),
    ("foreign-skill", "isolation", ["grill-me"]),
    ("credits-drawn", "subscription", ["not a plan result", "credits"]),
    ("provider-leak", "subscription", ["not a plan result", "openrouter"]),
])
def test_a_failed_run_with_a_billing_or_isolation_signal_is_untested(name, kind, fragments):
    """testing-harness spec: MCP tool call in a Codex run; Foreign skill
    offered — the failure is named, but the run is untested, not a runner
    failure."""
    problem = codex_cli.run_problem([*stream(name), FAILED_TURN], skill_root=SKILL_ROOT,
                                    effort=None)
    assert problem is not None
    assert (problem.untested, problem.kind) == (True, kind)
    assert problem.message.startswith("codex failed: synthetic transport error (")
    for fragment in fragments:
        assert fragment in problem.message
    assert (problem.billing is not None) is (kind == "subscription")


CHECK = "proposal-check/SKILL.md"
UP = "../../../etc/x/SKILL.md"


@pytest.mark.parametrize(("roots", "files", "outside", "unresolved"), [
    ({"r0": str(SKILL_ROOT)}, [f"r0/{CHECK}"], [], []),
    (None, [str(SKILL_ROOT / CHECK)], [], []),  # an absolute locator, a record without roots
    (None, [f"r0/{CHECK}"], [], [f"r0/{CHECK}"]),  # the kept record of task 7.3 attempt 1
    ({"r0": str(SKILL_ROOT)}, [f"r1/{CHECK}"], [], [f"r1/{CHECK}"]),  # an alias the table lacks
    ({"r0": ".agents/skills"}, [f"r0/{CHECK}"], [], [f"r0/{CHECK}"]),  # a relative root
    ({"r0": str(SKILL_ROOT)}, [CHECK], [], [CHECK]),  # a bare relative locator
    ({"r0": str(SKILL_ROOT)}, ["r0"], [], ["r0"]),  # an alias with nothing after it
    ({"r0": HOME_ROOT}, [f"r0/{GRILL}"],
     [f"{Path(HOME_ROOT, GRILL)} (r0/{GRILL})"], []),  # a root outside
    ({"r0": str(SKILL_ROOT)}, [f"r0/{UP}"], [f"{Path(SKILL_ROOT, UP)} (r0/{UP})"], []),
    (None, [str(Path(HOME_ROOT, GRILL))], [str(Path(HOME_ROOT, GRILL))], []),
], ids=["alias-inside", "absolute-inside", "attempt-1-no-table", "unknown-alias",
        "relative-root", "bare-relative", "alias-only", "root-outside", "traversal",
        "absolute-outside"])
def test_offered_skills_resolve_against_their_own_root_table(roots, files, outside, unresolved):
    """Task 7.3 attempt 1 (2026-10-13): codex-cli 0.160 offers skills as
    `rN/…` locators under a `### Skill roots` table. A locator resolves only
    through its own record's table to an absolute root; anything else is
    unresolved, and both an unresolved locator and one outside the
    workspace's skill directory make the run untested for isolation."""
    record = {"type": "codex.skills", "files": files, **({"roots": roots} if roots else {})}
    assert codex_cli.offered_skills([record], SKILL_ROOT) == (outside, unresolved)
    problem = codex_cli.isolation_problem([record], SKILL_ROOT)
    if not outside and not unresolved:
        assert problem is None
        return
    assert problem is not None
    assert (problem.untested, problem.kind) == (True, "isolation")
    for named in [*outside, *unresolved]:
        assert named in problem.message
    assert ("does not resolve" in problem.message) is bool(unresolved)
    assert (f"outside {SKILL_ROOT}" in problem.message) is bool(outside)


def developer_message(*texts: str) -> str:
    return json.dumps({"type": "response_item", "payload": {
        "type": "message", "role": "developer",
        "content": [{"type": "input_text", "text": text} for text in texts]}})


def test_the_skills_block_reduces_to_its_own_root_table():
    """The 0.160 rendering (`codex debug prompt-input`, read offline): the
    table and the locators of one message form one record; an alias another
    message defines, or one the table names twice, stays unresolved."""
    block = (f"### Skill roots\n- `r0` = `{HOME_ROOT}`\n- `r1` = `{SKILL_ROOT}`\n"
             f"### Available skills\n- proposal-check: Synthetic. (file: r1/{CHECK})\n"
             f"- grill-me: Synthetic. (file: r0/{GRILL})\n")
    [record] = codex_cli.reduce_rollout([developer_message("<skills_instructions>", block)])
    assert record == {"type": "codex.skills", "roots": {"r0": HOME_ROOT, "r1": str(SKILL_ROOT)},
                      "files": [f"r1/{CHECK}", f"r0/{GRILL}"]}
    assert codex_cli.offered_skills([record], SKILL_ROOT) == (
        [f"{Path(HOME_ROOT, GRILL)} (r0/{GRILL})"], [])
    table_only = f"### Skill roots\n- `r0` = `{SKILL_ROOT}`\n"
    update = f"## Skills update\n- proposal-check: Synthetic. (file: r0/{CHECK})\n"
    records = codex_cli.reduce_rollout([developer_message(table_only), developer_message(update)])
    assert records == [{"type": "codex.skills", "roots": {}, "files": [f"r0/{CHECK}"]}]
    assert codex_cli.offered_skills(records, SKILL_ROOT) == ([], [f"r0/{CHECK}"])
    twice = (f"### Skill roots\n- `r0` = `{SKILL_ROOT}`\n- `r0` = `{HOME_ROOT}`\n"
             f"### Available skills\n- proposal-check: Synthetic. (file: r0/{CHECK})\n")
    [ambiguous] = codex_cli.reduce_rollout([developer_message(twice)])
    assert ambiguous["roots"] == {}
    assert codex_cli.offered_skills([ambiguous], SKILL_ROOT) == ([], [f"r0/{CHECK}"])


@pytest.mark.parametrize(("problem", "kind"), [
    (host_login.check_codex_version((0, 133, 0)), "precondition"),
    (host_login.check_codex_version(None), "precondition"),
    (host_login.check_codex_login("api-key", WS / "codex-home"), "subscription"),
    (host_login.check_presence(WS / "missing-home", CODEX), "subscription"),  # never created
], ids=["old-cli", "no-cli", "api-key-login", "no-home"])
def test_a_preflight_refusal_carries_the_kind_its_check_set(problem, kind, monkeypatch):
    """design Decision 12: the kind is data on the `LoginProblem`, set where
    the check builds it, never read back out of the message."""
    monkeypatch.setattr(codex_cli, "preflight", lambda _environ=None: problem)
    with pytest.raises(codex_cli.CodexRefused) as refused:
        codex_cli.isolated_home(ExitStack(), Namespace())
    assert refused.value.kind == kind
    assert refused.value.message == refusal(problem)


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
    assert records[1] == {"type": "codex.skills",
                          "roots": {"r0": "/tmp/devrun-check_report-fixture/.agents/skills"},
                          "files": ["r0/proposal-check/SKILL.md"]}
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
import json, os, pathlib, sys, time
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
    # whether the harness handed this child the run lock's open file
    # description: one of its descriptors is the lock file itself
    lock = os.stat(pathlib.Path(os.environ["CODEX_HOME"]) / ".harness-run.lock")
    held = []
    for fd in range(3, 256):
        try:
            found = os.fstat(fd)
        except OSError:
            continue
        held.append((found.st_dev, found.st_ino) == (lock.st_dev, lock.st_ino))
    (here / "exec.json").write_text(json.dumps({
        "argv": sys.argv[1:], "prompt": prompt, "env": sorted(os.environ),
        "home": os.environ.get("HOME"), "codex_home": os.environ.get("CODEX_HOME"),
        "lock_inherited": any(held)}), encoding="utf-8")
    day = pathlib.Path(os.environ["CODEX_HOME"]) / "sessions" / "2026" / "10" / "06"
    day.mkdir(parents=True, exist_ok=True)
    thread = "0199a0f0-0000-7000-8000-000000000001"
    (day / f"rollout-2026-10-06T10-00-00-{thread}.jsonl").write_text(
        (here / "rollout.jsonl").read_text(encoding="utf-8")
        .replace("__WS__", json.dumps(os.getcwd())[1:-1]),
        encoding="utf-8")
    # what the sandboxed shell may leave in the workspace (design Decision 16)
    plant = here / "plant.json"
    for name, (kind, target) in (json.loads(plant.read_text(encoding="utf-8")).items()
                                 if plant.exists() else []):
        path = pathlib.Path(name)
        if kind == "dir":
            path.mkdir(exist_ok=True)
            continue
        path.unlink(missing_ok=True)
        if kind == "link":
            path.symlink_to(target)
        elif kind == "fifo":
            os.mkfifo(path)
        else:
            os.link(target, path)
    close = here / "close.json"  # directories the shell left write-and-search only
    for name in json.loads(close.read_text(encoding="utf-8")) if close.exists() else []:
        os.chmod(name, 0o300)
    if (here / "replace").exists():  # the workspace itself swapped for a link
        cwd = pathlib.Path.cwd()
        cwd.rename(cwd.with_name(cwd.name + "-moved"))
        cwd.symlink_to(here)
    if (here / "remake").exists():  # the workspace removed and made again under its name
        cwd = pathlib.Path.cwd()
        os.chdir(here)
        cwd.rmdir()
        cwd.mkdir()
    for line in (here / "events.jsonl").read_text(encoding="utf-8").splitlines():
        print(line, flush=True)
    if (here / "hang").exists():  # a run that outlives its time limit
        time.sleep(60)
"""


def fake_run(tmp_path: Path, *, cloud_tool: bool = True) -> tuple[dict, Path, Path, Path]:
    """A fake `codex` whose quota read answers Plus, whose feature listing
    passes and whose exec writes `rollout-success.jsonl` (without its
    cloud-skill call unless `cloud_tool`) and prints `success.jsonl`'s exec
    events. Returns (environ, bindir, home, ws)."""
    environ = {**fake_codex(tmp_path, FAKE_CODEX), "CODEX_API_KEY": "placeholder-key",
               "HOME": str(tmp_path / "operator-home")}
    bindir = tmp_path / "bin"
    (bindir / "answer.json").write_text(json.dumps(answer("quota-ok")), encoding="utf-8")
    (bindir / "features.txt").write_text(listing("ok"), encoding="utf-8")
    home, ws = tmp_path / "codex-home", tmp_path / "ws"
    rollout = [line for line in (STREAMS / "rollout-success.jsonl").read_text(
        encoding="utf-8").splitlines() if cloud_tool or '"namespace":"skills"' not in line]
    (bindir / "rollout.jsonl").write_text(
        "\n".join(rollout).replace("/tmp/devrun-check_report-fixture", json_path(ws)) + "\n",
        encoding="utf-8")
    exec_events = [e for e in stream("success") if not e["type"].startswith("codex.")]
    (bindir / "events.jsonl").write_text("".join(json.dumps(e) + "\n" for e in exec_events),
                                         encoding="utf-8")
    host_login.seed(CODEX, home)
    ws.mkdir()
    return environ, bindir, home, ws


@POSIX
def test_run_codex_holds_the_lock_reads_the_quota_runs_and_captures(tmp_path):
    """The whole run against a fake `codex`: quota read, feature listing, the
    exec with its scratch HOME, the stripped environment and the lock's
    descriptor, the capture."""
    environ, bindir, home, ws = fake_run(tmp_path)
    exec_events = [e for e in stream("success") if not e["type"].startswith("codex.")]
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
    assert seen["lock_inherited"] is True  # design Decision 7: the child holds the lock
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
@pytest.mark.parametrize("cloud_tool", [False, True], ids=["clean-record", "cloud-skill-call"])
def test_a_run_at_its_limit_is_interrupted_captured_and_named(cloud_tool, tmp_path,
                                                              monkeypatch):
    """testing-harness spec: Codex interrupted before kill — the run ends as a
    runner failure naming the limit, its session record captured and deleted
    first; a record that shows a broken isolation makes it untested instead."""
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    environ, bindir, home, ws = fake_run(tmp_path, cloud_tool=cloud_tool)
    (bindir / "hang").write_text("", encoding="utf-8")
    with pytest.raises(codex_cli.CodexRunFailed) as failed:
        codex_cli.run_codex(ws, "request", model="gpt-fixture-a", effort=None, timeout=2,
                            home=home, scenario=claude_runner.SCENARIOS["check_report"],
                            environ=environ)
    assert failed.value.message == "codex did not finish within 2s"
    kinds = [e["type"] for e in failed.value.events]
    assert kinds[0] == "thread.started"  # what the child wrote before the interrupt
    assert "codex.session" in kinds
    assert kinds[-1] == "codex.harness"
    assert failed.value.events[-1]["exit_code"] is None
    assert not (home / "sessions").exists()
    assert not lock_held(home)
    late = codex_cli.timeout_problem(failed.value, skill_root=ws / ".agents" / "skills")
    assert late.message.startswith("codex did not finish within 2s")
    assert (late.untested, late.kind) == ((True, "isolation") if cloud_tool else (False, None))
    assert ("skills.load" in late.message) is cloud_tool


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


# ---------- 5.5: the workspace after the run and the isolation stop (D-d) -----------------------


def test_the_stop_store_records_appends_reads_damage_and_clears(tmp_path):
    """Design Decision 16: one kind, isolation; a second cause is appended; a
    damaged record reads as a stop; clearing removes it and nothing else."""
    home = tmp_path / "codex-home"
    host_login.seed(CODEX, home)
    assert codex_cli.read_stop(home) is None
    codex_cli.record_stop(home, "first")
    codex_cli.record_stop(home, "second")
    stop = codex_cli.read_stop(home)
    assert (stop["kind"], stop["cause"]) == ("isolation", "first; second")
    before = sorted(p.name for p in home.iterdir())
    assert codex_cli.clear_stop(home)["cause"] == "first; second"
    assert codex_cli.read_stop(home) is None
    assert sorted(p.name for p in home.iterdir()) == sorted(set(before) - {"stop.json"})
    assert codex_cli.clear_stop(home) is None
    for damaged in ("not json", "[]", '{"stop": {}}', '{"other": 1}'):
        (home / "stop.json").write_text(damaged, encoding="utf-8")
        assert "cannot be read" in codex_cli.read_stop(home)["cause"]
    problem = codex_cli.stop_problem(codex_cli.read_stop(home))
    assert problem.kind == "isolation"
    assert "uv run poe host-login codex --clear-stop" in problem.remedy
    assert host_login.check_codex_home(home) is None  # the stop file keeps the home clean


def test_a_recorded_stop_refuses_before_any_codex_process(tmp_path, monkeypatch):
    """testing-harness spec: Recorded Codex stop refuses later runs — the
    preflight reads it right after the location, before `codex --version`."""
    monkeypatch.setenv(host_login.STATE_VAR, str(tmp_path / "state"))
    monkeypatch.setattr(host_login, "system_tempdir", lambda: str(tmp_path / "system-tmp"))
    home = host_login.home(CODEX)
    host_login.seed(CODEX, home)
    codex_cli.record_stop(home, "the workspace held entries the harness must not follow")

    def no_probe(*_args, **_kwargs):
        raise AssertionError("a Codex process started")

    monkeypatch.setattr(codex_cli, "probe", no_probe)
    problem = codex_cli.preflight()
    assert problem.kind == "isolation"
    assert "must not follow" in problem.cause
    with pytest.raises(codex_cli.CodexRefused) as refused:
        codex_cli.isolated_home(ExitStack(), Namespace())
    assert refused.value.kind == "isolation"


@POSIX
def test_a_stop_recorded_while_the_run_waited_refuses_it_under_the_lock(tmp_path, monkeypatch):
    environ, bindir, home, ws = fake_run(tmp_path)
    codex_cli.record_stop(home, "recorded by another run")

    def no_read(*_args, **_kwargs):
        raise AssertionError("the quota was read")

    monkeypatch.setattr(codex_cli, "read_quota", no_read)
    with pytest.raises(codex_cli.CodexRefused) as refused:
        codex_cli.run_codex(ws, "request", model="gpt-fixture-a", effort=None, timeout=60,
                            home=home, scenario=claude_runner.SCENARIOS["check_report"],
                            environ=environ)
    assert refused.value.kind == "isolation"
    assert "recorded by another run" in refused.value.message
    assert not (bindir / "exec.json").exists()


def plant(bindir: Path, entries: dict[str, list[str]]) -> None:
    (bindir / "plant.json").write_text(json.dumps(entries), encoding="utf-8")


@POSIX
def test_a_codex_run_that_plants_entries_is_untested_with_a_stop(tmp_path):
    """testing-harness spec: Codex workspace entry the runner must not follow
    — a link to a file outside, the event file's name as a link to another, a
    FIFO and a hard link: each removed unfollowed, the targets untouched, the
    run untested for isolation before any other finding, an isolation stop
    recorded."""
    environ, bindir, home, ws = fake_run(tmp_path, cloud_tool=False)
    secret, victim = tmp_path / "secret", tmp_path / "victim"
    secret.write_text("SYNTHETIC-SECRET-CONTENT", encoding="utf-8")
    victim.write_text("SYNTHETIC-VICTIM-CONTENT", encoding="utf-8")
    plant(bindir, {"broken-format.md": ["link", str(secret)],
                   claude_runner.EVENTS_FILE: ["link", str(victim)],
                   "pipe": ["fifo", ""], "hard": ["hard", str(secret)]})
    events = codex_cli.run_codex(ws, "request", model="gpt-fixture-a", effort=None, timeout=60,
                                 home=home, scenario=claude_runner.SCENARIOS["check_report"],
                                 environ=environ)
    planted = events[-1]["workspace_breach"]
    for named in ("broken-format.md (a link)", f"{claude_runner.EVENTS_FILE} (a link)",
                  "pipe (not a regular file)", "hard (a hard link)"):
        assert named in planted
    assert not any(p.is_symlink() for p in ws.rglob("*"))
    assert not (ws / "pipe").exists()
    assert not (ws / "hard").exists()
    assert secret.read_text(encoding="utf-8") == "SYNTHETIC-SECRET-CONTENT"
    assert victim.read_text(encoding="utf-8") == "SYNTHETIC-VICTIM-CONTENT"
    assert "SYNTHETIC" not in planted
    stop = codex_cli.read_stop(home)
    assert stop["kind"] == "isolation"
    assert "must not follow" in stop["cause"]
    problem = codex_cli.run_problem(events, skill_root=ws / ".agents" / "skills", effort=None)
    assert (problem.untested, problem.kind) == (True, "isolation")
    assert "no verdict read the run's files" in problem.message
    assert "--clear-stop" in problem.message
    assert not lock_held(home)


@POSIX
def test_a_codex_run_that_replaces_its_workspace_reads_nothing_in_it(tmp_path):
    environ, bindir, home, ws = fake_run(tmp_path, cloud_tool=False)
    (bindir / "replace").write_text("", encoding="utf-8")
    events = codex_cli.run_codex(ws, "request", model="gpt-fixture-a", effort=None, timeout=60,
                                 home=home, scenario=claude_runner.SCENARIOS["check_report"],
                                 environ=environ)
    assert events[-1]["workspace_breach"] == workspace_guard.WORKSPACE_REPLACED
    assert not ws.exists()  # the link in its place removed, never followed
    assert bindir.is_dir()
    assert (bindir / "events.jsonl").is_file()  # the link's target untouched
    assert codex_cli.read_stop(home)["cause"] == workspace_guard.WORKSPACE_REPLACED
    problem = codex_cli.run_problem(events, skill_root=ws / ".agents" / "skills", effort=None)
    assert problem.kind == "isolation"


@pytest.mark.skipif(not (PROC_FDS and host_login.fcntl),
                    reason="POSIX file locks, this process's descriptors (/proc/self/fd)")
def test_a_codex_run_that_makes_its_workspace_again_is_replaced_whatever_the_filesystem(
        tmp_path, monkeypatch):
    """The run holds the workspace's identity from before the child to the
    check (`workspace_guard.pinned`): a workspace the shell removes and makes
    again under its name is replaced even where the filesystem hands the
    removed inode number on (simulated, `reusing_lstat`; ext4 does)."""
    environ, bindir, home, ws = fake_run(tmp_path, cloud_tool=False)
    (bindir / "remake").write_text("", encoding="utf-8")
    monkeypatch.setattr(os, "lstat", reusing_lstat(ws, workspace_guard.workspace_identity(ws)))
    events = codex_cli.run_codex(ws, "request", model="gpt-fixture-a", effort=None, timeout=60,
                                 home=home, scenario=claude_runner.SCENARIOS["check_report"],
                                 environ=environ)
    assert events[-1]["workspace_breach"] == workspace_guard.WORKSPACE_REPLACED
    assert codex_cli.read_stop(home)["cause"] == workspace_guard.WORKSPACE_REPLACED


@POSIX
def test_a_codex_run_at_its_limit_is_still_checked_for_planted_entries(tmp_path, monkeypatch):
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    environ, bindir, home, ws = fake_run(tmp_path, cloud_tool=False)
    plant(bindir, {"broken-format.md": ["link", str(tmp_path / "secret")]})
    (bindir / "hang").write_text("", encoding="utf-8")
    with pytest.raises(codex_cli.CodexRunFailed) as failed:
        codex_cli.run_codex(ws, "request", model="gpt-fixture-a", effort=None, timeout=2,
                            home=home, scenario=claude_runner.SCENARIOS["check_report"],
                            environ=environ)
    assert "broken-format.md (a link)" in failed.value.events[-1]["workspace_breach"]
    late = codex_cli.timeout_problem(failed.value, skill_root=ws / ".agents" / "skills")
    assert (late.untested, late.kind) == (True, "isolation")
    assert codex_cli.read_stop(home)["kind"] == "isolation"


@ROOTLESS
@pytest.mark.parametrize(("where", "named"), [
    (".", "the workspace itself is a directory closed to its owner (mode 0300)"),
    ("sub", "sub (a directory closed to its owner (mode 0300))"),
], ids=["root", "sub"])
def test_a_codex_run_that_closes_a_workspace_directory_is_untested_with_a_stop(where, named,
                                                                             tmp_path):
    """testing-harness spec: Codex workspace directory the runner cannot list
    (Decision 16, revised 2026-10-07) — a link behind a directory the run
    left write-and-search only, at the top or below it: the check fails
    closed, the run is untested for isolation with a stop, the directory is
    never reopened and the link never followed."""
    environ, bindir, home, ws = fake_run(tmp_path, cloud_tool=False)
    secret = tmp_path / "secret"
    secret.write_text("SYNTHETIC-SECRET-CONTENT", encoding="utf-8")
    link = "broken-format.md" if where == "." else "sub/broken-format.md"
    plant(bindir, {"sub": ["dir", ""], link: ["link", str(secret)]})
    (bindir / "close.json").write_text(json.dumps([where]), encoding="utf-8")
    closed = ws if where == "." else ws / "sub"
    try:
        events = codex_cli.run_codex(ws, "request", model="gpt-fixture-a", effort=None,
                                     timeout=60, home=home,
                                     scenario=claude_runner.SCENARIOS["check_report"],
                                     environ=environ)
        assert named in events[-1]["workspace_breach"]
        assert closed.stat().st_mode & 0o777 == 0o300  # never reopened
        problem = codex_cli.run_problem(events, skill_root=ws / ".agents" / "skills",
                                        effort=None)
        assert (problem.untested, problem.kind) == (True, "isolation")
        assert "closed to its owner" in codex_cli.read_stop(home)["cause"]
        assert "SYNTHETIC" not in events[-1]["workspace_breach"]
    finally:
        closed.chmod(0o700)
    assert (ws / link).is_symlink()  # behind the closed directory: left, unread
    assert secret.read_text(encoding="utf-8") == "SYNTHETIC-SECRET-CONTENT"


def test_a_clean_workspace_is_no_finding():
    events = [*stream("success"), {"type": "codex.harness", "exit_code": 0,
                                    "workspace_breach": None}]
    assert codex_cli.planted_problem(events) is None


@POSIX
def test_a_planted_codex_run_end_to_end_saves_events_afresh_and_records_a_stop(
        tmp_path, monkeypatch, capsys):
    """Through the runner: untested (exit 3), no verdict, the event file
    created afresh beside the removed link, the victim unchanged, the secret
    in no output, and the next run refused by the stop."""
    environ, bindir, _home, _ws = fake_run(tmp_path, cloud_tool=False)
    monkeypatch.setenv("PATH", environ["PATH"])
    monkeypatch.setenv(host_login.STATE_VAR, str(tmp_path / "state"))
    monkeypatch.setattr(host_login, "system_tempdir", lambda: str(tmp_path / "system-tmp"))
    home = host_login.home(CODEX)
    host_login.seed(CODEX, home)
    monkeypatch.setattr(codex_cli, "preflight", lambda _environ=None: None)
    (bindir / "rollout.jsonl").write_text("", encoding="utf-8")
    secret, victim = tmp_path / "secret", tmp_path / "victim"
    secret.write_text("SYNTHETIC-SECRET-CONTENT", encoding="utf-8")
    victim.write_text("SYNTHETIC-VICTIM-CONTENT", encoding="utf-8")
    plant(bindir, {"broken-format.md": ["link", str(secret)],
                   claude_runner.EVENTS_FILE: ["link", str(victim)]})

    def no_verdict(*_args, **_kwargs):
        raise AssertionError("a verdict read the run's files")

    monkeypatch.setattr(claude_runner, "verdict", no_verdict)
    log = tmp_path / "run.jsonl"
    argv = ["check_report", "--host", "codex", "--model", "gpt-fixture-a", "--keep",
            "--summary-log", str(log)]
    status = claude_runner.main(argv)
    out, err = capsys.readouterr()
    ws = Path(next(line.split(": ", 1)[1] for line in out.splitlines()
                   if line.startswith("workspace kept: ")))
    try:
        assert status == claude_runner.EXIT_UNTESTED
        [line] = [json.loads(text) for text in log.read_text(encoding="utf-8").splitlines()]
        assert "must not follow" in line["why"]
        assert victim.read_text(encoding="utf-8") == "SYNTHETIC-VICTIM-CONTENT"
        assert "SYNTHETIC-SECRET-CONTENT" not in out + err + log.read_text(encoding="utf-8")
        events_file = ws / claude_runner.EVENTS_FILE
        assert events_file.is_file()
        assert not events_file.is_symlink()
        assert codex_cli.read_stop(home)["kind"] == "isolation"
        # the next run is refused by the stop: read again under the run lock
        # (the preflight is stubbed here), before any Codex exec
        (bindir / "exec.json").unlink()
        assert claude_runner.main([*argv[:-3], "--summary-log", str(log)]) == (
            claude_runner.EXIT_UNTESTED)
        capsys.readouterr()
        second = json.loads(log.read_text(encoding="utf-8").splitlines()[-1])
        assert "an isolation stop is recorded in the Codex harness home" in second["why"]
        assert "--clear-stop" in second["why"]
        assert not (bindir / "exec.json").exists()
    finally:
        shutil.rmtree(ws, ignore_errors=True)
