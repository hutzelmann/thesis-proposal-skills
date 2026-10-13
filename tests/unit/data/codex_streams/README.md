# Codex dev-runner stream fixtures

Synthetic inputs for the Codex host of the dev runner (`harness/codex_cli.py`,
change `add-codex-dev-runner`). **Every file here is synthetic** except
`features-0160-ok.txt`, a reduction of a feature listing the real CLI printed
offline (below). None was recorded from a run: no ChatGPT login existed in the
harness home when they were written, and no Codex model call was made. The field names follow the Codex sources at
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
| `success.jsonl` | synthetic, `exec_events.rs` + reduced `protocol.rs` records @ rust-v0.160.0 | the shape that passes every guard: provider `openai`, plan `plus`, a credits block with zero balance, one workspace skill (`r0/proposal-check/SKILL.md`, `r0` naming the workspace's `.agents/skills` in the record's `roots`), the turn model `gpt-fixture-a` read as the served one, the last `agent_message` as final text, `input_tokens` including `cached_input_tokens`, quota before and after |
| `skill-read.jsonl` | synthetic, `exec_events.rs` @ rust-v0.160.0 | a `cat …/.agents/skills/proposal-check/SKILL.md` command reads as a `Skill` call naming `proposal-check` (and a later `sed` read of another skill does not change the route); a repeated `item.completed` id is counted once |
| `helper-spawn.jsonl` | synthetic, `exec_events.rs` (`CollabToolCallItem`) @ rust-v0.160.0 | `collab_tool_call` `spawn_agent` reads as `Agent` carrying the verifier-brief prompt; `wait` reads as `collab:wait`; a `file_change` reads as `Edit` |
| `mcp-call.jsonl` | synthetic, `exec_events.rs` (`McpToolCallItem`) @ rust-v0.160.0 | an MCP call reads as `mcp__docs__publish` and makes the run untested for isolation |
| `foreign-skill.jsonl` | synthetic, skills block of `protocol.rs` @ rust-v0.160.0, locators in the 0.160 rendering (below) | a `codex.skills` locator (`r0/grill-me/SKILL.md`) whose root is a home `.agents/skills`: untested for isolation, the resolved path named |
| `cloud-skill-tool.jsonl` | synthetic, the `skills` tool namespace of `ext/skills/src/tools_mod.rs` (`SKILLS_NAMESPACE`) @ rust-v0.160.0 | a `codex.tool` in the `skills` namespace: untested for isolation |
| `provider-leak.jsonl` | synthetic, `session_meta.model_provider` @ rust-v0.160.0 | `model_provider: "openrouter"`: untested, provider and CLI version named |
| `no-rate-limits.jsonl` | synthetic, `event_msg`/`token_count` of `protocol.rs` @ rust-v0.160.0 | a `token_count` with `rate_limits: null`: plan use cannot be confirmed |
| `credits-unreported.jsonl` | synthetic, `token_count.rate_limits` of `protocol.rs` @ rust-v0.160.0 | `rate_limits` without a credits block: plan use cannot be confirmed |
| `credits-drawn.jsonl` | synthetic, `token_count.rate_limits.credits` of `protocol.rs` @ rust-v0.160.0 | `has_credits: true` and a positive balance: untested, the credits named, emptying the balance the one remedy |
| `plan-free.jsonl` | synthetic, `token_count.rate_limits.plan_type` of `protocol.rs` @ rust-v0.160.0 | `plan_type: "free"`: untested, the plan named |
| `limit-reached.jsonl` | synthetic, `token_count.rate_limits.rate_limit_reached_type` of `protocol.rs` @ rust-v0.160.0 | `rate_limit_reached_type` set: untested |
| `model-rerouted.jsonl` | synthetic, the `model rerouted: A -> B (…)` error item @ rust-v0.160.0 | untested, both models named; the served model reads as the reroute target |
| `effort-dropped.jsonl` | synthetic, `turn_context.effort` @ rust-v0.160.0 | `effort: "medium"` against a requested `xhigh`: untested for a precondition, both efforts named |
| `refresh-reused.jsonl` | synthetic, `manager.rs` refresh message @ rust-v0.160.0 | a `turn.failed` with the refresh-token-reused message: untested, `uv run poe host-login codex` named with the Codex login note |
| `restriction-logout.jsonl` | synthetic, the `exec` login-restriction line @ rust-v0.160.0 | the top-level `error` that logs the home out: untested, same remedy |
| `turn-failed.jsonl` | synthetic, `exec_events.rs` (`TurnFailedEvent`, `ThreadErrorEvent`) @ rust-v0.160.0 | a `turn.failed` with another message: a runner failure carrying Codex's message |
| `no-turn-completed.jsonl` | synthetic, `exec_events.rs` (`TurnStartedEvent` with no `TurnCompletedEvent`) @ rust-v0.160.0 | no `turn.completed`: a runner failure saying so, no verdict over partial narration |
| `rollout-success.jsonl` | synthetic raw session record, `protocol.rs` (`RolloutLine`) @ rust-v0.160.0; its skills block in the 0.160 rendering (below) | the skills block reduces to its `roots` table and its `rN/` locators; the reduction keeps only the fields the readers use and drops the rest (base instructions, environment details, git, messages) |
| `quota-ok.json` | synthetic `account/rateLimits/read` answer, app-server protocol v2 @ rust-v0.160.0 | Plus, both windows below 90 %, a credits block with zero balance: the run may start |
| `quota-credits.json` | synthetic `account/rateLimits/read` answer, app-server protocol v2 @ rust-v0.160.0 | a positive balance: refused, the balance named and emptying it the one remedy |
| `quota-no-credits.json` | synthetic `account/rateLimits/read` answer, app-server protocol v2 @ rust-v0.160.0 | windows but `credits: null`: refused as an unavailable read |
| `quota-free.json` | synthetic `account/rateLimits/read` answer, app-server protocol v2 @ rust-v0.160.0 | `planType: "free"`: refused, the plan named (the free-plan rehearsal's login refuses every run) |
| `quota-92.json` | synthetic `account/rateLimits/read` answer, app-server protocol v2 @ rust-v0.160.0 | the 5-hour window at 92 %: refused, the window and its reset time named |
| `quota-reached.json` | synthetic `account/rateLimits/read` answer, app-server protocol v2 @ rust-v0.160.0 | `rateLimitReachedType` set: refused |
| `quota-no-window.json` | synthetic `account/rateLimits/read` answer, app-server protocol v2 @ rust-v0.160.0 | no primary window: refused as an unavailable read |
| `quota-error.json` | synthetic JSON-RPC error answer to `account/rateLimits/read`, app-server protocol v2 @ rust-v0.160.0 | a JSON-RPC error answer: refused as an unavailable read |
| `features-ok.txt` | synthetic, columns shaped after `codex features list` (name, stage, state); the 0.133 default-on set from the brief | only `shell_tool` and `unified_exec` read enabled: passes |
| `features-extra-on.txt` | synthetic, columns shaped after `codex features list` (name, stage, state) as the CLI printed it at 0.133; `features-ok.txt` plus `realtime_conversation` | one more feature reads enabled: refused, the feature named |
| `features-0160-ok.txt` | reduced from `codex features list` with the run's `--disable` flags for a scenario without helpers, codex-cli 0.160.0, live check X7 rerun on 2026-10-13 (empty scratch `CODEX_HOME` holding only the pinned config, no login, `unshare -rn`); 63 of 154 rows kept: every pinned, allowed and subagent feature, every `removed` feature reading true, and a few rows of each other stage. Updated the same day after task 7.3 attempt 1, when `code_mode_host` left the `--disable` flags for the allowlist: a listing under the new flags, taken the same way (scratch homes under `~/.cache/thesis-proposal-dev/`, no login, `unshare -rn`), matches every row kept here except that one, which now reads `true`; the other five `code_mode*` rows were added as listed (68 rows) | the 0.160 shape: two-word stage `under development`, `removed` features reading true, the code-mode host on and every other code-mode feature off; passes without helpers and, with `multi_agent` flipped to true, for a helpers scenario |

Live check X7 (add-codex-dev-runner task 6.2, 2026-10-13) found that codex-cli
0.160.0 prints the two-word stage `under development` and that several
`removed` features read true even under `--disable`. The parser therefore
reads a row as the name (first token), a known stage (the tokens between) and
a known on/off state (last token), and the allowlist check ignores a
`removed` row reading true only when `REMOVED_ENABLED` pins its name (the nine
X7 measured); any other removed feature reading true refuses, since a removed
row still follows the flags. It still fails closed: any other
non-blank line, a stage 0.160 does not print included, refuses the run, so a
changed format reads as a refusal, never as a listing with the enabled feature
missing.

The skills block's 0.160 rendering was read offline on 2026-10-13 with `codex
debug prompt-input` (scratch homes, no login, `unshare -rn`; it renders the
model-visible input and makes no model call), after task 7.3 attempt 1 showed
a locator `r0/proposal-check/SKILL.md` the reader took for a relative path.
The block names each skill root once, as ``- `rN` = `/abs/dir` `` under
`### Skill roots`, and offers each skill as `(file: rN/<name>/SKILL.md)`
under `### Available skills`. The reduction therefore keeps the message's own
table as `roots` beside the locators (`{"type":"codex.skills","roots":{…},
"files":[…]}`); the isolation check resolves an `rN/` locator only against the
same record's table, accepts an absolute locator as it is, and refuses
anything else as unresolved. The saved event lists other than `success.jsonl`
and `foreign-skill.jsonl` keep absolute locators and no `roots`, a shape the
reader still accepts.
