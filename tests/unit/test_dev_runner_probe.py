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
    final_text,
    host_command,
    host_failure,
    parse_events,
    summary,
    telemetry,
)
from l1_checks import HELPER_TOOLS, verdict_single_context
from routing import tool_calls

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


def test_host_failure_reports_an_error_result_with_its_detail():
    stream = [{
        "type": "result", "subtype": "error_max_budget_usd", "is_error": True,
        "errors": ["Exceeded USD budget"], "total_cost_usd": 0.31, "num_turns": 4,
    }]
    message = host_failure(stream, 1, "")
    assert message.startswith("claude failed: error_max_budget_usd: Exceeded USD budget")
    assert "0.31 USD" in message
    assert "4 turns" in message


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


def test_summary_labels_an_isolated_run():
    out = summary(ARGS, False, "bad", events("recorded-result"), Path("/tmp/cfg"))
    assert out["l1"] == "FAIL"
    assert out["config"] == "isolated"
    assert out["config_dir"] == "/tmp/cfg"
    assert out["helper_calls"] == []
    assert out["single_context"] == "PASS: no helper agents spawned"
