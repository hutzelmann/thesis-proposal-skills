## 1. Whole-section pins

- [x] 1.1 Replace `tests/unit/data/pinned_sentences/proposal-review--execution-shape.txt` with the full `## Execution shape` section of `skills/proposal-review/SKILL.md` (heading through the last paragraph before `## What to assess`).
- [x] 1.2 Same for `proposal-supervise--execution-shape.txt` (through the paragraph before `## Normalize the submission`).
- [x] 1.3 Same for `proposal-check--execution-shape.txt` (through the paragraph before `## Target`).
- [x] 1.4 Same for `proposal-write--execution-shape.txt` (through the paragraph before `## Ground rules`).

## 2. Position and equality test

- [x] 2.1 Add `tests/unit/test_execution_shape.py`: discover skills from `pinned_sentences/*--execution-shape.txt`; assert the corpus is non-empty; per skill assert the first `## ` heading of the SKILL.md body is `## Execution shape` and that the section text (heading to the next `## `, stripped) equals the pin (stripped). Import paths via the configured `pythonpath`, no `sys.path` edits.

## 3. Verify

- [x] 3.1 `uv run poe test` green (pinned sentences still contain the four pins; new test passes for all four; header-pattern and report-offer untouched).
- [x] 3.2 `openspec validate --all --strict` passes.
- [x] 3.3 Negative check by hand, not committed: temporarily remove the second paragraph of one section and confirm the new test names the skill; restore.
