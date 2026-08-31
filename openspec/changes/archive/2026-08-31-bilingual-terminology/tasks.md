# Tasks

## 1. Guard

- [x] 1.1 Add `tests/unit/test_bilingual_terminology.py`: blurb sections split on `## English` / `## Deutsch` (assert both found, non-empty); English section has "proposal", no "exposé" (case-insensitive); German section has "Exposé" (accented), and after stripping URLs, backtick spans, and `thesis-proposal-skills` / `proposal-*` identifiers, no standalone "proposal"; failures name file and term.
- [x] 1.2 Same file: assert the German tier line in `skills/proposal-supervise/SKILL.md` carries "Exposé", and `skills/proposal-ideate/SKILL.md` carries the subtitles "Exposé zur Bachelorarbeit" and "Exposé zur Masterarbeit".

## 2. Verification

- [x] 2.1 `uv run poe test` green; `openspec validate --all --strict` green.
- [x] 2.2 Mutation check by hand: flip "Exposés" → "proposals" in the German blurb locally, confirm the new test fails naming the term, revert.
