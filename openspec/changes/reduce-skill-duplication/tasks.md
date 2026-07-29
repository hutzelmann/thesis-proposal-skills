# Tasks — reduce-skill-duplication

## 1. Ideate goes sibling-fallback (D1, D2)

- [x] 1.1 Rewrite the grounding section of `skills/proposal-ideate/SKILL.md`: sibling reference to `../proposal-lit-search/scripts/search.py` when installed; agent-fetch fallback with the three API URL templates (Crossref, DBLP, arXiv) inlined; ungrounded-notice behavior unchanged
- [x] 1.2 Remove the nine ideate script entries from SYNC_MAP in `scripts/sync_shared.py` (keep `common`/`crossref` → import and the guidelines/structure entries)
- [x] 1.3 Delete `skills/proposal-ideate/scripts/` (all nine vendored copies plus `__pycache__`)
- [x] 1.4 Run `python3 scripts/sync_shared.py --check` and the L0 suite; sweep tests/harness for references to `proposal-ideate/scripts` and fix any

## 2. Commit-time sync hook (D3)

- [x] 2.1 Add committed `.githooks/pre-commit` running `scripts/sync_shared.py` and auto-staging regenerated SYNC_MAP destinations
- [x] 2.2 Activate locally (`git config core.hooksPath .githooks`) and document the one-time activation in the README dev section (update the existing sync sentence around line 45)
- [x] 2.3 Verify end-to-end: edit `shared/guidelines/guidelines.md` trivially, commit, confirm copies refreshed in the same commit; revert the trial edit

## 3. Format-prose drift test (D4)

- [x] 3.1 Add L0 pytest under `tests/unit/` with key-count discovery (≥2 of the five canonical keys → must name all five, blank-line rule, trailing position); document threshold rationale in the test
- [x] 3.2 Confirm discovery finds exactly write, import, ideate today and passes; verify it fails when a canonical key is removed from one SKILL.md (temporary mutation, then restore)

## 4. Eval harness stages the sibling (D5)

- [x] 4.1 `harness/claude_runner.py`: add optional `siblings` list to scenarios; `stage()` copies each sibling into `ws/.claude/skills/`; declare `proposal-lit-search` for ideate scenarios (mechanism added; no ideate scenario exists in claude_runner today, so no declaration site yet)
- [x] 4.2 `harness/skill_evals.py`: stage lit-search scripts for ideate tasks via `extra_skill_files` under `proposal-lit-search/scripts/…` (staging statically verified: 9 sibling scripts at the sibling path, ideate `skill/` references-only)
- [ ] 4.3 Smoke-run one ideate eval scenario on the cheap dev loop to confirm grounding uses the staged sibling scripts (blocked: OPENROUTER_API_KEY not set in this session)

## 5. Drop ideate's redundant structure.json copy (follow-up fold-in)

- [x] 5.1 Remove `skills/proposal-ideate/references` from the structure.json destinations in SYNC_MAP; delete `skills/proposal-ideate/references/structure.json`
- [x] 5.2 Trim the guidance-awareness sentence in `skills/proposal-ideate/SKILL.md` to reference guidelines.md only
- [x] 5.3 Re-run L0 + sync check; commit as follow-up

## 6. Wrap-up

- [x] 6.1 Full L0 + lint pass (`pytest tests/unit`, `ruff check`, `sync_shared.py --check`) — 66 passed, ruff clean, copies in sync
- [x] 6.2 `openspec validate reduce-skill-duplication --strict`; commit the change
