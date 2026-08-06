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
    for name, module in GRAPH_SOURCES.items():
        for seed in seeds:
            doi = common.clean_doi(seed)
            if not doi:
                print(f"note: `{seed}` is not a DOI, skipped", file=sys.stderr)
                continue
            for kind in ("references", "citations", "recommendations"):
                if direction == "backward" and kind != "references":
                    continue
                if direction == "forward" and kind == "references":
                    continue
                func = getattr(module, kind, None)
                if func is None:
                    continue
                try:
                    collected.extend(func(doi, limit))
                except common.SourceError as exc:
                    print(f"note: source degraded — {exc}", file=sys.stderr)
                except Exception as exc:
                    print(f"note: {name}.{kind} failed — {exc}", file=sys.stderr)
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


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seeds", nargs="+", metavar="DOI")
    parser.add_argument("--limit-per-seed", type=int, default=20)
    parser.add_argument("--direction", choices=["both", "backward", "forward"], default="both")
    args = parser.parse_args()

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
