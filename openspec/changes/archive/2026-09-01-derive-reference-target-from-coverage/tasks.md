# Tasks

## 1. Structured data and prose

- [x] 1.1 Add `min_per_1000_words: 4` to `references` in `shared/structure.json` with a `_references_comment` marking it an estimation constant and naming its derivation (coverage rules → 10–15 at the default length)
- [x] 1.2 Rewrite the reference-target sentence in `shared/guidelines/guidelines.md` (Literature and Citations): derive the range from coverage (clusters ≥ 2 sources, RQ grounding, introduction grounding), state it as ~4–6 per 1000 words scaling with length, keep the floor sentence and the workspace-override note

## 2. Check script

- [x] 2.1 Extract the body word count from `rule_length` into a shared helper used by both rules
- [x] 2.2 Add `rule_reference_density`: warn below `ceil(words × density / 1000)`, suppress while the effective floor is unmet, `0` disables, invalid override reports `reference-density-invalid` and degrades to the default
- [x] 2.3 Register `reference-density-low` and `reference-density-invalid` in `RULE_IDS`; add `("references", "min_per_1000_words")` to `OVERRIDABLE`; wire the rule into `RULES`

## 3. Documentation surface

- [x] 3.1 Add `min_per_1000_words = 4` beside `min_count` in the `proposal-customize` SKILL.md TOML example

## 4. Tests and sync

- [x] 4.1 Unit tests in `tests/unit/test_check_rules.py`: fires on a long thin proposal, silent on short drafts, suppressed under the floor error, respects override, `0` disables, invalid degrades; add both ids to `COVERED_BY_UNIT_TESTS`
- [x] 4.2 End-to-end invalid-override message test in `tests/unit/test_check.py` mirroring the `min_count` one
- [x] 4.3 Run `python3 scripts/sync_shared.py`; verify no fixture oracle drifts (`uv run poe test`)
- [x] 4.4 `openspec validate --all --strict` green
