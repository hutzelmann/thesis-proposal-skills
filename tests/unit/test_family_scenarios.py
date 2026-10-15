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
from fixture_paths import fixture_dir
from helpers import CLEAN_DRAFT, FIXTURES

FAMILY_SCENARIOS = ("litsearch_snowball", "write_rename_family", "ideate_seed_rename")
STREAMS = Path(__file__).resolve().parent / "data" / "routing_streams"
LIT_SEED = "serverless-energy-scheduling/serverless-energy-scheduling.md"
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
    """A rename as the block describes it: the folder `<old>/` moves to
    `<new>/`, then `<old>.md` to `<new>.md`; role-named files and figures keep
    their names, so no link changes. `leave` names files left in `<old>/`."""
    for rel in files(ws):
        folder, _, inside = rel.partition("/")
        if folder != old or rel in leave:
            continue
        target = ws / new / (f"{new}.md" if inside == f"{old}.md" else inside)
        target.parent.mkdir(parents=True, exist_ok=True)
        (ws / rel).rename(target)
    for directory in sorted((p for p in (ws / old).rglob("*") if p.is_dir()), reverse=True):
        if not any(directory.iterdir()):
            directory.rmdir()
    if (ws / old).is_dir() and not any((ws / old).iterdir()):
        (ws / old).rmdir()


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


def test_staging_copies_the_fixture_tree_but_its_oracle_and_its_submission(tmp_path):
    """The fixture is the workspace root (design D24): every folder is staged
    as it lies, and `expected.json` and the import source stay behind."""
    scenario = {"fixture": "f16-figures-import", "skill": "proposal-publish"}
    stage(scenario, tmp_path, install_skill=False)
    assert files(tmp_path) == ["sensor-anomaly-triage/img/a.png", "sensor-anomaly-triage/img/b.png",
                               "sensor-anomaly-triage/sensor-anomaly-triage.md"]
    assert claude_runner.staged_files(scenario) == {
        rel: (tmp_path / rel).read_bytes() for rel in files(tmp_path)}


def test_staging_keeps_hidden_files_and_build_definitions_where_they_lie(tmp_path):
    for fixture, expected in (
            ("w05-workspace-build", "deterministic-container-rebuilds/proposal-build.py"),
            ("w13-orphaned-companions", ".agents/skills/.thesis-proposal-install.json")):
        ws = tmp_path / fixture
        ws.mkdir()
        scenario = {"fixture": fixture, "skill": "proposal-check"}
        stage(scenario, ws, install_skill=False)
        on_disk = {p.relative_to(ws).as_posix(): p.read_bytes() for p in ws.rglob("*")
                   if p.is_file()}
        assert expected in on_disk
        assert claude_runner.staged_files(scenario) == on_disk
        assert "expected.json" not in on_disk


@pytest.mark.parametrize("sources", [
    {"submission.pdf": "submission.pdf"},
    {"ci-repair-agent-configurations.md":
     "ci-repair-agent-configurations/ci-repair-agent-configurations.md"},
])
def test_sources_stage_only_the_files_they_map(sources, tmp_path):
    """`sources` maps workspace names to fixture-relative files: a professor's
    saved submission at the workspace root, or an import's source PDF alone."""
    fixture = "f16-figures-import" if "submission.pdf" in sources else "f28-open-decisions"
    scenario = {"fixture": fixture, "skill": "proposal-import", "sources": sources}
    stage(scenario, tmp_path, install_skill=False)
    assert files(tmp_path) == sorted(sources)
    staged = claude_runner.staged_files(scenario)
    assert staged == {name: (fixture_dir(fixture) / rel).read_bytes()
                      for name, rel in sources.items()}
    assert workspace_changes(scenario, tmp_path) == ([], [])


@pytest.mark.parametrize("name", ["import_messy", "ideate_scoped"])
def test_a_scenario_without_a_fixture_counts_every_file_as_added(name, tmp_path):
    (tmp_path / "soil-irrigation" / "img").mkdir(parents=True)
    (tmp_path / "soil-irrigation" / "soil-irrigation.md").write_text("# T\n", encoding="utf-8")
    (tmp_path / "soil-irrigation" / "img" / "map.png").write_bytes(b"\x89PNG")
    (tmp_path / ".claude" / "skills").mkdir(parents=True)
    (tmp_path / ".claude" / "skills" / "SKILL.md").write_text("installed", encoding="utf-8")
    changed, added = workspace_changes(SCENARIOS[name], tmp_path)
    assert changed == []
    assert added == ["soil-irrigation/img/map.png", "soil-irrigation/soil-irrigation.md"]


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
    for dump in ("serverless-energy-scheduling.candidates.yaml",
                 "serverless-energy-scheduling/candidates.yaml"):
        (ws / dump).write_text("- id: X\n", encoding="utf-8")
        passed, why = verdict("litsearch_snowball", SCENARIOS["litsearch_snowball"], ws, "")
        assert not passed
        assert dump in why
        (ws / dump).unlink()


# ---------- write_rename_family -----------------------------------------------------


def test_rename_passes_when_the_whole_family_moved(tmp_path):
    ws = staged("write_rename_family", tmp_path)
    rename_family(ws, W14, RENAMED)
    passed, why = verdict("write_rename_family", SCENARIOS["write_rename_family"], ws, "")
    assert passed, why
    assert "no companion-orphaned or proposal-folder-mismatch finding" in why


def test_rename_fails_on_a_figure_left_behind(tmp_path):
    ws = staged("write_rename_family", tmp_path)
    rename_family(ws, W14, RENAMED, leave=(f"{W14}/img/pipeline.png",))
    passed, why = verdict("write_rename_family", SCENARIOS["write_rename_family"], ws, "")
    assert not passed
    assert f"{W14}/img/pipeline.png" in why


def test_rename_fails_when_the_check_reports_an_orphan(tmp_path):
    """A review left in the old folder is a leftover and an orphan both."""
    ws = staged("write_rename_family", tmp_path)
    rename_family(ws, W14, RENAMED, leave=(f"{W14}/review.md",))
    passed, why = verdict("write_rename_family", SCENARIOS["write_rename_family"], ws, "")
    assert not passed
    assert f"{W14}/review.md" in why
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
    (ws / SEEDED / f"{SEEDED}.md").write_text(SEED_TEXT, encoding="utf-8")


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
    seed(ws, leave=(f"{W15}/reading-list.md",))
    passed, why = verdict("ideate_seed_rename", SCENARIOS["ideate_seed_rename"], ws, "")
    assert not passed
    assert f"{W15}/reading-list.md" in why


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
    (ws / "drift-detection").mkdir()
    (ws / "drift-detection" / "drift-detection.md").write_text(CLEAN_DRAFT, encoding="utf-8")
    out, status = run_out("write_from_seed", ws)
    assert (out["l1"], status) == ("PASS", EXIT_PASS)
    assert out["family"].startswith("FAIL: ")
    assert "`drift-detection/drift-detection.md`" in out["family"]
    assert "data-drift-detection/data-drift-detection.md" in out["family"]


def test_a_draft_into_its_seed_passes_the_advisory(tmp_path):
    ws = staged("write_from_seed", tmp_path)
    (ws / SCENARIOS["write_from_seed"]["proposal"]).write_text(CLEAN_DRAFT, encoding="utf-8")
    out, _ = run_out("write_from_seed", ws)
    assert out["family"] == "PASS: no file added"


def test_every_other_run_reports_the_advisory(tmp_path):
    ws = staged("check_report", tmp_path)
    (ws / "check-notes.txt").write_text("scratch", encoding="utf-8")
    out, _ = run_out("check_report", ws)
    assert out["family"].startswith("FAIL: ")
    assert "check-notes.txt" in out["family"]


def test_the_advisory_reads_a_review_as_the_check_does(tmp_path):
    """A review written into a folder that holds no proposal, notes file or
    harvest record is the orphan the check would report (testing-harness:
    Review written under a wrong slug)."""
    ws = staged("check_report", tmp_path)
    (ws / "broken-formats").mkdir()
    (ws / "broken-formats" / "review.md").write_text("Verdict: revise.\n", encoding="utf-8")
    out, _ = run_out("check_report", ws)
    assert out["family"].startswith("FAIL: ")
    assert "broken-formats/review.md" in out["family"]
