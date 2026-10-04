# Tasks

## 1. Failing tests first

- [x] 1.1 Add `tests/unit/data/routing_streams/expired-login.jsonl`: a synthetic stream holding a `system` init event and the error result recorded on 2026-10-03 and 2026-10-04 (`subtype` "success", `is_error` true, `errors` null, the reason in `result`, `terminal_reason` "api_error", 0 USD, 1 turn). Add its row to the fixture README. Verify: the README table names the file and what it pins.
- [x] 1.2 Add tests to `tests/unit/test_routing.py`:
  - the expired-login stream yields an error that carries the host's reason and names `claude` and `/login`, with no route;
  - a negative case does not pass on that stream;
  - a non-auth error result (a budget overrun) yields an error without the login remedy;
  - a non-error result with no skill call stays unrouted;
  - a route beats both an error result and a stream error;
  - a stream error with no result event is kept;
  - `report_due` is false for an all-error matrix and true once one measurement completed;
  - `main` exits non-zero on an errored measurement and leaves the report untouched when nothing completed. Do this through a monkeypatched `measure`, `isolated_config` and `REPORT_FILE`, with no host call.

  Verify: the new tests fail against the current code. (Recorded: collection failed with `ImportError: cannot import name 'case_result'`.)

## 2. Implementation

- [x] 2.1 In `harness/host_login.py`, add `LOGIN_FAILURE` and `login_remedy(message)` beside `RELOGIN`. Verify: the runner's login-remedy tests in `tests/unit/test_dev_runner_probe.py` pass once 2.3 is done.
- [x] 2.2 In `harness/routing.py`:
  - add `result_event` and `error_result_reason` beside `tool_calls`;
  - add the pure `case_result(case, events, stream_error)` and make `measure` delegate to it;
  - add `report_due(matrix)`;
  - in `main`, exit non-zero on any error and write the report only when `report_due` (the write moved into `write_report`).

  Verify: the tests from 1.2 pass.
- [x] 2.3 In `harness/claude_runner.py`, import `result_event` and `error_result_reason` from `routing`, and `login_remedy` from `host_login`. Drop the local copies and the now-unused `re` import. `host_failure_reason` delegates its error-result branch. Verify: `tests/unit/test_dev_runner_probe.py` passes unchanged.

## 3. Documentation and gate

- [x] 3.1 In `harness/README.md`'s routing section, say that a case the host ends with an error is recorded as an error with the host's reason, never as unrouted, and that a run with errors exits non-zero and leaves the report alone when nothing completed. Verify: the paragraph is present.
- [x] 3.2 Run `uv run poe test`, `uv run poe cov` and `uv run poe specs`. Verify: all three are green; no metered run is issued. (Recorded: 1992 passed, 1 skipped, ruff clean, copies in sync, 11 skills conform; coverage 84.65% against the 78% floor; specs 18/18 valid. No host or model call.)
