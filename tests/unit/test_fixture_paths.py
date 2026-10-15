"""L0: fixture files are found through one helper, in the folder layout
(testing-harness: Corpus walkers cover every proposal fixture).

The corpus lives in proposal folders, `<fixture>/<slug>/<slug>.md`
(adopt-proposal-folders, design D10). A test that spells
`FIXTURES / "<id>" / "<file>.md"` breaks on a layout change one call site at a
time, and a corpus walker whose glob stops matching passes vacuously. So every
fixture path goes through `harness/fixture_paths.py`, a guard refuses a spelled
one, every walker is held to the number of oracles, and the corpus itself is
held to its shape.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path

import check as check_script
import pytest
from fixture_paths import (
    corpus_proposals,
    fixture_file,
    fixture_of,
    fixture_proposal,
    fixture_proposals,
    staged_tree,
)
from helpers import CLEAN_DRAFT, FIXTURES, REPO, run_check, write_proposal

BLOCK = "# T\n\nBody.\n\n---\nreferences: []\n---\n"
ORACLE = "{}\n"


def put(root: Path, rel: str, text: str = BLOCK) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


# ---------- the helper, on synthetic corpora ---------------------------------


def test_a_folder_fixture_resolves_its_proposal_and_companions(tmp_path):
    put(tmp_path, "f01/expected.json", ORACLE)
    proposal = put(tmp_path, "f01/agents/agents.md")
    review = put(tmp_path, "f01/agents/review.md", "Verdict: revise.\n")
    notes = put(tmp_path, "f01/agents/notes.md", "# Notes\n")
    feedback = put(tmp_path, "f01/agents/feedback.md", "Dear student\n")
    put(tmp_path, "f01/guidelines.md", "# Rules\n")
    assert fixture_proposal("f01", tmp_path) == proposal
    assert fixture_file("f01", "proposal", tmp_path) == proposal
    assert fixture_file("f01", "review", tmp_path) == review
    assert fixture_file("f01", "notes", tmp_path) == notes
    assert fixture_file("f01", "feedback", tmp_path) == feedback


def test_the_flat_layout_is_no_longer_read(tmp_path):
    """A proposal beside the fixture's root files, and companions under the
    flat layout's names, are nobody's (design D1: no reading of old names)."""
    put(tmp_path, "f01/expected.json", ORACLE)
    put(tmp_path, "f01/agents.md")
    put(tmp_path, "f01/agents-review.md", "Verdict: revise.\n")
    put(tmp_path, "f01/agents.notes.md", "# Notes\n")
    put(tmp_path, "w06/soil.harvest.md", "# Harvest record\n")
    put(tmp_path, "w07/proposals/agents.md")
    assert fixture_proposals(tmp_path / "f01") == []
    assert fixture_proposals(tmp_path / "w07") == []
    for fixture, role in (("f01", "review"), ("f01", "notes"), ("w06", "harvest")):
        with pytest.raises(LookupError, match=fixture):
            fixture_file(fixture, role, tmp_path)


def test_a_configured_location_is_read(tmp_path):
    folder = put(tmp_path, "w07/proposals/agents/agents.md")
    review = put(tmp_path, "w07/proposals/agents/review.md", "Verdict: revise.\n")
    assert fixture_proposal("w07", tmp_path) == folder
    assert fixture_file("w07", "review", tmp_path) == review


def test_a_nested_file_counts_only_in_the_folder_named_by_its_stem(tmp_path):
    """`meetings/agenda.md` ends in a metadata block and still is no proposal."""
    put(tmp_path, "f01/meetings/agenda.md")
    assert fixture_proposals(tmp_path / "f01") == []


def test_a_flat_proposal_beside_a_folder_is_not_the_fixtures(tmp_path):
    """The orphan workspace keeps a flat proposal at its root on purpose; its
    own proposal is the one in a folder."""
    folder = put(tmp_path, "w13/agents/agents.md")
    put(tmp_path, "w13/stray.md")
    assert fixture_proposals(tmp_path / "w13") == [folder]


def test_the_staged_tree_is_the_fixture_but_its_oracle_and_its_submission(tmp_path):
    """What a runner stages: the fixture is the workspace root, so every file
    lies where it lies, hidden ones included; the oracle and the import
    source at the root stay behind (design D24)."""
    put(tmp_path, "f16/expected.json", ORACLE)
    put(tmp_path, "f16/submission.pdf", "%PDF")
    proposal = put(tmp_path, "f16/topic/topic.md")
    figure = put(tmp_path, "f16/topic/img/a.png", "png")
    hidden = put(tmp_path, "f16/.agents/skills/record.json", "{}")
    kept = put(tmp_path, "f16/topic/submission.pdf", "%PDF")
    assert staged_tree("f16", tmp_path) == {
        ".agents/skills/record.json": hidden, "topic/img/a.png": figure,
        "topic/submission.pdf": kept, "topic/topic.md": proposal}


def test_a_fixture_without_a_proposal_resolves_its_harvest_record(tmp_path):
    folder = put(tmp_path, "w06/soil/harvest.md", "# Harvest record\n")
    assert fixture_file("w06", "harvest", tmp_path) == folder


def test_a_missing_or_second_proposal_is_an_error(tmp_path):
    put(tmp_path, "f01/expected.json", ORACLE)
    with pytest.raises(LookupError, match="f01"):
        fixture_proposal("f01", tmp_path)
    put(tmp_path, "f01/a/a.md")
    put(tmp_path, "f01/b/b.md")
    with pytest.raises(LookupError, match="f01"):
        fixture_proposal("f01", tmp_path)


def test_the_corpus_walker_yields_each_oracle_bearing_fixtures_proposal(tmp_path):
    put(tmp_path, "f01/expected.json", ORACLE)
    first = put(tmp_path, "f01/agents/agents.md")
    put(tmp_path, "f01/agents/review.md", "Verdict: revise.\n")
    put(tmp_path, "f02/expected.json", ORACLE)
    configured = put(tmp_path, "f02/proposals/drift/drift.md")
    put(tmp_path, "f02/proposals/drift/notes.md", "# Notes\n")
    put(tmp_path, "w15/idea/notes.md", "# Notes\n")  # no oracle, no proposal
    assert corpus_proposals(tmp_path) == [first, configured]
    assert [fixture_of(p, tmp_path) for p in (first, configured)] == ["f01", "f02"]


# ---------- the test helpers --------------------------------------------------

GUIDELINES = "```toml\n[references]\nmin_count = {n}\n```\n"


def test_write_proposal_puts_the_proposal_in_its_folder(tmp_path):
    path = write_proposal(tmp_path, "agents", BLOCK)
    assert path == tmp_path / "agents" / "agents.md"
    assert path.read_text(encoding="utf-8") == BLOCK


def test_run_check_runs_from_the_folder_above_the_proposals(tmp_path):
    """A user's agent runs the check from the workspace root; the root's
    guidelines.md governs a proposal in its folder only from there."""
    proposal = write_proposal(tmp_path, "ml-code-review", CLEAN_DRAFT)
    (tmp_path / "guidelines.md").write_text(GUIDELINES.format(n=99), encoding="utf-8")
    before = Path.cwd()
    assert "at least 99 required" in run_check(proposal).stdout
    assert Path.cwd() == before


def test_run_check_runs_from_an_explicit_root(tmp_path):
    proposal = write_proposal(tmp_path / "proposals", "ml-code-review", CLEAN_DRAFT)
    (tmp_path / "guidelines.md").write_text(GUIDELINES.format(n=98), encoding="utf-8")
    assert "at least 98 required" in run_check(proposal, root=tmp_path).stdout


# ---------- the real corpus ---------------------------------------------------

ORACLES = sorted(FIXTURES.glob("*/expected.json"))


def test_every_oracle_bearing_fixture_yields_exactly_one_proposal():
    proposals = corpus_proposals()
    assert len(proposals) == len(ORACLES)
    assert sorted(fixture_of(p) for p in proposals) == [o.parent.name for o in ORACLES]


# ---------- the corpus shape (design D10 of adopt-proposal-folders) -----------

# the proposal fixtures: f* carry a proposal, w* a workspace around one; the
# other prefixes are sources (p, s) and served pages (g)
SHAPED = sorted(d for d in FIXTURES.iterdir() if d.is_dir() and d.name[0] in "fw")
LOCATION = "proposals"
# the one proposal kept outside a folder on purpose: w13's flat proposal at its
# root, which the check reports as an orphan
ROOT_PROPOSALS = {"w13-orphaned-companions": ["build-log-triage.md"]}
# the import sources a fixture keeps at its root, outside every proposal folder
SUBMISSIONS = ("f03-compliance-audit", "f09-llm-compliance-docs",
               "f11-migration-architecture", "f16-figures-import")
# the flat layout's names, which no corpus file carries any more
RETIRED_NAME = re.compile(
    r"\.notes\.md$|-review\.md$|-feedback\.md$|\.harvest\.md$|-handout\.md$")


def corpus_files(fixture: Path) -> list[Path]:
    """A fixture's files, hidden ones left out."""
    return sorted(p for p in fixture.rglob("*") if p.is_file()
                  and not any(part.startswith(".") for part in p.relative_to(fixture).parts))


def ends_in_block(path: Path) -> bool:
    return check_script.split_proposal(path.read_text(encoding="utf-8"))[1].found


def proposal_folders(fixture: Path) -> list[str]:
    """The folders of a fixture's root and its `proposals/` location that the
    check classifies as proposal folders."""
    found = []
    for location in (fixture, fixture / LOCATION):
        for folder in sorted(p for p in location.glob("*/") if p.is_dir()):
            files = [p.name for p in folder.iterdir()]
            def read(name: str, folder: Path = folder) -> str:
                return (folder / name).read_text(encoding="utf-8")
            if check_script.proposal_folder(folder.name, files, read):
                found.append(folder.relative_to(fixture).as_posix())
    return found


@pytest.mark.parametrize("oracle", ORACLES, ids=lambda p: p.parent.name)
def test_every_proposal_sits_in_a_folder_named_by_its_stem(oracle):
    proposal = fixture_proposal(oracle.parent.name)
    rel = proposal.relative_to(oracle.parent).parts
    assert rel in ((proposal.stem, proposal.name), (LOCATION, proposal.stem, proposal.name)), (
        f"{oracle.parent.name}: {'/'.join(rel)} is not <slug>/<slug>.md")


@pytest.mark.parametrize("fixture", SHAPED, ids=lambda p: p.name)
def test_no_fixture_holds_a_proposal_outside_a_folder(fixture):
    """Markdown ending in a metadata block at a fixture's root or in its
    `proposals/` location is a flat proposal; only w13 keeps one, for the
    check to report."""
    flat = [p.relative_to(fixture).as_posix()
            for location in (fixture, fixture / LOCATION)
            for p in sorted(location.glob("*.md")) if ends_in_block(p)]
    assert flat == ROOT_PROPOSALS.get(fixture.name, [])


@pytest.mark.parametrize("fixture", SHAPED, ids=lambda p: p.name)
def test_every_proposal_fixture_holds_a_proposal_folder(fixture):
    """By the check's own test: a proposal named after its folder, a notes
    file with the five headings (w15) or a harvest record (w06)."""
    assert proposal_folders(fixture), f"{fixture.name}: no proposal folder"


@pytest.mark.parametrize("fixture", SHAPED, ids=lambda p: p.name)
def test_no_corpus_file_carries_a_flat_layout_name(fixture):
    """Companions are role-named inside the folder, figures carry no slug, and
    a proposal slugged `…-review` (f00) is still its folder's own."""
    stale = []
    for path in corpus_files(fixture):
        rel = path.relative_to(fixture)
        own = path.parent.name == path.stem
        figure = path.parent.name == check_script.FIGURE_FOLDER and len(rel.parts) > 2
        if ((RETIRED_NAME.search(path.name) and not own) or path.name == "ideation.notes.md"
                or rel.parts[0] == check_script.FIGURE_FOLDER
                or (figure and path.name.startswith(rel.parts[-3] + "-"))):
            stale.append(rel.as_posix())
    assert not stale, f"{fixture.name}: flat-layout names {stale}"


@pytest.mark.parametrize("fixture", SHAPED, ids=lambda p: p.name)
def test_import_sources_stay_outside_the_proposal_folders(fixture):
    """A source PDF inside a folder under `<slug>.pdf` would read as a current
    build and satisfy a publish verdict with no build at all."""
    built = [p.relative_to(fixture).as_posix() for folder in proposal_folders(fixture)
             for p in sorted((fixture / folder).rglob("*"))
             if p.suffix in (".pdf", ".docx", ".typ", ".tex")]
    assert built == []
    root_pdfs = sorted(p.name for p in fixture.glob("*.pdf"))
    assert root_pdfs == (["submission.pdf"] if fixture.name in SUBMISSIONS else [])


def test_the_ci_typst_build_walks_the_same_corpus():
    """The CI image has no Python, so the script walks the corpus itself; its
    list mode must name exactly what the shared walker yields."""
    script = REPO / "scripts" / "ci_typst_build.sh"
    assert "--list" in script.read_text(encoding="utf-8"), "the CI build script has no list mode"
    shell = shutil.which("sh")
    if shell is None:
        pytest.skip("no POSIX shell")
    listed = subprocess.run([shell, str(script), "--list"], cwd=REPO, capture_output=True,
                            encoding="utf-8", check=True).stdout.split()
    assert sorted(listed) == sorted(p.relative_to(REPO).as_posix() for p in corpus_proposals())
    assert len(listed) == len(ORACLES)


# ---------- the guards ----------------------------------------------------------

# A fixture file's path joined at a call site: FIXTURES / <id> / <file> (also
# across a line break), the same through REPO / "tests" / "fixtures", a
# "<id>/<file>" literal, or a markdown name joined to fixture_dir().
SPELLED = re.compile(
    r"""\bFIXTURES\s*/\s*[^\s/()]+\s*/"""
    r"""|["']fixtures["']\s*/\s*[^\s/()]+\s*/"""
    r"""|["'][a-z]\d\d-[a-z0-9-]+/[^"'\s]*["']"""
    r"""|\bfixture_dir\([^)]*\)\s*/\s*["'][^"']*\.md["']"""
)
# a corpus walk of its own: a markdown glob straight over the fixture root
CORPUS_GLOB = re.compile(r"""(?:\bFIXTURES|["']fixtures["']\))\.r?glob\(\s*["'][^"']*\.md["']""")
EXEMPT = {"harness/fixture_paths.py", "tests/unit/test_fixture_paths.py"}


def offending_lines(pattern: re.Pattern[str]) -> list[str]:
    hits = []
    for top in ("tests", "harness"):
        for path in sorted((REPO / top).rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            if rel in EXEMPT or rel.startswith("tests/fixtures/"):
                continue
            text = path.read_text(encoding="utf-8")
            hits += [f"{rel}:{text.count(chr(10), 0, match.start()) + 1}: {match.group(0)!r}"
                     for match in pattern.finditer(text)]
    return hits


def test_no_module_spells_a_fixture_files_path():
    hits = offending_lines(SPELLED)
    assert not hits, ("resolve fixture files through harness/fixture_paths.py:\n"
                      + "\n".join(hits))


def test_no_module_walks_the_corpus_itself():
    hits = offending_lines(CORPUS_GLOB)
    assert not hits, ("walk the corpus through fixture_paths.corpus_proposals():\n"
                      + "\n".join(hits))


@pytest.mark.parametrize("line", [
    'run_check(FIXTURES / "f00-clean-en" / "ml-code-review.md")',
    'FIXTURES / "f25-case-study" /\n    "release-readiness-signals.md"',
    '(FIXTURES / "w09-revised-round"\n           / "x-review.md")',
    'FIXTURES / scenario["fixture"] / "expected.json"',
    'REPO / "tests" / "fixtures" / "f15-format-broken" / "broken-format.md"',
    '("f12-clean-de/typsystem-einheitenfehler.md", "Vogel")',
    'fixture_dir("f00-clean-en") / "ml-code-review.md"',
])
def test_the_guard_catches_every_spelling(line):
    assert SPELLED.search(line)


@pytest.mark.parametrize("line", [
    "fixture = FIXTURES / scenario[\"fixture\"]\n    for f in fixture.iterdir():",
    "(FIXTURES / fixture).iterdir()",
    'fixture_dir("p01-published-paper") / "quieter-pagers.txt"',
    "FIXTURES.glob(\"*/expected.json\")",
])
def test_the_guard_lets_a_fixture_root_pass(line):
    assert not SPELLED.search(line)
    assert not CORPUS_GLOB.search(line)
