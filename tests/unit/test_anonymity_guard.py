"""L0: nothing shipped declares a proposal author (proposal-file-format spec).

Proposals are anonymous: the metadata contract has no `author` key, so no skill
prose, no publish template, and no fixture may declare one — with a single
deliberate exception, the fixture that exists to trip the check warning.

The guard is on a top-level `author:` line. `author:` indented inside a
`references:` entry is a cited work's author and stays untouched, as does the
`$if(author)$` block in the typst template, which is the documented escape hatch
for a program that requires a named title page.
"""

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TRIPWIRE = REPO / "tests" / "fixtures" / "f15-format-broken" / "broken-format.md"
TOP_LEVEL_AUTHOR = re.compile(r"^author:", re.MULTILINE)


def declares_author(path: Path) -> bool:
    return bool(TOP_LEVEL_AUTHOR.search(path.read_text(encoding="utf-8")))


def test_no_fixture_declares_an_author_except_the_tripwire():
    offenders = [
        str(md.relative_to(REPO))
        for md in sorted((REPO / "tests" / "fixtures").glob("*/*.md"))
        if md != TRIPWIRE and declares_author(md)
    ]
    assert not offenders, f"fixtures declaring a proposal author: {offenders}"


def test_tripwire_still_declares_an_author():
    """Removing it would leave the check warning without a fixture that trips it."""
    assert declares_author(TRIPWIRE)


def test_no_skill_file_declares_an_author():
    offenders = [
        str(p.relative_to(REPO))
        for p in sorted((REPO / "skills").rglob("*"))
        if p.is_file() and p.suffix in {".md", ".typ", ".tex", ".json"}
        and declares_author(p)
    ]
    assert not offenders, f"skill files declaring a proposal author: {offenders}"
