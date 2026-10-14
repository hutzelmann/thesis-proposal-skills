"""L0: the changelog gate (release-history spec). The real CHANGELOG.md must
pass; each synthetic changelog below breaks exactly one rule and must fail with
a message that names what broke."""

from __future__ import annotations

from pathlib import Path

import changelog
import pytest
from helpers import CHANGELOG_SAMPLE as GOOD
from helpers import CHANGELOG_URL as URL
from helpers import REPO, changelog_root


def no_tags(_tag: str) -> str | None:
    return None


def messages(root: Path, resolve=no_tags) -> list[str]:
    return [str(p) for p in changelog.check(root, resolve)]


def test_the_real_changelog_passes():
    assert messages(REPO, changelog.git_tag_commit(REPO)) == []


def test_the_synthetic_baseline_passes(tmp_path):
    assert messages(changelog_root(tmp_path)) == []


def test_main_reports_ok_and_problems(tmp_path, capsys):
    root = changelog_root(tmp_path)
    assert changelog.main(["--root", str(root), "check"]) == 0
    (root / "CHANGELOG.md").write_text(GOOD.replace("## [0.1.0]", "## [0.1]"), encoding="utf-8")
    assert changelog.main(["--root", str(root), "check"]) == 1
    assert "malformed release heading" in capsys.readouterr().out


@pytest.mark.parametrize(("old", "new", "expected"), [
    ("## [0.1.0] - 2026-07-30", "## [0.1] - 2026-07-30", "malformed release heading"),
    ("## [0.1.0] - 2026-07-30", "## [0.3.0] - 2026-07-30", "is not older than"),
    ("## [0.1.0] - 2026-07-30", "## [0.1.0] - 2026-09-30", "is dated after"),
    ("## [Unreleased]\n", "", "the first section must be ## [Unreleased]"),
    ("### For contributors\n\n- A tool.\n", "### For contributors\n\n- A tool.\n- A tool.\n",
     "entry repeated: - A tool."),
    ("### For contributors", "### Notes", "unknown category 'Notes'"),
    ("### Changed\n\n- **Breaking:** A thing changed.\n\n### For contributors\n\n- A tool.",
     "### For contributors\n\n- A tool.\n\n### Changed\n\n- **Breaking:** A thing changed.",
     "out of order"),
    ("2026-10-15-b-change/", "2026-10-15-c-change/",
     "archive link does not resolve: 2026-10-15-c-change/"),
    (f"[0.1.0]: {URL}/compare/legacy-latex-template...v0.1.0\n", "",
     f"[0.1.0]: compare link should be {URL}/compare/legacy-latex-template...v0.1.0"),
])
def test_each_broken_rule_is_named(tmp_path, old, new, expected):
    assert old in GOOD
    found = messages(changelog_root(tmp_path, GOOD.replace(old, new, 1)))
    assert any(expected in m for m in found), found


def test_the_legacy_era_is_optional_but_only_last(tmp_path):
    era = "## Before the skills: LaTeX template (legacy-latex-template)\n\nProse.\n\n"
    assert messages(changelog_root(tmp_path / "a", GOOD.replace(era, ""))) == []
    moved = GOOD.replace("## [0.1.0]", "## Before the skills: x\n\n## [0.1.0]")
    assert any("legacy era" in m for m in messages(changelog_root(tmp_path / "b", moved)))


def test_an_archived_change_needs_an_entry_or_internal(tmp_path):
    archived = {"2026-07-29-a-change": "", "2026-10-15-b-change": "",
                "2026-10-16-quiet": "## Why\n\nTooling.\n\nChangelog: internal\n",
                "2026-10-16-forgotten": "## Why\n\nA feature.\n"}
    found = messages(changelog_root(tmp_path, archived=archived))
    assert found == ["2026-10-16-forgotten: archived without a changelog entry and "
                     "without 'Changelog: internal'"]


def test_changes_before_the_cutoff_are_not_gated(tmp_path):
    archived = {"2026-07-29-a-change": "", "2026-10-15-b-change": "", "2026-09-01-old": ""}
    assert messages(changelog_root(tmp_path, archived=archived)) == []


STAMPED = GOOD.replace("## [0.2.0]", "## [0.3.0] - 2026-10-20\n\nLead.\n\n### Added\n\n"
                       "- New.\n\n## [0.2.0]").replace(
    f"[Unreleased]: {URL}/compare/v0.2.0...HEAD",
    f"[Unreleased]: {URL}/compare/v0.3.0...HEAD\n[0.3.0]: {URL}/compare/v0.2.0...v0.3.0")


def test_a_stamped_release_needs_the_stamp_in_skills_and_pyproject(tmp_path):
    found = messages(changelog_root(tmp_path / "a", STAMPED))
    assert any("no skill carries a stamp" in m for m in found)
    assert messages(changelog_root(tmp_path / "b", STAMPED, stamp="0.3.0", project="0.3.0")) == []
    found = messages(changelog_root(tmp_path / "c", STAMPED, stamp="0.3.0", project="0.4.0"))
    assert any("differs from pyproject 0.4.0" in m for m in found)
    found = messages(changelog_root(tmp_path / "d", GOOD, stamp="0.3.0", project="0.3.0"))
    assert any("not the newest stamped release" in m for m in found)


def test_a_section_is_retroactive_or_stamped_never_both(tmp_path):
    # the skills' stamp can never name a retroactive release
    found = messages(changelog_root(tmp_path, GOOD, stamp="0.2.0", project="0.2.0"))
    assert any("not the newest stamped release (newest: none)" in m for m in found)


def test_a_tag_must_point_at_the_commit_its_section_names(tmp_path):
    root = changelog_root(tmp_path)
    tags = {"v0.1.0": "a" * 40, "v0.2.0": "c" * 40}
    found = messages(root, tags.get)
    assert found == ["[0.2.0]: tag v0.2.0 points at ccccccc, the section names bbbbbbb"]


def test_notes_prints_one_release_body(tmp_path, capsys):
    root = changelog_root(tmp_path)
    assert changelog.main(["--root", str(root), "notes", "0.2.0"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("_Retroactive release, tagged at bbbbbbb")
    assert "## [0.1.0]" not in out
    assert "[0.2.0]:" not in out
    assert changelog.main(["--root", str(root), "notes", "9.9.9"]) == 1
