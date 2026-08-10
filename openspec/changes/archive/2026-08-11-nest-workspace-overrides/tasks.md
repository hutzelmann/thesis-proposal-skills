## 1. Normalize the structured data

- [x] 1.1 In `shared/structure.json`, move `min_references` to `references.min_count`.
- [x] 1.2 Move `forbidden_heading_patterns`, `work_plan_heading_patterns` and `confidentiality_patterns` into a `forbidden` table as `heading_patterns`, `work_plan_patterns`, `confidentiality_patterns`.
- [x] 1.3 Move `todo_marker` to `todo.marker`.
- [x] 1.4 Rename `timeline.default_detail` to `timeline.detail` — a workspace sets the effective value, so "default" was wrong in the name of the overridden thing.
- [x] 1.5 Keep every value identical; this task changes paths only.

## 2. Resolve overrides by path

- [x] 2.1 Add a resolver to `check.py` that returns the workspace value when the workspace set that leaf, else the shipped default, taking the table and key names.
- [x] 2.2 Replace all six flat override reads with resolver calls.
- [x] 2.3 Replace all structure reads with the new paths.
- [x] 2.4 Make the research-question bounds overridable through the same resolver.

## 3. Break loudly

- [x] 3.1 Add a retired-key map: each pre-migration key to its replacement path.
- [x] 3.2 Report a retired key as an error naming the replacement; do not honour it.
- [x] 3.3 Report an override key that is neither retired nor overridable as an error naming the key, since a typo and a retired key are the same failure from the user's side.
- [x] 3.4 Keep the existing TOML parse-error finding working.

## 4. Documentation and fixtures

- [x] 4.1 Update the TOML example and merge-semantics text in `skills/proposal-customize/SKILL.md`, and add the migrate-on-encounter instruction.
- [x] 4.2 Update every override key named in `shared/guidelines/guidelines.md`.
- [x] 4.3 Rewrite `tests/fixtures/w02-override-workspace/guidelines.md` in the new shape, keeping the same effective settings so its oracle holds.
- [x] 4.4 Update `tests/fixtures/README.md` where it names override keys.

## 5. Tests

- [x] 5.1 Update existing tests naming override keys (`test_check.py`, `test_check_rules.py`, `test_timeline_section.py`, `test_harness_helpers.py`, `harness/l1_checks.py`).
- [x] 5.2 Add an L0 test that each retired key produces an error naming its replacement.
- [x] 5.3 Add an L0 test that an unknown override key errors.
- [x] 5.4 Add an L0 test that the research-question bounds are overridable in both directions.

## 6. Sync and verify

- [x] 6.1 Run `python3 scripts/sync_shared.py`.
- [x] 6.2 `uv run poe test` green.
- [x] 6.3 `uv run poe cov` holds the floor.
- [x] 6.4 `openspec validate --all --strict` green.
