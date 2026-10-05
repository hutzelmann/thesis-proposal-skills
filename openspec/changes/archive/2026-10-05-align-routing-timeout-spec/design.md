# Design

## Context

What `harness/routing.py` does today, traced before writing the delta:

- `stream_events` reads the host's stream line by line. After each line it stops on a route (`route_from_events` returns a `proposal-*` skill). Otherwise, if the deadline (`CASE_TIMEOUT_S`, 90 s, `--timeout`) has passed, it sets the stream error `"timed out after <N>s"` and stops. The host process is terminated either way.
- Exceeding the preparatory bound (`MAX_PREPARATORY_CALLS`, 3) makes `route_from_events` return `None` for the rest of the stream — a later skill call is not a route — but does not stop the reader. The case then ends one of three ways: the host closes the stream with a non-error result (unrouted), with an error result (host error), or the deadline passes first (timeout error).
- `case_result`: a route outranks every error; without one, the host's error result outranks the stream error; with neither, the stream error stands. A timed-out case therefore carries `"timed out after <N>s"` as `Result.error`.
- `classify` puts every errored result in `Matrix.errors` and in no kind's total, `Result.passed` is false for any error, and `main` exits 1 when any measurement errored (requirement "Routing reported as a confusion matrix", scenario "Errored measurement fails the run").

`tests/unit/test_routing.py` already pins the consumer side (`case_result` with a hand-written `"timed out after 90s"`, `classify` keeping it out of the totals). Nothing pins the producer: that the reader itself turns a passed deadline into that error.

## Goals / Non-Goals

**Goals:** the requirement states what the rig records at the time limit, and an offline test pins it end to end from the reader to the classification.

**Non-Goals:** changing the rig. Two behaviours surfaced by the trace are left as they are and reported for a separate decision:

- The deadline is only checked when a line arrives. A host that stalls without writing anything blocks the reader until the process exits; the 90 s limit does not bound that case.
- A case that exceeds the preparatory bound keeps running until the host ends it or the limit passes. Stopping it at the bound would save the rest of the run and turn the "exceeded the bound, then reached the limit" path into unrouted. The delta describes today's behaviour — the limit wins — explicitly, so either fix is a visible spec change.

## Decisions

**The spec follows the code** (maintainer decision, 2026-10-05). Recording a timeout as unrouted would score a stalled host as a correct negative case, which is exactly why the host-error paragraph exists; the timeout sentence now carries the same reason.

**The delta is the whole requirement block copied from the main spec.** Changed: the bound/limit sentence is split into an unrouted sentence for the bound and an error sentence for the limit; the "No skill chosen" scenario drops the time limit from its condition and states the path that actually yields unrouted; one scenario "Case reaches its time limit" is added. The host-error paragraph and the other five scenarios are unchanged.

**The test drives the real reader with a stand-in process**, not `case_result` alone: `subprocess.Popen` is replaced by an object whose stdout yields recorded non-skill events (`tests/unit/data/routing_streams/unrouted-explore.jsonl`), and the rig's clock jumps past the deadline after a set number of reads — after the first (within the bound) and after the sixth (past it). Asserting on the reader's own error string is what makes the test fail if someone changes the timeout path to return `None` (unrouted) — the consumer-side tests would stay green in that case.

## Risks / Trade-offs

- [Patching the clock affects anything else that reads it during the test] → only the routing module's `time` name is replaced, by `monkeypatch`, for one test; the global `time` module is untouched, and the stand-in process means no subprocess or thread runs inside it.
- [The test passes against a reader that never reports the limit] → checked by mutation: with the timeout branch set to leave the error empty, both parametrizations fail on `error == "timed out after 90s"`.
