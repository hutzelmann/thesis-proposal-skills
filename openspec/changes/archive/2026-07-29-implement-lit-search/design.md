# Design: implement-lit-search

## Context

skill-lit-search spec + S6 key rules + verified API facts (2026-07): DBLP/Crossref/arXiv/OpenCitations keyless; Semantic Scholar keyless-throttled (no key by policy); OpenAlex key-gated (env). ACM/IEEE content flows through these aggregators.

## Decisions

- **D-LS-1 — Client contract.** Every source module exposes `search(query, limit=10) -> list[dict]` returning CSL-JSON-shaped dicts (`title`, `author` [{family, given}], `issued` {year}, `container-title`, `DOI`, `URL` only when no DOI, `abstract` when available, `type`) plus `_source` provenance. Sources supporting the citation graph add `references(doi)` / `citations(doi)`. Failures raise `common.SourceError`; orchestrators catch and degrade with a note — never block.
- **D-LS-2 — common.py owns cross-cutting concerns**: urllib JSON fetch with timeout/retry/backoff (429/5xx), per-source min-interval throttling, polite User-Agent with optional `CONTACT_EMAIL`, `normalize_title`, `dedupe` (DOI first, normalized title second), `make_key` (AuthorYearFirstWord, <20 chars), CSL-YAML emission.
- **D-LS-3 — Orchestrators are thin**: `search.py` fans out to all available sources, merges, dedupes, prefers entries with DOI+abstract, emits CSL-YAML to stdout; relevance judgment stays with the agent (spec). `snowball.py` takes seed DOIs, pulls references/citations from graph-capable sources, merges the same way.
- **D-LS-4 — Missing key = silent source skip with stderr note** (openalex without `OPENALEX_API_KEY` reports "skipped (no key)"); orchestrator output states which sources contributed.
- **D-LS-5 — Tests are offline**: canned real API responses stored under `tests/unit/data/`, parse/normalize/dedupe tested against them; live round-trips behind `@pytest.mark.live`, deselected by default (`-m "not live"` in config).

## Risks / Trade-offs

- API response shapes drift → canned samples pin the parser contract; live marker tests catch drift when run deliberately.
- Semantic Scholar shared pool may 429 during skill use → per-source backoff + degradation note covers it (spec scenario).
