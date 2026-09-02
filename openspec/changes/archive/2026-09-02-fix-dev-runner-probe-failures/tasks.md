## 1. Runner

- [x] 1.1 `harness/claude_runner.py`: add `host_command(request, model, budget)` and `host_failure(events, returncode, stderr)`; `run_claude` parses stdout first and exits with the failure message when one applies.
- [x] 1.2 `final_text` returns the result event's `result` (or empty); drop the assistant-text fallback.
- [x] 1.3 Move isolated-config setup inside `try`; add `config_dir` to the summary; reword the placement comment.

## 2. Fixtures and tests

- [x] 2.1 `tests/unit/data/routing_streams/recorded-result.jsonl` (reduced recorded result event) plus README row; reword the README opening to cover the result event.
- [x] 2.2 `tests/unit/test_dev_runner_probe.py`: `host_failure` for error result (message carries subtype, errors, cost, turns), non-zero exit without result (stderr tail), missing result (named), success (None); `host_command` pins the stream flags and the budget pass-through; `summary()` with `config=None` and with a path; `telemetry`/`final_text` pinned against `recorded-result.jsonl`; drop the assistant-fallback test; docstring reworded.

## 3. Docs and verify

- [x] 3.1 `harness/README.md`: one sentence on failure reporting and `config_dir`.
- [x] 3.2 `uv run poe test` green; `openspec validate --all --strict` passes.
- [x] 3.3 One live run (`uv run poe dev check_report --model haiku --max-budget-usd 0.001`) shows the budget-overrun failure message with subtype and cost, then a normal run still passes.
