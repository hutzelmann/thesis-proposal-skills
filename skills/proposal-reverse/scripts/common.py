#!/usr/bin/env python3
# GENERATED from skills/proposal-lit-search/scripts/common.py
# Edit there, then run scripts/sync_shared.py
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
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

TIMEOUT = 20
RETRIES = 2
BACKOFF_SECONDS = 3.0
RETRY_CODES = (429, 500, 502, 503)
MAX_BODY = 16 * 1024 * 1024  # a larger answer is refused, never read whole
SCAN_LIMIT = 64 * 1024  # verification markers are searched in this prefix only
MAX_PASS_DELAY = 10  # seconds a verification page may ask the script to wait
MAX_XML_DEPTH = 32  # an Atom feed nests four deep; deeper is refused, not parsed
XML_CHUNK = 64 * 1024  # fed at a time, so a refused depth stops the parse early

_last_call: dict[str, float] = {}


class SourceError(Exception):
    """A source is unavailable (network, quota, missing key, unusable answer).

    `http_json` and `http_xml` classify their failures in `kind` — "challenge"
    (a verification page that was not passed), "unexpected" (HTML, other XML or
    other content than the document asked for), "malformed" (a document that
    does not parse; the message names the format), "http", "network" — so an
    orchestrator acts on the cause without parsing the message. Other raisers
    leave `kind` None.
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
    return _request(_Call(_with_params(url, params), headers or {}, source, _JSON), min_interval)


def http_xml(url: str, params: dict | None = None, source: str = "",
             min_interval: float = 1.0, *, root: str) -> ET.Element:
    """GET an XML document (arXiv's Atom feed) under the same rules as
    `http_json`, and return its root element, which must be `root` (Clark
    notation, e.g. "{http://www.w3.org/2005/Atom}feed").

    A body is parsed only when its first markup is that root element, so no
    document type declaration — and no entity definition — reaches the parser.
    """
    return _request(_Call(_with_params(url, params), {}, source, _Xml(root)), min_interval)


def _with_params(url: str, params: dict | None) -> str:
    return f"{url}?{urllib.parse.urlencode(params)}" if params else url


def _request(call: _Call, min_interval: float):
    """Throttle, fetch and retry by cause; every failure leaves as a classified
    SourceError."""
    source = call.source
    wait = _last_call.get(source, 0) + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    call.headers = {"User-Agent": user_agent(), **call.headers}
    last_error: BaseException | None = None
    for attempt in range(RETRIES + 1):
        try:
            return _fetch(call)
        except urllib.error.HTTPError as exc:
            exc.close()  # its reason phrase is the server's text: only the code is kept
            if exc.code not in RETRY_CODES or attempt == RETRIES:
                raise SourceError(f"{source}: HTTP {exc.code}", kind="http",
                                  status=exc.code) from exc
            time.sleep(BACKOFF_SECONDS * (attempt + 1))
        except SourceError as exc:
            # a truncated transfer may succeed on retry; a page the server
            # chose to send instead of the document will not
            if exc.kind != "malformed" or attempt == RETRIES:
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


# ---------- document formats ---------------------------------------------------
#
# A body is parsed only when it starts as the document asked for; such a body
# is never taken for a verification page, whatever its records quote. Anything
# else is classified by `_decode`, and each format names what it saw.

_HTML_TYPES = ("text/html", "application/xhtml+xml")


def _unwrapped(body: bytes) -> bytes:
    """The body without a UTF-8 BOM and leading whitespace."""
    return body.removeprefix(b"\xef\xbb\xbf").lstrip()


class _OtherDocument(Exception):
    """Well-formed, but another document than the one asked for."""


class _Json:
    name = "JSON"

    @staticmethod
    def start(body: bytes) -> bytes | None:
        text = _unwrapped(body)
        return text if text[:1] in (b"{", b"[") else None

    @staticmethod
    def parse(text: bytes):
        return json.loads(text)

    @staticmethod
    def other(body: bytes, media_type: str) -> tuple[str, str]:
        if body.lstrip()[:1] == b"<" or media_type in _HTML_TYPES:
            return "returned an HTML page", ", not JSON"
        return "returned non-JSON content", ""


# the first start tag's local name, any prefix; matched on a bounded prefix only
_START_TAG = re.compile(rb"<(?:[A-Za-z_][\w.-]{0,63}:)?([A-Za-z_][\w.-]{0,63})[\s/>]")


class _Xml:
    name = "XML"

    def __init__(self, root: str) -> None:
        self.root = root
        self.local = root.rpartition("}")[2].encode()

    @staticmethod
    def _first_markup(body: bytes) -> bytes:
        """The body from its first markup, past an XML declaration — one that
        holds no markup of its own, as a real declaration never does."""
        text = _unwrapped(body)
        end = text.find(b"?>", 0, 1024) if text.startswith(b"<?xml") else -1
        if end >= 0 and b"<" not in text[1:end]:
            return text[end + 2:].lstrip()
        return text

    def start(self, body: bytes) -> bytes | None:
        """The body, if its first markup is the root element's start tag: a
        document type declaration would precede it, so none gets through."""
        match = _START_TAG.match(self._first_markup(body)[:256])
        return _unwrapped(body) if match and match.group(1) == self.local else None

    def parse(self, text: bytes) -> ET.Element:
        """The document, built in chunks so that a depth past MAX_XML_DEPTH
        ends the parse within one chunk: expat keeps its own tag stack, which
        a hostile depth would otherwise grow by hundreds of MiB."""
        parser = ET.XMLParser(target=_DepthLimited())
        try:
            for offset in range(0, len(text), XML_CHUNK):
                parser.feed(text[offset:offset + XML_CHUNK])
            document = parser.close()
        except ET.ParseError as exc:  # a SyntaxError, not a ValueError
            raise ValueError("malformed XML") from exc
        if document.tag != self.root:
            raise _OtherDocument
        return document

    def other(self, body: bytes, media_type: str) -> tuple[str, str]:
        head = self._first_markup(body)[:16].lower()
        if head.startswith((b"<!doctype html", b"<html")) or media_type in _HTML_TYPES:
            return "returned an HTML page", ", not XML"
        if head[:1] == b"<":
            return "returned XML other than the expected document", ""
        return "returned non-XML content", ""


class _DepthLimited:
    """An XMLParser target: the standard tree builder, refusing nesting deeper
    than MAX_XML_DEPTH with a ValueError (classified as malformed)."""

    def __init__(self) -> None:
        self.builder = ET.TreeBuilder()
        self.depth = 0

    def start(self, tag: str, attrs: dict) -> ET.Element:
        self.depth += 1
        if self.depth > MAX_XML_DEPTH:
            raise ValueError("XML nested too deep")
        return self.builder.start(tag, attrs)

    def end(self, tag: str) -> ET.Element:
        self.depth -= 1
        return self.builder.end(tag)

    def data(self, data: str) -> None:
        self.builder.data(data)

    def close(self) -> ET.Element:
        return self.builder.close()


_JSON = _Json()


@dataclass
class _Call:
    url: str
    headers: dict
    source: str
    fmt: _Json | _Xml
    may_pass: bool = field(default=True)


@dataclass
class _Reply:
    request: urllib.request.Request
    response: http.client.HTTPResponse
    body: bytes
    fmt: _Json | _Xml

    @property
    def status(self) -> int:
        return self.response.status

    def document(self) -> bytes | None:
        """The body to parse, if it starts as the document asked for."""
        return self.fmt.start(self.body)


def _get(call: _Call) -> _Reply:
    request = urllib.request.Request(call.url, headers=call.headers)
    _last_call[call.source] = time.monotonic()
    with _OPENER.open(request, timeout=TIMEOUT) as response:
        return _Reply(request, response, response.read(MAX_BODY + 1), call.fmt)


def _fetch(call: _Call):
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
    if reply.document() is not None:  # a record quoting the markup is still data
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
    """The document, or a SourceError naming what came back instead."""
    fmt = reply.fmt
    media_type = _media_type(reply.response.headers.get("Content-Type"))

    def unusable(kind: str, what: str, suffix: str = "") -> SourceError:
        return SourceError(f"{source}: API {what} (HTTP {reply.status}, {media_type}){suffix}",
                           kind=kind, status=reply.status, media_type=media_type)

    if len(reply.body) > MAX_BODY:
        raise unusable("unexpected", "response exceeded 16 MiB")
    if (text := reply.document()) is not None:
        try:
            return fmt.parse(text)
        except _OtherDocument:
            raise unusable("unexpected",
                           f"returned {fmt.name} other than the expected document") from None
        except (ValueError, RecursionError) as exc:
            raise unusable("malformed", f"returned malformed {fmt.name}") from exc
    if _is_challenge(reply):
        raise unusable("challenge", "returned an Anubis browser-verification page",
                       f", not {fmt.name}, and automatic verification did not pass")
    if not reply.body.strip():
        raise unusable("unexpected", "returned an empty body")
    raise unusable("unexpected", *fmt.other(reply.body, media_type))


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


# ---------- output streams -------------------------------------------------------

def utf8_output() -> None:
    """Write stdout and stderr as UTF-8, whatever encoding the platform chose.

    A Windows pipe is encoded in the ANSI code page (cp1252 in Western Europe),
    so printing a character outside it raised UnicodeEncodeError. Each stream
    keeps its error handler, which reconfigure() would otherwise reset to
    strict, and its newline handling; a stream without reconfigure() (a
    caller's StringIO, or None without a console) is left alone. The same in
    every script family (tests/unit/test_utf8_output.py).
    """
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors=stream.errors)
