"""L0: every skill states where files go in one shared block (skill-packaging:
Workspace-files block in every skill).

The block lives once, in `shared/blocks/workspace-files.md`, and is
materialized by `scripts/sync_shared.py` as the whole of a `## Workspace files`
section directly before `## Handing over`. Unlike the handoff section, it holds
the block alone: a sentence appended in one skill survives the sync and fails
here, rather than being overwritten.

The block also names files, and three other places decide about the same
names: the check's family vocabulary and its allowed names, and the
installer's tables. Each list is held equal to the block in both directions.
"""

import re
from pathlib import Path

import check
import pytest
import sync_shared

import install

REPO = Path(__file__).resolve().parents[2]
SKILL_DIRS = sync_shared.skill_dirs()
HEADING = sync_shared.WORKSPACE_FILES_HEADING
BLOCK = sync_shared.workspace_files_block()
SLUGLESS_ROLE = "ideation notes"
# instances for the placeholders the table uses
PLACEHOLDERS = {"<slug>": "ci-agents", "<label>": "candidates", "<ext>": "yaml", "<name>": "sketch"}

ids = lambda dirs: [d.name for d in dirs]  # noqa: E731


def headings(skill_dir: Path) -> list[str]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    return [line for line in text.splitlines() if line.startswith("## ")]


def section_body(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    after = text.split(f"\n{HEADING}\n", 1)[1]
    return after.split("\n## ", 1)[0].strip()


def tokens(text: str) -> list[str]:
    return re.findall(r"`([^`]+)`", text)


def file_tokens(text: str) -> list[str]:
    """Backticked spans that name a file or folder: a path-like span with a
    dot or a slash (`[paths] proposals` and the labels `notes` and `harvest`
    are not files)."""
    return [t for t in tokens(text) if re.fullmatch(r"[\w.<>/-]+", t) and ("." in t or "/" in t)]


def table_rows(block: str) -> dict[str, list[str]]:
    rows = [line for line in block.splitlines() if line.startswith("| ")]
    cells = [[c.strip() for c in row.strip("|").split("|")] for row in rows[1:]]
    return {role: tokens(names) for role, names in cells}


def instance(shape: str) -> str:
    for placeholder, value in PLACEHOLDERS.items():
        shape = shape.replace(placeholder, value)
    return shape


# ---------- placement and content -------------------------------------------


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=ids(SKILL_DIRS))
def test_section_present_once_and_placed_before_handing_over(skill_dir):
    heads = headings(skill_dir)
    assert heads.count(HEADING) == 1, f"{skill_dir.name}: expected one `{HEADING}` section"
    position = heads.index(HEADING)
    assert heads[position + 1] == sync_shared.HANDOFF_HEADING, (
        f"{skill_dir.name}: `{HEADING}` must sit directly before "
        f"`{sync_shared.HANDOFF_HEADING}`"
    )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=ids(SKILL_DIRS))
def test_section_is_the_block_and_nothing_else(skill_dir):
    assert section_body(skill_dir) == BLOCK, (
        f"{skill_dir.name}: the `{HEADING}` section differs from "
        "shared/blocks/workspace-files.md — run scripts/sync_shared.py; a sentence "
        "of the skill's own belongs elsewhere"
    )


def test_the_block_has_the_pinned_paragraph_count():
    """Paragraphs as the sync counts them: blank-line-separated blocks, the
    role table one of them. Changing the count is a migration."""
    assert BLOCK.count("\n\n") + 1 == sync_shared.WORKSPACE_FILES_PARAGRAPHS


def test_a_source_with_another_paragraph_count_is_refused(monkeypatch, tmp_path):
    (tmp_path / "workspace-files.md").write_text("One.\n\nTwo.\n", encoding="utf-8")
    monkeypatch.setattr(sync_shared, "BLOCKS", tmp_path)
    with pytest.raises(sync_shared.AnchorError, match="WORKSPACE_FILES_PARAGRAPHS"):
        sync_shared.workspace_files_block()


def body_with(section: str, after: str = "") -> str:
    return (f"\n# T\n\nIntro.\n\n## Steps\n\nDo it.\n\n{section}{after}"
            f"{sync_shared.HANDOFF_HEADING}\n\nHand.\n\n{sync_shared.OFFER_HEADING}\n\nOffer.\n")


FILLER = "\n\n".join(f"P{i}." for i in range(sync_shared.WORKSPACE_FILES_PARAGRAPHS))


def test_span_covers_exactly_the_block_paragraphs():
    body = body_with(f"{HEADING}\n\n{FILLER}\n\n")
    start, end = sync_shared.workspace_files_span(body)
    assert body[start:end] == FILLER


def test_an_appended_sentence_stays_outside_the_span():
    body = body_with(f"{HEADING}\n\n{FILLER}\n\nAppended by hand.\n\n")
    start, end = sync_shared.workspace_files_span(body)
    assert body[start:end] == FILLER
    assert "Appended by hand." in body[end:]


def test_a_short_section_never_swallows_the_next_heading():
    body = body_with(f"{HEADING}\n\nP1.\n\nP2.\n\n")
    with pytest.raises(sync_shared.AnchorError, match="run into a heading"):
        sync_shared.workspace_files_span(body)


def test_a_missing_section_is_an_anchor_error():
    with pytest.raises(sync_shared.AnchorError, match="no '## Workspace files'"):
        sync_shared.workspace_files_span(body_with(""))


def test_a_duplicated_section_is_an_anchor_error():
    twice = f"{HEADING}\n\n{FILLER}\n\n{HEADING}\n\n{FILLER}\n\n"
    with pytest.raises(sync_shared.AnchorError, match="more than once"):
        sync_shared.workspace_files_span(body_with(twice))


def test_a_misplaced_section_is_an_anchor_error():
    body = (f"\n# T\n\n{HEADING}\n\n{FILLER}\n\n## Steps\n\nDo it.\n\n"
            f"{sync_shared.HANDOFF_HEADING}\n\nHand.\n")
    with pytest.raises(sync_shared.AnchorError, match="directly before"):
        sync_shared.workspace_files_span(body)


def test_the_sync_keeps_an_appended_sentence_and_this_suite_names_the_skill(tmp_path):
    """The scenario 'Skill-specific sentence appended to the section': the
    sync writes the block and leaves the sentence, so the section no longer
    equals the block and the content test above fails for that skill."""
    victim = REPO / "skills" / "proposal-review"
    stub = tmp_path / victim.name
    stub.mkdir()
    text = (victim / "SKILL.md").read_text(encoding="utf-8")
    marker = f"\n{sync_shared.HANDOFF_HEADING}\n"
    head, tail = text.split(marker, 1)
    (stub / "SKILL.md").write_text(f"{head}\n\nAppended by hand.\n{marker}{tail}",
                                   encoding="utf-8")
    rendered = sync_shared.render_skill_md(stub)
    section = rendered.split(f"\n{HEADING}\n", 1)[1].split("\n## ", 1)[0].strip()
    assert section.startswith(BLOCK)
    assert section.endswith("Appended by hand.")


# ---------- the names agree --------------------------------------------------


def test_the_family_table_lists_every_role_once_both_ways():
    roles = list(table_rows(BLOCK))
    assert len(roles) == len(set(roles)), f"a role is listed twice: {roles}"
    expected = set(check.FAMILY_ROLES) | {SLUGLESS_ROLE}
    missing, extra = expected - set(roles), set(roles) - expected
    assert not missing, f"the block's table lacks the check's role(s): {sorted(missing)}"
    assert not extra, f"the block's table has role(s) the check does not know: {sorted(extra)}"


def test_every_row_names_files_of_its_own_role():
    handles = frozenset({PLACEHOLDERS["<slug>"]})
    for role, names in table_rows(BLOCK).items():
        if role == SLUGLESS_ROLE:
            assert check.IDEATION_NOTES in names, role
            continue
        shapes = [n for n in names if "<slug>" in n]
        assert shapes, f"row `{role}` names no `<slug>` file"
        for shape in shapes:
            got = check.family_member(instance(shape), handles)
            assert got == (PLACEHOLDERS["<slug>"], role), f"`{shape}` is {got}, row says {role}"


def test_every_allowed_name_of_the_check_appears_in_the_block():
    named = {t.rstrip("/") for t in tokens(BLOCK)}
    for name in sorted(check.WORKSPACE_LEVEL):
        assert name in named, f"check.py allows `{name}`; the block does not name it"
    assert check.BUILD_STEM in named
    lowered = {t.lower() for t in named}
    for recipe in sorted(check.RECIPE_NAMES):
        assert recipe in lowered, f"check.py takes `{recipe}` for a build definition"


def test_every_file_the_block_names_is_classified_or_allowed():
    for name in file_tokens(BLOCK):
        if "<" in name:
            assert check.family_member(instance(name), frozenset({"ci-agents"})), name
        elif name != f"{check.FIGURE_FOLDER}/":
            assert check.workspace_allowed(name), (
                f"the block names `{name}`; the check would report it")


def installer_folders() -> set[str]:
    """Every workspace skill folder the installer and its tables know."""
    shared = set(install.SHARED_DIRS)
    hosts = {host.folder_dir for host in install.HOST_DIRS if host.folder_dir}
    native = {rel for _app, base, rel in install.NATIVE_DIRS if base == "folder"}
    return shared | hosts | native


def test_the_installer_folders_agree_with_the_installer_tables():
    named = {t.rstrip("/") for t in tokens(BLOCK) if t.startswith(".") and t.endswith("/")}
    expected = installer_folders()
    assert not expected - named, f"installer folders the block lacks: {sorted(expected - named)}"
    assert not named - expected, f"folders the installer does not know: {sorted(named - expected)}"


def captures(text: str) -> set[str]:
    return set(re.findall(r"`([a-z]+-output\.txt)`", text))


def test_the_troubleshooting_captures_are_the_ones_troubleshoot_writes():
    """Troubleshoot names each capture it has the user write, and offers to
    remove both once the bundle carries them (Q8); the block allows exactly
    those names while a report is assembled."""
    text = (REPO / "skills" / "proposal-troubleshoot" / "SKILL.md").read_text(encoding="utf-8")
    own = text.replace(BLOCK, "")
    allowed = captures(BLOCK)
    assert allowed == captures(own), (
        f"the block allows {sorted(allowed)}; troubleshoot names {sorted(captures(own))}")
    offer = [p for p in own.split("\n\n") if "remove" in p and captures(p) == allowed]
    assert offer, "troubleshoot never offers to remove the captures once the bundle has them"


SEEDING_COLLISION = "the slug takes the numeric suffix and the whole family moves to it"


def test_a_taken_name_at_seeding_moves_the_whole_family():
    """proposal-file-format: a taken target at seeding suffixes the slug for
    the whole family. Read per file, the clause would put a seed beside
    another idea's notes file, the fragmentation the block exists to prevent;
    ideate's seeding step states the same rule."""
    assert SEEDING_COLLISION in BLOCK
    ideate = (REPO / "skills" / "proposal-ideate" / "SKILL.md").read_text(encoding="utf-8")
    assert SEEDING_COLLISION in ideate.replace(BLOCK, "")


def test_the_installer_records_are_named_and_allowed():
    named = set(tokens(BLOCK))
    assert install.RECORD_NAME in named
    assert "skills-lock.json" in named
    assert "skills-lock.json" in Path(install.__file__).read_text(encoding="utf-8")
    assert check.workspace_allowed(install.RECORD_NAME)
    assert check.workspace_allowed("skills-lock.json")
