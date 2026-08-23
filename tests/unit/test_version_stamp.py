"""L0: the publish stamp — writing it (stamp_version) and reading it back
(identify_release's fast path). The version's single source of truth is
`[project] version` in pyproject.toml; everything else is a copy. No git
history needed here: the pure text transformations carry the contract."""

from __future__ import annotations

import identify_release
import pytest
import stamp_version

STAMP = "0.2.0"
NEWER = "0.3.0"

SKILL_MD = """---
name: proposal-example
description: Example. Use when testing.
license: MIT
---

# Body
"""


def test_stamp_is_inserted_before_the_closing_delimiter():
    stamped = stamp_version.stamp_text(SKILL_MD, STAMP, path=None)
    assert f"license: MIT\nmetadata:\n  version: {STAMP}\n---\n" in stamped
    assert stamped.endswith("# Body\n")


def test_restamping_replaces_rather_than_duplicates():
    once = stamp_version.stamp_text(SKILL_MD, STAMP, path=None)
    twice = stamp_version.stamp_text(once, NEWER, path=None)
    assert NEWER in twice
    assert STAMP not in twice
    assert twice.count("metadata:") == 1


def test_a_file_without_frontmatter_is_refused():
    with pytest.raises(ValueError, match="closing frontmatter delimiter"):
        stamp_version.stamp_text("no frontmatter here", STAMP, path=None)


def test_the_version_source_is_pyproject_and_is_semver():
    assert stamp_version.SEMVER.fullmatch(stamp_version.project_version())


def test_find_stamp_reads_the_stamped_line_shape(tmp_path):
    (tmp_path / "SKILL.md").write_text(
        f"---\nname: x\nmetadata:\n  version: {STAMP}\n---\n", encoding="utf-8"
    )
    assert identify_release.find_stamp(tmp_path) == STAMP


def test_find_stamp_ignores_bare_version_numbers(tmp_path):
    (tmp_path / "hashes.txt").write_text(
        "# collected with tool 3.2.1 on python 3.11.9\nSKILL.md git_blob=abc123\n",
        encoding="utf-8",
    )
    assert identify_release.find_stamp(tmp_path) is None


def test_prioritize_moves_the_stamped_revision_first():
    revisions = [("aaa", "d", "s"), ("bbb", "d", "s"), ("ccc", "d", "s")]
    assert identify_release.prioritize(revisions, "bbb")[0][0] == "bbb"
    assert identify_release.prioritize(revisions, None) == revisions
    assert identify_release.prioritize(revisions, "zzz") == revisions
