#!/usr/bin/env python3
"""Shared helpers for the literature-search source clients.

Stdlib-only (Python >= 3.11). Every source module exposes
`search(query, limit) -> list[dict]` returning CSL-JSON-shaped dicts plus a
`_source` provenance tag; graph-capable sources add `references(doi)` and
`citations(doi)`. Failures raise SourceError — orchestrators degrade, never block.
"""

from __future__ import annotations

import html
import http.client
import http.cookiejar
import json
import os
import re
import socket
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

TIMEOUT = 20
RETRIES = 2
BACKOFF_SECONDS = 3.0
RETRY_CODES = (429, 500, 502, 503)
MAX_BODY = 16 * 1024 * 1024  # a larger answer is refused, never read whole
SCAN_LIMIT = 64 * 1024  # verification markers are searched in this prefix only
MAX_PASS_DELAY = 10  # seconds a verification page may ask the script to wait

_last_call: dict[str, float] = {}


class SourceError(Exception):
    """A source is unavailable (network, quota, missing key, unusable answer).

    `http_json` classifies its failures in `kind` — "challenge" (a verification
    page that was not passed), "unexpected" (HTML or other non-JSON content),
    "malformed_json", "http", "network" — so an orchestrator acts on the cause
    without parsing the message. Other raisers leave `kind` None.
    """

    def __init__(self, message: str, *, kind: str | None = None, status: int | None = None,
                 media_type: str | None = None) -> None:
        super().__init__(message)
        self.kind = kind
        self.status = status
        self.media_type = media_type


KEY_FILE = "api-keys.env"
KEY_FILE_ENV = "THESIS_PROPOSAL_KEYS"
GLOBAL_KEY_FILE = Path.home() / ".config" / "thesis-proposal" / KEY_FILE
KEY_LOCATIONS = (
    f"the {KEY_FILE_ENV} path, "
    f"{KEY_FILE} in the working directory, "
    f"or ~/.config/thesis-proposal/{KEY_FILE}"
)


def key_file_candidates() -> list[Path]:
    """Key files to consult, most specific first.

    Explicit `THESIS_PROPOSAL_KEYS` override, then `api-keys.env` in the
    working directory (the workspace root in the standard agent setup), then a
    user-global file for keys shared across workspaces. Deliberately no
    ancestor-directory search: credential lookup never reads files outside the
    directory the script was invoked in.
    """
    candidates: list[Path] = []
    if override := os.environ.get(KEY_FILE_ENV):
        candidates.append(Path(override).expanduser())
    candidates.append(Path.cwd() / KEY_FILE)
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
    """GET a JSON document with politeness throttling, 429/5xx retry, and at
    most one pass through a source's refresh-tier verification page.

    Anything that is not usable JSON raises a classified SourceError whose
    message names only the source, the status and the media type — never the
    URL, the query, cookies or any text the server chose.
    """
    if params:
        url = f"{url}?{urllib.parse.urlencode(params)}"
    wait = _last_call.get(source, 0) + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    call = _Call(url, {"User-Agent": user_agent(), **(headers or {})}, source)
    last_error: BaseException | None = None
    for attempt in range(RETRIES + 1):
        try:
            return _fetch_json(call)
        except urllib.error.HTTPError as exc:
            exc.close()
            if exc.code not in RETRY_CODES or attempt == RETRIES:
                raise SourceError(f"{source}: HTTP {exc.code}", kind="http",
                                  status=exc.code) from exc
            time.sleep(BACKOFF_SECONDS * (attempt + 1))
        except SourceError as exc:
            # a truncated transfer may succeed on retry; a page the server
            # chose to send instead of JSON will not
            if exc.kind != "malformed_json" or attempt == RETRIES:
                raise
            time.sleep(BACKOFF_SECONDS)
        except (OSError, http.client.HTTPException) as exc:  # URLError, timeouts, resets
            last_error = exc
            if attempt < RETRIES:
                time.sleep(BACKOFF_SECONDS)
        except ValueError as exc:  # an answer no parser above anticipated
            raise SourceError(f"{source}: API answer could not be processed",
                              kind="unexpected") from exc
    raise SourceError(f"{source}: network failure ({_network_reason(last_error)})",
                      kind="network") from last_error


# Network failures are named from this fixed vocabulary, never by the error's
# own text: `BadStatusLine` carries the server's raw status line, for one.
_NETWORK_REASONS: tuple[tuple[type[BaseException], str], ...] = (
    (TimeoutError, "timed out"),
    (ConnectionRefusedError, "connection refused"),
    (ConnectionError, "connection closed by the server"),  # reset, aborted, RemoteDisconnected
    (socket.gaierror, "host name not resolved"),
    (ssl.SSLCertVerificationError, "TLS certificate could not be verified"),
    (ssl.SSLError, "TLS error"),
    (http.client.HTTPException, "invalid HTTP response"),
)


def _network_reason(exc: BaseException | None) -> str:
    if isinstance(exc, urllib.error.URLError) and isinstance(exc.reason, BaseException):
        exc = exc.reason
    return next((text for kind, text in _NETWORK_REASONS if isinstance(exc, kind)),
                "unclassified error")


# ---------- verification pages ------------------------------------------------
#
# Some sources (DBLP since 2026-10) sit behind Anubis, which answers with an
# HTML verification page instead of the API's JSON. Its no-JavaScript tier is
# a plain refresh to the verifier's own pass-challenge address: wait the stated
# seconds, request that address with the page's cookie, receive an auth cookie,
# repeat the request. That tier is passed here, once per call and host, under
# fixed guardrails; proof-of-work tiers are not, and degrade with a diagnostic.

PASS_PATH = "/.within.website/x/cmd/anubis/api/pass-challenge"
_CHALLENGE_MARKERS = (b'id="anubis_challenge"', b'id="anubis_version"',
                      b"/.within.website/x/cmd/anubis/")
_REFRESH = re.compile(r"\s*(\d{1,3})\s*;\s*url\s*=\s*(\S+)\s*", re.IGNORECASE)
_META_REFRESH = re.compile(rb'<meta\s+http-equiv="?refresh"?\s+content="([^"<>]{1,4096})"',
                           re.IGNORECASE)
# media types a diagnostic may name; anything else is "unknown type", so no
# server-chosen text reaches a message
_KNOWN_MEDIA_TYPES = frozenset({
    "application/json", "application/ld+json", "application/problem+json",
    "application/xml", "text/xml", "application/atom+xml",
    "text/html", "application/xhtml+xml", "text/plain", "application/octet-stream",
})


class _ChallengedHosts(http.cookiejar.DefaultCookiePolicy):
    """Keep and send cookies only for hosts that served a verification page this
    run: every other source's cookies are refused, and a challenged host's
    parent-domain cookie never reaches a sibling host, so nothing tracks
    across sources."""

    def __init__(self) -> None:
        super().__init__()
        self.hosts: set[str] = set()

    def _challenged(self, request) -> bool:
        return urllib.parse.urlsplit(request.get_full_url()).hostname in self.hosts

    def set_ok(self, cookie, request) -> bool:
        return self._challenged(request) and super().set_ok(cookie, request)

    def return_ok(self, cookie, request) -> bool:
        return self._challenged(request) and super().return_ok(cookie, request)


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """The pass step only collects its cookie: its redirect is never followed,
    the original request is repeated instead."""

    def redirect_request(self, *_args, **_kwargs):
        return None


_POLICY = _ChallengedHosts()
_JAR = http.cookiejar.CookieJar(_POLICY)  # memory only, for one process
_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_JAR))
_PASS_OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(_JAR), _NoRedirect())
# hosts whose verification could not be passed: no further waits this run
_UNPASSABLE: set[str] = set()


def reset_session() -> None:
    """Forget cookies, challenged and unpassable hosts, and throttle state (tests)."""
    _JAR.clear()
    _POLICY.hosts.clear()
    _UNPASSABLE.clear()
    _last_call.clear()


@dataclass
class _Call:
    url: str
    headers: dict
    source: str
    may_pass: bool = field(default=True)


@dataclass
class _Reply:
    request: urllib.request.Request
    response: http.client.HTTPResponse
    body: bytes

    @property
    def status(self) -> int:
        return self.response.status

    def json_text(self) -> bytes | None:
        """The body without BOM and leading whitespace, if it starts like JSON."""
        text = self.body.removeprefix(b"\xef\xbb\xbf").lstrip()
        return text if text[:1] in (b"{", b"[") else None


def _get(call: _Call) -> _Reply:
    request = urllib.request.Request(call.url, headers=call.headers)
    _last_call[call.source] = time.monotonic()
    with _OPENER.open(request, timeout=TIMEOUT) as response:
        return _Reply(request, response, response.read(MAX_BODY + 1))


def _fetch_json(call: _Call):
    reply = _get(call)
    host = urllib.parse.urlsplit(call.url).hostname
    if call.may_pass and host not in _UNPASSABLE and _is_challenge(reply):
        call.may_pass = False
        if _pass(reply, call.source):
            reply = _get(call)
        if _is_challenge(reply):
            _UNPASSABLE.add(host)
    return _decode(reply, call.source)


def _refresh(reply: _Reply) -> tuple[int, str] | None:
    """(delay, target) from a Refresh header, else from a meta refresh tag."""
    raw = reply.response.headers.get("Refresh")
    if raw is None:
        match = _META_REFRESH.search(reply.body[:SCAN_LIMIT])
        if match is None:
            return None
        raw = html.unescape(match.group(1).decode("ascii", "replace"))
    match = _REFRESH.fullmatch(raw)
    return (int(match.group(1)), match.group(2)) if match else None


def _pass_url(base: str, target: str) -> str | None:
    """The refresh target, only if it is the verifier on the request's own origin."""
    if not (target.isascii() and target.isprintable()):
        return None
    try:  # brackets, bad ports and the like make the parsers raise
        url = urllib.parse.urljoin(base, target)
        origin, resolved = urllib.parse.urlsplit(base), urllib.parse.urlsplit(url)
        same_origin = ((resolved.scheme, resolved.hostname, resolved.port)
                       == (origin.scheme, origin.hostname, origin.port))
    except ValueError:
        return None
    if not same_origin or "@" in resolved.netloc or resolved.path != PASS_PATH:
        return None
    return url


def _is_challenge(reply: _Reply) -> bool:
    if reply.json_text() is not None:
        return False
    head = reply.body[:SCAN_LIMIT]
    if any(marker in head for marker in _CHALLENGE_MARKERS):
        return True
    refresh = reply.response.headers.get("Refresh")
    match = _REFRESH.fullmatch(refresh) if refresh else None
    try:
        return bool(match) and urllib.parse.urlsplit(match.group(2)).path == PASS_PATH
    except ValueError:
        return False


def _pass(reply: _Reply, source: str) -> bool:
    """Follow a refresh-tier verification page once; True when the verifier
    answered with success or a redirect (whose cookie the jar now holds)."""
    refresh = _refresh(reply)
    # a redirected answer would have its refresh and cookie judged against the
    # original URL rather than the host that sent them
    if refresh is None or reply.response.geturl() != reply.request.full_url:
        return False
    delay, target = refresh
    url = _pass_url(reply.request.full_url, target)
    if url is None or delay > MAX_PASS_DELAY:
        return False
    _POLICY.hosts.add(urllib.parse.urlsplit(url).hostname)
    # the page's own cookie arrived before the page was recognized; keep it now
    _JAR.extract_cookies(reply.response, reply.request)
    time.sleep(delay)
    _last_call[source] = time.monotonic()
    request = urllib.request.Request(url, headers={"User-Agent": user_agent()})
    try:
        with _PASS_OPENER.open(request, timeout=TIMEOUT):
            return True
    except urllib.error.HTTPError as exc:
        exc.close()
        return 300 <= exc.code < 400
    except (OSError, http.client.HTTPException):
        return False


def _media_type(raw: str | None) -> str:
    """The declared media type if it is a known one, never raw header text."""
    if raw is None:
        return "no media type"
    value = raw.split(";", 1)[0].strip().lower()
    return value if value in _KNOWN_MEDIA_TYPES else "unknown type"


def _decode(reply: _Reply, source: str):
    """The JSON document, or a SourceError naming what came back instead."""
    media_type = _media_type(reply.response.headers.get("Content-Type"))

    def unusable(kind: str, what: str, suffix: str = "") -> SourceError:
        return SourceError(f"{source}: API {what} (HTTP {reply.status}, {media_type}){suffix}",
                           kind=kind, status=reply.status, media_type=media_type)

    if len(reply.body) > MAX_BODY:
        raise unusable("unexpected", "response exceeded 16 MiB")
    if (text := reply.json_text()) is not None:
        try:
            return json.loads(text)
        except (ValueError, RecursionError) as exc:
            raise unusable("malformed_json", "returned malformed JSON") from exc
    if _is_challenge(reply):
        raise unusable("challenge", "returned an Anubis browser-verification page",
                       ", not JSON, and automatic verification did not pass")
    if not reply.body.strip():
        raise unusable("unexpected", "returned an empty body")
    if reply.body.lstrip()[:1] == b"<" or media_type in ("text/html", "application/xhtml+xml"):
        raise unusable("unexpected", "returned an HTML page", ", not JSON")
    raise unusable("unexpected", "returned non-JSON content")


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
