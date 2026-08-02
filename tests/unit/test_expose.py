"""L0: the Overleaf-ready LaTeX project generator (skill-publish spec).

No TeX or pandoc is involved — the generator is pure stdlib, so these tests
assert on the emitted .tex and .bib rather than on a compiled PDF.
"""

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "skills" / "proposal-publish" / "scripts"
STRUCTURE = json.loads(
    (REPO / "skills" / "proposal-publish" / "references" / "structure.json").read_text(encoding="utf-8")
)


def load_expose():
    sys.path.insert(0, str(SCRIPTS))
    spec = importlib.util.spec_from_file_location("expose", SCRIPTS / "expose.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


expose = load_expose()


MINIMAL = """# Introduction and Motivation

Cars exist [@Smith24Cars].

# Problem Statement and Research Questions

Something is unclear.

1. To what degree does it matter?

# Objectives

- Measure the thing.

# Related Work

@Smith24Cars measured it once.

# Methodology: Prototype Implementation

## Use Case Definition

A simulator.

## Previous Work

Tools exist.

## Requirements

It must run.

## Evaluation

It is measured (RQ1).

# Expected Contributions and Results

Evidence is expected.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Build | 1-6 |
| Measure | 6-10 |
| Submit | 12 |

Build gates measurement.

---
title: A Title
author: Jane Doe
student_id: "12345678"
degree_program: MSc Computer Science
supervisor: Prof. Dr. Example
submission_date: 01.01.2027
lang: en
abbreviations:
  ADAS: Advanced Driver Assistance Systems
references:
- id: Smith24Cars
  type: paper-conference
  author:
  - family: Smith
    given: J.
  issued:
    year: 2024
  title: Cars and Their Discontents
  container-title: Proceedings of Example
  DOI: 10.xxxx/x1
---
"""


@pytest.fixture
def built(tmp_path):
    source = tmp_path / "thing.md"
    source.write_text(MINIMAL, encoding="utf-8")
    out = tmp_path / "out"
    notes = expose.build(source, out, STRUCTURE)
    return out, notes, (out / "expose.tex").read_text(encoding="utf-8")


def test_emits_project_files(built):
    out, _, _ = built
    assert (out / "expose.tex").exists()
    assert (out / "literature.bib").exists()
    assert (out / "images" / "thiRGB.jpg").exists()


def test_no_placeholders_survive(built):
    _, _, tex = built
    assert "{{" not in tex


def test_title_page_filled_from_metadata(built):
    _, notes, tex = built
    assert r"\textbf{Jane Doe}" in tex
    assert "12345678" in tex
    assert "Prof. Dr. Example" in tex
    assert not [n for n in notes if "title page" in n]


def test_missing_title_field_is_reported_not_invented(tmp_path):
    source = tmp_path / "thing.md"
    source.write_text(MINIMAL.replace('student_id: "12345678"\n', ""), encoding="utf-8")
    notes = expose.build(source, tmp_path / "out", STRUCTURE)
    tex = (tmp_path / "out" / "expose.tex").read_text(encoding="utf-8")
    assert any("student_id" in n for n in notes)
    assert "TODO: add student ID" in tex


def test_methodology_heading_loses_the_branch_name(built):
    """The template renders a plain "Methodology"; the branch lives in the source
    only, so that check.py can verify the right subsections are present."""
    _, _, tex = built
    assert r"\section{Methodology}" in tex
    assert "Prototype Implementation}" not in tex


def test_sections_and_subsections_render(built):
    _, _, tex = built
    for section in ("Introduction and Motivation", "Objectives", "Related Work",
                    "Expected Contributions and Results", "Work Plan and Schedule"):
        assert rf"\section{{{section}}}" in tex
    assert r"\subsection{Use Case Definition}" in tex


def test_research_questions_become_an_enumerate(built):
    _, _, tex = built
    assert r"\begin{enumerate}" in tex
    assert r"\item To what degree does it matter?" in tex


def test_work_plan_table_becomes_a_gantt_chart(built):
    _, _, tex = built
    assert r"\begin{ganttchart}" in tex
    assert r"{Build}{1}{6}" in tex
    # a single-week row is a milestone, not a zero-length bar
    assert r"\ganttmilestone{Submit}{12}" in tex


def test_work_plan_without_week_ranges_degrades_to_a_table(tmp_path):
    source = tmp_path / "thing.md"
    source.write_text(
        MINIMAL.replace("| Build | 1-6 |", "| Build | early |")
               .replace("| Measure | 6-10 |", "| Measure | later |")
               .replace("| Submit | 12 |", "| Submit | end |"),
        encoding="utf-8",
    )
    notes = expose.build(source, tmp_path / "out", STRUCTURE)
    tex = (tmp_path / "out" / "expose.tex").read_text(encoding="utf-8")
    assert r"\begin{ganttchart}" not in tex
    assert r"\begin{tabular}" in tex
    assert any("week ranges" in n for n in notes)


def test_citations_convert(built):
    _, _, tex = built
    assert r"\cite{Smith24Cars}" in tex
    assert r"\citet{Smith24Cars}" in tex


def test_trailing_punctuation_is_not_swallowed_into_a_citation_key(tmp_path):
    """`@Key.` at a sentence end must cite Key and keep the full stop."""
    source = tmp_path / "thing.md"
    source.write_text(
        MINIMAL.replace("@Smith24Cars measured it once.", "It was measured by @Smith24Cars."),
        encoding="utf-8",
    )
    expose.build(source, tmp_path / "out", STRUCTURE)
    tex = (tmp_path / "out" / "expose.tex").read_text(encoding="utf-8")
    assert r"\citet{Smith24Cars}." in tex
    assert "Smith24Cars.}" not in tex


def test_bibtex_conversion(built):
    out, _, _ = built
    bib = (out / "literature.bib").read_text(encoding="utf-8")
    assert "@inproceedings{Smith24Cars," in bib
    assert "author    = {Smith, J.}" in bib
    assert "booktitle = {Proceedings of Example}" in bib
    assert "doi       = {10.xxxx/x1}" in bib


def test_glossary_only_when_abbreviations_declared(built, tmp_path):
    _, _, tex = built
    assert r"\newglossaryentry{ADAS}" in tex
    assert r"\printglossary" in tex

    source = tmp_path / "bare.md"
    source.write_text(
        MINIMAL.replace("abbreviations:\n  ADAS: Advanced Driver Assistance Systems\n", ""),
        encoding="utf-8",
    )
    expose.build(source, tmp_path / "bare-out", STRUCTURE)
    bare = (tmp_path / "bare-out" / "expose.tex").read_text(encoding="utf-8")
    assert "glossaries" not in bare
    assert r"\printglossary" not in bare


def test_latex_specials_are_escaped(tmp_path):
    source = tmp_path / "thing.md"
    source.write_text(MINIMAL.replace("Cars exist", "Cars & trucks cost 50% more"), encoding="utf-8")
    expose.build(source, tmp_path / "out", STRUCTURE)
    tex = (tmp_path / "out" / "expose.tex").read_text(encoding="utf-8")
    assert r"Cars \& trucks cost 50\% more" in tex


def test_missing_metadata_block_is_an_error(tmp_path):
    source = tmp_path / "thing.md"
    source.write_text("# Introduction and Motivation\n\nNo metadata here.\n", encoding="utf-8")
    with pytest.raises(expose.ExposeError):
        expose.build(source, tmp_path / "out", STRUCTURE)


def test_german_source_sets_main_babel_language(tmp_path):
    source = tmp_path / "de.md"
    source.write_text(
        MINIMAL.replace("lang: en", "lang: de")
               .replace("# Methodology: Prototype Implementation", "# Methodik: Prototypimplementierung"),
        encoding="utf-8",
    )
    expose.build(source, tmp_path / "out", STRUCTURE)
    tex = (tmp_path / "out" / "expose.tex").read_text(encoding="utf-8")
    assert r"\usepackage[english, ngerman]{babel}" in tex  # last listed wins in babel
    assert r"\section{Methodik}" in tex


@pytest.mark.parametrize("fixture", ["f00-clean-en", "f21-empirical-evaluation", "f22-mixed-methods"])
def test_compliant_fixtures_build_without_notes(tmp_path, fixture):
    """A fixture that passes check must also produce a project whose only notes
    concern title-page fields the fixture deliberately leaves open."""
    src = next(p for p in (REPO / "tests" / "fixtures" / fixture).glob("*.md")
               if p.name != "guidelines.md")
    notes = expose.build(src, tmp_path / fixture, STRUCTURE)
    assert all("title page" in n for n in notes), notes
    tex = (tmp_path / fixture / "expose.tex").read_text(encoding="utf-8")
    assert "{{" not in tex
    assert r"\begin{ganttchart}" in tex
