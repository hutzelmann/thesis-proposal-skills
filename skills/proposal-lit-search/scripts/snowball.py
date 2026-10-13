#!/usr/bin/env python3
"""Snowballing mode: expand from seed DOIs backward (their references) and
forward (papers citing them) via the graph-capable sources; merge, dedupe,
emit CSL-YAML on stdout.

Usage: snowball.py DOI [DOI ...] [--limit-per-seed N] [--direction both|backward|forward]

Bare-DOI results (e.g. from OpenCitations) are enriched with metadata via
Crossref before emission. Relevance judgment stays with the agent.
"""

from __future__ import annotations

import argparse
import sys

import common
import crossref
import openalex
import opencitations
import semantic_scholar

# static registry — the graph walk never loads modules from input strings
GRAPH_SOURCES = {
    "semantic_scholar": semantic_scholar,
    "openalex": openalex,
    "crossref": crossref,
    "opencitations": opencitations,
}


def expand(seeds: list[str], limit: int, direction: str) -> list[dict]:
    collected: list[dict] = []
    noted: set[str] = set()

    def note(text: str) -> None:
        """Each distinct note once per run, however many seeds and directions
        hit the same failure (a missing key used to print once per call)."""
        if text not in noted:
            noted.add(text)
            print(text, file=sys.stderr)

    for name, module in GRAPH_SOURCES.items():
        for seed in seeds:
            doi = common.clean_doi(seed)
            if not doi:
                note(f"note: `{seed}` is not a DOI, skipped")
                continue
            for edge in ("references", "citations", "recommendations"):
                if direction == "backward" and edge != "references":
                    continue
                if direction == "forward" and edge == "references":
                    continue
                func = getattr(module, edge, None)
                if func is None:
                    continue
                try:
                    collected.extend(func(doi, limit))
                except common.SourceError as exc:
                    note(f"note: source degraded — {exc}")
                except Exception as exc:  # the type only: its text can carry server output
                    note(f"note: {name}.{edge} failed — {type(exc).__name__}")
    return common.dedupe(collected)


def enrich_bare_dois(items: list[dict]) -> list[dict]:
    """Fill title/authors for graph results that carry only a DOI."""
    enriched: list[dict] = []
    for item in items:
        if item.get("title"):
            enriched.append(item)
            continue
        doi = item.get("DOI")
        if not doi:
            continue
        try:
            data = common.http_json(
                f"https://api.crossref.org/works/{doi}", source="crossref", min_interval=0.5
            )["message"]
            enriched.append(crossref.parse_work(data))
        except Exception:  # enrichment is best-effort; a bad item must not kill the run
            continue
    return enriched


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seeds", nargs="+", metavar="DOI")
    parser.add_argument("--limit-per-seed", type=int, default=20)
    parser.add_argument("--direction", choices=["both", "backward", "forward"], default="both")
    args = parser.parse_args(argv)

    expanded = expand(args.seeds, args.limit_per_seed, args.direction)
    merged = common.dedupe(enrich_bare_dois(expanded))
    seed_dois = {common.clean_doi(s) for s in args.seeds}
    merged = [m for m in merged if m.get("DOI") not in seed_dois]
    if not merged:
        print("no expansion results", file=sys.stderr)
        return 1
    for item in merged:
        item["id"] = common.make_key(item)
    print(common.to_csl_yaml(merged), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
