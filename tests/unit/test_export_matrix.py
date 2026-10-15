"""L0: every fixture proposal must build on every resolvable output tier.

The bug this guards against shipped because no test had ever produced a
document: test_publish.py exercises engine *selection* against a fake `which`,
never build() itself. Selection logic is not coverage of a build path.

These drive publish.build() directly rather than reassembling the pandoc
invocation, so a defect in how the shipped code builds that command is caught
instead of reproduced. Each tier skips when its toolchain is absent; CI supplies
the toolchain in container jobs so they run there.
"""

import os
import re
import shutil
import subprocess
import zipfile
from pathlib import Path

import publish
import pytest
from fixture_paths import FIXTURES, corpus_proposals, fixture_of, fixture_proposal

REPO = Path(__file__).resolve().parents[2]

# a fixture's proposal, wherever its layout keeps it; what else sits beside one
# — a workspace override, a harvest record, an earlier round's review — is an
# input to a skill, never a document to build (fixture_paths.corpus_proposals).
PROPOSALS = corpus_proposals()


def latex_engine():
    return next((e for e in publish.LATEX_ENGINES if shutil.which(e)), None)


TIERS = {
    "typst": lambda: ("typst", "typst") if shutil.which("typst") else None,
    "latex": lambda: ("latex", latex_engine()) if latex_engine() else None,
    "docx": lambda: ("docx", "pandoc"),
}


def staged(proposal: Path, tmp_path: Path) -> Path:
    """Copy the proposal's folder, so relatively referenced assets resolve —
    f16-figures-import's proposal links the img/ folder beside it."""
    target = tmp_path / proposal.parent.name
    shutil.copytree(proposal.parent, target)
    return target / proposal.name


def build_in(proposal: Path, tmp_path: Path, tier: str) -> list[Path]:
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc not installed")
    resolved = TIERS[tier]()
    if resolved is None:
        pytest.skip(f"no toolchain for the {tier} tier")
    kind, tool = resolved
    return publish.build(staged(proposal, tmp_path), kind, tool)


@pytest.mark.slow
@pytest.mark.parametrize("tier", sorted(TIERS))
@pytest.mark.parametrize("proposal", PROPOSALS, ids=fixture_of)
def test_fixture_builds_on_every_tier(proposal, tier, tmp_path):
    outputs = build_in(proposal, tmp_path, tier)
    assert outputs, f"{tier} tier declared no outputs"
    for path in outputs:
        assert path.exists(), f"{tier} tier declared {path.name} but did not write it"
        assert path.stat().st_size > 0, f"{tier} tier wrote an empty {path.name}"
        if path.suffix == ".pdf":
            assert path.read_bytes()[:5] == b"%PDF-", f"{path.name} is not a PDF"
        if path.suffix == ".docx":
            assert zipfile.is_zipfile(path), f"{path.name} is not a readable archive"


def test_discovery_covers_the_whole_corpus():
    fixtures = {fixture_of(p) for p in PROPOSALS}
    expected = {p.parent.name for p in FIXTURES.glob("*/expected.json")}
    assert fixtures == expected, (
        f"fixture proposals and oracles disagree: {fixtures ^ expected}"
    )


# -- content the build-succeeds check cannot see ---------------------------

CONTENT_FIXTURE = fixture_proposal("f19-drift-alert-validity")


@pytest.fixture(scope="module")
def typst_source(tmp_path_factory):
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc not installed")
    tmp_path = tmp_path_factory.mktemp("content")
    proposal = staged(CONTENT_FIXTURE, tmp_path)
    source = proposal.with_suffix(".typ")
    subprocess.run(
        [*publish.pandoc_command(proposal, "typst"), "-o", str(source)],
        capture_output=True, text=True, check=True,
    )
    return source.read_text(encoding="utf-8")


@pytest.mark.slow
def test_citations_resolve_in_the_built_source(typst_source):
    # an unresolved key reaches typst as a bare @key with no matching label
    assert "@Tan25Flexibl" not in typst_source
    assert "@Cerqueira26Framewo" not in typst_source


@pytest.mark.slow
def test_research_question_styling_survives(typst_source):
    assert "#rq(1)[" in typst_source
    assert "#rq(3)[" in typst_source


@pytest.mark.slow
def test_todo_markers_are_annotated_and_numbered(typst_source):
    assert "[TODO:" not in typst_source
    assert "#todo-block(1)[" in typst_source
    assert "#todo-block(4)[" in typst_source


# -- figures embedded whatever the working directory (testing-harness:
#    Figure embedding verified from another working directory) --------------

FIGURE_FIXTURE = fixture_proposal("f16-figures-import")
FIGURE_LINK = re.compile(r"!\[[^\]]*\]\((img/[^)\s]+)\)")
# a PDF image object; pdfTeX writes `/Subtype/Image`, dvipdfmx `/Subtype /Image`
PDF_IMAGE = re.compile(rb"/Subtype ?/Image")
# the parent of a proposal folder whose path pandoc's --resource-path cannot carry
SEPARATOR_PARENT = f"with{os.pathsep}separator"


def figure_workspace(root: Path) -> Path:
    """The figure fixture's proposal and its `img/` as a proposal folder under
    `root`, and nothing else: its import-source PDF stays behind, so a PDF the
    test finds is the one the build wrote."""
    folder = root / FIGURE_FIXTURE.stem
    folder.mkdir(parents=True)
    shutil.copy2(FIGURE_FIXTURE, folder / FIGURE_FIXTURE.name)
    shutil.copytree(FIGURE_FIXTURE.parent / "img", folder / "img")
    return folder / FIGURE_FIXTURE.name


def embedded_figures(output: Path) -> int:
    if output.suffix == ".docx":
        with zipfile.ZipFile(output) as archive:
            return sum(1 for name in archive.namelist() if name.startswith("word/media/"))
    return len(PDF_IMAGE.findall(output.read_bytes()))


@pytest.mark.slow
@pytest.mark.parametrize("parent", ["", SEPARATOR_PARENT], ids=["plain", "separator"])
@pytest.mark.parametrize("tier", ["latex", "docx"])
def test_figures_embed_when_built_from_the_workspace_root(tier, parent, tmp_path, monkeypatch):
    """Built through the shipped build path from the workspace root, the way a
    user's agent runs publish: pandoc resolved `img/` against the working
    directory and dropped both figures with only a warning (skill-publish:
    Figures resolved against the proposal's folder)."""
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc not installed")
    resolved = TIERS[tier]()
    if resolved is None:
        pytest.skip(f"no toolchain for the {tier} tier")
    kind, tool = resolved
    proposal = figure_workspace(tmp_path / parent)
    linked = len(FIGURE_LINK.findall(proposal.read_text(encoding="utf-8")))
    assert linked == 2, "the figure fixture no longer links two figures"
    monkeypatch.chdir(tmp_path)
    outputs = publish.build(proposal, kind, tool)
    document = next(o for o in outputs if o.suffix in {".pdf", ".docx"})
    found = embedded_figures(document)
    if document.suffix == ".docx":
        assert found == linked, f"{tier} tier embedded {found} of {linked} figures"
    else:
        assert found >= linked, f"{tier} tier embedded {found} of {linked} figures"


MISSING_FIGURE = (
    "# A Title for the Thesis\n\n*Master's Thesis Proposal*\n\n"
    "## Introduction to the Topic\n\nText.\n\n"
    "![Figure 1: Overview](img/overview.png)\n\n## References\n"
)


def missing_figure_workspace(root: Path) -> Path:
    folder = root / "missing-figure"
    folder.mkdir()
    proposal = folder / "missing-figure.md"
    proposal.write_text(MISSING_FIGURE, encoding="utf-8")
    return proposal


@pytest.mark.slow
def test_missing_figure_warning_relayed_on_a_successful_docx_build(
        tmp_path, monkeypatch, capsys):
    if shutil.which("pandoc") is None:
        pytest.skip("pandoc not installed")
    proposal = missing_figure_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    outputs = publish.build(proposal, "docx", "pandoc")
    assert outputs[0].is_file(), "the build was expected to succeed"
    err = capsys.readouterr().err
    assert "[WARNING]" in err
    assert "img/overview.png" in err


@pytest.mark.slow
def test_missing_figure_fails_the_typst_build_naming_the_file(tmp_path, monkeypatch):
    if shutil.which("pandoc") is None or shutil.which("typst") is None:
        pytest.skip("pandoc or typst not installed")
    proposal = missing_figure_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as failure:
        publish.build(proposal, "typst", "typst")
    assert "overview.png" in str(failure.value.code)
