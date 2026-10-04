# Design

## Context

`harness/routing.py::measure` stages a workspace, calls `stream_events` (a subprocess reading `claude -p --output-format stream-json` until a route is decided), then derives the `Result` inline. Only `route_from_events` is a pure function today; the rule "no events means an error" sits in `stream_events`, and the rule "a route wins over a stream error" sits in `measure`. Neither can be reached by an L0 test without spawning the host.

`harness/claude_runner.py` already reads the result event. `host_failure_reason` composes the error-result message (subtype, errors or `terminal_reason` plus `result` text, cost, turns), and `host_failure` appends the re-login instruction when `LOGIN_FAILURE` matches. `claude_runner.py` is omitted from coverage, because it only executes under a live model run, and it imports `routing` (`OUTWARD_TOOLS`, `isolated_config`, `tool_calls`). Because of that import, `routing` cannot import from the runner.

## Goals / Non-Goals

**Goals:**
- One composition of the error-result reason and the login remedy, used by both the runner and the rig.
- The case-level decision becomes a pure function the L0 suite can call with a synthetic stream.

**Non-Goals:**
- Aborting a sweep early when the first case reports a dead login. Each case fails at 0 USD within seconds, the claim logic in `host_login` already refuses runs whose refresh never arrives, and an early abort would need cross-thread cancellation for little gain.
- Changing the runner's messages. Its wording and the order of its checks stay as they are; only where the code lives changes.
- Re-rendering a saved run log (`--render`). It renders whatever the log holds, and a log written after this change already carries the errors.

## Decisions

**The error-result reason lives in `routing.py`, beside `tool_calls`.** `routing.py` already provides the runner's stream reader (`tool_calls`) and its isolation (`isolated_config`), so the dependency direction exists and stays one-way. `result_event` moves with the reason, and `claude_runner` re-imports it under the same name, so its callers and tests are untouched. *Alternative:* a new `harness/host_stream.py` module. It is cleaner in name, but it adds a module for two functions, and it would leave `tool_calls`, the other stream reader, in `routing.py`.

**Login-failure recognition lives in `host_login.py`, beside `RELOGIN`.** The pattern (`LOGIN_FAILURE`) and the sentence that appends the remedy (`login_remedy`) are about the stored login, and `host_login` already owns the remedy's wording. The runner keeps applying the remedy to its whole message, including the stderr path, as before. *Alternative:* fold the remedy into `error_result_reason`. Rejected: the runner also needs the remedy for a stderr-only failure ("Not logged in"), so the remedy has to stand alone.

**`case_result(case, events, stream_error)` is the pure decision; `measure` only stages and streams.** The order is the spec's:
1. A malformed `Skill` call raises → error.
2. A route → route. A route beats every error, so a host that fails after the selection does not erase it.
3. An error result → error, with the remedy appended for a login failure.
4. A stream error (timeout, no events) → error.
5. Otherwise → unrouted.

Putting the error result before the stream error means a host that printed its reason and exited is reported in its own words, not as "no events".

**Run-level outcome in `main`.** The exit status becomes `0` only when there are no errors and `passed == total`. The report is written only when the matrix holds at least one completed measurement (`total > 0`). The raw log in `logs/routing/` is always written, because it is the diagnosis. When the report is skipped, the run prints that it left the report unchanged, so an operator who expected a new report knows why the file did not change. The decision is a pure predicate (`report_due(matrix)`) so the guard has an L0 test of its own.

## Risks / Trade-offs

- [The host changes its error-result shape — for example, a login failure reported as `is_error: false`] → the case would again read as unrouted. The synthetic stream follows the shape recorded on 2026-10-03 and 2026-10-04, which `tests/unit/test_dev_runner_probe.py` already pins for the runner. A shape change therefore surfaces in the runner first, and the dev runner is run far more often than the rig.
- [A partially errored sweep still overwrites the report] → intended. The report lists the errors in its own section and counts only completed measurements. Keeping the old report would hide the real measurements that did complete.
- [Moving `result_event` breaks an importer] → `claude_runner` re-imports it under the same name. `uv run poe test` covers every importer.
