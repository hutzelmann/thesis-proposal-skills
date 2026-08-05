"""L0: mechanical thesis-title tells (skill-check spec, guidance-model spec).

Only the tells a pattern can carry are tested here. Whether a proper noun in a
title names a tool, a product or a vendor is agent judgement and is deliberately
absent from the structured data, so no test can reach it.
"""

import json
import subprocess
import sys
import unicodedata
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CHECK = REPO / "skills" / "proposal-check" / "scripts" / "check.py"
FIXTURES = REPO / "tests" / "fixtures"
CLEAN = FIXTURES / "f00-clean-en" / "ml-code-review.md"
TITLE_CFG = json.loads((REPO / "shared" / "structure.json").read_text())["title"]


def run_check(proposal: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(CHECK), str(proposal)], capture_output=True, text=True
    )


def with_title(tmp_path: Path, title: str, name: str = "titled.md") -> Path:
    source = CLEAN.read_text()
    victim = tmp_path / name
    victim.write_text(
        source.replace(
            "\ntitle: Machine Learning for Automated Code Review", f"\ntitle: {title}", 1
        )
    )
    return victim


@pytest.mark.parametrize(
    "title",
    [
        "Implementing a Detector for Data Drift in Deployed Pipelines",
        "Development of a Detector for Data Drift in Deployed Pipelines",
        "Entwicklung eines Detektors für Data Drift in produktiven Pipelines",
        "Konzept für ein Verfahren zur Erkennung von Data Drift",
    ],
)
def test_implementation_opener_warns(tmp_path, title):
    out = run_check(with_title(tmp_path, title)).stdout
    assert "implementation framing" in out
    assert "study certificate" in out
    assert "WARNING" in out


def test_opener_only_matches_at_the_start(tmp_path):
    """A framing word mid-title describes the object, not the thesis."""
    title = "A Reference Model for the Development of Drift Detectors"
    assert "implementation framing" not in run_check(with_title(tmp_path, title)).stdout


def test_buzzword_warns(tmp_path):
    title = "A Cutting-Edge Approach to Drift Detection in Deployed Pipelines"
    out = run_check(with_title(tmp_path, title)).stdout
    assert "marketing tone" in out
    assert "`cutting-edge`" in out


def test_german_buzzword_warns(tmp_path):
    title = "Ein bahnbrechendes Verfahren zur Erkennung von Data Drift"
    out = run_check(with_title(tmp_path, title)).stdout
    assert "marketing tone" in out
    assert "`bahnbrechend`" in out


def test_decomposed_umlaut_matches_too(tmp_path):
    """NFD input ('a' + combining diaeresis) is the same word to the reader."""
    title = unicodedata.normalize("NFD", "Ein revolutionäres Verfahren zur Erkennung von Data Drift")
    assert "marketing tone" in run_check(with_title(tmp_path, title)).stdout


def test_block_scalar_title_is_not_judged(tmp_path):
    """`title: >-` continues on lines the narrow extraction never reads; judging
    the indicator itself would report a one-word title that does not exist."""
    victim = tmp_path / "folded.md"
    victim.write_text(
        CLEAN.read_text().replace(
            "\ntitle: Machine Learning for Automated Code Review",
            "\ntitle: >-\n  Validity of Unsupervised Drift Alerts Against Delayed-Label Decay",
            1,
        )
    )
    assert "title runs" not in run_check(victim).stdout


def test_german_minimum_is_lower_than_the_english_one(tmp_path):
    """German compounds into one noun what English spreads over three."""
    assert TITLE_CFG["min_words"]["de"] < TITLE_CFG["min_words"]["en"]
    victim = tmp_path / "de.md"
    victim.write_text(
        CLEAN.read_text()
        .replace("\nlang: en", "\nlang: de", 1)
        .replace(
            "\ntitle: Machine Learning for Automated Code Review",
            "\ntitle: Anomalieerkennung in Produktionsnetzwerken",
            1,
        )
    )
    assert "title runs" not in run_check(victim).stdout


@pytest.mark.parametrize("domain_term", ["Smart Home", "Intelligent Tutoring"])
def test_domain_terms_are_not_buzzwords(tmp_path, domain_term):
    """`smart` and `intelligent` are domain vocabulary, deliberately not listed."""
    title = f"Energy Attribution in {domain_term} Deployments Under Partial Metering"
    assert "marketing tone" not in run_check(with_title(tmp_path, title)).stdout


def test_question_title_warns(tmp_path):
    title = "How Reliable Are Unsupervised Drift Detectors in Production?"
    out = run_check(with_title(tmp_path, title)).stdout
    assert "phrased as a question" in out


def test_title_below_minimum_words_warns(tmp_path):
    title = "Drift Detection"
    out = run_check(with_title(tmp_path, title)).stdout
    assert f"at least {TITLE_CFG['min_words']['en']} expected" in out
    assert "without the subtitle" in out


def test_title_above_maximum_words_warns(tmp_path):
    title = " ".join(["Drift"] * (TITLE_CFG["max_words"] + 1))
    out = run_check(with_title(tmp_path, title)).stdout
    assert f"at most {TITLE_CFG['max_words']} expected" in out


@pytest.mark.parametrize(
    "title",
    [
        "Implementing a Detector for Data Drift in Deployed Pipelines",
        "A Cutting-Edge Approach to Drift Detection in Deployed Pipelines",
        "How Reliable Are Unsupervised Drift Detectors in Production?",
        "Drift Detection",
        " ".join(["Drift"] * (TITLE_CFG["max_words"] + 1)),
    ],
)
def test_every_title_warning_names_the_certificate(tmp_path, title):
    """The certificate is the whole reason a title warning outranks a style nit —
    a finding that omits it reads as an arbitrary complaint."""
    lines = [
        line for line in run_check(with_title(tmp_path, title)).stdout.splitlines()
        if line.startswith("- WARNING: title")
    ]
    assert lines, "expected a title warning"
    for line in lines:
        assert "study certificate" in line, line


def test_word_count_bounds_are_inclusive(tmp_path):
    at_min = " ".join(["Drift"] * TITLE_CFG["min_words"]["en"])
    at_max = " ".join(["Drift"] * TITLE_CFG["max_words"])
    assert "title runs" not in run_check(with_title(tmp_path, at_min, "min.md")).stdout
    assert "title runs" not in run_check(with_title(tmp_path, at_max, "max.md")).stdout


def test_clean_title_stays_silent(tmp_path):
    """A title naming a contribution and its object costs the student nothing."""
    title = "Validity of Unsupervised Drift Alerts Against Delayed-Label Decay"
    out = run_check(with_title(tmp_path, title)).stdout
    for tell in ("implementation framing", "marketing tone", "phrased as a question", "title runs"):
        assert tell not in out


def test_title_tells_never_fail_the_run(tmp_path):
    """Heuristics on a semantic matter: warnings, never a non-zero exit."""
    title = "Implementing a Cutting-Edge Dashboard for Everything?"
    result = run_check(with_title(tmp_path, title))
    out = result.stdout
    assert "implementation framing" in out
    assert "marketing tone" in out
    assert "phrased as a question" in out
    assert result.returncode == 0, out


def test_no_tool_names_are_encoded_as_data():
    """The formalization boundary: the tool set is unbounded, so it stays prose."""
    listed = " ".join(TITLE_CFG["implementation_openers"] + TITLE_CFG["buzzwords"]).lower()
    for tool in ("kubernetes", "react", "docker", "python", "sap", "tensorflow", "aws"):
        assert tool not in listed
