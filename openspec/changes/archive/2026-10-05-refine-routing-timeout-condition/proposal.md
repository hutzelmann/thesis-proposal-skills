# Condition the routing time-limit error on the route, not on a skill call

## Why

`2026-10-05-align-routing-timeout-spec` made a case that reaches its time limit an error rather than unrouted, but conditioned that on "no `proposal-*` skill invoked". The rig conditions it on something else: once the preparatory-call bound is exceeded, `route_from_events` (`harness/routing.py`) returns no route for the rest of the stream, so a `proposal-*` call arriving after the bound is not a route, the reader keeps going, and a case still running at its limit is recorded as "timed out after <N>s" whenever no route was recorded — including when a skill was invoked late. Under the current wording that case falls under neither the time-limit sentence (a skill *was* invoked) nor anything else, so the spec says nothing about a path the rig takes. The code is right — its own design.md describes the bound as making "a later skill call … not a route" — and the wording is imprecise.

## What Changes

- MODIFIED requirement "Route determined by the first skill invocation" (testing-harness): in the time-limit sentence, "with no `proposal-*` skill invoked" becomes "with no route recorded"; in the scenario "Case reaches its time limit", "no `proposal-*` skill was invoked" becomes "no route was recorded". Every other sentence and scenario is unchanged.
- `tests/unit/test_routing.py`: one L0 test drives the real stream reader over a stream in which `proposal-check` is invoked fifth, past the bound of three, and the deadline passes on the next line, and asserts the case is a "timed out after 90s" error, not routed and not unrouted. The existing time-limit test covers only streams without any skill call.
- `harness/README.md` (routing section): the time-limit sentence says "no route recorded" instead of "no skill selected".
- No change to `harness/routing.py`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `testing-harness`: "Route determined by the first skill invocation" — the time-limit error applies whenever no route was recorded, including a skill invoked past the preparatory bound.

## Impact

- `openspec/specs/testing-harness/spec.md` (via archive), `tests/unit/test_routing.py` (one test), `harness/README.md` (one sentence).
- No runtime behaviour changes.
