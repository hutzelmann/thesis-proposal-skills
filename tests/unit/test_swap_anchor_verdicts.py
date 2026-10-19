"""L0: the swap-test anchor verdicts (testing-harness spec: swap-test anchor
coverage) on crafted review and feedback texts — no model call.

The fixtures under test are a minimal pair (`tests/fixtures/f31-decorative-tool`,
`f32-tool-as-object`): the same text naming the fictitious framework Mendwright
in its title and research questions, differing only in the contribution's
close. The verdicts read what the review and supervise skills write beside
them, so these tests hand them texts written the way a passing and a failing run
would write them — and pin that the pair stays minimal.
"""

from __future__ import annotations

import difflib
from pathlib import Path

import pytest
from helpers import fixture_proposal
from l1_checks import (
    SWAP_PAIR_TOOL,
    numbered_points,
    swap_failure_cited,
    verdict_earlier_round_rewritten,
    verdict_review_swap_anchored,
    verdict_review_swap_decorative,
    verdict_supervise_pass_listed,
    verdict_supervise_point_kept,
    verdict_supervise_swap_missed,
    verdict_supervise_swap_question,
    verdict_supervise_swap_quiet,
)

DECORATIVE = fixture_proposal("f31-decorative-tool").read_text(encoding="utf-8")
ANCHORED = fixture_proposal("f32-tool-as-object").read_text(encoding="utf-8")
NAME = "ci-repair-agent-configurations/review.md"
CLOSING = {"English": "This feedback was drafted with AI tools; the swap test is one of them."}

DECORATIVE_REVIEW = """\
**Verdict: needs revision** — one blocker under the swap test.

## Proposal blockers

1. **Mendwright is decorative (swap test).** Title, purpose statement, RQ1 and RQ2
   name Mendwright, but the contribution claims configuration effects in general;
   any comparable framework leaves the research questions, the method and the
   contribution unchanged. State what the research depends on in Mendwright, or
   generalize the title and RQs to agent configurations. Either repair changes a
   research question or the contribution, so it cannot wait for the thesis.

## Clarify early in the thesis

1. **Exact model versions.** Selection rule stated; pick the release before the first run.

## Optional refinements

None.
"""

ANCHORED_REVIEW = """\
**Verdict: ready** — delta, falsifiability, swap, method-fit and executability pass.

## Proposal blockers

None.

## Clarify early in the thesis

1. **Exact model versions.** Selection rule stated; pick the release before the first run.
2. **Audit sample size.** Fixed after the pilot of twenty patches.

## Optional refinements

1. RQ1 could name Mendwright's default configuration explicitly.
"""

QUESTION_FEEDBACK = """\
**Needs revision** — address the points below and resubmit.

1. **Why Mendwright?** Your title and RQ1 and RQ2 name Mendwright. What in your
   thesis would change if a comparable framework stood in its place? Either say
   what your research depends on in it, or state the claim for agent
   configurations in general. proposal-write

**Clarify early in the thesis** — settled once the thesis starts:

- Exact model versions.

**What to keep:** the within-model design.

This feedback was drafted with AI tools; the swap test is one of them.
"""

QUIET_FEEDBACK = """\
**Ready** — no substantial revisions are needed from my side.

**Clarify early in the thesis** — settled once the thesis starts:

- Exact model versions.
- Audit sample size after the pilot.

**What to keep:** evaluating Mendwright's own default is a clear object.

This feedback was drafted with AI tools; the swap test is one of them.
"""


# ---------- review_swap_decorative -----------------------------------------------


def test_decorative_blocker_passes():
    ok, why = verdict_review_swap_decorative(DECORATIVE, DECORATIVE, DECORATIVE_REVIEW, NAME)
    assert ok, why
    assert SWAP_PAIR_TOOL in why


def test_decorative_ready_review_fails():
    ok, why = verdict_review_swap_decorative(DECORATIVE, DECORATIVE, ANCHORED_REVIEW, NAME)
    assert not ok
    assert "expected needs revision" in why


@pytest.mark.parametrize("drop", ["Mendwright", "swap test"])
def test_decorative_blocker_without_tool_or_test_fails(drop):
    review = DECORATIVE_REVIEW.replace(drop, "the framework" if drop == "Mendwright"
                                       else "delta test")
    ok, why = verdict_review_swap_decorative(DECORATIVE, DECORATIVE, review, NAME)
    assert not ok
    assert "none citing the swap test" in why


def test_decorative_swap_finding_outside_the_blockers_fails():
    review = DECORATIVE_REVIEW.replace(
        "## Proposal blockers\n\n1.", "## Proposal blockers\n\n1. Thin literature.\n\n"
        "## Optional refinements\n\n1.")
    ok, why = verdict_review_swap_decorative(DECORATIVE, DECORATIVE, review, NAME)
    assert not ok, why


def test_decorative_edited_proposal_fails():
    ok, why = verdict_review_swap_decorative(DECORATIVE, DECORATIVE + "x",
                                             DECORATIVE_REVIEW, NAME)
    assert not ok
    assert "modified the proposal" in why


# ---------- review_swap_anchored -------------------------------------------------


def test_anchored_ready_review_passes_though_the_verdict_names_swap():
    ok, why = verdict_review_swap_anchored(ANCHORED, ANCHORED, ANCHORED_REVIEW, NAME)
    assert ok, why
    assert "ready" in why


@pytest.mark.parametrize(("section", "item"), [
    ("## Proposal blockers\n\nNone.",
     "## Proposal blockers\n\n1. Mendwright fails the swap test: generalize the RQs."),
    ("2. **Audit sample size.** Fixed after the pilot of twenty patches.",
     "2. **Swap check on the name.** Confirm Mendwright is needed."),
    ("1. RQ1 could name Mendwright's default configuration explicitly.",
     "1. The title name is close to a swap-test failure; consider generalizing."),
])
def test_anchored_swap_finding_in_any_class_fails(section, item):
    review = ANCHORED_REVIEW.replace(section, item)
    ok, why = verdict_review_swap_anchored(ANCHORED, ANCHORED, review, NAME)
    assert not ok
    assert "swap-test finding" in why
    assert why.split(": ", 1)[1][:10] in item


def test_anchored_refinement_saying_the_name_passes_the_swap_test_passes():
    review = ANCHORED_REVIEW.replace(
        "1. RQ1 could name Mendwright's default configuration explicitly.",
        "1. The title names Mendwright, which passes the swap test as the object of study;\n"
        "   it still reaches the certificate, so check it reads as intended.")
    ok, why = verdict_review_swap_anchored(ANCHORED, ANCHORED, review, NAME)
    assert ok, why


def test_decorative_blocker_saying_the_name_passes_does_not_count():
    review = DECORATIVE_REVIEW.replace(
        "1. **Mendwright is decorative (swap test).**",
        "1. **Thin literature.** Mendwright passes the swap test, but the delta is thin.")
    review = review.replace("under the swap test", "under the delta test")
    ok, why = verdict_review_swap_decorative(DECORATIVE, DECORATIVE, review, NAME)
    assert not ok
    assert "none citing the swap test" in why


@pytest.mark.parametrize(("item", "cited"), [
    ("1. **Swap test — Mendwright.** Any comparable framework would do.", True),
    ("1. Mendwright fails the swap test, though it passes the delta test.", True),
    ("1. Mendwright is decorative (swap test).", True),
    ("1. Mendwright passes the swap test as the object of study.", False),
    ("1. Mendwright does not fail the swap test: the close evaluates it.", False),
    ("1. No swap-test finding on Mendwright; the title is long.", False),
    ("1. The delta is thin.", False),
    # a denied pass is a failure, and "holds"/"clears" are passes (final
    # verification, 2026-10-19; haiku wrote "The swap test holds for Mendwright")
    ("1. **Mendwright does not pass the swap test.** The gap is stated for the class.", True),
    ("1. **Swap test not passed: Mendwright.** Any comparable framework leaves it.", True),
    ("1. **Mendwright never passes the swap test as written.**", True),
    ("1. **Title length.** The swap test holds for Mendwright, since every claim is scoped "
     "to it.", False),
    ("1. **Mendwright clears the swap test as the object of study.**", False),
])
def test_swap_failure_cited(item, cited):
    assert swap_failure_cited(item) is cited


def test_anchored_reports_blockers_without_asserting_the_tier():
    review = DECORATIVE_REVIEW.replace("(swap test)", "(delta test)").replace(
        "under the swap test", "under the delta test")
    ok, why = verdict_review_swap_anchored(ANCHORED, ANCHORED, review, NAME)
    assert ok, why
    assert "needs revision" in why
    assert "1 naming Mendwright" in why


def test_anchored_review_without_sections_fails():
    ok, why = verdict_review_swap_anchored(ANCHORED, ANCHORED, "Ready.\n\n1. Fine.\n", NAME)
    assert not ok
    assert "blockers section" in why


# ---------- supervise_swap_decorative --------------------------------------------


def test_question_feedback_passes_with_the_closing_note_excluded():
    ok, why = verdict_supervise_swap_question(QUESTION_FEEDBACK, closing=CLOSING)
    assert ok, why


def test_test_name_outside_the_closing_note_fails():
    feedback = QUESTION_FEEDBACK.replace("Why Mendwright?", "Swap test on Mendwright?")
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert not ok
    assert "test name reaches the student" in why


def test_closing_note_counts_when_not_stripped():
    ok, why = verdict_supervise_swap_question(QUESTION_FEEDBACK)
    assert not ok
    assert "swap test" in why


def test_tool_point_without_a_question_fails():
    feedback = QUESTION_FEEDBACK.replace("Why Mendwright?", "Mendwright.").replace(
        "in its place?", "in its place.")
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert not ok
    assert "asks no replacement question" in why


def test_point_quoting_a_research_question_is_not_the_replacement_question():
    """f31's RQ1 names the tool and ends in "?": a point on another issue that
    quotes it verbatim asks the student no replacement question."""
    rq1 = next(line for line in DECORATIVE.splitlines() if line.startswith("1. To what degree"))
    assert SWAP_PAIR_TOOL in rq1
    assert rq1.endswith("?")
    feedback = QUESTION_FEEDBACK.replace(
        QUESTION_FEEDBACK[QUESTION_FEEDBACK.index("1. **Why"):QUESTION_FEEDBACK.index("**Clarify")],
        f"1. **RQ1 and RQ3 overlap.** RQ1 asks: \"{rq1[3:]}\" RQ3 asks the same for patch\n"
        "   size. Fold them or say what each adds. proposal-write\n\n")
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert not ok
    assert "asks no replacement question" in why


@pytest.mark.parametrize("question", [
    "Should the title name the two architectures instead?",
    "Would replacing the two opening sentences with Mendwright-scoped gaps change your aim?",
])
def test_a_repair_direction_is_no_replacement_question(question):
    """Final verification (2026-10-19): "replace" or "instead" without the name
    as its object replaces no tool."""
    feedback = QUESTION_FEEDBACK.replace(
        "What in your\n   thesis would change if a comparable framework stood in its place?",
        question)
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert not ok
    assert "asks no replacement question" in why


@pytest.mark.parametrize("question", [
    "What would change if another framework were used instead?",
    "Would anything in your thesis differ if Mendwright were replaced?",
    "Replacing Mendwright, what in the thesis would change?",
    "What would change if you used a second framework instead of Mendwright?",
])
def test_replacement_question_variants_pass(question):
    feedback = QUESTION_FEEDBACK.replace(
        "What in your\n   thesis would change if a comparable framework stood in its place?",
        question)
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert ok, why


# The point sonnet wrote on f31 in the 2026-10-13 dev run (task 5.2), verbatim:
# it asks the replacement question indirectly, and carries no "?" at all.
SONNET_POINT = (
    "1. **The name Mendwright carries claims the research does not depend on.** It appears in "
    "the title (\"Effects of Mendwright Agent Configurations on Automated Repair of Failing "
    "Continuous Integration Builds\"), in the purpose that closes the introduction, in the "
    "research focus and in RQ1 (\"Mendwright's single-agent and planner–executor "
    "configurations\"). Yet your contribution is stated for a wider group: \"What will be new "
    "is a within-model estimate of configuration effects on build repair, for teams and tool "
    "builders who choose between configurations rather than between models.\" The setup "
    "describes Mendwright only as the place the two architectures come from: \"Both "
    "architectures are taken from Mendwright, an open-source agent framework that implements "
    "them\". Please ask yourself what in the thesis would change if another framework "
    "implementing the same two architectures, with the same switch between a truncated and a "
    "full build log, stood in its place. If the answer is \"nothing in the questions, the "
    "method or the data\", the title and the questions currently promise a result about one "
    "framework while the contribution claims it for configurations in general. There are two "
    "ways to resolve this. You can state what the research depends on in Mendwright, for "
    "example that it is the only framework exposing both architectures and the log-context "
    "switch, and then claim the result for Mendwright. Or you can state the questions for "
    "their class, single-agent versus planner–executor configurations with truncated versus "
    "full build log, and keep Mendwright in the experimental setup as the instrument. The "
    "title reaches your certificate and outlives the framework, so it should name the class "
    "in the second case, for instance \"Effects of Agent Architecture and Build-Log Context on "
    "Automated Repair of Failing Continuous Integration Builds\". The choice is yours. Skill: "
    "proposal-write.")
SONNET_FEEDBACK = (
    "**Needs revision.** The core of the proposal is in place. One point blocks it from being "
    "ready.\n\n" + SONNET_POINT + "\n\n**Clarify early in the thesis.** These are settled once "
    "the thesis starts.\n- The exact release of the agent framework and the benchmark commit "
    "used.\n\nThis feedback was drafted with AI tools; the swap test is one of them.\n")
POINT_QUESTION = ("What in your\n   thesis would change if a comparable framework stood in its "
                  "place?")


def test_sonnet_indirect_replacement_question_passes():
    assert "?" not in SONNET_POINT
    ok, why = verdict_supervise_swap_question(SONNET_FEEDBACK, closing=CLOSING)
    assert ok, why
    assert "ask yourself what in the thesis would change if another framework" in why


@pytest.mark.parametrize("question", [
    "Consider what would change if another framework stood in its place.",
    "Ask yourself whether anything would differ if Mendwright were replaced.",
    "Überlegen Sie, was sich ändern würde, wenn ein vergleichbares Framework an seiner "
    "Stelle stünde.",
    "Fragen Sie sich, ob ein vergleichbares Framework dieselben Ergebnisse liefern würde.",
])
def test_indirect_replacement_question_variants_pass(question):
    feedback = QUESTION_FEEDBACK.replace(POINT_QUESTION, question)
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert ok, why


@pytest.mark.parametrize("question", [
    "Please ask yourself what in the thesis depends on Mendwright.",
    "Überlegen Sie, was Ihre Arbeit von Mendwright braucht.",
    "Ask yourself what depends on it. Another option is to generalize.",
])
def test_indirect_question_without_a_contrast_fails(question):
    """The contrast cue must sit in the sentence that asks; a contrast word in
    a neighbouring sentence does not make a question of it."""
    feedback = QUESTION_FEEDBACK.replace(POINT_QUESTION, question)
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert not ok
    assert "asks no replacement question" in why


def test_indirect_cue_before_a_quoted_research_question_is_not_the_replacement_question():
    rq1 = next(line for line in DECORATIVE.splitlines() if line.startswith("1. To what degree"))
    feedback = QUESTION_FEEDBACK.replace(
        QUESTION_FEEDBACK[QUESTION_FEEDBACK.index("1. **Why"):QUESTION_FEEDBACK.index("**Clarify")],
        f"1. **RQ1 and RQ3 overlap.** Consider what RQ1 asks: \"{rq1[3:]}\" Then ask yourself\n"
        "   whether RQ3 asks the same for patch size. proposal-write\n\n")
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert not ok
    assert "asks no replacement question" in why


def test_no_point_on_the_tool_fails():
    feedback = QUESTION_FEEDBACK.replace("Mendwright", "the framework")
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert not ok
    assert "none naming Mendwright" in why


def test_question_feedback_opening_ready_fails():
    ok, why = verdict_supervise_swap_question(QUIET_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "expected needs revision" in why


# ---------- supervise_swap_anchored ----------------------------------------------


def test_quiet_feedback_passes():
    ok, why = verdict_supervise_swap_quiet(QUIET_FEEDBACK)
    assert ok, why


def test_anchored_feedback_opening_needs_revision_fails():
    ok, why = verdict_supervise_swap_quiet(QUESTION_FEEDBACK)
    assert not ok
    assert "needs revision" in why


def test_anchored_feedback_carrying_a_point_fails_and_quotes_it():
    feedback = QUIET_FEEDBACK.replace(
        "**Clarify early", "1. Why Mendwright and not another framework?\n\n**Clarify early")
    ok, why = verdict_supervise_swap_quiet(feedback)
    assert not ok
    assert "Why Mendwright" in why


# ---------- numbered points --------------------------------------------------------


def test_points_fold_continuations_and_stop_at_the_next_paragraph():
    points = numbered_points(QUESTION_FEEDBACK)
    assert len(points) == 1
    assert points[0].endswith("proposal-write")
    assert "Clarify" not in points[0]


def test_points_split_on_each_number():
    assert len(numbered_points("Intro.\n\n1. One.\n   more\n2) Two?\n\nAfter.\n")) == 2


# ---------- the pair stays minimal ------------------------------------------------


CLOSE_LINES = 3


def contribution_bounds(lines: list[str]) -> tuple[int, int]:
    """Index of the contribution heading and one past its last non-blank line."""
    start = next(i for i, line in enumerate(lines)
                 if line.startswith("## Contribution to the State-of-the-Art"))
    end = next(i for i in range(start + 1, len(lines)) if lines[i].startswith("## "))
    return start, max(i for i in range(start, end) if lines[i].strip()) + 1


def contribution_close_problems(a: str, b: str, close_lines: int = CLOSE_LINES) -> list[str]:
    """Why two proposal texts are not a minimal pair: every differing line must
    sit among the last `close_lines` sentence-lines of the contribution
    section, and the pair must differ somewhere."""
    lines_a = a.splitlines()
    _, body_end = contribution_bounds(lines_a)
    close = range(body_end - close_lines, body_end)
    matcher = difflib.SequenceMatcher(a=lines_a, b=b.splitlines(), autojunk=False)
    changed = [(tag, i1, i2) for tag, i1, i2, _, _ in matcher.get_opcodes() if tag != "equal"]
    if not changed:
        return ["the pair is identical"]
    return [f"line {i1 + 1}: {tag} outside the contribution close"
            for tag, i1, i2 in changed
            if not (i1 >= close.start and max(i2, i1 + 1) <= close.stop)]


def test_the_pair_differs_only_in_the_contribution_close():
    assert contribution_close_problems(DECORATIVE, ANCHORED) == []


def test_the_pair_check_catches_an_edit_elsewhere(tmp_path: Path):
    edited = tmp_path / "ci-repair-agent-configurations.md"
    edited.write_text(ANCHORED.replace("either Mendwright configuration",
                                       "either configuration"), encoding="utf-8")
    problems = contribution_close_problems(DECORATIVE, edited.read_text(encoding="utf-8"))
    assert problems
    assert "outside the contribution close" in problems[0]


def test_the_pair_check_catches_an_identical_copy(tmp_path: Path):
    copy = tmp_path / "ci-repair-agent-configurations.md"
    copy.write_text(DECORATIVE, encoding="utf-8")
    assert contribution_close_problems(DECORATIVE, copy.read_text(encoding="utf-8"))


def test_both_halves_name_the_tool_where_the_design_puts_it():
    """Title, purpose statement, research focus, RQ1, RQ2 and the method sentence."""
    for text in (DECORATIVE, ANCHORED):
        assert text.splitlines()[0].startswith(f"# Effects of {SWAP_PAIR_TOOL} ")
        assert text.count(SWAP_PAIR_TOOL) >= 6
    assert "configuration effects on build repair, for teams and tool builders" in DECORATIVE
    assert f"evaluates {SWAP_PAIR_TOOL} itself" in ANCHORED


# ---------- the Bachelor's claim-scope pair stays minimal --------------------------


SETTING = fixture_proposal("f34-named-setting").read_text(encoding="utf-8")
MIXED = fixture_proposal("f33-mixed-scope").read_text(encoding="utf-8")


def test_the_bachelor_pair_differs_only_by_lines_added_to_the_contribution():
    """f33 is f34 plus class-scoped gap sentences inside the contribution section,
    so a verdict difference between them can only come from the claim scope."""
    lines = SETTING.splitlines()
    start, body_end = contribution_bounds(lines)
    assert contribution_close_problems(SETTING, MIXED, close_lines=body_end - start - 1) == []
    matcher = difflib.SequenceMatcher(a=lines, b=MIXED.splitlines(), autojunk=False)
    assert {tag for tag, *_ in matcher.get_opcodes() if tag != "equal"} == {"insert"}


def test_both_bachelor_halves_carry_the_same_names_and_bait():
    for text in (SETTING, MIXED):
        assert text.splitlines()[0].startswith(f"# Effects of {SWAP_PAIR_TOOL} ")
        assert "*Bachelor's Thesis Proposal*" in text
        assert f"team whose continuous integration pipeline already runs {SWAP_PAIR_TOOL}" in text
        assert f"Every run executes in {SWAP_PAIR_TOOL}'s sandbox" in text
        assert f"either {SWAP_PAIR_TOOL} configuration" in text
    assert SETTING.count(SWAP_PAIR_TOOL) == MIXED.count(SWAP_PAIR_TOOL)
    assert "fills that gap" not in SETTING


# ---------- earlier rounds and listed passes (claim-scope coverage) --------------


MISSED_REVIEW = """\
**Verdict: needs revision** — one blocker under the swap test.

## Earlier round

1. **API budget for the second model** — resolved: the revision runs one model on the
   group's own server.
2. **Title naming Mendwright** — the earlier round kept it as a title refinement without
   holding it to the swap test; it fails now and is missed in the earlier round.

## Proposal blockers

1. **Mendwright's claim scope is undecided (swap test).** The contribution opens with
   "Evaluations of agent configurations for build repair that hold the model fixed are
   missing altogether" while the close is scoped to Mendwright, and nothing says why the
   result is about Mendwright. Scope every gap to Mendwright, say why the result is
   about it, or state the claim for agent configurations.

## Clarify early in the thesis

1. **Exact model version.** Selection rule stated.

## Verification

Verified by: fresh verifier
"""

NEW_POINT_FEEDBACK = QUESTION_FEEDBACK.replace("1. **Why Mendwright?**",
                                               "1. **New: why Mendwright?**")


def test_missed_blocker_with_a_new_point_passes():
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, NEW_POINT_FEEDBACK, closing=CLOSING)
    assert ok, why
    assert "missed in the earlier round" in why


def test_a_bold_label_is_its_own_sentence():
    """Regression (opus dev run on w17, round 6): the label citing the swap
    test ran into the next sentence, whose "passed … without the swap test"
    cancelled it."""
    blocker = ("1. **Mendwright is named in every claim, but the proposal never states why the "
               "result is about Mendwright (swap test) — missed in the earlier round.** The "
               "earlier round passed the name as the object of study in a title refinement "
               "without the swap test; that remark passes nothing.")
    assert swap_failure_cited(blocker)
    review = MISSED_REVIEW.replace(
        MISSED_REVIEW[MISSED_REVIEW.index("1. **Mendwright's claim scope"):
                      MISSED_REVIEW.index("## Clarify early")], blocker + "\n\n")
    ok, why = verdict_supervise_swap_missed(review, NEW_POINT_FEEDBACK, closing=CLOSING)
    assert ok, why


def test_missed_label_in_the_blocker_itself_passes():
    review = MISSED_REVIEW.replace("it fails now and is missed in the earlier round",
                                   "it fails now").replace(
        "(swap test).**", "(swap test, missed in the earlier round).**")
    ok, why = verdict_supervise_swap_missed(review, NEW_POINT_FEEDBACK, closing=CLOSING)
    assert ok, why


def test_missed_verdict_fails_without_the_label():
    review = MISSED_REVIEW.replace("and is missed in the earlier round", "")
    ok, why = verdict_supervise_swap_missed(review, NEW_POINT_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "not recorded as missed" in why


def test_missed_verdict_fails_without_an_earlier_round_section():
    review = MISSED_REVIEW.replace("## Earlier round", "## Background")
    ok, why = verdict_supervise_swap_missed(review, NEW_POINT_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "earlier-round section" in why


def test_a_new_point_announced_in_the_opening_counts():
    """Regression (sonnet dev run on w17, 2026-10-19): the feedback said "One
    point is new; it concerns the role of Mendwright" before the point."""
    announced = QUESTION_FEEDBACK.replace(
        "address the points below and resubmit.",
        "address the point below and resubmit. One point is new; it concerns Mendwright.")
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, announced, closing=CLOSING)
    assert ok, why


def test_a_point_announced_as_not_raised_before_counts():
    """Regression (sonnet dev run on w17, 2026-10-19): "The point below was not
    raised in the first round; it concerns the name Mendwright"."""
    announced = QUESTION_FEEDBACK.replace(
        "address the points below and resubmit.",
        "address the points below and resubmit. The point below was not raised in the "
        "first round; it concerns the name Mendwright.")
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, announced, closing=CLOSING)
    assert ok, why


def test_a_question_described_to_the_student_counts():
    """Regression (sonnet dev run on f33, 2026-10-19): "a reader can ask what
    would change if another framework implementing them stood in its place"."""
    described = QUESTION_FEEDBACK.replace(
        "What in your\n   thesis would change if a comparable framework stood in its place?",
        "A reader can ask what would change if another framework stood in its place.")
    ok, why = verdict_supervise_swap_question(described, closing=CLOSING)
    assert ok, why


SUPPOSED = ("Suppose another open-source framework stood in Mendwright's place. What in "
            "your\n   thesis would change?")


@pytest.mark.parametrize("asked", [
    SUPPOSED,
    "Try putting another framework in Mendwright's place. The questions would stay the\n"
    "   same. So what in the thesis would change?",
    "Try a test. Imagine a comparable framework instead. What would change?",
    'You write "the gap is missing altogether." Try putting another framework in its '
    "place. What would change?",
])
def test_a_question_after_a_supposed_replacement_counts(asked):
    """Regression (opus dev runs on f31, f33 and w17, 2026-10-19): the
    replacement supposed in one sentence, the question asked in the next or
    the one after."""
    feedback = QUESTION_FEEDBACK.replace(
        "What in your\n   thesis would change if a comparable framework stood in its place?",
        asked)
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert ok, why


@pytest.mark.parametrize("asked", [
    "Suppose the team keeps Mendwright. What in your\n   thesis would change?",
    "Suppose another framework stood in its place. It would run. It would log. "
    "What would change?",
    # a repair direction or an idiom makes no replacement (final review, 2026-10-19)
    "Put another way, the proposal claims two different results. Which one do you mean?",
    "Replace the two opening sentences with gaps scoped to Mendwright. Which of these fits?",
    "Try replacing the two opening sentences with gaps scoped to Mendwright. Which fits?",
])
def test_a_supposition_without_contrast_or_out_of_reach_does_not_count(asked):
    feedback = QUESTION_FEEDBACK.replace(
        "What in your\n   thesis would change if a comparable framework stood in its place?",
        asked)
    ok, why = verdict_supervise_swap_question(feedback, closing=CLOSING)
    assert not ok
    assert "asks no replacement question" in why


def test_new_elsewhere_in_the_opening_does_not_count():
    opening = QUESTION_FEEDBACK.replace(
        "address the points below and resubmit.",
        "address the points below and resubmit. The new evaluation plan holds.")
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, opening, closing=CLOSING)
    assert not ok
    assert "not marked new" in why


def test_missed_verdict_fails_when_the_point_is_not_marked_new():
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, QUESTION_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "not marked new" in why


def test_a_pass_listed_under_verification_is_no_blocker():
    entry = "Swap test — Mendwright: missed in the earlier round."
    assert swap_failure_cited(entry)  # it would count as a blocker, were it one
    review = MISSED_REVIEW.split("## Proposal blockers")[0] + (
        f"## Proposal blockers\n\nNone.\n\n## Verification\n\n- {entry}\n")
    ok, why = verdict_supervise_swap_missed(review, NEW_POINT_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "no swap-test blocker" in why


@pytest.mark.parametrize("head", [
    "1. **Not new: why Mendwright?**",
    "1. **Why Mendwright?** (no new point)",
    '1. **Why Mendwright?** You write "What will be new is the comparison".',
])
def test_a_negated_or_quoted_new_is_no_mark(head):
    feedback = QUESTION_FEEDBACK.replace("1. **Why Mendwright?**", head)
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, feedback, closing=CLOSING)
    assert not ok
    assert "not marked new" in why


def test_a_quote_running_past_the_head_marks_nothing():
    """Final review (2026-10-19): a proposal quote opening inside the point's
    first 200 characters and closing after them must not leave its "new"."""
    head = ("1. **Why Mendwright?** Mendwright stands in your title, your research focus "
            "and both research questions, and you write \"What will be new is a within-model "
            "estimate of how Mendwright's two architectures differ on build repair.\"")
    assert head.index('"') < 200 < head.rindex('"')
    feedback = QUESTION_FEEDBACK.replace("1. **Why Mendwright?**", head)
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, feedback, closing=CLOSING)
    assert not ok
    assert "not marked new" in why
    ok, why = verdict_supervise_point_kept(KEPT_REVIEW, feedback, closing=CLOSING)
    assert ok, why


@pytest.mark.parametrize("opening", [
    "Your revision resolves the earlier point: the new setup runs on one model.",
    "Please address the point below and send a new version.",
    "The neutral comparison stays; one point remains.",
])
def test_new_beside_a_point_in_the_opening_is_no_mark(opening):
    feedback = QUESTION_FEEDBACK.replace("address the points below and resubmit.", opening)
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, feedback, closing=CLOSING)
    assert not ok
    assert "not marked new" in why
    ok, why = verdict_supervise_point_kept(KEPT_REVIEW, feedback, closing=CLOSING)
    assert ok, why


def test_a_paraphrase_of_what_will_be_new_is_no_mark():
    """Final verification (2026-10-19): the proposal's own sentence, unquoted in
    the point's first sentence, is no new-point mark."""
    head = ("1. **Why Mendwright?** You say what will be new is a within-model estimate "
            "for Mendwright.")
    feedback = QUESTION_FEEDBACK.replace("1. **Why Mendwright?**", head)
    ok, why = verdict_supervise_point_kept(KEPT_REVIEW, feedback, closing=CLOSING)
    assert ok, why
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, feedback, closing=CLOSING)
    assert not ok
    assert "not marked new" in why


def test_a_parenthesis_marking_the_point_new_counts():
    """Regression (opus dev run on w17, round 6): "Why Mendwright? (new, missed
    in the earlier round)"."""
    feedback = QUESTION_FEEDBACK.replace(
        "1. **Why Mendwright?**", "1. **Why Mendwright? (new, missed in the earlier round).**")
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, feedback, closing=CLOSING)
    assert ok, why


def test_a_new_point_remaining_open_counts():
    """Regression (opus dev run on w17, round 4): "One new point remains open.
    My earlier feedback should have raised it and did not"."""
    feedback = QUESTION_FEEDBACK.replace(
        "address the points below and resubmit.",
        "address the point below and resubmit. One new point remains open.")
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, feedback, closing=CLOSING)
    assert ok, why


def test_a_german_new_mark_counts():
    feedback = QUESTION_FEEDBACK.replace("1. **Why Mendwright?**",
                                         "1. **Neuer Punkt: why Mendwright?**")
    ok, why = verdict_supervise_swap_missed(MISSED_REVIEW, feedback, closing=CLOSING)
    assert ok, why


KEPT_REVIEW = """\
**Verdict: needs revision** — one blocker under the swap test.

## Earlier round

1. **Mendwright's role (swap test)** — open: the passages the point concerned are unchanged,
   and the claim scope is still undecided.

## Proposal blockers

1. **Mendwright's claim scope is undecided (swap test).** As in the earlier round.
"""


def test_kept_point_passes():
    ok, why = verdict_supervise_point_kept(KEPT_REVIEW, QUESTION_FEEDBACK, closing=CLOSING)
    assert ok, why


def test_a_point_listed_not_resolved_counts_as_open():
    review = KEPT_REVIEW.replace("open: the passages", "not resolved: the passages")
    ok, why = verdict_supervise_point_kept(review, QUESTION_FEEDBACK, closing=CLOSING)
    assert ok, why


@pytest.mark.parametrize("status", [
    "open: the passages are unchanged, so there is no ground to withdraw or demote it,",
    "open, not withdrawn: the passages are unchanged,",
    # a withdrawal of something else after the status (final verification)
    "open: the passages are unchanged; the earlier round withdrew its budget blocker,",
    "open: on unchanged text it can't be withdrawn or demoted,",
])
def test_a_negated_withdrawal_keeps_the_point_open(status):
    review = KEPT_REVIEW.replace("open: the passages the point concerned are unchanged,", status)
    ok, why = verdict_supervise_point_kept(review, QUESTION_FEEDBACK, closing=CLOSING)
    assert ok, why


def test_a_redo_feedback_marking_the_point_new_fails():
    ok, why = verdict_supervise_point_kept(KEPT_REVIEW, NEW_POINT_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "marks the point new" in why


@pytest.mark.parametrize("status", [
    "withdrawn: the Bachelor's named-setting clause passes the setting-scoped close",
    "resolved: the close claims its result for the setting",
    "partly resolved: demoted to an optional refinement",
    "open in the earlier round, now withdrawn: the setting-scoped close carries it",
    "open, demoted to an optional refinement",
])
def test_withdrawn_or_demoted_point_fails_even_with_a_reason(status):
    review = KEPT_REVIEW.replace("open: the passages the point concerned are unchanged,",
                                 status + ",")
    ok, why = verdict_supervise_point_kept(review, QUESTION_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "not listed open" in why


def test_kept_point_written_as_prose_passes():
    """Regression (sonnet dev run on w18, 2026-10-19): the earlier round as one
    paragraph, the point's status after a dash, other points after a semicolon."""
    prose = KEPT_REVIEW.replace(
        "1. **Mendwright's role (swap test)** — open: the passages the point concerned are "
        "unchanged,\n   and the claim scope is still undecided.",
        "The text is unchanged. Earlier points: the Mendwright role (swap test) — open; "
        "model release — open, clarify early.")
    ok, why = verdict_supervise_point_kept(prose, QUESTION_FEEDBACK, closing=CLOSING)
    assert ok, why


def test_prose_earlier_round_with_a_withdrawn_point_fails():
    prose = KEPT_REVIEW.replace(
        "1. **Mendwright's role (swap test)** — open: the passages the point concerned are "
        "unchanged,\n   and the claim scope is still undecided.",
        "Earlier points: the Mendwright role (swap test) — withdrawn; model release — open.")
    ok, why = verdict_supervise_point_kept(prose, QUESTION_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "not listed open" in why


def test_kept_point_fails_when_the_feedback_drops_it():
    ok, why = verdict_supervise_point_kept(KEPT_REVIEW, QUIET_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "expected needs revision" in why


def test_kept_point_fails_without_an_earlier_item_on_the_tool():
    review = KEPT_REVIEW.replace("Mendwright's role (swap test)", "The framework's role")
    ok, why = verdict_supervise_point_kept(review, QUESTION_FEEDBACK, closing=CLOSING)
    assert not ok
    assert "no earlier-round item" in why


GAP_QUOTE = ("None of these studies has measured how Mendwright's own two architectures "
             "differ on build repair with the model held fixed.")
LISTED_REVIEW = f"""\
**Verdict: ready.**

## Proposal blockers

None.

## Verification

Verified by: fresh verifier

- Swap-test pass, Mendwright, object of study by the scope of its claims: "{GAP_QUOTE}"
"""


def test_pass_listed_with_a_proposal_quote_passes():
    ok, why = verdict_supervise_pass_listed(LISTED_REVIEW, SETTING)
    assert ok, why


@pytest.mark.parametrize(("review", "cue"), [
    (LISTED_REVIEW.replace(GAP_QUOTE, "Mendwright is the obvious object of this thesis."),
     "quotes nothing"),
    (LISTED_REVIEW.replace(GAP_QUOTE, "two architectures differ"), "quotes nothing"),
    (LISTED_REVIEW.replace("Mendwright, object", "the framework, object").replace(
        GAP_QUOTE, "None of these studies has measured how the architectures differ."),
     "names no pass"),
    (LISTED_REVIEW.split("## Verification")[0], "no verification section"),
])
def test_pass_listing_without_a_verbatim_quote_fails(review, cue):
    ok, why = verdict_supervise_pass_listed(review, SETTING)
    assert not ok
    assert cue in why


@pytest.mark.parametrize("review", [
    LISTED_REVIEW.replace("## Verification", "## 5. Verification"),
    LISTED_REVIEW.replace("## Verification", "### Claim verification"),
    LISTED_REVIEW.replace(GAP_QUOTE, "None of these studies has measured how Mendwright's own "
                                     "two architectures … with the model held fixed."),
    LISTED_REVIEW.replace(GAP_QUOTE, "None ... has measured how Mendwright's own two "
                                     "architectures differ ... held fixed"),
    LISTED_REVIEW.replace(f'- Swap-test pass, Mendwright, object of study by the scope of its '
                          f'claims: "{GAP_QUOTE}"',
                          f'- Swap-test pass, Mendwright, object of study by the scope of its '
                          f'claims:\n  - gap: "{GAP_QUOTE}"'),
])
def test_pass_listing_under_other_layouts_passes(review):
    """A numbered or `### Claim verification` heading, an elided quote whose
    pieces are verbatim, and a quote in a sub-bullet of the entry naming the
    tool all carry the pass."""
    ok, why = verdict_supervise_pass_listed(review, SETTING)
    assert ok, why


def test_a_pass_lead_in_with_nested_claims_carries_the_pass():
    """Regression (opus dev run on f34, round 9): the pass under a colon-ended
    lead-in, its quotes in sub-bullets of a top-level bullet. A second
    `_LIST_ITEM` defined later in l1_checks, anchored to one line, made that
    bullet read as no list item, so the lead-in was dropped."""
    review = LISTED_REVIEW.replace(
        f'- Swap-test pass, Mendwright, object of study by the scope of its claims: "{GAP_QUOTE}"',
        "Swap-test pass — Mendwright (object of study; every claim instance-scoped):\n"
        "- Comparable alternative put in its place: another open-source framework.\n"
        f'- Claims, each with scope, all instance:\n  - Gap: "{GAP_QUOTE}" — instance.\n'
        "  - RQ2: about either Mendwright configuration — instance.")
    ok, why = verdict_supervise_pass_listed(review, SETTING)
    assert ok, why


HEADED_PASS = f"""\
**Verdict: ready.**

## Proposal blockers

None.

## Verification

Verified by: fresh verifier

### Swap-test pass — Mendwright

Replacement: another open-source framework offering both architectures.

Claims the test covers, each with its scope (all: the named instance):
- Gap: "{GAP_QUOTE}" — instance.
- RQ2: either Mendwright configuration — instance.
"""


def test_a_pass_sub_heading_leads_the_chunks_under_it():
    """Final verification (opus dev run on f34, round 8): the pass under a
    `###` sub-heading, its quotes in bullets under a lead-in that names neither
    the test nor a pass."""
    ok, why = verdict_supervise_pass_listed(HEADED_PASS, SETTING)
    assert ok, why


def test_text_listed_as_excluded_carries_no_pass():
    """Final verification (opus dev run on f34, round 8): its recorded PASS came
    from the paragraph listing what the pass does not rest on."""
    excluded = HEADED_PASS.replace(
        "Claims the test covers, each with its scope (all: the named instance):\n"
        f'- Gap: "{GAP_QUOTE}" — instance.\n- RQ2: either Mendwright configuration — instance.\n',
        f'Not counted (introduction motivation): "{GAP_QUOTE}" is not relied on for the pass.\n')
    ok, why = verdict_supervise_pass_listed(excluded, SETTING)
    assert not ok
    assert "quotes nothing" in why


def test_no_claim_left_out_is_no_exclusion():
    """Regression (sonnet dev run on f34, round 5): "… and no claim left out;
    no dispute of the pass" lists nothing as excluded."""
    review = LISTED_REVIEW.replace(
        f'- Swap-test pass, Mendwright, object of study by the scope of its claims: "{GAP_QUOTE}"',
        f'Swap-test pass (Mendwright): carried by "{GAP_QUOTE}"; the verifier found every '
        "quoted sentence and no claim left out.")
    ok, why = verdict_supervise_pass_listed(review, SETTING)
    assert ok, why


def test_a_dispute_bullet_quoting_the_tool_is_no_pass_entry():
    """Final review (sonnet dev run on f34, round 5): the pass line pointed
    back to the ledger and quoted nothing, and a verifier-dispute bullet that
    quoted a Mendwright sentence carried the verdict."""
    review = LISTED_REVIEW.replace(
        f'- Swap-test pass, Mendwright, object of study by the scope of its claims: "{GAP_QUOTE}"',
        f'- Gap quote cut before the Mendwright qualifier — accepted; quote extended to '
        f'"{GAP_QUOTE}"\n- Swap-test pass (Mendwright): carried by the quoted gap sentence in '
        f'the ledger above.')
    ok, why = verdict_supervise_pass_listed(review, SETTING)
    assert not ok
    assert "quotes nothing" in why


def test_a_pass_lead_in_lends_its_bullets_the_pass():
    review = LISTED_REVIEW.replace(
        f'- Swap-test pass, Mendwright, object of study by the scope of its claims: "{GAP_QUOTE}"',
        f'Swap-test pass, Mendwright, carried by:\n\n- the gap: "{GAP_QUOTE}"')
    ok, why = verdict_supervise_pass_listed(review, SETTING)
    assert ok, why
    no_colon = review.replace("Verified by: fresh verifier", "Verified by: fresh verifier; "
                              "twelve claims passed").replace("carried by:", "listed below.")
    ok, why = verdict_supervise_pass_listed(no_colon, SETTING)
    assert not ok


def test_a_top_level_entry_does_not_lend_its_quote_to_the_next():
    review = LISTED_REVIEW.replace(
        f'- Swap-test pass, Mendwright, object of study by the scope of its claims: "{GAP_QUOTE}"',
        '- Executability pass: "A repair counts as accepted when the build, the originally '
        'failing test and the project\'s other tests pass in a fresh container"\n'
        '- Swap-test pass, Mendwright: object of study.')
    assert "the originally failing test and the project's other tests" in SETTING
    ok, why = verdict_supervise_pass_listed(review, SETTING)
    assert not ok
    assert "quotes nothing" in why


STAGED = {"review.md": "earlier review\n", "feedback.md": "earlier feedback\n"}
STAGED_POINTS = {"review.md": "earlier review\n",
                 "feedback.md": "**Needs revision**\n\n1. **Why Mendwright?** Decide the scope.\n"}


def test_rewritten_earlier_round_passes():
    written = {"slug/review.md": "new review\n", "slug/feedback.md": "new feedback\n"}
    ok, why = verdict_earlier_round_rewritten(written, STAGED)
    assert ok, why


def test_staged_feedback_left_in_place_fails():
    written = {"slug/review.md": "new review\n", "slug/feedback.md": "earlier feedback\n"}
    ok, why = verdict_earlier_round_rewritten(written, STAGED)
    assert not ok
    assert "not rewritten" in why


def test_a_second_proposal_folder_fails():
    written = {"slug/review.md": "earlier review\n", "slug/feedback.md": "earlier feedback\n",
               "other/review.md": "new review\n", "other/feedback.md": "new feedback\n"}
    ok, why = verdict_earlier_round_rewritten(written, STAGED)
    assert not ok
    assert "expected one" in why


def test_a_second_proposal_folder_named_by_the_runner_fails():
    written = {"slug/review.md": "new review\n", "slug/feedback.md": "new feedback\n"}
    ok, why = verdict_earlier_round_rewritten(written, STAGED,
                                              ["other/other.md", "slug/slug.md"])
    assert not ok
    assert "2 proposal folder(s)" in why


def test_nothing_staged_fails():
    ok, why = verdict_earlier_round_rewritten({"slug/review.md": "new review\n"}, {})
    assert not ok
    assert "no earlier round was staged" in why


def test_a_feedback_that_keeps_the_staged_points_fails():
    kept = STAGED_POINTS["feedback.md"].replace("**Needs revision**",
                                                "**Needs revision** — resubmit.")
    written = {"slug/review.md": "new review\n", "slug/feedback.md": kept}
    ok, why = verdict_earlier_round_rewritten(written, STAGED_POINTS, ["slug/slug.md"])
    assert not ok
    assert "keeps the staged points verbatim" in why
    written["slug/feedback.md"] = kept.replace("Decide the scope.", "Scope every gap to it.")
    ok, why = verdict_earlier_round_rewritten(written, STAGED_POINTS, ["slug/slug.md"])
    assert ok, why
