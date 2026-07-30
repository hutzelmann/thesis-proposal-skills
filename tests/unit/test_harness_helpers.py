"""L0: pure scoring helpers from harness/l1_checks.py (no model calls)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "harness"))

import pytest  # noqa: E402
from l1_checks import (  # noqa: E402
    disallowed_errors,
    is_enumerated_review,
    parse_grade,
    verdict_import,
)

GOOD_IMPORT = """\
# Introduction to the Topic

Irrigation schedules ignore soil data [@Rivera23Survey].
@Tanaka24Lora measured LoRa range in field conditions.

---
title: Soil-Aware Irrigation Control
lang: en
references:
- id: Rivera23Survey
  type: article-journal
  author:
  - family: Rivera
    given: L.
  issued:
    year: 2023
---
"""


def test_disallowed_errors_filters_allowed():
    out = "- ERROR: only 1 references — at least 3 required\n- ERROR: forbidden section: `Timeline`"
    assert disallowed_errors(out, ("references — at least",)) == [
        "- ERROR: forbidden section: `Timeline`"
    ]
    assert disallowed_errors(out) and len(disallowed_errors(out)) == 2


def test_is_enumerated_review():
    assert is_enumerated_review("Findings:\n1. RQs too broad — narrow them.\n2. Missing lit.")
    assert not is_enumerated_review("Looks fine overall, nothing enumerated here.")


def test_parse_grade_takes_last():
    assert parse_grade("thinking... GRADE: I ... reconsidering ... GRADE: C")
    assert not parse_grade("GRADE: I")
    assert not parse_grade("no grade at all")


CLEAN_CHECK = "# Check: x.md\n\n## Verified mechanically — no errors\n"
SHORT_REFS_CHECK = "- ERROR: only 2 references — at least 3 required\n"
BROKEN_CHECK = (
    "- ERROR: no trailing metadata block found (file must end with a `---` YAML block)\n"
    "- ERROR: no ordered-list research questions found in the research-questions section\n"
)


def test_verdict_import_accepts_a_clean_import():
    passed, why = verdict_import(GOOD_IMPORT, CLEAN_CHECK, "soil-aware-irrigation.md")
    assert passed, why
    assert "soil-aware-irrigation.md" in why


def test_verdict_import_requires_a_produced_file():
    passed, why = verdict_import(None)
    assert not passed
    assert "no proposal file produced" in why


@pytest.mark.parametrize("mutation,needle", [
    (lambda t: t.replace("lang: en", "lang: en\nmatriculation: 00000000"), "00000000"),
    (lambda t: "PROPOSAL - CONFIDENTIAL\n\n" + t, "CONFIDENTIAL"),
])
def test_verdict_import_reports_leaks_the_check_cannot_see(mutation, needle):
    passed, why = verdict_import(mutation(GOOD_IMPORT), CLEAN_CHECK, "x.md")
    assert not passed
    assert needle in why


def test_verdict_import_fails_on_check_errors():
    """The defect that motivated this: a file holding the expected substrings
    while its metadata block is unclosed and its RQs are not a list."""
    passed, why = verdict_import(GOOD_IMPORT, BROKEN_CHECK, "x.md")
    assert not passed
    assert "no trailing metadata block" in why
    assert "ordered-list research questions" in why


def test_verdict_import_tolerates_a_reference_shortfall():
    """The source carries what it carries — import must not invent sources."""
    passed, why = verdict_import(GOOD_IMPORT, SHORT_REFS_CHECK, "x.md")
    assert passed, why


@pytest.mark.parametrize("sentence", [
    "Rivera et al. [@Rivera23Survey] surveyed irrigation control.",
    "The LoRa study of Tanaka [@Tanaka24Lora] measured range.",
])
def test_verdict_import_rejects_a_name_carried_over_from_the_source(sentence):
    """The source renders "Rivera et al. [1]"; carrying that name into the
    prose beside a bracketed key freezes it against the reference entry."""
    mutated = GOOD_IMPORT.replace("# Introduction to the Topic",
                                  "# Introduction to the Topic\n\n" + sentence)
    passed, why = verdict_import(mutated, CLEAN_CHECK, "x.md")
    assert not passed
    assert "author name typed before a bracketed citation" in why


def test_verdict_import_ignores_reference_block_author_names():
    """`family: Rivera` in the metadata must not trip the typed-name check."""
    passed, why = verdict_import(GOOD_IMPORT, CLEAN_CHECK, "x.md")
    assert passed, why


def test_verdict_import_rejects_a_todo_marker_inside_the_metadata_block():
    """Observed in 4/4 dev-runner artifacts: pandoc rejects the whole block,
    while check.py extracts narrowly and reports the file clean."""
    broken = GOOD_IMPORT.replace(
        "    year: 2023\n",
        "    year: 2023\n  [TODO: recover full reference details]\n",
    )
    passed, why = verdict_import(broken, CLEAN_CHECK, "x.md")
    assert not passed
    assert "bare line in the metadata block" in why


@pytest.mark.parametrize("value", [
    '  title: "[TODO: recover the title]"',   # quoted
    "  title: [TODO: recover the title]",     # unquoted but keyed
])
def test_verdict_import_allows_a_keyed_todo_marker_in_the_metadata(value):
    """Both shapes parse under pandoc; only a bare line breaks the block."""
    keyed = GOOD_IMPORT.replace("  title: A survey of smart irrigation control", value)
    passed, why = verdict_import(keyed, CLEAN_CHECK, "x.md")
    assert passed, why


def test_verdict_import_allows_todo_markers_in_the_body():
    with_todo = GOOD_IMPORT.replace(
        "# Introduction to the Topic\n",
        "# Introduction to the Topic\n\n[TODO: state the delta to prior work]\n",
    )
    passed, why = verdict_import(with_todo, CLEAN_CHECK, "x.md")
    assert passed, why
