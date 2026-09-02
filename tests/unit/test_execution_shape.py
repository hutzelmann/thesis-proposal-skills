"""L0: every `## Execution shape` section is the first section of its skill's
body and is pinned verbatim as a whole (skill-review / skill-supervise /
skill-check / skill-write specs: Single-context execution, Single-agent
execution, One writer per file).

The general pin test checks containment, which a partial pin also satisfies.
This test closes the two gaps a substring cannot express: the section's
position — first `##` of the body, so it is read before a run is planned —
and its completeness, by requiring the pin to equal the whole section. The
skill set is discovered from the pin filenames (`<skill>--execution-shape.txt`),
so a sibling gains coverage by adding a pin, with no edit here.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PIN_DIR = Path(__file__).resolve().parent / "data" / "pinned_sentences"
HEADING = "## Execution shape"
PINS = sorted(PIN_DIR.glob("*--execution-shape.txt"))

FRONTMATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
SECTION_HEADING = re.compile(r"^## ", re.MULTILINE)


def skill_of(pin: Path) -> str:
    return pin.stem.split("--")[0]


def body(skill: str) -> str:
    text = (REPO / "skills" / skill / "SKILL.md").read_text(encoding="utf-8")
    return FRONTMATTER.sub("", text)


def sections(text: str) -> list[str]:
    """`## `-headed sections of a body, each from its heading to the next."""
    starts = [m.start() for m in SECTION_HEADING.finditer(text)]
    ends = [*starts[1:], len(text)]
    return [text[a:b].strip() for a, b in zip(starts, ends, strict=True)]


def test_pin_corpus_is_nonempty():
    """A glob that matches nothing would make every test below vacuous."""
    assert PINS, "no execution-shape pins under tests/unit/data/pinned_sentences/"


@pytest.mark.parametrize("pin", PINS, ids=skill_of)
def test_execution_shape_is_the_first_section(pin):
    skill = skill_of(pin)
    first = sections(body(skill))[0]
    assert first.startswith(HEADING + "\n"), (
        f"{skill}: the first section is {first.splitlines()[0]!r}, not {HEADING!r} — "
        "the shape is read before a run is planned only when it comes first"
    )


@pytest.mark.parametrize("pin", PINS, ids=skill_of)
def test_pin_is_the_whole_section(pin):
    skill = skill_of(pin)
    section = next(s for s in sections(body(skill)) if s.startswith(HEADING))
    assert pin.read_text(encoding="utf-8").strip() == section, (
        f"{skill}: {pin.name} differs from the whole `{HEADING}` section — a partial "
        "pin guards only the sentence it holds; revise the pinned copy in the same change"
    )
