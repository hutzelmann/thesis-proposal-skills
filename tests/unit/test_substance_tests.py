"""L0: the substance-test set is named identically everywhere it is named
(testing-harness spec: substance-test names consistent across guidance, skills,
specs and pins).

The tests are prose guidance, and the skills cite them *by name* — the review
verdict is required to. That makes the set a contract between the guidance and
every judgment surface, and nothing checked that the contract held: "the five
substance tests" is written out across the guidance, four SKILL.md bodies, three
spec files and two verbatim pins, so adding a test to the guidance alone would
leave nine sites quietly describing a set that no longer exists.

This file exists to be in place *before* the set changes. Its whole value is the
loud failure at every stale site inside the same change; landing it afterwards
would make the first run green and prove nothing.

`shared/guidelines/guidelines.md` is the single source: the set is parsed from
its Substance Tests section rather than restated here, because a literal here
would be a second place the set is decided.

`README.md` is a site too: it names the set to every reader before any skill
does, and it called the swap test "anti-generic" while it sat outside this
guard (`2026-10-05-name-swap-test-in-readme`).

Generated `references/guidelines.md` copies are out of scope — they are
materialized by `scripts/sync_shared.py`, and its `--check` is what guards them.
So is `openspec/changes/`: a change folder describes a set that is being
proposed, not the one in force.

`openspec/specs/` is in scope only while no change is in flight. Main specs are
rewritten from a change's delta by `openspec archive`, not by hand, so between
implementing a change and archiving it they legitimately describe the previous
set. Failing the suite for that window would make the gate something to route
around; skipping it there costs nothing, because the same archive step that
updates the specs also un-skips this check.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from helpers import REPO

GUIDELINES = REPO / "shared" / "guidelines" / "guidelines.md"
SECTION_HEADING = "## Substance Tests"

# `- **Delta test** — the proposal states …`
_TEST_BULLET = re.compile(r"^-\s+\*\*([A-Za-z][A-Za-z-]*) test\*\*\s+—", re.MULTILINE)

NUMBER_WORDS = (
    "zero", "one", "two", "three", "four", "five",
    "six", "seven", "eight", "nine", "ten",
)


def _section(text: str, heading: str) -> str:
    """The body of one `## ` section, up to the next `## ` heading."""
    start = text.index(heading) + len(heading)
    rest = text[start:]
    end = rest.find("\n## ")
    return rest if end == -1 else rest[:end]


def _canonical() -> list[str]:
    body = _section(GUIDELINES.read_text(encoding="utf-8"), SECTION_HEADING)
    return [m.group(1).lower() for m in _TEST_BULLET.finditer(body)]


CANONICAL = _canonical()
CANONICAL_SET = frozenset(CANONICAL)
CANONICAL_COUNT_WORD = NUMBER_WORDS[len(CANONICAL)] if len(CANONICAL) < len(NUMBER_WORDS) else ""

_NAME = "|".join(sorted(map(re.escape, CANONICAL_SET), key=len, reverse=True))
# A comma-joined run of three or more bare words, with an optional `and`/`or`
# before the last. Three is the shortest run that reads as an enumeration rather
# than as two tests mentioned in one sentence.
#
# The run is deliberately *not* built from the canonical names: a run of names
# would stop matching the moment one name was replaced by something else, which
# is precisely the drift this file exists to catch. Matching bare words and then
# asking how many canonical names the run holds catches substitution, omission
# and addition alike. `MIN_NAMES_IN_RUN` is what separates an enumeration of the
# tests from any other comma list in the prose.
_WORD = r"[a-z][a-z-]{2,}"
_RUN = re.compile(
    rf"\b{_WORD}(?:\s*,\s*(?:and\s+|or\s+)?(?:the\s+)?{_WORD}){{2,}}", re.IGNORECASE
)
MIN_NAMES_IN_RUN = 2
# `the five substance tests`, `name five substance tests` — a claim about how
# big the set is. A number introduced by `at least` or `only` is an evidence bar
# ("at least three substance tests fail decisively") and says nothing about the
# set, so it is excluded the same way a partial enumeration is. In "at least
# three of the five substance tests" the match starts at `five`, which is the
# set claim; `three` is the bar and is left alone.
#
# The second branch reads `Five tests define the substance bar` — the source's
# own count sentence, which puts the qualifier after the verb and was invisible
# to the first branch while it said "Five" over a list of six. It is keyed on
# the clause going on to name the substance bar, not on the verb, so a reworded
# verb is still caught; and it is not a bare `<N> tests`, which would flag
# "Naming those three tests is a statement about this fixture" in the
# testing-harness spec — a sentence written to say it is *not* a count.
_COUNT = re.compile(
    r"(?<!at least )(?<!only )\b(\w+)\s+"
    r"(?:(?:substance|named)\s+tests\b|tests\b(?=[^.;:]{0,40}\bsubstance\b))",
    re.IGNORECASE,
)
# A run introduced by `at least` is a deliberate subset — a verdict citing the
# three tests that actually failed, not a claim about the whole set.
_PARTIAL = re.compile(r"at least\b[^.;]*$", re.IGNORECASE)


def _change_in_flight() -> bool:
    """Any unarchived OpenSpec change folder — see the module docstring."""
    changes = REPO / "openspec" / "changes"
    return any(d.is_dir() and d.name != "archive" for d in changes.iterdir()) \
        if changes.is_dir() else False


def _sites() -> list[Path]:
    sites = [
        GUIDELINES,
        REPO / "README.md",
        *(REPO / "skills").glob("proposal-*/SKILL.md"),
        *(REPO / "tests" / "unit" / "data" / "pinned_sentences").glob("*.txt"),
    ]
    if not _change_in_flight():
        sites += (REPO / "openspec" / "specs").glob("*/spec.md")
    return sorted(sites)


SITES = _sites()
SOURCE = GUIDELINES.relative_to(REPO).as_posix()
ids = lambda paths: [p.relative_to(REPO).as_posix() for p in paths]  # noqa: E731


def test_the_set_parses_and_the_site_list_is_not_empty():
    """Every assertion below is vacuous if either of these is empty."""
    assert len(CANONICAL) >= 2, (
        f"parsed {CANONICAL} from {SECTION_HEADING} in {SOURCE} — the bullets are expected "
        "to read `- **Name test** — …`, and a formatting change that breaks that pattern "
        "would silently empty this suite"
    )
    assert len(CANONICAL) == len(CANONICAL_SET), f"duplicate test name in {CANONICAL}"
    assert CANONICAL_COUNT_WORD, f"no number word for {len(CANONICAL)} tests"
    assert len(SITES) > 10, f"only {len(SITES)} files scanned"


@pytest.mark.parametrize("site", SITES, ids=ids(SITES))
def test_enumerations_name_the_whole_set(site):
    text = site.read_text(encoding="utf-8")
    for match in _RUN.finditer(text):
        run = match.group(0)
        before = text[max(0, match.start() - 200):match.start()]
        if _PARTIAL.search(before):
            continue
        named = {n.lower() for n in re.findall(rf"\b(?:{_NAME})\b", run, re.IGNORECASE)}
        if len(named) < MIN_NAMES_IN_RUN:
            continue
        assert named == CANONICAL_SET, (
            f"{site.relative_to(REPO).as_posix()} enumerates the substance tests as "
            f"{sorted(named)}, but {SOURCE} names {sorted(CANONICAL_SET)}. The guidance is "
            "the source: update this site, or mark the run as a deliberate subset with "
            "`at least`.\n"
            f"  {run}"
        )


@pytest.mark.parametrize(
    ("phrase", "count"),
    [
        ("judge the six substance tests and every dimension", "six"),
        ("Substance, by the six named tests", "six"),
        ("Five tests define the substance bar; agents judging", "five"),
        ("Six tests set the substance bar", "six"),
        ("at least three of the six substance tests fail decisively", "six"),
        ("at least three substance tests fail decisively", None),
        ("only two substance tests fail decisively", None),
        ("Naming those three tests is a statement about this fixture, "
         "not about how many tests exist.", None),
        ("Three tests ran. The substance bar is unchanged.", None),
    ],
)
def test_count_pattern_reads_set_claims_only(phrase, count):
    """The pattern's reach, pinned on literal phrasings: a set claim is read
    whichever side of `tests` the qualifier sits, an evidence bar or a plain
    mention of some tests is not."""
    found = [m.group(1).lower() for m in _COUNT.finditer(phrase)
             if m.group(1).lower() in NUMBER_WORDS]
    assert found == ([count] if count else [])


@pytest.mark.parametrize("site", SITES, ids=ids(SITES))
def test_counts_agree_with_the_set(site):
    text = site.read_text(encoding="utf-8")
    for match in _COUNT.finditer(text):
        word = match.group(1).lower()
        if word not in NUMBER_WORDS:
            continue
        assert word == CANONICAL_COUNT_WORD, (
            f"{site.relative_to(REPO).as_posix()} says \"{match.group(0)}\", but {SOURCE} "
            f"names {len(CANONICAL)} ({CANONICAL_COUNT_WORD}): {sorted(CANONICAL_SET)}"
        )
