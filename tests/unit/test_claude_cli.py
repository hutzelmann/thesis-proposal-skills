"""L0: the dev runner's subscription text calls (testing-harness spec:
Subscription text roles (dev runner)).

Everything here runs without a model and without the `claude` binary: the pure
parts take plain values, and the async parts get a fake child process — except
the timeout test, which spawns a real sleeping Python child to prove it is
killed and reaped. Streams come from `data/claude_cli_streams/` (synthetic, one
fail-closed check per file) and the recorded-shape expired-login fixture under
`data/routing_streams/`.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import anyio
import claude_cli
import host_login
import pytest
from account_surfaces import PROFILE_DIR
from claude_cli import (
    Criterion,
    SubscriptionUnavailable,
    build_command,
    check_auth_status,
)
from host_login import CLAUDE, LOGIN_COMMAND, LoginSource, allowlisted_env
from l2_rubrics import read_grade

DATA = Path(__file__).resolve().parent / "data"
STREAMS = DATA / "claude_cli_streams"
MODEL = "claude-fixture-1-0"
SYSTEM = "You grade text against a rubric."
# the judge's configuration: only named to the child, never created
CONFIG = Path("judge-config")
# the login the remedies below name, unless a test says otherwise
SOURCE = LoginSource.OPERATOR


def parse_stream(events, requested, effort, source=SOURCE):
    return claude_cli.parse_stream(events, requested, effort, source)


def stream(name: str) -> list[dict]:
    path = STREAMS / f"{name}.jsonl"
    if name == "expired-login":
        path = DATA / "routing_streams" / "expired-login.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


def stream_text(name: str) -> str:
    return (STREAMS / f"{name}.jsonl").read_text(encoding="utf-8")


# ---------- build_command -----------------------------------------------------


def test_build_command_is_the_pinned_judge_invocation():
    assert build_command(MODEL, "medium", SYSTEM) == [
        "claude", "-p", "--model", MODEL, "--safe-mode", "--system-prompt", SYSTEM,
        "--tools", "", "--effort", "medium", "--output-format", "stream-json", "--verbose",
        "--no-session-persistence", "--max-turns", "1",
    ]


def test_build_command_takes_the_effort_from_its_argument():
    assert build_command(MODEL, "high", SYSTEM)[build_command(MODEL, "high", SYSTEM)
                                                .index("--effort") + 1] == "high"
    with pytest.raises(ValueError, match="effort"):
        build_command(MODEL, "turbo", SYSTEM)


def test_build_command_never_carries_the_minimal_mode_flag():
    """`--bare` never reads the subscription login (host 2.1.284)."""
    for effort in ("low", "medium", "high", "xhigh", "max"):
        assert "--bare" not in build_command(MODEL, effort, SYSTEM)


def test_call_sends_the_prompt_on_stdin_never_in_argv(monkeypatch):
    seen = {}

    async def fake_run_child(command, stdin_text, env, cwd, timeout):
        seen.update(command=command, stdin=stdin_text, env=env, cwd=cwd, timeout=timeout)
        return 0, stream_text("success"), ""

    monkeypatch.setattr(claude_cli, "run_child", fake_run_child)
    prompt = "GRADE THIS DRAFT: unique-prompt-marker-31"
    result = anyio.run(lambda: claude_cli.call(
        prompt, model=MODEL, effort="medium", system_prompt=SYSTEM, config=CONFIG,
        source=SOURCE, environ={"PATH": "/usr/bin"}))
    assert result.text.endswith("GRADE: C")
    assert seen["stdin"] == prompt
    assert not any("unique-prompt-marker-31" in arg for arg in seen["command"])
    assert seen["cwd"] == claude_cli.workdir()
    assert seen["env"] == allowlisted_env(CLAUDE, CONFIG, {"PATH": "/usr/bin"})


# ---------- the judge's environment (built by host_login.allowlisted_env, which
# test_isolated_env.py covers for every site) ------------------------------------

LAUNCHING_ENV = {
    "PATH": "/usr/bin", "HOME": "/home/x", "USER": "x", "LOGNAME": "x", "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8", "TMPDIR": "/tmp", "XDG_RUNTIME_DIR": "/run/user/1",
    "CLAUDE_CONFIG_DIR": "/home/x/.claude-ambient",
    "ANTHROPIC_API_KEY": "placeholder-not-a-key", "ANTHROPIC_AUTH_TOKEN": "placeholder",
    "ANTHROPIC_BASE_URL": "https://gateway.invalid", "ANTHROPIC_DEFAULT_SONNET_MODEL": "x",
    "OPENROUTER_API_KEY": "placeholder-not-a-key", "SEMANTIC_SCHOLAR_API_KEY": "placeholder",
    "CLAUDE_CODE_USE_BEDROCK": "1", "CLAUDE_CODE_USE_VERTEX": "1", "CLAUDE_EFFORT": "max",
    "CLAUDECODE": "1", "CLAUDE_CODE_ENTRYPOINT": "cli", "CLAUDE_CODE_SSE_PORT": "1234",
    "MAX_THINKING_TOKENS": "0", "PYTHONPATH": "/somewhere",
}
KEPT = ("PATH", "HOME", "USER", "LOGNAME", "LANG", "LC_ALL", "TMPDIR", "XDG_RUNTIME_DIR")


def judge_env(monkeypatch, launching: dict) -> dict:
    """The environment the judge's call hands its child."""
    seen = {}

    async def fake_run_child(_command, _stdin_text, env, _cwd, _timeout):
        seen["env"] = env
        return 0, stream_text("success"), ""

    monkeypatch.setattr(claude_cli, "run_child", fake_run_child)
    anyio.run(lambda: claude_cli.call("p", model=MODEL, effort="medium", system_prompt=SYSTEM,
                                      config=CONFIG, source=SOURCE, environ=launching))
    return seen["env"]


def test_the_judge_keeps_the_machine_and_drops_credentials_effort_and_session(monkeypatch):
    """testing-harness spec: Credentials and session settings never forwarded."""
    env = judge_env(monkeypatch, {**LAUNCHING_ENV,
                                  "CLAUDE_CODE_OAUTH_TOKEN": "placeholder-token",
                                  "ENABLE_CLAUDEAI_MCP_SERVERS": "true"})
    for name in KEPT:
        assert env[name] == LAUNCHING_ENV[name]
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "placeholder-token"
    assert env["CLAUDE_CONFIG_DIR"] == str(CONFIG)
    assert env["ANTHROPIC_CONFIG_DIR"] == str(CONFIG / PROFILE_DIR)
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    for name in LAUNCHING_ENV:
        if name.startswith(("ANTHROPIC_", "CLAUDE_CODE_", "MAX_THINKING")) or name.endswith(
                "_API_KEY") or name in ("CLAUDE_EFFORT", "CLAUDECODE", "PYTHONPATH"):
            assert LAUNCHING_ENV[name] != env.get(name), name


def test_the_judge_leaves_its_launching_environment_alone(monkeypatch):
    snapshot = dict(LAUNCHING_ENV)
    before = dict(os.environ)
    judge_env(monkeypatch, LAUNCHING_ENV)
    assert snapshot == LAUNCHING_ENV
    assert dict(os.environ) == before


# ---------- parse_stream ------------------------------------------------------


def test_success_stream_records_the_call():
    result = parse_stream(stream("success"), MODEL, "medium")
    assert result.text.endswith("GRADE: C")
    assert result.model == MODEL
    assert result.cli_version == "2.1.284"
    assert result.effort == "medium"
    assert result.thinking_tokens == 180
    assert result.notional_usd == pytest.approx(0.0551)
    assert result.rate_limit.status == "allowed"
    assert read_grade(result.text) is True


def test_warning_level_rate_limit_still_grades_and_reports_its_window():
    result = parse_stream(stream("allowed-warning"), MODEL, "medium")
    assert result.rate_limit.status == "allowed_warning"
    assert result.rate_limit.window == "seven_day"
    assert result.rate_limit.utilization == pytest.approx(0.82)


def test_auxiliary_model_without_output_passes():
    assert parse_stream(stream("auxiliary-model"), MODEL, "medium").model == MODEL


def test_no_grade_line_parses_but_reads_no_grade():
    result = parse_stream(stream("no-grade"), MODEL, "medium")
    assert read_grade(result.text) is None


@pytest.mark.parametrize(("name", "fragment"), [
    ("overage", "overage"),
    ("rejected", "'rejected'"),
    ("unknown-status", "'allowed_with_metering'"),
    ("zero-output", "zero output tokens"),
    ("empty-model-usage", "no per-model usage"),
    ("empty-result", "no text"),
    ("api-key-source", "'ANTHROPIC_API_KEY'"),
    ("foreign-provider", "'bedrock'"),
    ("no-result", "no result event"),
    ("no-rate-limit", "rate limit not reported, overage cannot be ruled out"),
    ("no-overage-flag", "without an overage flag, overage cannot be ruled out (Claude Code 2.1."),
    ("no-cost", "notional cost not reported, the cap cannot be enforced (Claude Code 2.1.284)"),
])
def test_fail_closed_streams_raise_unavailable(name, fragment):
    with pytest.raises(SubscriptionUnavailable) as exc:
        parse_stream(stream(name), MODEL, "medium")
    assert fragment in exc.value.reason


@pytest.mark.parametrize("cost", [None, "0.05", True])
def test_a_cost_that_is_not_a_number_fails_closed(cost):
    """`True` is an int to Python; a flag where the cost belongs is no cost."""
    events = stream("success")
    events[-1]["total_cost_usd"] = cost
    with pytest.raises(SubscriptionUnavailable, match="notional cost not reported"):
        parse_stream(events, MODEL, "medium")


def test_rate_refusal_reads_only_explicit_reports():
    """The errored-run classifier: overage or a refused status counts; a stream
    without a report, or with an allowed one, is no refusal."""
    assert "overage" in claude_cli.rate_refusal(stream("overage"))
    assert "'rejected'" in claude_cli.rate_refusal(stream("rejected"))
    for name in ("success", "allowed-warning", "no-rate-limit", "expired-login"):
        assert claude_cli.rate_refusal(stream(name)) is None, name


def test_mismatched_served_model_names_both_ids():
    with pytest.raises(SubscriptionUnavailable) as exc:
        parse_stream(stream("model-mismatch"), MODEL, "medium")
    assert "claude-fixture-2-0" in exc.value.reason
    assert MODEL in exc.value.reason


def test_unreported_rate_limit_names_the_cli_version_despite_the_grade_line():
    events = stream("no-rate-limit")
    assert "GRADE: C" in events[-1]["result"]
    with pytest.raises(SubscriptionUnavailable) as exc:
        parse_stream(events, MODEL, "medium")
    assert "2.1.284" in exc.value.reason


def test_expired_login_is_reported_with_the_relogin_instruction_first():
    """The expired-login stream also lacks a rate-limit event: check 1 runs
    first, so the reason is the host's own plus `/login`, never the overage one."""
    with pytest.raises(SubscriptionUnavailable) as exc:
        parse_stream(stream("expired-login"), MODEL, "medium")
    assert "OAuth session expired" in exc.value.reason
    assert "/login" in exc.value.reason
    assert "overage" not in exc.value.reason


@pytest.mark.parametrize(("source", "remedy"), [
    (LoginSource.HARNESS, LOGIN_COMMAND), (LoginSource.OPERATOR, "`/login`"),
    (LoginSource.TOKEN, "claude setup-token")])
def test_an_expired_login_names_the_remedy_for_the_login_in_use(source, remedy):
    """testing-harness spec: Expired login during judging."""
    with pytest.raises(SubscriptionUnavailable) as exc:
        parse_stream(stream("expired-login"), MODEL, "medium", source)
    assert remedy in exc.value.reason
    assert exc.value.billing is None


def test_a_billing_problem_is_marked_as_billing():
    with pytest.raises(SubscriptionUnavailable) as exc:
        parse_stream(stream("overage"), MODEL, "medium")
    assert "overage" in exc.value.billing


@pytest.mark.parametrize(("signal", "fragment"), [
    ({"type": "rate_limit_event", "rate_limit_info": {
        "status": "allowed", "isUsingOverage": True, "rateLimitType": "five_hour"}}, "overage"),
    ({"type": "system", "subtype": "init", "apiKeySource": "ANTHROPIC_API_KEY"},
     "'ANTHROPIC_API_KEY'"),
], ids=["overage", "api-key-source"])
def test_an_error_result_still_carries_its_billing_signal(signal, fragment):
    """A judge call the host ended with an error is untested on the error, but
    a billing signal beside it is named and carried as `billing`, so a judged
    smoke step stops the later ones — as the model-under-test run does."""
    init = {"type": "system", "subtype": "init", "apiKeySource": "none"}
    error = {"type": "result", "subtype": "error_during_execution", "is_error": True,
             "errors": ["synthetic failure"], "total_cost_usd": 0, "num_turns": 1}
    events = [signal, error] if signal["type"] == "system" else [init, signal, error]
    with pytest.raises(SubscriptionUnavailable) as exc:
        parse_stream(events, MODEL, "medium")
    assert "synthetic failure" in exc.value.reason
    assert fragment in exc.value.reason
    assert fragment in exc.value.billing


def test_billing_problem_reads_only_source_and_rate_limit():
    assert claude_cli.billing_problem(stream("success")) is None
    assert claude_cli.billing_problem(stream("model-mismatch")) is None
    assert "overage" in claude_cli.billing_problem(stream("overage"))
    assert "rate limit not reported" in claude_cli.billing_problem(stream("no-rate-limit"))


def test_billing_signals_read_nothing_from_a_stream_stopped_at_init():
    """A run stopped at its first event carries no rate-limit report; only an
    explicit reason may be named beside an account surface."""
    init = [e for e in stream("success") if e.get("subtype") == "init"]
    assert init
    assert claude_cli.billing_signals(init) == []
    assert claude_cli.billing_signals([]) == []


@pytest.mark.parametrize(("name", "fragment"), [
    ("api-key-source", "'ANTHROPIC_API_KEY'"),
    ("foreign-provider", "'bedrock'"),
    ("overage", "overage in use"),
    ("rejected", "'rejected'"),
])
def test_billing_signals_name_each_explicit_reason(name, fragment):
    [signal] = claude_cli.billing_signals(stream(name))
    assert fragment in signal


def test_billing_signals_read_a_partial_stream():
    """Overage reported before the run was stopped still counts."""
    partial = [e for e in stream("overage") if e.get("type") != "result"]
    assert any("overage" in s for s in claude_cli.billing_signals(partial))


# ---------- check_auth_status -------------------------------------------------

PRIVATE = {"email": "erika.musterfrau@example.org", "orgName": "Example Org", "orgId": "org-0000"}


def status(**fields):
    return {"loggedIn": True, "authMethod": "claude.ai", "apiProvider": "firstParty",
            **PRIVATE, **fields}


def test_subscription_login_passes():
    check_auth_status(status(), {}, SOURCE)


def test_long_lived_token_passes_only_when_exported():
    check_auth_status(status(authMethod="oauth_token"), {"CLAUDE_CODE_OAUTH_TOKEN": "x"},
                      LoginSource.TOKEN)
    with pytest.raises(SubscriptionUnavailable):
        check_auth_status(status(authMethod="oauth_token"), {}, SOURCE)


@pytest.mark.parametrize("bad", [
    {"authMethod": "api_key"}, {"loggedIn": False}, {"apiProvider": "bedrock"},
])
def test_other_logins_are_refused_with_the_relogin_instruction(bad):
    with pytest.raises(SubscriptionUnavailable) as exc:
        check_auth_status(status(**bad), {}, SOURCE)
    assert "/login" in exc.value.reason
    for value in PRIVATE.values():
        assert value not in exc.value.reason
    assert "API key" not in exc.value.reason.replace("never an API key", "")


@pytest.mark.parametrize("passed", [False, True])
@pytest.mark.parametrize(("source", "remedy"), [
    (LoginSource.HARNESS, LOGIN_COMMAND), (LoginSource.OPERATOR, "`/login`"),
    (LoginSource.TOKEN, "claude setup-token")])
def test_a_refused_login_names_the_remedy_for_the_login_in_use(source, remedy, passed,
                                                               monkeypatch):
    """testing-harness spec: API-key login refused — the remedy for the login in
    use; the harness login's closes with the login note."""
    monkeypatch.setattr(host_login, "L3_PASSED", passed)
    with pytest.raises(SubscriptionUnavailable) as exc:
        check_auth_status(status(loggedIn=False), {}, source)
    assert remedy in exc.value.reason
    if source is LoginSource.HARNESS:
        assert exc.value.reason.endswith(host_login.login_note(LOGIN_COMMAND))


def test_preflight_runs_auth_status_with_the_child_environment(monkeypatch, tmp_path):
    seen = {}

    async def fake_run_child(command, _stdin_text, env, _cwd, _timeout):
        seen.update(command=command, env=env)
        return 0, json.dumps(status()), ""

    monkeypatch.setattr(claude_cli, "run_child", fake_run_child)
    anyio.run(lambda: claude_cli.preflight(tmp_path, SOURCE, {**LAUNCHING_ENV}))
    assert seen["command"] == ["claude", "auth", "status", "--json"]
    assert seen["env"] == allowlisted_env(CLAUDE, tmp_path, LAUNCHING_ENV)
    assert "ANTHROPIC_API_KEY" not in seen["env"]
    assert seen["env"]["CLAUDE_CONFIG_DIR"] == str(tmp_path)
    assert seen["env"]["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert seen["env"]["ANTHROPIC_CONFIG_DIR"] == str(tmp_path / PROFILE_DIR)


def test_preflight_without_json_is_unavailable(monkeypatch, tmp_path):
    async def fake_run_child(*_args):
        return 1, "Not logged in", ""

    monkeypatch.setattr(claude_cli, "run_child", fake_run_child)
    with pytest.raises(SubscriptionUnavailable, match="/login"):
        anyio.run(lambda: claude_cli.preflight(tmp_path, SOURCE, {}))
    with pytest.raises(SubscriptionUnavailable, match=LOGIN_COMMAND):
        anyio.run(lambda: claude_cli.preflight(tmp_path, LoginSource.HARNESS, {}))


# ---------- concurrency, warm-up, notional bounds ------------------------------


class FakeHost:
    """A stand-in child process: records order and concurrency, answers with a
    stored stream after a short delay."""

    def __init__(self, text: str | None = None, delay: float = 0.02):
        self.text = text or stream_text("success")
        self.delay = delay
        self.log: list[tuple[str, int]] = []
        self.in_flight = 0
        self.peak = 0
        self.calls = 0

    async def __call__(self, *_child):
        number = self.calls
        self.calls += 1
        self.in_flight += 1
        self.peak = max(self.peak, self.in_flight)
        self.log.append(("start", number))
        await anyio.sleep(self.delay)
        self.in_flight -= 1
        self.log.append(("end", number))
        return 0, self.text, ""


async def no_preflight(*_args, **_kwargs):
    return None


def judge_all(criteria, **kwargs):
    options = {"model": MODEL, "effort": "medium", "system_prompt": SYSTEM, "config": CONFIG,
               "source": SOURCE, "cap": 5.0, "environ": {}, "notify": lambda _line: None,
               **kwargs}
    return anyio.run(lambda: claude_cli.judge_all(criteria, **options))


def criteria(n: int) -> list[Criterion]:
    return [Criterion(f"c{i}", f"prompt {i}") for i in range(n)]


def test_ten_direct_calls_never_exceed_four_children(monkeypatch):
    host = FakeHost()
    monkeypatch.setattr(claude_cli, "run_child", host)

    async def ten():
        async with anyio.create_task_group() as tg:
            for _ in range(10):
                tg.start_soon(lambda: claude_cli.call(
                    "p", model=MODEL, effort="medium", system_prompt=SYSTEM, config=CONFIG,
                    source=SOURCE, environ={}))

    anyio.run(ten)
    assert host.calls == 10
    assert host.peak == claude_cli.CONCURRENCY == 4


def test_judge_all_warms_up_alone_then_fans_out_at_most_four(monkeypatch):
    host = FakeHost()
    monkeypatch.setattr(claude_cli, "run_child", host)
    monkeypatch.setattr(claude_cli, "preflight", no_preflight)
    run = judge_all(criteria(10))
    assert [g.passed for g in run.grades] == [True] * 10
    assert host.log[:2] == [("start", 0), ("end", 0)], "the warm-up ran alone"
    assert 1 < host.peak <= 4
    assert run.spent == pytest.approx(10 * 0.0551)


def test_unavailable_call_stops_further_calls(monkeypatch):
    host = FakeHost(text=stream_text("overage"))
    monkeypatch.setattr(claude_cli, "run_child", host)
    monkeypatch.setattr(claude_cli, "preflight", no_preflight)
    run = judge_all(criteria(5))
    assert host.calls == 1
    assert all(g.passed is None for g in run.grades)
    assert "overage" in run.grades[0].reason
    assert "overage" in run.grades[4].reason
    assert "overage" in run.billing  # what stops a smoke sequence


def test_a_grade_carries_no_billing_reason(monkeypatch):
    monkeypatch.setattr(claude_cli, "run_child", FakeHost())
    monkeypatch.setattr(claude_cli, "preflight", no_preflight)
    assert judge_all(criteria(2)).billing is None


def test_missing_grade_line_is_untested_and_stops(monkeypatch):
    host = FakeHost(text=stream_text("no-grade"))
    monkeypatch.setattr(claude_cli, "run_child", host)
    monkeypatch.setattr(claude_cli, "preflight", no_preflight)
    run = judge_all(criteria(3))
    assert host.calls == 1
    assert run.grades[0].passed is None
    assert "GRADE" in run.grades[0].reason


def test_notional_cap_stops_issuing_calls(monkeypatch):
    host = FakeHost()
    monkeypatch.setattr(claude_cli, "run_child", host)
    monkeypatch.setattr(claude_cli, "preflight", no_preflight)
    run = judge_all(criteria(3), cap=0.05)
    assert host.calls == 1
    assert run.grades[0].passed is True
    assert [g.passed for g in run.grades[1:]] == [None, None]
    assert "notional cap $0.05" in run.grades[2].reason


def test_batch_projection_over_the_cap_stops_after_the_warm_up(monkeypatch):
    host = FakeHost()
    lines = []
    monkeypatch.setattr(claude_cli, "run_child", host)
    monkeypatch.setattr(claude_cli, "preflight", no_preflight)
    run = judge_all(criteria(10), cap=0.3, projection=True, notify=lines.append)
    assert host.calls == 1
    assert run.projection == pytest.approx(10 * 0.0551)
    assert any("projection" in line and "$0.30" in line for line in lines)
    assert all("projected" in g.reason for g in run.grades[1:])


def test_failed_preflight_makes_no_call(monkeypatch):
    host = FakeHost()

    async def refused(*_args, **_kwargs):
        raise SubscriptionUnavailable("logged in by 'api_key': run `claude` and enter `/login`")

    monkeypatch.setattr(claude_cli, "run_child", host)
    monkeypatch.setattr(claude_cli, "preflight", refused)
    run = judge_all(criteria(2))
    assert host.calls == 0
    assert all(g.passed is None and "/login" in g.reason for g in run.grades)


def test_no_criteria_makes_no_call_at_all(monkeypatch):
    monkeypatch.setattr(claude_cli, "preflight", lambda *_a, **_k: pytest.fail("preflight ran"))
    assert judge_all([]).grades == ()


# ---------- process handling -------------------------------------------------


def test_timeout_kills_and_reaps_the_child(tmp_path, monkeypatch):
    spawned = []
    real_open = anyio.open_process

    async def spy(*args, **kwargs):
        process = await real_open(*args, **kwargs)
        spawned.append(process)
        return process

    monkeypatch.setattr(claude_cli.anyio, "open_process", spy)
    sleeper = [sys.executable, "-c", "import time; time.sleep(60)"]
    with pytest.raises(SubscriptionUnavailable, match="timed out"):
        anyio.run(lambda: claude_cli.run_child(sleeper, "", dict(os.environ), tmp_path, 1.5))
    [process] = spawned
    assert process.returncode is not None, "the child was killed and waited for"
    if os.name == "posix":
        with pytest.raises(ProcessLookupError):
            os.kill(process.pid, 0)  # reaped: not even a zombie keeps the PID


TRAPS_SIGTERM = (
    "import pathlib, signal, sys, time\n"
    "def done(*_):\n"
    "    pathlib.Path(sys.argv[1]).write_text('terminated', encoding='utf-8')\n"
    "    sys.exit(0)\n"
    "signal.signal(signal.SIGTERM, done)\n"
    "pathlib.Path(sys.argv[2]).write_text('ready', encoding='utf-8')\n"
    "time.sleep(60)\n"
)


@pytest.mark.skipif(os.name != "posix", reason="SIGTERM handlers are POSIX")
def test_a_timed_out_child_is_asked_to_terminate_first(tmp_path, monkeypatch):
    """testing-harness spec: Time limit kills the child — a termination request
    first, so a host part-way through writing a refreshed login can finish."""
    monkeypatch.setattr(host_login, "TERM_GRACE_S", 5)
    marker, ready = tmp_path / "terminated", tmp_path / "ready"
    child = [sys.executable, "-c", TRAPS_SIGTERM, str(marker), str(ready)]
    with pytest.raises(SubscriptionUnavailable, match="timed out"):
        anyio.run(lambda: claude_cli.run_child(child, "", dict(os.environ), tmp_path, 1.5))
    assert ready.exists(), "the child installed its handler within the limit"
    assert marker.read_text(encoding="utf-8") == "terminated"


def test_run_child_writes_stdin_and_reads_both_streams(tmp_path):
    echo = [sys.executable, "-c",
            "import sys; data = sys.stdin.read(); print(data.upper()); "
            "print('note', file=sys.stderr); sys.exit(3)"]
    code, out, err = anyio.run(
        lambda: claude_cli.run_child(echo, "grade me", dict(os.environ), tmp_path, 30))
    assert (code, out.strip(), err.strip()) == (3, "GRADE ME", "note")


def test_nonzero_exit_without_a_result_reports_stderr(monkeypatch):
    async def failing(*_args):
        return 1, "", "Not logged in · Please run /login\n"

    monkeypatch.setattr(claude_cli, "run_child", failing)
    with pytest.raises(SubscriptionUnavailable) as exc:
        anyio.run(lambda: claude_cli.call(
            "p", model=MODEL, effort="medium", system_prompt=SYSTEM, config=CONFIG,
            source=SOURCE, environ={}))
    assert "Not logged in" in exc.value.reason
    assert "`/login`" in exc.value.reason


def test_working_directory_is_fixed_and_created_on_first_use(monkeypatch, tmp_path):
    assert Path(tempfile.gettempdir()) / "thesis-proposal-devjudge" == claude_cli.WORKDIR
    assert not claude_cli.WORKDIR.is_relative_to(tmp_path)
    fresh = tmp_path / "elsewhere" / "thesis-proposal-devjudge"
    monkeypatch.setattr(claude_cli, "WORKDIR", fresh)
    assert not fresh.exists()
    assert claude_cli.workdir() == fresh
    assert fresh.is_dir()
    assert list(fresh.iterdir()) == []
