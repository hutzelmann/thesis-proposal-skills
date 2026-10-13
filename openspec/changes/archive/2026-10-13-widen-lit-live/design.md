# Design

## Context

`poe lit-live` was added by `pass-source-verification` (its D9) as one DBLP query through `search.py`. It is networked and read-only, and it stays out of `poe test` and CI. Since `classify-arxiv-answers`, every failure that `common.http_json` or `common.http_xml` raises is a `SourceError` with a `kind` from a fixed vocabulary (`challenge`, `unexpected`, `malformed`, `http`, `network`) and a numeric `status` where one exists. Errors that the source modules raise themselves (a missing key, an empty DOI) carry `kind` None. `search.py` federates dblp, crossref, arxiv, semantic_scholar and openalex. `snowball.py` walks semantic_scholar, openalex, crossref and opencitations. OpenCitations is graph-only: it has no `search()`.

The maintainer approved the design in the session chat on 2026-10-13: "Approve as described (Recommended)". The decisions below record it.

## Goals / Non-Goals

**Goals:**
- Exercise each source module's live path: request, verification pass, retry, decoding and parser.
- Print a cause the developer can act on, in the same classified vocabulary the scripts use.
- Keep the exit code meaningful for a script or a human: 1 means change the code, 0 means nothing to do.

**Non-Goals:**
- Covering each endpoint. One request per module: no `citations`, no `recommendations`, no Crossref or Semantic Scholar `references`, no `validate_refs.py` lookups.
- Running in CI, in `poe test` or on a schedule. An external block or rate limit must never make the suite flaky.
- Changing any shipped script, diagnostic or exit code under `skills/`.
- Passing a proof-of-work verification tier, or touching the browser fallback.

## Decisions

**D1 — Through the shipped modules, from their own directory.** `harness/lit_live.py` imports `common`, `dblp`, `crossref`, `arxiv`, `semantic_scholar`, `opencitations` and `openalex` by their top-level names. That is how the modules import each other. When the script runs as `python3 harness/lit_live.py`, it puts `skills/proposal-lit-search/scripts` at the front of `sys.path`, but only if that directory is not already there. Under pytest, the configured `pythonpath` already lists it, ahead of the `proposal-import` copies. So tests import the same modules and the script does not mutate the path at all. The `sys.path` ban in `test_repo_conventions.py` covers `tests/` only; `harness/eval_export.py` and `harness/skill_evals.py` adjust the path the same way for their own directory.
- Rejected: `importlib.util.spec_from_file_location`, which `l1_checks.py` uses for `check.py`. The source modules `import common` by name, so their directory must be importable anyway.
- Rejected: a `PYTHONPATH` in the poe task's `env`. The script would no longer run on its own, and the path would be defined in a second place.

**D2 — A static probe table, one request per module.** `PROBES` maps each source name to its module, the request it makes, and an optional key name, in the style of `search.py`'s "static registry". The constants:
- `QUERY = "pentest"` and `LIMIT = 3`, which are today's DBLP query and limit. dblp, crossref, arxiv, semantic_scholar and openalex make `search(QUERY, limit=LIMIT)`.
- opencitations makes `references(SEED_DOI, LIMIT)` with `SEED_DOI = "10.1145/3292500.3330919"`. That is the work whose references `tests/unit/data/opencitations_refs_sample.json` captured live on 2026-07-29, so it is known to the index. OpenCitations maps an HTTP 404 to an empty list, so an unknown seed reads as zero hits.

An L0 test asserts that `PROBES` covers every name in `search.SEARCH_SOURCES` and `snowball.GRAPH_SOURCES`. A source added to the skill without a live probe then fails the suite. Without that test, the live check would quietly stop covering the skill.

**D3 — OpenAlex is key-gated, resolved the shipped way.** Before the request, the script calls `common.get_key("OPENALEX_API_KEY")`. That lookup checks the environment, then `$THESIS_PROPOSAL_KEYS`, then `api-keys.env` in the working directory, then `~/.config/thesis-proposal/api-keys.env`. No key gives `skipped (no key)` with exit 0, since a missing key is configuration, not drift. The module itself sends the key. `lit_live.py` never prints it, never logs it, and never reads the repository's dev `.env`. The `lit-live` poe task has no `envfile`, and an L0 test pins both the command and the missing `envfile`.

**D4 — The verdict vocabulary.** A pure function maps each outcome to a `Verdict(label, needs_change)` dataclass. The printed line is `<source> <label>`. A label is built only from the result count, the classified `kind`, the integer `status`, or an exception's class name. Server text, URLs, queries and exception messages never appear in it.

| Outcome | Label | Needs change (exit 1) |
|---|---|---|
| n > 0 results | `ok (n)` | no |
| zero results | `empty (0)` | yes: parser or query drift |
| key-gated, no key | `skipped (no key)` | no |
| `kind="network"` | `busy (network)` | no |
| `kind="http"`, status 429 or any 5xx | `busy (HTTP s)` | no |
| `kind="http"`, any other status (400, 404, 410, …) | `http (HTTP s)` | yes: the API changed |
| `kind="challenge"` | `challenge (HTTP s)` | yes: verification page not passed |
| `kind="unexpected"` / `"malformed"` | `unexpected (HTTP s)` / `malformed (HTTP s)` | yes |
| `SourceError` with another or no kind | `unclassified` | yes |
| any other exception | `crashed (<ExceptionType>)` | yes |

`(HTTP s)` is appended whenever the error carries an integer status. The transient set is HTTP 429 and every 5xx, as approved: a server fault or a rate limit never means the API changed, so it never asks for a code change. It contains `common.RETRY_CODES` (429, 500, 502, 503), which the shipped client has already retried twice with backoff; a 504, which the client does not retry, still reads `busy`. An implementation draft tied `busy` to `common.RETRY_CODES` alone and counted 504 as a change signal; the maintainer's approved design said 429/5xx, so the wider set stands. Today's meaning of exit 1 holds: DBLP's unpassed verification page is `challenge`.

**D5 — Output and exit.** Each selected source gets one stdout line, in table order: dblp, crossref, arxiv, semantic_scholar, opencitations, openalex. The exit code is 1 if any verdict needs a change, otherwise 0. `--sources a,b` selects a subset. An unknown name is a usage error (exit 2) that lists the valid names, as `search.py` does. The entry point is `main(argv: list[str] | None = None) -> int`.

**D6 — Tests are offline.** `tests/unit/test_lit_live.py` stubs the probe table with in-process fakes; no socket opens. The conftest autouse fixture already blinds the developer's key files and drops `OPENALEX_API_KEY`. So the no-key path is the default in L0, and the keyed path sets the variable through `monkeypatch`. The tests cover:
- the verdict table, cell by cell;
- exit codes for all-ok, busy-only, and mixed results;
- `--sources` selection and refusal;
- that neither a leaky exception message nor a key value reaches the output;
- probe coverage of both orchestrator registries;
- the poe task line.

## Risks / Trade-offs

- [The fixed query or seed stops returning hits at one source] → that source reads `empty (0)` and the check exits 1. The developer confirms by hand and changes the constant in a reviewed edit. A false alarm costs a look; a silent zero would cost a student's run.
- [Semantic Scholar's keyless pool answers 429 often] → it reads `busy (HTTP 429)` with exit 0, after the shipped retry ran. A persistent 429 is visible in the line, but it does not count as a code defect.
- [Retries and DBLP's verification pass raise the request count] → about 6 requests normally. The worst case is three attempts per source plus one pass, all read-only and throttled by `common`. The check runs by hand, never in a loop.
- [A developer's exported `OPENALEX_API_KEY` is used] → intended. That is the shipped resolution order, and the value is never printed.
- [Worst-case runtime with every source timing out] → several minutes (20 s timeout, 3 attempts, 6 sources). That is acceptable for a manual check, and every timeout reads `busy (network)`.

## Migration Plan

None. The poe task name stays the same; only its command and scope change. To roll back, revert the task line.
