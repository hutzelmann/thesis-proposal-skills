"""L0: the pure halves of the install check — README command extraction and
shipped-skill derivation. The networked install itself runs as `poe
install-check` in its own CI workflow, never here."""

from __future__ import annotations

import install_check
import pytest
from helpers import REPO


def test_readme_documents_the_install_command():
    command, package = install_check.readme_install_command(
        (REPO / "README.md").read_text(encoding="utf-8")
    )
    assert command[:3] == ["npx", "skills", "add"]
    assert package == "hutzelmann/thesis-proposal-skills"


def test_extraction_fails_loudly_when_the_command_is_gone():
    with pytest.raises(ValueError, match="README no longer documents"):
        install_check.readme_install_command("install it somehow")


def test_shipped_skills_is_the_eleven_proposal_dirs():
    skills = install_check.shipped_skills(REPO)
    assert len(skills) == 11
    assert all(s.startswith("proposal-") for s in skills)
    assert skills == sorted(skills)


def test_compare_tree_reports_missing_and_differing(tmp_path):
    src, dst = tmp_path / "src", tmp_path / "dst"
    (src / "sub").mkdir(parents=True)
    dst.mkdir()
    (src / "same.md").write_text("x", encoding="utf-8")
    (dst / "same.md").write_text("x", encoding="utf-8")
    (src / "changed.md").write_text("a", encoding="utf-8")
    (dst / "changed.md").write_text("b", encoding="utf-8")
    (src / "sub" / "gone.md").write_text("y", encoding="utf-8")
    problems = install_check.compare_tree(src, dst)
    assert problems == ["differs: changed.md", "missing: sub/gone.md"]


def test_verbatim_problems_sees_through_ansi_color():
    # Under CI=true the skills CLI colorizes the count ("Found \x1b[32m11\x1b[39m
    # skills"), which broke the literal match in the first scheduled run.
    expected = ["proposal-check", "proposal-write"]
    stdout = (
        "\x1b[?25l\x1b[1G\x1b[J◇  Found \x1b[32m2\x1b[39m skills\x1b[?25h\n"
        "│    proposal-check\n"
        "│    proposal-write\n"
    )
    assert install_check.verbatim_problems(stdout, expected) == []


def test_verbatim_problems_reports_a_missing_skill():
    expected = ["proposal-check", "proposal-write"]
    stdout = "Found 1 skills\n  proposal-check\n"
    assert install_check.verbatim_problems(stdout, expected) == [
        "published repo offers 1/2 shipped skills"
    ]


def test_verbatim_problems_reports_a_count_mismatch():
    expected = ["proposal-check", "proposal-write"]
    stdout = "Found 3 skills\n  proposal-check\n  proposal-write\n  proposal-extra\n"
    assert install_check.verbatim_problems(stdout, expected) == [
        "published repo offers a different skill count than the tracked tree ships"
    ]


def test_isolated_env_strips_claude_and_redirects_home(tmp_path, monkeypatch):
    monkeypatch.setenv("CLAUDECODE", "1")
    env = install_check.isolated_env(tmp_path)
    assert "CLAUDECODE" not in env
    assert env["HOME"] == str(tmp_path)
    assert env["XDG_CONFIG_HOME"].startswith(str(tmp_path))
