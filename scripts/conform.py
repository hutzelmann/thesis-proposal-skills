#!/usr/bin/env python3
"""Run the Agent Skills reference validator over every skill (standard-conformance spec).

`skills-ref` is the standard's own validator (https://agentskills.io/specification,
"Validation"); it runs beside this repository's stricter tests, not instead of
them. The version pin below is the one place the standard's toolchain version is
chosen — bumping it is the reviewed step by which movement in the standard
arrives here. The CLI validates a single directory per call, so this wrapper
fans out and aggregates.

Usage:
    python3 scripts/conform.py            # validate skills/proposal-*
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS_REF_PIN = "skills-ref@0.1.5"


def validate(skill_dir: Path) -> tuple[bool, str]:
    proc = subprocess.run(
        ["npx", "-y", SKILLS_REF_PIN, "validate", str(skill_dir)],
        capture_output=True, text=True, check=False, cwd=REPO,
    )
    output = (proc.stdout + proc.stderr).strip()
    return proc.returncode == 0, output


def main(argv: list[str] | None = None) -> int:
    if argv:
        print("usage: python3 scripts/conform.py (no arguments)", file=sys.stderr)
        return 2
    skill_dirs = sorted(d for d in (REPO / "skills").glob("proposal-*") if d.is_dir())
    if not skill_dirs:
        print("error: no skill directories found", file=sys.stderr)
        return 2
    failures = []
    for skill_dir in skill_dirs:
        ok, output = validate(skill_dir)
        print(output or f"{'ok' if ok else 'FAIL'}: {skill_dir.name}")
        if not ok:
            failures.append(skill_dir.name)
    if failures:
        print(f"\n{len(failures)} skill(s) fail {SKILLS_REF_PIN}: {', '.join(failures)}")
        return 1
    print(f"\nall {len(skill_dirs)} skills conform ({SKILLS_REF_PIN})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
