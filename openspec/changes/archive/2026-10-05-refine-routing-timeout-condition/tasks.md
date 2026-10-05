# Tasks

## 1. Spec delta

- [x] 1.1 Write the MODIFIED "Route determined by the first skill invocation" block in `specs/testing-harness/spec.md`, copied whole from the main spec with only the time-limit sentence's and the "Case reaches its time limit" scenario's condition changed to "no route recorded"; verify with a diff against the main spec (exactly two lines differ) and `openspec validate refine-routing-timeout-condition --strict`.
  Evidence: the diff shows lines 2 and 31 of the block only; the change validates.

## 2. Pin the late-skill path

- [x] 2.1 Move the stand-in host and stepped clock of `test_a_case_that_reaches_its_time_limit_is_an_error_not_unrouted` into a helper beside it; verify both parametrizations still pass.
  Evidence: `read_until_the_limit` in `tests/unit/test_routing.py`; both parametrizations pass.
- [x] 2.2 Add a test in `tests/unit/test_routing.py` that drives `stream_events` over four peeks, then `proposal-check`, then one more line, with the deadline passing on that last line, and asserts the skill call was read, the error is "timed out after 90s", the case has no route, a negative case does not pass, and no kind total counts it; verify it passes.
  Evidence: `test_a_skill_invoked_past_the_bound_does_not_save_a_case_from_its_time_limit`, asserted for both the `proposal-check` case and the negative case; passes.
- [x] 2.3 Mutation check: raise the bound `stream_events` hands `route_from_events` so the late call becomes a route, confirm the new test fails, restore and confirm `harness/routing.py` is unchanged.
  Evidence: with `bound=10` → 2 passed, 1 failed (`assert None == 'timed out after 90s'`, the new test only); restored → 56 passed, `git diff harness/routing.py` empty.

## 3. Document

- [x] 3.1 `harness/README.md` routing section: the time-limit sentence says "no route recorded" instead of "no skill selected"; verify by reading the paragraph.

## 4. Verify and archive

- [x] 4.1 `uv run poe test` and `uv run poe specs` green.
- [x] 4.2 Archive with spec sync and confirm the main spec's time-limit sentence and scenario say "no route recorded" and no longer "no `proposal-*` skill invoked".
