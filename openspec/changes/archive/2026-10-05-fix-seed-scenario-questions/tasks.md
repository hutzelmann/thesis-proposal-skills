# Tasks

## 1. Guard

- [x] 1.1 Add `test_every_draft_scenario_says_nobody_will_answer` to `tests/unit/test_dev_runner_probe.py`: every scenario in `DRAFT_SCENARIOS` carries "I cannot answer any questions — decide and tell me what you did." in its request; verify it fails on the current `write_from_seed` request.
  Evidence: with the old request the test fails with `AssertionError: write_from_seed`.

## 2. Fix the scenario

- [x] 2.1 Append the sentence, copied verbatim from `write_rich_seed` / `write_repair_citations`, to `SCENARIOS["write_from_seed"]["request"]` in `harness/claude_runner.py`; verify the guard passes and `uv run pytest tests/unit/test_dev_runner_probe.py` stays green (86 passed).
- [x] 2.2 Confirm nothing else pins the old dev-runner request: `grep -rF 'mark anything missing as TODO'` finds only the Inspect tasks in `harness/skill_evals.py`, their `evals.json` projection, and the synthetic `tests/unit/data/l2_prompts/` pins (own task text); `test_judged_run_reports_l2_beside_l1` reads the request from the table. Leave `harness/skill_evals.py` untouched and verify `uv run python harness/eval_export.py --check` exits 0.

## 3. Verify

- [x] 3.1 `uv run poe test` and `uv run poe specs` green; no model-calling run.
