"""Model currency: compare the registry's pins against OpenRouter's public catalog.

For every roster pin and role in harness/models.toml, derive its version line
(the ID with its first version number wildcarded and a trailing snapshot token
ignored), find the newest member of that line in the catalog, and report what is
newer, missing, expiring or repriced. Prices come from the model vendor's own
endpoint at its standard tier (`GET /api/v1/models/<id>/endpoints`). New lines in
a vendor namespace the registry uses are reported, never written.

Standard library only, so CI runs it with plain `python3`; no key, no credential.

Usage:
    uv run poe models                       # human-readable findings
    python3 harness/model_currency.py --json
    python3 harness/model_currency.py --write --pr-body body.md   # the weekly bump PR
    python3 harness/model_currency.py --catalog models.json --endpoints endpoints/  # replay

Exit status: 0 current (or only informational findings), 1 actionable findings,
2 currency unknown (catalog or endpoint unreachable or malformed; nothing written),
3 the write mode could not apply an edit to the registry (nothing written).
"""

from __future__ import annotations

import argparse
import http.client
import json
import re
import subprocess
import sys
import tomllib
import urllib.request
from collections.abc import Callable, Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path

import support

HARNESS = Path(__file__).resolve().parent
REGISTRY = HARNESS / "models.toml"
CATALOG_URL = "https://openrouter.ai/api/v1/models"
ENDPOINTS_URL = "https://openrouter.ai/api/v1/models/{model_id}/endpoints"
TIMEOUT = 30.0
GATE_TIMEOUT = 5.0
PRICE_TOLERANCE = 0.005  # relative; first-party prices move in discrete steps
SKIPPED_TIERS = frozenset({"fast", "flex"})  # above and below the standard tier

KINDS = (
    "newer", "missing", "expiring", "price_drift", "no_vendor_endpoint",
    "held", "untracked", "new_line",
)
INFORMATIONAL = frozenset({"held", "untracked", "new_line"})
HELD_ROLES = ("judge", "persona")
# The one price-field list: registry key, endpoint pricing key, and whether the
# endpoint must list it. An optional price the endpoint omits is left out of the
# registry, where the parser defaults it to the input price. Every comparison,
# report and write below iterates this list.
PRICE_FIELDS = (
    ("input_price", "prompt", True),
    ("output_price", "completion", True),
    ("cache_read_price", "input_cache_read", False),
    ("cache_write_price", "input_cache_write", False),
)
PRICE_LABEL = "in/out/cache-read/cache-write"

_SNAPSHOT_RE = re.compile(r"-(\d{8}|\d{6}|\d{4}|\d{2}-\d{2})$")
_VERSION_RE = re.compile(r"\d+(?:\.\d+)*")
_DATE_SUFFIX_RE = re.compile(r"-\d{8}$")
_DIGIT_DASH_RE = re.compile(r"(?<=\d)-(?=\d)")
_DIGIT_DOT_RE = re.compile(r"(?<=\d)\.(?=\d)")

Fetch = Callable[[str, float], object]


class CurrencyUnknown(Exception):
    """The catalog or an endpoint list could not be read or was malformed."""


@dataclass(frozen=True)
class Finding:
    subject: str  # roster:<id> | role:<name> | role_price:<id> | line:<glob>
    kind: str  # one of KINDS
    pinned: str
    proposed: str = ""
    detail: str = ""
    writable: bool = False


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    created: int
    expiration_date: str | None = None


@dataclass(frozen=True)
class Quote:
    """$/Mtok at one endpoint; an optional price is None when the endpoint has none."""

    input_price: float
    output_price: float
    cache_read_price: float | None
    endpoint: str
    cache_write_price: float | None = None

    def prices(self) -> dict[str, float | None]:
        return {key: getattr(self, key) for key, _, _ in PRICE_FIELDS}


@dataclass(frozen=True)
class Edit:
    kind: str  # roster | role | role_price
    target: str  # roster: outgoing ID; role: role name; role_price: model ID
    new_id: str = ""
    quote: Quote | None = None


@dataclass(frozen=True)
class Result:
    findings: tuple[Finding, ...]
    edits: tuple[Edit, ...]

    @property
    def exit_code(self) -> int:
        return int(any(f.kind not in INFORMATIONAL for f in self.findings))

    @property
    def alerts(self) -> list[str]:
        """Pins that are missing or expiring with no writable successor."""
        writable = {
            f.subject for f in self.findings if f.writable and f.kind in ("newer", "missing")
        }
        return sorted({
            f.subject for f in self.findings
            if f.kind in ("missing", "expiring") and f.subject not in writable
        })


# ---------- IO ----------------------------------------------------------------


def fetch_json(url: str, timeout: float) -> object:
    """The one network call: an unauthenticated GET of a public catalog URL."""
    request = urllib.request.Request(url, headers={"User-Agent": "thesis-proposal-skills"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def _fetch(fetch: Fetch | None) -> Fetch:
    # the global name is looked up at call time, never bound as a default, so a
    # substitute installed on the module (the L0 conftest fixture) reaches every path
    return fetch if fetch is not None else fetch_json


def replay_fetch(catalog: Path, endpoints: Path | None = None) -> Fetch:
    """A fetch that serves a recorded snapshot: the catalog file for the catalog
    URL, `<vendor>__<slug>.json` under `endpoints` for an endpoint URL."""
    prefix, suffix = ENDPOINTS_URL.split("{model_id}")

    def fetch(url: str, timeout: float) -> object:
        if url == CATALOG_URL:
            return json.loads(catalog.read_text(encoding="utf-8"))
        if not (url.startswith(prefix) and url.endswith(suffix)):
            raise OSError(f"a replay serves no {url}")
        if endpoints is None:  # catalog replayed, endpoint prices read live
            return fetch_json(url, timeout)
        model_id = url[len(prefix):-len(suffix)]
        path = endpoints / (model_id.replace("/", "__") + ".json")
        if not path.is_file():
            raise OSError(f"no recorded endpoints for {model_id} ({path.name})")
        return json.loads(path.read_text(encoding="utf-8"))

    return fetch


def _read(fetch: Fetch, url: str, timeout: float) -> object:
    try:
        return fetch(url, timeout)
    # URLError and JSONDecodeError included; a truncated body (IncompleteRead)
    # is an HTTPException, which is neither
    except (OSError, ValueError, http.client.HTTPException) as exc:
        raise CurrencyUnknown(f"{url}: {exc}") from exc


# ---------- identifiers and lines -----------------------------------------------


def catalog_id(model_id: str) -> str:
    """The catalog spelling of a registry ID: no `openrouter/` routing prefix,
    and a subscription-CLI ID (`claude-<family>-<major>-<minor>[-<yyyymmdd>]`)
    mapped to its catalog form (`anthropic/claude-<family>-<major>.<minor>`)."""
    bare = model_id.removeprefix("openrouter/")
    if "/" in bare or not bare.startswith("claude-"):
        return bare
    return "anthropic/" + _DIGIT_DASH_RE.sub(".", _DATE_SUFFIX_RE.sub("", bare))


def subscription_id(catalog: str) -> str:
    """The subscription CLI's spelling of an anthropic catalog ID."""
    return _DIGIT_DOT_RE.sub("-", catalog.removeprefix("anthropic/"))


def split_snapshot(name: str) -> tuple[str, str]:
    match = _SNAPSHOT_RE.search(name)
    if match is None:
        return name, ""
    return name[: match.start()], match.group(1)


def derive_line(cid: str) -> str | None:
    """`vendor/name` with its first version number wildcarded, snapshot dropped."""
    vendor, _, name = cid.rpartition("/")
    base, _ = split_snapshot(name)
    match = _VERSION_RE.search(base)
    if match is None:
        return None
    return f"{vendor}/{base[: match.start()]}*{base[match.end():]}"


def _line_regex(line: str) -> re.Pattern[str]:
    head, _, tail = line.partition("*")
    return re.compile(f"^{re.escape(head)}(\\d+(?:\\.\\d+)*){re.escape(tail)}$")


def _eligible(cid: str) -> bool:
    return ":" not in cid and not cid.startswith("~") and "/~" not in cid


def _version(cid: str, pattern: re.Pattern[str]) -> tuple[int, ...] | None:
    vendor, _, name = cid.rpartition("/")
    match = pattern.match(f"{vendor}/{split_snapshot(name)[0]}")
    if match is None:
        return None
    return tuple(int(part) for part in match.group(1).split("."))


def line_members(line: str, catalog: dict[str, CatalogEntry]) -> list[CatalogEntry]:
    pattern = _line_regex(line)
    return [
        e for cid, e in catalog.items() if _eligible(cid) and _version(cid, pattern) is not None
    ]


def _order(entry: CatalogEntry, pattern: re.Pattern[str]) -> tuple[tuple[int, ...], int]:
    return (_version(entry.id, pattern) or (), entry.created)


def newest_in_line(line: str, catalog: dict[str, CatalogEntry]) -> CatalogEntry | None:
    pattern = _line_regex(line)
    members = line_members(line, catalog)
    return max(members, key=lambda e: _order(e, pattern)) if members else None


def assess(
    cid: str, line: str | None, catalog: dict[str, CatalogEntry]
) -> tuple[str | None, CatalogEntry | None]:
    """("missing" | "newer" | None, the proposed successor) for one pin. A pin
    that does not fit its (overridden) line sorts below every member."""
    newest = newest_in_line(line, catalog) if line else None
    entry = catalog.get(cid)
    if entry is None:
        return "missing", newest
    if newest is not None and line is not None and newest.id != cid:
        pattern = _line_regex(line)
        if _order(newest, pattern) > _order(entry, pattern):
            return "newer", newest
    return None, None


def is_downgrade(cid: str, line: str | None, proposed: CatalogEntry | None) -> bool:
    """A missing pin's proposed successor carries a lower version than the pin.
    Writing it would move the roster backwards, so it is never writable. A pin
    that does not fit its (overridden) line has no version and never compares
    higher."""
    if proposed is None or line is None:
        return False
    pattern = _line_regex(line)
    pinned = _version(cid, pattern)
    return pinned is not None and (_version(proposed.id, pattern) or ()) < pinned


def _line_for(model: support.Model, cid: str) -> str | None:
    if model.track is False:
        return None
    return model.track if isinstance(model.track, str) else derive_line(cid)


# ---------- catalog and prices ------------------------------------------------


def parse_catalog(raw: object) -> dict[str, CatalogEntry]:
    data = raw.get("data") if isinstance(raw, dict) else None
    if not isinstance(data, list) or not data:
        raise CurrencyUnknown("malformed catalog: no `data` list")
    entries = {}
    for item in data:
        if not isinstance(item, dict):
            raise CurrencyUnknown(f"malformed catalog entry: {item!r}")
        cid, created, expires = item.get("id"), item.get("created"), item.get("expiration_date")
        if not isinstance(cid, str) or not isinstance(created, int | float) or not (
            expires is None or isinstance(expires, str)
        ):
            raise CurrencyUnknown(f"malformed catalog entry: {str(item)[:120]}")
        entries[cid] = CatalogEntry(cid, int(created), expires or None)
    return entries


def _per_mtok(value: object) -> float:
    try:
        return float(Decimal(str(value)) * 1_000_000)
    except InvalidOperation as exc:
        raise CurrencyUnknown(f"malformed endpoint price {value!r}") from exc


def _endpoint_list(raw: object) -> list[dict]:
    data = raw.get("data") if isinstance(raw, dict) else None
    endpoints = data.get("endpoints") if isinstance(data, dict) else None
    if not isinstance(endpoints, list) or not all(isinstance(e, dict) for e in endpoints):
        raise CurrencyUnknown("malformed endpoint list")
    return endpoints


def _vendor_candidates(endpoints: list[dict], vendor: str, price_endpoint: str) -> list[dict]:
    if price_endpoint:
        return [e for e in endpoints if e.get("tag") == price_endpoint]
    exact = [e for e in endpoints if e.get("tag") == vendor]
    if exact:
        return exact
    tiered = [
        e for e in endpoints
        if str(e.get("tag", "")).startswith(vendor + "/")
        and str(e.get("tag")).split("/", 1)[1] not in SKIPPED_TIERS
    ]
    return tiered if len(tiered) == 1 else []  # one quantization variant, never a guess


def vendor_quote(raw: object, vendor: str, price_endpoint: str = "") -> Quote | None:
    """The vendor's own endpoint at its standard tier, or the named endpoint."""
    candidates = _vendor_candidates(_endpoint_list(raw), vendor, price_endpoint)
    if not candidates:
        return None
    endpoint = candidates[0]
    pricing = endpoint.get("pricing")
    required = [api for _, api, needed in PRICE_FIELDS if needed]
    if not isinstance(pricing, dict) or any(api not in pricing for api in required):
        raise CurrencyUnknown(f"malformed pricing on endpoint {endpoint.get('tag')!r}")
    prices = {
        key: _per_mtok(pricing[api]) if needed or pricing.get(api) is not None else None
        for key, api, needed in PRICE_FIELDS
    }
    return Quote(endpoint=str(endpoint.get("tag")), **prices)


def _effective(quote: Quote) -> tuple[float, ...]:
    """The quote as the registry would read it: an omitted price is the input price."""
    return tuple(quote.input_price if p is None else p for p in quote.prices().values())


def _current(current: support.Price | support.Model | support.RolePrice) -> tuple[float, ...]:
    return tuple(getattr(current, key) for key, _, _ in PRICE_FIELDS)


def drifted(current: support.Price | support.Model | support.RolePrice, quote: Quote) -> bool:
    pairs = zip(_current(current), _effective(quote), strict=True)
    return any(abs(have - want) > PRICE_TOLERANCE * max(abs(want), 1e-12) for have, want in pairs)


def _num(value: float) -> str:
    return f"{value:g}"


def _price_text(prices: Iterable[float | None]) -> str:
    return "/".join("—" if p is None else _num(p) for p in prices)


def _price_change(current, quote: Quote | None) -> str:
    before = _price_text(_current(current))
    if quote is None:
        return f"{PRICE_LABEL} {before} $/Mtok kept (no vendor endpoint)"
    after = _price_text(_effective(quote))
    return f"{PRICE_LABEL} {before} → {after} $/Mtok ({quote.endpoint} endpoint)"


# ---------- the check -----------------------------------------------------------


@dataclass
class _Run:
    registry: support.Registry
    catalog: dict[str, CatalogEntry]
    fetch: Fetch
    timeout: float
    findings: list[Finding]
    edits: list[Edit]

    def quote(self, cid: str, price_endpoint: str) -> Quote | None:
        raw = _read(self.fetch, ENDPOINTS_URL.format(model_id=cid), self.timeout)
        return vendor_quote(raw, cid.split("/", 1)[0], price_endpoint)

    def add(self, *args, **kwargs) -> None:
        self.findings.append(Finding(*args, **kwargs))


def _expiry(run: _Run, subject: str, model_id: str, cid: str) -> None:
    entry = run.catalog.get(cid)
    if entry is not None and entry.expiration_date:
        run.add(subject, "expiring", model_id, detail=f"expires {entry.expiration_date}")


def _successor(run: _Run, subject: str, model_id: str, cid: str, line: str | None) -> str:
    """Report newer/missing for one pin; return the successor's catalog ID or ""."""
    kind, newest = assess(cid, line, run.catalog)
    if kind is None:
        return ""
    proposed = newest.id if newest is not None else ""
    if kind == "missing" and not proposed:
        detail = "absent from the catalog and no member of its line is listed"
        run.add(subject, "missing", model_id, detail=detail)
        return ""
    if kind == "missing" and is_downgrade(cid, line, newest):
        run.add(subject, "missing", model_id,
                detail=f"absent from the catalog; the newest listed member of its line, "
                f"{proposed}, is an older version and is not proposed")
        return ""
    detail = "absent from the catalog" if kind == "missing" else f"newer in {line}"
    run.add(subject, kind, model_id, proposed, detail, writable=True)
    return proposed


def _check_roster_entry(run: _Run, model: support.Model) -> None:
    cid = catalog_id(model.id)
    subject = f"roster:{model.id}"
    if model.track is False:
        run.add(subject, "untracked", model.id, detail="track = false")
    successor = _successor(run, subject, model.id, cid, _line_for(model, cid))
    _expiry(run, subject, model.id, cid)
    carried = successor or (cid if cid in run.catalog else "")
    if not carried:
        return
    quote = run.quote(carried, model.price_endpoint)
    if quote is None:
        run.add(subject, "no_vendor_endpoint", model.id, carried,
                f"no {model.price_endpoint or cid.split('/', 1)[0]} endpoint at the standard "
                "tier; the price stays as it is")
    if successor:
        new_id = model.id.removesuffix(cid) + successor
        _amend_detail(run, subject, _price_change(model, quote))
        run.edits.append(Edit("roster", model.id, new_id, quote))
        _follow_roster_move(run, model, cid, new_id)
    elif quote is not None and drifted(model, quote):
        run.add(subject, "price_drift", model.id, detail=_price_change(model, quote),
                writable=True)
        run.edits.append(Edit("roster", model.id, model.id, quote))


def _amend_detail(run: _Run, subject: str, extra: str) -> None:
    for i, f in enumerate(run.findings):
        if f.subject == subject and f.writable and f.kind in ("newer", "missing"):
            run.findings[i] = Finding(f.subject, f.kind, f.pinned, f.proposed,
                                      f"{f.detail}; {extra}", f.writable)


def _follow_roster_move(run: _Run, model: support.Model, cid: str, new_id: str) -> None:
    """The smoke role follows its roster row; a held role naming the outgoing ID
    keeps it, priced by a [role_prices] entry written in the same edit."""
    roles = run.registry.roles
    if roles.smoke == model.id:
        run.edits.append(Edit("role", "smoke", new_id))
    if model.id in (roles.judge, roles.persona) and model.id not in run.registry.role_prices:
        held = run.quote(cid, model.price_endpoint) if cid in run.catalog else None
        if held is None:  # no vendor endpoint: carry the row's own price over
            held = Quote(model.input_price, model.output_price, model.cache_read_price,
                         model.price_endpoint, model.cache_write_price)
        run.edits.append(Edit("role_price", model.id, model.id, held))


def _check_held_roles(run: _Run) -> None:
    written = {e.target for e in run.edits if e.kind == "role_price"}
    for name in HELD_ROLES:
        model_id = getattr(run.registry.roles, name)
        cid = catalog_id(model_id)
        subject = f"role:{name}"
        kind, newest = assess(cid, derive_line(cid), run.catalog)
        _expiry(run, subject, model_id, cid)
        if kind == "missing":
            run.add(subject, "missing", model_id, newest.id if newest else "",
                    "absent from the catalog; held roles move only with a re-baseline")
        elif kind == "newer":
            detail = "held until a deliberate full re-baseline moves it"
            if model_id in written:
                detail += f'; [role_prices."{model_id}"] written to keep it priced'
            run.add(subject, "held", model_id, newest.id, detail)


def subscription_catalog_id(model_id: str, catalog: dict[str, CatalogEntry]) -> str:
    """catalog_id, except that a dated subscription ID keeps its date when the
    catalog lists that dated snapshot: compared as its undated sibling, a dated
    pin would be outranked by itself and re-proposed every week."""
    cid = catalog_id(model_id)
    dated = _DATE_SUFFIX_RE.search(model_id)
    if "/" not in model_id and dated and cid + dated.group(0) in catalog:
        return cid + dated.group(0)
    return cid


def _check_dev_judge(run: _Run) -> None:
    model_id = run.registry.roles.dev_judge
    cid = subscription_catalog_id(model_id, run.catalog)
    subject = "role:dev_judge"
    line = derive_line(cid)
    kind, newest = assess(cid, line, run.catalog)
    _expiry(run, subject, model_id, cid)
    if kind is None:
        return
    if newest is None or (kind == "missing" and is_downgrade(cid, line, newest)):
        run.add(subject, "missing", model_id,
                detail="absent from the catalog, and no member of its line at the same or a "
                "higher version is listed")
        return
    proposed = subscription_id(newest.id) if cid.startswith("anthropic/") else newest.id
    if proposed == model_id:
        return  # the pin itself in another spelling: nothing to move
    run.add(subject, kind, model_id, proposed,
            "subscription role: confirm the CLI resolves the new ID to itself before merging",
            writable=True)
    run.edits.append(Edit("role", "dev_judge", proposed))


def _check_role_prices(run: _Run) -> None:
    for model_id, entry in run.registry.role_prices.items():
        cid = catalog_id(model_id)
        if cid not in run.catalog:
            continue  # the held role reports it missing
        subject = f"role_price:{model_id}"
        quote = run.quote(cid, entry.price_endpoint)
        if quote is None:
            run.add(subject, "no_vendor_endpoint", model_id,
                    detail="no vendor endpoint at the standard tier; the price stays")
        elif drifted(entry, quote):
            run.add(subject, "price_drift", model_id, detail=_price_change(entry, quote),
                    writable=True)
            run.edits.append(Edit("role_price", model_id, model_id, quote))


def _known_lines(registry: support.Registry) -> set[str]:
    known = set()
    for m in registry.models:
        known.add(derive_line(catalog_id(m.id)))
        if isinstance(m.track, str):
            known.add(m.track)
    for name in support.MODEL_ROLES:
        known.add(derive_line(catalog_id(getattr(registry.roles, name))))
    known.update(derive_line(catalog_id(mid)) for mid in registry.role_prices)
    return {line for line in known if line}


def new_line_findings(
    registry: support.Registry, catalog: dict[str, CatalogEntry]
) -> list[Finding]:
    """Lines in a registry vendor namespace that no entry or role derives, with a
    member created after `lines_reviewed_as_of`. Informational, never written."""
    reviewed = registry.lines_reviewed_as_of or date.min
    cutoff = datetime(reviewed.year, reviewed.month, reviewed.day, tzinfo=UTC) + timedelta(days=1)
    known = _known_lines(registry)
    namespaces = {line.split("/", 1)[0] for line in known}
    groups: dict[str, list[CatalogEntry]] = {}
    for cid, entry in catalog.items():
        line = derive_line(cid) if _eligible(cid) else None
        if line and line not in known and line.split("/", 1)[0] in namespaces:
            groups.setdefault(line, []).append(entry)
    found = []
    for line, members in sorted(groups.items()):
        if not any(e.created >= cutoff.timestamp() for e in members):
            continue
        newest = max(members, key=lambda e: _order(e, _line_regex(line)))
        found.append(Finding(
            f"line:{line}", "new_line", "", newest.id,
            f"{len(members)} member(s), not in the registry; newest created "
            f"{datetime.fromtimestamp(newest.created, UTC).date().isoformat()}",
        ))
    return found


def check(
    registry: support.Registry,
    catalog: dict[str, CatalogEntry],
    fetch: Fetch | None = None,
    timeout: float = TIMEOUT,
) -> Result:
    """Every finding for the registry against one catalog snapshot, plus the
    edits a write applies. Raises CurrencyUnknown when an endpoint list cannot
    be read."""
    run = _Run(registry, catalog, _fetch(fetch), timeout, [], [])
    for model in registry.models:
        _check_roster_entry(run, model)
    _check_held_roles(run)
    _check_dev_judge(run)
    _check_role_prices(run)
    run.findings.extend(new_line_findings(registry, catalog))
    return Result(tuple(run.findings), tuple(run.edits))


# ---------- the registry edit -----------------------------------------------------

_HEADER_RE = re.compile(r"^\s*\[\[?\s*([^\]]+?)\s*\]\]?\s*(#.*)?$")


def _key_re(key: str) -> re.Pattern[str]:
    return re.compile(rf"^(\s*{re.escape(key)}\s*=\s*)(.*?)(\s+#.*)?$")


def _table_path(header: str) -> tuple[str, ...]:
    """A table header's key path however it is quoted or spaced, so
    `[role_prices."x"]` and `[ role_prices . 'x' ]` name the same table."""
    try:
        node: object = tomllib.loads(f"[{header}]\n")
    except tomllib.TOMLDecodeError:
        return (header,)
    path = []
    while isinstance(node, dict) and len(node) == 1:
        key, node = next(iter(node.items()))
        path.append(key)
    return tuple(path)


def _blocks(lines: list[str]) -> list[tuple[tuple[str, ...], int, int]]:
    """(header key path, first line, end line) per table; the top level is ()."""
    starts = [
        (_table_path(m.group(1)), i) for i, line in enumerate(lines)
        if (m := _HEADER_RE.match(line))
    ]
    bounds = [((), 0), *starts]
    return [
        (path, start, bounds[k + 1][1] if k + 1 < len(bounds) else len(lines))
        for k, (path, start) in enumerate(bounds)
    ]


def _value(text: str) -> object:
    """A TOML value's meaning, whichever string quoting spells it."""
    try:
        return tomllib.loads(f"v = {text}\n")["v"]
    except tomllib.TOMLDecodeError:
        return None


def _set_key(lines: list[str], start: int, end: int, key: str, value: str | None,
             after: str) -> int:
    """Set `key = value` inside lines[start:end], keeping any trailing comment;
    None deletes the key; a missing key is inserted after `after`. Returns the
    change in line count, so a caller can keep its block end current."""
    pattern = _key_re(key)
    for i in range(start, end):
        match = pattern.match(lines[i])
        if match:
            if value is None:
                del lines[i]
                return -1
            lines[i] = match.group(1) + value + (match.group(3) or "")
            return 0
    if value is None:
        return 0
    anchor = _key_re(after)
    at = next((i + 1 for i in range(start, end) if after and anchor.match(lines[i])), end)
    lines.insert(at, f"{key} = {value}")
    return 1


def _set_prices(lines: list[str], start: int, end: int, quote: Quote) -> None:
    """Every PRICE_FIELDS key in field order; an omitted optional price is deleted,
    and a new key goes after the last price key the block keeps."""
    anchor = "id"
    for key, value in quote.prices().items():
        end += _set_key(lines, start, end, key, None if value is None else repr(value), anchor)
        if value is not None:
            anchor = key


def _model_block(lines: list[str], model_id: str) -> tuple[int, int]:
    for path, start, end in _blocks(lines):
        if path != ("models",):
            continue
        for i in range(start, end):
            match = _key_re("id").match(lines[i])
            if match and _value(match.group(2)) == model_id:
                return start, end
    raise ValueError(f"no [[models]] block with id {model_id!r}")


def _apply_roster(lines: list[str], edit: Edit) -> None:
    start, end = _model_block(lines, edit.target)
    if edit.new_id != edit.target:
        _set_key(lines, start, end, "id", json.dumps(edit.new_id), "")
    if edit.quote is not None:
        _set_prices(lines, start, end, edit.quote)


def _apply_role(lines: list[str], edit: Edit) -> None:
    for path, start, end in _blocks(lines):
        if path == ("roles",):
            _set_key(lines, start, end, edit.target, json.dumps(edit.new_id), "")
            return
    raise ValueError("no [roles] table")


def _apply_role_price(lines: list[str], edit: Edit) -> None:
    header = f"role_prices.{json.dumps(edit.target)}"
    blocks = _blocks(lines)
    for path, start, end in blocks:
        if path == ("role_prices", edit.target):
            _set_prices(lines, start, end, edit.quote)
            return
    roles_end = next((end for path, _, end in blocks if path == ("roles",)), None)
    if roles_end is None:
        raise ValueError("no [roles] table")
    at = roles_end
    while at > 0 and not lines[at - 1].strip():
        at -= 1
    q = edit.quote
    block = [
        "",
        f"[{header}]   # held role, off the roster; refreshed weekly",
        *(f"{key} = {value!r}" for key, value in q.prices().items() if value is not None),
    ]
    if q.endpoint and q.endpoint != edit.target.removeprefix("openrouter/").split("/", 1)[0]:
        block.append(f"price_endpoint = {json.dumps(q.endpoint)}")
    lines[at:at] = block


def apply_edits(text: str, edits: Iterable[Edit], as_of: date) -> str:
    """The registry text with every edit applied line by line, so comments and
    notes survive. No edit, no change: prices_as_of moves only with a price."""
    edits = list(edits)
    if not edits:
        return text
    lines = text.splitlines()
    appliers = {"roster": _apply_roster, "role": _apply_role, "role_price": _apply_role_price}
    for edit in edits:
        appliers[edit.kind](lines, edit)
    top_start, top_end = _blocks(lines)[0][1:]
    _set_key(lines, top_start, top_end, "prices_as_of", as_of.isoformat(), "")
    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


# ---------- output ----------------------------------------------------------------


def render_text(result: Result, source: str) -> str:
    out = [f"model currency vs {source}"]
    for f in result.findings:
        arrow = f" → {f.proposed}" if f.proposed else ""
        tag = " (informational)" if f.kind in INFORMATIONAL else (
            " [writable]" if f.writable else "")
        out.append(f"  {f.kind:18s} {f.subject}: {f.pinned or '—'}{arrow}{tag}")
        if f.detail:
            out.append(f"  {'':18s}   {f.detail}")
    actionable = sum(f.kind not in INFORMATIONAL for f in result.findings)
    out.append(f"{actionable} actionable, {len(result.findings) - actionable} informational")
    for subject in result.alerts:
        out.append(f"ALERT: {subject} is missing or expiring with no writable successor")
    return "\n".join(out)


def render_json(result: Result, source: str, fetched_at: str) -> dict:
    return {
        "source": source,
        "fetched_at": fetched_at,
        "findings": [asdict(f) for f in result.findings],
        "alerts": result.alerts,
    }


def _bullets(findings: Iterable[Finding]) -> list[str]:
    lines = []
    for f in findings:
        arrow = f" → `{f.proposed}`" if f.proposed else ""
        detail = f" — {f.detail}" if f.detail else ""
        lines.append(f"- **{f.kind}** `{f.subject}`: `{f.pinned or '—'}`{arrow}{detail}")
    return lines


def render_pr_body(result: Result, as_of: date, stale_files: list[str]) -> str:
    actionable = [f for f in result.findings if f.kind not in INFORMATIONAL]
    held = [f for f in result.findings if f.kind in ("held", "untracked")]
    lines_found = [f for f in result.findings if f.kind == "new_line"]
    role_prices = [e.target for e in result.edits if e.kind == "role_price"]
    dev_judge = next((e.new_id for e in result.edits if e.target == "dev_judge"), "")
    body = [
        f"Weekly model-currency bump from OpenRouter's public catalog ({as_of.isoformat()}).",
        "",
        "## Findings",
        *(_bullets(actionable) or ["- none"]),
        "",
        "## Held roles",
        "The matrix judge and the dialogue persona are held until a deliberate full "
        "re-baseline moves them: changing either invalidates every rubric-counted cell, so "
        "the check reports a newer model in their line and never rewrites them.",
        *(_bullets(held) or ([] if role_prices else ["- none reported this run"])),
        *(f'- `[role_prices."{mid}"]` written so the held role stays priced after its '
          "roster row moved" for mid in role_prices),
        "",
        "## New lines (a roster decision)",
        *(_bullets(lines_found) or ["- none"]),
        "Never written by this workflow. Clear one by adding a roster entry for the line, "
        "or by moving `lines_reviewed_as_of` in `harness/models.toml` by hand.",
        "",
        "## Before merging",
        "1. Regenerate the shipped verdicts on a machine that holds the eval logs and push "
        "the result to this branch: `uv run poe report`, then `python3 scripts/sync_shared.py`. "
        "`logs/` is gitignored, so CI cannot do it, and the shipped-verdict test stays red "
        "until it is done.",
        "2. New IDs render as untested until a cost-gated matrix run (`uv run poe matrix`) "
        "measures them; its estimate is shown first and waits for approval.",
    ]
    if dev_judge:
        body.append(
            f"3. Subscription role bump: check for free that `claude -p --model {dev_judge} "
            '--output-format json "ok"` reports that same ID in `modelUsage`.')
    if stale_files:
        body += ["", "## Tracked files still naming an outgoing ID",
                 *(f"- `{path}`" for path in stale_files)]
    body += ["", "If CI's checks do not appear on this PR, close and reopen it."]
    return "\n".join(body) + "\n"


# change records and the recorded catalog name old IDs by design
_SNAPSHOT_PATHS = ("openspec/", "tests/unit/data/model_catalog/")


def spellings(cid: str) -> list[str]:
    """The spellings tracked files use for one catalog ID: vendor-qualified,
    vendor-stripped (as `poe matrix --models` takes it), and for an anthropic ID the
    subscription CLI's form; the same spellings the model-ID guard resolves."""
    found = [cid, cid.split("/", 1)[-1]]
    if cid.startswith("anthropic/"):
        found.append(subscription_id(cid))
    return list(dict.fromkeys(found))


def files_naming(ids: Iterable[str], repo: Path) -> list[str]:
    """Best effort: tracked files (outside the change records and the recorded
    catalog) that still name one of the outgoing IDs as a whole token, in any
    of its `spellings`."""
    ids = list(dict.fromkeys(s for cid in ids for s in spellings(cid)))
    patterns = [re.compile(rf"(?<![\w.-]){re.escape(i)}(?![\w-]|\.\d)") for i in ids]
    if not patterns:
        return []
    try:
        grep = subprocess.run(
            ["git", "-C", str(repo), "grep", "-n", "-I", "-F",
             *(arg for i in ids for arg in ("-e", i))],
            capture_output=True, text=True, encoding="utf-8", check=False,
        )
    except OSError:
        return []
    hits = set()
    for row in grep.stdout.splitlines():
        path, _, text = row.partition(":")
        if not path.startswith(_SNAPSHOT_PATHS) and any(p.search(text) for p in patterns):
            hits.add(path)
    return sorted(hits)


# ---------- the cost-gate warning ---------------------------------------------------


def _gate_line(label: str, model_id: str, line: str | None, catalog) -> str | None:
    cid = catalog_id(model_id)
    kind, newest = assess(cid, line, catalog)
    entry = catalog.get(cid)
    if kind == "missing":
        tail = f" (newest in its line: {newest.id})" if newest else ""
        return f"model currency: {label} {model_id} is missing from the catalog{tail}"
    if kind == "newer":
        return f"model currency: {label} {model_id} is stale — newer in its line: {newest.id}"
    if entry is not None and entry.expiration_date:
        return f"model currency: {label} {model_id} expires {entry.expiration_date}"
    return None


def gate_warnings(
    registry: support.Registry,
    models: Iterable[support.Model],
    environ: Mapping[str, str] | None = None,
    fetch: Fetch | None = None,
    timeout: float = GATE_TIMEOUT,
) -> list[str]:
    """Stale-model lines for the matrix cost gate from one catalog request,
    covering the selected models and the judge and persona the run will use.
    Never raises: any failure becomes a single "model currency unknown" line."""
    try:
        catalog = parse_catalog(_fetch(fetch)(CATALOG_URL, timeout))
    except Exception as exc:  # the gate warns; it never blocks or fails a run
        return [f"model currency unknown (catalog unreachable: {exc})"]
    lines = []
    for m in models:
        lines.append(_gate_line("model", m.id, _line_for(m, catalog_id(m.id)), catalog))
    roles: dict[str, list[str]] = {}
    for name in HELD_ROLES:
        roles.setdefault(support.role_model(registry.roles, name, environ or {}), []).append(name)
    for model_id, names in roles.items():
        label = "/".join(names) + " role"
        line = _gate_line(label, model_id, derive_line(catalog_id(model_id)), catalog)
        lines.append(line and f"{line} (held until a full re-baseline)")
    found = [line for line in lines if line]
    if not found:
        return ["model currency: every selected pin is current in the OpenRouter catalog"]
    return [*found, "model currency: run `uv run poe models` for the full report"]


# ---------- entry point -------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="print findings as JSON")
    parser.add_argument("--write", action="store_true",
                        help="apply bumps and refreshed prices to the registry")
    parser.add_argument("--pr-body", type=Path, help="write the bump-PR description here")
    parser.add_argument("--catalog", type=Path, help="replay a recorded catalog file")
    parser.add_argument("--endpoints", type=Path, help="replay recorded endpoint files")
    parser.add_argument("--registry", type=Path, default=REGISTRY)
    parser.add_argument("--as-of", type=date.fromisoformat,
                        help="snapshot date written to prices_as_of (default: today, UTC)")
    return parser


def _write(args, text: str, result: Result) -> None:
    updated = apply_edits(text, result.edits, args.as_of or datetime.now(UTC).date())
    if updated == text:
        return
    support.parse_registry(updated)  # never write a registry that does not parse
    args.registry.write_text(updated, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    text = args.registry.read_text(encoding="utf-8")
    registry = support.parse_registry(text)
    fetch = replay_fetch(args.catalog, args.endpoints) if args.catalog else None
    source = args.catalog.as_posix() if args.catalog else CATALOG_URL
    try:
        catalog = parse_catalog(_read(_fetch(fetch), CATALOG_URL, TIMEOUT))
        result = check(registry, catalog, fetch)
    except CurrencyUnknown as exc:
        print(f"model currency unknown: {exc}", file=sys.stderr)
        return 2
    fetched_at = datetime.now(UTC).isoformat(timespec="seconds")
    if args.write:
        try:
            _write(args, text, result)
        except ValueError as exc:  # an edit the registry text could not take
            print(f"model currency: write failed, nothing written: {exc}", file=sys.stderr)
            return 3
    if args.pr_body:
        outgoing = [e.target.removeprefix("openrouter/") for e in result.edits
                    if e.kind == "roster" and e.new_id != e.target]
        body = render_pr_body(result, args.as_of or datetime.now(UTC).date(),
                              files_naming(outgoing, HARNESS.parent))
        args.pr_body.write_text(body, encoding="utf-8")
    if args.json:
        print(json.dumps(render_json(result, source, fetched_at), indent=2))
    else:
        print(render_text(result, source))
    return result.exit_code


if __name__ == "__main__":
    sys.exit(main())
