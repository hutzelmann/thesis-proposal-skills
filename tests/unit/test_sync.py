"""L0: shared/ copies must be in sync (skill-packaging spec: sync verification).

The tampering cases run in-process so the drift logic is measurable; one case
keeps the subprocess call, because a broken shebang or a missing
`sys.exit(main())` is invisible to an in-process test and `poe test` invokes
this script from the command line.
"""

import subprocess
import sys
from pathlib import Path

import pytest
import sync_shared

REPO = Path(__file__).resolve().parents[2]
SYNC = REPO / "scripts" / "sync_shared.py"


# These tests share mutable state that is not `tmp_path`: the tampering cases
# edit tracked files in place and restore them, and the in-sync cases read those
# same files. Under `-n auto` they would otherwise land on different workers and
# race, so the group keeps them on one worker in declaration order.
pytestmark = pytest.mark.xdist_group("sync_shared_tree")


def test_copies_in_sync(capsys):
    assert sync_shared.main(["--check"]) == 0, capsys.readouterr().out


def test_cli_entry_point_runs():
    """The interpreter boundary: shebang, imports, and `sys.exit(main())`."""
    result = subprocess.run(
        [sys.executable, str(SYNC), "--check"], capture_output=True, text=True
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_attribute_block_covers_every_sync_destination():
    """The block is derived from SYNC_MAP, so it cannot fall behind it."""
    listed = {
        line.split(" ", 1)[0]
        for line in sync_shared.attribute_block().splitlines()
        if not line.startswith("#")
    }
    assert listed == set(sync_shared.generated_paths())
    assert all((REPO / p).is_file() for p in listed)


def test_synced_lines_stay_parseable_by_the_pre_commit_hook(capsys):
    """.githooks/pre-commit stages the fourth field of each `synced` line.

    A line with a trailing note ("synced X -> y (16 paths)") makes the hook run
    `git add 'y (16 paths)'` and abort every commit, so the format is a contract.
    """
    assert sync_shared.main([]) == 0
    for line in capsys.readouterr().out.splitlines():
        if not line.startswith("synced "):
            continue
        fields = line.split()
        assert len(fields) == 4, line
        assert (REPO / fields[3]).is_file(), line


def test_attributes_committed_and_in_sync():
    assert (REPO / ".gitattributes").read_text(encoding="utf-8") == (
        sync_shared.render_gitattributes(
            (REPO / ".gitattributes").read_text(encoding="utf-8")
        )
    )


def test_hand_written_attributes_survive_a_sync():
    hand = "*.pdf binary\n"
    rendered = sync_shared.render_gitattributes(hand + sync_shared.attribute_block())
    assert rendered.startswith(hand)
    assert sync_shared.BEGIN_MARK in rendered


def test_attribute_render_is_idempotent():
    once = sync_shared.render_gitattributes("")
    assert sync_shared.render_gitattributes(once) == once


def test_check_detects_stale_attribute_block(capsys):
    victim = REPO / ".gitattributes"
    original = victim.read_text(encoding="utf-8")
    try:
        stale = original.replace(sync_shared.END_MARK, "stale\n" + sync_shared.END_MARK)
        victim.write_text(stale, encoding="utf-8")
        assert sync_shared.main(["--check"]) == 1
        assert ".gitattributes" in capsys.readouterr().out
    finally:
        victim.write_text(original, encoding="utf-8")


def test_shared_blocks_round_trip_every_skill():
    """Rendering a SKILL.md from the shared blocks reproduces the committed file.

    This is the adoption gate the change turned on: materialization changed who
    maintains the three blocks, never what they say.
    """
    for skill_dir in sync_shared.skill_dirs():
        committed = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
        assert sync_shared.render_skill_md(skill_dir) == committed, skill_dir.name


def test_render_skill_md_is_idempotent():
    for skill_dir in sync_shared.skill_dirs():
        once = sync_shared.render_skill_md(skill_dir)
        assert once == sync_shared.render_skill_md(skill_dir), skill_dir.name


def test_reporter_is_excluded_from_the_offer():
    """The reporter has no closing section, and that absence is not drift."""
    reporter = REPO / "skills" / sync_shared.REPORTER
    assert sync_shared.OFFER_HEADING not in (reporter / "SKILL.md").read_text(encoding="utf-8")
    assert sync_shared.render_skill_md(reporter)  # renders without an offer anchor


def test_skill_specific_paragraph_after_the_offer_survives():
    """Six skills follow the offer with a sentence of their own; only the first
    paragraph of the closing section is materialized."""
    victim = REPO / "skills" / "proposal-check"
    text = (victim / "SKILL.md").read_text(encoding="utf-8")
    tail = text.split(sync_shared.OFFER_HEADING, 1)[1].strip().split("\n\n")
    assert len(tail) > 1, "fixture lost its skill-specific paragraph"
    assert tail[1] in sync_shared.render_skill_md(victim)


def test_unresolvable_anchor_raises_instead_of_writing(tmp_path):
    stub = tmp_path / "proposal-nonsense"
    stub.mkdir()
    (stub / "SKILL.md").write_text("---\nname: x\n---\n\n# T\n\nonly one block\n", encoding="utf-8")
    with pytest.raises(sync_shared.AnchorError):
        sync_shared.render_skill_md(stub)


def test_check_detects_a_tampered_shared_region(capsys):
    victim = REPO / "skills" / "proposal-review" / "SKILL.md"
    original = victim.read_text(encoding="utf-8")
    try:
        victim.write_text(original.replace("**Voice:**", "**Tone:**", 1), encoding="utf-8")
        assert sync_shared.main(["--check"]) == 1
        assert "proposal-review/SKILL.md" in capsys.readouterr().out
    finally:
        victim.write_text(original, encoding="utf-8")


@pytest.mark.parametrize("victim_rel", [
    "skills/proposal-write/references/guidelines.md",
    "skills/proposal-write/scripts/check.py",
])
def test_check_detects_tampering(victim_rel, capsys):
    victim = REPO / victim_rel
    original = victim.read_text(encoding="utf-8")
    try:
        victim.write_text(original + "\ntampered\n", encoding="utf-8")
        assert sync_shared.main(["--check"]) == 1
        assert "OUT OF SYNC" in capsys.readouterr().out
    finally:
        victim.write_text(original, encoding="utf-8")
