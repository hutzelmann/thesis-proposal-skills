"""L0: every shipped SKILL.md opens with the same four blocks (skill-packaging
spec: uniform skill opening structure, enforced offline).

Order is title, purpose, workflow line, voice block, mandate. The workflow line
is byte-identical across the set except for which skill name is bolded, the
voice block is byte-identical everywhere, and each mandate is pinned in
`tests/unit/data/skill_mandates/`, so a reword fails here instead of passing
review silently.

Adjacency ("nothing inserted between a mandate and the paragraph beneath it") is
enforced from both sides: above, the only insertable header blocks — purpose,
workflow line, voice block — are pinned to fixed indices, with the workflow line
required to appear exactly once in the whole file; below, the block directly
beneath each mandate is pinned in `tests/unit/data/mandate_successors/` (empty
pin = the mandate closes the header region), so a paragraph slipped in after a
mandate fails instead of passing silently.

The title is not required to match the skill name — proposal-lit-search's is
`# Literature Search`.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL_DIRS = sorted(
    d for d in (REPO / "skills").iterdir() if d.is_dir() and d.name.startswith("proposal-")
)
SKILL_MDS = [d / "SKILL.md" for d in SKILL_DIRS]
MANDATE_DIR = REPO / "tests" / "unit" / "data" / "skill_mandates"
SUCCESSOR_DIR = REPO / "tests" / "unit" / "data" / "mandate_successors"

ids = lambda paths: [str(p.relative_to(REPO)) for p in paths]  # noqa: E731

WORKFLOW_LABEL = "**Workflow:**"
PURPOSE_INDEX = 1
WORKFLOW_INDEX = 2
VOICE_INDEX = 3
MANDATE_INDEX = 4
# Byte-identical in every skill (skill-packaging spec: voice block). Chat
# conduct only — it carries no operational rules, so it cannot collide with a
# mandate.
VOICE_BLOCK = (
    "**Voice:** neutral and constructive — never praise the user or their "
    "material, never compliment your own output. Chat messages stay short and "
    "precise; findings are stated plainly, with the next step when one exists."
)
# "one or two sentences" — a bound on padding, not a style rule.
PURPOSE_MAX_CHARS = 400

FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)


def header_blocks(skill_md: Path) -> list[str]:
    """Blank-line-separated blocks from the title up to the first `##` heading."""
    body = FRONTMATTER.sub("", skill_md.read_text(encoding="utf-8"))
    region = re.split(r"^## ", body, maxsplit=1, flags=re.MULTILINE)[0]
    return [b.strip() for b in re.split(r"\n\s*\n", region.strip()) if b.strip()]


def workflow_line(skill_md: Path) -> str:
    return header_blocks(skill_md)[WORKFLOW_INDEX]


def test_every_skill_is_discovered():
    """A glob that silently matches nothing would make every test below vacuous."""
    assert len(SKILL_MDS) == 10, f"expected 10 skills, found {[p.parent.name for p in SKILL_MDS]}"
    pinned = {p.stem for p in MANDATE_DIR.glob("*.txt")}
    assert pinned == {d.name for d in SKILL_DIRS}, (
        f"pinned mandates do not cover the skill set: {pinned ^ {d.name for d in SKILL_DIRS}}"
    )
    successors = {p.stem for p in SUCCESSOR_DIR.glob("*.txt")}
    assert successors == {d.name for d in SKILL_DIRS}, (
        "pinned mandate successors do not cover the skill set: "
        f"{successors ^ {d.name for d in SKILL_DIRS}}"
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=ids(SKILL_MDS))
def test_header_block_order(skill_md):
    blocks = header_blocks(skill_md)
    name = skill_md.parent.name
    assert len(blocks) > MANDATE_INDEX, f"{name}: header has only {len(blocks)} blocks"
    assert blocks[0].startswith("# "), f"{name}: body does not open with a `# ` title"

    purpose = blocks[PURPOSE_INDEX]
    assert not purpose.startswith(WORKFLOW_LABEL), (
        f"{name}: no purpose block — the workflow line follows the title directly"
    )
    assert not purpose.startswith("#"), f"{name}: a heading sits where the purpose block belongs"
    assert len(purpose) <= PURPOSE_MAX_CHARS, (
        f"{name}: purpose block is {len(purpose)} chars (max {PURPOSE_MAX_CHARS}) — "
        "one or two sentences, do not pad the top of the file"
    )
    assert blocks[WORKFLOW_INDEX].startswith(WORKFLOW_LABEL), (
        f"{name}: block {WORKFLOW_INDEX} is not the workflow line — exactly one paragraph "
        "may precede it"
    )
    assert blocks[VOICE_INDEX] == VOICE_BLOCK, (
        f"{name}: block {VOICE_INDEX} is not the voice block, or its wording drifted — "
        "the voice block is byte-identical in every skill, between the workflow line "
        "and the mandate"
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=ids(SKILL_MDS))
def test_workflow_line_appears_once(skill_md):
    """Pins adjacency: the line cannot also be repeated below a mandate."""
    text = skill_md.read_text(encoding="utf-8")
    assert text.count(WORKFLOW_LABEL) == 1, (
        f"{skill_md.parent.name}: workflow line appears {text.count(WORKFLOW_LABEL)} times"
    )


def test_workflow_line_identical_across_skills():
    unmarked = {md.parent.name: workflow_line(md).replace("**", "") for md in SKILL_MDS}
    distinct = set(unmarked.values())
    assert len(distinct) == 1, "workflow line drifted between skills:\n" + "\n".join(
        f"  {name}: {line}" for name, line in sorted(unmarked.items())
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=ids(SKILL_MDS))
def test_workflow_line_marks_its_own_skill(skill_md):
    name = skill_md.parent.name
    roster = workflow_line(skill_md).removeprefix(WORKFLOW_LABEL)
    marked = re.findall(r"\*\*(.+?)\*\*", roster)
    assert len(marked) == 1, f"{name}: {len(marked)} bolded names in the workflow line, expected 1"
    assert re.fullmatch(r"proposal-[a-z-]+", marked[0]), (
        f"{name}: bolded `{marked[0]}` is not a skill name"
    )
    assert marked[0] == name, (
        f"{name}: workflow line bolds `{marked[0]}` — a sibling's line was copied "
        "without re-marking"
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=ids(SKILL_MDS))
def test_mandate_matches_pinned_copy(skill_md):
    name = skill_md.parent.name
    pinned = (MANDATE_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()
    assert header_blocks(skill_md)[MANDATE_INDEX] == pinned, (
        f"{name}: mandate differs from tests/unit/data/skill_mandates/{name}.txt — "
        "a mandate stays verbatim; revise the pinned copy in the same change to reword it"
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=ids(SKILL_MDS))
def test_mandate_adjacent_to_pinned_successor(skill_md):
    """Nothing is inserted between a mandate and the paragraph beneath it
    (skill-packaging spec). An empty pin means the mandate closes the header
    region, so any block after it is an insertion."""
    name = skill_md.parent.name
    pinned = (SUCCESSOR_DIR / f"{name}.txt").read_text(encoding="utf-8").strip()
    blocks = header_blocks(skill_md)
    if not pinned:
        assert len(blocks) == MANDATE_INDEX + 1, (
            f"{name}: {len(blocks) - MANDATE_INDEX - 1} block(s) inserted after the "
            "mandate — the pinned successor is empty, so the mandate must close the "
            "header region"
        )
        return
    assert len(blocks) > MANDATE_INDEX + 1, (
        f"{name}: a successor paragraph is pinned but the mandate closes the header region"
    )
    assert blocks[MANDATE_INDEX + 1] == pinned, (
        f"{name}: the block beneath the mandate differs from "
        f"tests/unit/data/mandate_successors/{name}.txt — nothing is inserted "
        "between a mandate and the paragraph beneath it; revise the pinned copy "
        "in the same change to reword that paragraph"
    )
