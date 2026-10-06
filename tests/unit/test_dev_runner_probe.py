"""L0: the dev runner's cost and helper-agent probe (testing-harness spec:
Dev-runner cost and helper-agent telemetry).

The probe reads the host's stream-json events. Three sources under
`data/routing_streams/`: the synthetic `helper-fanout.jsonl` pins the failing
case, the reduced recording `recorded-result.jsonl` pins the host's result-event
shape — a field rename fails here instead of blanking the telemetry line — and
the failure paths are fed synthetic events, since no recorded run hit them. The
account-surface checks read the reduced recording `claudeai-surfaces.jsonl` and
the synthetic `clean-init.jsonl` and `ambient-user-mcp.jsonl`. The host is
replaced at its stream reader (`follow_stream`), so the check script's own
subprocess still runs.
"""

import argparse
import json
import shutil
import tomllib
from contextlib import ExitStack, contextmanager
from pathlib import Path

import claude_cli
import claude_runner
import pytest
from account_surfaces import PROFILE_DIR
from claude_cli import JudgeCall, RateLimit
from claude_runner import (
    DRAFT_SCENARIOS,
    EVENTS_FILE,
    EXIT_FAIL,
    EXIT_PASS,
    EXIT_RUNNER,
    EXIT_UNTESTED,
    EXIT_USAGE,
    JUDGE_LABEL,
    NO_LINE,
    SCENARIOS,
    SKILLS,
    aggregate_status,
    exit_status,
    final_text,
    host_command,
    main,
    model_env,
    normalized_proposal,
    parse_events,
    save_events,
    summary,
    summary_rows,
    supervise_extra,
    supervise_verdict,
    telemetry,
    verdict,
)
from helpers import CLEAN_DRAFT, FIXTURES, REPO, followed, shipped_registry
from host_login import CLAUDE, LOGIN_COMMAND, LoginSource, allowlisted_env, login_note
from l1_checks import HELPER_TOOLS, load_closing_note, verdict_l2_grades, verdict_single_context
from routing import DISALLOWED_TOOLS, OUTWARD_TOOLS, tool_calls

STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"
ARGS = argparse.Namespace(scenario="check_report", model="haiku", no_skill=False)


def host_failure(events: list[dict], returncode: int, stderr: str,
                 source: LoginSource = LoginSource.AMBIENT) -> str | None:
    """The runner's own, for an ambient run unless a test names the login."""
    return claude_runner.host_failure(events, returncode, stderr, source)


def events(name: str) -> list[dict]:
    lines = (STREAMS / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def names(name: str) -> list[str]:
    return [tool for tool, _ in tool_calls(events(name))]


# ---------- verdict ----------------------------------------------------------


def test_helper_tools_cover_every_spawning_name():
    """A host rename of the spawning tool would otherwise pass silently."""
    assert set(HELPER_TOOLS) == {"Agent", "Task", "Workflow"}


def test_single_context_passes_without_helpers():
    passed, why = verdict_single_context(["Read", "Bash", "Skill"])
    assert passed
    assert "no helper" in why


def test_single_context_fails_naming_each_spawn():
    passed, why = verdict_single_context(["Read", "Task", "Workflow", "Task"])
    assert not passed
    assert "3 helper-agent call(s)" in why
    assert "Task" in why
    assert "Workflow" in why


def test_single_context_allowance_admits_the_supervise_verifier():
    """supervise allows one fresh verifier of the finished feedback; a second
    helper is the fan-out again (skill-supervise spec: single-context execution)."""
    passed, why = verdict_single_context(["Read", "Agent", "Write"], allowed=1)
    assert passed
    assert "within the allowance of 1" in why
    passed, why = verdict_single_context(["Agent", "Read", "Agent"], allowed=1)
    assert not passed
    assert "2 helper-agent call(s), 1 allowed" in why
    assert "Agent" in why


def test_recorded_exploration_spawned_nothing():
    assert verdict_single_context(names("unrouted-explore"))[0]


def test_synthetic_fanout_is_detected():
    assert names("helper-fanout") == ["Task", "Read"]
    passed, why = verdict_single_context(names("helper-fanout"))
    assert not passed
    assert "Task" in why


# ---------- stream readers ---------------------------------------------------


def test_parse_events_skips_non_json_lines():
    stdout = '{"type":"system"}\nnot json\n\n{"type":"result","result":"done"}\n'
    assert [e["type"] for e in parse_events(stdout)] == ["system", "result"]


def test_final_text_is_the_result_events_text_and_nothing_else():
    assert final_text(events("helper-fanout")) == "Reviewed; findings written."
    assert final_text(events("unrouted-explore")) == ""


def test_telemetry_reads_the_result_event():
    assert telemetry(events("helper-fanout")) == {
        "cost_usd": 0.42, "num_turns": 7, "duration_ms": 61000,
        "tokens_in": 1200, "tokens_out": 350,
        "tokens_cache_read": 9000, "tokens_cache_write": 300,
    }


def test_telemetry_pinned_against_the_recorded_result_event():
    """The host's own shape (2.1.207 routing run, reduced): a renamed field
    fails here rather than printing None."""
    assert telemetry(events("recorded-result")) == {
        "cost_usd": 0.15239159999999996, "num_turns": 8, "duration_ms": 16575,
        "tokens_in": 8, "tokens_out": 1126,
        "tokens_cache_read": 116892, "tokens_cache_write": 16636,
    }
    assert final_text(events("recorded-result")).startswith("I found three")


def test_telemetry_is_none_without_a_result_event():
    assert telemetry(events("unrouted-explore")) == {
        "cost_usd": None, "num_turns": None, "duration_ms": None,
        "tokens_in": None, "tokens_out": None,
        "tokens_cache_read": None, "tokens_cache_write": None,
    }


# ---------- command and failure paths ---------------------------------------


def test_host_command_pins_the_stream_flags_and_the_budget_pass_through():
    plain = host_command("do it", "sonnet")
    assert plain[:3] == ["claude", "-p", "do it"]
    assert plain[plain.index("--output-format") + 1] == "stream-json"
    assert "--verbose" in plain
    assert "--max-budget-usd" not in plain
    assert host_command("do it", "sonnet", budget=2)[-2:] == ["--max-budget-usd", "2"]


def test_host_command_denies_every_outward_tool_and_keeps_the_ones_runs_need():
    """Permission prompts are skipped, so the command itself must deny the host's
    publishing, messaging and scheduling tools (haiku published artifacts in a
    2026-10-03 run); the supervise verifier and the lookups must stay usable."""
    command = host_command("do it", "sonnet")
    denied = command[command.index("--disallowed-tools") + 1:]
    for tool in OUTWARD_TOOLS:
        assert tool in denied, tool
    for needed in ("Agent", "Task", "WebFetch", "WebSearch", "Skill"):
        assert needed not in denied, needed
    # the variadic list must not swallow the budget flag that follows it
    budgeted = host_command("do it", "sonnet", budget=2)
    assert budgeted[-2:] == ["--max-budget-usd", "2"]
    assert "Artifact" in OUTWARD_TOOLS


def test_routing_rig_denies_the_same_outward_tools():
    assert set(OUTWARD_TOOLS) <= set(DISALLOWED_TOOLS)


def test_host_failure_reports_an_error_result_with_its_detail():
    stream = [{
        "type": "result", "subtype": "error_max_budget_usd", "is_error": True,
        "errors": ["Exceeded USD budget"], "total_cost_usd": 0.31, "num_turns": 4,
    }]
    message = host_failure(stream, 1, "")
    assert message.startswith("claude failed: error_max_budget_usd: Exceeded USD budget")
    assert "0.31 USD" in message
    assert "4 turns" in message


def test_host_failure_reads_the_result_text_when_errors_are_empty():
    """Recorded 2026-10-03: an expired host login ends as subtype "success",
    is_error true, errors null, the reason in `result` — the message must carry
    it rather than "no detail"."""
    stream = [{
        "type": "result", "subtype": "success", "is_error": True, "errors": None,
        "result": "Failed to authenticate: OAuth session expired and could not be refreshed",
        "terminal_reason": "api_error", "total_cost_usd": 0, "num_turns": 1,
    }]
    message = host_failure(stream, 0, "")
    assert "api_error" in message
    assert "OAuth session expired" in message
    assert "no detail" not in message


def test_host_failure_tells_the_operator_to_log_in_again():
    """The stored login cannot be repaired from inside a run; the only remedy
    is an interactive login, so the message has to say which one."""
    stream = [{
        "type": "result", "subtype": "success", "is_error": True, "errors": None,
        "result": "Failed to authenticate: OAuth session expired and could not be refreshed",
        "terminal_reason": "api_error", "total_cost_usd": 0, "num_turns": 1,
    }]
    message = host_failure(stream, 0, "")
    assert "`claude`" in message
    assert "`/login`" in message
    assert "/login" in host_failure([], 1, "Not logged in · Please run /login\n")


EXPIRED_RESULT = [{
    "type": "result", "subtype": "success", "is_error": True, "errors": None,
    "result": "Failed to authenticate: OAuth session expired and could not be refreshed",
    "terminal_reason": "api_error", "total_cost_usd": 0, "num_turns": 1,
}]


@pytest.mark.parametrize("passed", [False, True])
def test_host_failure_on_the_harness_login_names_host_login(passed, monkeypatch):
    """testing-harness spec: Expired login names the remedy — the harness
    login's one remedy, closing with the login note."""
    monkeypatch.setattr(claude_runner.host_login, "L3_PASSED", passed)
    message = host_failure(EXPIRED_RESULT, 0, "", LoginSource.HARNESS)
    assert "OAuth session expired" in message
    assert LOGIN_COMMAND in message
    assert "/login" not in message
    assert message.endswith(f"{login_note(LOGIN_COMMAND)}.")


def test_host_failure_names_no_login_remedy_for_other_errors():
    stream = [{
        "type": "result", "subtype": "error_max_budget_usd", "is_error": True,
        "errors": ["Exceeded USD budget"], "total_cost_usd": 0.31, "num_turns": 4,
    }]
    assert "/login" not in host_failure(stream, 1, "")


def test_host_failure_falls_back_to_stderr_without_a_result():
    assert host_failure([], 1, "boom\n") == "claude failed: boom"
    assert host_failure([], 1, "") == "claude failed: no stderr"


def test_host_failure_names_a_missing_result_event():
    assert host_failure(events("unrouted-explore"), 0, "") == "claude emitted no result event"


def test_host_failure_is_none_on_success():
    assert host_failure(events("recorded-result"), 0, "") is None


# ---------- summary ----------------------------------------------------------


def test_summary_labels_an_ambient_run_and_lists_helpers():
    out = summary(ARGS, True, "fine", events("helper-fanout"), None)
    assert out["l1"] == "PASS"
    assert out["config"] == "ambient"
    assert out["config_dir"] is None
    assert out["cost_usd"] == 0.42
    assert out["helper_calls"] == ["Task"]
    assert out["single_context"] == "FAIL: 1 helper-agent call(s): Task"


def test_summary_labels_an_isolated_run(tmp_path):
    config = tmp_path / "cfg"
    out = summary(ARGS, False, "bad", events("recorded-result"), config)
    assert out["l1"] == "FAIL"
    assert out["config"] == "isolated"
    assert out["config_dir"] == str(config)
    assert out["helper_calls"] == []
    assert out["single_context"] == "PASS: no helper agents spawned"
    assert out["billing"] is None


def test_summary_labels_the_login_and_its_directory(tmp_path, monkeypatch):
    """testing-harness spec: Isolated run labelled; Write-back target labelled."""
    monkeypatch.setenv(claude_runner.host_login.STATE_VAR, str(tmp_path / "state"))
    monkeypatch.delenv("CLAUDE_CODE_OAUTH_TOKEN", raising=False)
    home = claude_runner.host_login.home(CLAUDE)
    home.mkdir(parents=True)
    (home / ".credentials.json").write_text("{}", encoding="utf-8")
    config = tmp_path / "cfg"
    config.mkdir()
    try:
        (config / ".credentials.json").symlink_to(home / ".credentials.json")
    except OSError:
        pytest.skip("symlinks cannot be created here")
    out = summary(ARGS, True, "fine", events("recorded-result"), config)
    assert (out["login"], out["login_dir"]) == ("harness", str(home))
    ambient = summary(ARGS, True, "fine", events("recorded-result"), None)
    assert (ambient["login"], ambient["login_dir"]) == ("ambient", None)
    monkeypatch.setenv("CLAUDE_CODE_OAUTH_TOKEN", "placeholder-not-a-token")
    token = summary(ARGS, True, "fine", events("recorded-result"), config)
    assert (token["login"], token["login_dir"]) == ("token", None)


def test_summary_applies_the_scenario_allowance_and_reports_extras():
    out = summary(ARGS, True, "fine", events("helper-fanout"), None,
                  allowed=1, extra={"feedback_words": 640})
    assert out["single_context"] == "PASS: 1 helper-agent call(s) within the allowance of 1"
    assert out["feedback_words"] == 640


# ---------- supervise dispatch ------------------------------------------------
#
# Synthetic workspaces in the shape a supervise run leaves behind: the
# normalized proposal, its notes, the review and the feedback side by side.

CLOSING_EN = load_closing_note(SKILLS)["English"]

SCOPED_FEEDBACK = f"""My verdict: **needs revision** — please address the points below and resubmit.

The plan is large for a Bachelor's thesis: five packages wait on each other in fourteen
weeks. Two ways to cut it to one core — the choice is yours:

A) Model and diagnosis: the priority model and the gap analysis; the revised checklist
moves to the outlook.
B) Revision and evaluation: a borrowed ranking, the weight on the revised checklist and a
trial with its users.

1. Name the criteria the model ranks by and where each comes from — proposal-write.
2. Say how many requirements the catalogue holds; it decides the audit's size — proposal-write.

What to keep: the access to the web team and the real checklist.

{CLOSING_EN}
"""

SCOPED_REVIEW = """**Verdict: needs revision.**

## Workload

| Package | Depends on | Size driver | Estimate (weeks, est.) |
|---|---|---|---|
| Catalogue review | — | catalogue size (unknown) | 3–6 |
| Priority model | catalogue review | criteria, expert time | 3 |

Scope verdict: over-scoped

## Verification

Verified by: fresh verifier

Contradicted: the regulation the export names for municipal websites.
"""

# the host stream of a run that started its verifier with the shipped brief
VERIFIER_EVENTS = [{"type": "assistant", "message": {"content": [{
    "type": "tool_use", "name": "Task",
    "input": {"description": "Verify feedback",
              "prompt": "Follow references/verifier-brief.md. Feedback: x-feedback.md"},
}]}}]


def supervise_ws(tmp_path, feedback=SCOPED_FEEDBACK, review=SCOPED_REVIEW):
    (tmp_path / "accessibility-priority-model.md").write_text(
        "# Prioritizing Accessibility Requirements\n\nWCAG 2.2 and EN 301 549.\n",
        encoding="utf-8")
    (tmp_path / "accessibility-priority-model.notes.md").write_text(
        "# Notes\n", encoding="utf-8")
    (tmp_path / "accessibility-priority-model-review.md").write_text(review, encoding="utf-8")
    (tmp_path / "accessibility-priority-model-feedback.md").write_text(
        feedback, encoding="utf-8")
    return tmp_path


def test_normalized_proposal_skips_the_sidecars(tmp_path):
    text = normalized_proposal(supervise_ws(tmp_path))
    assert text.startswith("# Prioritizing")
    assert normalized_proposal(tmp_path / "missing") is None


def test_supervise_scope_scenario_passes_a_complete_run(tmp_path):
    passed, why = supervise_verdict(SCENARIOS["supervise_scope"], supervise_ws(tmp_path),
                                    VERIFIER_EVENTS)
    assert passed, why
    assert "lettered cut options A, B" in why
    assert "workload table" in why
    assert "fresh verifier started with the brief" in why


def test_supervise_scenario_fails_when_the_verifier_was_skipped(tmp_path):
    """The headless host offers a subagent tool, so checking inline there is
    a skip, not the fallback (testing-harness spec: skipped verifier fails)."""
    passed, why = supervise_verdict(SCENARIOS["supervise_feedback"], supervise_ws(tmp_path), [])
    assert not passed
    assert "verifier did not run" in why


def test_supervise_scenario_fails_without_a_declaration(tmp_path):
    undeclared = SCOPED_REVIEW.replace("Verified by: fresh verifier\n", "")
    passed, why = supervise_verdict(SCENARIOS["supervise_feedback"],
                                    supervise_ws(tmp_path, review=undeclared), VERIFIER_EVENTS)
    assert not passed
    assert "does not say who verified" in why


def test_supervise_scope_scenario_fails_without_options_or_review_sections(tmp_path):
    flat = SCOPED_FEEDBACK.replace("A) ", "").replace("B) ", "")
    passed, why = supervise_verdict(
        SCENARIOS["supervise_scope"],
        supervise_ws(tmp_path, feedback=flat, review="**Verdict: needs revision.**\n"))
    assert not passed
    assert "lettered cut option" in why
    assert "no workload section" in why


def test_supervise_scope_scenario_uses_its_own_identity_tokens(tmp_path):
    leaked = SCOPED_FEEDBACK.replace("What to keep:", "Prof. Mustermann agrees. What to keep:")
    passed, why = supervise_verdict(SCENARIOS["supervise_scope"],
                                    supervise_ws(tmp_path, feedback=leaked), VERIFIER_EVENTS)
    assert not passed
    assert "Mustermann" in why


def test_supervise_feedback_scenario_skips_the_scope_verdicts(tmp_path):
    passed, why = supervise_verdict(SCENARIOS["supervise_feedback"], supervise_ws(tmp_path),
                                    VERIFIER_EVENTS)
    assert passed, why
    assert "lettered" not in why


def test_save_events_writes_jsonl_outside_the_markdown_globs(tmp_path):
    path = save_events([*VERIFIER_EVENTS, {"type": "result", "result": "done"}], tmp_path)
    lines = path.read_text(encoding="utf-8").splitlines()
    assert [json.loads(line)["type"] for line in lines] == ["assistant", "result"]
    assert path.name == EVENTS_FILE
    assert not list(tmp_path.glob("*.md"))


def test_supervise_scenarios_allow_exactly_one_verifier():
    for name in ("supervise_feedback", "supervise_literature", "supervise_scope"):
        assert SCENARIOS[name]["helpers"] == 1
    assert "helpers" not in SCENARIOS["check_report"]


NO_QUESTIONS = "I cannot answer any questions — decide and tell me what you did."


def test_every_draft_scenario_says_nobody_will_answer():
    """A dev run is one unattended turn, so a draft scenario that does not say
    so can end in a clarifying question and no draft — a haiku `write_from_seed`
    run stopped to ask for the degree level on 2026-10-04."""
    for name in DRAFT_SCENARIOS:
        assert NO_QUESTIONS in SCENARIOS[name]["request"], name


def test_supervise_extra_reports_the_body_length(tmp_path):
    words = supervise_extra(SCENARIOS["supervise_scope"], supervise_ws(tmp_path))
    assert 60 < words["feedback_words"] < 200
    assert supervise_extra(SCENARIOS["check_report"], tmp_path) == {}


# ---------- L2 aggregate verdict ---------------------------------------------


def test_l2_grades_pass_when_every_criterion_passes():
    passed, why = verdict_l2_grades({"write_l2_rq_quality": True, "write_l2_density": True})
    assert passed
    assert "write_l2_density" in why


def test_l2_grades_fail_naming_the_failed_criterion():
    passed, why = verdict_l2_grades({"write_l2_rq_quality": True, "write_l2_density": False})
    assert not passed
    assert "write_l2_density" in why
    assert "write_l2_rq_quality" not in why


def test_l2_grades_fail_when_nothing_was_graded():
    passed, why = verdict_l2_grades({})
    assert not passed
    assert "nothing graded" in why


# ---------- served model, exit statuses, billing strip ----------------------

MODEL_UNDER_TEST = "claude-fixture-1-0"
ROLES = shipped_registry().roles


def model_stream(*, status="allowed", overage=False, source="none", rate=True,
                 served=MODEL_UNDER_TEST, text="Done; the draft is written.") -> list[dict]:
    """A model-under-test stream in the host 2.1.284 shape: init, a rate-limit
    report, the result with its per-model usage."""
    events = [{"type": "system", "subtype": "init", "model": served, "apiKeySource": source,
               "claude_code_version": "2.1.284"}]
    if rate:
        events.append({"type": "rate_limit_event", "rate_limit_info": {
            "status": status, "rateLimitType": "five_hour", "utilization": 0.2,
            "isUsingOverage": overage}})
    events.append({
        "type": "result", "subtype": "success", "is_error": False, "result": text,
        "total_cost_usd": 0.41, "num_turns": 9, "duration_ms": 61000,
        "usage": {"input_tokens": 20, "output_tokens": 900, "cache_read_input_tokens": 5000,
                  "cache_creation_input_tokens": 700},
        "modelUsage": {served: {"outputTokens": 900, "provider": "firstParty"}},
    })
    return events


def stdout_of(events: list[dict]) -> str:
    return "".join(json.dumps(e) + "\n" for e in events)


def test_summary_records_requested_alias_served_model_and_cli_version():
    out = summary(ARGS, True, "fine", model_stream(), None)
    assert out["model_requested"] == "haiku"
    assert out["model"] == MODEL_UNDER_TEST
    assert out["cli_version"] == "2.1.284"


def test_summary_notes_a_served_model_modelusage_does_not_list():
    events = model_stream()
    events[-1]["modelUsage"] = {"claude-fixture-2-0": {"outputTokens": 900}}
    out = summary(ARGS, True, "fine", events, None)
    assert out["model"] == MODEL_UNDER_TEST
    assert "claude-fixture-2-0" in out["model_check"]


def test_exit_status_precedence_is_runner_failure_then_fail_then_untested():
    assert (EXIT_PASS, EXIT_FAIL, EXIT_USAGE, EXIT_UNTESTED, EXIT_RUNNER) == (0, 1, 2, 3, 4)
    assert exit_status(runner_failure=True, failed=True, untested=True) == EXIT_RUNNER
    assert exit_status(runner_failure=False, failed=True, untested=True) == EXIT_FAIL
    assert exit_status(runner_failure=False, failed=False, untested=True) == EXIT_UNTESTED
    assert exit_status(runner_failure=False, failed=False, untested=False) == EXIT_PASS


LAUNCH_ENV = {
    "PATH": "/usr/bin", "ANTHROPIC_API_KEY": "placeholder-not-a-key",
    "ANTHROPIC_AUTH_TOKEN": "placeholder", "ANTHROPIC_BASE_URL": "https://gateway.invalid",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "remapped", "CLAUDE_CODE_USE_BEDROCK": "1",
    "CLAUDE_CODE_USE_VERTEX": "1", "CLAUDE_EFFORT": "xhigh", "CLAUDECODE": "1",
    "CLAUDE_CODE_OAUTH_TOKEN": "placeholder-token", "OPENROUTER_API_KEY": "placeholder",
}


def test_model_env_strips_billing_variables_in_both_modes(tmp_path):
    """No inherited `ANTHROPIC_*` value in either mode; the isolated child's one
    `ANTHROPIC_` name is the empty profile directory the harness sets."""
    before = dict(LAUNCH_ENV)
    for config, harness_set in ((None, []), (tmp_path, ["ANTHROPIC_CONFIG_DIR"])):
        env = model_env(LAUNCH_ENV, config)
        assert not [k for k in env if k.startswith("CLAUDE_CODE_USE_")]
        assert [k for k in env if k.startswith("ANTHROPIC_")] == harness_set
        for kept in ("PATH", "CLAUDE_CODE_OAUTH_TOKEN"):
            assert env[kept] == LAUNCH_ENV[kept]
    assert before == LAUNCH_ENV


def test_isolated_model_env_names_the_empty_profile_directory(tmp_path):
    env = model_env({**LAUNCH_ENV, "ANTHROPIC_CONFIG_DIR": "/home/x/.config/anthropic"}, tmp_path)
    assert env["ANTHROPIC_CONFIG_DIR"] == str(tmp_path / PROFILE_DIR)


def test_model_env_switches_connectors_off_in_both_modes(tmp_path):
    launching = {**LAUNCH_ENV, "ENABLE_CLAUDEAI_MCP_SERVERS": "true"}
    for config in (None, tmp_path):
        assert model_env(launching, config)["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"


def test_ambient_model_env_keeps_the_operator_settings():
    env = model_env(LAUNCH_ENV, None)
    for kept in ("CLAUDE_EFFORT", "CLAUDECODE", "OPENROUTER_API_KEY"):
        assert env[kept] == LAUNCH_ENV[kept]
    assert "CLAUDE_CONFIG_DIR" not in env


def test_isolated_model_env_is_the_allowlist(tmp_path):
    # testing-harness spec: Isolated child environment — nothing of the
    # launching session, effort included, reaches an isolated run
    env = model_env(LAUNCH_ENV, tmp_path)
    assert env == allowlisted_env(CLAUDE, tmp_path, LAUNCH_ENV)
    for dropped in ("CLAUDE_EFFORT", "CLAUDECODE", "OPENROUTER_API_KEY"):
        assert dropped not in env
    assert env["CLAUDE_CONFIG_DIR"] == str(tmp_path)


# ---------- main(argv): fakes for the host, the isolation and the judge -------


@pytest.fixture
def isolated(monkeypatch, tmp_path):
    """`--isolated` without touching the stored login: a plain directory."""
    config = tmp_path / "isolated-config"
    config.mkdir()

    @contextmanager
    def fake_isolated_config(_prefix):
        yield config

    monkeypatch.setattr(claude_runner, "isolated_config", fake_isolated_config)
    return config


NO_LOGIN = "no stored login to link: run `claude`, then `/login`, then rerun"


def refuse_isolation(monkeypatch, code: object = NO_LOGIN) -> None:
    """`--isolated` whose preparation exits the way `routing.prepare_config` and
    `host_login.acquire_claim` do when the subscription cannot serve the run."""
    @contextmanager
    def refusing_isolated_config(_prefix):
        raise SystemExit(code)
        yield  # a generator, as the real context manager is

    monkeypatch.setattr(claude_runner, "isolated_config", refusing_isolated_config)


def fake_host(monkeypatch, stdout: str = "", returncode: int = 0, stderr: str = "",
              raises: Exception | None = None, timed_out: bool = False) -> dict:
    """Replace only the host's stream reader, which applies the stop condition
    the runner hands it event by event; the check script's own subprocess
    still runs. `seen["stop"]` is that condition."""
    seen: dict = {}

    def follow(command, **kwargs):
        seen.update(command=command, env=kwargs["env"], stop=kwargs["stop"])
        if raises is not None:
            raise raises
        return followed(parse_events(stdout), kwargs["stop"], returncode=returncode,
                        stderr=stderr, timed_out=timed_out)

    monkeypatch.setattr(claude_runner, "follow_stream", follow)
    return seen


def fake_run(monkeypatch, produce=None, events=None) -> list:
    """Replace `run_claude`: `produce(ws)` writes what the model would have."""
    runs = []

    def run_claude(ws, request, model, _timeout, budget=None, config=None):
        runs.append({"request": request, "model": model, "budget": budget, "config": config})
        if produce:
            produce(ws)
        return events if events is not None else model_stream()

    monkeypatch.setattr(claude_runner, "run_claude", run_claude)
    return runs


class FakeJudge:
    """Stands in for `claude_cli.call`: grades every criterion, at a fixed
    notional cost, and records each prompt it was handed."""

    def __init__(self, grade="C", cost=0.05):
        self.grade, self.cost, self.prompts = grade, cost, []

    async def __call__(self, prompt, **kwargs):
        self.prompts.append(prompt)
        return JudgeCall(text=f"Reasoned.\nGRADE: {self.grade}", model=kwargs["model"],
                         cli_version="2.1.284", effort=kwargs["effort"], thinking_tokens=100,
                         notional_usd=self.cost, rate_limit=RateLimit("allowed", "five_hour", 0.2))


async def _no_preflight(*_args, **_kwargs):
    return None


@pytest.fixture
def judge(monkeypatch):
    monkeypatch.delenv("DEV_JUDGE_MODEL", raising=False)
    fake = FakeJudge()
    monkeypatch.setattr(claude_cli, "call", fake)
    monkeypatch.setattr(claude_cli, "preflight", _no_preflight)
    return fake


def write_draft(ws: Path) -> None:
    """A fresh `<slug>.md` beside the seed — named so that it does not end in
    `-review.md`, which the draft selection skips beside a seed."""
    (ws / "drift-detection-proposal.md").write_text(CLEAN_DRAFT, encoding="utf-8")


def logged(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


# ---------- runner failures and untested model runs --------------------------

EXPIRED = (STREAMS / "expired-login.jsonl").read_text(encoding="utf-8")
BUDGET_OVERRUN = stdout_of([{
    "type": "result", "subtype": "error_max_budget_usd", "is_error": True,
    "errors": ["Exceeded USD budget"], "total_cost_usd": 2.01, "num_turns": 30,
}])


def test_expired_login_is_untested_with_the_message_unchanged(monkeypatch, tmp_path):
    fake_host(monkeypatch, EXPIRED)
    log = tmp_path / "log.jsonl"
    assert main(["check_report", "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert line["outcome"] == "UNTESTED"
    assert line["why"] == host_failure(parse_events(EXPIRED), 0, "")


def test_budget_overrun_is_a_runner_failure_not_a_fail(monkeypatch, tmp_path):
    fake_host(monkeypatch, BUDGET_OVERRUN, returncode=1)
    log = tmp_path / "log.jsonl"
    assert main(["check_report", "--max-budget-usd", "2", "--summary-log", str(log)]) == EXIT_RUNNER
    [line] = logged(log)
    assert line["outcome"] == "RUNNER FAILURE"
    assert line["why"].startswith("claude failed: error_max_budget_usd: Exceeded USD budget")


LIMIT_TEXT = "You've hit your limit · resets 3pm"


def refused_stream(**rate) -> list[dict]:
    """A run the host stopped on a rate-limit report, in the shape of the
    expired-login recording: an error result carrying the host's own text,
    and (in the cases below) a non-zero exit."""
    events = model_stream(**rate)
    events[-1] = {"type": "result", "subtype": "success", "is_error": True, "errors": None,
                  "result": LIMIT_TEXT, "total_cost_usd": 0, "num_turns": 1,
                  "duration_ms": 900}
    return events


@pytest.mark.parametrize(("stream", "returncode", "cause"), [
    (model_stream(overage=True), 0, "overage"),
    (model_stream(overage=None), 0, "without an overage flag"),
    (model_stream(source="ANTHROPIC_API_KEY"), 0, "'ANTHROPIC_API_KEY'"),
    (model_stream(rate=False), 0, "rate limit not reported, overage cannot be ruled out"),
    (refused_stream(status="rejected"), 1, "'rejected'"),
    (refused_stream(overage=True), 1, "overage"),
    (refused_stream(source="ANTHROPIC_API_KEY"), 1, "'ANTHROPIC_API_KEY'"),
])
@pytest.mark.usefixtures("isolated")
def test_billed_model_runs_are_untested_and_never_judged(stream, returncode, cause, monkeypatch,
                                                          tmp_path, judge):
    """Every one records `billing`, so the smoke gate stops the later steps —
    a failed run with an API-key source included."""
    fake_host(monkeypatch, stdout_of(stream), returncode=returncode)
    log = tmp_path / "log.jsonl"
    code = main(["write_from_seed", "--isolated", "--judge", "--summary-log", str(log)])
    assert code == EXIT_UNTESTED
    assert judge.prompts == []
    [line] = logged(log)
    assert cause in line["why"]
    assert cause in line["billing"]
    if returncode:  # the host's own message stays, the billing reason is appended
        assert LIMIT_TEXT in line["why"]


def test_budget_overrun_under_an_allowed_rate_limit_stays_a_runner_failure(monkeypatch,
                                                                           tmp_path):
    """Only an explicit refusal moves an errored run to untested."""
    stream = [*model_stream()[:2], *parse_events(BUDGET_OVERRUN)]
    fake_host(monkeypatch, stdout_of(stream), returncode=1)
    log = tmp_path / "log.jsonl"
    assert main(["check_report", "--summary-log", str(log)]) == EXIT_RUNNER
    assert "not a subscription result" not in logged(log)[0]["why"]


def test_isolation_refused_is_untested_and_labelled_isolated(monkeypatch, tmp_path):
    refuse_isolation(monkeypatch)
    fake_host(monkeypatch, raises=AssertionError("the model ran without its config"))
    log = tmp_path / "log.jsonl"
    assert main(["check_report", "--isolated", "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert (line["outcome"], line["why"]) == ("UNTESTED", NO_LOGIN)
    assert (line["config"], line["config_dir"]) == ("isolated", None)


def test_isolation_exit_without_a_message_is_not_swallowed(monkeypatch):
    refuse_isolation(monkeypatch, code=5)
    with pytest.raises(SystemExit) as exc, ExitStack() as stack:
        claude_runner.enter_isolation(stack, "devrun-config-")
    assert exc.value.code == 5


def test_host_timeout_is_a_runner_failure(monkeypatch, tmp_path):
    fake_host(monkeypatch, timed_out=True)
    log = tmp_path / "log.jsonl"
    assert main(["check_report", "--timeout", "5", "--summary-log", str(log)]) == EXIT_RUNNER
    [line] = logged(log)
    assert line["outcome"] == "RUNNER FAILURE"
    assert line["why"] == "claude did not finish within 5s"


def test_runner_crash_is_a_runner_failure_with_its_line(monkeypatch, tmp_path, capsys):
    fake_run(monkeypatch, write_draft)

    def crash(*_args, **_kwargs):
        raise RuntimeError("verdict crashed")

    monkeypatch.setattr(claude_runner, "verdict", crash)
    log = tmp_path / "log.jsonl"
    assert main(["write_from_seed", "--summary-log", str(log)]) == EXIT_RUNNER
    [line] = logged(log)
    assert line["outcome"] == "RUNNER FAILURE"
    assert line["why"] == "runner crashed: RuntimeError('verdict crashed')"
    assert "Traceback" in capsys.readouterr().err


def test_unwritable_summary_log_is_a_runner_failure_not_a_fail(monkeypatch, tmp_path, capsys):
    fake_run(monkeypatch, write_draft)
    assert main(["write_from_seed", "--summary-log", str(tmp_path)]) == EXIT_RUNNER
    assert "Traceback" in capsys.readouterr().err


@pytest.mark.parametrize("isolated_run", [False, True])
def test_host_receives_the_stripped_environment(isolated_run, monkeypatch, request):
    for name, value in LAUNCH_ENV.items():
        if name != "PATH":
            monkeypatch.setenv(name, value)
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    seen = fake_host(monkeypatch, stdout_of(model_stream()))
    argv = ["check_report"]
    if isolated_run:
        config = request.getfixturevalue("isolated")
        argv.append("--isolated")
    main(argv)
    env = seen["env"]
    assert not [k for k in env if k.startswith("CLAUDE_CODE_USE_")]
    inherited = set(LAUNCH_ENV.values())
    assert not [k for k, v in env.items() if k.startswith("ANTHROPIC_") and v in inherited]
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == "placeholder-token"
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    if isolated_run:
        # the allowlist: the operator's effort setting is not the default host's
        assert "CLAUDE_EFFORT" not in env
        assert env["CLAUDE_CONFIG_DIR"] == str(config)
        assert env["ANTHROPIC_CONFIG_DIR"] == str(config / PROFILE_DIR)
    else:
        assert env["CLAUDE_EFFORT"] == "xhigh"
        assert "CLAUDE_CONFIG_DIR" not in env
        assert not [k for k in env if k.startswith("ANTHROPIC_")]


# ---------- claude.ai account surfaces (testing-harness spec: Isolated
# measurement environment; Dev-runner cost and helper-agent telemetry) --------

SURFACES = events("claudeai-surfaces")
CLEAN_INIT = events("clean-init")
AMBIENT_MCP = events("ambient-user-mcp")


def handed_stop(monkeypatch, tmp_path, config: Path | None):
    """The stop condition `run_claude` hands the stream reader."""
    seen = fake_host(monkeypatch, stdout_of(model_stream()))
    claude_runner.run_claude(tmp_path, "request", "haiku", 5, config=config)
    return seen["stop"]


def test_the_isolated_stop_fires_on_the_recorded_init(monkeypatch, tmp_path):
    stop = handed_stop(monkeypatch, tmp_path, tmp_path)
    assert stop(SURFACES[:1])
    assert stop(SURFACES[:2])  # a tagged command-list change on its own fires too
    assert not stop(CLEAN_INIT)
    assert not stop(model_stream())


def test_the_ambient_stop_fires_only_on_the_claudeai_server(monkeypatch, tmp_path):
    stop = handed_stop(monkeypatch, tmp_path, None)
    assert stop(AMBIENT_MCP)
    user_only = [{**AMBIENT_MCP[0], "mcp_servers": AMBIENT_MCP[0]["mcp_servers"][:1]}]
    assert user_only[0]["mcp_servers"][0]["source"] == "user"
    assert not stop(user_only)


def run_with(monkeypatch, tmp_path, stream: list[dict], *, config: Path | None,
             returncode: int = 0) -> claude_runner.RunnerFailure:
    fake_host(monkeypatch, stdout_of(stream), returncode=returncode)
    with pytest.raises(claude_runner.RunnerFailure) as raised:
        claude_runner.run_claude(tmp_path, "request", "haiku", 5, config=config)
    return raised.value


def test_a_stopped_stream_is_untested_naming_the_surface(monkeypatch, tmp_path):
    # the recorded leak followed by a host error the stop never lets through
    failure = run_with(monkeypatch, tmp_path, [*SURFACES, *parse_events(BUDGET_OVERRUN)],
                       config=tmp_path)
    assert failure.untested
    assert "claude.ai Claude Docs" in failure.message
    assert "opt-outs did not hold" in failure.message
    assert "claude failed" not in failure.message
    assert "rate limit not reported" not in failure.message
    assert failure.events == SURFACES[:1]


def test_a_claudeai_connector_stops_an_ambient_run(monkeypatch, tmp_path):
    failure = run_with(monkeypatch, tmp_path, [*AMBIENT_MCP, *model_stream()], config=None)
    assert failure.untested
    assert "claude.ai Claude Docs" in failure.message
    assert "local-notes" not in failure.message
    # the operator's own settings were never the opt-out here; the switch was
    assert "connector switch did not hold" in failure.message
    assert "disableClaudeAiConnectors" not in failure.message


def test_synced_content_outranks_a_timeout(monkeypatch, tmp_path):
    """A polluted run's other failures say nothing about the skill, so the
    leak comes first — a deadline included."""
    (tmp_path / "skills" / "synced" / "x").mkdir(parents=True)
    fake_host(monkeypatch, stdout_of(model_stream()[:1]), timed_out=True)
    with pytest.raises(claude_runner.RunnerFailure) as raised:
        claude_runner.run_claude(tmp_path, "request", "haiku", 5, config=tmp_path)
    failure = raised.value
    assert failure.untested
    assert failure.message.index("skills/synced/x") < failure.message.index(
        "claude did not finish within 5s")


def test_synced_content_left_in_the_configuration_is_untested(monkeypatch, tmp_path):
    (tmp_path / "skills" / "synced" / "x").mkdir(parents=True)
    failure = run_with(monkeypatch, tmp_path, model_stream(), config=tmp_path)
    assert failure.untested
    assert "skills/synced/x" in failure.message
    assert failure.events == model_stream()


def test_a_configuration_leak_carries_the_host_failure_too(monkeypatch, tmp_path):
    (tmp_path / "plugins" / "synced" / "y").mkdir(parents=True)
    failure = run_with(monkeypatch, tmp_path, parse_events(BUDGET_OVERRUN), config=tmp_path,
                       returncode=1)
    assert failure.untested
    assert failure.message.index("plugins/synced/y") < failure.message.index(
        "claude failed: error_max_budget_usd")


def test_a_surface_does_not_hide_overage(monkeypatch, tmp_path):
    """testing-harness spec: A surface does not hide overage."""
    overage = model_stream(overage=True)[1]
    stream = [*CLEAN_INIT[:1], overage, SURFACES[1], *model_stream()[2:]]
    failure = run_with(monkeypatch, tmp_path, stream, config=tmp_path)
    assert failure.untested
    assert "docs" in failure.message
    assert "overage in use" in failure.message


def test_an_ambient_run_measures_the_operators_own_mcp_server(monkeypatch, tmp_path):
    user_only = [{**AMBIENT_MCP[0], "mcp_servers": AMBIENT_MCP[0]["mcp_servers"][:1]}]
    fake_host(monkeypatch, stdout_of([*user_only, *model_stream()[1:]]))
    events = claude_runner.run_claude(tmp_path, "request", "haiku", 5)
    assert events[0]["mcp_servers"][0]["name"] == "local-notes"


@pytest.mark.usefixtures("isolated")
def test_a_surface_makes_the_run_untested_and_never_judged(monkeypatch, tmp_path, judge):
    fake_host(monkeypatch, stdout_of([*SURFACES, *model_stream()]))
    log = tmp_path / "log.jsonl"
    code = main(["write_from_seed", "--isolated", "--judge", "--summary-log", str(log)])
    assert code == EXIT_UNTESTED
    assert judge.prompts == []
    [line] = logged(log)
    assert line["outcome"] == "UNTESTED"
    assert "l1" not in line
    assert "claude.ai Claude Docs" in line["why"]


# ---------- --judge -------------------------------------------------------


def refuse_staging(monkeypatch):
    def no_workspace(*_args, **_kwargs):
        raise AssertionError("staged before the usage error")

    monkeypatch.setattr(claude_runner.tempfile, "mkdtemp", no_workspace)


@pytest.mark.usefixtures("judge")
def test_judge_without_isolation_is_refused_before_staging(monkeypatch, capsys):
    refuse_staging(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        main(["write_from_seed", "--judge"])
    assert exc.value.code == EXIT_USAGE
    assert "--isolated" in capsys.readouterr().err


@pytest.mark.usefixtures("judge")
def test_judge_on_a_scenario_without_a_rubric_is_refused(monkeypatch, capsys):
    refuse_staging(monkeypatch)
    with pytest.raises(SystemExit) as exc:
        main(["check_report", "--isolated", "--judge"])
    assert exc.value.code == EXIT_USAGE
    assert "no rubric twin" in capsys.readouterr().err


@pytest.mark.parametrize("wrong", ["openrouter/lab/judge-1", "sonnet", "anthropic/claude-x-1"])
def test_metered_or_alias_dev_judge_is_refused_before_any_call(wrong, monkeypatch, judge, capsys):
    refuse_staging(monkeypatch)
    monkeypatch.setenv("DEV_JUDGE_MODEL", wrong)
    with pytest.raises(SystemExit) as exc:
        main(["write_from_seed", "--isolated", "--judge"])
    assert exc.value.code == EXIT_USAGE
    assert "[roles].dev_judge" in capsys.readouterr().err
    assert judge.prompts == []


@pytest.mark.usefixtures("isolated")
def test_judged_run_reports_l2_beside_l1(monkeypatch, tmp_path, judge):
    fake_run(monkeypatch, write_draft)
    log = tmp_path / "log.jsonl"
    assert main(["write_from_seed", "--isolated", "--judge", "--summary-log", str(log)]) == 0
    [line] = logged(log)
    assert line["l1"] == "PASS"
    assert line["l2_label"] == JUDGE_LABEL == "dev-runner L2, not comparable to matrix"
    l2 = line["l2"]
    assert {name: c["grade"] for name, c in l2["criteria"].items()} == {
        "write_l2_rq_quality": "PASS", "write_l2_density": "PASS"}
    assert l2["judge_model"] == l2["judge_served"] == ROLES.dev_judge
    assert l2["effort"] == ROLES.dev_judge_effort
    assert l2["cli_version"] == "2.1.284"
    assert l2["thinking_tokens"] == 200
    assert l2["notional_usd"] == pytest.approx(0.10)
    assert line["self_graded"] is False
    assert line["outcome"] == "PASS"
    request = SCENARIOS["write_from_seed"]["request"]
    assert all(request in prompt and CLEAN_DRAFT in prompt for prompt in judge.prompts)


@pytest.mark.usefixtures("isolated", "judge")
def test_judge_graded_by_the_model_under_test_is_flagged(monkeypatch, tmp_path):
    monkeypatch.setenv("DEV_JUDGE_MODEL", MODEL_UNDER_TEST)
    fake_run(monkeypatch, write_draft)
    log = tmp_path / "log.jsonl"
    main(["write_from_seed", "--isolated", "--judge", "--summary-log", str(log)])
    assert logged(log)[0]["self_graded"] is True


@pytest.mark.usefixtures("isolated")
def test_failed_criterion_fails_the_run(monkeypatch, tmp_path, judge):
    judge.grade = "I"
    fake_run(monkeypatch, write_draft)
    log = tmp_path / "log.jsonl"
    assert main(["write_from_seed", "--isolated", "--judge", "--summary-log", str(log)]) == 1
    assert "write_l2_density" in logged(log)[0]["l2_verdict"]


@pytest.mark.usefixtures("isolated")
def test_missing_artifact_is_not_judged(monkeypatch, tmp_path, judge):
    fake_run(monkeypatch)  # the model wrote nothing
    log = tmp_path / "log.jsonl"
    assert main(["write_from_seed", "--isolated", "--judge", "--summary-log", str(log)]) == 1
    criteria = logged(log)[0]["l2"]["criteria"]
    assert {c["why"] for c in criteria.values()} == {"not judged: no artifact"}
    assert judge.prompts == []


@pytest.mark.usefixtures("isolated")
def test_notional_cap_stops_further_judge_calls(monkeypatch, tmp_path, judge):
    fake_run(monkeypatch, write_draft)
    log = tmp_path / "log.jsonl"
    code = main(["write_from_seed", "--isolated", "--judge", "--max-notional", "0.04",
                 "--summary-log", str(log)])
    assert code == EXIT_UNTESTED
    assert len(judge.prompts) == 1
    grades = [c["grade"] for c in logged(log)[0]["l2"]["criteria"].values()]
    assert sorted(grades) == ["PASS", "UNTESTED"]


# ---------- --rejudge ------------------------------------------------------


def kept_workspace(root: Path, name: str) -> Path:
    ws = root / name
    ws.mkdir()
    write_draft(ws)
    save_events(model_stream(), ws)
    return ws


def no_model_run(monkeypatch):
    def run_claude(*_args, **_kwargs):
        raise AssertionError("re-grading ran the model under test")

    monkeypatch.setattr(claude_runner, "run_claude", run_claude)


@pytest.mark.usefixtures("isolated")
def test_rejudge_grades_kept_workspaces_without_a_model_run(monkeypatch, tmp_path, judge):
    no_model_run(monkeypatch)
    first, second = kept_workspace(tmp_path, "a"), kept_workspace(tmp_path, "b")
    log = tmp_path / "log.jsonl"
    code = main(["write_from_seed", "--rejudge", str(first), str(second),
                 "--summary-log", str(log)])
    assert code == EXIT_PASS
    assert len(judge.prompts) == 4
    lines = logged(log)
    assert [line["workspace"] for line in lines] == [str(first), str(second)]
    assert all(line["l2_label"] == JUDGE_LABEL for line in lines)
    assert all(line["self_graded"] is False for line in lines)


@pytest.mark.usefixtures("isolated")
def test_rejudge_projection_over_the_cap_stops_the_batch(monkeypatch, tmp_path, judge, capsys):
    no_model_run(monkeypatch)
    judge.cost = 1.0
    first, second = kept_workspace(tmp_path, "a"), kept_workspace(tmp_path, "b")
    log = tmp_path / "log.jsonl"
    code = main(["write_from_seed", "--rejudge", str(first), str(second),
                 "--max-notional", "2", "--summary-log", str(log)])
    assert code == EXIT_UNTESTED
    assert len(judge.prompts) == 1
    assert "projection" in capsys.readouterr().out
    second_grades = logged(log)[1]["l2"]["criteria"].values()
    assert {c["grade"] for c in second_grades} == {"UNTESTED"}


@pytest.mark.usefixtures("isolated")
def test_rejudge_refuses_a_missing_workspace(monkeypatch, tmp_path, judge):
    no_model_run(monkeypatch)
    assert main(["write_from_seed", "--rejudge", str(tmp_path / "gone")]) == EXIT_USAGE
    assert judge.prompts == []


def test_rejudge_with_isolation_refused_is_untested(monkeypatch, tmp_path, judge):
    no_model_run(monkeypatch)
    refuse_isolation(monkeypatch)
    ws = kept_workspace(tmp_path, "a")
    log = tmp_path / "log.jsonl"
    assert main(["write_from_seed", "--rejudge", str(ws), "--summary-log", str(log)]) == \
        EXIT_UNTESTED
    assert judge.prompts == []
    [line] = logged(log)
    assert line["outcome"] == "UNTESTED"
    assert {(c["grade"], c["why"]) for c in line["l2"]["criteria"].values()} == {
        ("UNTESTED", NO_LOGIN)}


async def _no_claude_binary(*_args, **_kwargs):
    raise FileNotFoundError(2, "No such file or directory", "claude")


def undecodable_draft(ws: Path) -> None:
    (ws / "drift-detection-proposal.md").write_bytes(b"# Draft\n\n\xff\xfe not UTF-8\n")


@pytest.mark.parametrize("crash", ["no-binary", "undecodable-draft"])
@pytest.mark.usefixtures("isolated", "judge")
def test_rejudge_crash_is_a_runner_failure_per_workspace(crash, monkeypatch, tmp_path, capsys):
    no_model_run(monkeypatch)
    first, second = kept_workspace(tmp_path, "a"), kept_workspace(tmp_path, "b")
    if crash == "no-binary":
        monkeypatch.setattr(claude_cli, "preflight", _no_claude_binary)
    else:
        undecodable_draft(second)
    log = tmp_path / "log.jsonl"
    code = main(["write_from_seed", "--rejudge", str(first), str(second),
                 "--summary-log", str(log)])
    assert code == EXIT_RUNNER
    lines = logged(log)
    assert [(line["workspace"], line["outcome"]) for line in lines] == [
        (str(first), "RUNNER FAILURE"), (str(second), "RUNNER FAILURE")]
    assert all(line["why"].startswith("runner crashed: ") for line in lines)
    assert "Traceback" in capsys.readouterr().err


# ---------- --summary-log and --summarize -------------------------------------


def test_summary_log_appends_on_success_and_failure_paths(monkeypatch, tmp_path):
    log = tmp_path / "logs" / "smoke.jsonl"
    fake_run(monkeypatch, write_draft)
    main(["write_from_seed", "--summary-log", str(log)])
    monkeypatch.undo()  # back to the real run_claude; fake only the host from here
    fake_host(monkeypatch, BUDGET_OVERRUN, returncode=1)
    main(["check_report", "--summary-log", str(log)])
    assert [(line["scenario"], line["outcome"]) for line in logged(log)] == [
        ("write_from_seed", "PASS"), ("check_report", "RUNNER FAILURE")]


# ---------- the smoke gate: no host after a billing signal (testing-harness spec:
# Smoke stops after a billing signal) ------------------------------------------------

OVERAGE = "overage in use (rate limit five_hour)"


def test_an_overage_run_records_its_billing_reason(monkeypatch, tmp_path):
    fake_host(monkeypatch, stdout_of(model_stream(overage=True)))
    log = tmp_path / "smoke.jsonl"
    assert main(["check_report", "--summary-log", str(log)]) == EXIT_UNTESTED
    [line] = logged(log)
    assert line["billing"] == OVERAGE


def test_a_clean_run_records_no_billing_reason(monkeypatch, tmp_path):
    fake_run(monkeypatch, write_draft)
    log = tmp_path / "smoke.jsonl"
    main(["write_from_seed", "--summary-log", str(log)])
    assert logged(log)[0]["billing"] is None


def test_a_step_after_a_billing_signal_starts_no_host(monkeypatch, tmp_path, capsys):
    log = tmp_path / "smoke.jsonl"
    log.write_text(json.dumps({"scenario": "write_from_seed", "outcome": "UNTESTED",
                               "exit_status": EXIT_UNTESTED, "why": "x",
                               "billing": OVERAGE}) + "\n", encoding="utf-8")
    refuse_isolation(monkeypatch, code=AssertionError("isolation was prepared"))
    fake_host(monkeypatch, raises=AssertionError("a host was started after a billing signal"))
    assert main(["import_messy", "--isolated", "--summary-log", str(log)]) == EXIT_UNTESTED
    line = logged(log)[-1]
    assert (line["scenario"], line["outcome"]) == ("import_messy", "UNTESTED")
    assert line["why"].startswith(f"not run: write_from_seed reported {OVERAGE}")
    assert "--summarize" in line["why"]
    capsys.readouterr()
    core = ["write_from_seed", "import_messy"]
    assert main(["--summarize", str(log), "--expect", *core]) == EXIT_UNTESTED
    assert "import_messy: not run: write_from_seed reported overage" in capsys.readouterr().out


def test_a_log_without_billing_lets_the_step_run(monkeypatch, tmp_path):
    log = tmp_path / "smoke.jsonl"
    write_log(log, {"write_from_seed": 1})
    seen = fake_host(monkeypatch, stdout_of(model_stream()))
    main(["check_report", "--summary-log", str(log)])
    assert "command" in seen
    assert logged(log)[-1]["scenario"] == "check_report"


def test_summary_rows_keep_the_latest_line_per_scenario():
    rows = summary_rows([
        {"scenario": "a", "outcome": "FAIL", "exit_status": 1, "why": "first"},
        {"scenario": "b", "outcome": "PASS", "exit_status": 0, "why": "fine"},
        {"scenario": "a", "outcome": "PASS", "exit_status": 0, "why": "rerun"},
    ])
    assert [(r["scenario"], r["outcome"], r["why"]) for r in rows] == [
        ("a", "PASS", "rerun"), ("b", "PASS", "fine")]


def write_log(path: Path, outcomes: dict[str, int]) -> None:
    names = {0: "PASS", 1: "FAIL", 3: "UNTESTED", 4: "RUNNER FAILURE"}
    path.write_text("".join(
        json.dumps({"scenario": s, "outcome": names[c], "exit_status": c, "why": "x"}) + "\n"
        for s, c in outcomes.items()), encoding="utf-8")


def test_summarize_prints_one_row_per_scenario_and_removes_the_log(tmp_path, capsys):
    log = tmp_path / "smoke.jsonl"
    write_log(log, {"write_from_seed": 0, "import_messy": 1, "customize_override": 3})
    assert main(["--summarize", str(log)]) == EXIT_FAIL
    out = capsys.readouterr().out
    for scenario in ("write_from_seed", "import_messy", "customize_override"):
        assert out.count(scenario) == 1
    assert not log.exists()


def test_summarize_passes_only_when_every_row_passed(tmp_path):
    log = tmp_path / "smoke.jsonl"
    write_log(log, {"write_from_seed": 0, "import_messy": 0})
    assert main(["--summarize", str(log)]) == EXIT_PASS
    write_log(log, {"write_from_seed": 0, "import_messy": 3})
    assert main(["--summarize", str(log)]) == EXIT_UNTESTED
    assert main(["--summarize", str(log)]) == EXIT_RUNNER, "no log, nothing ran"


def test_aggregate_status_reads_any_non_verdict_status_as_a_runner_failure():
    assert aggregate_status([EXIT_PASS, EXIT_PASS]) == EXIT_PASS
    assert aggregate_status([EXIT_PASS, EXIT_UNTESTED, EXIT_FAIL]) == EXIT_FAIL
    for odd in (EXIT_USAGE, 5, -1):
        assert aggregate_status([EXIT_PASS, odd]) == EXIT_RUNNER
    assert aggregate_status([]) == EXIT_RUNNER


def test_summarize_lists_an_expected_scenario_that_left_no_line(monkeypatch, tmp_path, capsys):
    """A step that exits before its run records anything — here the usage
    error of a judge ID the subscription does not serve — is a runner failure
    in the closing summary, never left out of a summary that reads PASS."""
    log = tmp_path / "smoke.jsonl"
    write_log(log, {"import_messy": 0, "customize_override": 0})
    monkeypatch.setenv("DEV_JUDGE_MODEL", "sonnet")
    with pytest.raises(SystemExit) as exc:
        main(["write_from_seed", "--isolated", "--judge", "--summary-log", str(log)])
    assert exc.value.code == EXIT_USAGE
    capsys.readouterr()
    core = ["write_from_seed", "import_messy", "customize_override"]
    assert main(["--summarize", str(log), "--expect", *core]) == EXIT_RUNNER
    out = capsys.readouterr().out
    assert "=== 3 run(s) ===" in out
    assert f"RUNNER FAILURE  write_from_seed: {NO_LINE[:60]}" in out
    assert "=== RUNNER FAILURE ===" in out


def test_summarize_with_nothing_logged_lists_every_expected_scenario(tmp_path, capsys):
    rows = summary_rows([], ["write_from_seed", "import_messy", "write_from_seed"])
    assert [(r["scenario"], r["exit_status"]) for r in rows] == [
        ("write_from_seed", EXIT_RUNNER), ("import_messy", EXIT_RUNNER)]
    assert main(["--summarize", str(tmp_path / "absent.jsonl"),
                 "--expect", "write_from_seed"]) == EXIT_RUNNER
    assert "write_from_seed" in capsys.readouterr().out


def test_expect_without_summarize_is_a_usage_error(capsys):
    with pytest.raises(SystemExit) as exc:
        main(["write_from_seed", "--expect", "write_from_seed"])
    assert exc.value.code == EXIT_USAGE
    assert "--summarize" in capsys.readouterr().err


# ---------- customize_override ---------------------------------------------

F00 = "ml-code-review.md"
OVERRIDE = ('# Workspace rules\n\n```toml\n[references]\nmin_count = 8\n\n'
            '[timeline]\ndetail = "detailed"\n```\n')


def customize_ws(tmp_path: Path, guidelines: str | None) -> Path:
    shutil.copy(FIXTURES / "f00-clean-en" / F00, tmp_path / F00)
    if guidelines is not None:
        (tmp_path / "guidelines.md").write_text(guidelines, encoding="utf-8")
    return tmp_path


def test_customize_override_scenario_passes_with_the_nested_override(tmp_path):
    scenario = SCENARIOS["customize_override"]
    assert (scenario["fixture"], scenario["skill"]) == ("f00-clean-en", "proposal-customize")
    passed, why = verdict("customize_override", scenario, customize_ws(tmp_path, OVERRIDE), "")
    assert passed, why


def test_customize_override_scenario_fails_without_the_override(tmp_path):
    passed, why = verdict("customize_override", SCENARIOS["customize_override"],
                          customize_ws(tmp_path, None), "")
    assert not passed
    assert "guidelines.md not created" in why


# ---------- the subscription smoke task (design D8) ---------------------------


def poe_tasks() -> dict:
    return tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))["tool"]["poe"][
        "tasks"]


def test_smoke_is_a_subscription_sequence_over_the_core_scenarios():
    smoke = poe_tasks()["smoke"]
    assert smoke["default_item_type"] == "cmd"
    assert smoke["ignore_fail"] == "return_non_zero"
    assert "envfile" not in smoke
    *steps, closing = smoke["sequence"]
    core = list(shipped_registry().tasks.core)
    assert [step.split()[2] for step in steps] == core
    logs = set()
    for step in steps:
        words = step.split()
        assert words[:2] == ["python", "harness/claude_runner.py"]
        assert "--isolated" in words
        assert "--max-budget-usd" in words
        logs.add(words[words.index("--summary-log") + 1])
    [log] = logs
    # every step is expected, so one that exits before logging is not left out
    assert closing.split() == ["python", "harness/claude_runner.py", "--summarize", log,
                               "--expect", *core]


def test_metered_smoke_stays_behind_the_key_file_and_the_gate():
    smoke_inspect = poe_tasks()["smoke-inspect"]
    assert smoke_inspect["envfile"] == ".env"
    assert smoke_inspect["cmd"] == "python harness/matrix.py --smoke"
