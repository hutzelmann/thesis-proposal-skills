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


def test_level2_sections_still_checked(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    demoted = source.replace("\n# ", "\n## ").replace("\n## Previous", "\n### Previous").replace(
        "\n## Requirements", "\n### Requirements").replace("\n## Evaluation", "\n### Evaluation")
    demoted = demoted.replace("(RQ3)", "")  # break one cross-ref
    victim = tmp_path / "demoted.md"
    victim.write_text(demoted)
    result = run_check(victim)
    assert "(RQ3) never referenced" in result.stdout


def test_multiple_metadata_blocks_error(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "double.md"
    victim.write_text("---\ntitle: front\n---\n\n" + source)
    result = run_check(victim)
    assert "additional metadata block" in result.stdout


def with_nameless_references(source: str, sentence: str) -> str:
    """Append an authorless and an editor-only reference, and cite them."""
    lines = source.rstrip("\n").split("\n")
    extra = [
        "- id: NoName01Standard",
        "  type: webpage",
        "  title: Model monitoring practices",
        "  issued:",
        "    year: 2001",
        "- id: Ed02Collected",
        "  type: book",
        "  title: Collected works on drift",
        "  editor:",
        "  - family: Klein",
        "    given: Karl",
        "  issued:",
        "    year: 2002",
    ]
    body = "\n".join(lines[:-1] + extra + [lines[-1]]) + "\n"
    return body.replace("# Introduction to the Topic",
                        "# Introduction to the Topic\n\n" + sentence, 1)


def test_author_in_text_citation_of_authorless_reference_warns(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "nameless.md"
    victim.write_text(with_nameless_references(source, "@NoName01Standard states this."))
    result = run_check(victim)
    out = result.stdout
    assert "`@NoName01Standard` is cited author-in-text" in out
    assert "use `[@NoName01Standard]` instead" in out
    assert "WARNING" in out


def test_bracketed_citation_of_authorless_reference_is_silent(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "bracketed.md"
    victim.write_text(with_nameless_references(source, "Reported widely [@NoName01Standard]."))
    result = run_check(victim)
    assert "cited author-in-text" not in result.stdout


def test_author_in_text_citation_of_editor_only_reference_is_silent(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "editor.md"
    victim.write_text(with_nameless_references(source, "@Ed02Collected collects work."))
    result = run_check(victim)
    assert "cited author-in-text" not in result.stdout


def test_first_person_capitalized_caught(tmp_path):
    source = (FIXTURES / "f00-clean-en" / "ml-code-review.md").read_text()
    victim = tmp_path / "fp.md"
    victim.write_text(source.replace(
        "Software quality assurance relies heavily",
        "We propose a novel approach. Our contribution relies heavily",
    ))
    result = run_check(victim)
    assert "first-person pronouns" in result.stdout
