#!/usr/bin/env python3
"""Resolve a submitted bug report's file hashes to the revision that produced it.

The collector shipped inside proposal-troubleshoot emits git blob hashes, which
are the object names git already stores. Identification is therefore a tree
comparison rather than a content walk: the install matches revision R when every
submitted blob equals the blob at that path in R's tree.

Reports the newest such revision, how far behind HEAD it is, and any file that
matches no revision at all — that file was edited locally, which is the answer to
most "works for me" reports.

Reads a `hashes.txt` from a bug report, or a whole bundle directory.

Usage:
    python3 scripts/identify_release.py <bug-report/ | hashes.txt>
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_PREFIX = "skills/"
FIELD_RE = re.compile(r"(\w+)=([0-9a-f]+|\d+)")
# The publish pipeline stamps `metadata.version` into every SKILL.md — the
# suite's semantic version, sourced from pyproject.toml (skill-packaging spec).
# A report that carries the stamp names its snapshot outright, and the tree
# comparison degrades to a verification step. The frontmatter line shape is
# required, not a bare X.Y.Z: version-looking numbers occur all over bug
# reports (tool versions, dates), the stamped line only in a SKILL.md snapshot.
STAMP_RE = re.compile(r"^\s*version:\s*(\d+\.\d+\.\d+)\s*$", re.MULTILINE)

# which checkout the lookups run against; --repo overrides it so the resolver can
# be exercised against a purpose-built history instead of this one
_repo: Path = REPO


def git(*args: str) -> str:
    proc = subprocess.run(
        ["git", "-C", str(_repo), *args], capture_output=True, text=True, check=False
    )
    return proc.stdout if proc.returncode == 0 else ""


def parse_hashes(text: str) -> list[dict[str, str]]:
    entries: list[dict[str, str]] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        entry: dict[str, str] = {"path": SKILLS_PREFIX + parts[0]}
        for field in parts[1:]:
            m = FIELD_RE.fullmatch(field)
            if m:
                entry[m.group(1)] = m.group(2)
        if "git_blob" in entry:
            entries.append(entry)
    return entries


def tree_blobs(rev: str) -> dict[str, str]:
    """path -> blob for every file under skills/ at this revision."""
    out: dict[str, str] = {}
    for line in git("ls-tree", "-r", rev, SKILLS_PREFIX).splitlines():
        meta, _, path = line.partition("\t")  # "<mode> blob <sha>\t<path>"
        fields = meta.split()
        if len(fields) >= 3 and fields[1] == "blob":
            out[path] = fields[2]
    return out


def find_stamp(report: Path) -> str | None:
    """First publish stamp found in the report's text files, hashes.txt included."""
    files = sorted(report.rglob("*")) if report.is_dir() else [report]
    for f in files:
        if not f.is_file() or f.suffix not in (".txt", ".md", ".json"):
            continue
        if m := STAMP_RE.search(f.read_text(encoding="utf-8", errors="replace")):
            return m.group(1)
    return None


def stamped_revision(stamp: str) -> str | None:
    """The commit that introduced this stamp under skills/ — the publish commit."""
    raw = git("log", "--reverse", "--format=%h", f"-Sversion: {stamp}", "--", SKILLS_PREFIX)
    lines = raw.splitlines()
    return lines[0] if lines else None


def prioritize(
    revisions: list[tuple[str, str, str]], sha: str | None
) -> list[tuple[str, str, str]]:
    """Try the stamped revision first; the full-match short-circuit does the rest."""
    if not sha:
        return revisions
    hit = [r for r in revisions if r[0] == sha]
    return hit + [r for r in revisions if r[0] != sha] if hit else revisions


def candidate_revisions() -> list[tuple[str, str, str]]:
    """Commits touching skills/, newest first: (sha, date, subject)."""
    raw = git("rev-list", "HEAD", "--format=%h\x1f%ad\x1f%s", "--date=short", "--",
              SKILLS_PREFIX)
    out = []
    for line in raw.splitlines():
        if "\x1f" not in line:  # rev-list prints a bare "commit <sha>" header line
            continue
        sha, _, rest = line.partition("\x1f")
        date, _, subject = rest.partition("\x1f")
        out.append((sha, date, subject))
    return out


def entry_matches(entry: dict[str, str], tree: dict[str, str]) -> bool:
    actual = tree.get(entry["path"])
    if actual is None:
        return False
    return actual in (entry.get("git_blob"), entry.get("git_blob_lf"))


def best_revision(
    entries: list[dict[str, str]], revisions: list[tuple[str, str, str]]
) -> tuple[tuple[str, str, str] | None, int, dict[str, str]]:
    """Newest revision matching the most submitted files. Stops at a full match."""
    best: tuple[str, str, str] | None = None
    best_count = -1
    best_tree: dict[str, str] = {}
    for rev in revisions:
        tree = tree_blobs(rev[0])
        count = sum(1 for e in entries if entry_matches(e, tree))
        if count > best_count:
            best, best_count, best_tree = rev, count, tree
        if count == len(entries):
            break
    return best, max(best_count, 0), best_tree


def commits_behind(sha: str) -> int | None:
    raw = git("rev-list", "--count", f"{sha}..HEAD").strip()
    return int(raw) if raw.isdigit() else None


def known_paths() -> set[str]:
    """Every path that ever existed under skills/, so a file absent from history
    is reported as locally added rather than as a mismatch.
    """
    raw = git("log", "--all", "--pretty=format:", "--name-only", "--", SKILLS_PREFIX)
    return {line.strip() for line in raw.splitlines() if line.strip()}


def render(entries: list[dict[str, str]], revisions: list[tuple[str, str, str]]) -> tuple[str, int]:
    if not revisions:
        return "error: no commits touch skills/ in this repository\n", 2

    rev, matched, tree = best_revision(entries, revisions)
    seen_paths = known_paths()
    mismatched = [e for e in entries if not entry_matches(e, tree)]
    unknown = [e for e in mismatched if e["path"] not in seen_paths]
    modified = [e for e in mismatched if e["path"] in seen_paths]

    sha, date, subject = rev if rev else ("?", "?", "?")
    behind = commits_behind(sha)
    lines = [
        f"{len(entries)} file(s) submitted, {matched} matching the best revision",
        "",
        "## Best match",
        f"  {sha} ({date}) {subject}",
    ]
    if behind is not None:
        lines.append(f"  {behind} commit(s) behind HEAD")
    lines.append("")

    if modified:
        lines.append(f"## Differs from that revision — {len(modified)} file(s)")
        lines.extend(f"  {e['path']}" for e in modified)
        lines.append("")
    if unknown:
        lines.append(f"## Not in this repository's history — {len(unknown)} file(s)")
        lines.extend(f"  {e['path']}" for e in unknown)
        lines.append("")

    lines.append("## Verdict")
    if matched == len(entries):
        if behind == 0:
            lines.append("Every submitted file matches HEAD. The report is against current code.")
        else:
            lines.append(
                f"Clean install of {sha}. Reproduce against that revision, not HEAD — "
                f"{behind} commit(s) have landed since."
            )
        exit_code = 0
    elif modified and not unknown:
        lines.append(
            f"{len(modified)} file(s) match no revision at any point in history: this install "
            "was edited locally, or was assembled from more than one revision. Treat the report "
            "as being about modified code and ask the user to reinstall before reproducing."
        )
        exit_code = 1
    else:
        lines.append(
            f"{len(unknown)} file(s) are unknown to this repository (a newer release, another "
            "package, or hand-added files) and "
            f"{len(modified)} file(s) differ from {sha}. Identification is partial."
        )
        exit_code = 1
    return "\n".join(lines) + "\n", exit_code


def main(argv: list[str] | None = None) -> int:
    global _repo
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("target", type=Path,
                        help="a bug-report directory or a hashes.txt from one")
    parser.add_argument("--repo", type=Path, default=REPO,
                        help="checkout to resolve against (default: this repository)")
    args = parser.parse_args(argv)
    _repo = args.repo

    path = args.target / "hashes.txt" if args.target.is_dir() else args.target
    if not path.is_file():
        print(f"error: no hashes.txt at {path}", file=sys.stderr)
        return 2
    if not git("rev-parse", "--git-dir").strip():
        print("error: not a git repository — this tool runs in the development repo",
              file=sys.stderr)
        return 2

    entries = parse_hashes(path.read_text(encoding="utf-8"))
    if not entries:
        print(f"error: no hash entries parsed from {path}", file=sys.stderr)
        return 2

    revisions = candidate_revisions()
    if stamp := find_stamp(args.target):
        sha = stamped_revision(stamp)
        print(f"publish stamp {stamp} -> {sha or 'no commit introduces it here'}")
        revisions = prioritize(revisions, sha)

    text, code = render(entries, revisions)
    print(text, end="")
    return code


if __name__ == "__main__":
    sys.exit(main())
