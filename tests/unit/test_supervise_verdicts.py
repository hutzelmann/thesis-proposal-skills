"""L0: the supervise feedback verdicts (testing-harness spec: supervise
feedback coverage). Each verdict function is exercised without model calls; the
feedback snippets mirror what the skill's own instructions produce.
"""

import textwrap
from pathlib import Path

import pytest
from l1_checks import (
    CLOSING_NOTE_LANGUAGES,
    load_closing_note,
    verdict_supervise_closing,
    verdict_supervise_feedback,
    verdict_supervise_feedback_contract,
    verdict_supervise_literature,
    verdict_supervise_no_personal_data,
    verdict_supervise_pointers,
    verdict_supervise_points,
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
3. One sentence with start and submission month is enough — phases go to notes; see proposal-check.

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
