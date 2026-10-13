## Context

**Status (2026-10-13).** The maintainer approved the change as drafted:
- D1: `http_xml` replaces `http_text`.
- D4: the `malformed` kind.
- D5: a malformed feed is retried like JSON.
- D6: HTTPS plus the guard test.
- The backlog wording.

Two further decisions came with the approval:
- The Atom variant of the browser-fallback section is deferred to `docs/backlog.md`.
- L0 key-file isolation is folded in as D11.

See proposal.md, "Why". The relevant state:

- `common.http_json` classifies, caps, passes and sanitizes, as `pass-source-verification` describes (archived 2026-10-13, cited below as PSV D1–D9 and T1–T11). `common.http_text` predates it. It sends the request with `urllib.request.urlopen`, which is not the scoped opener and makes no verification pass. It reads the body with no size limit. Its only handler is `except (URLError, TimeoutError)`, and urllib's `HTTPError` is a `URLError`. Any failure ends as `SourceError(f"{source}: {exc}")`, with no `kind`. `arxiv.py` is its only caller. It parses the text with `ET.fromstring`, raises `arxiv: invalid Atom XML ({exc})` on a `ParseError`, and otherwise returns whatever `atom:entry` children the root has.
- `search.py:56` and `snowball.py:53` catch every other exception and print `{exc}`. `snowball.expand` loops over graph source × seed × direction and prints each note as it happens.
- **Local-server probe, 2026-10-13.** The shipped scripts ran against `ThreadingHTTPServer` on 127.0.0.1 with `time.sleep` recorded; the probe script lives in the session scratchpad and is not committed.

| Answer | Today's result | Requests | Sleeps |
|---|---|---|---|
| `200 text/html`, HTML5 page | `SourceError: arxiv: invalid Atom XML (syntax error: line 1, column 0)` | 1 | — |
| `200 application/xhtml+xml`, well-formed XHTML | `[]`, which `search.py` would list as `arxiv(0)` | 1 | — |
| `404` | `SourceError: arxiv: HTTP Error 404: Not Found` (the server's reason phrase) | 3 | 3.0, 3.0 |
| raw `HTTP/1.1 IGNORE-PREVIOUS 192.0.2.7\r\n\r\n` | `BadStatusLine` escapes `except SourceError`; `search.py` prints `note: source failed unexpectedly — arxiv: HTTP/1.1 IGNORE-PREVIOUS 192.0.2.7` plus a stray line break | 1 | — |
| `snowball.expand` with seeds `10.1/a` and `10.1/b`, direction both, OpenAlex only, no key | 4 note lines, 1 distinct | 0 | — |

- **Live capture, 2026-10-13**, three requests with the shipped user agent and no contact address:

| Request | Answer |
|---|---|
| `http://export.arxiv.org/api/query?search_query=all:pentest&max_results=1` | `301`, `Location: https://export.arxiv.org/api/query?…` (Varnish) |
| the same over `https://` | `200 application/atom+xml; charset=utf-8`. Body: `<?xml version='1.0' encoding='UTF-8'?>`, then `<feed xmlns="http://www.w3.org/2005/Atom" …>`, no DOCTYPE. The feed's `<title>` echoes the query. |
| `https://…&max_results=-1` | `400 application/atom+xml`: a feed with one `<entry>` titled `Error` whose `<id>` is `https://arxiv.org/api/errors#max_results_must_be_non-negative` |

## Goals / Non-Goals

**Goals:**
- Every answer any literature-search script receives, JSON or Atom, gets the same classification, retry policy, size cap, verification handling and sanitized wording.
- A hostile or broken answer from arXiv can do no more than degrade arXiv. Rows T12–T18 below extend the archived threat model.
- No orchestrator note carries text a server or an exception chose.

**Non-Goals:**
- Changing any JSON diagnostic's wording, the `"{source}: HTTP {code}"` form, the `sources:` line, exit codes, or `validate_refs.py`.
- Widening `poe lit-live` beyond DBLP. That is the separate `widen-lit-live` follow-up, recorded in the backlog by this change.
- Adapting the browser-fallback section of `proposal-lit-search` to Atom. Step 2 says "continue only on DBLP's JSON", so an arXiv verification note would point at a section that does not say what a valid arXiv page looks like. arXiv serves no verification page today. The maintainer deferred this on 2026-10-13, and it is recorded in `docs/backlog.md`.
- Interpreting arXiv's error feed. arXiv sends it with HTTP 400, which is already a classified, non-retried `HTTP 400`.
- Isolating subprocess runs of the scripts. The only one in L0, `test_search_rejects_unknown_source`, exits on argument parsing before any key lookup. Orchestrators are tested in-process through `main(argv)`.

## Decisions

**D1 — One request path, two document formats.** `http_json` and the new `http_xml(url, params=None, source="", min_interval=1.0, *, root)` become thin wrappers over one `_request(call)`. It holds the throttle, `_fetch` (scoped opener, 16 MiB + 1 read, refresh-tier pass per PSV D4, challenged-host jar per PSV D5), the retry loop and `_network_reason`. The two wrappers differ only in the format the call carries: a name for messages (`JSON`, `XML`), a test for "this body starts as the expected document", and a parser. `http_text` is removed. `arxiv.py` was its only caller, and the vendored copies in import and reverse never called it. Alternatives rejected:
  - Patch `http_text`'s except clauses. This keeps a second retry loop, and a weaker second copy is exactly how this gap opened. It would also still miss the cap and the pass.
  - Keep `http_text` returning `str` and validate in `arxiv.py`. The diagnostic would lack the status and media type the spec requires, the parse would sit outside the retry loop, and the HTML-versus-malformed decision would be split across two modules.
  - Keep the name `http_text` with a new return type. That misleads the next reader.

**D2 — A feed is parsed only when it starts as the feed.** This mirrors PSV D3's "starts with `{` or `[`". First skip a UTF-8 BOM, whitespace, and an optional XML declaration: `<?xml` through the first `?>` within the first KiB, then whitespace. The declaration is skipped only when it holds no `<`, which a real declaration never does. Otherwise a DOCTYPE hidden inside it would reach expat, which rejects it as a malformed declaration, but only after reading it (security review, below). The first markup must then be the start tag of `root`'s local name, with any prefix, followed by whitespace, `>` or `/`. Such a body goes to `ET.fromstring(bytes)`.
  - Two outcomes are possible. A `ParseError` (or `ValueError`) is `malformed`. A root whose Clark name differs from `root` (`{http://www.w3.org/2005/Atom}feed`) is `unexpected`.
  - A document type declaration must precede the root element. A body that passes this test therefore carries none, and without a DTD there is no entity declaration to expand. Billion-laughs and external entities never reach expat, whatever expat version the user's Python links. That is the reason, under the stdlib-only rule, for not reaching for `defusedxml` or relying on expat's own amplification limits.
  - A body that starts as the expected document, JSON or feed, is never scanned for verification markers. A record whose abstract quotes Anubis's markup cannot turn a valid answer into a "challenge". For JSON this already holds; for XML it is new, and without it any search hitting such a paper would degrade arXiv (T17).
  - A body that does not start as the document is classified in this order: verification markers in the first 64 KiB (unchanged) → `challenge`; empty → `unexpected`; first markup `<!doctype html` or `<html` in any case, or an HTML media type → HTML page; any other body starting with `<` → other XML; anything else → non-XML content. The size check comes first, as today.
  - The declared media type still decides nothing about acceptance. It feeds the message, and for XML it chooses only between "HTML page" and "other XML" wording.
  - Alternative rejected: substring refusal of `<!DOCTYPE`/`<!ENTITY` before parsing. That is a weaker guarantee, since it leaves a check to get right in every future format, and with D2's start test it is redundant.

**D2a — Feed depth is capped while parsing.** `MAX_XML_DEPTH = 32`; an Atom feed nests four deep.
- The parser's target is the standard `TreeBuilder` behind a depth counter, which raises `ValueError` past the cap. The error is classified `malformed`, like a JSON depth bomb.
- The body is fed in 64 KiB chunks. A callback's exception only surfaces at the end of `feed()`, and until then expat keeps parsing its buffer and growing its own tag stack. Feeding in chunks bounds that to one chunk.
- Alternatives rejected:
  - Building the tree first and measuring depth afterwards: the cost is paid before the check.
  - `XMLPullParser` with a depth check after each chunk: the same bound, with event bookkeeping that the target already does.

**D3 — Messages.** JSON wording is byte-identical to today. XML follows the same pattern with `XML` in place of `JSON`:
- `arxiv: API returned an Anubis browser-verification page (HTTP 200, text/html), not XML, and automatic verification did not pass`
- `arxiv: API returned an HTML page (HTTP 200, text/html), not XML`
- `arxiv: API returned XML other than the expected document (HTTP 200, application/xml)`. This covers XML with another root, a foreign namespace, or a DOCTYPE before the root.
- `arxiv: API returned non-XML content (HTTP 200, text/plain)`
- `arxiv: API returned an empty body (HTTP 200, application/atom+xml)`
- `arxiv: API response exceeded 16 MiB (HTTP 200, application/atom+xml)`
- `arxiv: API returned malformed XML (HTTP 200, application/atom+xml)`
- `arxiv: HTTP 404` · `arxiv: HTTP 400` · `arxiv: HTTP 503`. Only the integer code is used, never `str(HTTPError)`, which carries the server's reason phrase.
- `arxiv: network failure (timed out)` and the rest of PSV D7's fixed vocabulary
- `arxiv: API answer could not be processed`. This is the existing `ValueError` fallback, kind `unexpected`.

Orchestrator notes:
- `note: source degraded — {exc}`, plus the browser hint for `challenge`: unchanged.
- `note: source failed unexpectedly — {name}: {type(exc).__name__}` (search.py).
- `note: {name}.{edge} failed — {type(exc).__name__}` (snowball.py; `edge` is today's loop variable `kind`, renamed so it no longer reads like `SourceError.kind`; `direction` was taken, it is `expand`'s parameter).

**D4 — `kind="malformed"` replaces `"malformed_json"`.** The set becomes `{challenge, unexpected, malformed, http, network}`. A kind names the cause an orchestrator acts on; the format is in the message. `search.py` branches on `challenge` only, and `validate_refs.py` reads no kind. The rename touches the retry condition, the `SourceError` docstring and two test files. Alternative rejected: adding `malformed_xml`. That is two values for one cause, and the retry condition would grow a set for no reader's benefit.

**D5 — Retry by kind, one table for both formats.**
- HTTP 429/500/502/503: backoff `BACKOFF_SECONDS × (attempt + 1)`.
- Network faults (`OSError`, `http.client.HTTPException`): `BACKOFF_SECONDS`.
- `malformed`: two retries at `BACKOFF_SECONDS`, the transient-transfer case PSV D6 kept for JSON.
- Every other HTTP status, 400 and 404 included, and `challenge` and `unexpected`: raised at once.

For arXiv this means:
- 404 and 400 go from three requests to one.
- A malformed feed goes from none to two retries, at most two extra requests at arXiv's 3-second interval.
- 503/429 keep three attempts.

Alternative rejected: no retry for malformed XML only. That needs a per-format retry flag, and "a truncated transfer may succeed on retry" holds for any format.

**D6 — Every source over HTTPS.** `arxiv.BASE_URL = "https://export.arxiv.org/api/query"`, the URL `proposal-ideate` already documents. The live capture shows the plain-HTTP URL only ever answers with a redirect. That costs a round trip, sends the query in cleartext first, and makes a verification pass impossible, since PSV D4 refuses to pass a redirected answer.
- An L0 guard scans `skills/proposal-lit-search/scripts/*.py` with `ast` for string constants that start with `http://`. The allowlist holds XML namespace names that are never requested: `http://www.w3.org/2005/Atom` and `http://arxiv.org/schemas/atom`.
- A second assertion pins `arxiv.BASE_URL` to `https://`.
- Host names are unchanged, so `docs/install.md`'s host list and the Copilot runner's domain allowlist stay correct.

**D7 — Catch-all notes name the type.** After D1, `OSError`, `HTTPException` and `ValueError` raised during a request are classified inside `common`. What still reaches the catch-alls is a programming error or an unforeseen parser input, such as `KeyError` or `AttributeError`. `type(exc).__name__` is enough for a bug report and cannot carry server text, line breaks or addresses. Alternatives rejected:
  - `repr(exc)` or a scrubbed `str(exc)`: arbitrary exception text has no fixed vocabulary to scrub against.
  - Printing a traceback: the paths it prints reveal the user's directory layout.

**D8 — Snowball prints each distinct note once per run.** `expand` keeps a local `set` of printed lines. Every note it prints goes through one helper: degradation, catch-all, and "not a DOI, skipped". A line already printed is skipped. The set is per call, not module-level: `main` calls `expand` once per process, and in-process tests need no reset. `search.py` needs nothing, since it calls each source once. Alternative rejected: a count suffix (`(×4)`). That is a new output form, and the note's job is to name a degraded source, not to count how often.

**D9 — Leak assertions carry distinctive values.** In `tests/unit/test_lit_http.py`:
- Today's `verify=challenge-cookie` and `auth=passed` become `verify=COOKIE-VERIFY-1b7e` and `auth=COOKIE-AUTH-4c2d`. The `gated` and `verifier` routes match on the new values.
- The diagnostics test sends `api_key=KEY-API-9d0f` as a query parameter, as OpenAlex does. On the JSON path it also sends `authorization: TOKEN-OC-6a3b` as a header, as OpenCitations does.
- `PRIVATE` gains all four values. The parametrized leak test runs every response once through `http_json` and once through `http_xml`.
- XML-specific rows are added: a truncated feed whose `<title>` echoes the query, and a raw `404 SECRET-REASON-…` status line.
- The catch-all tests in `test_lit_search_cli.py` raise an exception whose text carries every `PRIVATE` value plus `\r\n`. They assert that the note is the single expected line.

**D10 — Tests over the existing local server.**
- The arXiv tests live in `tests/unit/test_lit_http.py`, so the `server` fixture keeps its single caller file, as PSV D8 placed it.
- A `fetch_feed` helper sits beside `fetch`.
- End-to-end `arxiv.search` runs patch `arxiv.BASE_URL` to the server; recorded sleeps include arXiv's 3-second throttle where a test calls twice.
- New synthetic fixture `tests/unit/data/arxiv_empty.xml`: the existing sample's header with `opensearch:totalResults` 0, no entries, and a synthetic query in its title.
- Malformed, foreign, DOCTYPE and marker-carrying feeds are built in the test from the existing `arxiv_search_sample.xml` or inline bytes.
- The entity case patches the XML parse function to fail the test if it is ever called.
- No live test. `poe lit-live` is unchanged.

**D11 — L0 never reads the developer's key files.** `common.get_key` consults three things: the environment, `THESIS_PROPOSAL_KEYS`, and two files. One file is `api-keys.env` in the working directory, the repository root under pytest. The other is `GLOBAL_KEY_FILE`, which is computed from the real home at import. `user_agent()` calls `get_key("CONTACT_EMAIL")` on every request. So any L0 test that exercises the HTTP path, or a key lookup, reads the developer's own files. Two tests assume those files hold no OpenAlex key. One is `test_get_key_never_reads_ancestor_directories`. The other is `test_openalex_requires_key`, which would send a live, keyed request if one were there. Neither file exists on this machine today, so the problem has not shown up yet.

An autouse fixture in `tests/conftest.py`, beside `_harness_login_offline` and `_model_catalog_offline`, does four things for every test:
- points `common.GLOBAL_KEY_FILE` at an absent path under the session temp directory;
- drops `THESIS_PROPOSAL_KEYS`, `OPENALEX_API_KEY`, `CONTACT_EMAIL` and `OPENCITATIONS_TOKEN` from the environment;
- wraps `common._read_key`, the only key-file reader, so that a path outside pytest's base temp directory reads as absent without being opened;
- leaves tests that write a key file under `tmp_path`, and point `THESIS_PROPOSAL_KEYS` or the working directory at it, working as before.

`test_lit_common.py` proves it. While `get_key`, `user_agent()` and OpenAlex's no-key path run, it spies on `Path.read_text`. The spy asserts that neither `Path.home() / ".config/thesis-proposal/api-keys.env"` nor the repository-root `api-keys.env` is opened. A self-test asks the wrapped reader for an existing file outside the temp root (`pyproject.toml`) and asserts it is not opened.

`import common` resolves to the lit-search source module for every test (the pythonpath order), so `validate_refs.py`'s tests are covered by the same patch.

Alternatives rejected:
- `chdir` into a temp directory for every test, which would change the working directory for the whole suite.
- Overriding `HOME`, which does not reach a path `common` computed at import.
- Stubbing `get_key` per test, which leaves the next test to forget.

## Threat model additions

Rows T1–T11 (PSV) now apply to arXiv as well, through D1. New rows, each with an L0 test:

| # | Threat | Mitigation |
|---|---|---|
| T12 | Query sent in cleartext and redirected before every arXiv request; a redirected verification page can never be passed | D6: HTTPS base URL; guard test against plain-HTTP request URLs |
| T13 | Entity expansion (billion laughs) or external entities in an XML answer | D2: only bodies whose first markup is the root element are parsed, so no DTD reaches expat |
| T14 | Server text in notes: reason phrase, raw status line with CR/LF and an address, parser error text | D1 and D3: `HTTP {code}` and the fixed network vocabulary; D7: catch-alls print the type name only |
| T15 | Memory exhaustion through an unbounded arXiv read | D1: the shared 16 MiB + 1 read cap |
| T16 | A non-feed XML document counted as a zero-hit answer | D2: root Clark name checked; anything else is `unexpected` |
| T17 | Content-controlled degradation: a record quoting the verifier's markup turns a valid answer into a "challenge" | D2: a body that starts as the expected document is never scanned for markers |
| T18 | Memory exhaustion through feed depth under the 16 MiB cap: expat's tag stack | D2a: depth cap 32, parsed in 64 KiB chunks |

**Security review (task 6.5).** The maintainer asked for no model calls, so this review was done in-session, without a separate reviewer agent. It read the diff against T1–T18 and ran offline probes (scratch scripts, not committed).
- **Fixed, test-first:**
  - (medium) A 16 MiB feed nested 2.4 million deep was parsed in full: +702 MiB peak. Now it is refused at depth 33 with +0 MiB (D2a). Tests `test_a_feed_nested_deeper_than_any_feed_is_malformed` and `test_feed_depth_limit_admits_a_real_feed_shape`.
  - (low) A DOCTYPE inside a malformed XML declaration reached expat, which rejected it as malformed and expanded nothing, and the answer was retried. Now it is not admitted (D2). Test case `doctype-in-declaration`.
- **Accepted:** a flat 16 MiB feed of empty elements peaks near +366 MiB and 1.6 s while parsing. This is the same order as the +400 MiB PSV accepted for JSON, for the same reason: a lower cap would cut legitimate answers.
- **Checked, no finding:**
  - JSON wording is byte-identical.
  - The HTTP reason phrase never reaches a message.
  - Only the type name of an exception reaches a note.
  - arXiv answers go through the challenged-host cookie policy.
  - TLS uses the default context.
  - A stylesheet instruction or a comment before a DOCTYPE is not admitted.
  - A prefixed root (`atom:feed`) and a BOM with whitespace are admitted.

## Risks / Trade-offs

- [arXiv adds a stylesheet processing instruction, a comment or a DOCTYPE before `<feed>`, or changes namespace] → arXiv degrades with "XML other than the expected document". It is never parsed into zero hits, and the start test is widened in a reviewed change. `poe lit-live` does not watch arXiv; the backlog entry `widen-lit-live` records that.
- [Malformed feeds now cost up to two extra requests] → bounded by `RETRIES` and arXiv's 3-second interval, and identical to the JSON policy.
- [The `malformed_json` → `malformed` rename] → only `common.py` and two test files compare the value (`rg malformed_json` outside the archive). The vendored copies change with the sync.
- [An arXiv verification page's note points at a section written for DBLP's JSON] → arXiv serves none today; the Atom variant is a `docs/backlog.md` entry.
- [The autouse key-file wrapper hides a test that really needs a key file elsewhere] → such a test writes its file under `tmp_path`, as every current one does; a path outside the temp root reads as absent, which fails loudly as "no key" rather than silently reading real credentials.
- [De-duplication hides how many seeds hit the same failure] → the note names the degraded source, which is what the agent acts on. Different failures still print different lines.
- [Vendored copies in import/reverse gain `http_xml` and lose `http_text`] → neither skill calls either. The JSON path's behaviour and wording are unchanged apart from the kind value, which `validate_refs.py` does not read; `tests/unit/test_validate_refs.py` stays the check.
- [Shared checkout] → `.githooks/pre-commit` stages every sync destination, so this change is implemented in sequence with any other session that edits `shared/` or vendored scripts, never beside it.

## Migration Plan

None: no data, no configuration. Users get the change with the next skill update. To roll back, revert the commit and re-run `python3 scripts/sync_shared.py`.

## Open Questions

None. The one question raised in the draft, an Atom variant of the browser-fallback section, was deferred to `docs/backlog.md` by the maintainer on 2026-10-13.
