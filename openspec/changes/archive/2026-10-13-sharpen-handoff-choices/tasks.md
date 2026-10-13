## 1. Anchored choice

- [x] 1.1 Rewrite the anchored-choice sentence in `shared/blocks/handoff.md` as an operational shape (quote the passage, say what the choice changes, at most three options from the student's material, end with "or something else") with the agreed RQ2 example, keeping three paragraphs; run `python3 scripts/sync_shared.py` and verify `--check`, the handoff-block tests and the body-size tests pass

## 2. Direct-request scenario

- [x] 2.1 Keep `handoff_direct_revision` (w11, single cold request) with the after-revision verdict minus the status turn and its rubric twin; add an L0 test that the scenario installs the full set and that a bare edit fails it; document it in `harness/README.md`; verify `uv run pytest tests/unit -k handoff`

## 3. Verification

- [x] 3.1 `uv run poe test` and `uv run poe specs` green — 3317 passed, 19 specs valid
- [x] 3.2 Sonnet dev runs, `--isolated --judge`: `handoff_review_feedback` twice, `handoff_todos` once (regression guard for the check's anchored choice); `handoff_direct_revision` measured twice before the block change (record here); record outcomes
  - `handoff_direct_revision` (2026-10-13, before the block change, with the write description from `add-stage-handoffs`): 2/2 PASS on L1 and L2 — the writing skill loaded on the cold request, the blocker passage was rewritten, the review left alone, a fresh review recommended. The bare edit of rounds 1 and 2 came before that description named "apply review findings or blockers".
  - After the block change: `handoff_review_feedback` 2/2 PASS on L1 and L2, where every earlier round failed L2. Both replies now quote the proposal's own passage ("an explicit assessment of study quality and industrial relevance"; "Secondary studies to date either survey technical debt …"), say what the choice changes, offer options from the student's material and end with "or something else", with the proposal untouched. `handoff_todos` PASS on L1 and L2 (165-word closing). Haiku not re-run: out of scope by the user's decision.
