#!/usr/bin/env python3
"""Verify that the README's install command works on the tracked tree.

Exports `git archive HEAD` (byte-for-byte what the registry serves — tracked
files only, so a checkout's untracked `.claude/skills/*` helpers never leak in),
installs it with the skills CLI under an isolated HOME/XDG, and asserts:

- the install command is extracted from the README itself (drift guard),
- exactly the shipped `proposal-*` skills install, nothing else,
- every installed skill file is byte-identical to the repository's,
- the installed proposal-check script runs against a broken fixture and
  reports findings (scripts, references, and sync copies travel).

The CLI is deliberately unpinned: users run latest, and an installer regression
that would break their installs is exactly what the scheduled CI run exists to
catch. Empirics (skills CLI 1.5.23): a local path is a valid package argument,
the agent id is `claude-code`, non-interactive needs `-y -a claude-code -s '*'`,
and a project-scoped install lands in `<project>/.claude/skills/<name>/`.

Usage:
    uv run poe install-check              # archive-based check (network: npx)
    uv run poe install-check --verbatim   # also run the README command as-is
                                          # against GitHub with --list
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
README = REPO / "README.md"
SMOKE_FIXTURE = REPO / "tests" / "fixtures" / "f15-format-broken" / "broken-format.md"
INSTALL_FLAGS = ["-y", "-a", "claude-code", "-s", "*", "--copy"]
COMMAND_RE = re.compile(r"npx skills add (\S+)")


def readme_install_command(text: str) -> tuple[list[str], str]:
    """(command tokens, package argument) from the README's documented command."""
    m = COMMAND_RE.search(text)
    if not m:
        raise ValueError("README no longer documents an `npx skills add <package>` command")
    return m.group(0).split(), m.group(1)


def shipped_skills(repo: Path) -> list[str]:
    return sorted(d.name for d in (repo / "skills").iterdir()
                  if d.is_dir() and d.name.startswith("proposal-"))


def isolated_env(home: Path) -> dict[str, str]:
    env = {k: v for k, v in os.environ.items() if not k.startswith("CLAUDE")}
    env.update(
        HOME=str(home),
        XDG_CONFIG_HOME=str(home / ".config"),
        XDG_DATA_HOME=str(home / ".local" / "share"),
        XDG_CACHE_HOME=str(home / ".cache"),
    )
    return env


def compare_tree(source: Path, installed: Path) -> list[str]:
    """Repo-side files missing or differing in the installed copy."""
    problems = []
    for f in sorted(source.rglob("*")):
        if not f.is_file():
            continue
        target = installed / f.relative_to(source)
        if not target.is_file():
            problems.append(f"missing: {f.relative_to(source).as_posix()}")
        elif target.read_bytes() != f.read_bytes():
            problems.append(f"differs: {f.relative_to(source).as_posix()}")
    return problems


def run_smoke(project: Path) -> tuple[bool, str]:
    """The installed check script against a known-broken proposal."""
    proposal = project / SMOKE_FIXTURE.name
    proposal.write_bytes(SMOKE_FIXTURE.read_bytes())
    script = project / ".claude" / "skills" / "proposal-check" / "scripts" / "check.py"
    result = subprocess.run(
        [sys.executable, str(script), proposal.name],
        cwd=project, capture_output=True, text=True, check=False,
    )
    if result.returncode != 1:
        return False, (f"expected exit 1 with findings, got {result.returncode}: "
                       f"{result.stderr[-300:]}")
    if "ERROR" not in result.stdout:
        return False, "check ran but reported no findings on a broken fixture"
    return True, "installed check.py found the seeded errors"


def check_verbatim(command: list[str], env: dict[str, str], cwd: Path,
                   expected: list[str]) -> list[str]:
    """Run the README command unchanged with --list: the published repo must
    resolve and offer exactly the shipped skills. Scheduled runs only."""
    result = subprocess.run(
        ["npx", "-y", *command[1:], "--list"],
        cwd=cwd, env=env, capture_output=True, text=True, check=False, timeout=300,
    )
    if result.returncode != 0:
        return [f"verbatim README command failed: {result.stderr[-300:]}"]
    listed = [s for s in expected if s in result.stdout]
    if listed != expected:
        return [f"published repo offers {len(listed)}/{len(expected)} shipped skills"]
    if f"Found {len(expected)} skills" not in result.stdout:
        return ["published repo offers a different skill count than the tracked tree ships"]
    return []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbatim", action="store_true",
                        help="also run the README command unchanged against GitHub (--list)")
    args = parser.parse_args(argv)

    command, package = readme_install_command(README.read_text(encoding="utf-8"))
    expected = shipped_skills(REPO)
    print(f"README command: {' '.join(command)}   ({len(expected)} skills shipped)")

    problems: list[str] = []
    with tempfile.TemporaryDirectory(prefix="install-check-") as tmp:
        base = Path(tmp)
        src, project, home = base / "src", base / "project", base / "home"
        for d in (src, project, home):
            d.mkdir()
        archive = subprocess.run(["git", "-C", str(REPO), "archive", "HEAD"],
                                 capture_output=True, check=True)
        subprocess.run(["tar", "-x", "-C", str(src)], input=archive.stdout, check=True)

        env = isolated_env(home)
        local_command = [t if t != package else str(src) for t in command]
        result = subprocess.run(
            ["npx", "-y", *local_command[1:], *INSTALL_FLAGS],
            cwd=project, env=env, capture_output=True, text=True, check=False, timeout=600,
        )
        if result.returncode != 0:
            print(f"install failed:\n{result.stdout[-500:]}\n{result.stderr[-500:]}")
            return 1

        installed_root = project / ".claude" / "skills"
        installed = sorted(d.name for d in installed_root.iterdir()) \
            if installed_root.is_dir() else []
        if installed != expected:
            problems.append(f"installed {installed} != shipped {expected}")
        for skill in expected:
            problems += [f"{skill}: {p}"
                         for p in compare_tree(src / "skills" / skill, installed_root / skill)]
        ok, why = run_smoke(project)
        print(f"smoke: {why}")
        if not ok:
            problems.append(why)
        if args.verbatim:
            problems += check_verbatim(command, env, project, expected)

    if problems:
        print("\ninstall check FAILED:")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"install check passed: {len(expected)} skills, byte-identical, smoke green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
