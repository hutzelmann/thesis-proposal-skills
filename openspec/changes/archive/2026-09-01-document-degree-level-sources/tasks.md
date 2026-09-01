# Tasks

## 1. Write the document

- [x] 1.1 Write `docs/degree-level-sources.md` in the register of `docs/methodology-sources.md`: purpose paragraph naming the 2026-09-01 survey, per-dimension contrast with sources, proposal-level implications, convergence strength, caveats, and the design consequence (same skeleton, level is scope judgement plus workspace configuration).
- [x] 1.2 Cite only sources the survey actually fetched and read; mark single-source claims as illustrative; keep any verbatim fragment under 15 words; note that Berndtsson et al. (2008) was read from a privately held copy that stays outside the repository.

## 2. Verify

- [x] 2.1 Spot-check every cited URL still resolves and the named document carries the claim attributed to it.
- [x] 2.2 Run `uv run poe test` and `openspec validate --all --strict`; confirm no generated copies or shared content changed.
