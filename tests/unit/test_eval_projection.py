"""L0: the per-skill `evals/evals.json` projections match the harness.

The projection (standard-conformance spec) is generated, never authored: these
tests regenerate it in memory and compare byte-for-byte, so a harness change
that forgets to rerun the export — or a hand edit to a projection — fails here
rather than shipping a stale or forked eval definition.
"""

from __future__ import annotations

import json

import eval_export
import pytest
from helpers import REPO

SKILLS = REPO / "skills"


@pytest.fixture(scope="module")
def projections() -> dict[str, dict]:
    return eval_export.export_evals()


def test_every_skill_carries_a_projection(projections):
    skills = {d.name for d in SKILLS.iterdir() if d.is_dir() and d.name.startswith("proposal-")}
    assert set(projections) == skills


def test_committed_projections_match_the_harness(projections):
    stale = [
        skill for skill, doc in projections.items()
        if (SKILLS / skill / "evals" / "evals.json").read_text(encoding="utf-8")
        != eval_export.render(doc)
    ]
    assert not stale, (
        f"stale evals.json for {stale} — edit the harness, then run: "
        "uv run python harness/eval_export.py"
    )


def test_projection_speaks_the_standard_shape(projections):
    for skill, doc in projections.items():
        assert doc["skill_name"] == skill
        assert doc["evals"], f"{skill}: no evals exported"
        for entry in doc["evals"]:
            assert entry["prompt"].strip(), f"{skill}/{entry['task']}: empty prompt"
            assert entry["expected_output"].strip()
            assert entry["assertions"], f"{skill}/{entry['task']}: no assertions"


def test_the_ideate_dialogues_project_no_workspace_file(projections):
    """The dialogues start from an empty workspace, so their input files are
    none: the projection must not list a proposal the run never sees, as it
    did once the dialogue's emptying setup changed under the folder layout."""
    entries = projections["proposal-ideate"]["evals"]
    dialogues = [e for e in entries if e["prompt"] == entries[0]["prompt"]]
    assert len(dialogues) == 5
    assert {e["task"]: e["files"] for e in dialogues} == {e["task"]: [] for e in dialogues}


def test_the_projection_lists_workspace_files_not_the_installed_skill(projections):
    """A task's files are the workspace it starts from, by their path from the
    workspace root; the skill's own scripts and references are not inputs."""
    for skill, doc in projections.items():
        for entry in doc["evals"]:
            for name in entry["files"]:
                assert not name.startswith(("ws/", "skill/", ".claude/skills/")), (
                    f"{skill}/{entry['task']}: {name}")


def test_check_mode_reports_clean(capsys):
    assert eval_export.main(["--check"]) == 0
    assert "drift" not in capsys.readouterr().out


def test_projection_files_are_valid_json():
    for path in sorted(SKILLS.glob("proposal-*/evals/evals.json")):
        json.loads(path.read_text(encoding="utf-8"))
