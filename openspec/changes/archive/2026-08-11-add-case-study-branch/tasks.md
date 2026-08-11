## 1. Structured data and prose

- [x] 1.1 Add the `case_study` branch to `shared/structure.json` with both-language titles and the three subsections.
- [x] 1.2 Update `shared/guidelines/guidelines.md`: shipped-set enumeration, methodology title table, subsection table rows.
- [x] 1.3 Add the Case Study content contract to Methodology Content, including the observation-versus-intervention boundary note.

## 2. Fixtures

- [x] 2.1 Add `tests/fixtures/f25-case-study/` from the former w04 proposal, retitled to the shipped subsections and extended with units of analysis, selection rationale, triangulation, and the method-fit opener.
- [x] 2.2 Calibrate f25's `expected.json` against the check script.
- [x] 2.3 Rewrite `tests/fixtures/w04-methodology-branch/`: workspace guidelines declare Action Research with per-subsection guidance (theoretical stays disabled), a new proposal uses it, and `expected.json` semantics name Action Research as the not-shipped branch.
- [x] 2.4 Calibrate w04's `expected.json` against the check script.
- [x] 2.5 Update both rows in `tests/fixtures/README.md`.

## 3. Sync and verify

- [x] 3.1 Run `python3 scripts/sync_shared.py`.
- [x] 3.2 `uv run poe test` green.
- [x] 3.3 `openspec validate --all --strict` green.
