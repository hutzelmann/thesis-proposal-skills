"""L0: the frontmatter contract — the only text a host reads before choosing.

`test_skill_header_pattern.py` starts after the closing `---`; everything above
it was unguarded until this file. That matters more than body wording: a body is
read once a skill has been selected, while `name` and `description` decide
whether it is selected at all, and they sit in context for every session whether
the skill is used or not.

The routing sweep (`harness/routing.py`, `docs/skill-routing.md`) measures the
same surface empirically but needs a host install and a subscription. This file
is the part that can gate a commit.
"""

from __future__ import annotations

import json
import re
import statistics
from pathlib import Path

import pytest
from helpers import REPO

SKILLS = REPO / "skills"
SKILL_DIRS = sorted(d for d in SKILLS.iterdir() if d.is_dir() and d.name.startswith("proposal-"))
SKILL_MDS = [d / "SKILL.md" for d in SKILL_DIRS]
TRIGGER_TERMS = json.loads(
    (Path(__file__).parent / "data" / "trigger_terms.json").read_text(encoding="utf-8")
)

# The skill format's own limits, quoted from Anthropic's skill-authoring
# guidance: name ≤ 64 characters, description ≤ 1024, body under 500 lines.
NAME_LIMIT = 64
DESCRIPTION_FORMAT_LIMIT = 1024
BODY_LINE_LIMIT = 500

# Tighter than the format allows, because these are ours to spend. Every skill's
# metadata is loaded whether or not the skill is used, so the total is the number
# that competes with the user's context; 3471 was the total on 2026-08-10, and
# the headroom exists for the cross-references that keep skills from colliding.
DESCRIPTION_BUDGET = 500
METADATA_BUDGET = 4500

# Judgment, not derivation, and the only constant here with no external source.
# A relative bound self-adjusts as the suite grows, which an absolute word count
# does not. On 2026-08-10 the median body was 1330 words and the largest
# (proposal-ideate, 2348) sat at 88% of the ceiling — tight enough to be a real
# guard, loose enough that the conversational skills are not forced to shed
# content into reference files a selector never reads.
BODY_PROPORTION = 2.0

FRONTMATTER_KEYS = {"name", "description"}

# Third person by exclusion: "the user", "their", "a student" is the register.
# The official guidance warns that a mixed point of view degrades discovery.
PERSONAL_PRONOUNS = re.compile(r"\b(I|we|our|us|my|me|you|your|yours)\b", re.IGNORECASE)

TRIGGER_CLAUSE = "use when"
MIN_WHAT_CLAUSE = 30


def frontmatter(skill_md: Path) -> dict[str, str]:
    """The `key: value` block between the opening and closing `---`.

    Deliberately not a YAML parser: the contract is that frontmatter stays two
    flat keys, and a general parser would quietly permit general frontmatter.
    """
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    assert lines, f"{skill_md} is empty"
    assert lines[0] == "---", f"{skill_md} does not open with frontmatter"
    fields = {}
    for line in lines[1:]:
        if line == "---":
            return fields
        key, separator, value = line.partition(":")
        assert separator, f"{skill_md}: frontmatter line is not `key: value`: {line!r}"
        fields[key.strip()] = value.strip()
    raise AssertionError(f"{skill_md}: frontmatter is never closed")


def description(skill_md: Path) -> str:
    return frontmatter(skill_md)["description"]


def body(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8")
    return text.split("---", 2)[2] if text.startswith("---") else text


@pytest.fixture(scope="module")
def descriptions() -> dict[str, str]:
    return {md.parent.name: description(md) for md in SKILL_MDS}


# ---------- identity ---------------------------------------------------------


def test_the_skill_set_is_not_empty():
    assert len(SKILL_MDS) >= 9


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_name_equals_its_directory(skill_md):
    assert frontmatter(skill_md)["name"] == skill_md.parent.name


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_name_within_the_format_limit(skill_md):
    name = frontmatter(skill_md)["name"]
    assert len(name) <= NAME_LIMIT
    assert re.fullmatch(r"proposal-[a-z0-9-]+", name), name


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_frontmatter_carries_no_unknown_keys(skill_md):
    assert set(frontmatter(skill_md)) == FRONTMATTER_KEYS


# ---------- description contract --------------------------------------------


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_description_within_budget(skill_md):
    text = description(skill_md)
    assert len(text) <= DESCRIPTION_FORMAT_LIMIT
    assert len(text) <= DESCRIPTION_BUDGET, (
        f"{skill_md.parent.name}: {len(text)} chars, budget {DESCRIPTION_BUDGET}"
    )


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_description_stays_in_the_third_person(skill_md):
    found = PERSONAL_PRONOUNS.findall(description(skill_md))
    assert not found, f"{skill_md.parent.name}: first/second person {found}"


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_description_states_both_what_and_when(skill_md):
    text = description(skill_md)
    lowered = text.lower()
    assert TRIGGER_CLAUSE in lowered, f"{skill_md.parent.name}: no `Use when` trigger clause"
    what = text[: lowered.index(TRIGGER_CLAUSE)].strip()
    assert len(what) >= MIN_WHAT_CLAUSE, f"{skill_md.parent.name}: what-clause too thin: {what!r}"


def test_combined_metadata_stays_within_the_context_it_costs():
    total = sum(
        len(frontmatter(md)["name"]) + len(frontmatter(md)["description"]) for md in SKILL_MDS
    )
    assert total <= METADATA_BUDGET, f"metadata totals {total} chars, budget {METADATA_BUDGET}"


# ---------- trigger ownership ------------------------------------------------


def test_every_owner_names_an_installed_skill():
    installed = {d.name for d in SKILL_DIRS}
    unknown = {s for s in TRIGGER_TERMS["owned"].values() if s not in installed}
    assert not unknown, f"owned-trigger table names skills that do not exist: {unknown}"


def test_no_term_is_both_owned_and_shared():
    overlap = set(TRIGGER_TERMS["owned"]) & set(TRIGGER_TERMS["shared"])
    assert not overlap, f"terms cannot be owned and shared at once: {overlap}"


def test_owned_trigger_terms_have_exactly_one_claimant(descriptions):
    intruders = [
        (term, owner, skill)
        for term, owner in TRIGGER_TERMS["owned"].items()
        for skill, text in descriptions.items()
        if term in text.lower() and skill != owner
    ]
    assert not intruders, "\n".join(
        f"{skill} claims {term!r}, which belongs to {owner}" for term, owner, skill in intruders
    )


def test_shared_terms_are_allowed_to_appear_anywhere(descriptions):
    """The escape hatch has to actually work, or the first honest overlap turns
    this file into noise the next reader disables."""
    corpus = " ".join(descriptions.values()).lower()
    assert any(term in corpus for term in TRIGGER_TERMS["shared"])


def test_a_second_claimant_would_be_reported():
    owned = {"ready for their supervisor": "proposal-review"}
    descriptions = {
        "proposal-review": "Use when asking whether it is ready for their supervisor.",
        "proposal-check": "Use when checking before it is ready for their supervisor.",
    }
    intruders = [
        skill for term, owner in owned.items()
        for skill, text in descriptions.items()
        if term in text.lower() and skill != owner
    ]
    assert intruders == ["proposal-check"]


# ---------- size -------------------------------------------------------------


@pytest.mark.parametrize("skill_md", SKILL_MDS, ids=lambda p: p.parent.name)
def test_body_under_the_published_line_cap(skill_md):
    lines = len(body(skill_md).splitlines())
    assert lines < BODY_LINE_LIMIT, f"{skill_md.parent.name}: {lines} lines"


def test_no_skill_body_outgrows_its_siblings():
    words = {md.parent.name: len(body(md).split()) for md in SKILL_MDS}
    ceiling = BODY_PROPORTION * statistics.median(words.values())
    oversized = {name: count for name, count in words.items() if count > ceiling}
    assert not oversized, (
        f"bodies past {ceiling:.0f} words (median × {BODY_PROPORTION}): {oversized}"
    )
