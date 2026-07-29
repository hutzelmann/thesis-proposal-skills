#!/usr/bin/env python3
# GENERATED from skills/proposal-lit-search/scripts/crossref.py — edit there, then run scripts/sync_shared.py
"""Crossref source client.

API base: https://api.crossref.org — REST/JSON, keyless. Politeness comes from
the shared User-Agent (set CONTACT_EMAIL to join Crossref's polite pool) plus a
0.5 s minimum interval between requests.

Exposes `search()` and `references()`. Crossref offers no incoming-citation
listing, so there is deliberately no `citations()`.
"""

from __future__ import annotations

import re
import urllib.parse

import common

API = "https://api.crossref.org/works"
_SELECT = "DOI,title,author,issued,container-title,type,abstract,is-referenced-by-count"

_TYPE_MAP = {
    "journal-article": "article-journal",
    "proceedings-article": "paper-conference",
}

# CSL 1.0.2 item types; Crossref types not mappable here fall back to article-journal.
_CSL_TYPES = frozenset({
    "article", "article-journal", "article-magazine", "article-newspaper",
    "bill", "book", "broadcast", "chapter", "classic", "collection",
    "dataset", "document", "entry", "entry-dictionary", "entry-encyclopedia",
    "event", "figure", "graphic", "hearing", "interview", "legal_case",
    "legislation", "manuscript", "map", "motion_picture", "musical_score",
    "pamphlet", "paper-conference", "patent", "performance", "periodical",
    "personal_communication", "post", "post-weblog", "regulation", "report",
    "review", "review-book", "software", "song", "speech", "standard",
    "thesis", "treaty", "webpage",
})


def _entry_type(crossref_type: str | None) -> str:
    mapped = _TYPE_MAP.get(crossref_type or "", crossref_type or "")
    return mapped if mapped in _CSL_TYPES else "article-journal"


def _year(work: dict) -> int | None:
    for field in ("issued", "published-print", "published-online"):
        parts = (work.get(field) or {}).get("date-parts") or [[]]
        if parts[0] and parts[0][0]:
            try:
                return int(parts[0][0])
            except (TypeError, ValueError):
                continue
    return None


def _authors(raw: list | None) -> list[dict] | None:
    authors: list[dict] = []
    for person in raw or []:
        family = person.get("family") or person.get("name")
        if not family:
            continue
        author: dict = {"family": family}
        if person.get("given"):
            author["given"] = person["given"]
        authors.append(author)
    return authors or None


def _from_work(work: dict) -> dict:
    item = common.entry(
        title=(work.get("title") or [""])[0],
        source="crossref",
        authors=_authors(work.get("author")),
        year=_year(work),
        venue=(work.get("container-title") or [None])[0],
        doi=work.get("DOI"),
        abstract=work.get("abstract"),  # JATS XML; entry() strips the tags
        entry_type=_entry_type(work.get("type")),
    )
    if (count := work.get("is-referenced-by-count")) is not None:
        item["_cited_by"] = count
    return item


def search(query: str, limit: int = 10) -> list[dict]:
    """Relevance search over Crossref works, CSL-JSON-shaped."""
    data = common.http_json(
        API,
        params={"query": query, "rows": limit, "select": _SELECT},
        source="crossref",
        min_interval=0.5,
    )
    return [_from_work(work) for work in data.get("message", {}).get("items", [])]


def _ref_year(raw: object) -> int | None:
    if match := re.search(r"\d{4}", str(raw or "")):
        return int(match.group())
    return None


def references(doi: str, limit: int = 30) -> list[dict]:
    """Outgoing references of a work; skips refs with neither DOI nor title."""
    cleaned = common.clean_doi(doi)
    if not cleaned:
        raise common.SourceError("crossref: invalid DOI")
    data = common.http_json(
        f"{API}/{urllib.parse.quote(cleaned)}",
        source="crossref",
        min_interval=0.5,
    )
    results: list[dict] = []
    for ref in data.get("message", {}).get("reference") or []:
        if not ref.get("DOI") and not ref.get("article-title"):
            continue
        results.append(common.entry(
            title=ref.get("article-title") or ref.get("unstructured") or "",
            source="crossref",
            authors=[{"family": ref["author"]}] if ref.get("author") else None,
            year=_ref_year(ref.get("year")),
            venue=ref.get("journal-title") or ref.get("volume-title"),
            doi=ref.get("DOI"),
        ))
        if len(results) >= limit:
            break
    return results
