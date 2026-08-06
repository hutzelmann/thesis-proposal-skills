"""L0: todo-filter.lua renders [TODO: …] markers as numbered annotations.

Mirrors the publish pipeline's exact filter chain (a marker must survive
citeproc and rq-filter untouched); skipped when pandoc is not installed.
"""

import shutil
import subprocess
import textwrap
import zipfile
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "skills" / "proposal-publish" / "templates"

pytestmark = [
    pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed"),
    pytest.mark.slow,
]

METADATA = textwrap.dedent("""\

    ---
    title: Test Proposal
    subtitle: "{subtitle}"
    lang: en
    references:
    - id: Tan25Flexibl
      type: article-journal
      title: Flexible label-less drift detection
      author:
      - family: Tan
        given: Ada
      issued:
        year: 2025
      abstract: "Holds a bracketed fragment [TODO: never numbered] inside."
    ---
    """)


def convert(
    body: str,
    to: str = "typst",
    subtitle: str = "A Proposal",
    out: Path | None = None,
    template: bool = False,
) -> str:
    """Run the real publish filter chain over a document, return the output."""
    cmd = [
        "pandoc", "-f", "markdown", "-t", to,
        # unwrapped so assertions can match an annotation on one line
        "--wrap=none",
        "--lua-filter", str(TEMPLATES / "author-intext.lua"),
        "--lua-filter", str(TEMPLATES / "cite-split.lua"),
        "--csl", str(TEMPLATES / "compact-numeric.csl"),
        "--citeproc",
        "--lua-filter", str(TEMPLATES / "rq-filter.lua"),
        "--lua-filter", str(TEMPLATES / "todo-filter.lua"),
    ]
    if template:
        cmd += ["--template", str(TEMPLATES / "proposal.typ")]
    if out is not None:
        cmd += ["-o", str(out)]
    result = subprocess.run(
        cmd, input=body + METADATA.format(subtitle=subtitle),
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def test_own_line_marker_becomes_a_block_and_keeps_surrounding_prose():
    out = convert(textwrap.dedent("""\
        Prose before the gap.
        [TODO: name the dataset]
        Prose after the gap.
        """))
    assert "#todo-block(1)[name the dataset]" in out
    assert "Prose before the gap." in out
    assert "Prose after the gap." in out
    assert "[TODO:" not in out


def test_marker_inside_a_sentence_stays_inline():
    out = convert("The evaluation uses [TODO: select the dataset] as its input.\n")
    assert "#todo-inline(1)[select the dataset]" in out
    assert "The evaluation uses" in out
    assert "as its input." in out


def test_numbering_is_continuous_across_both_forms():
    out = convert(textwrap.dedent("""\
        First gap is [TODO: inline one] here.

        Second gap owns its line.
        [TODO: block two]
        Prose resumes.

        Third gap is [TODO: inline three] here.
        """))
    assert "#todo-inline(1)[inline one]" in out
    assert "#todo-block(2)[block two]" in out
    assert "#todo-inline(3)[inline three]" in out


def test_subtitle_marker_takes_number_one_and_body_continues():
    # needs the real template: the title block is where a subtitle renders
    out = convert(
        "A gap in the body [TODO: body gap] here.\n",
        subtitle="[TODO: confirm degree level]",
        template=True,
    )
    assert "#todo-inline(1)[confirm degree level]" in out
    assert "#todo-inline(2)[body gap]" in out


def test_marker_inside_a_reference_is_neither_styled_nor_numbered():
    out = convert("A gap in the body [TODO: body gap] here.\n")
    # the reference abstract holds "[TODO: never numbered]" — it must not
    # consume number 1, and must never reach the annotation macros
    assert "#todo-inline(1)[body gap]" in out
    assert "never numbered" not in out


def test_marker_in_a_research_question_item_degrades_to_inline():
    out = convert(textwrap.dedent("""\
        # Research Focus and Research Questions

        1. To what degree do drift signals predict decay [@Tan25Flexibl], and
           [TODO: confirm the baseline detector] under delay?
        2. How does label delay affect reliability?
        """))
    # a block annotation here would break rq-filter's pandoc.Plain rebuild
    assert "#todo-block" not in out
    assert "#todo-inline(1)[confirm the baseline detector]" in out
    assert "#rq(1)[" in out
    assert "#rq(2)[" in out
    assert "@Tan25Flexibl" not in out  # citation still resolved


def test_marker_split_across_source_lines_joins_into_one_annotation():
    out = convert(textwrap.dedent("""\
        The gap is [TODO: decide between a prototype
        implementation and a literature review] and it ends here.
        """))
    assert (
        "#todo-inline(1)[decide between a prototype implementation and a literature review]"
        in out
    )


def test_latex_guard_skips_the_fill_when_the_hint_carries_markup():
    plain = convert("A gap [TODO: pick one option] here.\n", to="latex")
    assert "\\todoinline{1}{pick one option}" in plain

    marked_up = convert("A gap [TODO: pick *either* option] here.\n", to="latex")
    # soul aborts on anything richer than plain text inside \hl
    assert "\\todoinlineplain{1}{" in marked_up
    assert "\\todoinline{1}{" not in marked_up


def test_latex_own_line_marker_uses_the_block_macro():
    out = convert(textwrap.dedent("""\
        Prose before.
        [TODO: name the dataset]
        Prose after.
        """), to="latex")
    assert "\\todoblock{1}{name the dataset}" in out


def test_docx_tier_emits_a_highlighted_run(tmp_path):
    target = tmp_path / "out.docx"
    convert("A gap [TODO: select the dataset] here.\n", to="docx", out=target)
    with zipfile.ZipFile(target) as archive:
        document = archive.read("word/document.xml").decode("utf-8")
    assert "w:highlight" in document
    assert "TODO 1" in document
