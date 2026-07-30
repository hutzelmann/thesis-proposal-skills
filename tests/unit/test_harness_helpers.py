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


def test_verdict_import_accepts_a_clean_import():
    passed, why = verdict_import(GOOD_IMPORT, "soil-aware-irrigation.md")
    assert passed, why
    assert "soil-aware-irrigation.md" in why


def test_verdict_import_requires_a_produced_file():
    passed, why = verdict_import(None)
    assert not passed
    assert "no proposal file produced" in why


@pytest.mark.parametrize("mutation,needle", [
    (lambda t: t.split("\n---")[0], "not in standard format"),
    (lambda t: t.replace("lang: en", "lang: en\nmatriculation: 00000000"), "00000000"),
    (lambda t: "PROPOSAL - CONFIDENTIAL\n\n" + t, "CONFIDENTIAL"),
    (lambda t: t.replace("# Introduction", "# Timeline\n\nMonth 1-2.\n\n# Introduction"), "timeline"),
])
def test_verdict_import_reports_each_failure_mode(mutation, needle):
    passed, why = verdict_import(mutation(GOOD_IMPORT), "x.md")
    assert not passed
    assert needle in why


@pytest.mark.parametrize("sentence", [
    "Rivera et al. [@Rivera23Survey] surveyed irrigation control.",
    "The LoRa study of Tanaka [@Tanaka24Lora] measured range.",
])
def test_verdict_import_rejects_a_name_carried_over_from_the_source(sentence):
    """The source renders "Rivera et al. [1]"; carrying that name into the
    prose beside a bracketed key freezes it against the reference entry."""
    passed, why = verdict_import(GOOD_IMPORT.replace("# Introduction to the Topic",
                                                     "# Introduction to the Topic\n\n" + sentence), "x.md")
    assert not passed
    assert "author name typed before a bracketed citation" in why


def test_verdict_import_ignores_reference_block_author_names():
    """`family: Rivera` in the metadata must not trip the typed-name check."""
    passed, why = verdict_import(GOOD_IMPORT, "x.md")
    assert passed, why
