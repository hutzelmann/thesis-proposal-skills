"""Where a fixture's files lie: the one place that knows the corpus layout.

Every test and harness module resolves a fixture file through here and never
spells its path, and every corpus walker is this module's `corpus_proposals()`
(testing-harness: Corpus walkers cover every proposal fixture). An L0 guard in
`tests/unit/test_fixture_paths.py` holds both, and holds the corpus to its
shape, so a layout change touches the fixtures and this module, not a hundred
call sites.

A fixture is a workspace root (adopt-proposal-folders, design D10): its
proposal lies in a folder of its own, `<fixture>/<slug>/<slug>.md`, or
`<fixture>/proposals/<slug>/<slug>.md` where the fixture's workspace configures
`[paths] proposals`, with role-named companions in the same folder
(`notes.md`, `review.md`, ...). A nested markdown file counts only in the
folder named by its stem, so a flat proposal kept at a fixture's root on
purpose (w13) is never taken for the fixture's own, and the flat layout's
names are not read at all. `expected.json` and the import sources lie at the
fixture's root, outside every proposal folder.

Kept free of eval-framework imports so the dev runner, the routing rig and the
L0 tests can all use it.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURES = REPO / "tests" / "fixtures"
ORACLE = "expected.json"
# the import source a fixture keeps at its root, outside every proposal folder
SUBMISSION = "submission.pdf"
# what a fixture's root holds that a runner never stages as part of its tree:
# the oracle, and the import source, which a scenario stages only by name
UNSTAGED = frozenset({ORACLE, SUBMISSION})
# the location a fixture's workspace may configure with `[paths] proposals`
LOCATION = "proposals"
# a companion's file name by role, inside the proposal's folder
ROLE_FILES = {
    "notes": "notes.md",
    "review": "review.md",
    "feedback": "feedback.md",
    "harvest": "harvest.md",
}


def fixture_dir(fixture: str, fixtures: Path = FIXTURES) -> Path:
    """A fixture's root, which is the workspace root its files are staged
    under: `expected.json` and the sources an import reads lie here."""
    return fixtures / fixture


def oracle_path(fixture: str, fixtures: Path = FIXTURES) -> Path:
    return fixture_dir(fixture, fixtures) / ORACLE


def fixture_of(path: Path, fixtures: Path = FIXTURES) -> str:
    """The fixture a corpus file belongs to."""
    return path.relative_to(fixtures).parts[0]


def _locations(directory: Path) -> list[Path]:
    """The directories a fixture keeps its proposal folders in: its root and,
    where its workspace configures one, the proposal location."""
    return [d for d in (directory, directory / LOCATION) if d.is_dir()]


def fixture_proposals(directory: Path) -> list[Path]:
    """Every proposal a fixture directory holds: each `<slug>/<slug>.md` in
    one of its locations."""
    return [folder / f"{folder.name}.md" for location in _locations(directory)
            for folder in sorted(location.iterdir())
            if (folder / f"{folder.name}.md").is_file()]


def _only(fixture: str, what: str, found: list[Path]) -> Path:
    if len(found) != 1:
        names = [p.name for p in found]
        raise LookupError(f"{fixture}: expected one {what}, found {len(found)} {names}")
    return found[0]


def fixture_proposal(fixture: str, fixtures: Path = FIXTURES) -> Path:
    """The fixture's one proposal."""
    return _only(fixture, "proposal", fixture_proposals(fixture_dir(fixture, fixtures)))


def fixture_file(fixture: str, role: str, fixtures: Path = FIXTURES) -> Path:
    """The fixture's proposal (`role="proposal"`) or its one companion of a
    role in ROLE_FILES, `<slug>/<role>.md`; a fixture without a proposal (w06's
    harvest record) resolves its companion all the same."""
    if role == "proposal":
        return fixture_proposal(fixture, fixtures)
    found = [p for location in _locations(fixture_dir(fixture, fixtures))
             for p in sorted(location.glob(f"*/{ROLE_FILES[role]}"))]
    return _only(fixture, role, found)


def staged_tree(fixture: str, fixtures: Path = FIXTURES) -> dict[str, Path]:
    """What a runner stages from a fixture, by workspace-relative path: the
    fixture is the workspace root, so its whole tree, hidden files included,
    but for UNSTAGED at its root (design D24 of adopt-proposal-folders)."""
    directory = fixture_dir(fixture, fixtures)
    return {rel: path for path in sorted(directory.rglob("*")) if path.is_file()
            and (rel := path.relative_to(directory).as_posix()) not in UNSTAGED}


def corpus_proposals(fixtures: Path = FIXTURES) -> list[Path]:
    """Every proposal of every fixture that carries an oracle, in fixture
    order: the one corpus walker the tests, the export matrix and the guards
    share."""
    return [proposal for oracle in sorted(fixtures.glob(f"*/{ORACLE}"))
            for proposal in fixture_proposals(oracle.parent)]
