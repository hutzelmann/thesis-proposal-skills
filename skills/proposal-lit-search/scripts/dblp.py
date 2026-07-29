#!/usr/bin/env python3
"""DBLP source client (search-only).

API base URL: https://dblp.org/search/publ/api (q, format=json, h=limit).
Key policy: no API key required; DBLP is open but rate-limited, so requests
are throttled via common.http_json politeness (min_interval 1.0s) and 429s
retry with backoff. No abstracts and no citation graph are available.
"""

from __future__ import annotations

import common

BASE_URL = "https://dblp.org/search/publ/api"

_TYPE_MAP = {
    "Conference and Workshop Papers": "paper-conference",
    "Journal Articles": "article-journal",
}


def _parse_authors(raw: dict | list | str | None) -> list[dict]:
    """DBLP nests authors as info.authors.author: a dict for one, a list for many."""
    if not raw:
        return []
    if isinstance(raw, dict):
        raw = raw.get("author", [])
    if isinstance(raw, dict):
        raw = [raw]
    authors: list[dict] = []
    for author in raw:
        name = (author.get("text", "") if isinstance(author, dict) else str(author)).strip()
        # DBLP disambiguates homonyms with a numeric suffix ("Wei Wang 0001").
        parts = name.split()
        if parts and parts[-1].isdigit():
            parts = parts[:-1]
        if not parts:
            continue
        if len(parts) == 1:
            authors.append({"family": parts[0]})
        else:
            authors.append({"family": parts[-1], "given": " ".join(parts[:-1])})
    return authors


def _parse_hit(hit: dict) -> dict | None:
    info = hit.get("info") or {}
    title = (info.get("title") or "").strip().rstrip(".")
    if not title:
        return None
    year_raw = info.get("year")
    year = int(year_raw) if isinstance(year_raw, str) and year_raw.isdigit() else None
    venue = info.get("venue")
    if isinstance(venue, list):
        venue = ", ".join(str(v) for v in venue)
    return common.entry(
        title=title,
        source="dblp",
        authors=_parse_authors(info.get("authors")),
        year=year,
        venue=venue,
        doi=info.get("doi"),
        url=info.get("ee") or info.get("url"),
        entry_type=_TYPE_MAP.get(info.get("type", ""), "article-journal"),
    )


def search(query: str, limit: int = 10) -> list[dict]:
    """Search DBLP publications; returns CSL-JSON-shaped dicts."""
    data = common.http_json(
        BASE_URL,
        params={"q": query, "format": "json", "h": limit},
        source="dblp",
        min_interval=1.0,
    )
    hits = ((data.get("result") or {}).get("hits") or {}).get("hit") or []
    return [item for hit in hits if (item := _parse_hit(hit)) is not None][:limit]
