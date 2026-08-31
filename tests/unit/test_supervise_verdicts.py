"""L0: the supervise letter verdicts (testing-harness spec: supervise letter
coverage). Each verdict function is exercised without model calls; the letter
snippets mirror what the skill's own instructions produce.
"""

import pytest
from l1_checks import (
    verdict_supervise_letter,
    verdict_supervise_letter_contract,
    verdict_supervise_no_personal_data,
    verdict_supervise_pointers,
    verdict_supervise_points,
    verdict_supervise_tier,
)

SKILL_SET = (
    "proposal-check", "proposal-customize", "proposal-ideate", "proposal-import",
    "proposal-lit-search", "proposal-publish", "proposal-review",
    "proposal-supervise", "proposal-troubleshoot", "proposal-write",
)

LETTER = """Verdict: needs revision — please address the points below and resubmit.

1. The idea is a build goal, not yet a research question — proposal-ideate helps sharpen it.
2. Two blog posts cannot ground a thesis; proposal-lit-search finds citable literature.
3. The work plan does not belong in a proposal — proposal-check explains the timeline rule.

What to keep: the observed problem is concrete and worth studying.

This feedback was prepared with an AI assistant; every decision about your thesis stays yours.
"""


def test_letter_present_and_absent():
    assert verdict_supervise_letter(LETTER)[0]
    ok, why = verdict_supervise_letter(None)
    assert not ok
    assert "no letter" in why
    assert not verdict_supervise_letter("   \n")[0]


def test_points_counted_within_curation_cap():
    ok, why = verdict_supervise_points(LETTER)
    assert ok
    assert "3" in why


def test_points_missing_or_uncurated_fail():
    assert not verdict_supervise_points("Dear student, all is well.")[0]
    six = "\n".join(f"{i}. point" for i in range(1, 7))
    ok, why = verdict_supervise_points(six)
    assert not ok
    assert "at most five" in why


def test_tier_found_in_opening_lines_case_insensitive():
    assert verdict_supervise_tier(LETTER)[0]
    assert verdict_supervise_tier("Ergebnis: kein tragfähiger Thesenkern.\n\n1. …")[0]
    assert verdict_supervise_tier("READY — no substantial revisions needed from my side.")[0]


def test_tier_absent_or_buried_fails():
    assert not verdict_supervise_tier("Dear student,\n\nthanks for the idea.")[0]
    buried = "line\n" * 6 + "Verdict: ready"
    assert not verdict_supervise_tier(buried)[0]


def test_tier_accepts_naturally_negated_no_viable_core():
    """Regression (sonnet dev run 2026-08-10): real letters phrase the bottom
    tier as prose — 'does not yet have a viable thesis core' — not verbatim."""
    letter = ("Dear student,\n\nThank you for sending this idea. Right now it does "
              "not yet have a viable thesis core — the material needs re-grounding.")
    assert verdict_supervise_tier(letter)[0]


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
    files = {"idea-letter.md": LETTER + "\nErika Musterfrau, 00000000"}
    ok, why = verdict_supervise_no_personal_data(files, ("Musterfrau", "00000000"))
    assert not ok
    assert "idea-letter.md" in why
    assert "Musterfrau" in why


def test_personal_data_clean_and_missing_letter():
    clean = {"idea-letter.md": LETTER}
    assert verdict_supervise_no_personal_data(clean, ("Musterfrau", "00000000"))[0]
    assert not verdict_supervise_no_personal_data({}, ("Musterfrau",))[0]


def test_personal_data_match_is_case_insensitive():
    files = {"idea-letter.md": "contact: ERIKA.MUSTERFRAU@EXAMPLE.ORG"}
    assert not verdict_supervise_no_personal_data(
        files, ("erika.musterfrau@example.org",))[0]


def test_pointers_ignore_the_repo_name_in_the_install_blurb():
    """Regression (sonnet dev run 2026-08-10): `hutzelmann/thesis-proposal-skills`
    in the getting-started blurb must not read as a skill named proposal-skills."""
    letter = ("1. Sharpen the question — proposal-ideate.\n\nFree writing tools are "
              "available at https://github.com/hutzelmann/thesis-proposal-skills.")
    ok, why = verdict_supervise_pointers(letter, SKILL_SET)
    assert ok
    assert "proposal-skills" not in why


def test_letter_contract_aggregate_passes_on_a_complete_letter():
    files = {"idea-letter.md": LETTER}
    ok, why = verdict_supervise_letter_contract(files, ("Musterfrau",), SKILL_SET)
    assert ok
    assert "3 curated points" in why


def test_letter_contract_aggregate_reports_every_failed_aspect():
    files = {"idea-notes.md": "Erika Musterfrau"}
    ok, why = verdict_supervise_letter_contract(files, ("Musterfrau",), SKILL_SET)
    assert not ok
    assert "no letter" in why
    assert "Musterfrau" in why
    assert "no numbered points" in why


@pytest.mark.parametrize(("letter", "ok", "fragment"), [
    (LETTER, True, "proposal-ideate"),
    ("No tools mentioned anywhere.", False, "no skill"),
    ("Try proposal-polish for the prose.", False, "proposal-polish"),
])
def test_pointers_resolve_against_installed_set(letter, ok, fragment):
    got_ok, why = verdict_supervise_pointers(letter, SKILL_SET)
    assert got_ok == ok
    assert fragment in why
