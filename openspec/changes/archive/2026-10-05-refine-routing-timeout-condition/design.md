# Design

## Context

The trace in `2026-10-05-align-routing-timeout-spec/design.md` still holds: `stream_events` stops on a route; otherwise, once the deadline has passed, it sets "timed out after <N>s" and stops. Exceeding the preparatory bound makes `route_from_events` return no route for the rest of the stream — a later skill call is not a route — without stopping the reader. So the reader's stop conditions are "route recorded" and "deadline passed", and nothing in between looks at whether a `proposal-*` skill appeared after the bound. `case_result` then keeps the stream error because there is no route and no host error result.

The existing test `test_a_case_that_reaches_its_time_limit_is_an_error_not_unrouted` drives the reader over `unrouted-explore.jsonl`, which contains no `Skill` call at all, so it pins the time limit within and past the bound but not the late-skill path this change names.

## Goals / Non-Goals

**Goals:** the time-limit sentence and its scenario name the condition the rig actually uses, and an L0 test pins the path that distinguishes the old wording from the new one.

**Non-Goals:**

- Changing the rig. Stopping the reader at the bound, or treating a late skill call as a route, would each be a visible spec change of their own.
- The host-error paragraph and the other scenarios. The paragraph conditions the host error on "before any `proposal-*` invocation", while `case_result` records a host error result as an error whenever no route was recorded, so a late skill call followed by an error result is an error in the rig and unrouted by the bound sentence. The scenarios "No skill chosen", "Host ends the case with an error" and "Unrouted answer is not an error" say "no `proposal-*` skill invoked" where the rig means "no route recorded"; for unrouted outcomes the bound sentence already covers the late call, so those are incomplete rather than wrong. Left for a separate decision; this change is scoped to the time-limit wording.

## Decisions

**"No route recorded", nothing more.** The requirement already defines what a route is and says a case past the bound is unrouted, so "no route recorded" carries the late-skill case without an extra clause, and "whether or not it had exceeded the bound" stays as it is. An explicit clause ("even when a `proposal-*` skill was invoked after the bound") was considered and dropped: it restates the bound sentence and would be one more sentence to keep in step with it. The delta is the whole requirement block copied from the main spec with exactly the two phrases replaced.

**A separate test, not a third parametrization.** The existing test's docstring and stand-in describe a host that never picks a skill; the late pick is a different claim — the skill call is present and still does not save the case — and asserts that the call is in the stream the reader saw. The clock-and-host setup the two tests share moves into a helper beside them. The stream is composed from tracked fixtures (four `Glob` peeks, then `routed-check.jsonl`: `proposal-check` fifth, then a `Bash` line), the same composition `test_wandering_past_the_bound_is_unrouted` uses, so no new fixture file is needed. The deadline passes on the `Bash` line, after the skill call was read in time.

## Risks / Trade-offs

- [The new test passes against a reader that would have timed out anyway] → it asserts the skill call is among the events the reader consumed before the deadline, and mutation-checks: with `route_from_events` given a bound high enough to accept the late call, the reader stops on the route and the test fails on the error string.
