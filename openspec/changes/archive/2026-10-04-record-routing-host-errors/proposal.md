# Proposal

## Why

The routing rig treats any non-empty event stream as a measurement. When the host ends a case with an error result — `{"type": "result", "is_error": true, "result": "Failed to authenticate: OAuth session expired and could not be refreshed"}`, the shape recorded on 2026-10-03 and 2026-10-04 — `route_from_events` finds no skill call and returns None. `stream_events` sets an error only when no events arrived, so `measure` records the case as route `none`.

A sweep run while the stored login is dead therefore produces a plausible-looking result: every `negative` case passes, because "no skill selected" is what a negative case expects, and every other case is scored as "not selected". That score is then written into `docs/skill-routing.md` as a finding about the descriptions. The dev runner already names this failure (`host_failure`, archived change `2026-10-04-keep-isolated-login`); the rig never looks at the result event at all.

Fixing only the per-case record would open a second hole. Errors are kept out of the matrix totals, so a sweep in which every case errored totals 0/0, and `main` returns success when `passed == total`. The report would also be overwritten with zero measurements, and the next run's "supersedes" line would compare against 0/0 instead of the last real score.

## What Changes

- **An error result is an error, not a route.** When a case's stream carries an error result event and no `proposal-*` invocation, the case is recorded as an error carrying the host's reason: the subtype, the host's errors or its result text, and the cost and turns so far. It is counted neither as unrouted nor as a route, so a negative case cannot pass on it.
- **A dead login names its remedy.** When that reason is an authentication failure, the error also tells the operator to run `claude` and enter `/login` — the same instruction the dev runner gives, composed by the same code.
- **Errors fail the run.** A routing run in which any measurement ended in an error exits non-zero.
- **Nothing measured, nothing reported.** A run in which no measurement completed leaves the tracked report unchanged. The raw per-case results are still written to `logs/routing/`.
- **One composition, two callers.** The error-result reason and the login-failure recognition move out of `harness/claude_runner.py` to places both the runner and the rig import, so the two cannot drift.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`:
  - *Route determined by the first skill invocation* gains the rule that a host error result with no route is an error rather than an unrouted case.
  - *Isolated measurement environment* gains a scenario: an authentication failure during a run names the re-login remedy and yields no verdict for that case.
  - *Routing reported as a confusion matrix* gains the run-level consequences: errors fail the run, and a run with no completed measurement leaves the report unchanged.

## Impact

- `harness/routing.py`: new `result_event` and `error_result_reason` beside `tool_calls`; a pure `case_result` that `measure` delegates to; `main` exits non-zero on errors and skips the report when nothing completed.
- `harness/host_login.py`: `LOGIN_FAILURE` and `login_remedy`, beside `RELOGIN`.
- `harness/claude_runner.py`: imports the shared pieces; behaviour unchanged.
- `tests/unit/test_routing.py`: L0 tests over a synthetic error-result stream, the exit status and the report guard. `tests/unit/data/routing_streams/`: the synthetic stream and its README row.
- `harness/README.md`: the routing section says what an errored case means.
- No user-side skill files, no new dependencies. No metered run: the behaviour is decided by pure functions over recorded events.
