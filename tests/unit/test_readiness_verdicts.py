"""L0: the readiness verdicts (testing-harness spec: readiness coverage) on
crafted review and feedback texts — no model call.

The fixtures under test are a minimal pair and a convergence workspace
(`tests/fixtures/f28-open-decisions`, `f29-doubtful-dependency`,
`w09-revised-round`); the verdicts read the review the skill writes beside
them, so these tests hand them review texts written the way a passing and a
failing run would write them.
"""

from __future__ import annotations

import pytest
from helpers import FIXTURES, fixture_proposal
from l1_checks import (
    MEETING_PROMISE,
    clarify_early_items,
    earlier_resolved,
    enumerated_items,
    review_sections,
    review_tier,
    supervise_opening_tier,
    verdict_review_converged,
    verdict_review_dependency,
    verdict_review_ready,
    verdict_supervise_pointers,
    verdict_supervise_points,
    verdict_supervise_ready_block,
)

SKILLS = ("proposal-review", "proposal-write")

PROPOSAL = fixture_proposal("f28-open-decisions").read_text(encoding="utf-8")
EARLIER = (FIXTURES / "w09-revised-round"
           / "ci-repair-agent-configurations-review.md").read_text(encoding="utf-8")
NAME = "ci-repair-agent-configurations-review.md"

READY = """\
**Verdict: ready** — the proposal supports a decision to supervise; the items under
Clarify early in the thesis are settled during the thesis, not before approval.

## Proposal blockers

None.

## Clarify early in the thesis

1. **Exact model versions.** Experimental Setup names a selection rule but no release.
   - What needs deciding: which release per family.
   - Why it matters: reproducibility.
   - When: before the first benchmark run.
   - Reasonable resolution: the most recent release, identifier and access date recorded.
   - Revisit on an adverse outcome: no.
2. **Audit sample size.** Fixed after the pilot of twenty patches, as stated.

## Optional refinements

1. Introduction, first sentence: the per-incident figure needs its source's number.
"""

NEEDS_REVISION = """\
**Verdict: needs revision** — one blocker under the executability test.

## Proposal blockers

1. **RQ3 rests on partner access that is not secured.** Analysis: the engineers at
   the industry partner are the only raters and access is still to be negotiated,
   so RQ3 cannot be answered if it fails; this decides whether it is answerable.

## Clarify early in the thesis

1. **Exact model versions.** Selection rule stated; pick the release before the first run.

## Optional refinements

None.
"""

CONVERGED = """\
**Verdict: ready** — both earlier blockers are resolved; the remaining items are
settled during the thesis.

## Earlier round

1. Configurations confounded with models — resolved: every configuration now runs on both models.
2. RQ3 rests on unsecured partner access — resolved: RQ3 is answered from the student's own audit.
3. Exact model versions (clarify early) — still a clarify-early item; the passage is unchanged.

## Proposal blockers

None.

## Clarify early in the thesis

1. **Exact model versions.** Carried over unchanged.
2. **Audit sample size** (new). Fixed after the pilot.

## Optional refinements

None.
"""


# ---------- parsing --------------------------------------------------------------


def test_tier_is_the_first_phrase_not_the_harshest():
    assert review_tier(READY) == "ready"
    assert review_tier("Verdict: ready — nothing needs revision before approval.") == "ready"
    assert review_tier(NEEDS_REVISION) == "needs revision"
    assert review_tier("**Urteil: Überarbeitung erforderlich** — ein Blocker.") == "needs revision"
    assert review_tier("Verdict: no viable thesis core.") == "no viable thesis core"
    assert review_tier("1. A finding.\n") is None


def test_sections_parse_in_either_language():
    sections = review_sections(READY)
    assert set(sections) == {"blockers", "early", "refinements"}
    assert enumerated_items(sections["blockers"]) == []
    assert len(enumerated_items(sections["early"])) == 2
    german = ("**Bereit**\n\n## Vor der Annahme zu klären\n\nKeine.\n\n"
              "## Früh in der Arbeit zu klären\n\n1. Modellversionen.\n")
    sections = review_sections(german)
    assert enumerated_items(sections["blockers"]) == []
    assert len(enumerated_items(sections["early"])) == 1


def test_items_written_as_subheadings_count():
    body = "\n### 1. Model versions\nRecord.\n\n### 2. Audit size\nPilot.\n"
    assert len(enumerated_items(body)) == 2


def test_the_staged_earlier_review_parses_as_its_fixture_says():
    """w09's README entry: two blockers, one clarify-early bait item."""
    sections = review_sections(EARLIER)
    assert len(enumerated_items(sections["blockers"])) == 2
    assert len(enumerated_items(sections["early"])) == 1


# ---------- review_ready ---------------------------------------------------------


def test_ready_review_passes():
    ok, why = verdict_review_ready(PROPOSAL, PROPOSAL, READY, NAME)
    assert ok, why
    assert "2 clarify-early" in why


@pytest.mark.parametrize(("review", "fragment"), [
    (NEEDS_REVISION, "expected ready"),
    (READY.replace("None.\n\n## Clarify",
                   "1. Model versions are not specified.\n\n## Clarify", 1), "blocker(s)"),
    (READY.replace("## Proposal blockers", "## Findings"), "no proposal-blockers section"),
    (READY.split("## Clarify")[0] + "## Optional refinements\n\n1. Title.\n",
     "no clarify-early items"),
])
def test_ready_review_failures(review, fragment):
    ok, why = verdict_review_ready(PROPOSAL, PROPOSAL, review, NAME)
    assert not ok
    assert fragment in why


def test_ready_review_fails_when_the_proposal_was_edited():
    ok, why = verdict_review_ready(PROPOSAL, PROPOSAL + "\nedited", READY, NAME)
    assert not ok
    assert "modified the proposal" in why


# ---------- review_dependency ----------------------------------------------------


def test_dependency_review_passes():
    ok, why = verdict_review_dependency(PROPOSAL, PROPOSAL, NEEDS_REVISION, NAME)
    assert ok, why


def test_dependency_review_fails_on_ready_or_on_an_unrelated_blocker():
    assert "expected needs revision" in verdict_review_dependency(
        PROPOSAL, PROPOSAL, READY, NAME)[1]
    unrelated = ("**Verdict: needs revision** — one blocker.\n\n## Proposal blockers\n\n"
                 "1. **RQ2 overlaps RQ1.** Both ask about the log condition.\n")
    ok, why = verdict_review_dependency(PROPOSAL, PROPOSAL, unrelated, NAME)
    assert not ok
    assert "none on the doubtful access" in why


# ---------- review_converge ------------------------------------------------------


def test_converged_review_passes():
    ok, why = verdict_review_converged(PROPOSAL, PROPOSAL, CONVERGED, NAME)
    assert ok, why


def test_unrewritten_earlier_review_never_passes():
    """A run that leaves the staged review in place must not read as converged."""
    assert not verdict_review_converged(PROPOSAL, PROPOSAL, EARLIER, NAME)[0]


def test_promoted_bait_is_named_even_when_the_tier_moved():
    promoted = CONVERGED.replace(
        "**Verdict: ready**", "**Verdict: needs revision**").replace(
        "## Proposal blockers\n\nNone.",
        "## Proposal blockers\n\n1. The exact model versions are not specified.")
    ok, why = verdict_review_converged(PROPOSAL, PROPOSAL, promoted, NAME)
    assert not ok
    assert "promoted" in why


@pytest.mark.parametrize(("review", "fragment"), [
    (CONVERGED.replace("## Earlier round", "## Previously"), "no earlier-round section"),
    (CONVERGED.replace("— resolved: every", "— partly resolved: every"), "1 blocker(s) resolved"),
    (CONVERGED.replace("## Proposal blockers\n\nNone.",
                       "## Proposal blockers\n\n1. Missed in the earlier round: RQ2 overlaps."),
     "new blocker(s)"),
])
def test_converged_review_failures(review, fragment):
    ok, why = verdict_review_converged(PROPOSAL, PROPOSAL, review, NAME)
    assert not ok
    assert fragment in why


# ---------- supervise ------------------------------------------------------------

READY_FEEDBACK = """\
**Ready** — no substantial revisions are needed from my side.

**Clarify early in the thesis** — these are settled once the thesis starts
and are not conditions for acceptance:

- which release of each model family you run, recorded with identifier and date;
- how many accepted patches the audit covers, fixed after your pilot;
- how a crashed or timed-out run is counted.

**What to keep:** the within-model comparison is what makes RQ1 answerable.

Note: closing.
"""


def test_opening_tier_reads_the_first_phrase():
    assert supervise_opening_tier(READY_FEEDBACK) == "ready"
    needs = "**Needs revision** — before it is ready, …"
    assert supervise_opening_tier(needs) == "needs revision"
    assert supervise_opening_tier("**Ideenphase — noch kein Exposé**") == "idea stage"


def test_zero_points_pass_only_on_a_ready_feedback():
    assert verdict_supervise_points(READY_FEEDBACK)[0]
    needs = READY_FEEDBACK.replace("**Ready** — no substantial revisions are needed",
                                   "**Needs revision** — address the points below")
    ok, why = verdict_supervise_points(needs)
    assert not ok
    assert "no numbered points" in why


def test_pointers_are_owed_per_point_only():
    """Regression (sonnet dev run over f28, 2026-10-13): a ready feedback with
    no numbered points names no skill, and that is correct."""
    assert verdict_supervise_pointers(READY_FEEDBACK, SKILLS)[0]
    point = READY_FEEDBACK.replace("**What to keep:**", "1. RQ2 overlaps.\n\n**What to keep:**")
    ok, why = verdict_supervise_pointers(point, SKILLS)
    assert not ok
    assert "names no skill" in why
    needs = READY_FEEDBACK.replace("**Ready**", "**Needs revision**")
    assert not verdict_supervise_pointers(needs, SKILLS)[0]


def test_clarify_early_items_are_the_dash_list_after_the_label():
    assert len(clarify_early_items(READY_FEEDBACK)) == 3
    assert clarify_early_items("**Ready**\n\nNothing else.") is None
    german = "**Bereit**\n\n**Früh in der Arbeit zu klären:**\n\n- Modellversion\n- Stichprobe\n"
    assert len(clarify_early_items(german)) == 2


def test_ready_block_passes():
    ok, why = verdict_supervise_ready_block(READY_FEEDBACK, {"English": "Note: closing."})
    assert ok, why


@pytest.mark.parametrize(("feedback", "fragment"), [
    (READY_FEEDBACK.replace("**Ready**", "**Needs revision**"), "opens with needs revision"),
    (READY_FEEDBACK.replace("**What to keep:**", "1. RQ2 overlaps.\n\n**What to keep:**"),
     "numbered points"),
    (READY_FEEDBACK.replace("**Clarify early in the thesis**", "**Later**"),
     "no clarify-early block"),
    (READY_FEEDBACK.replace("- how a crashed", "\n".join(["- x"] * 4) + "\n- how a crashed"),
     "at most five"),
    (READY_FEEDBACK.replace("fixed after your pilot", "agreed at our first meeting"),
     "promises supervisor action"),
])
def test_ready_block_failures(feedback, fragment):
    ok, why = verdict_supervise_ready_block(feedback, {"English": "Note: closing."})
    assert not ok
    assert fragment in why


def test_closing_note_is_left_out_of_the_promise_search():
    closing = "Note: we can meet the tools halfway."
    feedback = READY_FEEDBACK.replace("Note: closing.", closing)
    assert verdict_supervise_ready_block(feedback, {"English": closing})[0]


# ---------- regressions from the adversarial review (2026-10-13) ----------------


@pytest.mark.parametrize(("head", "tier"), [
    ("**Verdict: not ready** — needs revision before approval.", "needs revision"),
    ("**Not yet ready** — the proposal needs revision.", "needs revision"),
    ("Keine Überarbeitung erforderlich: das Exposé ist bereit.", "ready"),
    ("Noch nicht bereit — Überarbeitung erforderlich.", "needs revision"),
])
def test_negated_tier_phrases_are_not_the_verdict(head, tier):
    assert review_tier(head) == tier


def test_negated_ready_feedback_owes_points():
    feedback = "**Not yet ready** — the proposal needs revision.\n\n- RQ2 overlaps RQ1.\n"
    assert supervise_opening_tier(feedback) == "needs revision"
    assert not verdict_supervise_points(feedback)[0]


@pytest.mark.parametrize(("body", "count"), [
    ("1. Confound — resolved.\n2. Access — resolved: an own audit.\n", 2),
    ("Both earlier blockers are resolved.\n", 0),
    ("1. Confound — not resolved.\n2. Access — partly-resolved.\n", 0),
    ("1. Confound — resolved: the revision resolved it.\n2. Access — open.\n", 1),
    ("1. The open-weight confound — resolved.\n", 1),
    ("1. Konfundierung — erledigt.\n2. Zugang — gelöst.\n3. Modelle — teilweise gelöst.\n", 2),
])
def test_earlier_round_counts_items_by_their_first_status(body, count):
    assert earlier_resolved(body) == count


def test_bullets_and_bold_numbers_count_as_items():
    assert len(enumerated_items("- **Doubtful partner access.** RQ3 rests on it.\n")) == 1
    assert len(enumerated_items("**1.** Access.\n\n**2.** Scope.\n")) == 2
    # nested record bullets under a numbered item stay inside that item
    assert len(enumerated_items("1. Model versions.\n- What: the release.\n")) == 1
    review = READY.replace("None.\n\n## Clarify", "- Doubtful access.\n\n## Clarify", 1)
    assert not verdict_review_ready(PROPOSAL, PROPOSAL, review, NAME)[0]


def test_numbered_section_headings_parse():
    review = READY.replace("## Proposal blockers", "## 1. Proposal blockers")
    assert "blockers" in review_sections(review)


def test_clarify_early_label_must_open_its_line():
    prose = ("**Ready** — the few points to clarify early in the thesis are listed below.\n\n"
             + READY_FEEDBACK.split("\n", 1)[1])
    assert len(clarify_early_items(prose)) == 3


def test_wrapped_items_fold_and_still_count():
    wrapped = READY_FEEDBACK.replace(
        "- which release",
        "- which release of each family, a long item\n"
        "  wrapped onto its next line;\n- which release")
    wrapped = wrapped.replace("- how a crashed", "- x\n- y\n- z\n- how a crashed")
    items = clarify_early_items(wrapped)
    assert len(items) == 7
    assert "wrapped onto its next line" in items[0]


@pytest.mark.parametrize(("text", "promise"), [
    ("The design would meet the six-month window.", False),
    ("Die Modellauswahl lässt sich zu Beginn der Arbeit treffen.", False),
    ("A discussion of threats to validity follows.", False),
    ("We can discuss the model choice in our first conversation.", True),
    ("Let's meet once the pilot has run.", True),
    ("Das besprechen wir in einem ersten Gespräch.", True),
    ("Bitte vereinbaren Sie einen Termin.", True),
])
def test_meeting_promise_matches_promises_only(text, promise):
    assert bool(MEETING_PROMISE.search(text)) is promise


def test_scope_options_may_carry_the_only_blocker():
    feedback = ("**Needs revision** — the plan does not fit five months.\n\n"
                "A) Keep RQ1 and RQ2, drop RQ3. B) Keep all three on one model.\n"
                "The choice is yours.\n")
    assert verdict_supervise_points(feedback)[0]
    assert verdict_supervise_pointers(feedback, SKILLS)[0]
