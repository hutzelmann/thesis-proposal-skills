# Make the dev-runner probe fail loudly and pin it against a recorded stream

## Why

Review of `2026-09-02-add-dev-runner-cost-probe` against the host bundle found three silent paths. A host error result — a `--max-budget-usd` overrun produces one, with `subtype`, `errors`, `total_cost_usd` and `num_turns` — exits non-zero with nothing on stderr in stream-json mode, so the runner printed `claude failed:` with an empty message and threw away exactly the telemetry the probe exists to surface. A stream with no result event exits zero, so the runner printed all-`None` telemetry and ran the L1 verdict over the joined mid-run narration (a fallback the plain mode never had). And the only result event under test was the synthetic one, so a host field rename would blank the telemetry line with every test green — the opposite of the test file's docstring. The summary and the command the runner builds had no test at all, although the spec promises L0 coverage of the whole probe.

## What Changes

- `run_claude` parses stdout before judging the exit: a result event marked `is_error` ends the run as a runner failure whose message carries the host's subtype, errors, and cost and turns so far; a non-zero exit without one reports the stderr tail; a zero exit with no result event is a runner failure too. `final_text` returns the result event's text and nothing else, matching the old plain mode.
- The isolated-config setup moves inside the `try` so a refused run leaks nothing; the summary reports the resolved config directory; the comment about credential exposure says what sibling placement achieves (keeps the config out of the workspace and the verdicts' glob) and no more.
- A recorded result event, reduced to the fields the probe reads (2.1.207 routing run, session and model fields scrubbed, text truncated), joins the stream fixtures; `telemetry()` and `final_text()` are pinned against it. The command list is factored into `host_command()` and pinned; `summary()` is tested with and without an isolated config. The fixtures README's framing covers the result event.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `testing-harness`: "Dev-runner cost and helper-agent telemetry" — error results and missing result events are runner failures carrying the host's detail; telemetry pinned against a recorded result event; command and summary under L0 coverage.

## Impact

- `harness/claude_runner.py`, `tests/unit/test_dev_runner_probe.py`, `tests/unit/data/routing_streams/recorded-result.jsonl` (new) and that README, `harness/README.md` one sentence. Spec delta for `testing-harness`.
