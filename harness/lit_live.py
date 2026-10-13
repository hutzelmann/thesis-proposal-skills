#!/usr/bin/env python3
"""Live check of every proposal-lit-search source: one read-only request per
source module, made through the shipped modules, one classified line each.

Usage: python3 harness/lit_live.py [--sources a,b,c]      (uv run poe lit-live)

Exit 1 means the code needs to change: a verification page that was not
passed, an unexpected or malformed answer, an HTTP status other than 429 or
5xx, zero hits for the fixed request, or an unclassified failure. Transient
failures (HTTP 429, any 5xx, network errors) read `busy` and exit 0, and so
does OpenAlex without a key.

Networked and read-only, with no model call. It is never part of `poe test` or
CI, so an external block never makes the suite flaky. A line names only a
count, a classified kind, an HTTP status code or an exception's type: never
server text, URLs, exception messages or key values (widen-lit-live design).
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

# The shipped modules import one another by top-level name, so their directory
# has to be importable (design D1). Under pytest the configured `pythonpath`
# already lists it, and the path is left alone.
if (_scripts := str(Path(__file__).resolve().parents[1] / "skills/proposal-lit-search/scripts")
        ) not in sys.path:
    sys.path.insert(0, _scripts)

import arxiv
import common
import crossref
import dblp
import openalex
import opencitations
import semantic_scholar

QUERY = "pentest"  # the query `poe lit-live` sent to DBLP before this check widened
LIMIT = 3
# the work whose references tests/unit/data/opencitations_refs_sample.json
# captured live, so it is known to the index; an unknown DOI reads as zero hits
SEED_DOI = "10.1145/3292500.3330919"


def _search(module: ModuleType) -> list[dict]:
    return module.search(QUERY, limit=LIMIT)


def _references(module: ModuleType) -> list[dict]:
    return module.references(SEED_DOI, LIMIT)


@dataclass(frozen=True)
class Probe:
    """One source's live request: the module, the call made on it, and the key
    without which the source is skipped instead of asked."""

    module: ModuleType
    request: Callable[[ModuleType], list[dict]]
    key: str | None = None


# static registry — source selection never loads modules from input strings
PROBES: dict[str, Probe] = {
    "dblp": Probe(dblp, _search),
    "crossref": Probe(crossref, _search),
    "arxiv": Probe(arxiv, _search),
    "semantic_scholar": Probe(semantic_scholar, _search),
    "opencitations": Probe(opencitations, _references),
    "openalex": Probe(openalex, _search, key="OPENALEX_API_KEY"),
}

# kinds whose answer the code has to be changed to handle; "http" and "network"
# are decided by their status, and any other kind is unclassified
_CHANGE_KINDS = frozenset({"challenge", "unexpected", "malformed"})


@dataclass(frozen=True)
class Verdict:
    """What one source's line says, and whether it asks for a code change."""

    label: str
    needs_change: bool


def classify_results(results: list) -> Verdict:
    """Hits are a pass; zero hits for the fixed request is drift, never a pass."""
    if results:
        return Verdict(f"ok ({len(results)})", needs_change=False)
    return Verdict("empty (0)", needs_change=True)


def _transient(status: int | None) -> bool:
    """429 or any server fault: busy, never a sign that the API changed. This
    covers `common.RETRY_CODES`, which the client has retried by now."""
    return status == 429 or (isinstance(status, int) and 500 <= status <= 599)


def classify_error(exc: Exception) -> Verdict:
    """The verdict for a failed request, from its classification alone (design D4).

    Transient means HTTP 429, any 5xx, or a network failure.
    """
    if not isinstance(exc, common.SourceError):
        return Verdict(f"crashed ({type(exc).__name__})", needs_change=True)
    status = f" (HTTP {exc.status})" if isinstance(exc.status, int) else ""
    if exc.kind == "network":
        return Verdict("busy (network)", needs_change=False)
    if exc.kind == "http":
        if _transient(exc.status):
            return Verdict(f"busy{status}", needs_change=False)
        return Verdict(f"http{status}", needs_change=True)
    if exc.kind in _CHANGE_KINDS:
        return Verdict(f"{exc.kind}{status}", needs_change=True)
    return Verdict("unclassified", needs_change=True)


def run_probe(probe: Probe) -> Verdict:
    """Make the probe's one request, unless the key it needs resolves nowhere.

    The key is looked up exactly as the shipped scripts look it up
    (`common.get_key`), and only the module itself ever sends it.
    """
    if probe.key and not common.get_key(probe.key):
        return Verdict("skipped (no key)", needs_change=False)
    try:
        results = probe.request(probe.module)
    except Exception as exc:  # classified or not, every failure becomes a verdict
        return classify_error(exc)
    return classify_results(results)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sources", default=",".join(PROBES),
                        help="comma-separated subset of the sources (default: all)")
    args = parser.parse_args(argv)

    requested = {name.strip() for name in args.sources.split(",") if name.strip()}
    if unknown := sorted(requested - PROBES.keys()):
        parser.error(f"unknown source(s): {', '.join(unknown)} — valid: {', '.join(PROBES)}")
    if not requested:
        parser.error(f"no source selected — valid: {', '.join(PROBES)}")

    needs_change = False
    for name, probe in PROBES.items():
        if name in requested:
            verdict = run_probe(probe)
            print(f"{name} {verdict.label}", flush=True)
            needs_change |= verdict.needs_change
    return 1 if needs_change else 0


if __name__ == "__main__":
    sys.exit(main())
