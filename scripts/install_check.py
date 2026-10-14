#!/usr/bin/env python3
"""Verify that the scripted install routes work on the tracked tree.

Exports `git archive HEAD` (byte-for-byte what the registry and the
default-branch archive serve — tracked files only, so a checkout's untracked
`.claude/skills/*` helpers never leak in) and installs it twice, each under an
isolated HOME/XDG: with the README's skills-CLI command, and with the
repository's `install.py --scope all` given the export as a zip. It asserts:

- the CLI command is extracted from the README itself (drift guard),
- exactly the shipped `proposal-*` skills install, nothing else,
- every installed skill file is byte-identical to the repository's,
- the installer's records name HEAD's commit (read from the zip comment),
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
import json
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
# the installer's all-projects targets and its record (install.py, installation spec)
INSTALLER_DIRS = (".agents/skills", ".claude/skills")
RECORD_NAME = ".thesis-proposal-install.json"
# the package ends at whitespace or at the closing backtick of inline code
COMMAND_RE = re.compile(r"npx skills add ([^\s`]+)")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


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
        USERPROFILE=str(home),
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


def run_smoke(workdir: Path, installed_root: Path) -> tuple[bool, str]:
    """The installed check script against a known-broken proposal."""
    proposal = workdir / SMOKE_FIXTURE.name
    proposal.write_bytes(SMOKE_FIXTURE.read_bytes())
    script = installed_root / "proposal-check" / "scripts" / "check.py"
    result = subprocess.run(
        [sys.executable, str(script), proposal.name],
        cwd=workdir, capture_output=True, encoding="utf-8", check=False,
    )
    if result.returncode != 1:
        return False, (f"expected exit 1 with findings, got {result.returncode}: "
                       f"{result.stderr[-300:]}")
    if "ERROR" not in result.stdout:
        return False, "check ran but reported no findings on a broken fixture"
    return True, "installed check.py found the seeded errors"


def verbatim_problems(stdout: str, expected: list[str]) -> list[str]:
    """Problems in the README command's --list output: every shipped skill
    offered, count exact. The CLI colorizes the count under CI=true, so escape
    sequences are stripped before matching."""
    stdout = ANSI_RE.sub("", stdout)
    listed = [s for s in expected if s in stdout]
    if listed != expected:
        return [f"published repo offers {len(listed)}/{len(expected)} shipped skills"]
    if f"Found {len(expected)} skills" not in stdout:
        return ["published repo offers a different skill count than the tracked tree ships"]
    return []


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
    return verbatim_problems(result.stdout, expected)


def installed_problems(src: Path, installed_root: Path, expected: list[str],
                       label: str) -> list[str]:
    """Exactly the shipped skills, each byte-identical to the export."""
    installed = sorted(d.name for d in installed_root.iterdir() if d.is_dir()) \
        if installed_root.is_dir() else []
    problems = [] if installed == expected else [
        f"{label}: installed {installed} != shipped {expected}"]
    for skill in expected:
        problems += [f"{label}: {skill}: {p}"
                     for p in compare_tree(src / "skills" / skill, installed_root / skill)]
    return problems


def smoke_problems(workdir: Path, installed_root: Path, label: str) -> list[str]:
    ok, why = run_smoke(workdir, installed_root)
    print(f"smoke ({label}): {why}")
    return [] if ok else [f"{label}: {why}"]


def record_problems(installed_root: Path, revision: str, label: str) -> list[str]:
    record = installed_root / RECORD_NAME
    try:
        data = json.loads(record.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return [f"{label}: no readable install record in {installed_root.name}: {exc}"]
    found = data.get("revision")
    return [] if found == revision else [
        f"{label}: install record names revision {found}, expected {revision}"]


def npx_arm(command: list[str], package: str, src: Path, base: Path,
            expected: list[str], verbatim: bool) -> list[str]:
    """The README's skills-CLI command, pointed at the exported tree."""
    project, home = base / "npx-project", base / "npx-home"
    project.mkdir()
    home.mkdir()
    env = isolated_env(home)
    local_command = [t if t != package else str(src) for t in command]
    result = subprocess.run(
        ["npx", "-y", *local_command[1:], *INSTALL_FLAGS],
        cwd=project, env=env, capture_output=True, text=True, check=False, timeout=600,
    )
    if result.returncode != 0:
        return [f"npx: install failed:\n{result.stdout[-500:]}\n{result.stderr[-500:]}"]
    installed_root = project / ".claude" / "skills"
    problems = installed_problems(src, installed_root, expected, "npx")
    problems += smoke_problems(project, installed_root, "npx")
    if verbatim:
        problems += check_verbatim(command, env, project, expected)
    return problems


def installer_arm(src: Path, archive: Path, revision: str, base: Path,
                  expected: list[str]) -> list[str]:
    """The repository installer, as the install prompt runs it, given the
    exported tree as a zip whose comment names the revision, as GitHub's does."""
    workdir, home = base / "installer-project", base / "installer-home"
    workdir.mkdir()
    home.mkdir()
    result = subprocess.run(
        [sys.executable, str(src / "install.py"), "--scope", "all", "--source", str(archive)],
        cwd=workdir, env=isolated_env(home), capture_output=True, encoding="utf-8", check=False,
        timeout=300,
    )
    if result.returncode != 0:
        return [f"installer: exit {result.returncode}:\n{result.stdout[-500:]}"
                f"\n{result.stderr[-500:]}"]
    problems: list[str] = []
    for rel in INSTALLER_DIRS:
        root = home / rel
        problems += installed_problems(src, root, expected, f"installer {rel}")
        problems += record_problems(root, revision, f"installer {rel}")
    return problems + smoke_problems(workdir, home / INSTALLER_DIRS[-1], "installer")


def export_tracked_tree(base: Path, ref: str = "HEAD") -> tuple[Path, Path, str]:
    """(extracted tree, zip archive, commit id) of `ref` — tracked files only.

    `ref` may also be a tree (`git write-tree` checks the staged state before
    committing); a tree carries no commit id, so its zip has no comment and the
    installer records the revision as unknown, exactly as it would.
    """
    src, archive = base / "src", base / "thesis-proposal-skills-main.zip"
    src.mkdir()
    tarball = subprocess.run(["git", "-C", str(REPO), "archive", ref],
                             capture_output=True, check=True)
    subprocess.run(["tar", "-x", "-C", str(src)], input=tarball.stdout, check=True)
    subprocess.run(["git", "-C", str(REPO), "archive", "--format=zip",
                    "--prefix=thesis-proposal-skills-main/", "-o", str(archive), ref],
                   check=True)
    commit = subprocess.run(["git", "-C", str(REPO), "rev-parse", "--verify", "--quiet",
                             f"{ref}^{{commit}}"], capture_output=True, text=True, check=False)
    return src, archive, commit.stdout.strip() if commit.returncode == 0 else "unknown"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--verbatim", action="store_true",
                        help="also run the README command unchanged against GitHub (--list)")
    parser.add_argument("--ref", default="HEAD",
                        help="commit or tree to export (default HEAD; `git write-tree` "
                             "checks the staged state)")
    args = parser.parse_args(argv)

    with tempfile.TemporaryDirectory(prefix="install-check-") as tmp:
        base = Path(tmp)
        src, archive, revision = export_tracked_tree(base, args.ref)
        # every input comes from the tree being checked, never the checkout
        command, package = readme_install_command(
            (src / README.name).read_text(encoding="utf-8"))
        expected = shipped_skills(src)
        print(f"README command: {' '.join(command)}   ({len(expected)} skills shipped)")
        problems = npx_arm(command, package, src, base, expected, args.verbatim)
        problems += installer_arm(src, archive, revision, base, expected)

    if problems:
        print("\ninstall check FAILED:")
        for p in problems:
            print(f"  {p}")
        return 1
    print(f"install check passed: {len(expected)} skills through the skills CLI and the "
          f"installer, byte-identical, records name {revision[:12]}, smoke green")
    return 0


if __name__ == "__main__":
    sys.exit(main())
