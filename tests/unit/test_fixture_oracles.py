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


@pytest.mark.parametrize("oracle_path", ORACLES, ids=fixture_id)
def test_oracle_holds(oracle_path: Path):
    oracle = json.loads(oracle_path.read_text(encoding="utf-8"))
    proposals = [
        p for p in oracle_path.parent.glob("*.md")
        if p.name not in ("guidelines.md",) and not p.name.endswith("-handout.md")
    ]
    assert len(proposals) == 1, f"expected exactly one proposal md in {oracle_path.parent}"
    result = subprocess.run(
        [sys.executable, str(CHECK), str(proposals[0])], capture_output=True, text=True
    )
    expected = oracle["check"]
    assert result.returncode == expected["exit_code"], result.stdout

    error_lines = [l for l in result.stdout.splitlines() if l.startswith("- ERROR:")]
    warning_lines = [l for l in result.stdout.splitlines() if l.startswith("- WARNING:")]

    for needle in expected["errors_contain"]:
        assert any(needle in l for l in error_lines), f"missing error `{needle}`\n{result.stdout}"
    for needle in expected["warnings_contain"]:
        assert any(needle in l for l in warning_lines), f"missing warning `{needle}`\n{result.stdout}"
    # completeness: every actual error must be pinned by the oracle
    for line in error_lines:
        assert any(n in line for n in expected["errors_contain"]), f"unpinned error: {line}"


def test_corpus_has_minimum_coverage():
    ids = {fixture_id(p) for p in ORACLES}
    assert len(ids) >= 3  # grows as the corpus lands; hard floor prevents silent emptiness
