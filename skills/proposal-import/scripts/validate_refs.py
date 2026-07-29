#!/usr/bin/env python3
"""Validate and complement the references of an imported proposal.

Stdlib-only (Python >= 3.11). For every entry in the proposal's `references:`
block: a DOI is verified by Crossref lookup (and missing fields filled from
the record); an entry without DOI is identified via Crossref search and
completed only on a confident title match. Prints a per-reference report
(verified / enriched / unverifiable / offline) and, for enriched entries,
the completed CSL-YAML the agent applies to the proposal.

Usage: python3 validate_refs.py <proposal.md>
Exit codes: 0 = ran (see report), 2 = no references block found.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import common  # noqa: E402
import crossref  # noqa: E402


def extract_references(text: str) -> list[dict]:
    """Narrow extraction of reference entries from the trailing metadata block."""
    lines = text.rstrip("\n").split("\n")
    delim = [i for i, l in enumerate(lines) if re.fullmatch(r"---\s*", l)]
    if len(delim) < 2 or delim[-1] != len(lines) - 1:
        return []
    block = lines[delim[-2] + 1 : delim[-1]]
    refs: list[dict] = []
    in_refs = False
    current: dict | None = None
    for line in block:
        if re.match(r"^references:\s*$", line):
            in_refs = True
            continue
        if in_refs and re.match(r"^\w[\w-]*\s*:", line):  # next top-level key
            break
        if not in_refs:
            continue
        if m := re.match(r"^-\s+id:\s*(\S+)", line):
            current = {"id": m.group(1)}
            refs.append(current)
        elif current is not None:
            for field, pattern in (
                ("DOI", r"^\s+DOI:\s*(\S+)"),
                ("title", r"^\s+title:\s*(.+)$"),
                ("year", r"^\s+year:\s*(\d{4})"),
            ):
                if m := re.match(pattern, line):
                    current.setdefault(field, m.group(1).strip().strip("'\""))
    return refs


def title_matches(a: str | None, b: str | None) -> bool:
    na, nb = common.normalize_title(a or ""), common.normalize_title(b or "")
    return bool(na) and na == nb


def lookup_doi(doi: str) -> dict | None:
    """Crossref lookup; None for a DOI that does not resolve (HTTP 404).
    Network-class failures propagate as SourceError (reported as OFFLINE)."""
    try:
        data = common.http_json(
            f"https://api.crossref.org/works/{common.clean_doi(doi)}",
            source="crossref", min_interval=0.5,
        )
    except common.SourceError as exc:
        if "404" in str(exc):
            return None
        raise
    return crossref.parse_work(data["message"])


def identify(entry: dict) -> dict | None:
    """Crossref search; accept only a confident (normalized-title-equal) match."""
    if not entry.get("title"):
        return None
    for candidate in crossref.search(entry["title"], 5):
        if title_matches(candidate.get("title"), entry.get("title")):
            return candidate
    return None


def merge(entry: dict, record: dict) -> dict:
    merged = dict(record)
    merged["id"] = entry["id"]
    return merged


def main() -> int:
    proposal = Path(sys.argv[1])
    refs = extract_references(proposal.read_text(encoding="utf-8"))
    if not refs:
        print("no references block found — nothing to validate")
        return 2

    enriched_entries: list[dict] = []
    for entry in refs:
        try:
            if doi := entry.get("DOI"):
                record = lookup_doi(doi)
                if record is None or not record.get("title"):
                    print(f"UNVERIFIABLE {entry['id']}: DOI {doi} does not resolve — mark [TODO: verify reference {entry['id']}]")
                elif entry.get("title") and not title_matches(record["title"], entry["title"]):
                    print(f"UNVERIFIABLE {entry['id']}: DOI resolves to a different title ({record['title'][:60]}…) — mark [TODO: verify reference {entry['id']}]")
                else:
                    print(f"VERIFIED {entry['id']}: DOI resolves and matches")
                    enriched_entries.append(merge(entry, record))
            else:
                record = identify(entry)
                if record is None:
                    print(f"UNVERIFIABLE {entry['id']}: no confident match found — mark [TODO: verify reference {entry['id']}]")
                else:
                    print(f"ENRICHED {entry['id']}: identified via title match, DOI {record.get('DOI', '—')}")
                    enriched_entries.append(merge(entry, record))
        except common.SourceError as exc:
            print(f"OFFLINE {entry['id']}: {exc} — validation skipped for this entry")

    if enriched_entries:
        print("\n--- completed CSL-YAML (apply to the proposal, keeping the existing ids) ---")
        print(common.to_csl_yaml(enriched_entries))
    return 0


if __name__ == "__main__":
    sys.exit(main())
