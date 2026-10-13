## Why

DBLP now answers every API request from the literature-search scripts with an Anubis verification page — `HTTP 200`, `text/html`, a few kilobytes of challenge markup — instead of JSON. `common.http_json` hands that page straight to `json.load`, retries the decode failure twice as if it were a transient network fault, and the search finally reports `dblp: Expecting value: line 1 column 1 (char 0)`: a message that reads like malformed API data, names no cause, and offers no way forward. A live probe on 2026-10-13 showed the page is Anubis's no-JavaScript tier (`metarefresh`, difficulty 1): a client that waits the two seconds the page asks for, follows the page's own refresh URL once and keeps the cookie it is given receives the API's JSON, and keeps receiving it for an hour. The scripts can therefore pass the gate themselves; where they cannot — a proof-of-work tier, a changed page — the student needs a diagnosis that says so and a documented route through an ordinary browser that does not pretend the script recovered.

## What Changes

- **Verification pages are passed when the page offers a plain refresh.** `common.http_json` recognizes an Anubis page by its markup, waits the page's own delay (at most 10 seconds), follows its pass-challenge URL once — same origin, exact path, same-origin redirects only — and retries the original request with the cookie it received. Cookies live in memory for one process and are accepted only from hosts that served such a page; nothing is written to disk. No proof-of-work, no JavaScript, no change of user agent, no relaxed TLS.
- **Non-JSON answers are classified, not decoded blindly.** `SourceError` gains keyword-only fields `kind` (`challenge`, `unexpected`, `malformed_json`, `http`, `network`), `status`, and `media_type`; existing raisers and every `except SourceError` keep working. A verification page that could not be passed, an unrelated HTML page, other non-JSON content, malformed JSON, oversized bodies and JSON nested deep enough to exhaust the parser each produce their own short diagnostic.
- **Retries follow the cause.** Verification pages and unexpected content are not retried; malformed JSON keeps today's two retries; HTTP 429/500/502/503 and network faults keep their backoff unchanged.
- **Diagnostics stay sanitized.** Messages carry the source name, the numeric status and an allowlisted media type — never the request URL, the query, the refresh target, cookies, the response body, the user agent with its contact address, or the client IP the page echoes back.
- **`search.py` names the next step.** For a verification page that was not passed, its degradation note adds that a normal browser may still pass it, that the script stays blocked either way, and that the run continues without that source's results. A source that degraded is still never listed as a zero-hit contributor, and exit codes are unchanged.
- **Browser fallback in `proposal-lit-search`.** A new section describes the host-neutral browser route for a source the script could not get through: optional and consent-bound, the official API URL with public query terms only, JSON confirmed on the page, records merged under the existing judgment, dedupe and citation rules, no raw files written into the workspace, provenance stated in the report, and browser success never presented as script success. The networking-denied section points to it.
- **`proposal-ideate`** treats a DBLP verification page reached with its own fetch tools as a failed lookup, says so, and uses the Crossref author route.
- **`docs/install.md`** troubleshooting gains one sentence: a DBLP browser check is not a network-settings problem.
- **`poe lit-live`**: a networked, read-only check that runs one DBLP query through the shipped script, outside `poe test` and CI, so a change in DBLP's gate shows up before a student reports it.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-lit-search`: "Multi-source federation with graceful degradation" gains scenarios for a source that answered with a verification page (named with its cause, never counted as a zero-hit source, exit codes unchanged); new requirement "Verification pages passed or explained" (automatic pass contract, classification, retry policy, sanitized diagnostics); new requirement "Browser fallback for a blocked source" (the documented, optional browser route and its limits).
- `skill-ideate`: "Research-group scoping" gains a scenario — a DBLP verification page is a failed lookup that routes to Crossref.

## Impact

- `skills/proposal-lit-search/scripts/common.py` — response classification, verification pass, scoped in-memory cookie jar, structured `SourceError`; regenerated into `skills/proposal-import/scripts/` and `skills/proposal-reverse/scripts/` by `scripts/sync_shared.py`. `validate_refs.py` there is untouched: its `"404" in str(exc)` match keeps working because the HTTP message format is unchanged, and the new parser guards stop a depth-bomb `RecursionError` from escaping its `except SourceError`.
- `skills/proposal-lit-search/scripts/search.py` — browser hint on a `challenge` note. `dblp.py` docstring only; `snowball.py` and `http_text` (arXiv) unchanged.
- `skills/proposal-lit-search/SKILL.md` — new `## If a source asks for browser verification` section (≤ 250 words) and one sentence in `## If script networking is denied`; body stays far under the sibling-proportion ceiling.
- `skills/proposal-ideate/SKILL.md` — one sentence in the scoping paragraph.
- `docs/install.md` — one sentence in "Literature search cannot reach its sources".
- `pyproject.toml` — `lit-live` poe task.
- Tests: `tests/unit/test_lit_http.py` (new; its own localhost-server fixture, no external network), `tests/unit/test_lit_search_cli.py` (new; in-process `main(argv)`), sanitized fixtures under `tests/unit/data/anubis/` and two DBLP JSON samples; `tests/unit/test_repo_conventions.py`'s text-I/O scan exempts `<name>opener.open(...)` — urllib's `OpenerDirector.open`, a network call that takes no encoding — with a self-test pinning that nothing else is exempt; and a pin `tests/unit/data/pinned_sentences/proposal-lit-search--browser-fallback.txt`.
- No new dependency: `http.cookiejar`, `urllib`, `html`-free substring checks — standard library only, Python ≥ 3.11.
