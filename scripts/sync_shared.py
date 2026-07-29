#!/usr/bin/env python3
"""Materialize shared/ sources into self-contained skill copies.

One-way, deterministic: shared/ is the only place devs edit; committed copies
inside skills are what skills.sh installs. Run with --check (CI/L0) to fail on
drift instead of writing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

MD_HEADER = "<!-- GENERATED from shared/ — edit shared/, then run scripts/sync_shared.py -->\n\n"
JSON_HEADER_KEY = "_generated"
JSON_HEADER_VALUE = "from shared/structure.json — edit shared/, then run scripts/sync_shared.py"

# source (repo-relative) -> list of destination directories (repo-relative)
SYNC_MAP: dict[str, list[str]] = {
    "shared/guidelines/guidelines.md": [
        "skills/proposal-write/references",
        "skills/proposal-review/references",
        "skills/proposal-customize/references",
        "skills/proposal-ideate/references",
    ],
    "shared/structure.json": [
        "skills/proposal-check/references",
        "skills/proposal-ideate/references",
    ],
    # common+crossref vendored into import: validate_refs.py imports them as
    # Python modules, so a missing sibling would crash rather than degrade.
    # Ideate instead uses the sibling-fallback path (packaging spec).
    "skills/proposal-lit-search/scripts/common.py": ["skills/proposal-import/scripts"],
    "skills/proposal-lit-search/scripts/crossref.py": ["skills/proposal-import/scripts"],
}


def render(source: Path) -> str:
    text = source.read_text(encoding="utf-8")
    if source.suffix == ".md":
        return MD_HEADER + text
    if source.suffix == ".json":
        data = json.loads(text)
        stamped = {JSON_HEADER_KEY: JSON_HEADER_VALUE, **data}
        return json.dumps(stamped, ensure_ascii=False, indent=2) + "\n"
    if source.suffix == ".py":
        header = f"# GENERATED from {source.relative_to(REPO)} — edit there, then run scripts/sync_shared.py\n"
        lines = text.split("\n", 1)
        if lines[0].startswith("#!"):
            return lines[0] + "\n" + header + (lines[1] if len(lines) > 1 else "")
        return header + text
    return text


def sync(check: bool) -> int:
    drift: list[str] = []
    for src_rel, dest_dirs in SYNC_MAP.items():
        source = REPO / src_rel
        expected = render(source)
        for dest_dir in dest_dirs:
            dest = REPO / dest_dir / source.name
            if check:
                if not dest.exists() or dest.read_text(encoding="utf-8") != expected:
                    drift.append(str(dest.relative_to(REPO)))
            else:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_text(expected, encoding="utf-8")
                print(f"synced {src_rel} -> {dest.relative_to(REPO)}")
    if check and drift:
        print("OUT OF SYNC (run scripts/sync_shared.py):", *drift, sep="\n  ")
        return 1
    if check:
        print("shared/ copies in sync")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify copies instead of writing")
    return sync(parser.parse_args().check)


if __name__ == "__main__":
    sys.exit(main())
