# Tasks

## 1. Guard first

- [x] 1.1 Widen `_COUNT` in `tests/unit/test_substance_tests.py` with the clause-keyed branch from design.md and add a table-driven test of the pattern (set claims matched, evidence bars and the testing-harness fixture sentence not); verify the table test passes.
- [x] 1.2 With the guidance still reading "Five tests define the substance bar", run `uv run pytest tests/unit/test_substance_tests.py` and confirm `test_counts_agree_with_the_set[shared/guidelines/guidelines.md]` fails naming "Five tests" — record the result here.
  Evidence: 103 passed, 1 failed — `test_counts_agree_with_the_set[shared/guidelines/guidelines.md]`: `shared/guidelines/guidelines.md says "Five tests", but … names 6 (six)`. Before the widening the same file passed with "Five" (the drift shipped green on `5437e66`).

## 2. Fix the count

- [x] 2.1 Change "Five tests define the substance bar" to "Six tests define the substance bar" in `shared/guidelines/guidelines.md` and run `python3 scripts/sync_shared.py`; verify every `skills/*/references/guidelines.md` copy reads "Six tests" and `python3 scripts/sync_shared.py --check` is clean.
  Evidence: the five copies (customize, ideate, review, supervise, write) each contain "Six tests define" once; `--check` reports "generated copies in sync".
- [x] 2.2 Rerun `uv run pytest tests/unit/test_substance_tests.py` and confirm the guidance site passes — record the result here.
  Evidence: 104 passed with "Six". The round trip was then repeated on the fixed file: wording temporarily set back to "Five" → 103 passed, 1 failed (same test, same message); restored to "Six" → 104 passed.
- [x] 2.3 Confirm no other prose states the substance-test count wrongly (`grep -rn -i 'five tests\|fünf'` over `shared/`, `skills/`, `README.md`, `docs/`): only generated copies matched before the sync, none after.
  Evidence: before the sync the only matches were the source line and its five generated copies; after it, no match. The guidance has no German rendering of the sentence. Other count sites (two `SKILL.md` bodies, two pins, four specs, README) already say six.

## 3. Verify

- [x] 3.1 `uv run poe test` and `uv run poe specs` green.
