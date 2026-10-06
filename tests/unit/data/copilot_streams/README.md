# Copilot dev-runner fixtures

Synthetic inputs for the GitHub Copilot host of the dev runner
(`harness/copilot_cli.py`, change `add-copilot-dev-runner`). **Every file here is
synthetic.** None was recorded: no Copilot token existed in the harness home when
they were written, and no Copilot model call was made. They follow the package of
the pinned CLI, `@github/copilot` 1.0.91, as the V-pass read it (design, "Facts at
1.0.91"):

- `app.js` — the prompt mode's stdout writer (the exclusion set `SBr` at byte
  4738767 and the `result` writer at 4739749);
- `schemas/session-events.schema.json` — the event shapes: `tool.execution_start`
  (`toolCallId`, `toolName`, `arguments`, `mcpServerName`, `mcpToolName`,
  `parentToolCallId`), `tool.execution_complete` (`success`, `sandboxed`, `result`),
  `assistant.message` (`content`, `model`, `parentToolCallId`), `subagent.started`,
  `session.error` (`errorType`, `errorCode`), `session.warning`,
  `session_limits_exhausted.requested`, the ephemeral `session.skills_loaded` and
  `session.mcp_servers_loaded`, and the session file's `session.start`,
  `skill.invoked`, `session.shutdown` (`totalNanoAiu`, `modelMetrics`),
  `session.model_change` and `hook.*`;
- `schemas/api.schema.json` and `copilot-sdk/index.js` — the headless server's
  `connect`, `account.getCurrentAuth` (`authInfo` with `copilotUser.quota_snapshots`,
  `authErrors`) and `models.list` replies; `prebuilds/linux-x64/runtime.node` for the
  snapshot's `overage_entitlement`, which the schema omits;
- offline `copilot skill list --json` and `copilot mcp list --json` runs (no token,
  no network) for the roster shapes.

A stream file is a saved event list as the runner keeps it: the stdout events,
then the reduced `copilot.*` records it reads from the session file, then the
runner's own `copilot.harness` record (the status snapshots before and after,
the cap, the roster, the scenario's helper and network flags). `__WS__` stands
for the workspace and is filled in by the tests. Each stream is `success.jsonl`
with the one change its name says, so every other check in it passes. The model
names are synthetic (`copilot-fixture-a`, the requested one, and
`copilot-fixture-b`), so the model-ID guard (`tests/unit/test_model_ids.py`)
needs no exemption for them. Every fake token is short and obviously synthetic
(`github_pat_SYNTHETIC_TEST_ONLY`, `github_pat_FIXTURE_REPLY_ONLY`).

| file | provenance | what it pins |
| --- | --- | --- |
| `success.jsonl` | synthetic, from @github/copilot 1.0.91 `app.js` and `session-events.schema.json` | the passing shape: a `skill` call naming `proposal-check` with its `skill.invoked` (source `project`), a sandboxed shell call, the loaded-skills report, a shutdown at 12 credits under a 30-credit cap, and the `result` line |
| `exit0-error.jsonl` | synthetic, from @github/copilot 1.0.91 `session-events.schema.json` | a `model_call` session error under exit code 0: the event decides, a runner failure |
| `skill-failed.jsonl` | synthetic, from @github/copilot 1.0.91 `session-events.schema.json` | a `skill` call whose completion reports failure: an attempt, not a `Skill` call |
| `skill-file-view.jsonl` | synthetic, from @github/copilot 1.0.91 tool schema in `runtime.node` | a `view` of `.agents/skills/proposal-check/SKILL.md`: a `Read` flagged as a skill-file read, no `Skill` call |
| `helper-spawn.jsonl` | synthetic, from @github/copilot 1.0.91 `task` tool schema and `subagent.started` | a supervise run's one `task` call carrying the verifier brief, the helper's message on a second model, and per-model usage naming both: one `Agent` call, not untested |
| `unknown-tool.jsonl` | synthetic, from @github/copilot 1.0.91 `session-events.schema.json` (`tool.execution_start.toolName`) | a tool name neither offered nor internal: untested for a precondition |
| `mcp-call.jsonl` | synthetic, from @github/copilot 1.0.91 `mcpServerName`/`mcpToolName` | an MCP tool call: untested for isolation, `mcp__docs__publish` |
| `mcp-connected.jsonl` | synthetic, from @github/copilot 1.0.91 `session.mcp_servers_loaded` | a server reported `connected`: untested for isolation |
| `foreign-skill.jsonl` | synthetic, from @github/copilot 1.0.91 `skill.invoked` | a skill invoked from source `inherited`, outside the workspace: untested for isolation |
| `skills-unreported.jsonl` | synthetic, from @github/copilot 1.0.91 `session-events.schema.json` (`session.skills_loaded`, ephemeral) | no `session.skills_loaded`: untested, the loaded skills not confirmed |
| `hook-event.jsonl` | synthetic, from @github/copilot 1.0.91 `hook.*` | a hook event in the session file: untested for isolation |
| `sandbox-ignored.jsonl` | synthetic, from @github/copilot 1.0.91 `runtime.node` byte 6939584 | the "Sandboxing is enabled but is not supported on this host" warning: untested for isolation, isolation stop |
| `sandbox-unreported.jsonl` | synthetic, from @github/copilot 1.0.91 `tool.execution_complete.sandboxed` | a shell completion without `sandboxed`: the sandbox not reported active, isolation stop; played by the fake client before a hang, the live watch stops the run at that completion |
| `model-differs.jsonl` | synthetic, from @github/copilot 1.0.91 `session-events.schema.json` (`assistant.message.model`) | a top-level message on `copilot-fixture-b`: untested for a precondition, both models named |
| `model-switch.jsonl` | synthetic, from @github/copilot 1.0.91 `session.model_change.cause` | `rate_limit_auto_switch`: untested for a precondition |
| `effort-unapplied.jsonl` | synthetic, from @github/copilot 1.0.91 `runtime.node` byte 7688290 | the "does not support reasoning effort configuration" warning for a requested `high`: untested for a precondition |
| `auth-error.jsonl` | synthetic, from @github/copilot 1.0.91 `ErrorData.errorType` | an `authentication` session error: untested, the fine-grained token remedy and the not-affected note |
| `quota-error.jsonl` | synthetic, from @github/copilot 1.0.91 `ErrorData.errorCode` | a `quota` error: untested as a limit reached, no stop |
| `soft-cap.jsonl` | synthetic, from @github/copilot 1.0.91 `runtime.node` byte 8628857 | `session_limits_exhausted.requested` and `ai_credit_soft_cap_exhausted`: untested, billing stop |
| `session-limits.jsonl` | synthetic, from @github/copilot 1.0.91 `ErrorData.errorType` | a `session_limits` error: untested, billing stop |
| `over-cap.jsonl` | synthetic, from @github/copilot 1.0.91 `ShutdownData.totalNanoAiu` | 65 credits against a 30-credit cap (more than twice): untested, billing stop |
| `zero-nano.jsonl` | synthetic, from @github/copilot 1.0.91 `app.js` `totalNanoAiu??0` | zero nano-AIU while the per-model usage reports tokens: untested, billing stop |
| `no-result.jsonl` | synthetic, from @github/copilot 1.0.91 `result` writer | no closing `result` line: a runner failure |
| `no-shutdown.jsonl` | synthetic, from @github/copilot 1.0.91 `session-events.schema.json` (`session.shutdown`) | no `session.shutdown`: a runner failure (exit 4, never 3) with a billing stop |
| `token-in-output.jsonl` | synthetic, from @github/copilot 1.0.91 `app.js` (the stdout writer's `processSecretFilterFilter`) | the synthetic token in a message, a tool result and the stderr tail: scrubbed, untested for isolation, isolation stop |
| `events-raw.jsonl` | synthetic, from @github/copilot 1.0.91 `session-events.schema.json` | a raw session file with `system.message`, a user message, a `skill.invoked` carrying `content`, and extra fields: the reduction keeps only what the readers use |
| `status-ok.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`AccountGetCurrentAuthResult`, `TokenAuthInfo`) and `runtime.node` serde fields; the auth type is the one K1 recorded live for the named token (task 7.5) | `token` auth on `https://github.com`, token-based billing, `premium_interactions` with permission false, entitlement 0, count 0 and 80 % remaining; fake `login` (in `copilotUser`), organization lists and `token` the parse drops. The other `status-*.json` with a login share its `authInfo` shape |
| `status-no-overage-field.json` | synthetic, from @github/copilot 1.0.91 `runtime.node` serde fields, as `status-ok.json` | no `overage_permitted` (what `getQuota` would map to "no overage"): budget possible, refused |
| `status-no-entitlement-field.json` | synthetic, from @github/copilot 1.0.91 `runtime.node` serde fields, as `status-ok.json` | no `overage_entitlement`: budget possible, refused |
| `status-budget.json` | synthetic, from @github/copilot 1.0.91 `runtime.node` serde fields | `overage_permitted: true`: refused, delete the budget |
| `status-entitlement.json` | synthetic, from @github/copilot 1.0.91 `runtime.node` serde fields | `overage_entitlement: 50`: refused, delete the budget |
| `status-overage-drawn.json` | synthetic, from @github/copilot 1.0.91 `runtime.node` serde fields | `overage_count: 3`: refused, the reset date named |
| `status-legacy.json` | synthetic, from @github/copilot 1.0.91 `runtime.node` serde field `token_based_billing` | `token_based_billing: false`: refused, consumption in credits unreadable |
| `status-low.json` | synthetic, from @github/copilot 1.0.91 `runtime.node` serde field `percent_remaining` | 8 % remaining: refused, the reset date named |
| `status-free-chat.json` | synthetic, from @github/copilot 1.0.91 `runtime.node` (`/quota_snapshots/chat`; the SKU rule is 1.0.67's `app.js`) | SKU `free_limited_copilot`: the `chat` snapshot is chosen, not the exhausted `premium_interactions` |
| `status-no-user.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`TokenAuthInfo.copilotUser`, optional) | no `copilotUser`: the read unavailable |
| `status-auth-error.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`AccountGetCurrentAuthResult.authErrors`) | no `authInfo` and an auth error that names the fake login and token: the token remedy, nothing echoed |
| `status-gh-cli.json` | synthetic, from @github/copilot 1.0.91 `AuthInfoType` | auth type `gh-cli`: another credential reached the client |
| `status-enterprise.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`TokenAuthInfo.host`) | a host other than `https://github.com`: refused |
| `status-error.json` | synthetic, from @github/copilot 1.0.91 `copilot-sdk/index.js` (a JSON-RPC error reply) | a JSON-RPC error whose message carries the fake login and token: unavailable, naming the method and the code only |
| `models.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`Model`, `ModelPolicyState`) | four models: enabled with efforts, enabled without, `disabled`, `unconfigured` |
| `skills-ok.json` | synthetic, from @github/copilot 1.0.91 offline `copilot skill list --json` (shape) | the staged skill (source `project`) and the two bundled ones (source `builtin`) |
| `skills-extra.json` | synthetic, from @github/copilot 1.0.91 offline `copilot skill list --json` (source `inherited`, measured) | plus an `inherited` skill: the roster refuses, naming it |
| `mcp-ok.json` | synthetic, from @github/copilot 1.0.91 offline `copilot mcp list --json` (shape) | only the built-in `github-mcp-server`, source `builtin` |
| `mcp-extra.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (MCP server sources) | plus a `user` server: the roster refuses, naming it |
| `probe-ok.json` | synthetic, from @github/copilot 1.0.91 `session.shell.executeUserRequested` and `tool.execution_complete.sandboxed` | every target denied (the harness process's environment among them), `gh` and `git` non-zero, the interpreter and the skill script run, every command sandboxed. Every `probe-*.json` also carries the host rows: the measured `net_ns` `private`, which refuses nothing, and the two `/tmp` rows, which refuse since the user's decision D-b unless `denied`: `host_tmp` `denied`, and `tmp_write` `denied`, the word the harness itself reads on the host (in an end-to-end probe it replaces whatever the shell printed with `writable` or `denied`). The fake server answers with a `probe-*.json` only once `session.options.update` put the session in the home's sandbox block; without it, it answers as the 1.0.91 server did at K6 (every target readable, `gh` 0, nothing reported sandboxed) |
| `probe-token-readable.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`session.shell.executeUserRequested`) | the token file readable: refused for isolation |
| `probe-environ-readable.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`session.shell.executeUserRequested`) | the client process's environment readable: refused for isolation |
| `probe-harness-environ-readable.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`session.shell.executeUserRequested`) | the harness process's own environment readable (the host's `/proc` reachable from the sandbox): refused for isolation |
| `probe-gh-token.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`session.shell.executeUserRequested`) | `gh auth token` over the session bus exits 0: refused for isolation |
| `probe-git-credential.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`session.shell.executeUserRequested`) | `git credential fill` for github.com exits 0: refused for isolation |
| `probe-skill-fails.json` | synthetic, from @github/copilot 1.0.91 `api.schema.json` (`session.shell.executeUserRequested`) | the skill script fails: refused as a precondition |
| `client-config.jsonc` | synthetic, from @github/copilot 1.0.91 `runtime.node` strings (the two header lines) and `app.js` (`globalStateWriteKeyForContext(…, "firstLaunchAt", …)`), shaped as an offline headless start wrote it into a scratch `COPILOT_HOME` (no token, no network); the timestamp is invented | the client's own `config.json`: the two-line `//` header and `firstLaunchAt` only, which the clean-home rule accepts; the tests derive the refused variants from it (an extra key, a token-shaped value, a block comment) |

Replaced by reduced recordings in the follow-up change `record-copilot-streams`,
after the first approved run.
