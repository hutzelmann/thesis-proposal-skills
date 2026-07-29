#!/usr/bin/env python3
# GENERATED from skills/proposal-lit-search/scripts/arxiv.py — edit there, then run scripts/sync_shared.py
"""arXiv source client (search-only).

API base URL: http://export.arxiv.org/api/query (Atom XML feed).
Key policy: no API key required; arXiv asks for a courtesy delay of ~3 seconds
between requests, enforced here via min_interval=3.0.
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET

import common

BASE_URL = "http://export.arxiv.org/api/query"
NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
MIN_INTERVAL = 3.0


def _collapse(text: str | None) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _split_name(full: str) -> dict:
    """Split a full name at the last space into given/family."""
    full = _collapse(full)
    if " " in full:
        given, family = full.rsplit(" ", 1)
        return {"family": family, "given": given}
    return {"family": full}


def _parse_entry(node: ET.Element) -> dict:
    title = _collapse(node.findtext("atom:title", default="", namespaces=NS))
    abstract = _collapse(node.findtext("atom:summary", default="", namespaces=NS)) or None
    authors = [
        _split_name(name.text or "")
        for name in node.findall("atom:author/atom:name", NS)
        if _collapse(name.text)
    ]
    year: int | None = None
    published = node.findtext("atom:published", default="", namespaces=NS)
    if match := re.match(r"(\d{4})", published):
        year = int(match.group(1))
    url = node.findtext("atom:id", default="", namespaces=NS).strip() or None
    doi = node.findtext("arxiv:doi", default=None, namespaces=NS)
    return common.entry(
        title=title,
        source="arxiv",
        authors=authors or None,
        year=year,
        doi=doi,
        url=url,
        abstract=abstract,
        entry_type="article",
    )


def _parse_feed(xml_text: str) -> list[dict]:
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise common.SourceError(f"arxiv: invalid Atom XML ({exc})") from exc
    return [_parse_entry(node) for node in root.findall("atom:entry", NS)]


def search(query: str, limit: int = 10) -> list[dict]:
    """Search arXiv across all fields; returns CSL-shaped preprint entries."""
    xml_text = common.http_text(
        BASE_URL,
        params={"search_query": f"all:{query}", "max_results": limit},
        source="arxiv",
        min_interval=MIN_INTERVAL,
    )
    return _parse_feed(xml_text)
