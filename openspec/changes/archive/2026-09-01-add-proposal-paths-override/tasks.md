# Tasks: workspace proposal-location override

## 1. Structured data and check mechanics

- [x] 1.1 Add `[paths]` node (`proposals = "."`, with a `_paths_comment` explaining anchor + family rule) to `shared/structure.json`
- [x] 1.2 `check.py`: extend `load_overrides` to the resolution chain (explicit > `proposal.parent` > `Path.cwd()`); first file found governs the whole run
- [x] 1.3 `check.py`: add `(paths, proposals)` to `OVERRIDABLE`; value validation rule `paths-proposals-invalid` (string, relative, no `..`/absolute/`~`; error + default fallback)
- [x] 1.4 `check.py`: misplacement rule `proposal-misplaced` (governing file sets non-`"."` value and `proposal.parent` ≠ governing-dir/value; error names expected directory and governing file)
- [x] 1.5 Run `python3 scripts/sync_shared.py`; confirm the 7 structure.json and 4 check.py copies regenerate

## 2. L0 tests

- [x] 2.1 `test_check.py`: chain order (beside-proposal wins over cwd; whole file governs, no key merging; cwd position found when beside-proposal missing; no file anywhere → defaults). Tests that chdir or pass `--guidelines` to stay hermetic
- [x] 2.2 `test_check.py`: `paths-proposals-invalid` for absolute, `..`-escaping, `~`-anchored, and non-string values; unknown `[paths]` leaf → `override-key-unknown`
- [x] 2.3 `test_check.py`: `proposal-misplaced` fires on a straggler in the root, silent when unset, silent when the proposal is in the configured directory
- [x] 2.4 New fixture `tests/fixtures/w07-paths-workspace/` (w06 was taken by the reverse harvest; `expected.json` at the fixture root like every oracle, proposal inside `proposals/`); oracle tests run the check from the fixture root (the workspace anchor) and, like the export-matrix corpus, look one level down; new rule ids declared in `RULE_IDS` + `COVERED_BY_UNIT_TESTS`. Also fixed in passing: `sync_shared.py` now writes atomically and skips unchanged files — a real sync running inside the parallel suite was truncating `structure.json` under concurrent readers (flake seen three times)
- [x] 2.5 `tests/fixtures/README.md`: document w07

## 3. SKILL.md wording (source of truth: D6 in design.md)

- [x] 3.1 proposal-check: target-resolution + guidelines-lookup wording (chain, workspace root)
- [x] 3.2 proposal-import: output-location wording; edit pinned sentence `tests/unit/data/pinned_sentences/proposal-import--output-location.txt` in the same commit
- [x] 3.3 proposal-write: creation wording (apply-review wording already location-neutral: the review sits beside the proposal)
- [x] 3.4 proposal-reverse: add explicit proposal-location statement (closes the silence gap)
- [x] 3.5 proposal-supervise: normalized-file wording (artifact wording already proposal-relative)
- [x] 3.6 proposal-review: target wording added; output already "next to the proposal"
- [x] 3.7 proposal-ideate: seed wording; notes stay beside the proposal
- [x] 3.8 proposal-publish + proposal-troubleshoot: target-discovery wording only
- [x] 3.9 proposal-customize: document the `[paths]` namespace, value constraints, move-consequences dialog
- [x] 3.10 Import's mandate also carried "working directory": mandate + pinned mandate copy + pinned output-location sentence updated together; header/pin suites green

## 4. Docs and gate

- [x] 4.1 README ("For supervisors" + student sections) and `docs/getting-started.md`: name the override with the w07 fixture as working example
- [x] 4.2 `uv run poe test` green (1484 passed incl. slow lane; ruff clean; drift clean; 11 skills conform); `uv run poe specs` green (18/18)
- [x] 4.3 `uv run poe cov` — 81.01% ≥ 78% floor
