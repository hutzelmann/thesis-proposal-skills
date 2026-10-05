# Tell the dev runner's seed scenario that nobody answers questions

## Why

A dev run is one headless turn: nobody is there to answer a question, so a run that stops to ask one ends without a draft and is graded on nothing. The dev runner's other write scenarios (`write_rich_seed`, `write_repair_citations`, `write_offtopic_reference`) close their request with "I cannot answer any questions — decide and tell me what you did." `write_from_seed` does not, and on 2026-10-04 a haiku run of it stopped to ask for the degree level instead of drafting. `write_from_seed` is one of the three core scenarios `poe smoke` runs and the one it judges, so a stall there costs the smoke's only graded result.

## What Changes

- `harness/claude_runner.py`: the `write_from_seed` scenario's request gains the sentence its sibling write scenarios carry, verbatim: "I cannot answer any questions — decide and tell me what you did."
- `tests/unit/test_dev_runner_probe.py`: one L0 test asserts that every dev-runner draft scenario (`DRAFT_SCENARIOS`) carries that sentence, so the next draft scenario cannot be added without it.
- The Inspect task `write_from_seed` in `harness/skill_evals.py` is deliberately left unchanged, and with it the generated `skills/proposal-write/evals/evals.json` projection. That task feeds the model-support matrix, whose shipped verdicts compare runs across time; changing its prompt would make every earlier `write_from_seed` cell incomparable with the next one. The matrix is metered, multi-epoch and scored by its own scorers, so a single model's clarifying question there is a measured outcome, not a broken dev loop.

## Capabilities

### New Capabilities

(none — tooling, `skip_specs: true`)

### Modified Capabilities

(none — no requirement fixes the wording of a dev-runner scenario request)

## Impact

- `harness/claude_runner.py` (one scenario's request string), `tests/unit/test_dev_runner_probe.py` (one test).
- The dev-runner judge receives the request as the task statement, so its prompt for `write_from_seed` now carries the sentence too; `test_judged_run_reports_l2_beside_l1` reads the request from the scenario table rather than pinning it.
- Not touched: `harness/skill_evals.py`, `skills/proposal-write/evals/evals.json`, `tests/unit/data/l2_prompts/` (synthetic judge-prompt pins with their own task text), `docs/model-support.md`.
