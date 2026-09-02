"""L0: the dev runner's cost and helper-agent probe (testing-harness spec:
Dev-runner cost and helper-agent telemetry).

The probe reads the host's stream-json events. Everything here runs against
recorded or synthetic streams under `data/routing_streams/`, so a host output
change fails these tests instead of silently blanking the telemetry line.
"""

import json
from pathlib import Path

from claude_runner import final_text, parse_events, telemetry
from l1_checks import HELPER_TOOLS, verdict_single_context
from routing import tool_calls

STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"


def events(name: str) -> list[dict]:
    lines = (STREAMS / f"{name}.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def names(name: str) -> list[str]:
    return [tool for tool, _ in tool_calls(events(name))]


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


def test_parse_events_skips_non_json_lines():
    stdout = '{"type":"system"}\nnot json\n\n{"type":"result","result":"done"}\n'
    assert [e["type"] for e in parse_events(stdout)] == ["system", "result"]


def test_final_text_prefers_the_result_event():
    assert final_text(events("helper-fanout")) == "Reviewed; findings written."


def test_final_text_falls_back_to_assistant_text():
    stream = [
        {"type": "assistant", "message": {"content": [
            {"type": "text", "text": "first"},
            {"type": "tool_use", "name": "Read", "input": {}},
        ]}},
        {"type": "assistant", "message": {"content": [{"type": "text", "text": "second"}]}},
    ]
    assert final_text(stream) == "first\nsecond"


def test_telemetry_reads_the_result_event():
    assert telemetry(events("helper-fanout")) == {
        "cost_usd": 0.42, "num_turns": 7, "duration_ms": 61000,
        "tokens_in": 1200, "tokens_out": 350,
        "tokens_cache_read": 9000, "tokens_cache_write": 300,
    }


def test_telemetry_is_none_without_a_result_event():
    assert telemetry(events("unrouted-explore")) == {
        "cost_usd": None, "num_turns": None, "duration_ms": None,
        "tokens_in": None, "tokens_out": None,
        "tokens_cache_read": None, "tokens_cache_write": None,
    }
