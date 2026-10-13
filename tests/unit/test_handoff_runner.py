"""L0: the dev runner's follow-up turns and handoff scenarios (testing-harness
spec: handoff coverage). No host runs: `run_claude` is replaced by a fake that
answers each turn with a scripted stream and writes what the model would have.
"""

import argparse
import json
import shutil
from pathlib import Path

import claude_runner
import pytest
from claude_runner import (
    EXIT_FAIL,
    EXIT_PASS,
    EXIT_RUNNER,
    SCENARIOS,
    RunnerFailure,
    follow_up,
    host_command,
    l2_artifact,
    main,
    save_events,
    session_id,
    summary,
    telemetry,
    transcript,
    turn_texts,
    workspace_changes,
)
from helpers import FIXTURES, REPO

HANDOFF_SCENARIOS = sorted(name for name, s in SCENARIOS.items() if s.get("handoff"))
ARGS = argparse.Namespace(scenario="check_report", model="haiku", no_skill=False,
                          timeout=60, max_budget_usd=None)

SUPERSEDED_CHAT = (
    "Check: 0 errors.\n\n"
    "Where it stands: complete draft; the review on file judged the earlier, broader version.\n"
    'Next: a fresh review of the narrowed draft. Reply "yes", or send: "Review my proposal."\n'
)
WHAT_NOW_CHAT = (
    "One revision of the two blockers, then one fresh review.\n\n"
    "Where it stands: needs revision, two blockers.\n"
    'Next: work the two blockers into the draft. Send: "Apply the two blockers."\n'
)


def stream(text: str, session: str | None = "sess-1") -> list[dict]:
    init = {"type": "system", "subtype": "init", "model": "claude-fixture-1-0",
            "apiKeySource": "none", "claude_code_version": "2.1.284"}
    if session:
        init["session_id"] = session
    return [init,
            {"type": "rate_limit_event", "rate_limit_info": {
                "status": "allowed", "rateLimitType": "five_hour", "utilization": 0.2,
                "isUsingOverage": False}},
            {"type": "result", "subtype": "success", "is_error": False, "result": text,
             "total_cost_usd": 0.25, "num_turns": 4, "duration_ms": 30000,
             "usage": {"input_tokens": 10, "output_tokens": 400,
                       "cache_read_input_tokens": 2000, "cache_creation_input_tokens": 300},
             "modelUsage": {"claude-fixture-1-0": {"outputTokens": 400,
                                                   "provider": "firstParty"}}}]


def fake_turns(monkeypatch, turns: list[tuple[str, object]]) -> list[dict]:
    """Each call answers with the next scripted (chat, produce) pair; `produce`
    writes into the workspace what the model would have."""
    calls: list[dict] = []
    script = iter(turns)

    def run_claude(ws, request, _model, _timeout, budget=None, resume=None, **_rest):
        calls.append({"request": request, "resume": resume, "budget": budget})
        chat, produce = next(script)
        if produce:
            produce(ws)
        return stream(chat, resume or "sess-1")

    monkeypatch.setattr(claude_runner, "run_claude", run_claude)
    return calls


# ---------- the host invocation and the stream helpers -------------------------


def test_host_command_resumes_only_when_asked():
    assert "--resume" not in host_command("hi", "haiku")
    command = host_command("What now?", "haiku", budget=2.0, resume="sess-1")
    assert command[command.index("--resume") + 1] == "sess-1"
    assert command[command.index("--max-budget-usd") + 1] == "2.0"


def test_session_id_is_the_latest_turns():
    assert session_id(stream("a", "first") + stream("b", "second")) == "second"
    assert session_id(stream("a", None)) is None


def test_turn_texts_and_transcript_pair_each_question_with_its_answer():
    events = stream("review written") + stream("one revision, one review")
    scenario = {"request": "Review it.", "followups": ("What now?",)}
    assert turn_texts(events) == ["review written", "one revision, one review"]
    assert transcript(scenario, events) == (
        "USER: Review it.\n\nASSISTANT: review written\n\n"
        "USER: What now?\n\nASSISTANT: one revision, one review")


def skill_call(name: str) -> dict:
    return {"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Skill", "input": {"skill": name}}]}}


def test_skills_invoked_counts_only_the_turns_after_the_first():
    first = stream("status")
    first.insert(1, skill_call("proposal-check"))
    second = stream("revised")
    second.insert(1, skill_call("proposal-write"))
    assert claude_runner.skills_invoked(first + second) == ["proposal-check", "proposal-write"]
    assert claude_runner.skills_invoked(first + second, 1) == ["proposal-write"]


def test_telemetry_sums_per_turn_figures_and_keeps_the_running_cost():
    """`total_cost_usd` is the session's running total in a resumed turn, so
    the last one is the cost; turns, duration and tokens are per turn."""
    first, second = stream("a"), stream("b")
    second[-1]["total_cost_usd"] = 0.30  # 0.25 so far, plus 0.05 for the follow-up
    one = telemetry(first)
    two = telemetry(first + second)
    assert "conversation_turns" not in one
    assert two["conversation_turns"] == 2
    assert two["cost_usd"] == pytest.approx(0.30)
    assert two["num_turns"] == 2 * one["num_turns"]
    assert two["tokens_cache_read"] == 2 * one["tokens_cache_read"]


# ---------- follow-up turns ----------------------------------------------------


def test_follow_up_sends_each_turn_to_the_first_turns_session(monkeypatch, tmp_path):
    calls = fake_turns(monkeypatch, [("the reply", None)])
    scenario = {"followups": ("What now?",)}
    events = follow_up(ARGS, scenario, tmp_path, stream("first", "sess-9"), None)
    assert calls == [{"request": "What now?", "resume": "sess-9", "budget": None}]
    assert turn_texts(events) == ["first", "the reply"]


def test_follow_up_without_a_session_id_is_a_runner_failure(monkeypatch, tmp_path):
    fake_turns(monkeypatch, [])
    with pytest.raises(RunnerFailure, match="session id") as raised:
        follow_up(ARGS, {"followups": ("What now?",)}, tmp_path, stream("a", None), None)
    assert raised.value.status == EXIT_RUNNER
    assert turn_texts(raised.value.events) == ["a"]


def test_a_follow_up_that_opened_another_session_is_a_runner_failure(monkeypatch, tmp_path):
    def run_claude(*_args, **_kwargs):
        return stream("a fresh conversation", "sess-other")

    monkeypatch.setattr(claude_runner, "run_claude", run_claude)
    with pytest.raises(RunnerFailure, match="not the resumed 'sess-1'") as raised:
        follow_up(ARGS, {"followups": ("What now?",)}, tmp_path, stream("first"), None)
    assert turn_texts(raised.value.events) == ["first", "a fresh conversation"]


def test_a_failed_follow_up_keeps_the_earlier_turns_events(monkeypatch, tmp_path):
    def run_claude(*_args, **_kwargs):
        raise RunnerFailure("host crashed", events=stream("partial"))

    monkeypatch.setattr(claude_runner, "run_claude", run_claude)
    with pytest.raises(RunnerFailure) as raised:
        follow_up(ARGS, {"followups": ("What now?",)}, tmp_path, stream("first"), None)
    assert turn_texts(raised.value.events) == ["first", "partial"]


def test_a_scenario_without_follow_ups_is_untouched(monkeypatch, tmp_path):
    calls = fake_turns(monkeypatch, [])
    events = stream("only")
    assert follow_up(ARGS, {}, tmp_path, events, None) is events
    assert calls == []


# ---------- the advisory probe -------------------------------------------------


def test_every_summary_reports_the_handoff_without_judging_it():
    out = summary(ARGS, True, "fine", stream("Report done."), None)
    assert out["l1"] == "PASS"
    assert out["handoff"].startswith("FAIL: the chat does not close with handoff lines")
    assert summary(ARGS, True, "fine", stream(SUPERSEDED_CHAT), None)["handoff"].startswith(
        "PASS")


# ---------- workspace changes and the scenarios ----------------------------------


def staged(tmp_path: Path, fixture: str) -> Path:
    for f in (FIXTURES / fixture).iterdir():
        if f.is_file() and f.suffix in (".md", ".txt"):
            shutil.copy(f, tmp_path / f.name)
    return tmp_path


def test_workspace_changes_ignore_the_harness_and_interpreter_files(tmp_path):
    ws = staged(tmp_path, "w10-narrowed-scope")
    (ws / ".claude" / "skills" / "x" / "__pycache__").mkdir(parents=True)
    (ws / ".claude" / "skills" / "x" / "__pycache__" / "c.pyc").write_bytes(b"")
    (ws / ".devrun-events.jsonl").write_text("{}\n", encoding="utf-8")
    scenario = SCENARIOS["handoff_superseded"]
    assert workspace_changes(scenario, ws) == ([], [])
    (ws / "ci-repair-agent-configurations-review.md").write_text("new", encoding="utf-8")
    (ws / "ci-repair-agent-configurations.pdf").write_bytes(b"%PDF")
    assert workspace_changes(scenario, ws) == (["ci-repair-agent-configurations-review.md"],
                                               ["ci-repair-agent-configurations.pdf"])


def test_every_handoff_scenario_installs_the_full_set():
    every = sorted(d.name for d in (REPO / "skills").iterdir()
                   if d.is_dir() and d.name.startswith("proposal-"))
    for name in HANDOFF_SCENARIOS:
        scenario = SCENARIOS[name]
        assert sorted([scenario["skill"], *scenario["siblings"]]) == every, name


def test_the_incidents_follow_up_is_scripted():
    assert SCENARIOS["handoff_review_feedback"]["followups"] == (
        "What do we do now with that feedback?",)


def write_review(ws: Path) -> None:
    (ws / "microservice-technical-debt-review.md").write_text(
        "**Verdict: needs revision**\n", encoding="utf-8")


def test_review_then_what_now_passes_end_to_end(monkeypatch, tmp_path):
    calls = fake_turns(monkeypatch, [("Review written.", write_review),
                                     (WHAT_NOW_CHAT, None)])
    log = tmp_path / "log.jsonl"
    assert main(["handoff_review_feedback", "--summary-log", str(log)]) == EXIT_PASS
    assert [c["resume"] for c in calls] == [None, "sess-1"]
    line = json.loads(log.read_text(encoding="utf-8"))
    assert line["conversation_turns"] == 2
    assert line["handoff"].startswith("PASS")


def test_a_revision_started_unasked_fails_the_scenario(monkeypatch):
    def edit(ws: Path) -> None:
        path = ws / "microservice-technical-debt.md"
        path.write_text(path.read_text(encoding="utf-8") + "\nEdited.\n", encoding="utf-8")

    fake_turns(monkeypatch, [("Review written.", write_review), (WHAT_NOW_CHAT, edit)])
    assert main(["handoff_review_feedback"]) == EXIT_FAIL


@pytest.mark.parametrize(("scenario", "chat", "status"), [
    ("handoff_superseded", SUPERSEDED_CHAT, EXIT_PASS),
    ("handoff_superseded", "Where it stands: no current review exists.\n"
                           "Next: decide what to do.\n", EXIT_FAIL),
    ("handoff_todos", SUPERSEDED_CHAT, EXIT_PASS),
])
def test_status_scenarios(scenario, chat, status, monkeypatch):
    fake_turns(monkeypatch, [(chat, None)])
    assert main([scenario]) == status


REVISED_CHAT = (
    "Rewrote the RQ3 passage.\n\n"
    "Where it stands: the blocker's passage changed, so the review on file describes an "
    "earlier text.\n"
    'Next: a fresh review of the changed text. Send: "Review my proposal again."\n'
)


def revise(ws: Path) -> None:
    path = ws / "ci-repair-agent-configurations.md"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.replace("still to be negotiated with the company",
                                 "confirmed in writing by the company"), encoding="utf-8")


def fake_direct(monkeypatch, *, load_write: bool) -> None:
    def run_claude(ws, _request, _model, _timeout, **_rest):
        revise(ws)
        events = stream(REVISED_CHAT)
        if load_write:
            events.insert(1, skill_call("proposal-write"))
        return events

    monkeypatch.setattr(claude_runner, "run_claude", run_claude)


def test_a_cold_revision_under_the_writing_skill_passes(monkeypatch):
    """The direct request has no status turn: its own edits are the revision."""
    fake_direct(monkeypatch, load_write=True)
    assert main(["handoff_direct_revision"]) == EXIT_PASS


def test_a_cold_revision_as_a_bare_edit_fails(monkeypatch, capsys):
    fake_direct(monkeypatch, load_write=False)
    assert main(["handoff_direct_revision"]) == EXIT_FAIL
    assert "without the writing skill" in capsys.readouterr().out


def test_the_judge_reads_the_saved_conversation(tmp_path):
    scenario = SCENARIOS["handoff_review_feedback"]
    save_events(stream("Review written.") + stream(WHAT_NOW_CHAT), tmp_path)
    artifact = l2_artifact("handoff_review_feedback", scenario, tmp_path)
    assert artifact.startswith("USER: Please review my proposal")
    assert "USER: What do we do now with that feedback?" in artifact
    assert artifact.endswith(WHAT_NOW_CHAT)
