## 1. Guidance citations

- [x] 1.1 Close each of the seven branch contracts in `shared/guidelines/guidelines.md` with a one-sentence provenance citation.

## 2. Sources document

- [x] 2.1 Write `docs/methodology-sources.md`: per-branch provenance (taxonomy source, contract source, deliberate compressions) and the set-level argument (expressiveness, the default bar, why DSR, Mixed Methods, Grounded Theory, and Simulation are not defaults).
- [x] 2.2 Link the page from the README.

## 3. Sync and verify

- [x] 3.1 Run `python3 scripts/sync_shared.py`.
- [x] 3.2 `uv run poe test` green.
- [x] 3.3 `openspec validate --all --strict` green.
