#!/usr/bin/env python3
"""Run the Agent Skills reference validator over every skill (standard-conformance spec).

The reference validator is `skills-ref`, the Python package the standard's
maintainers publish in the standard's own repository
(https://github.com/agentskills/agentskills, subdirectory `skills-ref`; see
https://agentskills.io/specification, "Validation"). The npm package of the same
name is an unrelated third-party port and is not it. The validator runs beside
this repository's stricter tests, not instead of them.

The pin below is the one place the validator's version is chosen. It is a full
commit id, because the repository has no tags and the package is on no index,
and it carries the versions of the two dependencies that decide what the
validator accepts: `uvx` resolves a git source afresh and ignores the
package's own lock file. Bumping the pin is the reviewed step by which
movement in the standard arrives here, as one commit:

    git ls-remote https://github.com/agentskills/agentskills main
    # set SKILLS_REF_COMMIT to that id, and SKILLS_REF_DEPS to the click and
    # strictyaml versions in skills-ref/uv.lock at that commit
    uv run poe conform

The CLI validates a single directory per call, so this wrapper fans out and
aggregates. The first run needs network to fill the uv cache; later runs work
offline.

Usage:
    python3 scripts/conform.py            # validate skills/proposal-*
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
REFERENCE_REPO = "https://github.com/agentskills/agentskills"
# agentskills main as resolved on 2026-10-13 (commit dated 2026-08-09)
SKILLS_REF_COMMIT = "69ef37e9424c0a7ea9dd2293b559e43ec8176379"
# from skills-ref/uv.lock at SKILLS_REF_COMMIT: the YAML parser decides which
# frontmatter is accepted, the CLI library decides the exit codes
SKILLS_REF_DEPS = ("strictyaml==1.7.3", "click==8.3.1")
SKILLS_REF_SOURCE = f"git+{REFERENCE_REPO}@{SKILLS_REF_COMMIT}#subdirectory=skills-ref"
UV_INSTALL = "https://docs.astral.sh/uv/getting-started/installation/"


def command(skill_dir: Path, uvx: str = "uvx") -> list[str]:
    """The pinned validator's invocation for one skill directory."""
    pins = [arg for dep in SKILLS_REF_DEPS for arg in ("--with", dep)]
    return [uvx, "--from", SKILLS_REF_SOURCE, *pins, "skills-ref", "validate", str(skill_dir)]


def validate(skill_dir: Path, uvx: str) -> tuple[bool, str]:
    # The validator reads SKILL.md without naming an encoding, so on Windows it
    # would decode with the locale codec (cp1252) and miscount every non-ASCII
    # character against the standard's length limits.
    proc = subprocess.run(
        command(skill_dir, uvx), capture_output=True, text=True, encoding="utf-8",
        check=False, cwd=REPO, env={**os.environ, "PYTHONUTF8": "1"},
    )
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, output


def main(argv: list[str] | None = None) -> int:
    if argv:
        print("usage: python3 scripts/conform.py (no arguments)", file=sys.stderr)
        return 2
    uvx = shutil.which("uvx")
    if uvx is None:
        print("error: uvx not found. The reference validator runs through uv; install it "
              f"({UV_INSTALL}) and run again.", file=sys.stderr)
        return 2
    skill_dirs = sorted(d for d in (REPO / "skills").glob("proposal-*") if d.is_dir())
    if not skill_dirs:
        print("error: no skill directories found", file=sys.stderr)
        return 2
    label = f"agentskills skills-ref @ {SKILLS_REF_COMMIT[:7]}"
    failures = []
    for skill_dir in skill_dirs:
        ok, output = validate(skill_dir, uvx)
        print(output or f"{'ok' if ok else 'FAIL'}: {skill_dir.name}")
        if not ok:
            failures.append(skill_dir.name)
    if failures:
        print(f"\n{len(failures)} skill(s) fail {label}: {', '.join(failures)}")
        return 1
    print(f"\nall {len(skill_dirs)} skills conform ({label})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
