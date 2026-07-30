## 1. Import guidance

- [x] 1.1 Replace the citation clause in the mapping bullet of `skills/proposal-import/SKILL.md` with the selection rule: author named as the sentence's actor → `@key` with the name removed from the prose; citation as evidence → `[@key]`; never a typed name immediately before a bracketed citation
- [x] 1.2 Point at `../proposal-write/references/guidelines.md` ("Literature and Citations") for the full rule, with the inline fallback for when that skill is not installed — matching how the same file already handles canonical section titles
- [x] 1.3 Cover the author-date source case explicitly, since neither the name nor the year may survive in the prose

## 2. Harness coverage

- [x] 2.1 Extend `import_l1()` in `harness/skill_evals.py` with an assertion that the produced file contains no hand-typed author name immediately before a bracketed citation
- [x] 2.2 Confirm the existing `MESSY_SOURCE` exercises it ("the survey by Rivera et al. 2023", "the LoRa study of Tanaka 2024") so no new fixture is needed

## 3. Verification

- [x] 3.1 `uv run pytest` green (102 passed once the concurrent `anonymous-proposal-author` work landed; its `author:` warning had been tripping `test_clean_fixture_passes`)
- [x] 3.2 `uv run ruff check .` clean
- [x] 3.3 `openspec validate --all --strict` passes
- [x] 3.4 Hand the L1 eval command to the user rather than running it — model runs are metered and this change cannot be verified by L0
