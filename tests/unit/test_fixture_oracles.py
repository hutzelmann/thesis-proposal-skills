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

REPO = Path(__file__).resolve().parents[2]
CHECK = REPO / "skills" / "proposal-check" / "scripts" / "check.py"
FIXTURES = REPO / "tests" / "fixtures"

ORACLES = sorted(FIXTURES.glob("*/expected.json"))


def fixture_id(path: Path) -> str:
    return path.parent.name


def fixture_proposals(fixture_dir: Path) -> list[Path]:
    """The fixture's proposal markdown, top-level or one directory down —
    w07 keeps its proposal in a configured `proposals/` subdirectory. The
    one-proposal-per-fixture invariant holds across both levels."""
    return [
        p for p in sorted(fixture_dir.glob("*.md")) + sorted(fixture_dir.glob("*/*.md"))
        if p.name not in ("guidelines.md",) and not p.name.endswith("-handout.md")
    ]


@pytest.mark.parametrize("oracle_path", ORACLES, ids=fixture_id)
def test_oracle_holds(oracle_path: Path):
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    proposals = fixture_proposals(oracle_path.parent)
    assert len(proposals) == 1, f"expected exactly one proposal md in {oracle_path.parent}"
    # the fixture directory is the workspace root: the check's guidelines
    # chain ends at the working directory, which is where w07 keeps its file
    result = subprocess.run(
        [sys.executable, str(CHECK), str(proposals[0])], capture_output=True, text=True,
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
        capture_output=True, text=True, cwd=oracle_path.parent,
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
