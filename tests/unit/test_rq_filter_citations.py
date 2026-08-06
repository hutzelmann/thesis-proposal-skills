"""Regression: citations inside RQ list items must survive rq-filter.lua.

The filter once re-serialized each RQ item as a standalone sub-document,
which turned already-resolved citations back into bare typst @key
references that the final document cannot resolve, breaking the build
(fixed in a8127ef). Mirrors the publish pipeline's exact filter chain;
skipped when pandoc is not installed.
"""

import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
TEMPLATES = REPO / "skills" / "proposal-publish" / "templates"

DOC = textwrap.dedent("""\
    ---
    references:
    - id: Tan25Flexibl
      type: article-journal
      title: Flexible label-less drift detection
      author:
      - family: Tan
        given: Ada
      issued:
        year: 2025
    ---

    # Research Focus and Research Questions

    1. To what degree do drift signals predict decay, compared to
       label-less detectors designed for false-positive control
       [@Tan25Flexibl]?
    2. How does label delay affect signal reliability?
    """)


def run_filter_chain(target: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["pandoc", "-f", "markdown", "-t", target,
         "--lua-filter", str(TEMPLATES / "cite-split.lua"),
         "--csl", str(TEMPLATES / "compact-numeric.csl"),
         "--citeproc",
         "--lua-filter", str(TEMPLATES / "rq-filter.lua")],
        input=DOC, capture_output=True, text=True, check=True,
    )


@pytest.mark.slow
@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_citation_inside_rq_reaches_typst_resolved():
    result = run_filter_chain("typst")
    out = result.stdout
    assert "#rq(1)[" in out
    assert "#rq(2)[" in out
    # the broken filter re-emitted the citation as a bare typst @key
    # reference with no matching label in the final document
    assert "@Tan25Flexibl" not in out
    assert "not found" not in result.stderr


@pytest.mark.slow
@pytest.mark.skipif(shutil.which("pandoc") is None, reason="pandoc not installed")
def test_citation_inside_rq_reaches_latex_resolved():
    result = run_filter_chain("latex")
    out = result.stdout
    assert "\\rqblock{1}{" in out
    assert "\\rqblock{2}{" in out
    assert "@Tan25Flexibl" not in out
    assert "not found" not in result.stderr
