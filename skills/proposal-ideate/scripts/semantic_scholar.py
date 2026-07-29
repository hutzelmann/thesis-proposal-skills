#!/usr/bin/env python3
# GENERATED from skills/proposal-lit-search/scripts/semantic_scholar.py — edit there, then run scripts/sync_shared.py
"""Semantic Scholar source client.

API base URL: https://api.semanticscholar.org/graph/v1
Key policy: keyless by design (project policy — shared public pool). Expect
HTTP 429 under load; common.http_json retries with backoff, and persistent
429/5xx surfaces as SourceError so the orchestrator can degrade.
"""

from __future__ import annotations

import common

API = "https://api.semanticscholar.org/graph/v1"
SOURCE = "semantic_scholar"
MIN_INTERVAL = 1.5

_SEARCH_FIELDS = "title,abstract,year,venue,authors,externalIds,publicationTypes"
_GRAPH_FIELDS = "title,abstract,year,venue,authors,externalIds"

_TYPE_MAP = {
    "Conference": "paper-conference",
    "JournalArticle": "article-journal",
}


def _entry_type(publication_types: list[str] | None) -> str:
    for pub_type in publication_types or []:
        if pub_type in _TYPE_MAP:
            return _TYPE_MAP[pub_type]
    return "article-journal"


def _authors(raw: list[dict] | None) -> list[dict]:
    authors: list[dict] = []
    for author in raw or []:
        name = (author.get("name") or "").strip()
        if not name:
            continue
        given, _, family = name.rpartition(" ")
        authors.append({"family": family, "given": given} if given else {"family": family})
    return authors


def _paper_entry(paper: dict, entry_type: str | None = None) -> dict | None:
    title = (paper.get("title") or "").strip()
    if not title:
        return None
    external_ids = paper.get("externalIds") or {}
    return common.entry(
        title=title,
        source=SOURCE,
        authors=_authors(paper.get("authors")),
        year=paper.get("year"),
        venue=paper.get("venue") or None,
        doi=external_ids.get("DOI"),
        url=paper.get("url"),
        abstract=paper.get("abstract"),
        entry_type=entry_type or _entry_type(paper.get("publicationTypes")),
    )


def search(query: str, limit: int = 10) -> list[dict]:
    """Search Semantic Scholar; return CSL-JSON-shaped dicts."""
    data = common.http_json(
        f"{API}/paper/search",
        params={"query": query, "limit": limit, "fields": _SEARCH_FIELDS},
        source=SOURCE,
        min_interval=MIN_INTERVAL,
    )
    results = []
    for paper in data.get("data") or []:
        if item := _paper_entry(paper):
            results.append(item)
    return results


def _graph(doi: str, direction: str, wrapper_key: str, limit: int) -> list[dict]:
    clean = common.clean_doi(doi)
    if not clean:
        raise common.SourceError(f"{SOURCE}: invalid DOI {doi!r}")
    data = common.http_json(
        f"{API}/paper/DOI:{clean}/{direction}",
        params={"fields": _GRAPH_FIELDS, "limit": limit},
        source=SOURCE,
        min_interval=MIN_INTERVAL,
    )
    results = []
    for edge in data.get("data") or []:
        if item := _paper_entry(edge.get(wrapper_key) or {}):
            results.append(item)
    return results


def references(doi: str, limit: int = 30) -> list[dict]:
    """Papers the given DOI cites (outgoing edges)."""
    return _graph(doi, "references", "citedPaper", limit)


def citations(doi: str, limit: int = 30) -> list[dict]:
    """Papers citing the given DOI (incoming edges)."""
    return _graph(doi, "citations", "citingPaper", limit)
