# Proposal

## Why

`uv run poe lit-live` sends one DBLP query. The other five sources of `proposal-lit-search` (Crossref, arXiv, Semantic Scholar, OpenCitations, OpenAlex) are checked only against local fixtures. A new verification gate or a changed answer shape at one of them therefore first shows up in a student's run, not on the developer's machine. The just-archived `classify-arxiv-answers` change recorded this gap as its Non-Goal and Risk, and `docs/backlog.md` carries it as `widen-lit-live`. That change also made every source failure carry a classified `SourceError.kind` and `status`. A live check can now name the cause of each failure without printing server text.

## What Changes

- New dev script `harness/lit_live.py` makes one read-only request per source module of `proposal-lit-search`, through the shipped modules, so the real parsers and the `common` throttling, retry and verification handling are what is exercised:
  - `search` for dblp, crossref, arxiv and semantic_scholar, with one fixed query;
  - `references` of one fixed, stable DOI for opencitations;
  - `search` for openalex, but only when `common.get_key("OPENALEX_API_KEY")` finds a key. Without one the source reads `skipped (no key)`, which is not a failure.
- It prints one line per source, built only from the result count or from the classified `SourceError.kind` and `status`. It never prints server text, URLs, exception messages or key values. Examples: `dblp ok (3)`, `arxiv challenge`, `semantic_scholar busy (HTTP 429)`, `openalex skipped (no key)`.
- Exit 1 means the code needs to change: a verification page that was not passed, an `unexpected` or `malformed` answer, an HTTP status outside the transient set, zero hits for the fixed request, or an unclassified failure. Exit 0 covers successes and transient failures (`busy`: HTTP 429, any 5xx, network). Today's meaning holds: when DBLP's verification page can no longer be passed, the check exits 1.
- `--sources` selects a subset; the default is all six.
- `poe lit-live` is repointed from `search.py pentest --sources dblp --limit 3` to the new script. It stays local only: it is not part of `poe test` and not part of CI, it calls no model, and it never loads the repository's dev `.env`.
- Documentation follows. The `AGENTS.md` command line and the pyproject comment above the task describe the new scope. The `widen-lit-live` entry is removed from `docs/backlog.md`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. This is dev-side tooling: no shipped skill, script or spec-level behaviour changes, so the change sets `skip_specs: true`.

## Impact

- New: `harness/lit_live.py`, `tests/unit/test_lit_live.py`.
- Changed: `pyproject.toml` (the `lit-live` task and its comment), `AGENTS.md` (the command list), `docs/backlog.md` (the entry is removed).
- No change to `skills/`, so no generated copy and no sync run is involved.
- Network: one manual run sends about six read-only requests, plus whatever the shipped `common` retry and verification pass add. The suite stays offline: L0 tests stub the source modules.
