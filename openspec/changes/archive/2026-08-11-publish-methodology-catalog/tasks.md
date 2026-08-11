## 1. Catalog

- [x] 1.1 Write `docs/methodology-catalog.md` with ready-to-paste TOML declarations for Action Research, Simulation Study, Systematic Mapping Study, Repository Mining, Replication Study, and Mixed Methods (scope warning + Integration Plan subsection), plus the Design-Science-is-a-rename note.
- [x] 1.2 Keep every declaration in the exact format the workspace `guidelines.md` accepts (validated shape: title en/de, subsections with en/de/guidance).

## 2. README

- [x] 2.1 Extend the "For supervisors" section: the methodology set is per-workspace configurable (add/replace/disable), `proposal-customize` writes the file, the catalog has ready declarations, and `tests/fixtures/w04-methodology-branch/guidelines.md` is a working example.

## 3. Verify

- [x] 3.1 `uv run poe test` green.
- [x] 3.2 `openspec validate --all --strict` green.
