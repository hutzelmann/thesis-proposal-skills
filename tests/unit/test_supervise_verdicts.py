"""L0: the supervise feedback verdicts (testing-harness spec: supervise
feedback coverage). Each verdict function is exercised without model calls; the
feedback snippets mirror what the skill's own instructions produce.
"""

import textwrap
from pathlib import Path

import pytest
from l1_checks import (
    CLOSING_NOTE_LANGUAGES,
    feedback_body_words,
    load_closing_note,
    verdict_supervise_closing,
    verdict_supervise_feedback,
    verdict_supervise_feedback_contract,
    verdict_supervise_literature,
    verdict_supervise_locators,
    verdict_supervise_markup,
    verdict_supervise_no_personal_data,
    verdict_supervise_pointers,
    verdict_supervise_points,
    verdict_supervise_review_sections,
    verdict_supervise_scope_options,
    verdict_supervise_substance_only,
    verdict_supervise_tier,
)

REPO = Path(__file__).resolve().parents[2]

SKILL_SET = (
    "proposal-check", "proposal-customize", "proposal-ideate", "proposal-import",
    "proposal-lit-search", "proposal-publish", "proposal-review",
    "proposal-supervise", "proposal-troubleshoot", "proposal-write",
)

# the shipped snippet, so a reworded reference file cannot leave these tests
# asserting against a copy that no longer exists
CLOSING = load_closing_note(REPO / "skills")

FEEDBACK = """Verdict: needs revision — please address the points below and resubmit.

1. The idea is a build goal, not yet a research question — proposal-ideate helps sharpen it.
2. Two blog posts cannot ground a thesis; proposal-lit-search finds citable literature.
3. The plan names no evaluation: say how you will know the dashboard helps — proposal-write.

What to keep: the observed problem is concrete and worth studying.

This feedback was prepared with an AI assistant; every decision about your thesis stays yours.
"""


def test_feedback_present_and_absent():
    assert verdict_supervise_feedback(FEEDBACK)[0]
    ok, why = verdict_supervise_feedback(None)
    assert not ok
    assert "no feedback" in why
    assert not verdict_supervise_feedback("   \n")[0]


def test_points_counted_within_curation_cap():
    ok, why = verdict_supervise_points(FEEDBACK)
    assert ok
    assert "3" in why


def test_points_missing_or_uncurated_fail():
    assert not verdict_supervise_points("Dear student, all is well.")[0]
    six = "\n".join(f"{i}. point" for i in range(1, 7))
    ok, why = verdict_supervise_points(six)
    assert not ok
    assert "at most five" in why


def test_tier_found_in_opening_lines_case_insensitive():
    assert verdict_supervise_tier(FEEDBACK)[0]
    assert verdict_supervise_tier("Ergebnis: kein tragfähiger Thesenkern.\n\n1. …")[0]
    assert verdict_supervise_tier("READY — no substantial revisions needed from my side.")[0]


def test_tier_absent_or_buried_fails():
    assert not verdict_supervise_tier("Dear student,\n\nthanks for the idea.")[0]
    buried = "line\n" * 6 + "Verdict: ready"
    assert not verdict_supervise_tier(buried)[0]


def test_tier_accepts_naturally_negated_no_viable_core():
    """Regression (sonnet dev run 2026-08-10): real feedback phrases the bottom
    tier as prose — 'does not yet have a viable thesis core' — not verbatim."""
    feedback = ("Dear student,\n\nThank you for sending this idea. Right now it does "
                "not yet have a viable thesis core — the material needs re-grounding.")
    assert verdict_supervise_tier(feedback)[0]


def test_tier_accepts_idea_stage_rendering_en_de():
    """The student-facing bottom tier is 'idea stage' / 'Ideenphase'
    (skill-supervise spec: verdict expressed as proposal state)."""
    en = "Verdict: **idea stage** — this is not yet a proposal, and that is fine."
    de = ("Einschätzung: **Ideenphase — noch kein Exposé.** "
          "Der nächste Schritt ist die Ideenfindung.")
    assert verdict_supervise_tier(en)[0]
    assert verdict_supervise_tier(de)[0]


def test_tier_ready_is_word_bounded():
    ok, _ = verdict_supervise_tier("We have already received your idea.")
    assert not ok, "'already' must not count as the tier 'ready'"


def test_personal_data_leak_names_file_and_token():
    files = {"idea-feedback.md": FEEDBACK + "\nErika Musterfrau, 00000000"}
    ok, why = verdict_supervise_no_personal_data(files, ("Musterfrau", "00000000"))
    assert not ok
    assert "idea-feedback.md" in why
    assert "Musterfrau" in why


def test_personal_data_clean_and_missing_feedback():
    clean = {"idea-feedback.md": FEEDBACK}
    assert verdict_supervise_no_personal_data(clean, ("Musterfrau", "00000000"))[0]
    assert not verdict_supervise_no_personal_data({}, ("Musterfrau",))[0]


def test_personal_data_match_is_case_insensitive():
    files = {"idea-feedback.md": "contact: ERIKA.MUSTERFRAU@EXAMPLE.ORG"}
    assert not verdict_supervise_no_personal_data(
        files, ("erika.musterfrau@example.org",))[0]


def test_pointers_ignore_the_repo_name_in_the_install_blurb():
    """Regression (sonnet dev run 2026-08-10): `hutzelmann/thesis-proposal-skills`
    in the closing note must not read as a skill named proposal-skills."""
    feedback = ("1. Sharpen the question — proposal-ideate.\n\nFree writing tools are "
                "available at https://github.com/hutzelmann/thesis-proposal-skills.")
    ok, why = verdict_supervise_pointers(feedback, SKILL_SET)
    assert ok
    assert "proposal-skills" not in why


def test_feedback_contract_aggregate_passes_when_complete():
    files = {"idea-feedback.md": FEEDBACK}
    ok, why = verdict_supervise_feedback_contract(files, ("Musterfrau",), SKILL_SET)
    assert ok
    assert "3 curated points" in why


def test_feedback_contract_aggregate_reports_every_failed_aspect():
    files = {"idea-notes.md": "Erika Musterfrau"}
    ok, why = verdict_supervise_feedback_contract(files, ("Musterfrau",), SKILL_SET)
    assert not ok
    assert "no feedback" in why
    assert "Musterfrau" in why
    assert "no numbered points" in why


@pytest.mark.parametrize(("feedback", "ok", "fragment"), [
    (FEEDBACK, True, "proposal-ideate"),
    ("No tools mentioned anywhere.", False, "no skill"),
    ("Try proposal-polish for the prose.", False, "proposal-polish"),
])
def test_pointers_resolve_against_installed_set(feedback, ok, fragment):
    got_ok, why = verdict_supervise_pointers(feedback, SKILL_SET)
    assert got_ok == ok
    assert fragment in why


def test_closing_note_sections_parse_and_load_from_the_shipped_file():
    sections = load_closing_note(REPO / "skills")
    assert set(sections) == set(CLOSING_NOTE_LANGUAGES)
    assert sections["English"].startswith("Note:")
    assert sections["Deutsch"].startswith("Hinweis:")
    assert load_closing_note(REPO / "no-such-dir") == {}


def test_closing_note_carried_verbatim_passes():
    feedback = FEEDBACK + "\n" + CLOSING["English"]
    ok, why = verdict_supervise_closing(feedback, CLOSING, "English")
    assert ok
    assert "English" in why


def test_closing_note_survives_a_different_line_wrap():
    """The reference file wraps for readability; a produced feedback need not.
    Only the words are the contract."""
    rewrapped = " ".join(CLOSING["English"].split())
    ok, _ = verdict_supervise_closing(FEEDBACK + "\n" + rewrapped, CLOSING, "English")
    assert ok


def test_closing_note_paraphrase_fails():
    paraphrased = CLOSING["English"].replace("Free writing tools", "Some writing tools")
    ok, why = verdict_supervise_closing(FEEDBACK + "\n" + paraphrased, CLOSING, "English")
    assert not ok
    assert "verbatim" in why


def test_closing_note_in_the_wrong_language_fails():
    ok, why = verdict_supervise_closing(
        FEEDBACK + "\n" + CLOSING["Deutsch"], CLOSING, "English")
    assert not ok
    assert "Deutsch" in why
    assert "English" in why


def test_closing_note_both_languages_fails():
    both = FEEDBACK + "\n" + CLOSING["English"] + "\n" + CLOSING["Deutsch"]
    ok, why = verdict_supervise_closing(both, CLOSING, "English")
    assert not ok
    assert "both languages" in why


def test_closing_note_missing_feedback_or_sections():
    assert not verdict_supervise_closing(None, CLOSING, "English")[0]
    assert not verdict_supervise_closing("   ", CLOSING, "English")[0]
    ok, why = verdict_supervise_closing(FEEDBACK, {}, "English")
    assert not ok
    assert "no closing-note sections" in why


def test_closing_note_without_an_expected_language_accepts_either():
    assert verdict_supervise_closing(FEEDBACK + CLOSING["Deutsch"], CLOSING)[0]


def test_feedback_contract_aggregate_includes_the_closing_note():
    files = {"idea-feedback.md": FEEDBACK + "\n" + CLOSING["English"]}
    ok, why = verdict_supervise_feedback_contract(
        files, ("Musterfrau",), SKILL_SET, CLOSING, "English")
    assert ok
    assert "closing note carried verbatim" in why

    stale = {"idea-feedback.md": FEEDBACK}
    ok, why = verdict_supervise_feedback_contract(
        stale, ("Musterfrau",), SKILL_SET, CLOSING, "English")
    assert not ok
    assert "verbatim" in why


# ---- verdict_supervise_literature -------------------------------------------

DOI_A = "10.1000/example.2016.001"
DOI_B = "10.1000/example.2020.002"
DOI_C = "10.1000/example.2018.003"
# the Elsevier shape — a balanced parenthesis pair inside — on the DOI
# handbook's example prefix, so it resolves to nothing real
DOI_PARENS = "10.1000/S0000-0000(20)30183-5"

# a point that does work with its paper — the shape the skill prescribes
WOVEN = (
    "2. Read before you narrow, because your first research question has already been "
    "answered: Muster, Beispiel and Vorlage (2016), \"A granular taxonomy of cache "
    f"replacement policies\", Journal of Example Studies, https://doi.org/{DOI_A}, classify "
    "several hundred variants by the workload each serves. Start from that taxonomy, pick "
    "the one policy your thesis will study, and let proposal-lit-search find the papers "
    "around it."
)
NOTES = (f"## Feedback Literature\n\n- DOI: {DOI_A} — serves point 2\n"
         f"- DOI: {DOI_B} — serves What to keep\n- DOI: {DOI_C} — serves point 1\n")
ENTRY_A = f"Muster et al. (2016), A granular taxonomy, https://doi.org/{DOI_A} — the map."
ENTRY_B = f"Beispiel (2020), A worked negative result, https://doi.org/{DOI_B} — the shape."
ENTRY_C = f"Vorlage (2018), The same framing, https://doi.org/{DOI_C} — confirms it."


def test_literature_absent_passes():
    ok, why = verdict_supervise_literature(FEEDBACK, NOTES)
    assert ok
    assert "no literature" in why


def test_literature_woven_and_recorded_passes():
    ok, why = verdict_supervise_literature(FEEDBACK + "\n" + WOVEN, NOTES)
    assert ok
    assert "1 paper" in why


def test_literature_doi_match_ignores_case_and_trailing_punctuation():
    shouted = WOVEN.replace(DOI_A, DOI_A.upper() + ".")
    assert verdict_supervise_literature(FEEDBACK + "\n" + shouted, NOTES)[0]


def test_literature_hard_wrapped_point_is_judged_whole():
    """One DOI in a paragraph: the whole paragraph is the block, so a point
    wrapped at 80 columns is not read as a bare line."""
    wrapped = "\n".join(textwrap.wrap(WOVEN, 80))
    assert wrapped.count("\n") >= 3
    assert verdict_supervise_literature(FEEDBACK + "\n" + wrapped, NOTES)[0]


def test_literature_bulleted_list_fails_naming_the_doi():
    """The shape the professor rejected (real run, 2026-09-10): a block of
    entries after the strengths, each paper on its own bullet."""
    listed = (FEEDBACK + "\nWhere this conversation already is:\n\n"
              f"- Muster et al. (2016), A granular taxonomy, https://doi.org/{DOI_A}\n"
              f"- Beispiel (2020), Cache eviction traces, https://doi.org/{DOI_B}\n")
    ok, why = verdict_supervise_literature(listed, NOTES)
    assert not ok
    assert DOI_A in why
    assert "list" in why


@pytest.mark.parametrize("marker", ["• ", "– ", "* ", "+ "])
def test_literature_other_bullet_markers_fail_too(marker):
    listed = FEEDBACK + "\n" + marker + ENTRY_A + "\n" + marker + ENTRY_B + "\n"
    ok, why = verdict_supervise_literature(listed, NOTES)
    assert not ok
    assert "list" in why


def test_literature_bare_citation_line_fails():
    bare = FEEDBACK + f"\nMuster et al. (2016), A granular taxonomy, https://doi.org/{DOI_A}\n"
    ok, why = verdict_supervise_literature(bare, NOTES)
    assert not ok
    assert "bare citation" in why


def test_literature_list_without_blank_lines_is_judged_per_line():
    """Three entries on consecutive lines are one paragraph and together
    exceed the word floor; each line is a bare citation all the same."""
    plain = FEEDBACK + "\nWhere this conversation already is:\n" + "\n".join(
        (ENTRY_A, ENTRY_B, ENTRY_C)) + "\n"
    ok, why = verdict_supervise_literature(plain, NOTES)
    assert not ok
    assert "bare citation" in why
    assert DOI_A in why

    numbered = FEEDBACK + "\n" + "\n".join(
        f"{i}. {entry}" for i, entry in enumerate((ENTRY_A, ENTRY_B, ENTRY_C), 1)) + "\n"
    ok, why = verdict_supervise_literature(numbered, NOTES)
    assert not ok
    assert "bare citation" in why


def test_literature_doi_with_parentheses_is_captured_whole():
    woven = WOVEN.replace(DOI_A, DOI_PARENS)
    recorded = f"## Feedback Literature\n\n- DOI: {DOI_PARENS}\n"
    assert verdict_supervise_literature(FEEDBACK + "\n" + woven, recorded)[0]
    linked = WOVEN.replace(f"https://doi.org/{DOI_A}", f"[the paper](https://doi.org/{DOI_PARENS})")
    assert verdict_supervise_literature(FEEDBACK + "\n" + linked, recorded)[0]

    sibling = "## Feedback Literature\n\n- DOI: 10.1000/S0000-0000(20)99999-9\n"
    ok, why = verdict_supervise_literature(FEEDBACK + "\n" + woven, sibling)
    assert not ok
    assert DOI_PARENS.lower() in why


def test_literature_unrecorded_doi_fails():
    ok, why = verdict_supervise_literature(FEEDBACK + "\n" + WOVEN, "## Log\n\nnothing yet")
    assert not ok
    assert "not recorded" in why
    assert DOI_A in why
    assert not verdict_supervise_literature(FEEDBACK + "\n" + WOVEN, None)[0]


def test_literature_recorded_doi_must_match_as_a_token():
    """A cited DOI that merely prefixes a recorded one is not recorded."""
    longer = NOTES.replace(DOI_A, DOI_A + ".extra")
    ok, why = verdict_supervise_literature(FEEDBACK + "\n" + WOVEN, longer)
    assert not ok
    assert "not recorded" in why


def test_literature_cap_of_three():
    points = "\n\n".join(
        WOVEN.replace("2.", f"{i}.", 1).replace(DOI_A, f"10.1000/example.{i}")
        for i in range(1, 5)
    )
    ok, why = verdict_supervise_literature(points, "")
    assert not ok
    assert "at most 3" in why


def test_literature_missing_feedback_fails():
    assert not verdict_supervise_literature(None, NOTES)[0]
    assert not verdict_supervise_literature("  ", NOTES)[0]


def test_feedback_contract_aggregate_reads_the_notes_for_literature():
    files = {"idea-feedback.md": FEEDBACK + "\n" + WOVEN, "idea.notes.md": NOTES}
    ok, why = verdict_supervise_feedback_contract(files, ("Musterfrau",), SKILL_SET)
    assert ok
    assert "woven" in why

    unrecorded = {"idea-feedback.md": FEEDBACK + "\n" + WOVEN}
    ok, why = verdict_supervise_feedback_contract(unrecorded, ("Musterfrau",), SKILL_SET)
    assert not ok
    assert "not recorded" in why


def test_feedback_contract_aggregate_scans_the_notes_for_personal_data():
    """The dev runner passes the notes file in beside the feedback; identity
    surviving there is the same defect as in the feedback."""
    files = {"idea-feedback.md": FEEDBACK, "idea.notes.md": NOTES + "\nErika Musterfrau\n"}
    ok, why = verdict_supervise_feedback_contract(files, ("Musterfrau",), SKILL_SET)
    assert not ok
    assert "idea.notes.md" in why


# ---------- substance only: no format lecture ----------------------------------


@pytest.mark.parametrize("sentence", [
    # the real lecture shape (2026-09-01 and 2026-10-03 runs), abstracted
    "On format: the proposal should not carry your name, a chapter outline or the Gantt chart.",
    "The phase list and the Gantt chart do not belong in a proposal.",
    "Please remove the chapter outline and your name from the cover page.",
    "The timeline is one sentence naming the start and submission month.",
    "References should point to DOIs rather than library proxy links.",
    "Die Gliederung und das Gantt-Diagramm gehören nicht ins Exposé.",
    "Bitte das Deckblatt mit Ihrem Namen entfernen.",
])
def test_substance_only_catches_format_lectures(sentence):
    ok, why = verdict_supervise_substance_only(FEEDBACK + "\n" + sentence + "\n")
    assert not ok
    assert "format remark" in why


@pytest.mark.parametrize("sentence", [
    "Your Gantt chart fits five dependent packages into fourteen weeks, which leaves no buffer.",
    "Option A leaves out the remediation-plan revision and keeps the model as the core.",
    "Your work plan chains every package on the previous one; option B drops the trial.",
    "The timeline ends in December, before the expert review can report back.",
])
def test_substance_only_lets_scope_evidence_through(sentence):
    ok, why = verdict_supervise_substance_only(FEEDBACK + "\n" + sentence + "\n")
    assert ok, why


def test_substance_only_needs_a_feedback():
    assert not verdict_supervise_substance_only(None)[0]
    assert verdict_supervise_substance_only(FEEDBACK)[0]


# ---------- light markup -------------------------------------------------------


def test_markup_bold_and_lists_pass_with_the_closing_note():
    feedback = ("My verdict: **needs revision**.\n\n1. **Name the criteria.** Say which.\n\n"
                "A) keep the model\nB) keep the revision\n\n" + CLOSING["English"])
    assert verdict_supervise_markup(feedback)[0]


@pytest.mark.parametrize(("line", "fragment"), [
    ("## Points", "heading"),
    ("> Note: quoted", "blockquote"),
    ("1. Sharpen the questions → `proposal-write`", "code markup"),
])
def test_markup_heavy_lines_fail(line, fragment):
    ok, why = verdict_supervise_markup(FEEDBACK + "\n" + line + "\n")
    assert not ok
    assert fragment in why


def test_markup_needs_a_feedback():
    assert not verdict_supervise_markup("")[0]


# ---------- locators for standards and regulations -------------------------------


PROPOSAL = "The study maps WCAG 2.2 and EN 301 549 onto the portal (see ISO 9241-171:2008)."


def test_locators_pass_without_new_designations():
    ok, why = verdict_supervise_locators(FEEDBACK, PROPOSAL)
    assert ok
    assert "no standard" in why


def test_locators_ignore_designations_the_proposal_carries():
    point = "4. Your WCAG 2.2 mapping and EN 301 549 need one level of granularity."
    assert verdict_supervise_locators(FEEDBACK + "\n" + point, PROPOSAL)[0]
    # the year never decides a match
    assert verdict_supervise_locators("ISO 9241-171 is the anchor.", PROPOSAL)[0]


def test_locators_new_regulation_without_url_fails():
    point = ("4. Public-sector websites fall under Directive (EU) 2016/2102, not the act "
             "you cite.")
    ok, why = verdict_supervise_locators(FEEDBACK + "\n" + point, PROPOSAL)
    assert not ok
    assert "2016/2102" in why


def test_locators_new_regulation_with_url_passes():
    point = ("4. Public-sector websites fall under Directive (EU) 2016/2102 "
             "(https://eur-lex.europa.eu/eli/dir/2016/2102/oj), not the act you cite.")
    ok, why = verdict_supervise_locators(FEEDBACK + "\n" + point, PROPOSAL)
    assert ok
    assert "1 new" in why


def test_locators_part_numbers_are_distinct_standards():
    proposal = "Controls come from IEC 62443-3-3."
    feedback = "3. Target levels are set through IEC 62443-3-2, not in the part you cite."
    assert not verdict_supervise_locators(feedback, proposal)[0]


def test_locators_need_a_feedback():
    assert not verdict_supervise_locators(None, PROPOSAL)[0]


# ---------- scope options ----------------------------------------------------------


SCOPED = """My verdict: **needs revision**. The plan is large for a Bachelor's thesis: five
packages wait on each other in fourteen weeks. Two ways to cut it to one core — the choice
is yours:

A) Model and diagnosis: the prioritization model plus the gap analysis; the revised
checklist moves to the outlook.
B) Revision and evaluation: a borrowed ranking, the weight on the revised checklist and a
trial with its users.

1. Name the criteria the model ranks by (both options).
"""


def test_scope_options_lettered_with_choice_pass():
    ok, why = verdict_supervise_scope_options(SCOPED)
    assert ok
    assert "A, B" in why


def test_scope_options_inline_option_words_pass():
    inline = "Option A keeps the model; Option B keeps the revision. You decide which."
    assert verdict_supervise_scope_options(inline)[0]


def test_scope_options_single_or_numbered_fail():
    assert not verdict_supervise_scope_options(FEEDBACK)[0]
    numbered = SCOPED.replace("A) ", "1. ").replace("B) ", "2. ")
    assert not verdict_supervise_scope_options(numbered)[0]


def test_scope_options_without_student_choice_fail():
    ruling = "A) keep the model.\nB) keep the revision.\nI have picked A for you."
    ok, why = verdict_supervise_scope_options(ruling)
    assert not ok
    assert "choice" in why


def test_scope_options_do_not_count_as_points():
    ok, why = verdict_supervise_points(SCOPED)
    assert ok
    assert "1 curated" in why


# ---------- review sections ---------------------------------------------------------


REVIEW = """**Verdict: needs revision.**

## Workload

| Package | Depends on | Size driver | Estimate (weeks, est.) |
|---|---|---|---|
| Review the catalogue | — | number of requirements (unknown) | 3–6 |
| Build the model | catalogue | criteria | 3 |

Unknowns: the catalogue's size.

Scope verdict: over-scoped

## Verification

Contradicted: none. Unverifiable: one claim about a paywalled standard.
"""


def test_review_sections_complete_pass():
    assert verdict_supervise_review_sections(REVIEW)[0]


def test_review_sections_german_headings_pass():
    german = (REVIEW.replace("## Workload", "## Arbeitsumfang")
              .replace("Scope verdict: over-scoped", "Umfang: zu umfangreich")
              .replace("## Verification", "## Überprüfung"))
    assert verdict_supervise_review_sections(german)[0]


@pytest.mark.parametrize(("mutation", "fragment"), [
    (lambda r: r.replace("## Verification", "## Notes"), "no verification section"),
    (lambda r: r.replace("## Workload", "## Scope"), "no workload section"),
    (lambda r: r.replace("Scope verdict: over-scoped", ""), "no scope verdict"),
    (lambda r: "\n".join(line for line in r.splitlines() if not line.startswith("|")),
     "no work-package table"),
])
def test_review_sections_missing_pieces_fail(mutation, fragment):
    ok, why = verdict_supervise_review_sections(mutation(REVIEW))
    assert not ok
    assert fragment in why


def test_review_sections_need_a_review():
    assert not verdict_supervise_review_sections(None)[0]


# ---------- length and the extended aggregate ----------------------------------------


def test_feedback_body_words_exclude_urls_and_the_closing_note():
    body = "One two three (https://doi.org/10.1000/xyz) four."
    assert feedback_body_words(body + "\n\n" + CLOSING["English"], CLOSING) == 4
    assert feedback_body_words(None) == 0


def test_feedback_contract_aggregate_catches_a_format_lecture_and_heavy_markup():
    lecture = FEEDBACK + "\nThe Gantt chart does not belong in the proposal.\n## Next steps\n"
    ok, why = verdict_supervise_feedback_contract(
        {"idea-feedback.md": lecture}, ("Musterfrau",), SKILL_SET)
    assert not ok
    assert "format remark" in why
    assert "heading line" in why


def test_feedback_contract_aggregate_checks_locators_only_with_a_proposal():
    point = FEEDBACK + "\n4. Directive (EU) 2016/2102 governs public-sector sites.\n"
    files = {"idea-feedback.md": point}
    ok, why = verdict_supervise_feedback_contract(files, ("Musterfrau",), SKILL_SET)
    assert ok
    assert "locators not checked" in why
    ok, why = verdict_supervise_feedback_contract(files, ("Musterfrau",), SKILL_SET,
                                                  proposal=PROPOSAL)
    assert not ok
    assert "2016/2102" in why


# ---------- review-round regressions (2026-10-03) ------------------------------------
#
# Each case below was a confirmed finding of the adversarial review of this
# change: a scope sentence the first patterns called a lecture, a lecture they
# missed, a valid option layout they did not count, a valid review they rejected.


@pytest.mark.parametrize("sentence", [
    "Option A: drop WP5 from the work plan and keep the model as the core.",
    "Option B: remove validation from the work plan; the audit stays.",
    "Option A: Arbeitspaket 5 aus dem Arbeitsplan streichen und das Modell behalten.",
    "Your work plan chains five packages; package 3 should not be started before the "
    "catalogue size is known.",
    "The Gantt chart shows the evaluation in weeks 12-13, so it should not include a "
    "usability test as well.",
    "Die Evaluation gehört nicht in den Kern Ihres Arbeitsplans, sondern in Option B.",
    "Your timeline has no buffer; state in one sentence which package you would cut first.",
    "Option B: remove from the work plan the usability test with screen-reader users.",
    "The phase table shows the audit must not be longer than three weeks.",
    "Option A: cut the work plan to two packages and keep the evaluation inside them.",
])
def test_substance_only_scope_advice_is_not_a_lecture(sentence):
    ok, why = verdict_supervise_substance_only(FEEDBACK + "\n" + sentence + "\n")
    assert ok, why


@pytest.mark.parametrize("sentence", [
    # the lecture the HEAD sample itself carried before this change
    "One sentence with start and submission month is enough — phases go to notes; "
    "see proposal-check.",
    "Shorten the timeline to the start and end dates.",
    "Please cut the Gantt chart; a proposal does not need one.",
    "Leave the Gantt chart out of the proposal.",
    "Das Gantt-Diagramm bitte kürzen.",
    "The Gantt chart does not belong in the proposal.",
])
def test_substance_only_catches_the_lectures_it_missed(sentence):
    assert not verdict_supervise_substance_only(FEEDBACK + "\n" + sentence + "\n")[0]


def test_scope_options_ignore_the_closing_notes_decision():
    """The English closing note says "every decision … stays with you"; it must
    not stand in for the scope paragraph leaving the cut to the student."""
    ruling = "A) keep the model.\nB) keep the revision.\n\n" + CLOSING["English"]
    ok, why = verdict_supervise_scope_options(ruling, CLOSING)
    assert not ok
    assert "choice" in why
    assert verdict_supervise_scope_options(SCOPED + "\n" + CLOSING["English"], CLOSING)[0]


@pytest.mark.parametrize("feedback", [
    "Three ways to cut it: A) keep the model; B) keep the revision. Your choice.",
    "**Scope.** Too large. A) keep the model. B) keep the audit. The choice is yours.",
    "- A) keep the model\n- B) keep the revision\nYou decide.",
    "- **A — model:** keep it\n- **B — revision:** keep it\nThe choice is yours.",
    "Sie wählen: A) das Modell; B) die Überarbeitung. Die Entscheidung liegt bei Ihnen.",
])
def test_scope_options_inline_and_bulleted_layouts_count(feedback):
    ok, why = verdict_supervise_scope_options(feedback)
    assert ok, why


def test_scope_options_ignore_annex_and_initials():
    assert not verdict_supervise_scope_options(
        "See Annex A) and Annex B) of the standard; you decide.")[0]


@pytest.mark.parametrize("mutation", [
    lambda r: r.replace("Scope verdict: over-scoped", "**Scope verdict**: over-scoped"),
    lambda r: r.replace("Scope verdict: over-scoped", "Scope verdict: `over-scoped`"),
    lambda r: r.replace("over-scoped", "over‑scoped"),
    lambda r: r.replace("## Workload\n", "## 5. Workload\n\n### Work packages\n"),
    lambda r: r.replace("## Verification", "## Claim verification"),
])
def test_review_sections_accept_common_markdown_renderings(mutation):
    ok, why = verdict_supervise_review_sections(mutation(REVIEW))
    assert ok, why


def test_review_section_keeps_its_subheadings():
    nested = REVIEW.replace("## Workload\n", "## Workload\n\n### Packages\n").replace(
        "Scope verdict: over-scoped", "### Verdict\n\nScope verdict: over-scoped")
    assert verdict_supervise_review_sections(nested)[0]


def test_locators_need_a_url_only_at_first_mention():
    two = ("4. Directive (EU) 2016/2102 (https://eur-lex.europa.eu/eli/dir/2016/2102/oj) "
           "covers public-sector sites.\n\n5. Under Directive (EU) 2016/2102 the "
           "portal's audit scope is fixed.")
    ok, why = verdict_supervise_locators(two, PROPOSAL)
    assert ok, why


@pytest.mark.parametrize(("proposal", "feedback", "ok"), [
    # an EU act named without "(EU)" is still a designation
    (PROPOSAL, "4. Public websites fall under Directive 2016/2102.", False),
    # NIST spelled out in the proposal matches the short form in the feedback
    ("We follow NIST Special Publication 800-82 Rev. 3.",
     "3. NIST SP 800-82r3 sets the zones.", True),
    # a year or a count after the number is not part of it
    ("Controls follow ISO 27001.", "2. ISO 27001 2022 edition reorganised Annex A.", True),
])
def test_locators_designation_spellings(proposal, feedback, ok):
    assert verdict_supervise_locators(feedback, proposal)[0] == ok


def test_literature_leaves_a_standard_located_by_doi_to_the_locator_verdict():
    point = ("4. Zones and conduits are set in NIST SP 800-82r3 "
             "(https://doi.org/10.6028/NIST.SP.800-82r3), which your mapping already "
             "uses for its overlay baselines and which also fixes the evaluation's frame "
             "for the audit you plan in the third package of your work.")
    assert verdict_supervise_literature(FEEDBACK + "\n" + point, "")[0]


def test_pointers_accept_a_capitalized_sentence_start():
    """Regression (sonnet dev run 2026-10-03): with code markup gone, a point
    ends "Proposal-write helps with this." — a real pointer, capitalized."""
    ok, why = verdict_supervise_pointers("1. Define the overlap. Proposal-write helps.", SKILL_SET)
    assert ok
    assert "proposal-write" in why
    assert not verdict_supervise_pointers("Proposal-Polish helps.", SKILL_SET)[0]


def test_locators_treat_wcag_versions_as_one_family():
    """Regression (sonnet dev run on s02, 2026-10-03): the feedback named the
    WCAG 2.0 criteria a cited paper measured; the proposal cites WCAG 2.2."""
    feedback = "2. The tools cover at most half of the WCAG 2.0 success criteria."
    assert verdict_supervise_locators(feedback, PROPOSAL)[0]
