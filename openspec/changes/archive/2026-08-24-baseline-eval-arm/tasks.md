# Tasks — baseline-eval-arm

## 1. Baseline arm in the harness

- [x] 1.1 `harness/skill_evals.py`: `baseline: bool = False` parameter on every single-turn task builder, threaded through `proposal_task` — plain prompt with the same workspace framing and request; staging stays identical (the `skill/` files are scorer infrastructure — what the baseline removes is the instructions); persona-dialogue builders unchanged (no parameter = loud rejection)
- [x] 1.2 `harness/claude_runner.py`: `--no-skill` flag — same staging, skill not installed, bare request sent
- [x] 1.3 `harness/matrix.py`: `--baseline` pass-through setting the task arg on eligible tasks; estimate covers the run like any metered invocation

## 2. Delta reporting and duration

- [x] 2.1 `harness/report.py`: bucket logs by recorded `task_args.baseline`; exclude baseline logs from support classification at the single log-reading entry point
- [x] 2.2 Delta section when both arms exist per (model, task): pass-rate delta, token delta, duration delta; per-scorer dead-assertion (passes both arms) and too-hard (fails both arms) flags
- [x] 2.3 Duration read from each log's stats timestamps, shown beside tokens and cost in the existing grid

## 3. Coverage and docs

- [x] 3.1 L0 tests: baseline logs never reach support classification; delta and flag computation as pure functions over synthetic log summaries; wiring test asserts persona builders reject `baseline`
- [x] 3.2 `harness/README.md`: how to run a baseline sweep (`-T baseline=true` / `poe matrix --baseline`, dev `--no-skill`) and how to read the delta section

## 4. Verify

- [x] 4.1 `uv run poe test` green
- [x] 4.2 `openspec validate --all --strict` green
