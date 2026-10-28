"""L0: the novice ideation replay (testing-harness spec: Novice ideation dev
scenario; open-ideation-before-challenge, design D7, D8). No host runs: the
saved event streams are written by hand, as a run would leave them.
"""

from pathlib import Path

import l2_rubrics
from claude_runner import (
    NO_FILE,
    SCENARIOS,
    judge_criteria,
    l2_artifact,
    save_events,
    shown_turn_texts,
    transcript,
    verdict,
)
from helpers import NOTES_TEXT
from l1_checks import verdict_ideate_novice

NOVICE = SCENARIOS["ideate_novice"]
SEED = ("# Driver Knowledge in Route Planning\n\n*Master's Thesis Proposal*\n\nA sketch.\n\n"
        "## References\n\n---\nreferences: []\n---\n")


def turn(*texts: str) -> list[dict]:
    """One turn as the host streams it: each text in an assistant event of its
    own, with a tool call between them, then the result repeating the last."""
    events = []
    for text in texts:
        events.append({"type": "assistant", "message": {"content": [{"type": "text",
                                                                        "text": text}]}})
        events.append({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Write", "input": {"file_path": "idea/notes.md"}}]}})
    return [*events, {"type": "result", "subtype": "success", "result": texts[-1]}]


def write_files(ws: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        (ws / rel).parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).write_text(text, encoding="utf-8")


def test_the_scenario_is_a_staged_nothing_dialogue_with_lookups_declined():
    assert NOVICE["skill"] == "proposal-ideate"
    assert NOVICE["dialogue"] is True
    assert "fixture" not in NOVICE
    assert "don't look anything up online" in NOVICE["request"]
    assert "Don't write anything into a guidelines.md" in NOVICE["request"]
    followups = NOVICE["followups"]
    assert 4 <= len(followups) <= 5
    assert "don't know" in followups[-2]
    assert "stop for today" in followups[-1]


def test_shown_turn_texts_keep_every_text_a_turn_showed():
    events = turn("What happened the last time?", "Noted.") + turn("Only one.")
    assert shown_turn_texts(events) == ["What happened the last time?\n\nNoted.", "Only one."]


def test_a_dialogue_transcript_carries_every_shown_text_and_a_handoff_only_the_last():
    events = turn("What happened the last time?", "Noted.")
    assert "What happened the last time?" in transcript(NOVICE, events)
    handoff = SCENARIOS["handoff_ready"]
    assert transcript(handoff, events) == f"USER: {handoff['request']}\n\nASSISTANT: Noted."


def test_the_answer_is_the_seed_or_no_file_and_nothing_without_a_conversation(tmp_path):
    assert l2_artifact("ideate_novice", NOVICE, tmp_path) is None
    save_events(turn("What happened the last time?"), tmp_path)
    write_files(tmp_path, {"idea/notes.md": NOTES_TEXT})
    assert l2_artifact("ideate_novice", NOVICE, tmp_path) == NO_FILE
    write_files(tmp_path, {"driver-knowledge/driver-knowledge.md": SEED})
    assert l2_artifact("ideate_novice", NOVICE, tmp_path) == SEED


def test_the_judge_reads_the_transcript_as_the_question(tmp_path):
    save_events(turn("What did the tool actually do?") + turn("People usually show this by "
                                                               "asking, watching or testing."),
                tmp_path)
    criteria, not_judged = judge_criteria("ideate_novice", NOVICE, tmp_path, NOVICE["request"])
    assert not not_judged
    [criterion] = criteria
    assert criterion.name == "ideate_novice_l2"
    assert f"[Transcript]: USER: {NOVICE['request']}" in criterion.prompt
    assert f"USER: {NOVICE['followups'][0]}" in criterion.prompt
    assert f"[Final seeded file]: {NO_FILE}" in criterion.prompt
    assert l2_rubrics.CRITERIA[("ideate_novice", "ideate_novice_l2")] in criterion.prompt


def test_a_saved_session_passes_whether_or_not_it_seeded():
    files = {"idea/notes.md": NOTES_TEXT}
    passed, why = verdict_ideate_novice(sorted(files), files.get)
    assert passed, why
    assert "`idea/notes.md`" in why
    files = {"driver-knowledge/notes.md": NOTES_TEXT,
             "driver-knowledge/driver-knowledge.md": SEED}
    passed, why = verdict_ideate_novice(sorted(files), files.get)
    assert passed, why


def test_a_session_without_one_notes_file_fails():
    passed, why = verdict_ideate_novice([], {}.get)
    assert not passed
    assert "0 notes files" in why
    files = {"idea/notes.md": NOTES_TEXT, "driver-knowledge/notes.md": NOTES_TEXT}
    passed, why = verdict_ideate_novice(sorted(files), files.get)
    assert not passed
    assert "2 notes files" in why


def test_a_declined_guidelines_note_or_a_stray_file_fails():
    files = {"idea/notes.md": NOTES_TEXT, "guidelines.md": "Program: M.Sc.\n"}
    passed, why = verdict_ideate_novice(sorted(files), files.get)
    assert not passed
    assert "`guidelines.md`" in why
    files = {"idea/notes.md": NOTES_TEXT, "transcript-dump.txt": "raw"}
    passed, why = verdict_ideate_novice(sorted(files), files.get)
    assert not passed
    assert "transcript-dump.txt" in why


def test_the_runner_routes_the_scenario_to_its_verdict(tmp_path):
    write_files(tmp_path, {"idea/notes.md": NOTES_TEXT})
    passed, why = verdict("ideate_novice", NOVICE, tmp_path, "")
    assert passed, why
