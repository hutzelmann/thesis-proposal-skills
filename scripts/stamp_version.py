#!/usr/bin/env python3
"""Stamp `metadata.version` into every SKILL.md as part of the publish sequence.

The version is semantic and has exactly one source of truth: `[project] version`
in `pyproject.toml`. Publishing means bumping it there (patch for fixes, minor
for new behavior or skills, major for breaking workspace-facing changes), running
this script, and committing the stamp (`chore(publish): stamp <version>`), so the
published tree names its snapshot and `poe identify` resolves a bug report
without walking history. All skills share the suite version; a re-stamp of a
version that already exists in history is refused, keeping version → snapshot
unique. Never hand-edit the stamp (skill-packaging spec: `metadata` is not
hand-maintained).

Usage:
    python3 scripts/stamp_version.py            # stamp from pyproject.toml
    python3 scripts/stamp_version.py --force    # re-stamp an already-used version
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tomllib
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
METADATA_BLOCK = re.compile(r"metadata:\n  version: \S+\n")
SEMVER = re.compile(r"\d+\.\d+\.\d+")


def project_version() -> str:
    data = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    return data["project"]["version"]


def already_stamped(version: str) -> bool:
    """True when a commit already introduced this stamp under skills/."""
    proc = subprocess.run(
        ["git", "-C", str(REPO), "log", "--format=%h", f"-Sversion: {version}",
         "--", "skills/"],
        capture_output=True, text=True, check=False,
    )
    return bool(proc.stdout.strip())


def stamp_text(text: str, version: str, path: Path | None) -> str:
    block = f"metadata:\n  version: {version}\n"
    if METADATA_BLOCK.search(text):
        return METADATA_BLOCK.sub(block, text, count=1)
    head, sep, body = text.partition("\n---\n")
    if not sep:
        raise ValueError(f"{path}: no closing frontmatter delimiter")
    return head + "\n" + block + "---\n" + body


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--force", action="store_true",
                        help="re-stamp a version that already exists in history")
    args = parser.parse_args(argv)
    version = project_version()
    if not SEMVER.fullmatch(version):
        print(f"error: pyproject.toml version is not semver: {version!r}", file=sys.stderr)
        return 2
    if already_stamped(version) and not args.force:
        print(f"error: {version} is already stamped in history — bump "
              "[project] version in pyproject.toml first (--force to override)",
              file=sys.stderr)
        return 1
    for skill_md in sorted(REPO.glob("skills/proposal-*/SKILL.md")):
        text = skill_md.read_text(encoding="utf-8")
        skill_md.write_text(stamp_text(text, version, skill_md), encoding="utf-8")
        print(f"stamped {skill_md.parent.name} {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
