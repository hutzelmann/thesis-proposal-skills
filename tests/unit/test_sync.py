"""L0: shared/ copies must be in sync (skill-packaging spec: sync verification).

The tampering cases run in-process so the drift logic is measurable; one case
keeps the subprocess call, because a broken shebang or a missing
`sys.exit(main())` is invisible to an in-process test and `poe test` invokes
this script from the command line.
"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
import sync_shared
from helpers import copy_sync_tree

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


@pytest.fixture
def sync_tree(tmp_path, monkeypatch):
    """Everything the sync reads and writes, copied: the write-mode cases run on
    the copy, so no test ever syncs the tracked tree."""
    copy_sync_tree(tmp_path)
    monkeypatch.setattr(sync_shared, "REPO", tmp_path)
    monkeypatch.setattr(sync_shared, "SKILLS", tmp_path / "skills")
    monkeypatch.setattr(sync_shared, "BLOCKS", tmp_path / "shared" / "blocks")
    monkeypatch.setattr(sync_shared, "PROMPT_SOURCE", tmp_path / "shared/blocks/install-prompt.md")
    monkeypatch.setattr(sync_shared, "GITATTRIBUTES", tmp_path / ".gitattributes")
    return tmp_path


def announced(out: str) -> list[str]:
    """The destinations a sync run says it rewrote."""
    return [line.split(" -> ", 1)[1] for line in out.splitlines() if line.startswith("synced ")]


@pytest.mark.usefixtures("sync_tree")
def test_an_in_sync_tree_announces_nothing(capsys):
    """A sync names only what it rewrote. The pre-commit hook's refusal says
    "stage the files it lists", so an unchanged SKILL.md — a hand-written page
    that may carry the author's unrelated edits — must never be listed."""
    assert sync_shared.main([]) == 0
    out = capsys.readouterr().out
    assert announced(out) == []
    assert "generated copies already in sync" in out


def test_a_sync_announces_exactly_what_it_rewrote(sync_tree, capsys):
    voice = sync_tree / "shared" / "blocks" / "voice.md"
    voice.write_text(voice.read_text(encoding="utf-8").rstrip("\n") + " Extra.\n",
                     encoding="utf-8")
    assert sync_shared.main([]) == 0
    out = capsys.readouterr().out
    rewritten = sorted(f"skills/{d.name}/SKILL.md" for d in sync_shared.skill_dirs())
    assert sorted(announced(out)) == rewritten
    assert f"rewrote {len(rewritten)} generated file(s)" in out
    assert sync_shared.main(["--check"]) == 0


def test_a_reworded_workspace_files_block_reaches_every_skill_and_nothing_else(sync_tree, capsys):
    """Scenario 'Block reworded': every skill's section carries the new wording,
    and no other byte of any SKILL.md changes."""
    source = sync_tree / "shared" / "blocks" / "workspace-files.md"
    text = source.read_text(encoding="utf-8")
    source.write_text(text.replace("Nothing else goes there.", "Nothing else belongs there.", 1),
                      encoding="utf-8")
    skills = sync_shared.skill_dirs()
    before = {d.name: (d / "SKILL.md").read_text(encoding="utf-8") for d in skills}
    assert sync_shared.main([]) == 0
    rewritten = sorted(f"skills/{d.name}/SKILL.md" for d in skills)
    assert sorted(announced(capsys.readouterr().out)) == rewritten
    for d in skills:
        after = (d / "SKILL.md").read_text(encoding="utf-8")
        assert "Nothing else belongs there." in after
        assert after.replace("Nothing else belongs there.", "Nothing else goes there.") == (
            before[d.name])


def test_a_misplaced_workspace_files_section_is_refused_and_nothing_written(sync_tree):
    victim = sync_tree / "skills" / "proposal-review" / "SKILL.md"
    text = victim.read_text(encoding="utf-8")
    heading = f"\n{sync_shared.WORKSPACE_FILES_HEADING}\n"
    moved = text.replace(heading, "\n## Elsewhere\n\nA section between.\n" + heading, 1)
    moved = moved.replace(f"\n{sync_shared.HANDOFF_HEADING}\n",
                          f"\n## Another\n\nIn the way.\n\n{sync_shared.HANDOFF_HEADING}\n", 1)
    victim.write_text(moved, encoding="utf-8")
    with pytest.raises(sync_shared.AnchorError, match="directly before"):
        sync_shared.main([])
    assert victim.read_text(encoding="utf-8") == moved


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


def test_materialize_never_exposes_a_truncated_destination(tmp_path, monkeypatch):
    """Writes go through a temp file and an atomic replace, so a concurrent
    reader (an xdist worker, or a second sync in a shared checkout) sees the
    old content or the new content, never an empty file mid-truncation."""
    monkeypatch.setattr(sync_shared, "REPO", tmp_path)
    dest = tmp_path / "structure.json"
    dest.write_text("old", encoding="utf-8")
    if os.name == "posix":  # Windows chmod only toggles read-only; st_mode is 0o666
        dest.chmod(0o640)
    at_replace = []
    real_replace = os.replace

    def spying_replace(src, dst):
        at_replace.append(Path(dst).read_text(encoding="utf-8"))
        real_replace(src, dst)

    monkeypatch.setattr(os, "replace", spying_replace)
    assert sync_shared._materialize(dest, "new", "shared/x", check=False) == "structure.json"
    assert at_replace == ["old"], "destination was modified before the atomic swap"
    assert dest.read_text(encoding="utf-8") == "new"
    if os.name == "posix":
        assert (dest.stat().st_mode & 0o777) == 0o640


def test_materialize_failure_keeps_the_old_copy_and_leaves_no_litter(tmp_path, monkeypatch):
    monkeypatch.setattr(sync_shared, "REPO", tmp_path)
    dest = tmp_path / "structure.json"
    dest.write_text("old", encoding="utf-8")

    def failing_replace(_src, _dst):
        raise OSError("boom")

    monkeypatch.setattr(os, "replace", failing_replace)
    with pytest.raises(OSError, match="boom"):
        sync_shared._materialize(dest, "new", "shared/x", check=False)
    assert dest.read_text(encoding="utf-8") == "old"
    assert list(tmp_path.iterdir()) == [dest]


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


# ---------- install prompt materialized into documents ----------------------


PROMPT = "Install it.\n\n1. Do the thing.\n"


def test_prompt_fills_every_marked_fence():
    doc = ("intro\n<!-- install-prompt -->\n```text\nstale\n```\nmiddle\n"
           "<!-- install-prompt -->\n\n```text\n```\nend\n")
    out = sync_shared.render_prompt_doc(doc, PROMPT, "doc")
    assert out.count("Install it.\n\n1. Do the thing.\n```") == 2
    assert "stale" not in out
    assert out.startswith("intro\n")
    assert out.endswith("```\nend\n")
    assert sync_shared.render_prompt_doc(out, PROMPT, "doc") == out


def test_prompt_leaves_unmarked_fences_alone():
    doc = "```sh\nnpx skills add x\n```\n<!-- install-prompt -->\n```text\nold\n```\n"
    out = sync_shared.render_prompt_doc(doc, PROMPT, "doc")
    assert out.startswith("```sh\nnpx skills add x\n```\n")


@pytest.mark.parametrize("doc", [
    "no marker at all\n",
    "<!-- install-prompt -->\nprose instead of a fence\n",
    "<!-- install-prompt -->\n```text\nnever closed\n",
], ids=["no-marker", "no-fence", "unclosed"])
def test_prompt_anchor_problems_raise(doc):
    with pytest.raises(sync_shared.AnchorError):
        sync_shared.render_prompt_doc(doc, PROMPT, "doc")


@pytest.fixture
def prompt_tree(tmp_path, monkeypatch):
    """The prompt source and its documents, copied: the tamper cases below run
    on the copy, so no other worker ever reads a tampered README."""
    for rel in [*sync_shared.PROMPT_DOCS, "shared/blocks/install-prompt.md"]:
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp_path / rel).write_text((REPO / rel).read_text(encoding="utf-8"), encoding="utf-8")
    monkeypatch.setattr(sync_shared, "REPO", tmp_path)
    monkeypatch.setattr(sync_shared, "PROMPT_SOURCE", tmp_path / "shared/blocks/install-prompt.md")
    return tmp_path


@pytest.mark.parametrize("doc_rel", sync_shared.PROMPT_DOCS)
def test_check_detects_a_drifted_prompt_copy(doc_rel, prompt_tree):
    victim = prompt_tree / doc_rel
    original = victim.read_text(encoding="utf-8")
    victim.write_text(original.replace("(recommended)", "(advised)", 1), encoding="utf-8")
    assert sync_shared._sync_prompt_docs(check=True) == [doc_rel]
    assert sync_shared._sync_prompt_docs(check=False) == [doc_rel]
    assert victim.read_text(encoding="utf-8") == original
    assert sync_shared._sync_prompt_docs(check=False) == []


def test_a_prompt_change_announces_both_documents_and_nothing_else(prompt_tree, capsys):
    """A README that needed no change is not named; one whose prompt region was
    rewritten is."""
    assert sync_shared._sync_prompt_docs(check=False) == []
    assert capsys.readouterr().out == ""
    source = prompt_tree / "shared/blocks/install-prompt.md"
    source.write_text(source.read_text(encoding="utf-8") + "6. New step.\n", encoding="utf-8")
    assert sync_shared._sync_prompt_docs(check=False) == sync_shared.PROMPT_DOCS
    assert sorted(announced(capsys.readouterr().out)) == sorted(sync_shared.PROMPT_DOCS)
