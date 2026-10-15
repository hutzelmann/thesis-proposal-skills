"""L0: every fixture's mechanical oracle holds against the check script.

The fixture corpus is executable ground truth (testing-harness spec): each
fixture directory carries expected.json pinning the check verdict. Semantic
expectations in the oracles are consumed by L2, not here.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from fixture_paths import FIXTURES, fixture_proposals

REPO = Path(__file__).resolve().parents[2]
CHECK = REPO / "skills" / "proposal-check" / "scripts" / "check.py"

# the corpus walker's own fixture set: test_fixture_paths.py holds
# corpus_proposals() to one proposal per oracle, and fixture_proposals() is how
# it finds each — in a folder, or under the `proposals/` location w07 configures
ORACLES = sorted(FIXTURES.glob("*/expected.json"))


def fixture_id(path: Path) -> str:
    return path.parent.name


METADATA = "# T\n\n---\nreferences:\n---\n"


def put(root: Path, rel: str, text: str = METADATA) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def found(root: Path) -> list[str]:
    return [p.relative_to(root).as_posix() for p in fixture_proposals(root)]


def test_a_review_beside_its_proposal_is_not_a_proposal(tmp_path: Path):
    """w09 stages an earlier round's `review.md` in the folder; a proposal
    whose own slug ends in `-review` (f00) is still its folder's own."""
    put(tmp_path, "ml-code-review/ml-code-review.md")
    put(tmp_path, "agents/agents.md")
    put(tmp_path, "agents/review.md", "Verdict\n")
    assert found(tmp_path) == ["agents/agents.md", "ml-code-review/ml-code-review.md"]


def test_a_folder_a_rename_left_behind_holds_no_proposal(tmp_path: Path):
    """w13 carries a review and a figure in the folder of an earlier slug,
    and a flat proposal at its root: neither is the fixture's proposal."""
    put(tmp_path, "new-title/new-title.md")
    put(tmp_path, "old-title/review.md", "Verdict: revise.\n")
    put(tmp_path, "old-title/feedback.md", "Dear student\n")
    put(tmp_path, "stray.md")
    assert found(tmp_path) == ["new-title/new-title.md"]


def test_a_kept_markdown_file_is_not_a_proposal(tmp_path: Path):
    """w15 keeps a reading list beside its notes and has no proposal at all."""
    put(tmp_path, "flaky-ci/notes.md", "# Notes\n")
    put(tmp_path, "flaky-ci/reading-list.md")
    assert fixture_proposals(tmp_path) == []


def test_a_previous_handout_is_not_a_proposal_although_it_ends_in_a_block(tmp_path: Path):
    put(tmp_path, "new-title/new-title.md")
    put(tmp_path, "new-title/old-title.handout.md")
    assert found(tmp_path) == ["new-title/new-title.md"]


@pytest.mark.parametrize("oracle_path", ORACLES, ids=fixture_id)
def test_oracle_holds(oracle_path: Path):
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    proposals = fixture_proposals(oracle_path.parent)
    assert len(proposals) == 1, f"expected exactly one proposal md in {oracle_path.parent}"
    # the fixture directory is the workspace root: the check's guidelines
    # chain ends at the working directory, which is where w07 keeps its file
    result = subprocess.run(
        [sys.executable, str(CHECK), str(proposals[0])], capture_output=True, encoding="utf-8",
        cwd=oracle_path.parent,
    )
    expected = oracle["check"]
    assert result.returncode == expected["exit_code"], result.stdout

    error_lines = [ln for ln in result.stdout.splitlines() if ln.startswith("- ERROR:")]
    warning_lines = [ln for ln in result.stdout.splitlines() if ln.startswith("- WARNING:")]

    for needle in expected["errors_contain"]:
        assert any(needle in ln for ln in error_lines), (
            f"missing error `{needle}`\n{result.stdout}"
        )
    for needle in expected["warnings_contain"]:
        assert any(needle in ln for ln in warning_lines), (
            f"missing warning `{needle}`\n{result.stdout}"
        )
    # completeness: every actual error must be pinned by the oracle
    for line in error_lines:
        assert any(n in line for n in expected["errors_contain"]), f"unpinned error: {line}"


@pytest.mark.parametrize("oracle_path", ORACLES, ids=fixture_id)
def test_oracle_rule_identifiers_hold(oracle_path: Path):
    """The identifiers pin *which* checks fired; `errors_contain` pins *how* the
    finding reads. Both are needed: a text fragment can match the wrong finding,
    and an identifier says nothing about the wording a student sees.

    Exact set equality, unlike the fragment assertions above, so a check that
    stops firing fails here even when its message text still appears somewhere
    else in the report.
    """
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    expected = oracle["check"].get("rules")
    assert expected is not None, f"{fixture_id(oracle_path)}: oracle has no `rules` block"
    proposals = fixture_proposals(oracle_path.parent)
    result = subprocess.run(
        [sys.executable, str(CHECK), str(proposals[0]), "--json"],
        capture_output=True, encoding="utf-8", cwd=oracle_path.parent,
    )
    assert result.returncode == oracle["check"]["exit_code"]
    data = json.loads(result.stdout)
    for level in ("error", "warning"):
        actual = sorted({f["rule"] for f in data["findings"] if f["level"] == level})
        assert actual == expected[f"{level}s"], (
            f"{fixture_id(oracle_path)} {level} rules drifted:\n"
            f"  expected {expected[f'{level}s']}\n  actual   {actual}"
        )


def test_corpus_has_minimum_coverage():
    ids = {fixture_id(p) for p in ORACLES}
    assert len(ids) >= 3  # grows as the corpus lands; hard floor prevents silent emptiness
