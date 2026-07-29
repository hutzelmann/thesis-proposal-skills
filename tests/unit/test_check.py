"""L0: deterministic check script against blueprint fixtures (skill-check spec)."""

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CHECK = REPO / "skills" / "proposal-check" / "scripts" / "check.py"
FIXTURES = REPO / "tests" / "fixtures"


def run_check(proposal: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECK), str(proposal)], capture_output=True, text=True
    )


def test_clean_fixture_passes():
    result = run_check(FIXTURES / "f00-clean-en" / "ml-code-review.md")
    assert result.returncode == 0, result.stdout
    assert "no errors" in result.stdout
    assert "WARNING" not in result.stdout


def test_broken_fixture_trips_guardrails():
    result = run_check(FIXTURES / "f15-format-broken" / "broken-format.md")
    assert result.returncode == 1
    out = result.stdout
    assert "no blank line before the trailing" in out
    assert "boolean literal" in out
    assert "duplicate reference id `Lee24Index`" in out
    assert "cited key `@Ghost99Missing` not defined" in out
    assert "only 2 references" in out
    assert out.count("open [TODO:") == 2


def test_override_workspace_changes_verdicts():
    result = run_check(FIXTURES / "w02-override-workspace" / "ml-code-review.md")
    out = result.stdout
    # timeline heading is un-forbidden by the workspace TOML override
    assert "forbidden section" not in out
    # raised minimum is enforced
    assert "at least 8 required" in out


def test_default_forbids_timeline(tmp_path):
    source = (FIXTURES / "w02-override-workspace" / "ml-code-review.md").read_text()
    victim = tmp_path / "ml-code-review.md"
    victim.write_text(source)  # same file, but no guidelines.md next to it
    result = run_check(victim)
    assert "forbidden section: `Timeline`" in result.stdout
