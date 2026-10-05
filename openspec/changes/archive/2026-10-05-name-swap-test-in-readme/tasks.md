# Tasks

## 1. Guard first

- [x] 1.1 Add `README.md` to the sites in `tests/unit/test_substance_tests.py`; with the README still reading "anti-generic", run `uv run pytest tests/unit/test_substance_tests.py` and confirm exactly `test_enumerations_name_the_whole_set[README.md]` fails — record the result here.
  Evidence: 105 passed, 1 failed — `README.md enumerates the substance tests as ['delta', 'executability', 'falsifiability', 'method-fit', 'necessity'], but shared/guidelines/guidelines.md names [… 'swap']`, quoting the run. The README's count test ("six named tests") passed, so the README adds no other match.

## 2. Fix the name

- [x] 2.1 Replace "anti-generic" with "swap" in the README's substance-test enumeration and rerun the guard; verify it passes, then set the word back temporarily, confirm the same failure, and restore — record the result here.
  Evidence: fixed → 106 passed; set back to "anti-generic" → 1 failed, 105 passed (`test_enumerations_name_the_whole_set[README.md]`); restored → 106 passed.
- [x] 2.2 Confirm no other mention names the test "anti-generic" (`grep -rn -i anti-generic` over the tree, excluding `.git`, `.venv` and archived changes); verify only this change's own files match.
  Evidence: matches only in this change's proposal, design and tasks, and in the sentence of the guard's docstring that records the drift (2.3); none in `README.md`, `docs/`, any `SKILL.md`, `shared/` or `harness/`.
- [x] 2.3 Add the README to the scope description in the module docstring of `tests/unit/test_substance_tests.py`; verify by reading it.

## 3. Verify

- [x] 3.1 `uv run poe test` and `uv run poe specs` green.
