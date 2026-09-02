# Routing stream fixtures

Recorded and synthetic `claude -p --output-format stream-json` events, reduced to
the `tool_use` blocks the routing rig reads. They let `harness/routing.py`'s
verdict logic be tested without a model call, and they are the tripwire for a
host output-format change: if Claude Code stops emitting a skill invocation in
this shape, these tests fail with the unparseable input rather than the sweep
silently reporting every case unrouted.

| file | provenance | what it pins |
| --- | --- | --- |
| `routed-check.jsonl` | probe run, 2026-08-10, haiku | a real selection — the mis-route that motivated the rig (a review request answered by `proposal-check`) |
| `unrouted-explore.jsonl` | probe run, 2026-08-10, haiku, `--safe-mode` | no skills available: the agent explores with `Read`/`Bash` and never selects |
| `preparatory-then-route.jsonl` | synthetic | a legitimate glance at the workspace before choosing |
| `chained-sibling.jsonl` | synthetic | the selected skill invoking a sibling; the first pick still owns the route |
| `foreign-skill-first.jsonl` | synthetic | somebody else's skill selected first; not our route, and not fatal |
| `malformed-skill-call.jsonl` | synthetic | a `Skill` call carrying no skill name — the shape change that must raise |
| `helper-fanout.jsonl` | synthetic | a `Task` spawn plus a `result` event with cost fields — the dev-runner probe's failing case and its telemetry source (`harness/claude_runner.py`) |
