## 1. Structured data and prose

- [x] 1.1 Add the `experiment` branch to `shared/structure.json` with both-language titles and the three subsections.
- [x] 1.2 Update `shared/guidelines/guidelines.md`: shipped-set enumeration in the methodology section item, methodology title table, and subsection table rows.
- [x] 1.3 Add the Controlled Experiment content contract to Methodology Content.
- [x] 1.4 Add the User Study boundary sentence to the User Study contract.

## 2. Fixture

- [x] 2.1 Add `tests/fixtures/f23-controlled-experiment/` with a clean proposal using the branch.
- [x] 2.2 Calibrate `expected.json` against the check script.
- [x] 2.3 Document the fixture in `tests/fixtures/README.md`.

## 3. Sync and verify

- [x] 3.1 Run `python3 scripts/sync_shared.py`.
- [x] 3.2 `uv run poe test` green.
- [x] 3.3 `openspec validate --all --strict` green.
