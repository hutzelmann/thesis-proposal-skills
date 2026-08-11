## 1. Structured data and prose

- [x] 1.1 Add the `model_evaluation` branch to `shared/structure.json` with both-language titles and the three subsections.
- [x] 1.2 Update `shared/guidelines/guidelines.md`: shipped-set enumeration, methodology title table, subsection table rows.
- [x] 1.3 Add the Empirical Model Evaluation content contract to Methodology Content, including the benchmark-study homing sentence.

## 2. Fixture

- [x] 2.1 Add `tests/fixtures/f24-model-evaluation/` with a clean proposal using the branch.
- [x] 2.2 Calibrate `expected.json` against the check script.
- [x] 2.3 Document the fixture in `tests/fixtures/README.md`.

## 3. Sync and verify

- [x] 3.1 Run `python3 scripts/sync_shared.py`.
- [x] 3.2 `uv run poe test` green.
- [x] 3.3 `openspec validate --all --strict` green.
