# Tasks — add-proposal-notes-file

## 1. Format definition

- [x] 1.1 Add the companion-notes-file and blocking-TODO-split prose to the write skill's format reference source (`shared/guidelines` stays untouched; the format contract lives in the skills' shared format prose) — verify against the drift-guard test which surfaces state the metadata contract
- [x] 1.2 Confirm no `shared/` guidance edit is needed (formalization boundary: notes file is workflow machinery) — document in commit message

## 2. Skill adoption

- [x] 2.1 `skills/proposal-write/SKILL.md`: read-notes-before-drafting, record decisions, move resolved TODOs to Log, create-only-with-content rule
- [x] 2.2 `skills/proposal-lit-search/SKILL.md`: Excluded Literature recording, no-re-propose rule, never-create rule
- [x] 2.3 `skills/proposal-import/SKILL.md`: seed notes at import (unmapped content, gap list, initial Next Focus), personal-data rules apply
- [x] 2.4 Run `python3 scripts/sync_shared.py` and verify generated copies; mandates byte-identical (`uv run pytest tests/unit/test_skill_header_pattern.py`)

## 3. Harness

- [x] 3.1 `harness/l1_checks.py`: `select_draft` excludes `*.notes.md` (suffix predicate beside `NON_PROPOSAL_MARKDOWN`)
- [x] 3.2 Unit tests: notes file never selected (sorts-first case included); existing selection behavior unchanged

## 4. Verification

- [x] 4.1 `uv run pytest` green, `uv run ruff check .` clean, `python3 scripts/sync_shared.py --check` clean, `openspec validate --all --strict` passes
