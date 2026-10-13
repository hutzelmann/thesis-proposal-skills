"""L0: every skill closes with the shared stage handoff (skill-packaging spec:
stage handoff at stopping points).

The block lives once, in `shared/blocks/handoff.md`, and is materialized by
`scripts/sync_shared.py` as the opening of a `## Handing over` section that sits
directly before the report offer's section — last in the reporter, which carries
no offer. The skill's own routes follow it, so a section holding the block alone
is a skill that hands over without saying where to.
"""

from pathlib import Path

import pytest
import sync_shared

REPO = Path(__file__).resolve().parents[2]
SKILL_DIRS = sorted(
    d for d in (REPO / "skills").iterdir() if d.is_dir() and d.name.startswith("proposal-")
)
HEADING = sync_shared.HANDOFF_HEADING
BLOCK = sync_shared.handoff_block()

ids = lambda dirs: [d.name for d in dirs]  # noqa: E731


def sections(skill_dir: Path) -> list[str]:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    return [line for line in text.splitlines() if line.startswith("## ")]


def section_body(skill_dir: Path) -> str:
    text = (skill_dir / "SKILL.md").read_text(encoding="utf-8")
    after = text.split(f"\n{HEADING}\n", 1)[1]
    return after.split("\n## ", 1)[0].strip()


def test_block_names_the_ladder_and_the_labels():
    """The parts every handoff measures against; a reword that loses one fails here."""
    for part in ("ready for supervisor discussion", "`Where it stands:`", "`Next:`", "`Or:`",
                 "never carry a skill's name", "superseded", "nothing after them"):
        assert part in BLOCK, part


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=ids(SKILL_DIRS))
def test_section_present_once_and_placed_before_the_offer(skill_dir):
    heads = sections(skill_dir)
    assert heads.count(HEADING) == 1, f"{skill_dir.name}: expected one `{HEADING}` section"
    position = heads.index(HEADING)
    if skill_dir.name == sync_shared.REPORTER:
        assert position == len(heads) - 1, f"{skill_dir.name}: `{HEADING}` is not last"
    else:
        assert heads[position + 1] == sync_shared.OFFER_HEADING, (
            f"{skill_dir.name}: `{HEADING}` must sit directly before "
            f"`{sync_shared.OFFER_HEADING}`"
        )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=ids(SKILL_DIRS))
def test_section_opens_with_the_block_and_adds_routes(skill_dir):
    content = section_body(skill_dir)
    assert content.startswith(BLOCK), (
        f"{skill_dir.name}: the section does not open with shared/blocks/handoff.md — "
        "run scripts/sync_shared.py"
    )
    assert content[len(BLOCK):].strip(), f"{skill_dir.name}: no routes of its own after the block"


def test_handoff_after_the_offer_is_an_anchor_error():
    body = f"\n# T\n\n{sync_shared.OFFER_HEADING}\n\nOffer.\n\n{HEADING}\n\nBlock.\n"
    with pytest.raises(sync_shared.AnchorError, match="follows"):
        sync_shared.handoff_span(body)


def test_missing_section_is_an_anchor_error():
    with pytest.raises(sync_shared.AnchorError, match="no '## Handing over'"):
        sync_shared.handoff_span("\n# T\n\nNo closing section.\n")


def test_span_covers_exactly_the_block_paragraphs():
    paragraphs = BLOCK.count("\n\n") + 1
    filler = "\n\n".join(f"P{i}." for i in range(paragraphs))
    body = f"\n# T\n\n{HEADING}\n\n{filler}\n\nRoutes.\n\n{sync_shared.OFFER_HEADING}\n\nOffer.\n"
    start, end = sync_shared.handoff_span(body)
    assert body[start:end] == filler


def test_the_block_has_the_pinned_paragraph_count():
    """A source that grew or shrank a paragraph would move every skill's region
    boundary; the count is pinned so that change is a deliberate migration."""
    assert BLOCK.count("\n\n") + 1 == sync_shared.HANDOFF_PARAGRAPHS


def test_a_source_with_another_paragraph_count_is_refused(monkeypatch, tmp_path):
    (tmp_path / "handoff.md").write_text("One.\n\nTwo.\n\nThree.\n\nFour.\n", encoding="utf-8")
    monkeypatch.setattr(sync_shared, "BLOCKS", tmp_path)
    with pytest.raises(sync_shared.AnchorError, match="HANDOFF_PARAGRAPHS"):
        sync_shared.handoff_block()


def test_a_short_section_never_swallows_the_next_heading():
    """Two paragraphs where three are expected: the span would reach the offer
    heading, which is refused rather than overwritten."""
    body = (f"\n# T\n\n{HEADING}\n\nP1.\n\nP2.\n\n{sync_shared.OFFER_HEADING}\n\nOffer.\n")
    with pytest.raises(sync_shared.AnchorError, match="run into a heading"):
        sync_shared.handoff_span(body)


def test_a_prose_mention_of_the_offer_heading_is_not_an_anchor():
    filler = "\n\n".join(f"P{i}." for i in range(sync_shared.HANDOFF_PARAGRAPHS))
    body = (f"\n# T\n\nSee `{sync_shared.OFFER_HEADING}` below.\n\n{HEADING}\n\n{filler}\n\n"
            f"Routes.\n\n{sync_shared.OFFER_HEADING}\n\nOffer.\n")
    start, end = sync_shared.handoff_span(body)
    assert body[start:end] == filler


def test_routes_after_the_block_survive_a_render():
    victim = REPO / "skills" / "proposal-review"
    routes = section_body(victim)[len(BLOCK):].strip()
    assert routes
    assert routes in sync_shared.render_skill_md(victim)
