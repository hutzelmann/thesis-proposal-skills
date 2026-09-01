# Tasks

## 1. Guard first (gate before refactor)

- [x] 1.1 Extend `tests/unit/test_script_paths.py`: parametrized assertion over all `skills/proposal-*/SKILL.md` that the text does not contain "so use that location"; run it and confirm it fails on the five current files.

## 2. Reword the five fallback paragraphs

- [x] 2.1 `skills/proposal-write/SKILL.md`: replace "so use that location" with the import wording verbatim (design.md — Replacement paragraphs).
- [x] 2.2 `skills/proposal-check/SKILL.md`: drop the clause to the omission shape used by proposal-supervise/proposal-reverse.
- [x] 2.3 `skills/proposal-lit-search/SKILL.md`: import shape with the `api-keys.env` stake clause.
- [x] 2.4 `skills/proposal-publish/SKILL.md`: import shape with the outputs/workspace-build stake clause.
- [x] 2.5 `skills/proposal-troubleshoot/SKILL.md`: import shape with the report-bundle stake clause; sibling-skill sentence and closing sentence unchanged.

## 3. Verify

- [x] 3.1 `uv run poe test` green (includes the new guard, header-pattern, pinned-sentence, and drift checks — confirms no pin or materialized block was touched).
- [x] 3.2 `openspec validate --all --strict` passes.
