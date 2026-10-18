#!/usr/bin/env python3
"""Snowballing mode: expand from seed DOIs backward (their references) and
forward (papers citing them) via the graph-capable sources; merge, dedupe,
emit CSL-YAML on stdout.

Usage: snowball.py DOI [DOI ...] [--limit-per-seed N] [--direction both|backward|forward]

Bare-DOI results (e.g. from OpenCitations) are enriched with metadata via
Crossref before emission. Relevance judgment stays with the agent. A line on
stderr counts the candidates and the output's size before the output.

The default of 5 per seed keeps one seed's output within what every measured
host shows (measured 2026-10-14: 17,657 to 23,735 characters for one seed);
two seeds at 5 already exceed it, so the skill snowballs one seed per call.
"""

from __future__ import annotations

import argparse
import sys

# Run as the program, write no bytecode cache for the siblings below: the
# skill's install directory is read-only territory. Imported by the tests or
# the harness, leave their interpreter's setting alone.
if __name__ == "__main__":
    sys.dont_write_bytecode = True

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
DEFAULT_PER_SEED = 5

# More output than this from one command is more than some supported host shows:
# below Claude Code's 30,000 characters and OpenCode's 2,000 lines (skill-lit-search:
# Search output sized for what a host shows). search.py holds the same bounds.
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
    common.utf8_output()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("seeds", nargs="+", metavar="DOI")
    parser.add_argument("--limit-per-seed", type=int, default=DEFAULT_PER_SEED)
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
    output = common.to_csl_yaml(merged)
    print(count_line(len(merged), output), file=sys.stderr)
    print(output, end="")
    return 0


if __name__ == "__main__":
    sys.exit(main())
