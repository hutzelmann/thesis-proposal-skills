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
    result = run_check(FIXTURES / "f00-clean-en" / "llm-scenario-generation.md")
    assert result.returncode == 0, result.stdout
    assert "no errors" in result.stdout
    assert "WARNING" not in result.stdout


def test_broken_fixture_trips_guardrails():
    result = run_check(FIXTURES / "f15-format-broken" / "broken-format.md")
    assert result.returncode == 1
    out = result.stdout
    assert "no blank line before the trailing" in out
    assert "boolean literal" in out
    assert "duplicate reference id `Lee24Gaze`" in out
    assert "cited key `@Ghost99Missing` not defined" in out
    assert "only 2 references" in out
    assert out.count("open [TODO:") == 2


def test_override_workspace_changes_verdicts():
    result = run_check(FIXTURES / "w02-override-workspace" / "llm-scenario-generation.md")
    out = result.stdout
    # the workspace TOML override forbids a heading the default permits
    assert "forbidden section: `Timeline`" in out
    # and raises the reference minimum above the default
    assert "at least 14 required" in out


def test_default_permits_timeline(tmp_path):
    """Same file without the workspace guidelines.md: the exposé template has no
    prohibition on a Timeline heading, so only the override can introduce one."""
    source = (FIXTURES / "w02-override-workspace" / "llm-scenario-generation.md").read_text()
    victim = tmp_path / "llm-scenario-generation.md"
    victim.write_text(source)  # same file, but no guidelines.md next to it
    result = run_check(victim)
    assert "forbidden section" not in result.stdout
    assert "at least 14 required" not in result.stdout


def test_level2_sections_still_checked(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "llm-scenario-generation.md").read_text()
    demoted = source.replace("\n# ", "\n## ").replace("\n## Previous", "\n### Previous").replace(
        "\n## Requirements", "\n### Requirements").replace("\n## Evaluation", "\n### Evaluation")
    demoted = demoted.replace("(RQ3)", "")  # break one cross-ref
    victim = tmp_path / "demoted.md"
    victim.write_text(demoted)
    result = run_check(victim)
    assert "(RQ3) never referenced" in result.stdout


def test_multiple_metadata_blocks_error(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "llm-scenario-generation.md").read_text()
    victim = tmp_path / "double.md"
    victim.write_text("---\ntitle: front\n---\n\n" + source)
    result = run_check(victim)
    assert "additional metadata block" in result.stdout


def test_first_person_capitalized_caught(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "llm-scenario-generation.md").read_text()
    victim = tmp_path / "fp.md"
    victim.write_text(source.replace(
        "Automated driving functions are released only after",
        "We propose a novel approach. Our contribution is released only after",
    ))
    result = run_check(victim)
    assert "first-person pronouns" in result.stdout
