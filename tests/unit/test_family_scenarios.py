"""L0: the dev runner's proposal-family scenarios and its advisory `family`
field (testing-harness: Proposal-family coverage), with no model.

The three scenarios judge family-only as part of their L1 verdict; every other
run reports it beside `single_context` and `handoff`, where it never changes the
pass flag or the exit status. After-states are written by hand into a staged
workspace; the check script runs for real.
"""

import argparse
import json
from pathlib import Path

import claude_runner
import pytest
from claude_runner import (
    DRAFT_SCENARIOS,
    EXIT_PASS,
    SCENARIOS,
    completed_run,
    stage,
    verdict,
    workspace_changes,
)
from helpers import CLEAN_DRAFT, FIXTURES

FAMILY_SCENARIOS = ("litsearch_snowball", "write_rename_family", "ideate_seed_rename")
STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"
LIT_SEED = "serverless-energy-scheduling.md"
W14 = "ci-repair-agent-configurations"
W15 = "flaky-ci-triage"
SEEDED = "flaky-failure-triage"
RENAMED = "context-repair-agents"


def staged(name: str, ws: Path) -> Path:
    stage(SCENARIOS[name], ws, install_skill=False)
    return ws


def recorded_events() -> list[dict]:
    lines = (STREAMS / "recorded-result.jsonl").read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines if line.strip()]


def run_out(name: str, ws: Path) -> tuple[dict, int]:
    args = argparse.Namespace(scenario=name, model="haiku", no_skill=False)
    return completed_run(args, None, SCENARIOS[name], ws, SCENARIOS[name]["request"],
                         recorded_events(), None)


def files(ws: Path) -> list[str]:
    return sorted(p.relative_to(ws).as_posix() for p in ws.rglob("*")
                  if p.is_file() and not any(part.startswith(".")
                                             for part in p.relative_to(ws).parts))


def rename_family(ws: Path, old: str, new: str, leave: tuple[str, ...] = ()) -> None:
    """A rename as the block describes it: every family file, figures included,
    and the figure links in the proposal and its notes file."""
    for rel in files(ws):
        if rel in leave:
            continue
        if rel.startswith(f"img/{old}-"):
            (ws / rel).rename(ws / "img" / (new + rel[len("img/") + len(old):]))
        elif rel.startswith((f"{old}.", f"{old}-")):
            (ws / rel).rename(ws / (new + rel[len(old):]))
    for name in (f"{new}.md", f"{new}.notes.md"):
        if (path := ws / name).exists():
            text = path.read_text(encoding="utf-8")
            path.write_text(text.replace(f"img/{old}-", f"img/{new}-"), encoding="utf-8")


# ---------- the scenarios and their fixtures ----------------------------------------


@pytest.mark.parametrize("name", FAMILY_SCENARIOS)
def test_the_scenario_exists_and_its_fixture_stages(name, tmp_path):
    scenario = SCENARIOS[name]
    fixture = FIXTURES / scenario["fixture"]
    assert fixture.is_dir()
    ws = staged(name, tmp_path)
    assert files(ws), f"{name}: nothing staged"
    assert workspace_changes(scenario, ws) == ([], [])
    assert "keep" not in scenario["request"].lower()


@pytest.mark.parametrize("name", ["import_messy", "ideate_scoped"])
def test_a_scenario_without_a_fixture_counts_every_file_as_added(name, tmp_path):
    (tmp_path / "img").mkdir()
    (tmp_path / "soil-irrigation.md").write_text("# T\n", encoding="utf-8")
    (tmp_path / "img" / "soil-irrigation-map.png").write_bytes(b"\x89PNG")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    (tmp_path / ".claude" / "skills" / "SKILL.md").write_text("installed", encoding="utf-8")
    changed, added = workspace_changes(SCENARIOS[name], tmp_path)
    assert changed == []
    assert added == ["img/soil-irrigation-map.png", "soil-irrigation.md"]


# ---------- litsearch_snowball ------------------------------------------------------


def merge_one_reference(ws: Path) -> None:
    path = ws / LIT_SEED
    before, after = path.read_text(encoding="utf-8").rsplit("---", 1)
    entry = ("- id: Musterfrau26Synthetic\n  type: article-journal\n"
             "  title: A Synthetic Neighbour\n  DOI: 10.1/synthetic-neighbour\n")
    path.write_text(f"{before}{entry}---{after}", encoding="utf-8")


def test_snowball_passes_on_a_merged_reference_and_fails_on_a_dump(tmp_path):
    ws = staged("litsearch_snowball", tmp_path)
    passed, why = verdict("litsearch_snowball", SCENARIOS["litsearch_snowball"], ws, "")
    assert not passed
    assert "still only 3 references" in why
    merge_one_reference(ws)
    passed, why = verdict("litsearch_snowball", SCENARIOS["litsearch_snowball"], ws, "")
    assert passed, why
    dump = "serverless-energy-scheduling.candidates.yaml"
    (ws / dump).write_text("- id: X\n", encoding="utf-8")
    passed, why = verdict("litsearch_snowball", SCENARIOS["litsearch_snowball"], ws, "")
    assert not passed
    assert dump in why


# ---------- write_rename_family -----------------------------------------------------


def test_rename_passes_when_the_whole_family_moved(tmp_path):
    ws = staged("write_rename_family", tmp_path)
    rename_family(ws, W14, RENAMED)
    passed, why = verdict("write_rename_family", SCENARIOS["write_rename_family"], ws, "")
    assert passed, why
    assert "no companion-orphaned finding" in why


def test_rename_fails_on_a_figure_left_behind(tmp_path):
    ws = staged("write_rename_family", tmp_path)
    rename_family(ws, W14, RENAMED, leave=(f"img/{W14}-pipeline.png",))
    passed, why = verdict("write_rename_family", SCENARIOS["write_rename_family"], ws, "")
    assert not passed
    assert f"img/{W14}-pipeline.png" in why


def test_rename_fails_when_the_check_reports_an_orphan(tmp_path):
    """A review left under the old slug is a leftover and an orphan both."""
    ws = staged("write_rename_family", tmp_path)
    rename_family(ws, W14, RENAMED, leave=(f"{W14}-review.md",))
    passed, why = verdict("write_rename_family", SCENARIOS["write_rename_family"], ws, "")
    assert not passed
    assert f"{W14}-review.md" in why
    assert "companion-orphaned" in why


def test_rename_fails_when_the_check_did_not_run(tmp_path, monkeypatch):
    """An absent orphan finding is no evidence when the check crashed."""
    crash = tmp_path / "crash.py"
    crash.write_text("raise SystemExit('Traceback: the check crashed')\n", encoding="utf-8")
    monkeypatch.setattr(claude_runner, "CHECK", crash)
    ws = tmp_path / "ws"
    ws.mkdir()
    staged("write_rename_family", ws)
    rename_family(ws, W14, RENAMED)
    passed, why = verdict("write_rename_family", SCENARIOS["write_rename_family"], ws, "")
    assert not passed
    assert "did not run" in why
    assert "the check crashed" in why


def test_a_title_change_without_a_rename_fails(tmp_path):
    ws = staged("write_rename_family", tmp_path)
    passed, why = verdict("write_rename_family", SCENARIOS["write_rename_family"], ws, "")
    assert not passed
    assert "no proposal under a new slug" in why


# ---------- ideate_seed_rename ------------------------------------------------------


SEED_TEXT = ("# Separating Flaky Failures from Regressions in Continuous Integration\n\n"
             "*Master's Thesis Proposal*\n\nA sketch.\n\n## References\n\n"
             "---\nreferences: []\n---\n")


def seed(ws: Path, leave: tuple[str, ...] = ()) -> None:
    rename_family(ws, W15, SEEDED, leave=leave)
    (ws / f"{SEEDED}.md").write_text(SEED_TEXT, encoding="utf-8")


def test_seeding_passes_when_the_provisional_family_moved(tmp_path):
    ws = staged("ideate_seed_rename", tmp_path)
    seed(ws)
    passed, why = verdict("ideate_seed_rename", SCENARIOS["ideate_seed_rename"], ws, "")
    assert passed, why
    out, status = run_out("ideate_seed_rename", ws)
    assert (out["l1"], status) == ("PASS", EXIT_PASS)
    assert "family" not in out  # part of the verdict here, not an advisory


def test_seeding_fails_on_a_kept_file_left_under_the_provisional_slug(tmp_path):
    ws = staged("ideate_seed_rename", tmp_path)
    seed(ws, leave=(f"{W15}.reading-list.md",))
    passed, why = verdict("ideate_seed_rename", SCENARIOS["ideate_seed_rename"], ws, "")
    assert not passed
    assert f"{W15}.reading-list.md" in why


def test_seeding_fails_without_a_seed(tmp_path):
    ws = staged("ideate_seed_rename", tmp_path)
    passed, why = verdict("ideate_seed_rename", SCENARIOS["ideate_seed_rename"], ws, "")
    assert not passed
    assert "no proposal under a new slug" in why
    assert "no seeded proposal file" in why


# ---------- the advisory family field -----------------------------------------------


def test_a_draft_beside_its_seed_fails_the_advisory_and_keeps_the_l1_verdict(tmp_path):
    assert "write_from_seed" in DRAFT_SCENARIOS
    ws = staged("write_from_seed", tmp_path)
    (ws / "drift-detection.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    out, status = run_out("write_from_seed", ws)
    assert (out["l1"], status) == ("PASS", EXIT_PASS)
    assert out["family"].startswith("FAIL: ")
    assert "drift-detection.md" in out["family"]
    assert "data-drift-detection.md" in out["family"]


def test_a_draft_into_its_seed_passes_the_advisory(tmp_path):
    ws = staged("write_from_seed", tmp_path)
    (ws / "data-drift-detection.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    out, _ = run_out("write_from_seed", ws)
    assert out["family"] == "PASS: no file added"


def test_every_other_run_reports_the_advisory(tmp_path):
    ws = staged("check_report", tmp_path)
    (ws / "check-notes.txt").write_text("scratch", encoding="utf-8")
    out, _ = run_out("check_report", ws)
    assert out["family"].startswith("FAIL: ")
    assert "check-notes.txt" in out["family"]


def test_the_advisory_reads_a_review_as_the_check_does(tmp_path):
    """A review written under a slug no proposal carries, without a metadata
    block, is the orphan the check would report, not a proposal of its own."""
    ws = staged("check_report", tmp_path)
    (ws / "broken-formats-review.md").write_text("Verdict: revise.\n", encoding="utf-8")
    out, _ = run_out("check_report", ws)
    assert out["family"].startswith("FAIL: ")
    assert "broken-formats-review.md" in out["family"]
