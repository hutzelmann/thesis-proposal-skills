## 1. Verdict

- [x] 1.1 `harness/l1_checks.py`: add `HELPER_TOOLS = ("Agent", "Task", "Workflow")` and `verdict_single_context(tool_names: list[str]) -> tuple[bool, str]` (passes with "no helper agents spawned", fails naming the distinct spawning calls and their count).

## 2. Runner

- [x] 2.1 `harness/claude_runner.py`: run the child with `--output-format stream-json --verbose`; add `parse_events(stdout)`, `final_text(events)` (result event's `result`, falling back to concatenated assistant text), `telemetry(events)` (cost, turns, duration, tokens from the result event's `usage`).
- [x] 2.2 Add `--max-budget-usd` (passed through when given) and `--isolated` (reuse `routing.prepare_config` under the temp workspace, set `CLAUDE_CONFIG_DIR` for the child); summary gains `config: ambient|isolated`.
- [x] 2.3 Summary JSON carries `cost_usd`, `num_turns`, `duration_ms`, `tokens_in`, `tokens_out`, `helper_calls`, `single_context` (PASS/FAIL plus why); exit code unchanged (scenario L1 only).

## 3. Fixtures and tests

- [x] 3.1 Add `tests/unit/data/routing_streams/helper-fanout.jsonl` (synthetic: one assistant event with a `Task` tool_use, one with `Read`, one result event with `result`, `total_cost_usd`, `num_turns`, `duration_ms`, `usage`) and a row in that directory's README.
- [x] 3.2 Add `tests/unit/test_dev_runner_probe.py`: `verdict_single_context` pass/fail; `parse_events` skips malformed lines; `final_text` from result event and from assistant fallback; `telemetry` on `helper-fanout.jsonl` and on a stream without a result event (fields `None`); helper names from `unrouted-explore.jsonl` are empty and from `helper-fanout.jsonl` are `["Task"]`.

## 4. Docs

- [x] 4.1 `harness/README.md` dev-runs section: telemetry line, `--max-budget-usd`, `--isolated`, and what ambient vs isolated means; Known limitations fan-out bullet updated (probe exists; cannot switch on a workflow-by-default mode).

## 5. Verify

- [x] 5.1 `uv run poe test` green (conventions: `main(argv)`, verdict has an L0 test, complexity cap).
- [x] 5.2 `openspec validate --all --strict` passes.
- [x] 5.3 One live dev run (`uv run poe dev check_report --model haiku`) prints the telemetry line with a real cost and `single_context: PASS`.
