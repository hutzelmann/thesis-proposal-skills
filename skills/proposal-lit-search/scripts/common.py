#!/usr/bin/env python3
"""Shared helpers for the literature-search source clients.

Stdlib-only (Python >= 3.11). Every source module exposes
`search(query, limit) -> list[dict]` returning CSL-JSON-shaped dicts plus a
`_source` provenance tag; graph-capable sources add `references(doi)` and
`citations(doi)`. Failures raise SourceError — orchestrators degrade, never block.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

TIMEOUT = 20
RETRIES = 2
BACKOFF_SECONDS = 3.0

_last_call: dict[str, float] = {}


class SourceError(Exception):
    """A source is unavailable (network, quota, missing key)."""


KEY_FILE = "api-keys.env"
KEY_FILE_ENV = "THESIS_PROPOSAL_KEYS"
GLOBAL_KEY_FILE = Path.home() / ".config" / "thesis-proposal" / KEY_FILE
KEY_LOCATIONS = (
    f"the {KEY_FILE_ENV} path, "
    f"{KEY_FILE} in the working directory or any parent, "
    f"or ~/.config/thesis-proposal/{KEY_FILE}"
)


def key_file_candidates() -> list[Path]:
    """Key files to consult, most specific first.

    Explicit `THESIS_PROPOSAL_KEYS` override, then `api-keys.env` in the working
    directory and its ancestors — so a script works from anywhere inside the
    user's proposal workspace, not only its root — then a user-global file for
    keys shared across workspaces. Ancestor walking stops at the home directory.
    """
    candidates: list[Path] = []
    if override := os.environ.get(KEY_FILE_ENV):
        candidates.append(Path(override).expanduser())
    home = Path.home()
    cwd = Path.cwd()
    for directory in (cwd, *cwd.parents):
        candidates.append(directory / KEY_FILE)
        if directory == home:
            break
    if GLOBAL_KEY_FILE not in candidates:
        candidates.append(GLOBAL_KEY_FILE)
    return candidates


def _read_key(path: Path, name: str) -> str | None:
    """One KEY=VALUE per line, `#` comments allowed; missing file is not an error."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return None
    for line in text.splitlines():
        line = line.strip()
        if line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        if key.strip() == name and value.strip():
            return value.strip().strip("'\"")
    return None


def get_key(name: str) -> str | None:
    """Credential lookup: environment first, then each key file in turn.

    Resolution is per key, so a workspace file can hold the API key while the
    global file supplies CONTACT_EMAIL. Any key file must be gitignored by
    whichever skill creates it.
    """
    if value := os.environ.get(name):
        return value
    for path in key_file_candidates():
        if value := _read_key(path, name):
            return value
    return None


def user_agent() -> str:
    contact = get_key("CONTACT_EMAIL")
    base = "thesis-proposal-skills/0.1 (https://github.com/hutzelmann/thesis-proposal-skills)"
    return f"{base} mailto:{contact}" if contact else base


def http_json(url: str, params: dict | None = None, headers: dict | None = None,
              source: str = "", min_interval: float = 1.0):
    """GET a JSON document with politeness throttling and 429/5xx retry."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    wait = _last_call.get(source, 0) + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    request = urllib.request.Request(url, headers={"User-Agent": user_agent(), **(headers or {})})
    last_error: Exception | None = None
    for attempt in range(RETRIES + 1):
        try:
            _last_call[source] = time.monotonic()
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return json.load(response)
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code in (429, 500, 502, 503) and attempt < RETRIES:
                time.sleep(BACKOFF_SECONDS * (attempt + 1))
                continue
            raise SourceError(f"{source}: HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < RETRIES:
                time.sleep(BACKOFF_SECONDS)
                continue
    raise SourceError(f"{source}: {last_error}")


def http_text(url: str, params: dict | None = None, source: str = "",
              min_interval: float = 1.0) -> str:
    """GET a text document (arXiv Atom XML) with the same politeness rules."""
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    wait = _last_call.get(source, 0) + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    request = urllib.request.Request(url, headers={"User-Agent": user_agent()})
    for attempt in range(RETRIES + 1):
        try:
            _last_call[source] = time.monotonic()
            with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
                return response.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, TimeoutError) as exc:
            if attempt < RETRIES:
                time.sleep(BACKOFF_SECONDS)
                continue
            raise SourceError(f"{source}: {exc}") from exc
    raise SourceError(f"{source}: unreachable")


# ---------- normalization ----------------------------------------------------

def clean_doi(raw: str | None) -> str | None:
    if not raw:
        return None
    doi = raw.strip()
    doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.IGNORECASE)
    return doi.lower() or None


def normalize_title(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", title.lower()).strip()


def entry(*, title: str, source: str, authors: list[dict] | None = None,
          year: int | None = None, venue: str | None = None, doi: str | None = None,
          url: str | None = None, abstract: str | None = None,
          entry_type: str = "article-journal") -> dict:
    """Build a CSL-JSON-shaped dict; URL only kept when no DOI (guideline rule)."""
    item: dict = {"type": entry_type, "title": title.strip(), "_source": source}
    if authors:
        item["author"] = authors
    if year:
        item["issued"] = {"year": year}
    if venue:
        item["container-title"] = venue
    if doi := clean_doi(doi):
        item["DOI"] = doi
    elif url:
        item["URL"] = url
    if abstract:
        item["abstract"] = re.sub(r"<[^>]+>", "", abstract).strip()
    return item


def make_key(item: dict) -> str:
    """AuthorYearFirstWordOfTitle, < 20 chars (guideline rule)."""
    family = (item.get("author") or [{}])[0].get("family", "Anon")
    family = re.sub(r"[^A-Za-z]", "", family) or "Anon"
    year = str(item.get("issued", {}).get("year", ""))[-2:]
    stop = {"a", "an", "the", "on", "of", "for", "and", "in", "to", "with"}
    first = next(
        (w for w in re.findall(r"[A-Za-z]+", item.get("title", "")) if w.lower() not in stop),
        "Work",
    )
    return (family[:10] + year + first.capitalize()[:7])[:19]


def dedupe(items: list[dict]) -> list[dict]:
    """Merge duplicates by DOI, then by normalized title; richer entry wins fields."""
    result: list[dict] = []
    by_doi: dict[str, dict] = {}
    by_title: dict[str, dict] = {}
    for item in items:
        title_key = normalize_title(item.get("title", ""))
        existing = None
        if doi := item.get("DOI"):
            existing = by_doi.get(doi)
        if existing is None and title_key:
            existing = by_title.get(title_key)
        if existing is None:
            result.append(item)
            if doi := item.get("DOI"):
                by_doi[doi] = item
            if title_key:
                by_title[title_key] = item
        else:
            for field, value in item.items():
                if field != "_source" and field not in existing and value:
                    existing[field] = value
            existing["_source"] = f"{existing['_source']},{item['_source']}"
    return result


# ---------- CSL-YAML emission -------------------------------------------------

def _yaml_scalar(value: str) -> str:
    if re.search(r"[:#\[\]{}\"'|>&*!%@`,]|^\s|\s$|^[-?]", value) or value == "":
        return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'
    return value


def to_csl_yaml(items: list[dict]) -> str:
    """Emit entries as a CSL-YAML list ready for a proposal's references block."""
    lines: list[str] = []
    for item in items:
        lines.append(f"- id: {item.get('id') or make_key(item)}")
        lines.append(f"  type: {item.get('type', 'article-journal')}")
        if authors := item.get("author"):
            lines.append("  author:")
            for a in authors:
                lines.append(f"  - family: {_yaml_scalar(a.get('family', ''))}")
                if a.get("given"):
                    lines.append(f"    given: {_yaml_scalar(a['given'])}")
        if year := item.get("issued", {}).get("year"):
            lines.append(f"  issued:\n    year: {year}")
        lines.append(f"  title: {_yaml_scalar(item['title'])}")
        if venue := item.get("container-title"):
            lines.append(f"  container-title: {_yaml_scalar(venue)}")
        if doi := item.get("DOI"):
            lines.append(f"  DOI: {_yaml_scalar(doi)}")
        elif url := item.get("URL"):
            lines.append(f"  URL: {_yaml_scalar(url)}")
        if abstract := item.get("abstract"):
            lines.append(f"  abstract: {_yaml_scalar(abstract[:1500])}")
    return "\n".join(lines) + "\n"
