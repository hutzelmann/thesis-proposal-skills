#!/usr/bin/env python3
"""Keyword-mode literature search: federate all available sources, merge,
dedupe, emit CSL-YAML on stdout. Degradation notes go to stderr.

Usage: search.py "query terms" [--limit N] [--sources a,b,c]

Relevance judgment is NOT done here — the agent reading the output judges
relevance and writes accepted entries into the proposal (see SKILL.md).
"""

from __future__ import annotations

import argparse
import importlib
import sys

import common

SEARCH_SOURCES = ["dblp", "crossref", "arxiv", "semantic_scholar", "openalex"]


def federate(query: str, limit: int, sources: list[str]) -> list[dict]:
    collected: list[dict] = []
    contributed: list[str] = []
    for name in sources:
        try:
            module = importlib.import_module(name)
            results = module.search(query, limit=limit)
            collected.extend(results)
            contributed.append(f"{name}({len(results)})")
        except common.SourceError as exc:
            print(f"note: source degraded — {exc}", file=sys.stderr)
        except Exception as exc:  # a broken source must never block the search
            print(f"note: source failed unexpectedly — {name}: {exc}", file=sys.stderr)
    print(f"sources: {', '.join(contributed) or 'none'}", file=sys.stderr)
    return common.dedupe(collected)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query")
    parser.add_argument("--limit", type=int, default=10)
    parser.add_argument("--sources", default=",".join(SEARCH_SOURCES))
    args = parser.parse_args()

    merged = federate(args.query, args.limit, args.sources.split(","))
    if not merged:
        print("no results from any source", file=sys.stderr)
        return 1
    for item in merged:
        item["id"] = common.make_key(item)
    print(common.to_csl_yaml(merged), end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
