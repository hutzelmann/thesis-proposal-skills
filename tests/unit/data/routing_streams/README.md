# Routing stream fixtures

Recorded and synthetic `claude -p --output-format stream-json` events, reduced to
the events the harness reads: the `tool_use` blocks for the routing rig, plus the
`result` event for the dev-runner probe and for the rig's host-error check, plus
the `system/init` and `system/commands_changed` events the account-surface checks
read (`harness/account_surfaces.py`). They let `harness/routing.py`'s and
`harness/claude_runner.py`'s verdict logic be tested without a model call, and
they are the tripwire for a host output-format change: if Claude Code stops emitting a skill invocation in
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
| `helper-fanout.jsonl` | synthetic | a `Task` spawn plus a `result` event with cost fields — the dev-runner probe's failing case (`harness/claude_runner.py`) |
| `expired-login.jsonl` | synthetic, shape recorded 2026-10-03 and 2026-10-04 | the host ending a run on a dead login: `is_error` true, subtype `success`, `errors` null, the reason in `result` — an error for the rig, never an unrouted case |
| `recorded-result.jsonl` | routing run, 2026-08, Claude Code 2.1.207 | the host's real `result` event reduced to the fields the probe reads (session and model fields dropped, text truncated to one sentence) — the telemetry tripwire |
| `claudeai-surfaces.jsonl` | routing run, 2026-10-05, Claude Code 2.1.284, case `write-polish-collision` | the claude.ai account surfaces reaching an isolated run: `system/init` reduced to its MCP servers (the Claude Docs connector), plugins, skills, a four-entry `slash_commands` subset, `apiKeySource` and version; then the two `system/commands_changed` events, each cut to two entries tagged "(claude.ai sync)" with their `anthropic-skills:` alias and one `proposal-*` entry, descriptions shortened to their first 60 characters and their tag. Session, socket, scratchpad, memory and working-directory fields dropped |
| `clean-init.jsonl` | synthetic, 2.1.284 shape | an isolated run with the surfaces closed: no MCP server, only `@builtin` plugins, a command-list change with no tagged entry |
| `ambient-user-mcp.jsonl` | synthetic, 2.1.284 shape | an ambient run's `init` listing one MCP server the operator configured (source `user`) and one from claude.ai (source `claudeai`); only the second is a surface |
