#!/usr/bin/env python3
"""Keyword-mode literature search: federate all available sources, merge,
dedupe, emit CSL-YAML on stdout. Degradation notes go to stderr, followed by
the `sources:` line and a line counting the candidates and the output's size.

Usage: search.py "query terms" [--limit N] [--sources a,b,c]

Relevance judgment is NOT done here — the agent reading the output judges
relevance and writes accepted entries into the proposal (see SKILL.md).
"""

from __future__ import annotations

import argparse
import sys

# Run as the program, write no bytecode cache for the siblings below: the
# skill's install directory is read-only territory. Imported by the tests or
# the harness, leave their interpreter's setting alone.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

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

# appended to a note only for a verification page the script could not pass;
# the route itself is documented in SKILL.md, not here
BROWSER_HINT = (
    'A normal browser may still pass it (see "If a source asks for browser verification" '
    "in the skill); this script stays blocked either way. "
    "This run continues without {source} results."
)

# More output than this from one command is more than some supported host shows:
# below Claude Code's 30,000 characters and OpenCode's 2,000 lines (skill-lit-search:
# Search output sized for what a host shows). snowball.py holds the same bounds.
MAX_SHOWN_CHARS = 25_000
MAX_SHOWN_LINES = 1_800


def count_line(candidates: int, output: str) -> str:
    """The stderr line before the output: how much follows, so an agent can
    tell when its host showed less; flagged above the bounds."""
    lines, chars = len(output.splitlines()), len(output)
    line = f"candidates: {candidates} ({lines} lines, {chars} characters on stdout)"
    if chars > MAX_SHOWN_CHARS or lines > MAX_SHOWN_LINES:
        line += " — more than some hosts show from one command; run narrower"
    return line


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
            note = f"note: source degraded — {exc}"
            if exc.kind == "challenge":
                note += ". " + BROWSER_HINT.format(source=name)
            print(note, file=sys.stderr)
        except Exception as exc:  # a broken source must never block the search
            # the type only: an error's own text can carry what a server sent
            print(f"note: source failed unexpectedly — {name}: {type(exc).__name__}",
                  file=sys.stderr)
    print(f"sources: {', '.join(contributed) or 'none'}", file=sys.stderr)
    return common.dedupe(collected)


def main(argv: list[str] | None = None) -> int:
    common.utf8_output()
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
    output = common.to_csl_yaml(merged)
    print(count_line(len(merged), output), file=sys.stderr)
    print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
