"""L0: the methodology-opening verdict from harness/l1_checks.py (no model calls)."""

import pytest
from fixture_paths import corpus_proposals, fixture_of
from l1_checks import methodology_opening, verdict_draft, verdict_methodology_opening

CLEAN_CHECK = "# Check: x.md\n\n## Verified mechanically — no errors\n"


def proposal(heading: str, opening: str, subsection: str = "### Hypotheses and Variables") -> str:
    return (f"# Title\n\n*Master's Thesis Proposal*\n\n## Introduction to the Topic\n\n"
            f"Some context.\n\n## {heading}\n\n{opening}\n\n{subsection}\n\nDetail.\n")


EXPERIMENT = "Methodology for Research: Controlled Experiment"
CONFIDENT = ("Both questions ask how much of the resolution correctness the explanation style "
             "causes on its own. A controlled experiment answers that directly: it varies only "
             "the style while the defects and the task stay fixed.")


def test_a_suitability_verdict_on_the_branch_fails():
    passed, why = verdict_methodology_opening(proposal(
        EXPERIMENT, "A controlled experiment fits these questions because both ask for an effect."))
    assert not passed
    assert "suitability verdict" in why
    assert "A controlled experiment fits" in why


def test_a_german_suitability_verdict_fails():
    passed, why = verdict_methodology_opening(proposal(
        "Forschungsmethodik: Fallstudie",
        "Eine Fallstudie eignet sich, weil beide Fragen nach einer Entscheidung fragen.",
        "### Fall und Analyseeinheiten"))
    assert not passed
    assert "eignet sich" in why


def test_a_generic_method_name_with_a_frame_fails():
    passed, _ = verdict_methodology_opening(proposal(
        EXPERIMENT, "This methodology is suitable since the tools can be run repeatedly."))
    assert not passed


def test_a_workspace_branch_title_is_recognised():
    passed, why = verdict_methodology_opening(proposal(
        "Methodology for Research: Action Research",
        "Action research lends itself to these questions.", "### Problem Diagnosis"))
    assert not passed
    assert "Action research lends itself" in why


def test_a_missing_opening_fails():
    passed, why = verdict_methodology_opening(proposal(EXPERIMENT, ""))
    assert not passed
    assert "no opening" in why


def test_a_frame_in_a_sentence_not_naming_the_methodology_passes():
    opening = CONFIDENT + " The regression model fits the recorded data in a pilot."
    assert verdict_methodology_opening(proposal(EXPERIMENT, opening))[0]


def test_a_confident_opening_passes():
    passed, why = verdict_methodology_opening(proposal(EXPERIMENT, CONFIDENT))
    assert passed, why


def test_a_draft_without_a_methodology_section_is_left_to_the_check():
    text = "# Title\n\n*Master's Thesis Proposal*\n\n## Introduction to the Topic\n\nText.\n"
    assert methodology_opening(text) is None
    assert verdict_methodology_opening(text)[0]


def test_the_draft_verdict_applies_the_opening():
    passed, why = verdict_draft(proposal(EXPERIMENT, "A controlled experiment fits."), CLEAN_CHECK)
    assert not passed
    assert "suitability verdict" in why
    assert verdict_draft(proposal(EXPERIMENT, CONFIDENT), CLEAN_CHECK)[0]


OPENED = [path for path in corpus_proposals()
          if (found := methodology_opening(path.read_text(encoding="utf-8"))) and found[1].strip()]


def test_the_corpus_has_openings_to_guard():
    assert len(OPENED) >= 17


@pytest.mark.parametrize("path", OPENED, ids=[fixture_of(path) for path in OPENED])
def test_every_fixture_opening_models_the_target(path):
    passed, why = verdict_methodology_opening(path.read_text(encoding="utf-8"))
    assert passed, why
