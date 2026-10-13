## Context

See proposal.md — Why. The relevant state:

- `common.http_json` (lit-search, regenerated into `proposal-import` and `proposal-reverse`) opens every request with `urllib.request.urlopen` and calls `json.load` on the response. `JSONDecodeError` sits in the same `except` as `URLError` and `TimeoutError`, so a verification page is fetched three times and then reported as `{source}: Expecting value: line 1 column 1 (char 0)`.
- `search.py` prints `note: source degraded — {exc}` per failed source, then `sources: name(n), …` listing only sources that returned. `validate_refs.py` (import/reverse) catches only `SourceError` and matches `"404" in str(exc)` to detect a non-resolving DOI.
- **Live capture, 2026-10-13** (three plain requests, then one probe of the refresh path), Anubis v1.27.0 on every host:

| Request | Answer |
|---|---|
| `dblp.org`, shipped user agent | `200 text/html`; `Refresh: 2; url=/.within.website/x/cmd/anubis/api/pass-challenge?challenge=…&id=…&redir=<path+query>`; `Set-Cookie: dblp_org-cookie-verification-…` |
| `dblp.uni-trier.de`, shipped user agent | `200 text/html`; same refresh inside `<meta http-equiv="refresh" content="2; url=…">` in the body, no header; cookie set |
| `dblp.org`, `Python-urllib` user agent + `Accept: application/json` | same as the first row |
| refresh followed after 2 s with the cookie jar | `302`, `Set-Cookie: dblp_org-auth-…` valid 3600 s, `Location` = original path; repeating the query → `200 application/json` |
| second and zero-hit queries, same jar | JSON directly; zero hits arrive as `"hits":{"@total":"0",…}` with no `hit` key |

  Every challenge body carried `id="anubis_version"`, `id="anubis_challenge"` (a JSON blob with `"algorithm":"metarefresh","difficulty":1`, the echoed `User-Agent` and `X-Real-Ip`, and a random token) and `/.within.website/x/cmd/anubis/` asset paths.

## Goals / Non-Goals

**Goals:**
- The shipped scripts get through Anubis's refresh tier on their own, at the cost of one wait per host per run.
- Every other non-JSON answer is classified and explained without leaking request or response details.
- A hostile answer can do no more than degrade its own source (threat model below).

**Non-Goals:**
- Proof-of-work tiers, JavaScript execution, sharing a browser's session with the scripts, persisting cookies across runs.
- Changing redirect behaviour of ordinary requests, `http_text` (arXiv), `snowball.py`, or how any other source authenticates.
- Fixing `validate_refs.py`'s string match — it keeps working and is import's own code.

## Decisions

**D1 — Classification lives in `common`, the browser hint in `search.py`.** `common` is a generic helper vendored into import and reverse, whose `OFFLINE` lines must not point at a lit-search section that does not exist there. So `common` raises `SourceError` with a source-neutral message and a structured `kind`; `search.py` appends the browser sentence only for `kind == "challenge"`. Alternative rejected: the hint inside the message (leaks the workflow into other skills); DBLP-only detection in `dblp.py` (duplicates HTTP handling, leaves Crossref unprotected if it ever adopts the same gate).

**D2 — `SourceError` stays one class.** `SourceError(message, *, kind=None, status=None, media_type=None)`; `kind ∈ {challenge, unexpected, malformed_json, http, network}` on every raise from `http_json`, `None` from other raisers (missing key, invalid DOI). `str(exc)` and every existing `except SourceError` are unchanged, and the HTTP message keeps the exact form `"{source}: HTTP {code}"`, so `validate_refs.py`'s `"404"` match survives (pinned by a test). Subclasses were rejected: five classes for one branch in one orchestrator, multiplied into every vendored copy.

**D3 — Classify by body first, metadata second.** The body is read up to 16 MiB + 1 byte (more → `unexpected`, "exceeded 16 MiB"). Leading whitespace and a UTF-8 BOM are skipped; a body that then starts with `{` or `[` goes to `json.loads`, and `ValueError` or `RecursionError` there → `malformed_json`. Otherwise the response is a verification page when the first 64 KiB contain `id="anubis_challenge"`, `id="anubis_version"` or `/.within.website/x/cmd/anubis/`, or when a `Refresh` header targets the pass-challenge path; everything else is `unexpected` (HTML page, other non-JSON content, or an empty body). The declared `Content-Type` decides nothing — real JSON labelled `text/html` still parses, a challenge labelled `application/json` is still recognized — it only feeds the message. Markers are plain substring tests: no regular expression touches the body except the single meta-refresh pattern (D5), bounded to the same 64 KiB.

**D4 — Refresh tier passed once, under fixed guardrails.** On a verification page, a pass is attempted only if all hold: a refresh is present (header, else the meta tag); its delay parses as an integer 0–10; its target, resolved with `urljoin` against the request URL, has the request's scheme, host and port, no `@` anywhere in its authority (so not even empty userinfo), the exact path `/.within.website/x/cmd/anubis/api/pass-challenge`, and no control characters; a target the URL parser rejects (`//[`) fails the check rather than raising; and the page must not have arrived through a redirect, since the refresh and the cookie would then be judged against the original URL. A host whose pass failed is remembered for the process and never waited on again — `validate_refs.py` and snowball enrichment loop over many items. The script then sleeps the stated delay, GETs the target through an opener whose redirect handler refuses every redirect — the `302` carrying the auth cookie surfaces as `HTTPError` after the cookie processor has stored the cookie, and is accepted for any `2xx`/`3xx` — and repeats the original request once. A second verification page, a failed guardrail, or an error on the pass step → `kind="challenge"`, no retry. Alternative rejected: following the pass step's redirect (it would land on the API directly, but that means trusting a server-chosen URL; repeating our own request costs one round trip and removes the question).

**D5 — Cookies in memory, scoped to challenged hosts.** One module-level `CookieJar` with a `DefaultCookiePolicy` subclass whose `set_ok` admits a cookie only when the responding host is in a set of hosts that served a recognized verification page in this process, and whose `return_ok` sends one only to such a host — stdlib domain matching alone would hand a challenged `a.example.org`'s `Domain=.example.org` cookie to `b.example.org`. (Requiring `Domain` to equal the host was rejected: DBLP's mirror `dblp.uni-trier.de` sets `Domain=uni-trier.de`.) The first challenge response's own cookie arrives before the page is recognized, so after recognition the host joins the set and `jar.extract_cookies(response, request)` is replayed for that response. All of `http_json` goes through one opener with `HTTPCookieProcessor(jar)`; for a host that never challenged, the jar holds nothing to send and accepts nothing. Stdlib rules remain in force: domain matching, `Secure` cookies only over HTTPS. Alternative rejected: an on-disk `MozillaCookieJar` (saves two seconds per run, costs a token at rest, a cache path, and cleanup rules).

**D6 — Retries follow the cause.** `challenge` and `unexpected` raise immediately; `malformed_json` keeps the two retries with `BACKOFF_SECONDS`; HTTP 429/500/502/503 and network faults keep their backoff. The network class widens from `URLError`/`TimeoutError` to every `OSError` (a connection reset during the body read) and `http.client.HTTPException` (`RemoteDisconnected` from `getresponse`, which urllib does not wrap), both of which today escape `except SourceError`. The pass step is not a retry and does not consume one.

**D7 — Messages.** Fields: source, integer status, and the media type from the raw `Content-Type` (split at `;`, lowercased) only if it is in a fixed set of ten common types, else `unknown type` — a pattern allowlist still let a server place ~80 characters of its own text, and `text/x404` would flip `validate_refs.py`'s `"404"` match; a missing header reads `no media type` (not `email.message`'s `text/plain` default). Network failures read `{source}: network failure (<reason>)` with the reason from a fixed vocabulary (timed out, connection refused, connection closed by the server, host name not resolved, TLS certificate could not be verified, TLS error, invalid HTTP response, unclassified error) — never `str(exc)`, since `BadStatusLine` carries the server's raw status line. A `ValueError` nothing above anticipated becomes `kind="unexpected"`, `API answer could not be processed`, so no parser error reaches `validate_refs.py`, which catches only `SourceError`. Wording:
- `{source}: API returned an Anubis browser-verification page (HTTP 200, text/html), not JSON, and automatic verification did not pass`
- `{source}: API returned an HTML page (HTTP 200, text/html), not JSON` · `… returned non-JSON content (…)` · `… returned an empty body (…)` · `… response exceeded 16 MiB (…)` — every variant carries the same `(HTTP status, media type)` pair
- `{source}: API returned malformed JSON (HTTP 200, application/json)`
- `{source}: HTTP {code}` unchanged; `{source}: network failure (connection refused)` replaces the raw `<urlopen error …>` text (nothing in the repository matched on it).

`search.py` tail for `challenge`: `A normal browser may still pass it (see "If a source asks for browser verification" in the skill); this script stays blocked either way. This run continues without {source} results.` A successful pass prints nothing.

**D8 — Tests over a real local socket.** A `ThreadingHTTPServer` on `127.0.0.1:0` (a fixture inside `test_lit_http.py`, its only caller), driven by a per-test route table, exercises the real opener, cookie processor and redirect refusal; `common.time.sleep` is patched to record requested delays. A fixture resets the jar, the challenged-host set and `_last_call` between tests. Challenge fixtures are today's capture with every value that could identify anything replaced: synthetic token and id, `192.0.2.7` (TEST-NET-1), and an echoed user agent carrying `mailto:erika.musterfrau@example.org`. Cookies in fixtures omit `Secure`, since the server is plain HTTP. `search.py` is tested in-process through `main(argv)` with patched source modules.

**D9 — Live check outside the gate.** `poe lit-live` runs `search.py pentest --sources dblp --limit 3`: exit 0 with candidates when the pass works, exit 1 when DBLP is blocked. It is networked and read-only, like `poe models`, and stays out of `poe test` and CI so an external block never makes the suite flaky.

## Threat model

A malicious or compromised answer (or a MITM that defeated TLS) must not get more than a degraded source. Each row has an L0 test.

| # | Threat | Mitigation |
|---|---|---|
| T1 | Refresh to another host, internal address, `//host` protocol-relative, scheme downgrade, `../` or `%2e` traversal, (empty) userinfo; a redirected page | D4: same scheme/host/port, no `@`, exact path equality after `urljoin`; no pass on a redirected answer |
| T2 | Pass step redirects elsewhere | D4: no redirect followed on the pass step |
| T3 | Huge, negative or garbage delay; repeated waits | D4: integer 0–10 only; a failed host is not waited on again this run |
| T4 | Endless challenge loop | D4: one pass per request, no recursion |
| T5 | Memory or CPU exhaustion via body | D3: 16 MiB read cap; substring markers; one bounded pattern over 64 KiB |
| T6 | Depth bomb / bad encoding / unparsable URL escaping as `RecursionError` / `UnicodeDecodeError` / `ValueError` | D3: caught → `malformed_json`; D4: parse errors fail the guardrail; D7: any other `ValueError` → `unexpected` |
| T7 | Cookie tracking or injection across sources | D5: accept from and send to challenged hosts only; stdlib domain and `Secure` rules; memory only |
| T8 | Log or prompt injection through diagnostics; leaking query, token, IP, contact address | D7: only source, int status, a known media type, a fixed network-failure vocabulary |
| T9 | Control characters in the refresh target | D4: rejected before any request |
| T10 | TLS weakened | default context untouched; L0 test fails on `_create_unverified_context`, `CERT_NONE` or `check_hostname = False` in shipped scripts |
| T11 | Instructions embedded in records | unchanged pinned untrusted-data rule |

**Security review (task 5.5).** An independent read-only review of the implementation against this table, with offline probes, found two medium, four low and two informational issues; seven are fixed, each with a test: `ValueError` from `urlsplit` on `//[` escaping (T6), the network message echoing a server's raw status line (T8), parent-domain cookies reaching sibling hosts (T7), a redirected answer's cookie stored under the original host (T1/T7), repeated 10-second waits per call on an unpassable host (T3), empty userinfo passing the check (T1), and a pattern-allowlisted media type still carrying server text (T8). One finding is accepted as is: a hostile 16 MiB body of tiny JSON objects can peak near 400 MiB while parsing. A lower cap would cut legitimate answers (an OpenCitations citation list for a heavily cited paper runs to several MiB), and before this change the read was unbounded.

## Risks / Trade-offs

- [DBLP raises the tier to proof-of-work] → the script degrades with the challenge diagnostic and the browser route; `poe lit-live` shows it before a student report does.
- [Anubis changes its markup or pass path] → recognition falls back to `unexpected`, which still names an HTML page and never retries; the fixtures pin today's markers, and updating them is a reviewed change.
- [Two-second wait per run and host] → acceptable per the grill; silent on success, so students see no noise.
- [Passing an operator's gate] → the refresh tier is Anubis's designed path for clients without JavaScript; the script honours the delay, keeps its identifying user agent, never solves proof-of-work, and sends one request per verification.
- [Generated copies in import/reverse change behaviour too] → intended: a Crossref verification page during reference validation becomes a classified `OFFLINE` line instead of a decode error.

## Migration Plan

None: no data, no configuration. Users receive the change with the next skill update; rollback is reverting the commit and re-running the sync.
