## Context

See proposal.md — Why. Verified against the 2.1.258 bundle by the review: print-mode teardown exits non-zero on an error result; in stream-json mode the error result is the only output for a budget overrun (the `Error: Exceeded USD budget` line belongs to the text branch); a stream with no result event exits zero.

## Goals / Non-Goals

**Goals:** no silent path — every host failure mode reaches the operator with the host's own detail; the probe's readers are pinned against a real result event.

**Non-Goals:** no retry, no budget accounting of our own; no change to what the summary reports on success beyond the resolved config directory.

## Decisions

- **`host_failure(events, returncode, stderr)` decides, in that order: error result, non-zero exit, missing result.** The error result comes first because it carries the most information and coincides with a non-zero exit; stderr is the fallback for a crash before any result; the missing-result case catches the zero-exit silence. Pure function, tested with synthetic events.
- **`final_text` reads the result event only.** The assistant-text fallback was new behaviour relative to the plain mode and, with the missing-result guard, dead code; verdicts that read the chat (`verdict_check_report`, `verdict_ideate_scoped`) see exactly what they saw before.
- **`host_command(request, model, budget)` factored out** so the pass-through of the budget cap and the stream flags is one pinned list rather than a side effect of a subprocess call.
- **Recorded fixture reduced, not verbatim.** The routing-run result event carries session and model fields and a long final text; the fixture keeps the type, subtype, error flag, duration, turns, cost, a one-sentence text and the four usage counts — the shape the probe depends on — and the README says what was cut.
- **Config setup inside `try`.** `prepare_config` may `sys.exit` on missing credentials; the temp base must still be removed. The summary reports `config_dir` so a `ROUTING_CONFIG_DIR` redirect is visible rather than silently labelled isolated.

## Risks / Trade-offs

- [The recorded event is from 2.1.207, the current host is 2.1.258] → the review compared both schemas and found the read fields identical; the fixture is the tripwire for the next drift.
