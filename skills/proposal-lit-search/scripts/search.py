#!/usr/bin/env python3
"""Keyword-mode literature search: federate all available sources, merge,
dedupe, emit CSL-YAML on stdout. Degradation notes go to stderr.

Usage: search.py "query terms" [--limit N] [--sources a,b,c]

Relevance judgment is NOT done here — the agent reading the output judges
relevance and writes accepted entries into the proposal (see SKILL.md).
"""

from __future__ import annotations

import argparse
import sys

import arxiv
import common
import crossref
import dblp
import openalex
import semantic_scholar

# static registry — source selection never loads modules from input strings
SEARCH_SOURCES = {
    "dblp": dblp,
    "crossref": crossref,
    "arxiv": arxiv,
    "semantic_scholar": semantic_scholar,
    "openalex": openalex,
}


def federate(query: str, limit: int, sources: list[str]) -> list[dict]:
    collected: list[dict] = []
    contributed: list[str] = []
    for name in sources:
        module = SEARCH_SOURCES[name]
        try:
            results = module.search(query, limit=limit)
            collected.extend(results)
            contributed.append(f"{name}({len(results)})")
        except common.SourceError as exc:
            print(f"note: source degraded — {exc}", file=sys.stderr)
        except Exception as exc:  # a broken source must never block the search
            print(f"note: source failed unexpectedly — {name}: {exc}", file=sys.stderr)
    print(f"sources: {', '.join(contributed) or 'none'}", file=sys.stderr)
    return common.dedupe(collected)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--sources", default=",".join(SEARCH_SOURCES))
    args = parser.parse_args(argv)

    requested = [s.strip() for s in args.sources.split(",") if s.strip()]
    if unknown := [s for s in requested if s not in SEARCH_SOURCES]:
        parser.error(
            f"unknown source(s): {', '.join(unknown)} — valid: {', '.join(SEARCH_SOURCES)}"
        )
    merged = federate(args.query, args.limit, requested)
    if not merged:
        print("no results from any source", file=sys.stderr)
        return 1
    for item in merged:
        item["id"] = common.make_key(item)
    print(common.to_csl_yaml(merged), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
