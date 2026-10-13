Approved by the maintainer on 2026-10-13, with D11 folded in and the Atom browser variant deferred to the backlog. Implement on a working copy off `main` and land as one commit. Never in a parallel session sharing this checkout: `.githooks/pre-commit` stages every sync destination. Run `python3 scripts/sync_shared.py` after editing `common.py`; never edit the copies in `skills/proposal-import/scripts/` or `skills/proposal-reverse/scripts/`. Do not touch `search.py`'s `sources:` line or any `SKILL.md`.

Implemented 2026-10-13 in the main checkout on top of `0ba4a2e`, uncommitted. Baseline before any edit: `uv run pytest` over the lit-search, validate_refs and install-docs tests gave 119 passed.

## 1. Test scaffolding and fixtures

- [x] 1.1 In `tests/unit/test_lit_http.py`, make the cookie values distinctive: `verify=COOKIE-VERIFY-1b7e` and `auth=COOKIE-AUTH-4c2d`, with `gated` and `verifier` matching on them. Add `API_KEY = "KEY-API-9d0f"` and `ACCESS_TOKEN = "TOKEN-OC-6a3b"`, and extend `PRIVATE` with all four (design D9). Verify:
  - The existing file passes unchanged otherwise: 63 passed.
  - `rg -n "challenge-cookie|auth=passed" tests/unit/test_lit_http.py` finds nothing.
- [x] 1.2 Add `tests/unit/data/arxiv_empty.xml`, a synthetic zero-hit feed: the header of `arxiv_search_sample.xml`, `opensearch:totalResults` 0, no `<entry>`, and a synthetic query in `<title>`. Verify: through `http_xml`'s root check, `arxiv.search` returns `[]` (asserted in 3.2).
- [x] 1.3 Add a `fetch_feed(server, path="/api/query")` helper beside `fetch`. It calls `common.http_xml(server.url(path), params={…query, max_results, api_key…}, source="arxiv", min_interval=0, root=arxiv.FEED)`. `feed_failure` sits beside `failure`. `fetch` itself now also sends `api_key` and an `authorization` header. Verify: used by the 2.x tests.
- [x] 1.4 Key-file isolation (design D11), tests first. Two tests in `tests/unit/test_lit_common.py`:
  - `test_l0_never_opens_a_real_key_file`: spy on `Path.read_text` while `get_key`, `user_agent()` and OpenAlex's no-key path run. Assert that neither `Path.home()/.config/thesis-proposal/api-keys.env` nor the working-directory `api-keys.env` is opened, and that `common.GLOBAL_KEY_FILE` is not the real path.
  - `test_l0_key_reader_opens_nothing_outside_the_test_temp_root`: `_read_key(REPO/pyproject.toml)` returns `None` and opens nothing.

  Red first: both failed. `GLOBAL_KEY_FILE` was `/home/…/.config/thesis-proposal/api-keys.env`, and `_read_key` opened `pyproject.toml` and returned `'thesis-proposal-skills'` from its `name =` line. Then the autouse fixture `_lit_keys_offline` went into `tests/conftest.py`:
  - `GLOBAL_KEY_FILE` points under the session temp directory;
  - `THESIS_PROPOSAL_KEYS`, `OPENALEX_API_KEY`, `CONTACT_EMAIL` and `OPENCITATIONS_TOKEN` are dropped;
  - `_read_key` opens only paths under pytest's base temp directory.

  Verify: both green, and `test_lit_common.py`, `test_lit_parsers.py`, `test_validate_refs.py` and `test_lit_http.py` pass unchanged: 90 passed.

## 2. `common` — one request path, XML format (TDD: tests first in `tests/unit/test_lit_http.py`, then code)

- [x] 2.1 Write the red tests (design D2, D3, D5):
  - The sample feed returns a root with entries.
  - An HTML page (`anubis/unrelated.html`, `text/html`) gives `unexpected`, with exactly `arxiv: API returned an HTML page (HTTP 200, text/html), not XML`, and one request.
  - XHTML with an XML declaration is also an HTML page.
  - These cases give `unexpected`, "XML other than the expected document", and one request: `<error/>`, a `feed` in `urn:example:other`, and a DOCTYPE-first feed. Two cases were added in 6.5: a DOCTYPE inside the declaration, and one after a stylesheet instruction.
  - A truncated feed gives `malformed`, `arxiv: API returned malformed XML (HTTP 200, application/atom+xml)`, three requests and sleeps `[BACKOFF_SECONDS] * 2`.
  - Empty, plain-text and oversized bodies keep their wording with `XML`.
  - A challenge page at the feed path gives `challenge`, with "not XML", and one request.
  - A passable challenge in front of the feed is passed once and the feed returned.
  - A raw `HTTP/1.1 404 SECRET-REASON-…` gives exactly `arxiv: HTTP 404` and one request.
  - 503, 503, feed: returned, with sleeps `[3.0, 6.0]`.

  Verify, red: together with 2.3–2.5, 3.2 and 3.3, `test_lit_http.py` gave 30 failed, 55 passed against the old `common.py`. The JSON half of 2.4 and the HTTPS-scan self-test already passed; they stay as regression guards.
- [x] 2.2 Implement design D1–D5:
  - `_request(call)` shared by `http_json` and `http_xml`, where the call carries a format (`_Json`, `_Xml`).
  - The XML start test and parse, with the root Clark-name check.
  - The format-aware `_is_challenge`.
  - `kind="malformed"` replacing `"malformed_json"` in the code and the `SourceError` docstring.
  - `http_text` removed.

  Updated `test_malformed_json_is_classified_and_retried` and `test_lit_search_cli.py`'s kind list to `malformed`. Verify:
  - The lit tests are green (121 passed). The only JSON assertion edited is the kind value; the JSON wording is byte-identical.
  - `uv run ruff check .` is clean. The most complex functions are `_request` at 10 and `_decode` at 8, under the cap of 12, with no per-file ignore.
- [x] 2.3 Entity definitions never reach the parser (T13). For a billion-laughs body with nine entity levels before `<feed>`, the test patches `common.ET.XMLParser` to fail if called. Verify: `unexpected`, "XML other than the expected document", one request, the parser never called.
- [x] 2.4 Verifier markup inside a valid answer (T17), parametrized over JSON and feed. A DBLP-shaped hit's title and a feed `<summary>` quote `/.within.website/x/cmd/anubis/` and `id="anubis_challenge"`, and both are served with a `Refresh` header to the pass path. Verify: records returned, `server.paths()` is one request, `server.sleeps == []`, and the host is not in `common._UNPASSABLE`.
- [x] 2.5 Leak test over both formats (D9, T8, T14). Every row of `test_diagnostics_reveal_nothing_private` runs once through `fetch` (with `api_key` and `authorization`) and once through `fetch_feed`. Added rows: `feed-echo` (a truncated feed whose `<title>` echoes the query) and `reason-phrase` (a raw 404 whose reason carries the query and an address). Verify: `assert_private` passes for all 9 rows × 2 formats, with the cookie, key and token values in `PRIVATE`.
- [x] 2.6 `uv run python3 scripts/sync_shared.py` regenerated `skills/proposal-import/scripts/common.py` and `skills/proposal-reverse/scripts/common.py`. Verify:
  - `python3 scripts/sync_shared.py --check` reports "generated copies in sync".
  - `test_validate_refs.py` is green.
  - `rg -n "http_text|malformed_json" skills/` finds nothing.

## 3. `arxiv.py`

- [x] 3.1 `BASE_URL = "https://export.arxiv.org/api/query"`, with the docstring updated. `FEED = "{http://www.w3.org/2005/Atom}feed"`. `search` calls `common.http_xml(…, root=FEED)` and reads `atom:entry` from the returned root. `_parse_feed` and `invalid Atom XML ({exc})` are removed. Verify: `rg -n "invalid Atom XML|http_text" skills/proposal-lit-search` finds nothing.
- [x] 3.2 Tests:
  - `test_lit_parsers.py::test_arxiv_search` patches `common.http_xml` with the parsed sample.
  - `test_lit_http.py::test_arxiv_search_runs_through_the_shared_path`: the sample gives 3 entries with titles and abstracts; `arxiv_empty.xml` gives `[]`; the XHTML page raises `SourceError` ("HTML page"), not `[]`.

  Verify: green.
- [x] 3.3 HTTPS guard (D6, T12), beside `test_no_shipped_script_weakens_tls`:
  - `test_lit_search_requests_every_source_over_https`: an `ast` scan for string constants starting with `http://`. The allowlist is exactly the Atom and arXiv-schema namespace names. The test also asserts `arxiv.BASE_URL.startswith("https://")`.
  - `test_the_https_scan_reports_a_plain_http_request_address`: the scan reports a planted constant and an f-string prefix, and passes the namespace name.

  Verify: red against the old `arxiv.py` (in the 2.1 red run), green now.

## 4. Orchestrators (in-process tests in `tests/unit/test_lit_search_cli.py`; docstring now covers snowball)

- [x] 4.1 `search.py`'s catch-all is now `note: source failed unexpectedly — {name}: {type(exc).__name__}` (D3, D7). The test's stub `arxiv` raises `RuntimeError` with the query, an address, a contact and `\r\nnote: X-Injected`; stub `crossref` returns one paper.
  - Red first: the note carried `HTTP/1.1 SECRET-QUERY-7f3a 192.0.2.7 erika.musterfrau@example.org`, and the forged line printed as a second note.
  - Verify: exit 0, stdout CSL-YAML only, stderr exactly `["note: source failed unexpectedly — arxiv: RuntimeError", "sources: crossref(1)"]`. `test_install_docs.py` is green: the `sources:` line is untouched.
- [x] 4.2 `snowball.py` (D8): all notes in `expand` go through one once-per-run helper. The catch-all prints `note: {name}.{edge} failed — {type(exc).__name__}`, and the loop variable `kind` is renamed to `edge` (`direction` is `expand`'s parameter). Tests run `snowball.main(["10.1/a", "10.1/b"])` with `GRAPH_SOURCES` patched to:
  - the real `openalex`, keyless through the 1.4 isolation;
  - `broken`, raising `RuntimeError` with the private text;
  - `crossref`, returning one titled paper.

  Red first: the missing-key note appeared 4 times. Verify:
  - The missing-key note appears once.
  - `note: broken.references failed — RuntimeError` and `…citations…` appear once each.
  - No private value appears on stderr.
  - Exit 0, with CSL-YAML on stdout.
  - An OpenAlex-only run exits 1 with `no expansion results`.

## 5. Docs

- [x] 5.1 In `docs/backlog.md`, the "arXiv and snowball bot checks" entry is removed from "Skills". Under "Evaluation and measurement": "**Live check beyond DBLP** (working name `widen-lit-live`)". Under "Skills": "**Browser fallback for arXiv's Atom feed.**", deferred by the maintainer. Both cite `openspec/changes/classify-arxiv-answers/design.md`. The evidence paths name the open change, as other entries do; archiving rewrites them to `openspec/changes/archive/<date>-classify-arxiv-answers/`. Verify:
  - `rg -n "arXiv and snowball bot checks" docs/` finds nothing.
  - Both entries name their evidence path.
- [x] 5.2 No other prose changes. Verify: `/usr/bin/git diff --stat -- 'skills/*/SKILL.md' README.md docs/install.md AGENTS.md` is empty.

## 6. Verification

- [x] 6.1 `uv run poe test` green, 2026-10-13, after the 6.5 fixes: 4505 passed, 2 skipped; ruff "All checks passed!"; "generated copies in sync"; all 11 skills conform.
- [x] 6.2 `uv run poe specs` green: 20 passed, 0 failed.
- [x] 6.3 `uv run poe cov`: 94.40 % against the floor of 78.
  - Per file: `common.py` 98 %, `arxiv.py` 97 %, `search.py` 98 %, `snowball.py` 90 %.
  - Every uncovered line predates this change: the `ValueError` fallback in the retry loop, the refresh-parse `ValueError` guard, YAML emission, and snowball's "not a DOI" and direction filters.
  - The new branches are covered: XML start test, root mismatch, HTML-versus-other-XML wording, depth limit.
- [x] 6.4 Live, read-only, once, 2026-10-13: `python3 skills/proposal-lit-search/scripts/search.py pentest --sources arxiv --limit 3` gave stderr `sources: arxiv(3)`, no note, exit 0, and 3 CSL-YAML entries.
- [x] 6.5 Security review of the diff against T1–T18. It was done in-session without a reviewer agent, honouring "no model calls", and used offline scratch probes. Findings, recorded in design.md (Threat model, Security review):
  - Fixed test-first (medium): a 2.4M-deep 16 MiB feed peaked at +702 MiB. It is now refused at depth 33 with +0 MiB (D2a, T18).
  - Fixed test-first (low): a DOCTYPE inside a malformed XML declaration reached expat. It is no longer admitted (D2).
  - Accepted: a flat 16 MiB feed peaks near +366 MiB and 1.6 s, the same order as PSV's accepted JSON residual.
