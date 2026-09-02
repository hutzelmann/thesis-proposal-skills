## Context

See proposal.md — Why. `harness/claude_runner.py` runs `claude -p` with default text output and captures stdout; `harness/routing.py` runs the same binary with `--output-format stream-json --verbose`, parses one JSON object per line, extracts `tool_use` blocks (`tool_calls`), and prepares an isolated `CLAUDE_CONFIG_DIR` (`prepare_config`). The stream's final `result` event carries `result` (the final text), `total_cost_usd`, `num_turns`, `duration_ms` and `usage`. Verdict functions live in `l1_checks.py` and must have an L0 test (`test_repo_conventions.py`).

## Goals / Non-Goals

**Goals:**

- A per-run cost number and a helper-spawn tripwire in the everyday loop, reusing the routing rig's parser.
- Honest labelling of what a run measured (ambient session vs. default host).

**Non-Goals:**

- No reproduction of a workflow-by-default host mode: it is a session opt-in the runner cannot switch on.
- No matrix or Inspect changes: fan-out is impossible on that path (bash and text_editor only).
- No change to scenario verdicts or exit codes: the probe is advisory.

## Decisions

- **Stream-json for every dev run, not a separate probe mode.** One code path; the chat text the verdicts need comes from the result event's `result` field, which is the same final text the plain mode printed. Alternative: keep text mode and add `--probe` — rejected, two runners drift.
- **Verdict in `l1_checks.py`, extraction in `claude_runner.py`, parsing reused from `routing.py`.** `verdict_single_context(tool_names)` takes plain names so its L0 test needs no stream; `tool_calls(events)` from routing supplies the names; `telemetry(events)` in the runner reads the result event. This keeps logic where the conventions say it lives and gives the verdict the L0 test the conventions require.
- **Advisory, separately labelled.** A scenario's L1 stays the exit code; the probe prints `single_context: PASS|FAIL (...)`. Folding it into the L1 would make an operator's own session mode fail a skill verdict.
- **`--isolated` reuses `routing.prepare_config`.** Same semantics as the routing rig: empty settings, credentials linked, refuse to run without them. The label is derived from that choice, never from inspecting the environment: `isolated` when the flag is set, `ambient` otherwise.
- **Helper tool names as a constant `HELPER_TOOLS = ("Agent", "Task", "Workflow")`.** The routing rig denies `Task`; newer hosts name the same capability `Agent`; workflows are their own tool. A missing name would silently pass, so all three are listed and the constant is what a future host rename edits.
- **Synthetic stream fixture for the failing case.** No recorded run spawned a helper (the incident ran interactively), so `helper-fanout.jsonl` is synthetic and says so in the README table, as the other synthetic streams do.

## Risks / Trade-offs

- [Host changes the stream shape] → the routing-stream fixtures are the existing tripwire; the new fixture and tests join them.
- [`--max-budget-usd` unsupported on an older host] → the flag is only added when passed; the host's own error surfaces as the runner failure message.
- [Ambient runs measure the operator's mode] → labelled `ambient`; `--isolated` exists for the default-host question.
