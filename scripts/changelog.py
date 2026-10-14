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

`release` (`poe release`) cuts a release locally: it picks the version the
Unreleased entries require, refuses 1.0.0 until the readiness gate holds, adds
a model-support entry when the roster or a verdict moved, moves the entries
under the new heading, sets pyproject and uv.lock, stamps every SKILL.md,
re-runs the gate, commits exactly those files and creates the annotated tag.
It never pushes; it prints the push and `gh release` commands instead.

Usage:
    python3 scripts/changelog.py check
    python3 scripts/changelog.py notes 0.8.0
    python3 scripts/changelog.py release [--bump minor|--version 1.0.0] [--dry-run]
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from itertools import pairwise
from pathlib import Path

import stamp_version  # sibling script: one stamp format for `release` and the manual path

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


# ---------- release (add-release-command) ------------------------------------

BUMPS = ("patch", "minor", "major")
ONE_ZERO: Version = (1, 0, 0)
# The 1.0.0 readiness gate, agreed with the maintainer on 2026-10-14: the
# desktop install verified (its change archived) and every model in the README
# summary measured. Edit this list deliberately; the diff is the review.
READINESS_OPEN_CHANGES = ("desktop-first-install",)
SUMMARY_START, SUMMARY_END = "<!-- model-support:start -->", "<!-- model-support:end -->"
RELEASE_PATHS = ("CHANGELOG.md", "pyproject.toml", "uv.lock")
# main holds releases only and moves by fast-forward; work integrates on develop
# (add-changelog design D7).
MAIN, DEVELOP = "main", "develop"


class ReleaseRefused(Exception):
    """A precondition of `release` does not hold; the message says which."""


def required_bump(unreleased: Release, current: Version) -> str:
    if any(e.startswith("- **Breaking:**") for e in unreleased.entries):
        return "major" if current >= ONE_ZERO else "minor"
    return "minor" if unreleased.by_category.get("Added") else "patch"


def bumped(current: Version, kind: str) -> Version:
    major, minor, patch = current
    if kind == "major":
        return (major + 1, 0, 0)
    if kind == "minor":
        return (major, minor + 1, 0)
    return (major, minor, patch + 1)


def choose_version(unreleased: Release, current: Version, bump: str | None,
                   explicit: str | None) -> tuple[Version, str]:
    """The version to cut and why; refuses anything below what the entries need."""
    need = required_bump(unreleased, current)
    floor = bumped(current, need)
    if explicit:
        version = tuple(int(p) for p in explicit.split("."))
        if len(version) != 3 or version < floor:  # type: ignore[operator]
            raise ReleaseRefused(f"{explicit} is below {vstr(floor)}, which the entries "
                                 f"require ({need} bump over {vstr(current)})")
        return version, f"explicit --version over {vstr(current)}"  # type: ignore[return-value]
    if bump and BUMPS.index(bump) < BUMPS.index(need):
        raise ReleaseRefused(f"--bump {bump} is lower than the entries require ({need})")
    kind = bump or need
    return bumped(current, kind), f"{kind} bump over {vstr(current)} (entries require {need})"


def _lead_and_marker(body: list[str]) -> tuple[str, str]:
    first = next((i for i, line in enumerate(body) if line.startswith("### ")), len(body))
    head = body[:first]
    marker = next((line for line in head
                   if len(line) > 2 and line.startswith("_") and line.endswith("_")), "")
    lead = "\n".join(line for line in head if line != marker).strip()
    return marker, lead


def render_categories(by_category: dict[str, list[str]]) -> list[str]:
    out: list[str] = []
    for category in CATEGORIES:
        if by_category.get(category):
            out += [f"### {category}", "", *by_category[category], ""]
    return out


def cut(text: str, version: str, date: str, extra_changed: list[str]) -> str:
    """Move [Unreleased] under `## [version] - date`; reset it; fix compare links."""
    cl = parse(text)
    unreleased, newest = cl.releases[0], cl.numbered()[0]
    marker, lead = _lead_and_marker(unreleased.body)
    if not lead:
        raise ReleaseRefused("[Unreleased] has no lead paragraph to open the release with")
    by_category = {c: list(e) for c, e in unreleased.by_category.items()}
    by_category.setdefault("Changed", []).extend(extra_changed)
    lines = text.splitlines()
    start, end = unreleased.line - 1, newest.line - 1
    section = [f"## [{version}] - {date}", "", lead, "", *render_categories(by_category)]
    head = [lines[start], "", marker, ""] if marker else [lines[start], ""]
    new = lines[:start] + head + section + lines[end:]
    old_tag, new_tag = f"v{newest.title}", f"v{version}"
    out = "\n".join(new) + "\n"
    old_link = f"[{UNRELEASED}]: {REPO_URL}/compare/{old_tag}...HEAD"
    new_links = (f"[{UNRELEASED}]: {REPO_URL}/compare/{new_tag}...HEAD\n"
                 f"[{version}]: {REPO_URL}/compare/{old_tag}...{new_tag}")
    if old_link not in out:
        raise ReleaseRefused(f"compare link not found: {old_link}")
    return out.replace(old_link, new_links, 1)


def set_project_version(text: str, version: str) -> str:
    head, sep, tail = text.partition("[project]")
    return head + sep + re.sub(r'(?m)^version = "[^"]*"', f'version = "{version}"', tail, count=1)


def set_lock_version(text: str, version: str) -> str:
    return re.sub(r'(name = "thesis-proposal-skills"\nversion = )"[^"]*"',
                  rf'\g<1>"{version}"', text, count=1)


def summary_rows(readme: str) -> dict[str, str]:
    """`model -> verdict` from the README's generated model-support table."""
    if SUMMARY_START not in readme or SUMMARY_END not in readme:
        return {}
    region = readme.split(SUMMARY_START, 1)[1].split(SUMMARY_END, 1)[0]
    rows: dict[str, str] = {}
    for line in region.splitlines():
        cells = [c.strip() for c in line.split("|")]
        if len(cells) > 3 and cells[1].startswith("`"):
            rows[cells[1].strip("`")] = cells[2]
    return rows


def readiness_problems(root: Path) -> list[str]:
    problems = [f"OpenSpec change {name} is still open"
                for name in READINESS_OPEN_CHANGES
                if (root / "openspec" / "changes" / name).is_dir()]
    readme = root / "README.md"
    rows = summary_rows(readme.read_text(encoding="utf-8")) if readme.is_file() else {}
    problems += [f"model-support summary reads untested for {model}"
                 for model, verdict in rows.items() if "untested" in verdict]
    return problems


def prose_name(model_id: str) -> str:
    """'router/vendor/family-size-2.0' -> 'Family Size 2.0': a prose name, never an ID."""
    words = model_id.rsplit("/", 1)[-1].split("-")
    return " ".join("GPT" if w == "gpt" else w[:1].upper() + w[1:] for w in words)


def roster(models_toml: str) -> list[str]:
    data = tomllib.loads(models_toml)
    return [m["id"] for m in data.get("models", []) if m.get("enabled", True)]


def model_support_line(old_roster: list[str], new_roster: list[str],
                       old_verdicts: dict[str, str], new_verdicts: dict[str, str]) -> str | None:
    def clean(verdict: str) -> str:
        return re.sub(r"^[^\w]+", "", verdict).strip()

    old, new = {prose_name(m) for m in old_roster}, {prose_name(m) for m in new_roster}
    before = {prose_name(k): clean(v) for k, v in old_verdicts.items()}
    after = {prose_name(k): clean(v) for k, v in new_verdicts.items()}
    parts = []
    if added := sorted(new - old):
        parts.append("joins the roster: " + ", ".join(added))
    if retired := sorted(old - new):
        parts.append("leaves the roster: " + ", ".join(retired))
    rejudged = sorted(n for n in new & old if n in before and n in after and before[n] != after[n])
    if rejudged:
        parts.append("re-judged: " + ", ".join(f"{n} ({before[n]} → {after[n]})" for n in rejudged))
    if not parts:
        return None
    return "- Model support: " + "; ".join(parts) + " (see the README's Model support table)."


def git(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True,
                          check=False)
    if check and proc.returncode != 0:
        raise ReleaseRefused(f"git {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def previous_ref(cl: Changelog, resolve: Callable[[str], str | None]) -> str | None:
    newest = cl.numbered()[0]
    return resolve(f"v{newest.title}") or newest.commit


def model_line_since(root: Path, ref: str | None) -> str | None:
    new_toml, new_readme = root / "harness" / "models.toml", root / "README.md"
    if ref is None or not new_toml.is_file() or not new_readme.is_file():
        return None
    old_toml = git(root, "show", f"{ref}:harness/models.toml", check=False)
    if not old_toml:
        return None
    old_readme = git(root, "show", f"{ref}:README.md", check=False)
    return model_support_line(roster(old_toml), roster(new_toml.read_text(encoding="utf-8")),
                              summary_rows(old_readme),
                              summary_rows(new_readme.read_text(encoding="utf-8")))


def stamp_skills(root: Path, version: str) -> list[Path]:
    touched = []
    for skill_md in sorted(root.glob("skills/proposal-*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        skill_md.write_text(stamp_version.stamp_text(text, version, skill_md), encoding="utf-8")
        touched.append(skill_md)
    return touched


@dataclass
class Plan:
    version: str
    reason: str
    text: str
    model_line: str | None


def plan_release(root: Path, args: argparse.Namespace,
                 resolve: Callable[[str], str | None]) -> Plan:
    cl = parse((root / "CHANGELOG.md").read_text(encoding="utf-8"))
    if not cl.releases or cl.releases[0].title != UNRELEASED or not cl.numbered():
        raise ReleaseRefused("CHANGELOG.md needs [Unreleased] above at least one release")
    unreleased, current = cl.releases[0], cl.numbered()[0].version
    if not unreleased.entries:
        raise ReleaseRefused("[Unreleased] has no entries")
    version, reason = choose_version(unreleased, current, args.bump, args.version)  # type: ignore[arg-type]
    if version >= ONE_ZERO and (blockers := readiness_problems(root)):
        raise ReleaseRefused("1.0.0 readiness gate: " + "; ".join(blockers))
    line = model_line_since(root, previous_ref(cl, resolve))
    text = cut((root / "CHANGELOG.md").read_text(encoding="utf-8"), vstr(version), args.date,
               [line] if line else [])
    return Plan(vstr(version), reason, text, line)


def refuse_unsafe_tree(root: Path, version: str, resolve: Callable[[str], str | None]) -> None:
    dirty = git(root, "status", "--porcelain", "--", *RELEASE_PATHS, "skills/*/SKILL.md")
    if dirty.strip():
        raise ReleaseRefused("uncommitted edits in files the release writes:\n" + dirty)
    if resolve(f"v{version}"):
        raise ReleaseRefused(f"tag v{version} already exists")
    if git(root, "log", "--format=%h", f"-Sversion: {version}", "--", "skills/").strip():
        raise ReleaseRefused(f"{version} is already stamped in history")


def has_branch(root: Path, name: str) -> bool:
    return bool(git(root, "rev-parse", "--verify", "-q", f"refs/heads/{name}", check=False).strip())


def release_branch(root: Path) -> str:
    """Releases are cut on `develop`, which `main` then fast-forwards to. Before
    `develop` exists (the 0.9.0 transition) `main` itself may cut one."""
    current = git(root, "rev-parse", "--abbrev-ref", "HEAD").strip()
    if current == DEVELOP:
        if has_branch(root, MAIN) and not _is_ancestor(root, MAIN):
            raise ReleaseRefused(f"`{MAIN}` has commits `{DEVELOP}` lacks; it can no longer "
                                 "fast-forward to a release")
        return current
    if current == MAIN and not has_branch(root, DEVELOP):
        return current
    raise ReleaseRefused(f"releases are cut on `{DEVELOP}` (current branch: {current})")


def _is_ancestor(root: Path, ref: str) -> bool:
    proc = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", ref, "HEAD"],
                          capture_output=True, check=False)
    return proc.returncode == 0


def fast_forward_main(root: Path) -> str:
    """Move `main` to the release commit; never touches a checked-out `main`."""
    listing = git(root, "worktree", "list", "--porcelain")
    for block in listing.split("\n\n"):
        if f"branch refs/heads/{MAIN}" in block.splitlines():
            path = block.splitlines()[0].removeprefix("worktree ")
            return f"  git -C {path} merge --ff-only {DEVELOP}   # `{MAIN}` is checked out there"
    old = git(root, "rev-parse", "--verify", "-q", f"refs/heads/{MAIN}", check=False).strip()
    git(root, "update-ref", f"refs/heads/{MAIN}", "HEAD", *([old] if old else []))
    return ""


def apply_release(root: Path, plan: Plan, resolve: Callable[[str], str | None]) -> None:
    (root / "CHANGELOG.md").write_text(plan.text, encoding="utf-8")
    for name, setter in (("pyproject.toml", set_project_version), ("uv.lock", set_lock_version)):
        path = root / name
        if path.is_file():
            path.write_text(setter(path.read_text(encoding="utf-8"), plan.version),
                            encoding="utf-8")
    skills = stamp_skills(root, plan.version)
    if problems := check(root, resolve):
        raise ReleaseRefused("changelog check fails after the cut (files left modified):\n"
                             + "\n".join(f"- {p}" for p in problems))
    paths = [p for p in RELEASE_PATHS if (root / p).is_file()]
    paths += [s.relative_to(root).as_posix() for s in skills]
    git(root, "add", "--", *paths)
    git(root, "commit", "-m", f"chore(publish): stamp {plan.version}")
    git(root, "tag", "-a", f"v{plan.version}", "-m", f"Release v{plan.version}")


def run_release(root: Path, args: argparse.Namespace,
                resolve: Callable[[str], str | None] | None = None) -> int:
    resolve = resolve or git_tag_commit(root)
    try:
        plan = plan_release(root, args, resolve)
        print(f"release {plan.version}: {plan.reason}")
        if args.dry_run:
            print(notes(plan.text, plan.version) or "", end="")
            return 0
        branch = release_branch(root)
        refuse_unsafe_tree(root, plan.version, resolve)
        apply_release(root, plan, resolve)
        ff_note = fast_forward_main(root) if branch == DEVELOP else ""
    except ReleaseRefused as refusal:
        print(f"refused: {refusal}", file=sys.stderr)
        return 1
    tag = f"v{plan.version}"
    moved = f"`{MAIN}` fast-forwarded" if branch == DEVELOP and not ff_note else "committed"
    branches = f"{DEVELOP} {MAIN}" if branch == DEVELOP else MAIN
    print(f"{moved} and tagged {tag}. Nothing was pushed. To publish, run yourself:\n"
          + (f"{ff_note}\n" if ff_note else "")
          + f"  git push origin {branches} {tag}\n"
          f"  python3 scripts/changelog.py notes {plan.version} > /tmp/{tag}.md\n"
          f"  gh release create {tag} --title {tag} --notes-file /tmp/{tag}.md")
    return 0


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
    rel = sub.add_parser("release", help="cut a release locally: stamp, commit, tag")
    rel.add_argument("--bump", choices=BUMPS, help="raise the bump the entries require")
    rel.add_argument("--version", help="cut exactly this version (needed for 1.0.0)")
    rel.add_argument("--date", default=date.today().isoformat(), help="release date")
    rel.add_argument("--dry-run", action="store_true", help="print the plan, write nothing")
    args = parser.parse_args(argv)
    if args.command == "notes":
        return run_notes(args.root, args.version)
    if args.command == "release":
        return run_release(args.root, args)
    return run_check(args.root)


if __name__ == "__main__":
    sys.exit(main())
