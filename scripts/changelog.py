#!/usr/bin/env python3
"""Parse and check CHANGELOG.md, the suite's user-facing release history.

The format is Keep a Changelog 1.1.0 with this repository's additions
(release-history spec): `## [Unreleased]` first, then `## [X.Y.Z] - YYYY-MM-DD`
releases newest first, an optional closing `## Before the skills: …` era that
carries no version, fixed categories in a fixed order, `**Breaking:**` entries,
and links into `openspec/changes/archive/<date>-<id>/`. Retroactive releases
(history before the first stamp) carry a marker line naming the commit their
tag points at; stamped releases carry none.

`check` is the L0 gate (tests/unit/test_changelog.py runs it in-process):
heading shape and order, categories, duplicate entries (the `merge=union`
backstop), archive links, compare links, stamp agreement with pyproject and
the skills, coverage of every change archived since CUTOFF, and local tags
against the commits their sections name. A missing tag is skipped — CI
checkouts fetch no tags.

`notes X.Y.Z` prints one release's body, for `gh release create --notes-file`.

Usage:
    python3 scripts/changelog.py check
    python3 scripts/changelog.py notes 0.8.0
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from itertools import pairwise
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/hutzelmann/thesis-proposal-skills"
# Every change archived on or after this date must be linked or declared
# internal; the history before it was curated by hand (add-changelog).
CUTOFF = "2026-10-14"
LEGACY_TAG = "legacy-latex-template"
CATEGORIES = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security",
              "For contributors")
UNRELEASED = "Unreleased"

RELEASE_RE = re.compile(r"^## \[(\d+)\.(\d+)\.(\d+)\] - (\d{4}-\d{2}-\d{2})$")
LEGACY_RE = re.compile(r"^## Before the skills: ")
RETRO_RE = re.compile(r"^_Retroactive release, tagged at ([0-9a-f]{7,40}) on \d{4}-\d{2}-\d{2}\.")
ARCHIVE_LINK_RE = re.compile(r"\]\(openspec/changes/archive/([^/)]+)/\)")
LINK_DEF_RE = re.compile(r"^\[([^\]]+)\]: (\S+)$")
INTERNAL_RE = re.compile(r"^Changelog: internal\s*$", re.MULTILINE)
STAMP_RE = re.compile(r"^metadata:\n  version: (\S+)$", re.MULTILINE)

Version = tuple[int, int, int]


@dataclass
class Release:
    """One `## ` section. `version` is None for Unreleased and the legacy era."""

    title: str
    line: int
    version: Version | None = None
    date: str | None = None
    legacy: bool = False
    commit: str | None = None  # retroactive marker's commit; None when stamped
    categories: list[str] = field(default_factory=list)
    entries: list[str] = field(default_factory=list)
    by_category: dict[str, list[str]] = field(default_factory=dict)
    body: list[str] = field(default_factory=list)

    @property
    def retroactive(self) -> bool:
        return self.commit is not None


@dataclass
class Changelog:
    releases: list[Release]
    links: dict[str, str]
    archive_links: set[str]
    malformed: list[tuple[int, str]]

    def numbered(self) -> list[Release]:
        return [r for r in self.releases if r.version is not None]


@dataclass(frozen=True)
class Problem:
    where: str
    message: str

    def __str__(self) -> str:
        return f"{self.where}: {self.message}"


def vstr(version: Version) -> str:
    return ".".join(map(str, version))


def _start_section(line: str, number: int) -> Release | None:
    if line == f"## [{UNRELEASED}]":
        return Release(UNRELEASED, number)
    if m := RELEASE_RE.match(line):
        version = (int(m[1]), int(m[2]), int(m[3]))
        return Release(vstr(version), number, version=version, date=m[4])
    if LEGACY_RE.match(line):
        return Release(line[3:], number, legacy=True)
    return None


def _add_line(release: Release, line: str) -> None:
    release.body.append(line)
    if line.startswith("### "):
        release.categories.append(line[4:].strip())
        release.by_category.setdefault(release.categories[-1], [])
    elif line.startswith("- "):
        release.entries.append(line)
        if release.categories:
            release.by_category[release.categories[-1]].append(line)
    elif (m := RETRO_RE.match(line)) and release.commit is None:
        release.commit = m[1]


def parse(text: str) -> Changelog:
    """Split the file into sections; header lines before the first `## ` are skipped."""
    releases: list[Release] = []
    links: dict[str, str] = {}
    malformed: list[tuple[int, str]] = []
    for number, line in enumerate(text.splitlines(), start=1):
        if line.startswith("## "):
            section = _start_section(line, number)
            if section is None:
                malformed.append((number, line))
            else:
                releases.append(section)
        elif m := LINK_DEF_RE.match(line):
            links[m[1]] = m[2]
        elif releases:
            _add_line(releases[-1], line)
    return Changelog(releases, links, set(ARCHIVE_LINK_RE.findall(text)), malformed)


def check_structure(cl: Changelog) -> list[Problem]:
    problems = [Problem(f"line {n}", f"malformed release heading {text!r}")
                for n, text in cl.malformed]
    titles = [r.title for r in cl.releases]
    if not titles or titles[0] != UNRELEASED:
        problems.append(Problem("CHANGELOG.md", "the first section must be ## [Unreleased]"))
    if titles.count(UNRELEASED) > 1:
        problems.append(Problem("CHANGELOG.md", "## [Unreleased] appears more than once"))
    legacy = [i for i, r in enumerate(cl.releases) if r.legacy]
    if legacy and legacy != [len(cl.releases) - 1]:
        problems.append(Problem("CHANGELOG.md", "the legacy era must be the single last section"))
    numbered = cl.numbered()
    for newer, older in pairwise(numbered):
        if not newer.version > older.version:  # type: ignore[operator]
            problems.append(Problem(f"line {older.line}",
                                    f"{older.title} is not older than {newer.title} above it"))
        elif newer.date < older.date:  # type: ignore[operator]
            problems.append(Problem(f"line {older.line}",
                                    f"{older.title} is dated after {newer.title}"))
    return problems


def check_sections(cl: Changelog) -> list[Problem]:
    """Categories known and in order; no entry twice within one release."""
    problems: list[Problem] = []
    for release in cl.releases:
        if release.legacy:
            continue
        where = f"[{release.title}]"
        unknown = [c for c in release.categories if c not in CATEGORIES]
        problems += [Problem(where, f"unknown category {c!r}") for c in unknown]
        ranks = [CATEGORIES.index(c) for c in release.categories if c in CATEGORIES]
        if ranks != sorted(set(ranks)):
            problems.append(Problem(where, "categories repeat or are out of order "
                                           f"(order: {', '.join(CATEGORIES)})"))
        seen: set[str] = set()
        for entry in release.entries:
            if entry in seen:
                problems.append(Problem(where, f"entry repeated: {entry[:80]}"))
            seen.add(entry)
    return problems


def expected_links(cl: Changelog) -> dict[str, str]:
    """Compare link per section: each version against the one below it."""
    numbered = cl.numbered()
    tags = [f"v{r.title}" for r in numbered]
    expected: dict[str, str] = {}
    if any(r.title == UNRELEASED for r in cl.releases) and tags:
        expected[UNRELEASED] = f"{REPO_URL}/compare/{tags[0]}...HEAD"
    for i, release in enumerate(numbered):
        base = tags[i + 1] if i + 1 < len(tags) else LEGACY_TAG
        expected[release.title] = f"{REPO_URL}/compare/{base}...{tags[i]}"
    return expected


def check_links(cl: Changelog, root: Path) -> list[Problem]:
    problems = [Problem(f"[{title}]", f"compare link should be {url}")
                for title, url in expected_links(cl).items() if cl.links.get(title) != url]
    archive = root / "openspec" / "changes" / "archive"
    problems += [Problem("CHANGELOG.md", f"archive link does not resolve: {name}/")
                 for name in sorted(cl.archive_links) if not (archive / name).is_dir()]
    return problems


def skill_stamps(root: Path) -> dict[str, str | None]:
    stamps: dict[str, str | None] = {}
    for skill_md in sorted(root.glob("skills/proposal-*/SKILL.md")):
        m = STAMP_RE.search(skill_md.read_text(encoding="utf-8"))
        stamps[skill_md.parent.name] = m[1] if m else None
    return stamps


def project_version(root: Path) -> str:
    data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def check_stamp(cl: Changelog, stamps: dict[str, str | None], project: str) -> list[Problem]:
    """The newest stamped release, the skills' stamp and pyproject agree."""
    stamped = [r for r in cl.numbered() if not r.retroactive]
    values = set(stamps.values())
    if values == {None} or not values:
        if stamped:
            return [Problem(f"[{stamped[0].title}]",
                            "listed as a stamped release, but no skill carries a stamp")]
        return []
    if len(values) > 1:
        return [Problem("skills", f"skills carry different stamps: {sorted(map(str, values))}")]
    stamp = values.pop()
    problems: list[Problem] = []
    if stamp != project:
        problems.append(Problem("skills", f"stamp {stamp} differs from pyproject {project}"))
    if not stamped or stamped[0].title != stamp:
        newest = stamped[0].title if stamped else "none"
        problems.append(Problem("skills", f"stamp {stamp} is not the newest stamped "
                                          f"release (newest: {newest})"))
    return problems


def check_coverage(cl: Changelog, root: Path) -> list[Problem]:
    """Every change archived on or after CUTOFF is linked or declared internal."""
    problems: list[Problem] = []
    for folder in sorted((root / "openspec" / "changes" / "archive").iterdir()):
        if not folder.is_dir() or folder.name[:10] < CUTOFF or folder.name in cl.archive_links:
            continue
        proposal = folder / "proposal.md"
        text = proposal.read_text(encoding="utf-8") if proposal.is_file() else ""
        if not INTERNAL_RE.search(text):
            problems.append(Problem(folder.name, "archived without a changelog entry and "
                                                 "without 'Changelog: internal'"))
    return problems


def git_tag_commit(root: Path) -> Callable[[str], str | None]:
    def resolve(tag: str) -> str | None:
        proc = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "--verify", "-q", f"refs/tags/{tag}^{{commit}}"],
            capture_output=True, text=True, check=False)
        return proc.stdout.strip() or None
    return resolve


def check_tags(cl: Changelog, resolve: Callable[[str], str | None]) -> list[Problem]:
    """A local tag for a retroactive release points at the commit its section names."""
    problems: list[Problem] = []
    for release in cl.numbered():
        sha = resolve(f"v{release.title}") if release.commit else None
        if sha and not sha.startswith(release.commit):  # type: ignore[arg-type]
            problems.append(Problem(f"[{release.title}]",
                                    f"tag v{release.title} points at {sha[:7]}, "
                                    f"the section names {release.commit}"))
    return problems


def check(root: Path, resolve: Callable[[str], str | None] | None = None) -> list[Problem]:
    path = root / "CHANGELOG.md"
    if not path.is_file():
        return [Problem("CHANGELOG.md", "missing")]
    cl = parse(path.read_text(encoding="utf-8"))
    return (check_structure(cl) + check_sections(cl) + check_links(cl, root)
            + check_stamp(cl, skill_stamps(root), project_version(root))
            + check_coverage(cl, root) + check_tags(cl, resolve or git_tag_commit(root)))


def notes(text: str, version: str) -> str | None:
    """The body of one release: everything under its heading, trimmed."""
    for release in parse(text).releases:
        if release.title == version:
            return "\n".join(release.body).strip() + "\n"
    return None


def run_notes(root: Path, version: str) -> int:
    body = notes((root / "CHANGELOG.md").read_text(encoding="utf-8"), version)
    if body is None:
        print(f"error: no release {version} in CHANGELOG.md", file=sys.stderr)
        return 1
    sys.stdout.write(body)
    return 0


def run_check(root: Path) -> int:
    problems = check(root)
    for problem in problems:
        print(f"- {problem}")
    print(f"changelog: {len(problems)} problem(s)" if problems else "changelog: ok")
    return 1 if problems else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=REPO, help=argparse.SUPPRESS)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check", help="run the changelog gate")
    notes_cmd = sub.add_parser("notes", help="print one release's body")
    notes_cmd.add_argument("version")
    args = parser.parse_args(argv)
    if args.command == "notes":
        return run_notes(args.root, args.version)
    return run_check(args.root)


if __name__ == "__main__":
    sys.exit(main())


