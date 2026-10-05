# Tasks

## 1. Verify the code

- [x] 1.1 Trace the timeout path in `harness/routing.py` (`stream_events` → `case_result` → `classify` → `main`'s exit status) and record it in design.md Context; verify against `tests/unit/test_routing.py` which parts are already pinned.
  Evidence: a passed deadline yields the stream error "timed out after <N>s" (since `8341f33`); `case_result` keeps it when there is no route and no host error result; `classify` files it under errors and no kind total; `main` exits 1. Pinned before this change: the consumer side only (`test_a_stream_error_stands_when_the_host_gave_no_reason`, `test_errors_are_a_category_of_their_own_not_a_route`, `test_an_errored_measurement_fails_the_run`).

## 2. Spec delta

- [x] 2.1 Write the MODIFIED "Route determined by the first skill invocation" block in `specs/testing-harness/spec.md`, copied whole from the main spec: bound → unrouted, time limit → error naming the limit (whether or not past the bound), "No skill chosen" without the time limit, new scenario "Case reaches its time limit"; verify with `openspec validate align-routing-timeout-spec --strict`.

## 3. Pin the producer side

- [x] 3.1 Add `test_a_case_that_reaches_its_time_limit_is_an_error_not_unrouted` to `tests/unit/test_routing.py`, parametrized within and past the preparatory bound, driving `stream_events` with a stand-in host and a stepped clock; verify it passes.
- [x] 3.2 Mutation check: set the timeout branch in `stream_events` to leave the error empty and confirm both parametrizations fail; restore and confirm `git diff harness/routing.py` is empty.
  Evidence: mutated → 53 passed, 2 failed (`assert None == 'timed out after 90s'`); restored → 55 passed, `harness/routing.py` unchanged.

## 4. Document

- [x] 4.1 `harness/README.md` routing section: one sentence beside the host-error paragraph saying a case still running at its time limit is an error, even past the preparatory bound; verify by reading the paragraph.

## 5. Verify and archive

- [x] 5.1 `uv run poe test` and `uv run poe specs` green.
- [x] 5.2 Archive with spec sync and confirm the main spec's requirement carries the new sentence and the "Case reaches its time limit" scenario, and no longer says the time limit yields unrouted.
