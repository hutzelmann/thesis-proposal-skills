## Why

`pass-source-verification` (archived 2026-10-13) made every answer that goes through `common.http_json` classified and sanitized, and the spec now promises that for "the literature-search scripts". arXiv does not go through `http_json`: `arxiv.py` calls `common.http_text`, which that change left alone. On 2026-10-13 the shipped scripts were run against a local server, and the probe showed the gap. An HTML page is reported as `arxiv: invalid Atom XML (syntax error: line 1, column 0)`. A well-formed XHTML page parses as a feed with no entries, so arXiv would be listed as `arxiv(0)`, a degraded source counted as a zero-hit source. A 404 is requested three times with 3-second waits, because urllib's `HTTPError` is a `URLError`. It is then reported with the server's own reason phrase (`HTTP Error 404: Not Found`). A malformed status line escapes as `BadStatusLine`, and `search.py`'s catch-all note prints it verbatim: server text, the address it carried, and a line break, all on stderr. The body is read with no size limit.

A live request the same day found two more problems. arXiv's base URL is plain HTTP, and arXiv answers it with a 301 to HTTPS, so every query first crosses the network in cleartext. And because a verification page reached through a redirect is never passed, arXiv could never get through one. `snowball.py`'s catch-all has the same echo. It also repeats one degradation note per seed and direction: with no OpenAlex key, two seeds printed the same line four times.

## What Changes

- **arXiv shares the JSON sources' request path.** `common.http_text` is replaced by `common.http_xml`. It goes through the same throttle, 16 MiB read cap, refresh-tier verification pass, scoped cookie jar, retry loop and fixed network-failure vocabulary as `http_json`. It returns the parsed feed, checked to be the expected Atom `feed` element.
- **Feeds are classified like JSON.** A body is parsed only when its first markup is the expected feed element, so a document type declaration, and with it any entity definition, never reaches the XML parser. Such a body is also never taken for a verification page. Anything else is classified as one of: a verification page, an HTML page, other XML, non-XML content, an empty body, an oversized body, or malformed XML. Each diagnostic carries the source, the numeric status and an allowlisted media type, and nothing else.
- **Retries follow the cause for arXiv too.** HTTP 429/500/502/503 and network faults keep their backoff. A malformed document keeps its two retries. A 404, every other HTTP status, a verification page and unexpected content are not retried.
- **`SourceError.kind` `malformed_json` becomes `malformed`.** The message still names the format. Only the retry loop and two test files compare this value.
- **arXiv over HTTPS.** The base URL becomes `https://export.arxiv.org/api/query`, the URL `proposal-ideate` already documents. An offline test fails when a lit-search script requests a plain-HTTP address.
- **Catch-all notes name the error type only.** In `search.py` and `snowball.py`, a failure the scripts did not anticipate is noted with the source and the exception's class name, never its text.
- **Snowballing prints each note once per run.** One missing OpenAlex key gives one note, not one per seed and direction.
- **Sharper leak assertions.** The localhost fixtures carry distinctive cookie values, an API-key query parameter and an access-token header. The diagnostics tests assert that none of them appears, for both formats and for the catch-all notes.
- **L0 never reads the developer's key files.** An autouse fixture in `tests/conftest.py` redirects `common.GLOBAL_KEY_FILE` into the test temp directory. It drops `THESIS_PROPOSAL_KEYS` and the key variables, and lets the key-file reader open only files under pytest's temp root. Today a key in the real `~/.config/thesis-proposal/api-keys.env`, or an `api-keys.env` where pytest runs, reaches the suite: `test_openalex_requires_key` would then send a live, keyed OpenAlex request. A test proves that neither real path is opened.
- **`docs/backlog.md`.** The "arXiv and snowball bot checks" entry is removed in the implementing commit. Snowball already went through `http_json`, and arXiv now does too. Two remaining gaps get entries:
  - `poe lit-live` checks DBLP only (working name `widen-lit-live`);
  - the browser-fallback section has no Atom variant for arXiv (deferred by the maintainer, 2026-10-13).
- **Unchanged:** the `sources: …` summary line (byte for byte), every JSON diagnostic's wording, the `"{source}: HTTP {code}"` form `validate_refs.py` matches, exit codes, `poe lit-live`, and every `SKILL.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-lit-search`:
  - "Multi-source federation with graceful degradation": an unanticipated failure is noted by source and error type only; snowballing prints a repeated note once per run; the summary line keeps its form. Two new scenarios cover these.
  - "Verification pages passed or explained": every source is requested over HTTPS, and arXiv's Atom feed is classified like JSON. Feeds are parsed only when they start as the feed element. Markers inside a valid answer never make it a verification page. HTTP statuses outside 429/500/502/503 are not retried. API keys, access tokens and the server's reason phrase join the diagnostics' exclusion list. New arXiv scenarios cover these.

## Impact

- `skills/proposal-lit-search/scripts/common.py`: one request path for both formats; `http_xml` replaces `http_text`; the `malformed` kind. It is regenerated into `skills/proposal-import/scripts/` and `skills/proposal-reverse/scripts/` by `scripts/sync_shared.py`. The JSON path stays byte-identical in behaviour and wording, so `validate_refs.py` is untouched.
- `skills/proposal-lit-search/scripts/arxiv.py`: HTTPS base URL, `http_xml`, and the feed root named once. `_parse_feed`'s own error message goes.
- `skills/proposal-lit-search/scripts/search.py`: the catch-all note only (line 56). The `sources:` line is not touched; `tests/unit/test_install_docs.py` pins its prefix for the readiness guide.
- `skills/proposal-lit-search/scripts/snowball.py`: notes printed once per run, and the catch-all note names the type only.
- Tests:
  - `tests/unit/test_lit_http.py`: XML classification, retries and leak cases over the existing `server` fixture; distinctive cookie, key and token values; the HTTPS guard.
  - `tests/unit/test_lit_search_cli.py`: catch-all notes and snowball de-duplication, in-process through `main(argv)`.
  - `tests/unit/test_lit_parsers.py`: the arXiv test patches `http_xml`.
  - New synthetic fixture `tests/unit/data/arxiv_empty.xml`.
  - `tests/conftest.py`: autouse key-file isolation.
  - `tests/unit/test_lit_common.py`: the never-opened proof.
- `docs/backlog.md`: one entry removed, two added.
- No new dependency: `xml.etree.ElementTree` is standard library. No `SKILL.md` changes, so nothing is shared with `tighten-proposal-family`. `add-setup-readiness-guide`'s `SKILL.md` edit is already on `main`.
