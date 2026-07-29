#!/usr/bin/env python3
"""OpenAlex source client (search + citation graph).

API base URL: https://api.openalex.org
Key policy: KEY-GATED. Requires the OPENALEX_API_KEY environment variable
(free key: https://openalex.org/settings/api); it is sent as the `api_key`
query parameter on every request. All public functions raise
common.SourceError when the variable is unset.
"""

from __future__ import annotations

import os
import urllib.parse

import common

API = "https://api.openalex.org/works"
SELECT = ("id,title,display_name,authorships,publication_year,"
          "primary_location,doi,abstract_inverted_index,referenced_works")
MIN_INTERVAL = 0.2
BATCH_MAX = 50  # OpenAlex allows at most ~50 OR-joined values per filter


def _api_key() -> str:
    key = os.environ.get("OPENALEX_API_KEY")
    if not key:
        raise common.SourceError(
            "openalex: no OPENALEX_API_KEY set (free key: https://openalex.org/settings/api)")
    return key


def _get(url: str, params: dict) -> dict:
    return common.http_json(url, params=params, source="openalex",
                            min_interval=MIN_INTERVAL)


def _reconstruct_abstract(inverted: dict[str, list[int]] | None) -> str | None:
    """Rebuild abstract text from OpenAlex's inverted index (often null)."""
    if not inverted:
        return None
    pairs = sorted((pos, word) for word, positions in inverted.items() for pos in positions)
    return " ".join(word for _, word in pairs) or None


def _authors(work: dict) -> list[dict]:
    authors: list[dict] = []
    for authorship in work.get("authorships") or []:
        name = (authorship.get("author") or {}).get("display_name")
        if not name:
            continue
        given, _, family = name.strip().rpartition(" ")
        author = {"family": family}
        if given:
            author["given"] = given
        authors.append(author)
    return authors


def _parse(work: dict) -> dict:
    location = work.get("primary_location") or {}
    venue = (location.get("source") or {}).get("display_name")
    return common.entry(
        title=work.get("title") or work.get("display_name") or "",
        source="openalex",
        authors=_authors(work) or None,
        year=work.get("publication_year"),
        venue=venue,
        doi=work.get("doi"),
        url=work.get("id"),
        abstract=_reconstruct_abstract(work.get("abstract_inverted_index")),
    )


def _lookup(doi: str, key: str) -> dict:
    cleaned = common.clean_doi(doi)
    if not cleaned:
        raise common.SourceError("openalex: empty DOI")
    url = f"{API}/doi:{urllib.parse.quote(cleaned)}"
    return _get(url, {"select": "id,referenced_works", "api_key": key})


def search(query: str, limit: int = 10) -> list[dict]:
    key = _api_key()
    data = _get(API, {
        "search": query,
        "per-page": max(1, min(limit, 200)),
        "select": SELECT,
        "api_key": key,
    })
    return [_parse(work) for work in data.get("results") or []]


def references(doi: str, limit: int = 30) -> list[dict]:
    """Works cited by the given DOI (one batch fetch of referenced_works ids)."""
    key = _api_key()
    work = _lookup(doi, key)
    ids = [ref.rsplit("/", 1)[-1] for ref in work.get("referenced_works") or []]
    ids = ids[:min(limit, BATCH_MAX)]
    if not ids:
        return []
    data = _get(API, {
        "filter": "openalex_id:" + "|".join(ids),
        "per-page": len(ids),
        "select": SELECT,
        "api_key": key,
    })
    return [_parse(work) for work in data.get("results") or []]


def citations(doi: str, limit: int = 30) -> list[dict]:
    """Works that cite the given DOI."""
    key = _api_key()
    work = _lookup(doi, key)
    work_id = (work.get("id") or "").rsplit("/", 1)[-1]
    if not work_id:
        raise common.SourceError(f"openalex: no work id for DOI {doi}")
    data = _get(API, {
        "filter": f"cites:{work_id}",
        "per-page": max(1, min(limit, 200)),
        "select": SELECT,
        "api_key": key,
    })
    return [_parse(work) for work in data.get("results") or []]
