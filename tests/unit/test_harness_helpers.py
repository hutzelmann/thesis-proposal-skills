"""L0: pure scoring helpers from harness/l1_checks.py (no model calls)."""

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "harness"))

from l1_checks import disallowed_errors, is_enumerated_review, parse_grade  # noqa: E402


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
