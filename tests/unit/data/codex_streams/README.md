# Codex dev-runner stream fixtures

Synthetic inputs for the Codex host of the dev runner (`harness/codex_cli.py`,
change `add-codex-dev-runner`). **Every file here is synthetic.** None was
recorded: no ChatGPT login existed in the harness home when they were written,
and no Codex model call was made. The field names follow the Codex sources at
the pinned minimum CLI version, tag `rust-v0.160.0`:

- `codex-rs/exec/src/exec_events.rs` and
  `codex-rs/exec/src/event_processor_with_jsonl_output.rs` — the `codex exec
  --json` events (`thread.started`, `turn.started`, `turn.completed` with
  `usage`, `turn.failed` with `error.message`, `item.started`/`item.completed`
  with `command_execution`, `file_change`, `mcp_tool_call`, `collab_tool_call`,
  `web_search`, `agent_message`, `reasoning` and `error` items, and the
  top-level `error` event);
- `codex-rs/protocol/src/protocol.rs` — the session record's `session_meta`,
  `turn_context` and `event_msg`/`token_count` with `rate_limits` (`primary`,
  `secondary`, `credits`, `plan_type`, `rate_limit_reached_type`), and the
  app-server's `account/rateLimits/read` answer in camel case;
- `codex-rs/login/src/auth/manager.rs` — the refresh-failure messages, and the
  login-restriction line of `exec`.

A saved event list (`*.jsonl` other than `rollout-*`) is what the runner keeps
in a workspace's `.devrun-events.jsonl`: the exec events, then the records the
runner reduces from the session record (design Decision 10: `codex.session`,
`codex.turn_context`, `codex.token_count`, `codex.skills`, `codex.tool`,
`codex.error`), then the runner's own `codex.harness` record (duration, exit
status, stderr tail and the quota read before the run). `__WS__` stands for the
run's workspace; the tests substitute it. The model names are synthetic
(`gpt-fixture-a`, `gpt-fixture-b`): the model-ID guard's `gpt-\d` head does not
match them, so `tests/unit/test_model_ids.py` needs no exemption, as with the
`claude-fixture-…` names in `../claude_cli_streams/`. The follow-up change
`record-codex-streams` replaces these files with reduced recordings after the
first approved Plus run, as `../routing_streams/recorded-result.jsonl` was for
Claude.

| file | provenance | what it pins |
| --- | --- | --- |
| `success.jsonl` | synthetic, `exec_events.rs` + reduced `protocol.rs` records @ rust-v0.160.0 | the shape that passes every guard: provider `openai`, plan `plus`, a credits block with zero balance, one workspace skill, the last `agent_message` as final text, `input_tokens` including `cached_input_tokens`, quota before and after |
| `skill-read.jsonl` | synthetic, `exec_events.rs` @ rust-v0.160.0 | a `cat …/.agents/skills/proposal-check/SKILL.md` command reads as a `Skill` call naming `proposal-check` (and a later `sed` read of another skill does not change the route); a repeated `item.completed` id is counted once |
| `helper-spawn.jsonl` | synthetic, `exec_events.rs` (`CollabToolCallItem`) @ rust-v0.160.0 | `collab_tool_call` `spawn_agent` reads as `Agent` carrying the verifier-brief prompt; `wait` reads as `collab:wait`; a `file_change` reads as `Edit` |
| `mcp-call.jsonl` | synthetic, `exec_events.rs` (`McpToolCallItem`) @ rust-v0.160.0 | an MCP call reads as `mcp__docs__publish` and makes the run untested for isolation |
| `foreign-skill.jsonl` | synthetic, skills block of `protocol.rs` @ rust-v0.160.0 | a `codex.skills` path under a home `.agents/skills`: untested for isolation, the path named |
| `cloud-skill-tool.jsonl` | synthetic | a `codex.tool` in the `skills` namespace: untested for isolation |
| `provider-leak.jsonl` | synthetic, `session_meta.model_provider` @ rust-v0.160.0 | `model_provider: "openrouter"`: untested, provider and CLI version named |
| `no-rate-limits.jsonl` | synthetic | a `token_count` with `rate_limits: null`: plan use cannot be confirmed |
| `credits-unreported.jsonl` | synthetic | `rate_limits` without a credits block: plan use cannot be confirmed |
| `credits-drawn.jsonl` | synthetic | `has_credits: true` and a positive balance: untested, the credits named, emptying the balance the one remedy |
| `plan-free.jsonl` | synthetic | `plan_type: "free"`: untested, the plan named |
| `limit-reached.jsonl` | synthetic | `rate_limit_reached_type` set: untested |
| `model-rerouted.jsonl` | synthetic, the `model rerouted: A -> B (…)` error item @ rust-v0.160.0 | untested, both models named; the served model reads as the reroute target |
| `effort-dropped.jsonl` | synthetic, `turn_context.effort` @ rust-v0.160.0 | `effort: "medium"` against a requested `xhigh`: untested for a precondition, both efforts named |
| `refresh-reused.jsonl` | synthetic, `manager.rs` refresh message @ rust-v0.160.0 | a `turn.failed` with the refresh-token-reused message: untested, `uv run poe host-login codex` named with the Codex login note |
| `restriction-logout.jsonl` | synthetic, the `exec` login-restriction line @ rust-v0.160.0 | the top-level `error` that logs the home out: untested, same remedy |
| `turn-failed.jsonl` | synthetic | a `turn.failed` with another message: a runner failure carrying Codex's message |
| `no-turn-completed.jsonl` | synthetic | no `turn.completed`: a runner failure saying so, no verdict over partial narration |
| `rollout-success.jsonl` | synthetic raw session record, `protocol.rs` (`RolloutLine`) @ rust-v0.160.0 | the reduction keeps only the fields the readers use and drops the rest (base instructions, environment details, git, messages) |
| `quota-ok.json` | synthetic `account/rateLimits/read` answer, app-server protocol v2 @ rust-v0.160.0 | Plus, both windows below 90 %, a credits block with zero balance: the run may start |
| `quota-credits.json` | synthetic | a positive balance: refused, the balance named and emptying it the one remedy |
| `quota-no-credits.json` | synthetic | windows but `credits: null`: refused as an unavailable read |
| `quota-free.json` | synthetic | `planType: "free"`: refused, the plan named (the free-plan rehearsal's login refuses every run) |
| `quota-92.json` | synthetic | the 5-hour window at 92 %: refused, the window and its reset time named |
| `quota-reached.json` | synthetic | `rateLimitReachedType` set: refused |
| `quota-no-window.json` | synthetic | no primary window: refused as an unavailable read |
| `quota-error.json` | synthetic | a JSON-RPC error answer: refused as an unavailable read |
| `features-ok.txt` | synthetic, columns shaped after `codex features list` (name, stage, state); the 0.133 default-on set from the brief | only `shell_tool` and `unified_exec` read enabled: passes |
| `features-extra-on.txt` | synthetic | one more feature reads enabled: refused, the feature named |

The feature listing's exact format at 0.160 is unverified; live check X7
(add-codex-dev-runner task 6.2) confirms the parser and the pinned
`DISABLED_FEATURES` against the real CLI with no login and no network.
