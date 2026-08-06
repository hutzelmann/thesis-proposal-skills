"""L0: author-in-text citation rendering through the real publish chain.

A numeric CSL style has no names element in its citation layout, so citeproc's
author-only half of an author-in-text citation renders empty and `@key`
collapses to a bare `[1]` — the defect author-intext.lua exists to fix. These
tests drive pandoc with the skill's actual filters and style, so a reordered
filter chain or a regressed CSL layout fails here. Skipped when pandoc is
not installed.
"""

import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "skills" / "proposal-publish" / "templates"
FIXTURES = REPO / "tests" / "fixtures"

# the filter joins label and bracket with this; spelled out so no assertion
# needle can carry an invisible literal instead
NBSP = "\u00a0"

REFERENCES = """\
    references:
    - id: Six
      type: article-journal
      title: Six-author work
      author:
      - family: Smith
        given: Alice
      - family: Brown
        given: Bob
      - family: Carter
        given: Cara
      - family: Diaz
        given: Dan
      - family: Evans
        given: Eve
      - family: Frank
        given: Fay
      issued:
        year: 2020
    - id: Three
      type: article-journal
      title: Three-author work
      author:
      - family: Tan
        given: Ada
      - family: Ito
        given: Ken
      - family: Roy
        given: Ravi
      issued:
        year: 2021
    - id: Two
      type: article-journal
      title: Two-author work
      author:
      - family: Jones
        given: Jane
      - family: Klein
        given: Karl
      issued:
        year: 2019
    - id: One
      type: article-journal
      title: Single-author work
      author:
      - family: Weiss
        given: Nora
      issued:
        year: 2022
    - id: Literal
      type: report
      title: Threat landscape
      author:
      - literal: ENISA
      issued:
        year: 2024
    - id: Particle
      type: book
      title: Process mining
      author:
      - family: Aalst
        given: Wil
        non-dropping-particle: van der
      issued:
        year: 2016
    - id: EditorOnly
      type: book
      title: Collected works on drift
      editor:
      - family: Hahn
        given: Lena
      issued:
        year: 2018
    - id: TitleOnly
      type: webpage
      title: Model monitoring practices
      issued:
        year: 2001
"""


def document(body: str, lang: str = "en") -> str:
    # the blank line before the trailing block is part of the format contract;
    # without it pandoc reads the block as body text and no reference resolves
    return (
        textwrap.dedent(body).rstrip("\n")
        + "\n\n---\ntitle: T\nlang: " + lang + "\n"
        + textwrap.dedent(REFERENCES) + "---\n"
    )


def render(doc: str, to: str = "plain", resolves: bool = True) -> str:
    """Run the real pre-citeproc chain from publish.py, in its real order."""
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", to,
         "--lua-filter", str(TEMPLATES / "author-intext.lua"),
         "--lua-filter", str(TEMPLATES / "cite-split.lua"),
         "--csl", str(TEMPLATES / "compact-numeric.csl"),
         "--citeproc"],
        input=doc, capture_output=True, text=True, check=True,
    )
    if resolves:
        assert "not found" not in result.stderr
    return result.stdout


pytestmark = [
    pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed"),
    pytest.mark.slow,
]


@pytest.mark.parametrize(("key", "expected"), [
    ("One", "Weiss"),
    ("Two", "Jones and Klein"),
    ("Three", "Tan et al."),
    ("Six", "Smith et al."),
    ("Literal", "ENISA"),
    ("Particle", "van der Aalst"),
    ("EditorOnly", "Hahn (ed.)"),
    ("TitleOnly", "“Model monitoring practices”"),
])
def test_author_label_forms_en(key, expected):
    out = render(document(f"Body: @{key} reports things."))
    assert f"Body: {expected}{NBSP}[1] reports things." in out


@pytest.mark.parametrize(("key", "expected"), [
    ("Two", "Jones und Klein"),
    ("Three", "Tan et al."),
    ("EditorOnly", "Hahn (Hrsg.)"),
])
def test_author_label_forms_de(key, expected):
    out = render(document(f"Text: @{key} berichtet.", lang="de"))
    assert f"Text: {expected}{NBSP}[1] berichtet." in out


def test_bracketed_form_stays_bare():
    out = render(document("Reported widely [@Three]."))
    assert "Reported widely [1]." in out
    assert "Tan" not in out.split("[1] Tan")[0]


def test_multi_key_bracketed_still_splits_per_reference():
    out = render(document("Both agree [@Three; @Two]."))
    assert "Both agree [1] [2]." in out


def test_locator_in_bracketed_form():
    out = render(document("See [@Three, p. 5] for details."))
    assert "See [1, p. 5] for details." in out


def test_locator_in_author_in_text_form():
    out = render(document("As @Three [p. 5] writes."))
    assert f"As Tan et al.{NBSP}[1, p. 5] writes." in out


def test_suffix_containing_a_further_citation():
    out = render(document("Thus @Three [see also @Two] argue."))
    assert f"Thus Tan et al.{NBSP}[1] [see also 2] argue." in out


def test_two_author_in_text_citations_in_one_sentence():
    out = render(document("Both @Three and @Two report."))
    assert f"Both Tan et al.{NBSP}[1] and Jones and Klein{NBSP}[2] report." in out


def test_author_in_text_inside_research_question_item():
    """rq-filter.lua re-serializes RQ items post-citeproc; the expanded label
    must survive that, as resolved citations must (see test_rq_filter_citations).
    """
    doc = document("""\
        # Research Focus and Research Questions

        1. How far does the detector of @Three generalize?
        2. How does label delay affect reliability?
        """)
    result = subprocess.run(
        ["pandoc", "-f", "markdown", "-t", "typst",
         "--lua-filter", str(TEMPLATES / "author-intext.lua"),
         "--lua-filter", str(TEMPLATES / "cite-split.lua"),
         "--csl", str(TEMPLATES / "compact-numeric.csl"),
         "--citeproc",
         "--lua-filter", str(TEMPLATES / "rq-filter.lua")],
        input=doc, capture_output=True, text=True, check=True,
    )
    assert "#rq(1)[" in result.stdout
    assert "#rq(2)[" in result.stdout
    assert "Tan et al.~\\[1\\]" in result.stdout
    assert "@Three" not in result.stdout


def test_non_breaking_space_survives_typst_writer():
    out = render(document("Body: @Three reports."), to="typst")
    assert "Tan et al.~\\[1\\]" in out


@pytest.mark.parametrize(("fixture", "label", "sentence_start"), [
    ("f12-clean-de/typsystem-einheitenfehler.md", "Vogel", "Gegenüber"),
    ("f16-figures-import/sensor-anomaly-triage.md", "Duarte", None),
    ("w03-snowball-seed/serverless-energy-scheduling.md", "Weiss and Lindgren", None),
])
def test_corpus_fixtures_render_their_author_in_text_citations(fixture, label, sentence_start):
    """The corpus already writes `@key` where the authors are the subject; before
    this filter existed those sentences rendered as a bare "[n] propose …".
    The label is joined to its bracket by U+00A0, not a plain space.
    """
    out = render((FIXTURES / fixture).read_text(encoding="utf-8"))
    assert re.search(rf"{re.escape(label)}{NBSP}\[\d+\]", out), out
    if sentence_start:
        assert not re.search(rf"{sentence_start} \[\d+\]", out), out


def test_unknown_key_is_left_alone():
    """A citation the metadata does not define must not crash the filter."""
    out = render(document("Body: @Missing reports."), resolves=False)
    assert "Missing" in out
