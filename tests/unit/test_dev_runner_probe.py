"""L0: the dev runner's cost and helper-agent probe (testing-harness spec:
Dev-runner cost and helper-agent telemetry).

The probe reads the host's stream-json events. Three sources under
`data/routing_streams/`: the synthetic `helper-fanout.jsonl` pins the failing
case, the reduced recording `recorded-result.jsonl` pins the host's result-event
shape — a field rename fails here instead of blanking the telemetry line — and
the failure paths are fed synthetic events, since no recorded run hit them.
"""

import argparse
import json
from pathlib import Path

from claude_runner import (
    EVENTS_FILE,
    SCENARIOS,
    SKILLS,
    final_text,
    host_command,
    host_failure,
    normalized_proposal,
    parse_events,
    save_events,
    summary,
    supervise_extra,
    supervise_verdict,
    telemetry,
)
from l1_checks import HELPER_TOOLS, load_closing_note, verdict_single_context
from routing import DISALLOWED_TOOLS, OUTWARD_TOOLS, tool_calls

STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"
ARGS = argparse.Namespace(scenario="check_report", model="haiku", no_skill=False)


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


def test_supervise_extra_reports_the_body_length(tmp_path):
    words = supervise_extra(SCENARIOS["supervise_scope"], supervise_ws(tmp_path))
    assert 60 < words["feedback_words"] < 200
    assert supervise_extra(SCENARIOS["check_report"], tmp_path) == {}
