# Tasks

## 1. Routing cases and staging

- [x] 1.1 Add `("f27-citation-runs", "dependency-update-breakage.md")` to `WORKSPACE_FIXTURES` in `harness/routing.py`; verify `test_every_case_in_the_shipped_dataset_can_be_staged` passes once 1.2 lands
- [x] 1.2 Add `write-polish-collision` (the `write_repair_citations` request verbatim, expected `proposal-write`) and `review-ready-collision` ("Is my proposal ready for my supervisor?", expected `proposal-review`) to `harness/routing_cases.toml`; verify `uv run pytest tests/unit/test_routing.py` passes
- [x] 1.3 Update the routing case count in `harness/README.md` (44 → 46); verify by grep

## 2. Before-measurement (description unchanged)

- [x] 2.1 Confirm no `ANTHROPIC_API_KEY`, `ANTHROPIC_AUTH_TOKEN` or `CLAUDE_CODE_USE_*` is exported in the launching shell (AGENTS.md, Metered model calls); verify with `env`
- [x] 2.2 Routing rig, haiku, the ten write and review cases, 3 epochs, `--no-report`; record per-case results in `measurement.md`

## 3. Description edit and after-measurement

- [x] 3.1 Extend `proposal-write`'s description as in proposal.md, and add "polishing pass" → `proposal-write` to `tests/unit/data/trigger_terms.json`; verify `uv run pytest tests/unit/test_skill_frontmatter.py` passes
- [x] 3.2 Routing rig, haiku, the same ten cases, 3 epochs, `--no-report`; record per-case results
- [x] 3.3 Routing rig, sonnet, the full set, 1 epoch, `--conditions-changed`; keep the regenerated `docs/skill-routing.md` and record the case-by-case comparison against the 2026-08-10 report
- [x] 3.4 Dev runner, `write_repair_citations`, haiku, 3 runs (`--isolated --keep --max-budget-usd 1`); record per run whether a `Skill` call named `proposal-write` (jq over `.devrun-events.jsonl`), whether `check.py` ran, the L1 verdict, and the reported cost
- [x] 3.5 Dev runner, `write_repair_citations`, sonnet, 1 run (`--max-budget-usd 2`), as a guard; record the same fields
- [x] 3.6 Control: 3 haiku runs of the same scenario with the original description restored in place (`skills/` identical to `main`), same flags; record the same fields, then re-apply the edit and confirm the diff

## 4. Decision and record

- [x] 4.1 Apply the decision rule and write the outcome into `measurement.md`. Keep: the edit stays. Revert: restore the description and the trigger table, and add the haiku polishing note to the README model-support section. Verify the diff matches the outcome.
- [x] 4.2 Record the root cause in `measurement.md`: haiku × repair failed because the skill was never loaded, not from general non-adherence as the `scope-citation-attribution` measurement stated
- [x] 4.3 Gate: `uv run poe test` and `uv run poe specs` exit 0
