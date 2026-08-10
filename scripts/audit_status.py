#!/usr/bin/env python3
"""Post-publish confirmation: fetch the skills.sh audit verdicts for every
shipped skill and diff them against the committed audit-baseline.json.

Verdicts drift both through our publishes and through provider-side re-scans,
so a zero-diff run is the only evidence the published state is what we think
it is. `--update` rewrites the baseline after a reviewed change. A skill the
site does not know yet (HTTP 404 — shipped here but never published) is
recorded as null rather than failing the run, so the baseline names it and
the first publish shows up as drift.

Usage: uv run python scripts/audit_status.py [--update]
Exit codes: 0 = matches baseline (or baseline updated), 1 = drift, 2 = fetch failure.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINE = REPO / "audit-baseline.json"
API = "https://skills.sh/api/v1/skills/audit/hutzelmann/thesis-proposal-skills/{skill}"
# derived, not listed: audit_scan.py globs the same directories, and a listed
# roster is how proposal-troubleshoot went unmonitored for four days
SKILLS = sorted(p.name for p in (REPO / "skills").glob("proposal-*") if p.is_dir())


def normalize(payload: dict) -> dict:
    """Keep the signal: {provider: {status, riskLevel}}. Summaries and
    timestamps churn on provider re-runs without changing the verdict."""
    return {
        audit["provider"]: {
            "status": audit.get("status"),
            "riskLevel": audit.get("riskLevel"),
        }
        for audit in payload.get("audits") or []
    }


def diff(baseline: dict, current: dict) -> list[str]:
    lines: list[str] = []
    for skill in sorted(set(baseline) | set(current)):
        base_providers = baseline.get(skill) or {}  # null = recorded as unpublished
        cur_providers = current.get(skill) or {}
        for provider in sorted(set(base_providers) | set(cur_providers)):
            before = base_providers.get(provider)
            after = cur_providers.get(provider)
            if before != after:
                lines.append(f"{skill} / {provider}: {before} -> {after}")
    return lines


def fetch_all() -> dict:
    verdicts: dict = {}
    for skill in SKILLS:
        request = urllib.request.Request(
            API.format(skill=skill), headers={"User-Agent": "thesis-proposal-skills audit poller"}
        )
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                verdicts[skill] = normalize(json.load(response))
        except urllib.error.HTTPError as exc:
            if exc.code != 404:
                raise
            verdicts[skill] = None  # shipped here, never published
    return verdicts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--update", action="store_true", help="rewrite the baseline")
    args = parser.parse_args(argv)

    try:
        current = fetch_all()
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"fetch failed: {exc}", file=sys.stderr)
        return 2

    if args.update or not BASELINE.exists():
        BASELINE.write_text(json.dumps(current, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(f"baseline written: {BASELINE.name}")
        return 0

    baseline = json.loads(BASELINE.read_text(encoding="utf-8"))
    changes = diff(baseline, current)
    if changes:
        print("verdict drift vs baseline:", *changes, sep="\n  ")
        return 1
    print(f"all {len(SKILLS)} skills match the baseline")
    return 0


if __name__ == "__main__":
    sys.exit(main())
