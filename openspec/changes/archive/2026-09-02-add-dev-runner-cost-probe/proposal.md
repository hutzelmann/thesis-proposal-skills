# Add a cost and helper-agent probe to the dev runner

## Why

The dev runner (`harness/claude_runner.py`) runs the real host binary and then discards everything the host reports except the chat text: the stream-json result event already carries `total_cost_usd`, `num_turns`, `duration_ms` and token usage, and the assistant events carry every `tool_use`, including helper-agent spawns. After the 2026-09-02 fan-out incident (27 agents, ~8.3M tokens) the repository has execution-shape sections guarded by wording pins and no measurement at all: nothing in the dev loop would show a fifteen-fold cost or a single helper spawn. The routing rig already parses the same event stream (`harness/routing.py`: `tool_calls`), so the probe is a reuse, not a new parser.

## What Changes

- The dev runner runs the child with `--output-format stream-json --verbose`, reassembles the chat from the result event, and prints beside the L1 verdict: `cost_usd`, `num_turns`, `duration_ms`, input and output tokens, the list of helper-agent tool calls, and a `single_context` verdict.
- A new verdict function `verdict_single_context(tool_names)` in `harness/l1_checks.py` passes when no helper-spawning tool (`Agent`, `Task`, `Workflow`) was called and names them when one was. It is advisory in the dev runner: the scenario's own L1 still decides the exit code, and the probe line is a second, separately labelled verdict.
- `--max-budget-usd <n>` passes through to the host as a hard cap for probes, and `--isolated` runs against a fresh host configuration prepared the way the routing rig does it (settings emptied, credentials linked), so a probe can be labelled as measuring the default host rather than the operator's session. The summary carries `config: ambient|isolated`.
- L0 coverage: the verdict, the event parsing and the telemetry extraction are tested against recorded streams under `tests/unit/data/routing_streams/`, plus one new synthetic stream `helper-fanout.jsonl` (a `Task` spawn and a result event with cost fields), documented in that directory's README.
- `harness/README.md`: the dev-runs section documents the telemetry line and the two flags; the Known limitations fan-out bullet says what the probe can and cannot see.

Out of scope: the probe cannot reproduce a workflow-by-default host mode, which is a session opt-in; it measures whatever mode the invoking session carries (ambient) or the default host (isolated), and says which.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `testing-harness`: add a dev-runner telemetry requirement — per-run cost, turns, token usage and helper-agent invocations recorded from the host's event stream, reported beside the L1 verdict, with a dedicated verdict function under L0 coverage, a budget cap, and an ambient-versus-isolated label.

## Impact

- `harness/claude_runner.py` (stream-json capture, telemetry, two flags), `harness/l1_checks.py` (one verdict function and the helper-tool constant)
- `tests/unit/test_dev_runner_probe.py` (new), `tests/unit/data/routing_streams/helper-fanout.jsonl` (new) and that directory's README
- `harness/README.md`; spec delta for `testing-harness`. No skill files, no shared content.
