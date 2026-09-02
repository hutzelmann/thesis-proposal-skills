# Tasks

## 1. Write the README adjustment

- [x] 1.1 Draft the README coverage of degree-level tailoring in the README's own register, placed where a student and a supervisor would each look for it: level read from the subtitle only, four graded expectations, the both-directions bar, structure and checks level-blind; Bachelor-side wording stays "not required", never a prohibition; no promise of enforcement or blocking.
- [x] 1.2 In "For supervisors", link `docs/degree-level-sources.md` beside the existing `docs/methodology-sources.md` link and reconcile the "explicit contribution over the state of the art" clause with the graded expectation.
- [x] 1.3 Verify every claim in the new text against `shared/guidelines/guidelines.md` (Degree Level), the five tailored `SKILL.md` bodies, and `docs/degree-level-sources.md`; nothing beyond what landed in `2026-09-02-add-degree-level-tailoring`.

## 2. Verify

- [x] 2.1 Confirm with a diff that only the intended README hunks changed: model-support marker block, install command, session excerpts, badges and divergence table untouched; the "six rules" count correct if that list changed.
- [x] 2.2 Run `uv run poe test` and `openspec validate --all --strict`; confirm no generated copies or shared content changed.
