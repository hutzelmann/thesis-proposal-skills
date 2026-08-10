## 1. Structured data

- [x] 1.1 Add `"max_count": 5` to the `research_questions` block in `shared/structure.json`.
- [x] 1.2 Run `python3 scripts/sync_shared.py` and confirm the five generated `structure.json` copies pick it up.

## 2. Check

- [x] 2.1 In `skills/proposal-check/scripts/check.py`, report an error when the ordered-list item count exceeds the bound, naming both the count found and the bound.
- [x] 2.2 Read the bound with `.get()` so a workspace or an older structure file without the key disables the rule rather than crashing.

## 3. Prose

- [x] 3.1 State the bound in the research-questions section of `shared/guidelines/guidelines.md`, naming undecided scope as the failure it detects.
- [x] 3.2 Re-sync the generated `guidelines.md` copies.

## 4. Tests

- [x] 4.1 Add an L0 test that a proposal with six research questions errors and names the count.
- [x] 4.2 Add an L0 test that a proposal at exactly the bound passes.
- [x] 4.3 Confirm no fixture oracle changes — no fixture declares more than three questions.

## 5. Verify

- [x] 5.1 `uv run poe test` green.
- [x] 5.2 `openspec validate --all --strict` green.
