"""L0: every fixture proposal must build on every resolvable output tier.

The bug this guards against shipped because no test had ever produced a
document: test_publish.py exercises engine *selection* against a fake `which`,
never build() itself. Selection logic is not coverage of a build path.

These drive publish.build() directly rather than reassembling the pandoc
invocation, so a defect in how the shipped code builds that command is caught
instead of reproduced. Each tier skips when its toolchain is absent; CI supplies
the toolchain in container jobs so they run there.
"""

import shutil
import subprocess
import zipfile
from pathlib import Path

import publish
import pytest

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "tests" / "fixtures"

# a fixture's proposal is its markdown file; guidelines.md is a workspace
# override that w02 ships alongside one, and README.md documents the corpus
NOT_PROPOSALS = {"README.md", "guidelines.md"}
# a harvest record is what the reverse skill reads out of a finished thesis, so
# it stands where the thesis would: an input to a skill, never a document to build.
# w07 keeps its proposal one level down, in the subdirectory its workspace
# guidelines.md configures — the corpus covers both layouts.
PROPOSALS = sorted(
    p for p in list(FIXTURES.glob("*/*.md")) + list(FIXTURES.glob("*/proposals/*.md"))
    if p.name not in NOT_PROPOSALS and not p.name.endswith(".harvest.md")
)


def latex_engine():
    return next((e for e in publish.LATEX_ENGINES if shutil.which(e)), None)


TIERS = {
    "typst": lambda: ("typst", "typst") if shutil.which("typst") else None,
    "latex": lambda: ("latex", latex_engine()) if latex_engine() else None,
    "docx": lambda: ("docx", "pandoc"),
}


def staged(proposal: Path, tmp_path: Path) -> Path:
    """Copy the fixture's whole directory, so relatively referenced assets
    resolve — f16-figures-import carries an img/ directory its body links to."""
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
@pytest.mark.parametrize("proposal", PROPOSALS,
                         ids=lambda p: p.relative_to(FIXTURES).parts[0])
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
    fixtures = {p.relative_to(FIXTURES).parts[0] for p in PROPOSALS}
    expected = {p.parent.name for p in FIXTURES.glob("*/expected.json")}
    assert fixtures == expected, (
        f"fixture proposals and oracles disagree: {fixtures ^ expected}"
    )


# -- content the build-succeeds check cannot see ---------------------------

CONTENT_FIXTURE = FIXTURES / "f19-drift-alert-validity" / "drift-alert-validity.md"


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
