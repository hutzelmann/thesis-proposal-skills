# Align the routing spec with how the rig records a timed-out case

## Why

The testing-harness requirement "Route determined by the first skill invocation" says a case that exceeds the preparatory-call bound *or its time limit* is recorded as unrouted. The rig has done something else for the time limit since it landed (`8341f33`, 2026-08-10), and the host-error change (`2026-10-04-record-routing-host-errors`) carried the old sentence forward unchanged: `stream_events` returns the stream error "timed out after <N>s", `case_result` keeps it as the case's error because no route and no host error result outrank it, `classify` counts it among the errors rather than in any kind's total, and an errored measurement makes the run exit with a failure status. The code is right and the spec is stale. A host that has not finished a case within its limit says nothing about the descriptions, and recording that as unrouted would let a negative case pass on a stalled host — the same reasoning the requirement already gives for a host error result. The decision (maintainer, 2026-10-05) is that the spec follows the code.

## What Changes

- MODIFIED requirement "Route determined by the first skill invocation" (testing-harness): exceeding the preparatory-call bound stays unrouted; a case still running at its time limit with no `proposal-*` skill invoked is recorded as an error naming the limit, not as unrouted and not retried, whether or not it had exceeded the bound. The "No skill chosen" scenario drops the time limit from its condition; a new scenario "Case reaches its time limit" states the error outcome. All other text and scenarios are unchanged.
- `tests/unit/test_routing.py`: one L0 test drives the rig's stream reader with a stand-in host that keeps talking without choosing, past a faked deadline, and asserts the "timed out after <N>s" error, that the case is not unrouted, that a negative case does not pass on it, and that it counts toward no kind's total. Until now only `case_result` was tested with a hand-written error string; nothing pinned that the reader produces that error at the limit.
- `harness/README.md` (routing section): one sentence saying a case still running at its time limit is an error too, beside the existing host-error paragraph.
- No change to `harness/routing.py`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `testing-harness`: "Route determined by the first skill invocation" — a case that reaches its time limit is an error, not unrouted.

## Impact

- `openspec/specs/testing-harness/spec.md` (via archive), `tests/unit/test_routing.py` (one test plus a small stand-in for the host process), `harness/README.md` (one sentence).
- No runtime behaviour changes; routing reports already record timeouts under Errors.
