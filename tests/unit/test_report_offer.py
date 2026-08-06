"""L0: the bug-report offer is byte-identical across the set and appears once
(skill-packaging spec: uniform failure-path report offer).

Two halves, and the second matters as much as the first. Every skill that can
fail carries the offer; `proposal-troubleshoot` carries it nowhere, because it is
where the offer leads — a skill that offers itself is a loop, not an offer.

The block is pinned here rather than in a data file because its wording is the
requirement: an offer reworded per skill stops reading as one voice, and an offer
that drifts toward firing on ordinary findings trains users to ignore it.
"""

from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SKILL_DIRS = sorted(
    d for d in (REPO / "skills").iterdir() if d.is_dir() and d.name.startswith("proposal-")
)
REPORTER = "proposal-troubleshoot"
OFFERING_DIRS = [d for d in SKILL_DIRS if d.name != REPORTER]

SECTION_HEADING = "## When this run fails"
OFFER_BLOCK = (
    "If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step "
    "failed repeatedly with no user edit in between, or the state makes no sense — offer a bug "
    "report once, in these words, and do not raise it again in the same session: \"Something "
    "here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` "
    "can diagnose it and, if it is one, assemble a report you can send.\" Ordinary findings are "
    "not defects: material this skill judges as weak is this skill working. Collect nothing "
    "unless the user accepts."
)
# the sentence the user actually hears, kept separately so a test failure says
# which half drifted
USER_FACING = (
    "Something here looks like a defect in the skill rather than in your proposal — "
    "`proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send."
)

ids = lambda dirs: [d.name for d in dirs]  # noqa: E731


def body(skill_dir: Path) -> str:
    return (skill_dir / "SKILL.md").read_text(encoding="utf-8")


def test_the_reporter_exists_and_the_set_is_not_empty():
    """Both halves below are vacuous if the globs match nothing."""
    names = {d.name for d in SKILL_DIRS}
    assert REPORTER in names, f"{REPORTER} is not installed in skills/: {sorted(names)}"
    assert len(OFFERING_DIRS) == len(SKILL_DIRS) - 1
    assert OFFERING_DIRS, "no skills left to carry the offer"


@pytest.mark.parametrize("skill_dir", OFFERING_DIRS, ids=ids(OFFERING_DIRS))
def test_offer_block_present_verbatim_exactly_once(skill_dir):
    text = body(skill_dir)
    count = text.count(OFFER_BLOCK)
    assert count == 1, (
        f"{skill_dir.name}: offer block appears {count}× verbatim (expected 1). The block is "
        "byte-identical across the set — copy it from tests/unit/test_report_offer.py rather "
        "than rewording it per skill."
    )


@pytest.mark.parametrize("skill_dir", OFFERING_DIRS, ids=ids(OFFERING_DIRS))
def test_offer_sits_in_its_own_closing_section(skill_dir):
    text = body(skill_dir)
    assert text.count(SECTION_HEADING) == 1, (
        f"{skill_dir.name}: expected exactly one `{SECTION_HEADING}` section"
    )
    assert text.index(SECTION_HEADING) < text.index(OFFER_BLOCK), (
        f"{skill_dir.name}: the offer block sits outside its `{SECTION_HEADING}` section"
    )


@pytest.mark.parametrize("skill_dir", OFFERING_DIRS, ids=ids(OFFERING_DIRS))
def test_user_facing_sentence_is_quoted_once(skill_dir):
    """Guards the half a reword is most likely to touch."""
    assert body(skill_dir).count(USER_FACING) == 1, (
        f"{skill_dir.name}: the user-facing offer sentence drifted or is repeated"
    )


def test_reporter_does_not_offer_itself():
    text = body(REPO / "skills" / REPORTER)
    assert USER_FACING not in text, (
        f"{REPORTER} carries the offer sentence — it is the destination of the offer, not a "
        "referrer, and offering itself would loop"
    )
    assert SECTION_HEADING not in text, (
        f"{REPORTER} carries a `{SECTION_HEADING}` section; its own failure mode is a missing "
        "collector, which its instructions already cover"
    )
