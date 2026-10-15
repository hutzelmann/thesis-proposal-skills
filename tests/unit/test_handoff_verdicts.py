"""L0: the stage-handoff verdicts (testing-harness spec: handoff coverage).

The chats below are the agreed examples from the design conversation, trimmed,
plus the shapes a model drifts into: two next steps, a skill name, a closing
pleasantry after the handoff.
"""

import pytest
from l1_checks import (
    handoff_lines,
    has_quoted_phrase,
    next_step,
    verdict_handoff,
    verdict_handoff_after_revision,
    verdict_handoff_ready,
    verdict_handoff_review_feedback,
    verdict_handoff_superseded,
    verdict_handoff_untouched,
)

BODY = "Verdict: needs revision. Two blockers: RQ2 cannot fail as phrased; RQ3 needs access.\n\n"
REVISION = (
    BODY
    + "**Where it stands:** two blockers stand between the draft and a supervisor discussion.\n"
    + '**Next:** work the two blockers into the draft, then a fresh review. Reply "yes", or '
    + 'send: "Apply the two blockers from the review."\n'
    + "**Or:** include refinements 1 and 3 in the same pass.\n"
    + "**Or:** settle the access with the partner first.\n"
)
SUPERSEDED = (
    "Check: 0 errors, 2 advisory warnings.\n\n"
    "Where it stands: complete draft, mechanically valid. The review on file judged the "
    "earlier design with four research questions and two sites.\n"
    'Next: a fresh review of the narrowed draft, review only. Reply "yes", or send: '
    '"Review my proposal — review only, no edits."\n'
)
GERMAN = (
    "Stand: vollständiger Entwurf; das vorliegende Review bewertet die frühere Fassung.\n"
    "Als Nächstes: ein neues Review des eingegrenzten Entwurfs. Antworte „ja“ oder schick: "
    "„Reviewe mein Exposé, ohne Änderungen.“\n"
)
READY = (
    "Where it stands: ready for supervisor discussion.\n"
    'Next: a final language check, then the PDF. Send: "Check my proposal before I hand it in."\n'
    'Or: skip the PDF and hand in the markdown: "Make a hand-in export."\n'
)


def test_agreed_examples_pass():
    for chat in (REVISION, SUPERSEDED, GERMAN, READY):
        ok, why = verdict_handoff(chat)
        assert ok, why


def test_lines_parsed_in_order_with_kinds():
    assert [kind for kind, _ in handoff_lines(REVISION)] == ["where", "next", "or", "or"]
    assert next_step(GERMAN).startswith("ein neues Review")


def test_list_and_blank_line_variants_parse():
    chat = "Body.\n\n- **Where it stands**: draft.\n\n- **Next**: a review. Send: \"Review it.\"\n"
    assert [kind for kind, _ in handoff_lines(chat)] == ["where", "next"]


@pytest.mark.parametrize(("chat", "fragment"), [
    ("All done, the review file is written.\n", "does not close"),
    (REVISION + "\nLet me know how you want to proceed!\n", "does not close"),
    ("Next: a review.\nNext: a revision.\n", "2 Next lines"),
    ("Next: a review.\nOr: a.\nOr: b.\nOr: c.\n", "3 Or lines"),
    ("Where it stands: a.\nWhere it stands: b.\nNext: c.\n", "2 Where"),
    ("Or: a revision.\nNext: a review.\n", "out of order"),
    ("Next: use proposal-review on the narrowed draft.\n", "a skill is named"),
    ("Next: run the review skill on the narrowed draft.\n", "a skill is named"),
    ("Where it stands: " + "word " * 210 + "\nNext: a review.\n", "words, cap"),
    ("Where it stands: a draft.\n", "0 Next lines"),
    ('Next: a fresh review. Send: "Review it."\n', "0 Where-it-stands lines"),
    ("Where it stands: a draft.\nNext:\n", "empty next line"),
    ("Where it stands: a draft.\nNext: a review.\nOr:\n", "empty or line"),
    ("Where it stands: a draft.\nNext: ask den Review-Skill.\n", "a skill is named"),
    ("Where it stands: a draft.\nNext: run your review skill again.\n", "a skill is named"),
])
def test_format_failures(chat, fragment):
    ok, why = verdict_handoff(chat)
    assert not ok
    assert fragment in why


@pytest.mark.parametrize("next_text", [
    "send the proposal-ready draft to your supervisor.",
    "überarbeite den Proposal-Entwurf.",
    "decide which soft skills the survey measures.",
])
def test_ordinary_words_are_not_skill_names(next_text):
    ok, why = verdict_handoff(f"Where it stands: a draft.\nNext: {next_text}\n")
    assert ok, why


def test_quoted_phrase_accepts_single_quotes_and_backticks_but_not_apostrophes():
    assert has_quoted_phrase("Send: 'Review my proposal.'")
    assert has_quoted_phrase("Send `Review my proposal`.")
    assert not has_quoted_phrase("Don't worry, it's fine.")


def test_alternatives_listed_under_an_empty_or_label_count_one_each():
    """The shape sonnet chose on 2026-10-13: the cap is on alternatives, not lines."""
    listed = ("Where it stands: a draft.\nNext: settle the timeline. Send: \"Start May.\"\n\n"
              "**Or:**\n- \"Pick the rater\": options laid out.\n- \"Review it now\".\n")
    assert [kind for kind, _ in handoff_lines(listed)] == ["where", "next", "or", "or"]
    assert verdict_handoff(listed)[0]
    three = listed + "- \"Fix the DOIs\".\n"
    ok, why = verdict_handoff(three)
    assert not ok
    assert "3 Or lines" in why


def test_a_closing_list_under_no_label_is_no_handoff():
    assert handoff_lines("Next: a review.\n\nSteps:\n- one\n- two\n") == []


def test_options_listed_under_next_continue_it():
    """Haiku's anchored choice on 2026-10-13: the options as a list under `Next:`,
    then the alternatives as `Or:` lines."""
    chat = ("Where it stands: five markers open.\n"
            "Next: decide who rates maintainability (line 58). Reply with one option:\n"
            "- \"the student's own audit\"\n- \"the partner's engineers\"\n"
            "- \"or something else\"\n\n"
            "Or: state the start and submission months.\n"
            "Or: move the audit sample size marker to the notes file.\n")
    lines = handoff_lines(chat)
    assert [kind for kind, _ in lines] == ["where", "next", "or", "or"]
    assert lines[1][1].endswith("\"the student's own audit\" \"the partner's engineers\" "
                                "\"or something else\"")
    assert verdict_handoff(chat)[0]


def test_a_list_above_the_closing_lines_stays_in_the_body():
    chat = ("Findings:\n- one\n- two\n"
            "Where it stands: a draft.\nNext: a review. Send: \"Review it.\"\n")
    assert [kind for kind, _ in handoff_lines(chat)] == ["where", "next"]


def test_mid_ideation_stocktake_is_not_a_handoff():
    """'Standing:' is the ideation stocktake, not the German position label."""
    assert handoff_lines("Standing: problem and method. Open: feasibility.\n") == []


def test_quoted_phrase_recognized_in_three_quote_styles():
    assert has_quoted_phrase('Send: "Review my proposal."')
    assert has_quoted_phrase("Send: “Review my proposal.”")
    assert has_quoted_phrase("Schick: „Reviewe mein Exposé.“")
    assert not has_quoted_phrase("Rename it and send it to your supervisor.")


# ---------- scenario verdicts ----------------------------------------------------

P, R = "draft/draft.md", "draft/review.md"


def test_review_feedback():
    assert verdict_handoff_review_feedback([], [R], REVISION, P, R)[0]
    ok, why = verdict_handoff_review_feedback([P], [R], REVISION, P, R)
    assert not ok
    assert "applied unasked" in why
    ok, why = verdict_handoff_review_feedback([], [], REVISION, P, R)
    assert not ok
    assert "no draft/review.md" in why


def test_superseded():
    assert verdict_handoff_superseded([], [], SUPERSEDED)[0]
    assert verdict_handoff_superseded([], [], GERMAN)[0]
    ok, why = verdict_handoff_superseded([R], [], SUPERSEDED)
    assert not ok
    assert "files written" in why
    no_cue = SUPERSEDED.replace("judged the earlier design", "judged the design")
    ok, why = verdict_handoff_superseded([], [], no_cue)
    assert not ok
    assert "earlier version" in why
    announced = SUPERSEDED.replace(
        'Next: a fresh review of the narrowed draft, review only. Reply "yes", or send: '
        '"Review my proposal — review only, no edits."',
        "Next: there is no current assessment yet.")
    ok, why = verdict_handoff_superseded([], [], announced)
    assert not ok
    assert "expected step" in why
    unquoted = SUPERSEDED.replace(
        'Reply "yes", or send: "Review my proposal — review only, no edits."', "")
    ok, why = verdict_handoff_superseded([], [], unquoted)
    assert not ok
    assert "phrase" in why


def swap_next(chat: str, new_next: str) -> str:
    lines = [f"Next: {new_next}" if line.startswith("Next:") else line
             for line in chat.splitlines()]
    return "\n".join(lines) + "\n"


@pytest.mark.parametrize("new_next", [
    'have the narrowed proposal reviewed afresh, since the old blockers no longer apply. '
    'Say "review it".',
    'a review of the narrowed draft. Send: "Review my proposal."',
])
def test_superseded_accepts_other_ways_of_recommending_the_review(new_next):
    ok, why = verdict_handoff_superseded([], [], swap_next(SUPERSEDED, new_next))
    assert ok, why


@pytest.mark.parametrize("new_next", [
    # the review adversary's false passes (2026-10-13): the word, not the step
    'there is no current review yet, so send it to your supervisor as is: "send it"',
    'no fresh review is needed; build the PDF: "build it"',
    'the review on file still applies, so build the PDF: "build it"',
    # review 2: negated after the step, or a hand-in step first
    'send it as it is — a fresh review is not needed: "send it"',
    'build the PDF now and get it reviewed after your supervisor reads it: "build it"',
])
def test_superseded_fails_when_the_review_is_mentioned_but_not_recommended(new_next):
    ok, why = verdict_handoff_superseded([], [], swap_next(SUPERSEDED, new_next))
    assert not ok
    assert "expected step" in why


def test_superseded_cue_must_concern_the_review():
    prior_work_only = ("Check: clean. The prior work section is thorough.\n\n"
                       "Where it stands: complete draft.\n"
                       'Next: a fresh review of the draft. Send: "Review my proposal."\n')
    ok, why = verdict_handoff_superseded([], [], prior_work_only)
    assert not ok
    assert "earlier version" in why


CLEAN = "- digest: sha256:abc\nmechanically clean\n"
DIRTY = "- ERROR: [section-missing] Methodology section missing\n"
AFTER = ("Applied both blockers.\n\nWhere it stands: both blocker passages changed.\n"
         'Next: a fresh review of the changed text. Send: "Review my proposal again."\n')


W = ["proposal-write"]


def test_a_revision_without_the_writing_skill_fails():
    """Rounds 1 and 2 (2026-10-13): both models carried a direct request out as
    a bare edit — no check run, no handoff. The approval must load the skill."""
    ok, why = verdict_handoff_after_revision([P], [], AFTER, CLEAN, P, R, ["proposal-check"], [])
    assert not ok
    assert "without the writing skill" in why


def test_a_status_answer_that_edits_fails_even_if_the_revision_is_right():
    ok, why = verdict_handoff_after_revision([P], [], AFTER, CLEAN, P, R, W, [P])
    assert not ok
    assert "before any approval" in why


def test_after_revision():
    assert verdict_handoff_after_revision([P], [], AFTER, CLEAN, P, R, W, [])[0]
    assert verdict_handoff_after_revision([P], ["draft/notes.md"], AFTER, CLEAN, P, R, W, [])[0]
    # a review written under any folder is a review that ran unasked
    ok, why = verdict_handoff_after_revision([P], ["other/review.md"], AFTER, CLEAN, P, R, W, [])
    assert not ok
    assert "other/review.md" in why
    ok, why = verdict_handoff_after_revision([], [], AFTER, CLEAN, P, R, W, [])
    assert not ok
    assert "unchanged" in why
    ok, why = verdict_handoff_after_revision([P, R], [], AFTER, CLEAN, P, R, W, [])
    assert not ok
    assert "review ran unasked" in why
    ok, why = verdict_handoff_after_revision([P], [], AFTER, DIRTY, P, R, W, [])
    assert not ok
    assert "check errors" in why
    final_check = AFTER.replace(
        'a fresh review of the changed text. Send: "Review my proposal again."',
        'the final language pass. Send: "Check it once more."')
    ok, why = verdict_handoff_after_revision([P], [], final_check, CLEAN, P, R, W, [])
    assert not ok
    assert "expected step" in why
    still_applies = swap_next(AFTER, 'the final check — the review on file still applies: "check"')
    ok, why = verdict_handoff_after_revision([P], [], still_applies, CLEAN, P, R, W, [])
    assert not ok
    assert "expected step" in why
    shortfall = "- ERROR: references — at least 3 required, 2 found\n"
    ok, why = verdict_handoff_after_revision([P], [], AFTER, shortfall, P, R, W, [])
    assert not ok
    assert "check errors" in why


def test_ready():
    assert verdict_handoff_ready([], [], READY)[0]
    ok, why = verdict_handoff_ready([], ["draft.pdf"], READY)
    assert not ok
    assert "draft.pdf" in why
    wrong = READY.replace("a final language check, then the PDF", "one more round of revision")
    wrong = wrong.replace('Send: "Check my proposal before I hand it in."', "")
    ok, why = verdict_handoff_ready([], [], wrong)
    assert not ok
    assert "expected step" in why


@pytest.mark.parametrize("new_next", [
    # review 2 (2026-10-13): correct ready runs the first step check failed
    'build the hand-in PDF — another review is not needed: "Build my proposal as a PDF."',
    'build the hand-in PDF, since a fresh review would add nothing: "Build the PDF."',
    'build the hand-in PDF — model versions, sample size and crash handling are settled '
    'in the thesis\'s first weeks, not before: "Build the PDF."',
])
def test_ready_accepts_a_review_or_deferred_items_named_only_to_rule_them_out(new_next):
    ok, why = verdict_handoff_ready([], [], swap_next(READY, new_next))
    assert ok, why


def test_ready_accepts_the_german_negation():
    chat = ("Stand: bereit für das Gespräch mit dem Betreuer.\n"
            "Als Nächstes: das PDF bauen — ein weiteres Review ist nicht nötig: „Baue das PDF.“\n")
    ok, why = verdict_handoff_ready([], [], chat)
    assert ok, why


@pytest.mark.parametrize(("new_next", "fragment"), [
    ('fix the audit sample size and model versions before you send it: "fix them"',
     "a step"),
    ('a fresh review to check the scope. Send: "Review it."', "another review"),
    ("build the PDF and send it.", "phrase"),
])
def test_ready_failures(new_next, fragment):
    ok, why = verdict_handoff_ready([], [], swap_next(READY, new_next))
    assert not ok
    assert fragment in why


def test_untouched():
    assert verdict_handoff_untouched([], [], SUPERSEDED)[0]
    ok, why = verdict_handoff_untouched([P], [], SUPERSEDED)
    assert not ok
    assert "files written" in why
