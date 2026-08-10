## 1. Per-case staging

- [x] 1.1 `files_named(utterance)` — pure function returning the fixture filenames a sentence names, sharing its token rule with the existing L0 test rather than reimplementing it
- [x] 1.2 `stage_workspace(ws, case)` stages exactly those files, or `DEFAULT_PROPOSAL` when the utterance names none
- [x] 1.3 A named file the suite cannot stage raises rather than measuring against an incomplete workspace
- [x] 1.4 L0 tests: names one file, names two, names none, names an unstageable file; the ten skills are installed either way

## 2. Uniform epochs

- [x] 2.1 Replace `COLLISION_EPOCHS` with a single `DEFAULT_EPOCHS = 3`; `--epochs` still overrides
- [x] 2.2 Report states the epoch count used, and reports per-case failures as a rate out of the epochs actually run
- [x] 2.3 L0 test: a case failing 1 of 3 renders as a rate, not as a bare failure

## 3. Conditions marker

- [x] 3.1 `--conditions-changed` flag: the report records the earlier score as measured under different conditions instead of as superseded
- [x] 3.2 L0 test for both renderings

## 4. Re-baseline

- [x] 4.1 `uv run poe test` green
- [x] 4.2 Sweep on sonnet with the corrected staging and uniform epochs, run with `--conditions-changed`
- [x] 4.3 Compare against the five outstanding failures case by case: which were rig artifacts, which survive as description defects
- [x] 4.4 Supersede the `litsearch-collision` reading in `harness/README.md` with what the corrected run shows
- [x] 4.5 `openspec validate --all --strict` green
