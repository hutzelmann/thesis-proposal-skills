# Tasks: extract-shared-guidance

## 1. Shared source

- [x] 1.1 Write `shared/structure.json`: en+de canonical titles, order, methodology table, forbidden-heading patterns, min_references, RQ conventions
- [x] 1.2 Write `shared/guidelines/guidelines.md`: prose guidance distilled from AGENTS.md, markdown/CSL conventions replacing LaTeX rules

## 2. Sync mechanism

- [x] 2.1 Write `scripts/sync_shared.py` (deterministic, GENERATED markers, `--check` mode)
- [x] 2.2 Run sync; verify skill `references/` trees materialize

## 3. Tests

- [x] 3.1 `tests/unit/test_sync.py`: `--check` passes when synced, fails on tampered copy
- [x] 3.2 `tests/unit/test_structure_drift.py`: every structure.json title appears verbatim in prose guidelines (en+de)
- [x] 3.3 `uv run pytest` green; commit
