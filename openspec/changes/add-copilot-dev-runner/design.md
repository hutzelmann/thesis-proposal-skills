# Design

## Context

**Order.** This change lands after `add-codex-dev-runner` (change 3), which lands after `close-claudeai-surfaces` (change 1) and `add-harness-claude-login` (change 2). It is change 4, and it builds on what changes 1 to 3 leave in place.

- **`harness/hosts.py`**: `Host`, `RunView` and `JudgeBackend`. `HOSTS` is built late in `claude_runner`, alongside `host_for(args)`, `stage(scenario, ws, install_skill, skill_dir)`, `--host`, and the `host`/`label` summary keys.
- **`harness/host_login.py`**:
  - the frozen `HostLogin` record with change 3's fields `strip_suffixes`, `stop_signal`, `outside_tempdir` and `child_vars`, plus `RECORDS`, `state_root`, `check_location(..., tempdir)`, marker, seed and `wipe`;
  - `allowlisted_env(record, config, environ)`, `login_env`, `AGENT_MARKERS`;
  - `LoginProblem(cause, remedy, client)`, `NOTES`, `login_note`, `refusal` and `login_remedy(message, source, record)`;
  - `run_lock`/`RunLockBusy`/`LOCK_WAIT_S`, and `run_host(record, argv, *, cwd, env, timeout, input, pass_fds)` with the Linux parent-death signal;
  - `TERM_GRACE_S` and `stop_child(proc, sig)`;
  - `main(argv)` behind `poe host-login`, `host-status` and `host-logout`.
- **The `read_quota` seam**, from change 3's Decision 9. It runs a client child under the run lock and makes no model call.
- **Judge isolation per backend**, from change 3's Decision 13. The Claude judge enters a fresh isolated Claude configuration for a run on another host.
- **The exit statuses**: 0 pass, 1 fail, 2 usage, 3 untested, 4 runner failure. Untested has three reasons: subscription, isolation and precondition.

**Shared blocks.**

- This change MODIFIES four requirements:
  - "Harness-owned host logins", "Dev-runner host adapters" and "Dev-runner cost and helper-agent telemetry". Each starts from change 3's current text, which itself folds in change 2's text as revised on 2026-10-05 and change 3's host-generic rewording.
  - "Isolated child environment". Change 3 does not modify it, so its block starts from change 2's text.
- Change 3's generic wording leaves "Inverted-hybrid runners", "Measured environments carry no eval definitions" and "Subscription text roles (dev runner)" with no sentence that counts the hosts. They therefore stay unmodified (Decision 2).
- If change 2 or 3 is revised again before it is archived, these blocks are rebased (tasks 0.1 and 9.3).

**Copilot facts this design relies on.**

- All of them were verified at CLI 1.0.67, by byte offset in the unpacked `app.js`, by strings in `runtime.node`, and in the local help and fetched docs (design brief, 2026-10-05).
- D-C3(b) pins 1.0.91. Task 1.2's V-pass re-derives every one of them from the 1.0.91 package before any fixture is written. A fact that changed in a way that alters a rule is revised through `openspec-update-change`, never patched in code alone.

The facts:

- **Credential precedence.** `COPILOT_GITHUB_TOKEN`, then `GH_TOKEN`, then `GITHUB_TOKEN`, then a stored OAuth token (keyring, or a plaintext file under `storeTokenPlaintext`), then a `gh auth token` fallback run by `runtime.node`.
  - Classic `ghp_` tokens are rejected in `-p` mode.
  - The hidden `--no-auto-login` disables both the stored-token and the `gh` fallbacks (`app.js` 8388924 and 8395006; supported per `changelog.md:166`). At 1.0.91 it disables reading `COPILOT_GITHUB_TOKEN` too, so every child that carries the token names it with `--auth-token-env` (facts measured after the first login).
- **`gh` reaches the keyring.** `gh` links godbus and go-keyring. godbus uses a non-empty `DBUS_SESSION_BUS_ADDRESS` verbatim, and otherwise falls back to `/run/user/<uid>/bus` whatever `XDG_RUNTIME_DIR` says.
- **The stdout stream.**
  - `--output-format json` writes events outside a filter set (`app.js` 8182243):
    - `tool.execution_start` and `tool.execution_complete`;
    - `assistant.message`;
    - `subagent.started`;
    - `session.error` and `session.warning`;
    - a closing `result` line (8183071).
  - `assistant.usage` reaches neither stdout nor disk.
  - `session.skills_loaded` and `session.mcp_servers_loaded` are ephemeral. They pass the filter but may be emitted before the writer subscribes.
- **On disk.** `<COPILOT_HOME>/session-state/<uuid>/events.jsonl` holds:
  - `session.start`, which echoes the creation options only (3318314);
  - `skill.invoked` (`name`, `path`, `source`, `trigger`);
  - `session.shutdown` (`totalNanoAiu`, `totalPremiumRequests`, `modelMetrics`);
  - `session.model_change`, `hook.*` and `system.message`.
  - `--session-id` sets the UUID of a new session (8379791).
- **Quota.**
  - `account.getCurrentAuth` returns `copilotUser.quota_snapshots` raw.
  - `getQuota` coerces a missing `overage_permitted` to `false` and a missing `overage_count` to `0` (`EZ`, 905928). It also fetches `/copilot_internal/user` itself when `copilotUser` is absent (3273391).
  - The CLI reads the `chat` snapshot for `free_limited_copilot` and `premium_interactions` otherwise (2314646 and 7175749).
  - A missing `total_nano_aiu` reads as 0 (2357086).
  - The relevant error codes are `session_limits` and `ai_credit_soft_cap_exhausted` (3118451 and 3118639).
- **Configuration.**
  - `config.json` overrides `settings.json` key by key (`runtime.node` string).
  - `sandbox.allowBypass` and `sandbox.auth.{git,gh}` default to true (`cli-config-dir-reference.md:498-501`).
  - **The deny-list key path is contradicted.** The docs name `sandbox.userPolicy.deniedPaths` (`cli-config-dir-reference.md:506`). The 1.0.67 package names only `sandbox.userPolicy.filesystem.deniedPaths`: its `runtime.node` strings carry that path once and `userPolicy.deniedPaths` zero times, and `schemas/api.schema.json` nests `deniedPaths` under `SandboxConfigUserPolicyFilesystem`, with `additionalProperties: false` at every level. A sandbox key that the CLI does not read is ignored silently (`changelog.md:398`, 1.0.79).
  - `sandbox.allowDevToolAccess` (renamed from `allowDevToolCaches` at 1.0.79) defaults to on, and since 1.0.83 it grants the sandboxed shell and file tools developer-tool configuration, "including token-bearing registry config such as ~/.npmrc" (`changelog.md:263`, `:398`, `:426`).
  - `--sandbox` exists since 1.0.70. When the sandbox is unavailable it only warns that it was "ignored" and runs the shell unconfined (`changelog.md:640`). Only an administrator's managed `sandbox.failIfUnavailable` turns that into a block (`cli-config-dir-reference.md:431`), so a personal account cannot.
  - Since 1.0.83 the Linux sandbox needs `slirp4netns`, `nsenter`, `iptables`, `ip6tables`, `iptables-restore` and `ip6tables-restore` on `PATH`, besides `bwrap` (`changelog.md:277`).
  - Windows cannot enforce `deniedPaths` (`:506`).
  - At 1.0.89 the sandboxed shell "can access session files and logs" (`changelog.md:48`), which are under `COPILOT_HOME`.
  - The 1.0.67 SDK declares model-free shell calls on a session, `shell.exec` and `shell.executeUserRequested` (`copilot-sdk/generated/rpc.d.ts:14641`, `:14657`, both experimental). Whether they run inside the session's sandbox is UNVERIFIED.
- **Auto-update.** Unless `--no-auto-update` or `COPILOT_AUTO_UPDATE=false` is set, the loader runs the newest cached `app.js` it finds, the operator's `~/.cache/copilot/pkg` included.
- **Skill discovery.**
  - In a folder that is not a git repo, the CLI reads `.agents/skills`, `.github/skills` and `.claude/skills` in every parent folder as `inherited` (measured).
  - `~/.agents/skills` is not read when `COPILOT_HOME` is set (changelog 1.0.66, measured).
  - The bundled `customize-cloud-agent` skill is always listed.
- **Exit codes.** Since 1.0.87, a failed child task can still exit 0, and a `model_call` error does not change the exit code.

**Facts at 1.0.91 (V-pass, 2026-10-06, task 1.2).**

- **The version.** `pacman -Q github-copilot-cli-bin` reads `1.0.91-1`, and the binary run as task 1.1 prescribes (`unshare -rn`, scratch `HOME`, `COPILOT_HOME` and `COPILOT_CACHE_HOME`, `COPILOT_AUTO_UPDATE=false`) prints `GitHub Copilot CLI 1.0.91.` and unpacks `pkg/linux-x64/1.0.91/` into the scratch cache. The operator's own `~/.cache/copilot/pkg/linux-x64/` also holds a 1.0.92, which the operator's auto-updating CLI downloaded; with auto-update off and the harness's own cache, a harness child runs the bundled 1.0.91. The pin therefore stays at 1.0.91, as D-C3(b) planned. The implementation's workflow brief asked for a 1.0.92 pin on the reading that 1.0.92 was installed; that reading is the operator's auto-updated CLI, and a 1.0.92 pin would refuse every harness run (its version check reads 1.0.91) until the package itself ships 1.0.92, so the pin stays. A spot check of the 1.0.92 package (its `app.js` is now a 40 KB loader beside `cli-main.js`) found the stdout exclusion set, the deny-list path, the sandbox message and the snapshot fields unchanged. A differential check on 2026-10-06 (string counts over `app.js`/`cli-main.js`, `runtime.node`, `cli-native.node`, `schemas/` and `copilot-sdk/` of both packages, no execution of 1.0.92) widened that: none of the 85 pinned fact strings (flags, error codes, RPC methods, snapshot fields, sandbox texts and tools, managed paths, settings keys, environment names, signal list) changed presence; the stdout exclusion set is identical (36 entries); `SandboxConfig`, `SandboxConfigUserPolicyFilesystem`, `SandboxHostSupport`, `AccountGetCurrentAuthResult` and the premium-interactions snapshot schema are identical. 1.0.92 only adds: an `AuthInfo` variant of type `account` (a provider-owned account; the status read's env-auth row refuses it), a `tool.shell_output` event (on stdout, read by no reader, covered by `scrub`), and model-provider configuration RPCs (the strip families keep their variables out). Bumping the pin remains its own change with a full V-pass, but no rule would change.
- **Sources read.** `<cache>/pkg/linux-x64/1.0.91/`: `app.js` (7.2 MB), `prebuilds/linux-x64/runtime.node` and `cli-native.node` strings, `schemas/api.schema.json`, `schemas/session-events.schema.json`, `copilot-sdk/index.js`, `builtin-skills/`, `changelog.json`; the output of `copilot --help`, `copilot skill list --help` and `copilot mcp list --help`. Three model-free, offline measurements (`unshare -rn`, scratch homes, no token): `copilot skill list --json` and `copilot mcp list --json` in a scratch workspace, once with and once without `COPILOT_HOME`.

| Fact | At 1.0.67 (above) | At 1.0.91 | Rule impact |
|---|---|---|---|
| Deny-list key path | package `sandbox.userPolicy.filesystem.deniedPaths`; docs `sandbox.userPolicy.deniedPaths` | `sandbox.userPolicy.filesystem.deniedPaths`: `runtime.node` 7851854 (settings catalog: "Absolute paths sandboxed commands are denied access to, even if nested under a read/write or read-only path"), schema `SandboxConfigUserPolicyFilesystem.deniedPaths` with `additionalProperties:false`; `userPolicy.deniedPaths` occurs 0 times | none: the pinned block already follows the package; the docs' reading is wrong at 1.0.91 |
| Sandbox defaults | `allowBypass` and `auth.{git,gh}` default true | schema: `allowBypass` "Default: false (opt-in)", `auth.git`/`auth.gh` "Default: false (opt-in)", `allowDevToolAccess` "Default: true"; new keys `addCurrentWorkingDirectory` (default true), `sandboxMcpServers`, `sandboxLspServers`, `credentials` | none: the pinned values (all false) stay explicit |
| Pinned settings keys | brief's list | every key of `pinned_settings` is in the `runtime.node` settings catalog: `autoUpdate` 7833366, `memory` 7836894, `continueOnAutoMode` 7841029, `storeTokenPlaintext` 7846258, `customAgents.defaultLocalOnly` 7849047, `ide.autoConnect` 7849166, `sandbox.enabled` 7851448, `sandbox.allowBypass` 7854587, `sandbox.auth.git` 7854724, `sandbox.auth.gh` 7854947, `disableAllHooks` 7859901, `experimental` 7862082; `allowDevToolAccess` in the schema. The unknown-key warning covers top-level keys only (changelog 1.0.78) | none |
| Sandbox unavailable | "ignored" warning, shell runs unconfined (1.0.70) | `runtime.node` 6939584: "Sandboxing is enabled but is not supported on this host, so shell commands and sandboxed services will fail."; 6997010: "Sandboxing is enabled but not supported on this platform: "; 7013801: "sandbox enforcement unavailable: "; no `--sandbox … was ignored` string remains (only the two `--no-sandbox was ignored` enterprise notices). The SDK's `sandbox.getHostSupport` (schema `SandboxHostSupport`) says an unsupported policy feature "fails each sandboxed command with `reason`" | none: the before-run and after-run checks stay as defence in depth; the after-run check matches these texts (`SANDBOX_WARNINGS`) |
| Sandbox-active report | UNVERIFIED | `sandbox.decision` (kind `enforcement_state`, outcome `engaged`) is ephemeral (`"const": true`) and in the stdout exclusion set (`app.js` 4738767), so it reaches neither stdout nor the session file. `tool.execution_complete.sandboxed` ("Whether this tool execution ran inside a sandbox container") is on stdout and on disk | the runner reads the report from `sandboxed` on every shell-tool completion: false or absent, or no shell completion at all, is "not reported active" (untested for isolation, isolation stop) |
| Tools the Linux sandbox needs | `bwrap` plus six (1.0.83) | `runtime.node`: "Bubblewrap (bwrap) is not installed or not on PATH", "requires util-linux 'unshare' on PATH", "requires 'slirp4netns' on PATH", and the proxy supervisor script runs `nsenter --net=… -- iptables-restore` and `ip6tables-restore` (7922595); changelog 1.0.83 still names `iptables` and `ip6tables` | `SANDBOX_TOOLS` = `bwrap`, `unshare`, `slirp4netns`, `nsenter`, `iptables`, `ip6tables`, `iptables-restore`, `ip6tables-restore` (one more than 1.0.83: `unshare`) |
| Model-free shell call and its confinement | `shell.exec`, `shell.executeUserRequested` declared; confinement UNVERIFIED | `session.shell.exec` and `session.shell.executeUserRequested` (schema, both experimental; SDK `index.js`); the latter returns `{toolCallId, success, output, exitCode}` and runs through the session's user-requested shell flow (`runtime.node`: `src/runtime/src/session/user_requested_shell_flow.rs`). Whether it runs inside the sandbox is not provable from strings, but each completion carries `tool.execution_complete.sandboxed`, delivered to the client as a `session.event` notification | the probe stays (Decision 13): it runs through `executeUserRequested` and refuses for isolation unless every probe command reports `sandboxed: true`. Fail-closed either way: a probe command outside the sandbox reads the token file and refuses. K6 confirms |
| Resolved-policy read | UNVERIFIED | none: `session.sandbox.getEnforcementStatus` reports only managed enforcement (`blocked`, `reason`, `required`); `sandbox.getHostSupport` reports host support | the probe adds `sandbox.getHostSupport.supported` as a row |
| Client tools inside the sandbox | UNVERIFIED | file tools are sandboxed since 1.0.83 (changelog); whether the bundled `rg` (under the package cache in `<state>/cache/copilot`, inside the denied account home) executes inside the sandbox is not derivable from strings | unchanged: P2's tool results show it; a failure revises the deny list through `openspec-update-change`. A `PATH` whose first `python3` lies under the account home (the repository's `.venv/bin` under `uv run`) is denied inside the sandbox too; the probe's `python3` row then refuses as a precondition, which K6 shows |
| `--effort` | `--effort` | absent: the flag is `--reasoning-effort <level>` (`--help`; `cli-native.node` 407216), values `none, minimal, low, medium, high, xhigh, max`; changelog 1.0.88: "An explicit `--reasoning-effort` still wins" | the command passes `--reasoning-effort` (Decision 8); `--effort` stays the harness's own option name |
| Effort left unapplied | 1.0.88 changelog | text `Model "…" does not support reasoning effort configuration (requested: "…").` (`runtime.node` 7688290); its event type is not derivable | the reader matches that text in `session.warning`, `session.info` and `session.error` messages; otherwise the effort reads "requested, not verified" |
| Hidden flags | `--no-auto-login` hidden; `--sandbox` since 1.0.70 | `cli-native.node`: `--headless` "Enable headless JSON-RPC server mode (alias for --server)" 669417, `--stdio` "Use stdio transport for server mode" 669745, `--sandbox` "Run this session's shell commands inside the OS-level sandbox for this run only" 671189, `--no-auto-login` "Disable automatic login detection (stored OAuth tokens and gh CLI)" 673063 | none |
| Decision 8 flags | 1.0.67 help | in the 1.0.91 help: `-p`, `--output-format`, `--stream`, `--no-color`, `--session-id` ("set the UUID for a new session"), `--model`, `--allow-all-tools`, `--available-tools`, `--deny-tool`, `--allow-url`, `--disable-builtin-mcps` ("currently: github-mcp-server, githubiq"), `--no-custom-instructions` ("Disable loading of custom instructions from AGENTS.md and related files"), `--no-ask-user`, `--no-remote`, `--no-remote-export`, `--no-auto-update` ("runs the version bundled in the executable"), `--no-bash-env`, `--disallow-temp-dir`, `--secret-env-vars`, `--log-level`, `--log-dir`, `--max-ai-credits`; `--max-ai-credits` at `cli-native.node` 671683 | none |
| stdout filter and `result` | `l_o` set, 8182243/8183071 | `SBr` at `app.js` 4738767 excludes `session.shutdown`, `session.model_change`, `assistant.usage`, `hook.*`, `system.message`, `skill.invoked(_ref)`, `skill.context_delivered(_ref)`, `sandbox.decision` and the session bookkeeping events; the writer passes every value through `processSecretFilterFilter`. `result` (`lQt`, 4739749): `{type, timestamp, sessionId, exitCode, usage:{premiumRequests, totalApiDurationMs, sessionDurationMs, codeChanges}}` | none |
| Session records | `skill.invoked`, `session.shutdown`, `session.model_change` | schema: `skill.invoked` requires `name, path, content` (the SKILL.md text: the reduction drops it) and carries `source`, `trigger` (`user-invoked`, `agent-invoked`, `context-load`); `session.shutdown` carries `shutdownType` (`routine`, `error`), `errorReason`, `totalPremiumRequests`, `totalNanoAiu` (optional; `totalNanoAiu??0` at `app.js` 5184652 and 6819791), `modelMetrics.<model>.{requests, usage:{inputTokens, outputTokens, cacheReadTokens, cacheWriteTokens, reasoningTokens}, totalNanoAiu}`; `session.model_change.cause` `rate_limit_auto_switch`. New on stdout: `session_limits_exhausted.requested {usedAiCredits, maxAiCredits}` | the soft-cap check also reads `session_limits_exhausted.requested` |
| `session.error` | `session_limits` 3118451, `ai_credit_soft_cap_exhausted` 3118639 | `runtime.node`: `ai_credit_soft_cap_exhausted` 8628857, `session_limits` among the error types; schema `ErrorData.errorType` "authentication", "authorization", "quota", "rate_limit", "context_limit", "query" | none |
| Status RPC and handshake | `account.getCurrentAuth`, `models.list` | Content-Length JSON-RPC (vscode-jsonrpc); handshake `connect {supportedTaskKinds}` → `protocolVersion` (SDK `MIN_PROTOCOL_VERSION = 3`), fallback `ping`. `account.getCurrentAuth` → `{authInfo, authErrors: string[]}`; `authInfo` (`EnvAuthInfo`: `type, host, login, token, envVar, copilotUser?`), types `hmac, env, user, gh-cli, api-key, token, token-provider, copilot-api-token`. `models.list` → `{models:[{id, policy:{state: enabled, disabled, unconfigured}, supportedReasoningEfforts}]}`. Sessions: `session.create {sessionId, workingDirectory, …}`, `session.delete`; events arrive as `session.event {sessionId, event}` notifications. The two status methods authenticate and list; neither sends a prompt | none |
| Quota snapshot fields | `overage_entitlement` parsed by `app.js` | the quota parse moved to Rust: `runtime.node` serde fields `entitlement, overage_count, overage_entitlement, overage_permitted, percent_remaining, quota_remaining, remaining, unlimited, timestamp_utc, has_quota, quota_reset_at, token_based_billing`; but the SDK schema's `CopilotUserResponseQuotaSnapshotsPremiumInteractions` omits `overage_entitlement`. `getQuota`'s coercion now lives in Rust (mapped fields `overage`, `overageAllowedWithExhaustedQuota`) | none, but a risk: if the reply omits `overage_entitlement`, every run refuses ("budget possible"), fail-closed by design. K2 settles it at $0 |
| Snapshot selection | `free_limited_copilot` → `chat` | the SKU literal is gone from both files; `runtime.node` reads `/quota_snapshots/premium_interactions`, `/quota_snapshots/chat`, `/monthly_quotas/chat` and `/limited_user_quotas/chat` | none: the harness keeps the 1.0.67 rule; for the teacher Pro plan it picks `premium_interactions` either way |
| Tool names | Decision 10 | shell tools `bash`/`powershell`/`local_shell`, `read_bash`, `write_bash`, `stop_bash`, `list_bash` (`runtime.node` 8572500; `app.js`); `skill` takes `skill` (`runtime.node` tool schema); `task` takes `name`, `description`, `agent_type`, `prompt`, `model`; `apply_patch`, `str_replace`, `report_intent`, `update_todo`, `task_complete`, `store_memory`, `ask_user`, `fetch_copilot_cli_documentation`, `read_agent`, `list_agents`, `write_agent`, `web_fetch`, `web_search` present | `local_shell` maps to `Bash` |
| Parent-folder walk | measured | measured again: parent `.agents/skills` and `.github/skills` list as `inherited` | none |
| `COPILOT_HOME` gate on `~/.agents/skills` | measured | measured again: listed as `personal-agents` without `COPILOT_HOME`, absent with it | none |
| Bundled skills | `customize-cloud-agent` | `builtin-skills/` holds `customize-cloud-agent`, `discover-resources`, `github-pr-media`; `skill list --json` lists `customize-cloud-agent` and `github-pr-media` (source `builtin`); shape `[{name, description, source, path, enabled}]` | `BUILTIN_SKILLS` = both listed names; the spec says "bundled skills" |
| Built-in MCP servers | `github-mcp-server` | `--help`: `github-mcp-server`, `githubiq`; `mcp list` reports `github-mcp-server` only when signed in (changelog 1.0.87); signed out the JSON is `{"mcpServers": {}}`; sources `user, workspace, plugin, builtin, managed` | `BUILTIN_MCP` = both names |
| Managed settings | `/etc/github-copilot/managed-settings.json` | `runtime.node`: `/etc/github-copilot/managed-settings.json` and `/etc/github-copilot/policy.d`, plus server-managed settings | both paths refuse; server-managed settings stay an accepted risk |
| Repository settings files | `.github/copilot/settings*.json` | `app.js`: `.github/copilot/settings.json` and `.github/copilot/settings.local.json` | the scan names both files |
| Signal handlers | SIGTERM, SIGINT, SIGHUP, SIGQUIT alike | `["SIGINT","SIGTERM","SIGHUP","SIGQUIT"]` at `app.js` 5173361 and 7311331 | none |
| Shell-exported markers | open question | no variable the shell tool exports to its commands found by string search; `COPILOT_AGENT_SESSION_ID` is read, not exported | `AGENT_MARKERS` unchanged; the AGENTS.md rule stays the guard |

**Rule changes at 1.0.91.** No rule of the spec changed, and none of D-C1 to D-C4. The V-pass changes constants and readings only: the effort flag's name, `SANDBOX_TOOLS`, `BUILTIN_SKILLS`, `BUILTIN_MCP`, the managed-settings paths, the scanned settings files, the sandbox warning texts, the sandbox-active report (now `tool.execution_complete.sandboxed`), and the probe's call (`session.shell.executeUserRequested`) with its per-command `sandboxed` check and the host-support row. Two consequences for the user are recorded as risks below: the snapshot's `overage_entitlement` may be absent from the reply, and a `PATH` whose `python3` lies under the account home fails the probe's skill rows.

**Facts measured after the first login (2026-10-06, task 7.4a).** The first `host-login copilot` wrote the token file and the approval stop, read version 1.0.91 and found every sandbox tool, but its status check ended untested: the home was "not clean: it holds config.json (unreadable), logs". Both entries were written by the status read's own headless server, after the clean check that let it start; the check that runs after the reads found them. Re-measured offline (`unshare -rn`, scratch `HOME`, `COPILOT_HOME` and `COPILOT_CACHE_HOME`, `COPILOT_AUTO_UPDATE=false`, no token, no model call):

- **What a Copilot child writes into `COPILOT_HOME`.** `copilot --version`, `--help`, `skill list --json` and `mcp list --json` write nothing there. The headless server (`--headless --stdio --no-auto-login --no-auto-update --log-level none`) writes two entries on start, before any request:
  - `config.json`, mode 0600, 131 bytes: two whole-line comments, `// User settings belong in settings.json.` and `// This file is managed automatically.` (`runtime.node` strings carry both), then a JSON object whose only key is `firstLaunchAt`, an ISO timestamp. `app.js` writes that key through `globalStateWriteKeyForContext` on every start that finds it unset (function `twn`). The harness parsed the file as strict JSON, so the comments made it "unreadable". The harness home's file after the first login matches: 131 bytes, mode 0600, each comment line present once (checked by whole-line match; the main session read its key list: `firstLaunchAt` only).
  - `logs/process-<ms>-<pid>.log`, mode 0600 in a 0700 directory, empty at `--log-level none` (the naming is `app.js`'s `process-${t}-${n}.log`).
- **Every other global-state key `app.js` writes is interactive.** `askedSetupTerminals`, `installedPlugins`, `sandboxCredentialProxyCaDeclined`, `sandboxOnboardingShown`, `autoFeedbackLastPromptedAt`, `appInstallNudgeResponded`, `recentModelIds` and `appTipShown` are written only from the terminal UI's handlers. `loggedInUsers` and `lastLoggedInUser` come from a client login, which a token-file home never runs, and they would carry a login name. `copilotTokens` is the plaintext store of a client login's tokens. `expAssignmentsCache` is the key of the experiment-assignment cache, which 1.0.91 keeps in a disposable cache file of its own (header "Disposable cache for experiment assignments, safe to delete."), not in `config.json`; the same holds for the Copilot-user and memory-enablement caches (`exp-cache`, `copilot-user-cache`, `memory-enablement-cache`). Where those cache files live (the cache home or `COPILOT_HOME`) is not derivable from strings. A read before the run (the status read, the listings, the probe, all authenticated since task 7.4b) that writes one into the home refuses that same run at the gate's last row, `clean_after_reads`, which `--preflight-only` prints for K3; one that a `-p` run writes refuses the next run (revised 2026-10-06, review follow-up of 7.4a).
- **`--log-dir <dir>` moves the process log.** With it, the headless server writes `process-<ms>-<pid>.log` into `<dir>` and creates no `logs/` in the home; `config.json` is still written. `--log-dir` is a global option: `copilot --log-dir <dir> skill list --json` is accepted, `copilot mcp list --json --log-dir <dir>` is a usage error, and neither listing writes a log anyway.
- **The credential flags are global options too** (measured offline after the review of task 7.4a, same setup, with a synthetic `github_pat_…` value). `copilot --no-auto-login --auth-token-env COPILOT_GITHUB_TOKEN --version`, `… skill list --json` and `… mcp list --json` all exit 0 with their usual output (the version line; the two bundled skills; `{"mcpServers": {}}`, offline and so signed out) and write nothing into `COPILOT_HOME`; `copilot mcp list --json --no-auto-login` is a usage error (exit 1), and so is an unknown option in global position, so the parser does not pass over what it is given there.
- **In server mode, `--no-auto-login` also drops `COPILOT_GITHUB_TOKEN`** (task 7.4b). The first login's read reported `auth_type` `-`, `host_ok` no, `token_based_billing` missing and no snapshot: exactly what `parse_status` makes of an `account.getCurrentAuth` result without `authInfo`, which `_status_lines` cannot tell from a failed read. The clean-home refusal came first in `status()` and hid the read's own refusal. Measured offline with a synthetic `github_pat_…` value in `COPILOT_GITHUB_TOKEN` (no network, so nothing validates; the `connect` and `account.getCurrentAuth` frames only):
  - the harness's flags (`--headless --stdio --no-auto-login --no-auto-update --log-level none`): `account.getCurrentAuth` → `{}`. The token is never read; without a token the reply is the same `{}`;
  - the same plus `--auth-token-env COPILOT_GITHUB_TOKEN`: `{"authErrors": ["Failed to validate SDK token: network fetch failed …"]}`. The named variable is read and validated;
  - without `--no-auto-login`: `{"authErrors": ["Failed to fetch PAT user login: network fetch failed …"]}`. The environment token is discovered with the other automatic sources.

  The help text still describes `--no-auto-login` as disabling "stored OAuth tokens and gh CLI" only, and the 1.0.67 reading (above) relied on that; at 1.0.91 the native `ProcessAuthHandle` treats the environment token as automatic detection too. The bundled SDK itself starts the server with `--auth-token-env COPILOT_SDK_AUTH_TOKEN` and `--no-auto-login` whenever it is given a token (`copilot-sdk/index.js`, `startCLIServer`), which is the pattern the harness now follows. Prompt mode builds the same `ProcessAuthHandle` from `authTokenEnv` and `autoLogin` (`app.js`), so a `-p` run under `--no-auto-login` alone would most likely run unauthenticated as well; that is not measured, because measuring it takes a `-p` start, and P2 confirms it. The auth type the explicit path reports is not measured either: `api.schema.json` offers `env` (`EnvAuthInfo`, "token sourced from an environment variable", with `envVar`) and `token` (`TokenAuthInfo`, "SDK-side token authentication"), and the offline reply carries no `authInfo`. K1 records which one.

## Goals / Non-Goals

**Goals:**

- Copilot is a third `Host` behind the one runner. `dev_run` gains no Copilot branch. Every Claude and Codex test passes unchanged, apart from the seams the tasks name.
- No environment, configuration or account state lets a Copilot run do any of these:
  - bill anything but included credits;
  - act with any credential but the harness PAT;
  - load anything of the operator's.

  Every way it could is refused before the run, or marked untested after it.
- Every check is a pure function over a stream, a status reply, a directory listing or an environment mapping. Each is tested offline on synthetic fixtures derived from the 1.0.91 package.
- No agent and no test ever needs a Copilot token. Live runs refuse until the token file exists, and the first model call waits for the user's explicit go.

**Non-Goals:**

- **Recorded streams and the K5–K7 outcomes.** They belong to `record-copilot-streams`, after the first approved run. The deny-path probe, formerly K6c, is no longer among them: it runs at $0 before every run, once the V-pass confirms a model-free shell call (Decision 13). Only if the V-pass finds none does it move to `record-copilot-streams`.
- **The auto-routed variant (D-C1(b)), and organization seats (D-C1(c))** beyond the guard's refusal of a seat that permits overage.
- **Per-scenario network policy for the sandboxed shell (D-C4(c)).** It is a recorded follow-up.
- **Out of scope as well:**
  - `smoke-copilot`, routing on Copilot, a Copilot judge and a Copilot install probe;
  - anything that feeds `report.py` or the matrix, and a registry role;
  - `--usage-output-file` as a telemetry source (P3);
  - VS Code's Copilot. Only the CLI is driven.

## Decisions

### 1. The user's decisions (2026-10-05) and the rejected alternatives

| Decision | Chosen | Rejected, and why |
|---|---|---|
| D-C1, plan | The account's free Copilot Pro for teachers: pinned models, about 1,500 credits a month | (b) Free or Student, auto-only: runs would be labelled "auto-routed", about 5–10 a month, and never comparable across runs. (c) An organization seat: the administrator controls overage. The guard still refuses any seat whose overage permission reads true. |
| D-C2, credential | (a) A fine-grained PAT carrying only "Copilot Requests", in `<state>/hosts/copilot.token` at 0600 beside the home, injected as `COPILOT_GITHUB_TOKEN`, with `--no-auto-login` on every child | (b) The same PAT exported as `THESIS_PROPOSAL_COPILOT_TOKEN`. The same relaxation applies, but the token sits in every process's environment, agents included. (c) An OAuth device login into the home. See below. |
| D-C3, version | (b) Upgrade to 1.0.91, pin that version exactly, and V-pass first | (a) Stay on 1.0.67. See below. (c) No pin: the event schema and the stdout filter change between versions. |
| D-C4, shell confinement | (b) Sandbox required: `--sandbox`, the pinned block with `allowBypass:false`, `allowDevToolAccess:false`, `auth.git/gh:false` and a deny list built by construction; a confinement probe before every run; refuse when unavailable or ignored, and refuse on Windows | (a) No sandbox: the model's shell could run `gh` against the operator's keyring, and read the token file and `~/.ssh`. (c) Network limits per scenario: their behaviour in `-p` mode is UNVERIFIED, so they are a recorded follow-up after K6. |
| Budget | No Copilot budget at all: the user deletes every budget | A $0 budget with "Stop usage" ticked. The CLI reads `overage_entitlement > 0` as "a budget exists", and the shape of a $0 budget is UNVERIFIED. Deleting leaves nothing to misread. |

Why D-C2(c), the OAuth device login, was rejected:

- it works on Linux only, because it needs the D-Bus cut-off plus `storeTokenPlaintext`;
- it carries the `repo` and `gist` scopes;
- it can only be revoked together with the operator's own CLI logins, and it counts toward GitHub's 10-token cap;
- it forfeits `--no-auto-login`;
- its logout goes through the Rust `authManagerLogout`, which may touch the operator's keyring entry.

Why D-C3(a), staying on 1.0.67, was rejected:

- it has no `claude-sonnet-5.5` or `opus-5.5`;
- it has no `--sandbox`, so D-C4(b) would be impossible;
- `--effort` would have to be refused;
- it still has the shell-secret debug-log leak that 1.0.87 fixed.

The cost of D-C3(b) is nil in schedule, because changes 1 to 3 gate this change's code anyway.

### 2. Spec shape

- **One ADDED and four MODIFIED requirements.**
  - ADDED "Copilot plan billing guard".
  - MODIFIED "Harness-owned host logins": the per-record credential kind is D-C2's relaxation.
  - MODIFIED "Dev-runner host adapters" and "Dev-runner cost and helper-agent telemetry".
  - MODIFIED "Isolated child environment".
- **Why "Isolated child environment" is modified.** Change 2 leaves a later client's child to "the same function … from that client's own description". The Copilot token is added *after* that function, by the caller, so that the builder stays pure and reads no credential. The requirement now says exactly that: one variable added for a token-file client, and none of it reaching any other child.
- **The D-C2 relaxation, line by line.** Change 3's "never … an access-token login" (`:241`), "the operator's own [environment], so that a browser can open" (`:243`) and the credential rules (`:310-314`) stay true for client-login records. Each is scoped to that kind, and the token-file kind gets its own exact limits:
  - one file read, kept beside the home rather than in it;
  - handed only to that client's children, under one variable;
  - only its prefix inspected, and otherwise used only to scrub the children's output;
  - never printed, logged or copied.
- **Not modified: "Inverted-hybrid runners", "Measured environments carry no eval definitions" and "Subscription text roles (dev runner)".**
  - Change 3 words them per host: "several host CLIs", "whichever host the run uses", "every non-Claude host".
  - Copilot's label scenario and staging scenario sit in "Dev-runner host adapters". The judge's token isolation sits in "Isolated child environment".
- **Not modified: "Isolated measurement environment".** Change 2 scopes it to Claude configurations.
- **Scenario names.** All 81 scenario names of the four base blocks are kept, checked name by name. Task 0.1 and task 9.3 repeat the check.

### 3. The `COPILOT` record and the credential kind

`HostLogin` gains two fields, with defaults that leave `CLAUDE` and `CODEX` unchanged:

- `credential: Literal["client-login", "token-file"] = "client-login"`;
- `token_env: str | None = None`.

| Field | Value |
|---|---|
| `name`, `binary`, `home_var` | `copilot`, `copilot`, `COPILOT_HOME` |
| `credential`, `token_env` | `token-file`, `COPILOT_GITHUB_TOKEN` |
| `login_argv`, `status_argv`, `logout_argv` | all `None`. `main` takes the token-file branch for login and logout, and status dispatches to `copilot_cli.read_status` |
| `admitted` | `CLAUDE.admitted` minus `CLAUDE_CODE_OAUTH_TOKEN` |
| `login_strip_prefixes`, `strip_suffixes` | `COPILOT_`, `GITHUB_`, `GH_`, `CAPI_`, `OTEL_`, `OPENAI_`, `ANTHROPIC_`, `AZURE_OPENAI_`; `_TOKEN`, `_API_KEY`. Plus the exact names `BASH_ENV` and `SSH_AUTH_SOCK` |
| `seed` | `settings.json` = `pinned_settings(home, account_home)`, and an empty `gh/` |
| `forbidden` | everything outside the allow-list (Decision 6) |
| `failure` | `session.error` with `errorType` authentication or authorization, which maps to the PAT remedy |
| `stop_signal`, `outside_tempdir` | default (SIGTERM), False. 1.0.67 handles SIGTERM, SIGINT, SIGHUP and SIGQUIT alike, and the V-pass re-checks this at the pin |
| `child_vars(home)` | change 3's signature, unchanged: the home-derived and constant variables of Decision 5. The scratch variables come from `copilot_cli.run_env`, as Codex's do |

- **`account_home`.** It comes from the password database (`pwd.getpwuid(os.getuid()).pw_dir`), never from `$HOME`. The children's `HOME` is a scratch directory, so a `~` in `deniedPaths` would deny a path under scratch and leave the operator's real home readable. `pinned_settings` writes absolute paths for that reason. The preflight recomputes it and compares the result with `settings.json` for equality.
- **`pinned_settings`** is the brief's object plus the sandbox block:

  ```json
  {"autoUpdate": false, "continueOnAutoMode": false, "customAgents": {"defaultLocalOnly": true},
   "disableAllHooks": true, "experimental": false, "ide": {"autoConnect": false},
   "memory": false, "storeTokenPlaintext": true,
   "sandbox": {"enabled": true, "allowBypass": false, "allowDevToolAccess": false,
               "auth": {"git": false, "gh": false},
               "userPolicy": {"filesystem": {"deniedPaths": DENY}}}}
  ```

  - **`DENY` is built by construction**, not picked entry by entry: `<acct>` (the whole account home), `/run/user/<uid>` (the session bus, and the `gcr`, `ssh-agent` and `gpg-agent` sockets a model could reach by setting `DBUS_SESSION_BUS_ADDRESS` or `SSH_AUTH_SOCK` itself), `<state>` when the state root lies outside `<acct>`, and the token file. A hand-picked list missed `~/.git-credentials`, `~/.netrc`, the other harness homes, `~/.claude`, `~/.codex` and the repository's `.env`; the whole home covers them and any later one. The workspace and the scratch `HOME` lie in the run's scratch directory, outside all of these; the parent-folder scan refuses a workspace under `<acct>` (Decision 7).
  - **The key path is UNVERIFIED.** The block above follows the 1.0.67 package, `sandbox.userPolicy.filesystem.deniedPaths`, against the docs' `sandbox.userPolicy.deniedPaths` (Context). Task 1.2 derives the exact path from the 1.0.91 `runtime.node` strings and settings schema, and the block follows the package. A missing unknown-key warning on stderr is not proof that a key is read. K6, at $0 before P2, reads the effective policy (Decision 13).
  - **Whether the client's own tools need anything under `<acct>`** inside the sandbox, the package cache under `<state>/cache/copilot` above all (the bundled `rg`), is UNVERIFIED. K6 runs `python3` and one skill script under the pinned policy at $0, and P2's tool results show whether `grep` and `glob` still work. If one of them fails, the deny list is revised through `openspec-update-change`, never widened in code alone.
  - K3 confirms that the CLI accepts every key with no unknown-key warning. A key it rejects is revised through `openspec-update-change`.
- **`check_location`** also refuses `~/.copilot`, an inherited `$COPILOT_HOME` and `~/.config/github-copilot` for every record, extending change 2's list of client directories.
- **The login note.** `NOTES["copilot"] = ("Your own Copilot login is not affected", None, True)`. A token-file client has no revocation check, so its caveat slot is empty and its pass flag is constant.
- **Imports.** `copilot_cli` imports `host_login` at module level. `host_login.main` imports `copilot_cli` inside the token-file branches only, so there is no import cycle.

### 4. The token file

- **Where it lives.** `token_path(home) = home.parent / "copilot.token"`, that is `<state>/hosts/copilot.token`: a 0600 sibling of the home, never inside it. Since 1.0.89 the sandboxed shell is granted the session files and logs under `COPILOT_HOME`, and how that grant interacts with a deny entry inside the same home is unknown. A file outside the home is covered by no grant on the home, and it stays on the deny list.
- **`host-login copilot`** runs these steps in order:
  1. the terminal check and the agent-marker check, unchanged;
  2. `check_location`;
  3. seed;
  4. `run_lock`;
  5. on an existing token file, delete it; on `--reset`, delete it, wipe the marked home and reseed it;
  6. `getpass.getpass("Fine-grained token (Copilot Requests only): ")`;
  7. `token_problem(prefix)` refuses `ghp_` by name, and any prefix other than `github_pat_`. Only the first 11 characters are compared, and the message never echoes them;
  8. write the file with `os.open(path, O_WRONLY|O_CREAT|O_EXCL, 0o600)`;
  9. `record_stop(home, "approval", "first run not yet approved")` (Decision 9);
  10. `read_status`, then the preflight with the approval stop set aside. Exit 0 when ready, otherwise 3. The message says that the first run waits for `uv run poe host-login copilot --clear-stop`.
- **`host-login copilot --clear-stop`** takes the same speed bumps and the lock. It removes the `stop` key from `quota.json`, whatever its kind, and touches nothing else (Decision 9). Clearing the approval stop is the user's go for the next model call, so the go is given at a terminal an agent does not drive, not only in chat.
- **`host-logout copilot`** takes the lock, unlinks the token file, and prints "Revoke the token at github.com/settings/personal-access-tokens." It runs no client logout and touches nothing else.
- **During a run**, `token_env(record, home) -> dict[str, str]` reads the file, strips one trailing newline and re-checks the prefix. `copilot_cli.spawn` merges the result into the environment after `allowlisted_env` and `run_env`, and then calls `assert_copilot_env`. The value never enters an argv, a log line, a `RunnerFailure` message or the saved events.
- **Scrubbing.** The CLI's own redaction is not the only guard: it failed before (shell secrets in debug logs until 1.0.87, `changelog.md:116`), and the model may still read the value from the live process. The pure `scrub(text, token) -> (text, hit)` replaces every occurrence with `[copilot-token]`. `copilot_cli` applies it to the child's stderr, every `RunnerFailure` text, the stdout events and the reduced records before they are saved, and to the judge's input. A hit makes the run untested for isolation and records an isolation stop (Decision 9). `--secret-env-vars=COPILOT_GITHUB_TOKEN` stays as the CLI-side backstop that strips the variable from the model's shell environment and redacts the value from the output.
- **Where it never lives.** Not in the repository's `.env`, which dev tasks deliberately do not load. And never under `COPILOT_GITHUB_TOKEN`, `GH_TOKEN` or `GITHUB_TOKEN` in any file a shell loads, because those names would silently replace the operator's own Copilot and `gh` logins. `harness/README.md` says so.

### 5. The Copilot child environment

- **Admitted.** The shared machine variables (`PATH`, locale, `TZ`, `SHELL`, proxy and certificate-trust variables, and the Windows basics).
- **`COPILOT.child_vars(home)`**, change 3's signature, holds only what the home determines and constants:
  - `TERM=dumb` and `NO_COLOR=1`;
  - `DBUS_SESSION_BUS_ADDRESS=disabled:`. It is set, not dropped, because godbus falls back to the fixed bus path when the variable is empty;
  - `COPILOT_HOME=<home>`, `COPILOT_CACHE_HOME=<state>/cache/copilot` with `<state> = home.parent.parent`, and `COPILOT_AUTO_UPDATE=false`. The cache is persistent, so that the 140 MB package is not unpacked into scratch on every run. It lies outside the home, so that the home's allow-list stays small;
  - `GH_CONFIG_DIR=<home>/gh`, an empty directory.

  `allowlisted_env` and the assertion's exemption read it exactly as they read `CODEX.child_vars(home)`, so no record and neither function changes signature.
- **`copilot_cli.run_env(env, scratch)`**, like `codex_cli.run_env`, then sets `HOME` and `XDG_{CONFIG,CACHE,DATA,STATE}_HOME` under the per-run or per-call scratch directory, and `XDG_RUNTIME_DIR=<scratch>/run`.
- **Added by the caller:** `COPILOT_GITHUB_TOKEN` (Decision 4), except for `host-status copilot --no-token`, whose read gets the same environment without it.
- **`assert_copilot_env(env)`** raises `BillingEnvError`, naming the variable and never its value, in either of these cases:
  - a key matches the strip families and is neither in `COPILOT.child_vars` nor `token_env`;
  - a token-shaped variable other than `token_env` is present. A name is token-shaped when it ends in `_TOKEN` or `_API_KEY`. A value is token-shaped when it starts with `github_pat_`, `ghp_`, `gho_`, `ghu_`, `ghs_` or `ghr_`.

  `spawn` is the single function that starts any Copilot child: the run, `--version`, `--headless` (the status read and the confinement probe), `skill list` and `mcp list`. Every one of them carries `--no-auto-login`, and `--auth-token-env COPILOT_GITHUB_TOKEN` exactly when it carries the token: the run and the headless server among their flags, the three short commands before their subcommand (`login_flags`, where 1.0.91 parses them as global options; revised 2026-10-06, review follow-up of task 7.4a, when the short commands still ran with the token readable and automatic login on).
- **L0 pins** mirror change 3's Decision 8:
  - a builder monkeypatched to leak `GH_TOKEN`, then `COPILOT_PROVIDER_BASE_URL`, then `XYZ=github_pat_…`, leads to no `Popen`;
  - `run_env` patched to add `GITHUB_TOKEN` after the builder still fires the assertion;
  - an environment holding only the record's names plus the token passes.

### 6. Status read, preflight and the clean-home allow-list

- **`read_status(home, env, *, models=False)`.**
  - It spawns `copilot --headless --stdio --no-auto-login --no-auto-update --log-level none [--auth-token-env COPILOT_GITHUB_TOKEN] --log-dir <call scratch>/logs` under the lock. The confinement probe's server takes the same flags with the run's scratch. The log therefore never lands in the home and is deleted with the scratch directory (revised 2026-10-06, task 7.4a). `--auth-token-env` is passed exactly when the child carries the token, so the `--no-token` read names no variable (revised 2026-10-06, task 7.4b: without it, `--no-auto-login` leaves the token unread at 1.0.91 and the read reports no login).
  - It speaks Content-Length-framed JSON-RPC.
  - It calls `account.getCurrentAuth`, and `models.list` when asked or before a run.
  - It stops at `STATUS_TIMEOUT_S = 20` through `stop_child`.
  - The method names and the handshake are re-derived by the V-pass and confirmed by K1 and K2.
- **`parse_status(reply) -> Status`** is pure. It keeps exactly the values the spec lists, and the raw reply is dropped at the parse. A runner-bug refusal names the method and the exception class only.
- **`choose_snapshot(user)`** picks `chat` when `access_type_sku == "free_limited_copilot"`, and `premium_interactions` otherwise.
- **`status_problem(status, model, effort) -> LoginProblem | None`** is a table of rows, so complexity stays at or below 12:
  - auth: no login, auth errors, a type outside `TOKEN_AUTH_TYPES = ("env", "token")`, a host other than `https://github.com`. Both types are what the client may report for the token it read from the variable `--auth-token-env` names (`EnvAuthInfo` or `TokenAuthInfo`). The 1.0.91 schema has a third variant typed `token`, `SettableTokenAuthInfo`, set only through the RPC `session.gitHubAuth.setCredentials`, whose Copilot user the runtime trusts as given; the harness is the only client of its headless servers and never sends that call. With `--no-auto-login` and the environment check of Decision 5, no other source produces either type. K1 records which one 1.0.91 reports, and the set is narrowed to it in a reviewed change (task 7.4b): narrowed to `env`, `Status` also keeps `EnvAuthInfo.envVar`, which `parse_status` drops today, and the guard requires it to equal `COPILOT_GITHUB_TOKEN`; narrowed to `token`, the record states that only the harness's own RPC calls could produce it;
  - billing: the five rows of the guard;
  - model: the model is not listed or its policy is not enabled, or the effort is not in `supportedReasoningEfforts`.
- **Preflight order.** Nothing spawns before the location is known to be safe: a refused state-directory override must find nothing created, and `copilot --version` already unpacks the package into `COPILOT_CACHE_HOME`, which lies under the state root. Then cheap and local checks, then everything under one lock hold:
  1. the location (`check_location`);
  2. the marker and mode;
  3. `check_copilot_home`;
  4. the token file and its prefix;
  5. a recorded stop of any kind. It reads only `quota.json` and starts nothing, so a stop refuses before the first Copilot process, as the spec requires. `--preflight-only` prints it and goes on;
  6. `copilot --no-auto-login --auth-token-env COPILOT_GITHUB_TOKEN --version` against `COPILOT_PINNED_VERSION = (1, 0, 91)`, the first `spawn`, carrying the token like every Copilot child;
  7. `/etc/github-copilot/managed-settings.json` and `/etc/github-copilot/policy.d` (1.0.91);
  8. the sandbox tools (Decision 13);
  9. the parent-folder scan (Decision 7);
  10. under the lock: the recorded stop and the token file read again, then `read_status`, then `status_problem`, then the rosters (Decision 7), then the confinement probe (Decision 13), then `check_copilot_home` once more, on the home as those reads left it (`clean_after_reads`). That last row starts nothing and comes whatever ended the reads before it, so `--preflight-only` always prints it; a run stops at it before the `-p` child (revised 2026-10-06, review follow-up of task 7.4a: the reads run authenticated since task 7.4b, and where the client's caches land is open). After those come the run and the read after it. The second reading exists because a run waits up to `LOCK_WAIT_S` (30 s) for the lock: in that window another run can record a billing or isolation stop, and a login, which holds the lock while it prompts, replaces the token and records the approval stop. Read only before the lock, the stop would be missed and the old token used.

  *Revised 2026-10-06 (review follow-up).* The first implementation ran the version check third, then fifth after the token; with the stop sixth, a recorded stop still started `copilot --version` before refusing, and the L0 tests that claimed "no `Popen`" stubbed the version read away. The stop now comes before the version, and those tests run against the fake client with a recording `Popen`.
- **`check_copilot_home(home, account_home)`** is an allow-list, because `config.json` overrides `settings.json`. It checks three things:
  - `settings.json` must equal `pinned_settings`;
  - `config.json` is read as the client writes it, failing closed:
    - the raw text, comments included, must hold no GitHub token prefix (`github_pat_`, `ghp_`, `gho_`, `ghu_`, `ghs_`, `ghr_`), so a token in a comment line is refused like one in a value (`a token-shaped string`);
    - the only comment allowed is the client's own header, `COPILOT_CONFIG_HEADER`: exactly the two lines `// User settings belong in settings.json.` and `// This file is managed automatically.`, at the top. It is dropped, and any other whole-line `//` comment, in any number or position, is refused (`unexpected comment`); a file without the header is read as plain JSON;
    - the rest must parse as a JSON object; a nesting too deep to parse is `unreadable`, like any other parse failure, never a traceback;
    - every top-level key must lie in `MANAGED_STATE_KEYS = {firstLaunchAt}`, the one key a token-mode home's children write at 1.0.91 (facts measured after the first login), and its value must be an ISO timestamp string (`datetime.fromisoformat`), which is all the client writes there. The parsed key is checked for a token prefix once more, for one written with JSON escapes, and such a key is not named at all.

    A value is never echoed: the offender names the key, or the state of the file (`unreadable`, `not an object`, `unexpected comment`, `a token-shaped string`). K3 confirms the set for a `-p` run; widening it is a reviewed change, and a key of another shape needs a value check of its own;
  - the only entries allowed are `settings.json`, `config.json`, `session-store.db*`, an empty `session-state/`, an empty `gh/`, `.harness-home`, `.harness-run.lock` and `quota.json`. The token file lives beside the home (Decision 4), so it is not on the list. `logs/` is allowed only while it is a real directory holding nothing but empty process logs (`process-<ms>-<pid>.log`, regular files of size 0, sized and never read): every child that writes a process log is pointed at scratch with `--log-dir` (the run since Decision 8, the status read and the probe since task 7.4a), so a log with content, another entry, a subdirectory or a link there means a child ran without it, and the log may hold what the harness must never keep.

  It names every offending key path or entry, never a value.

  *Revised 2026-10-06 (task 7.4a).* The first version read `config.json` as strict JSON and started `MANAGED_STATE_KEYS` from the operator's own home (`expAssignmentsCache`, `firstLaunchAt`, `lastLoggedInUser`, `loggedInUsers`), and the status read and probe wrote their log into `<home>/logs`. The first login therefore refused its own home after its status read. The client's comment header is now accepted, the set narrowed to the key token mode writes (the two login keys would carry a login name, and the cache key lives in a file of its own), a token-shaped value refused, and the log redirected rather than pruned: a prune leaves the log in the home while the child runs and for good when the harness dies before it, whereas the scratch directory is deleted with the call, and pruning would also hide a child that ignored the redirection, which the clean check now names.

  *Revised again 2026-10-06 (review follow-up of task 7.4a).* The first fix dropped every whole-line `//` comment before any check, so a token in a comment line passed, and comments were accepted in any number and position; `firstLaunchAt` accepted any JSON value, and a deeply nested file raised `RecursionError` instead of reading `unreadable`. The raw-text token check, the exact header, the timestamp value and the parse-failure mapping above close those. The same review moved the short commands behind the credential flags (Decision 5) and added the `clean_after_reads` row (preflight order, step 10).

  *Revised a third time 2026-10-06 (live check of task 7.4).* Until then `logs/` was refused outright, so the first login's home, which holds the one empty log its status read wrote before the redirection, needed a manual removal or a `--reset` before any live check. An empty log holds nothing the harness must keep out, so it is accepted, and the home the first login left reads clean as it is. What that gives up: a headless child at log level none that ignored `--log-dir` would leave an empty log unnoticed, which costs nothing because it wrote nothing, and the L0 tests pin `--log-dir` on every child that logs; a log with content still refuses the home.
- **The status command's `clean` line** reports the home as the reads left it — the same offender list the refusal names — not the state before them.
- **The status command's `auth_type` line** tells the cases apart (task 7.4b): `unknown` when no read ran, `unavailable` when the read failed, `none` when it answered without a login, and the reported type otherwise. The first login's `-` stood for both of the middle two.
- **The status command** prints exactly the spec's Copilot keys:
  - `home`, `marker`, `token_present`, `auth_type` and `host_ok`;
  - `plan_class`, `token_based_billing`, `overage_permitted`, `overage_count`, `overage_entitlement`, `remaining_pct` and `reset_date`;
  - `stop` (none, or its kind and cause), `clean` (or the offending names), `cli_version`/`pinned_version`, `sandbox` (each sandbox tool found or missing) and `runs_use`.

  Two options add a read each. `--models` adds one row per model: id, policy and efforts. `--no-token` repeats the read without the token and prints `logged_in: no` when the CLI finds no other credential, which is K1's isolation proof.

*Rejected for the status read:*

- `getQuota`'s mapped values. Its `EZ` coercion fails open.
- The harness calling `/copilot_internal/user` itself with the token. That would be a second use of the credential, and it is undocumented.
- The REST billing usage API. It needs a classic PAT, reports only what was consumed, and excludes teacher plans.
- `assistant.usage` quota snapshots. They reach neither stdout nor disk.

### 7. Workspace, staging, the parent-folder scan and the rosters

- **The workspace.** `ws = tempfile.mkdtemp(dir=<run scratch>)`, with the scratch `HOME` as a sibling. The workspace is not a git repo, and it lies outside the real home and the repository. `stage(..., skill_dir=(".agents", "skills"))` is change 3's, unchanged; it already leaves `evals/` out.
- **Why `.agents/skills`.**
  - `install.py --scope folder` writes `./.agents/skills` and `./.claude/skills`. Copilot lists the `.agents` copy as `project` and hides the `.claude` copy, so staging `.agents/skills` alone reproduces what the CLI sees in a student's folder install.
  - The "all projects" layout, `~/.agents/skills`, cannot be reproduced at all. With `COPILOT_HOME` set, the CLI never reads it.
- *Rejected staging options:*
  - staging both folders: it adds a scan exception and changes nothing observable;
  - `$COPILOT_HOME/skills`, `COPILOT_SKILLS_DIRS`, `--add-dir` and `--plugin-dir`: none of them is a student layout, and the first pollutes the login home;
  - `git init` to stop the parent walk: it adds git context to the prompt, and it departs from the Codex workspace and from a typical student folder.
- **`scan_parents(ws, exists)`** is pure over an injected `exists` predicate. It walks from `ws` to `/` and reports any of these, outside the staged skill directory:
  - `.agents/skills`, `.github/skills` and `.claude/skills`;
  - `AGENTS.md`, `CLAUDE.md`, `.claude/CLAUDE.md` and `GEMINI.md`;
  - `.github/copilot-instructions.md` and `.github/instructions/`;
  - `.github/agents/`, `.claude/agents/` and `.claude/rules/`;
  - `.github/hooks/`, `.github/copilot/settings*.json` and `.github/allowed_models.txt`;
  - `.claude/settings.json`, `.mcp.json`, `.github/mcp.json` and `.github/extensions/`.

  It also reports a `ws` that lies under the real home or the repository.
- **Rosters.** `copilot skill list --json` and `copilot mcp list --json` run through `spawn`, in the run's environment and with `cwd=ws`, under the lock.
  - `roster_problem(skills, mcps, staged)` is pure. Skills must equal the staged names plus a subset of `BUILTIN_SKILLS = ("customize-cloud-agent", "github-pr-media")` (1.0.91, measured), each staged name with source `project`. MCP servers must be a subset of `BUILTIN_MCP = ("github-mcp-server", "githubiq")` with source `builtin`.
  - Both sets are pinned per CLI version by the V-pass.
- **`--preflight-only`** runs every step of Decision 6's order, plus staging, the rosters and the confinement probe, prints each result, deletes the workspace and the probe's session folder, and exits 0 or 3. A recorded stop is printed and does not decide the exit status, so K3 runs while the approval stop still holds. It starts no `-p` child. K3 and K6 use it.
  - **Which refusals end it.** A refused stop, sandbox-tools, status, model or roster row is printed and the option goes on (`copilot_cli.REPORTED`): the later reads are model-free and need only the token and the workspace, so K6 can read the probe's rows even while, say, the guard refuses a reply without `overage_entitlement`. A refused location, home, clean state, token, version, managed settings file or parent-folder scan ends it, because a later start would then be unsafe: a child under a refused location or in an unclean home, without the token, speaking another version's server interface, under a managed policy, or beside parent-folder files such as hooks. A run stops at its first refusal of any row.
  - **Options it would ignore** (`--rejudge`, which would make a judge call, `--judge` and `--keep`) are usage errors.

### 8. The command

```
copilot -p <prompt> --output-format json --stream off --no-color
  --session-id=<uuid4>                       # harness-chosen; session-state/<uuid> must not exist
  --model <id> [--reasoning-effort <level>]  # effort only when listed for the model (`--effort` at 1.0.67)
  --allow-all-tools
  --available-tools=bash,read_bash,write_bash,stop_bash,list_bash,view,create,edit,apply_patch,glob,grep,rg,skill,report_intent,update_todo
      [+task,read_agent,list_agents,write_agent   scenario declares helpers]
      [+web_fetch                                  needs_network(scenario)]
  --deny-tool=memory --deny-tool=github-mcp-server --deny-tool='shell(gh:*)' --deny-tool='shell(git push)'
      [--allow-url=<host> per host in url_hosts(scenario); never --allow-all-urls]
  --disable-builtin-mcps --no-custom-instructions --no-ask-user --no-remote --no-remote-export
  --no-auto-login --auth-token-env COPILOT_GITHUB_TOKEN
  --no-auto-update --no-bash-env --disallow-temp-dir --secret-env-vars=COPILOT_GITHUB_TOKEN
  --sandbox
  --log-level warning --log-dir <scratch>/logs --max-ai-credits <N>
```

- **The credential flags** (revised 2026-10-06, task 7.4b). `--no-auto-login` keeps every automatic source out; at 1.0.91 that includes the environment token, so `--auth-token-env COPILOT_GITHUB_TOKEN` names the one variable the client may read. The status read before the run uses the same pair, so the $0 read validates the credential exactly as the run will use it: a token the explicit path rejects is refused before any `-p` child starts.
- **Visibility, approval and denial.** `--available-tools` decides what the model sees. `--allow-all-tools` approves without prompting, which `-p` needs. `--deny-tool` always wins over approval.
- **`needs_network`** is change 3's predicate, so both hosts treat the same scenarios as network scenarios.
- **`url_hosts(scenario)`** is pure.
  - A served fixture gets `127.0.0.1`, which is where `claude_runner` binds its fixture server.
  - The import, lit-search and reverse skills map, through a pinned `SKILL_HOSTS` table, to the API hosts their scripts contact.
  - An L0 test extracts every `https?://host` from those skills' `scripts/` and asserts that each one appears in the table. A new host then fails a test rather than a run.
  - Some hosts in those scripts are reached by no request. They sit in a second table, `NOT_CONTACTED`, each with its reason: `github.com` (the repository named in the User-Agent string), `openalex.org` (the API-key help text), `arxiv.org` (an XML namespace of the arXiv feed) and `www.w3.org` (the Atom namespace). A host enters that table only with a reason showing that no request reaches it; any other new host goes into `SKILL_HOSTS`, so the change that adds it is reviewed as a URL approval.
- **`auto` is refused** as a usage error. Under D-C1(a) the served model could never equal the request, so every run would be untested.
- **Flag provenance.**
  - Every flag is in the 1.0.67 help, except three: the hidden `--no-auto-login`, `--sandbox`, which arrived in 1.0.70, and the hidden `--auth-token-env` ("Read auth token from specified environment variable (for SDK use)", `cli-native.node`, 1.0.91), which the bundled SDK passes itself.
  - The 1.0.85 parser rewrite moved argument parsing into Rust, so the V-pass re-checks every flag at 1.0.91.
  - The pinned `command()` test fails on any drift.
- **Never passed:** `--add-dir`, `--plugin-dir`, `--allow-all-paths`, `--allow-all-urls`, `--enable-memory`, `--share*`, `--agent`, `--resume` and `--continue`.

### 9. The run, the reduction and the stops

`copilot_cli.run_copilot(...)`:

1. Take the lock, read the recorded stop and the token file again (Decision 6, step 10), run the preflight, and keep `before = read_status(...)`.
2. Start the child through `spawn`, with `Popen`, `pass_fds=(lock_fd,)` and the parent-death `preexec_fn`, under the wall-clock timeout. On timeout, `stop_child(proc, SIGTERM)`, then kill after `TERM_GRACE_S`.
3. Capture stdout and stderr.
4. Read `<home>/session-state/<uuid>/events.jsonl`. Its path is known even after a timeout. Reduce it, and append the result as `copilot.*` records. When a `result` line exists, cross-check its `sessionId`. Pass stdout, stderr and the records through `scrub` before anything is saved or reported (Decision 4).
5. Keep `after = read_status(...)`.
6. Delete `session-state/<uuid>/` and the scratch logs, which are never saved.
7. Release the lock.

Steps 3 to 6 fail closed. A read after the run that raises (a broken pipe while answering the server, a scratch home that cannot be made) counts as unavailable, which records a billing stop. Anything else that raises after the child started stops the child if it still runs, scrubs the workspace, records a billing stop ("the checks after the run did not complete") and lets the exception surface as a runner failure. Without this, an exception there would leave no stop, an unscrubbed workspace that `--keep` keeps, and no saved events.

Then:

- **`reduce_session(lines)`** keeps:
  - `session.start.copilotVersion`;
  - `skill.invoked{name, path, source, trigger}`;
  - `session.shutdown{shutdownType, errorReason, totalPremiumRequests, totalNanoAiu, modelMetrics}`;
  - `session.model_change{cause, previousModel, newModel}`;
  - the type alone of each `hook.*`;
  - the sandbox-active and sandbox-ignored events, and the effort-unapplied event, each as the V-pass names them.

  It drops `system.message` and everything else. The reason: the session file carries prompts, system text and unknown fields, and a kept workspace should hold only what the readers use, as change 3's Decision 10 argues for Codex.
- **`billing_after(before, after, view, cap) -> (problem, stop)`** is pure. `after` is `None` when the read after the run is unavailable. The `stop` flag is set for these cases:
  - the overage grew;
  - `after is None`, because overage growth cannot then be ruled out;
  - a `session.shutdown` whose `totalNanoAiu` is missing or not a number. Consumption that cannot be read is never read as zero: `credits_used` returns None, the summary's `ai_credits` and `notional_usd` are null, and the run is untested;
  - consumption above twice the cap;
  - zero nano-AIU with tokens reported;
  - no `session.shutdown`. The problem is then a runner failure, not untested (Decision 11);
  - `session_limits` or `ai_credit_soft_cap_exhausted`. The cause names the run's cap and, when the stream carries `session_limits_exhausted.requested`, the credits used and allowed, so the stop names the cap as the spec's scenario asks.

  The untested results of the guard and of `failure_reason` (a rejected token, a quota or rate limit, a reached cap) all read in the one refusal template, the login note included.
- **Stops persist across invocations.** `poe dev` takes one scenario per invocation (`claude_runner.py:1276`), so "skip the remaining scenarios" can only mean "refuse later invocations". `record_stop(home, kind, cause)` writes `{"stop": {"kind", "cause", "at"}}` into `quota.json` with `os.replace`; a second cause found by the same run is appended to `cause`. The kinds:
  - `billing`, from `billing_after`;
  - `isolation`, from the sandbox ignored or not reported active, and from a `scrub` hit (Decision 4);
  - `approval`, from every `host-login copilot` that writes a token file (Decision 4).

  The preflight refuses while that entry exists, and only `host-login copilot --clear-stop` or `--reset` removes it; a reset records a new approval stop. A `quota.json` that exists but cannot be read, that is not a JSON object, or whose `stop` is not a non-empty object reads as a billing stop ("the stop record in quota.json cannot be read"), never as no stop; a new status snapshot keeps it as that stop, and `--clear-stop` removes it.
  - *Rejected:* a stop that lasts within one invocation only, which would be vacuous; clearing through `host-status`, which agents may run; and no stop at all, because the next preflight catches drawn overage but not a soft-cap overshoot, broken accounting, or a sandbox that silently stopped confining.
  - *Rejected for the go:* a go given only in chat. At K3 an agent runs the exact live command with `--preflight-only` added, so one dropped flag would spend credits without it. The approval stop makes the go something the user does at a terminal.

### 10. Readers, canonical tool calls and `RunView`

- **`copilot_tool_calls(events)`** is a dictionary dispatch over `tool.execution_start`, paired with `tool.execution_complete` by `toolCallId`. The mapping table:

  | Copilot | Canonical |
  |---|---|
  | `bash`, `read_bash`, `write_bash`, `stop_bash`, `list_bash` | `Bash` |
  | `edit`, `create`, `apply_patch`, `str_replace`, `insert` | `Edit` |
  | `view` | `Read`, plus `skill_file_read` for `…/proposal-*/SKILL.md` |
  | `glob` / `grep`, `rg` | `Glob` / `Grep` |
  | `skill` | `Skill {"skill": arguments.skill}`, without any `<plugin>:` prefix; `success:false` counts as an attempt |
  | `task` | `Agent {"prompt"}`, cross-checked with `subagent.started` |
  | `web_fetch` / `web_search` | `WebFetch` / `WebSearch` |
  | `mcpServerName` and `mcpToolName` | `mcp__<server>__<tool>` |
  | `report_intent`, `update_todo`, `task_complete`, `store_memory`, `ask_user`, `sql`, `fetch_copilot_cli_documentation` | internal |

  Any other name is an `unknown_tool` finding. The `task` cross-check (`helper_after`) pairs every `task` start with a `subagent.started` by `toolCallId`, both ways: a task call that started no subagent would let the verifier verdict count a spawn that never ran, and a subagent no task call shows would hide a helper from the single-context verdict. Either is untested for a precondition.
- **`routing.tool_calls`** appends `copilot_tool_calls(events)` after the Claude and Codex shapes. The event types never collide, so these all work unchanged: `HELPER_TOOLS`, `verdict_supervise_verifier`, `verdict_single_context` and `route_from_events`, which needs `payload["skill"]` (`routing.py:247-252`).
- **`copilot_read(events, args) -> RunView`:**
  - `final_text` is the last top-level `assistant.message.content`;
  - `model_requested` is `args.model`;
  - `model` is the set of top-level `assistant.message.model` values together with the `modelMetrics` keys: one name, several names, or `"unreported"`. That these name the served model is UNVERIFIED until K5;
  - `cli_version` comes from `copilot.session_start`, cross-checked with the preflight (`version_after`): a session that reports another version than the pinned one the preflight checked, recorded in the runner's own record, is untested for a precondition. A session record without a version is left to the other findings.
- **Telemetry:**
  - `cost_usd = None`;
  - `ai_credits = totalNanoAiu / 1e9`;
  - `notional_usd = ai_credits × 0.01`, with `notional_basis = "copilot credits, not billed"`;
  - tokens from `modelMetrics.*.usage`, the reasoning count included;
  - `premium_requests`;
  - `cap_credits`;
  - `overage_before` and `overage_after`, and `remaining_before` and `remaining_after`;
  - `ignored_env`.
- **Effort.** Requested only when the listing offers it for the model. Until the V-pass and K5 pin the unapplied event, `effort_served` reads "requested, not verified". `session.start.reasoningEffort` and `selectedModel` echo the creation options (byte 3318314) and are never used as evidence.
- **Isolation findings** come from `isolation_after(view, staged, ws)`:
  - no `session.skills_loaded`, or one that differs from the roster. Until K5 says otherwise, absence counts;
  - a `skill.invoked` whose source is outside `{project, builtin}`, or whose path lies outside `ws/.agents/skills`;
  - any `mcpServerName`, or a connected server in `mcp_servers_loaded`. That check is presence-only;
  - any `hook.*`.

### 11. Exit mapping

| Finding | Exit, untested reason |
|---|---|
| A preflight row: version, home, token, auth, the guard's rows, model, managed settings, scan, roster, sandbox tools, confinement probe, stop, lock | 3: subscription, isolation or precondition, per the spec's list. A stop maps by kind: billing to subscription, isolation to isolation, approval to precondition |
| `session.error`, authentication or authorization | 3, subscription, with the PAT remedy and the not-affected note |
| `errorType` quota or rate_limit | 3, subscription: "limit reached, not a result" |
| `session_limits` or `ai_credit_soft_cap_exhausted`; overage grew; the read after the run unavailable; no readable `totalNanoAiu`; more than twice the cap; zero nano-AIU with tokens | 3, subscription, with a billing stop recorded |
| An isolation finding (Decision 10) | 3, isolation |
| The sandbox ignored or not reported active; a `scrub` hit | 3, isolation, with an isolation stop recorded |
| Served model differs (outside a helper scenario's usage); `model_change.cause == "rate_limit_auto_switch"`; effort reported unapplied; an unknown tool; a `task` call and `subagent.started` that do not pair up; a session CLI version other than the pinned one | 3, precondition |
| A non-zero exit with no classifiable event, no `result` line, or a timeout | 4 |
| No `session.shutdown` | 4, with a billing stop recorded |
| A step after the child's start that raises | 4 ("runner crashed"), with the workspace scrubbed and a billing stop recorded |
| A verdict | 0 or 1 |

The process exit code is never trusted on its own.

### 12. The judge

- Change 3's Decision 13 applies unchanged. `completed_run` calls `judge.backend.isolation(stack)` after `run_copilot` has returned, so the Copilot lock is released and the child has exited.
- The L0 pin is extended: the recorded judge environment and its login check carry neither `COPILOT_GITHUB_TOKEN` nor any value of the synthetic token, nor the Copilot home path. The judge's input is the scrubbed run (Decision 4), so a fake run that prints the synthetic token reaches the judge without it.
- The Claude sonnet-5.5 dev judge's load lands on Max, not on Copilot.

### 13. The sandbox (D-C4(b))

- **Why confinement is checked before the run.** An unavailable sandbox only warns "ignored" and runs the shell unconfined (Context), and a personal account cannot set `failIfUnavailable`. Checked only after the run, the first unconfined run has already happened. So the tools are checked, the confinement is probed, and a failure after the run leaves a stop behind.
- **Before the run.**
  - `sys.platform == "win32"` is a usage error.
  - On Linux, `sandbox_problem(which)` checks every tool of `SANDBOX_TOOLS`, which the V-pass fixes from the 1.0.91 package: at 1.0.83 that is `bwrap`, `slirp4netns`, `nsenter`, `iptables`, `ip6tables`, `iptables-restore` and `ip6tables-restore`. A missing tool is untested (precondition), with the remedy naming the tool.
  - macOS is allowed and labelled unverified.
  - **The confinement probe**, under the lock and after the rosters. `confinement_probe(home, env)` starts the headless server through `spawn`, creates a session carrying the run's sandbox settings and the scratch workspace as its working directory, and runs fixed commands through the session's model-free shell call (`session.shell.exec` at 1.0.67). Each command discards its own output and prints one word, `denied` or `readable`, or its exit code:
    - read the token file;
    - read `/proc/<pid>/environ` of the headless server, whose pid the harness knows and whose environment holds the token, as the run's client process does;
    - read `/proc/<pid>/environ` of the harness's own process (`os.getpid()`). It keeps every inherited variable the child builder drops (`GH_TOKEN`, `GITHUB_TOKEN`, provider keys, an exported `COPILOT_GITHUB_TOKEN`), and the deny list names paths, not `/proc`. The server's row can pass because the client process is not dumpable, which says nothing about the harness, so this row reads `denied` only when the sandbox hides the host's processes. *Chosen 2026-10-06 (review follow-up)* over dropping those variables from the runner's own environment, which would not cover its parents (`uv`, `poe`, the shell); one row suffices, because every process of the operator's is equally visible once the host's `/proc` is;
    - list the operator's real `~/.ssh` and `~/.config/gh`;
    - `DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/<uid>/bus gh auth token >/dev/null 2>&1; echo $?`, and `git credential fill` for `github.com`, with terminal prompts off and its output discarded;
    - run `python3 -c 'print(1)'` and one skill script's `--help` from the staged workspace, which must succeed, so that the deny list has not broken the skills.

    `probe_problem(results)` is pure. Any target `readable`, or an exit code of 0 from `gh` or `git`, refuses the run for isolation; a failing skill line refuses it as a precondition. The message names the target and never any output. The probe's session folder is deleted afterwards. Because its commands are fixed in code and print no output, agents may run it through `--preflight-only`, unlike K1's `run-env`, which takes any command.
  - **Settled by task 1.2 (Facts at 1.0.91).** The 1.0.91 headless server offers `session.shell.executeUserRequested`, a model-free shell call that returns the command's output and exit code, and every completion carries `tool.execution_complete.sandboxed`, delivered as a `session.event` notification. No call returns the resolved policy. The probe therefore runs its fixed commands through `executeUserRequested` in a session created with `session.create {sessionId, workingDirectory: ws, model}`, collects the `sandboxed` flag of each command's completion, and refuses for isolation unless every one reads true. It also asks `sandbox.getHostSupport` first and refuses as a precondition when `supported` is not true. The server is started without `--sandbox`: the home's pinned `sandbox.enabled` governs its sessions, and the per-command flag checks that it did. Whether the call runs inside the sandbox is thus measured on every probe rather than assumed; K6 reads the rows.
- **After the run.** The run is untested for isolation, and an isolation stop is recorded, in either case:
  - the CLI's sandbox warning appears, from `session.warning`, `session.error`, `session.info` or stderr, with a text the V-pass names (`SANDBOX_WARNINGS`: "Sandboxing is enabled but is not supported", "Sandboxing is enabled but not supported on this platform", "sandbox enforcement unavailable", and the 1.0.70 "was ignored");
  - the sandbox-active report the V-pass names is absent: a shell-tool `tool.execution_complete` whose `sandboxed` is not true, or no shell-tool completion at all. K6b confirms on the first run. Until then an absent report also stops, and the user clears the stop after reading the kept events. That holds whatever ended the run, a session error included: a run that a rejected token or a quota error ended before any tool call also records the stop. *Recorded 2026-10-06 (review follow-up):* the first implementation exempted any run with a session error and no shell call; the exemption is removed, because neither the spec nor this decision has it and a non-fatal error (such as the soft-cap error after a view-only run) also matched it. A `--reset` clears the stop with the rest of the home; after a limit error the user clears it.
- **Residual risk with the sandbox.**
  - The token file lies outside the home since this revision (Decision 4), so the 1.0.89 session-file grant cannot cover it. Whether the deny list holds for it, and for the CLI process's environment, is what the probe measures before every run.
  - Until the V-pass confirms the probe, the token's reach is bounded by its scope (Copilot Requests only), its expiry, revocation on its own, and `scrub`. The README states the deny claim as unverified until K6 passes.
- **Network.** Whether the sandboxed shell reaches the network by default is observed in K6b, on the first network scenario the user approves. If it does not, network scenarios on Copilot are refused as a usage error, through `openspec-update-change`, until D-C4(c) lands, so that a blocked network never reads as a skill failure.

### 14. Synthetic fixtures: `tests/unit/data/copilot_streams/`

- **Provenance.** Each file is a saved event list: stdout events plus reduced `copilot.*` records. They are derived from the V-pass's reading of the 1.0.91 `app.js` and `schemas/session-events.schema.json`.
- **Raw inputs:**
  - `events-raw.jsonl`, which carries extra fields the reduction must drop;
  - headless replies `status-*.json`;
  - roster outputs `skills-*.json` and `mcp-*.json`.
- **Model names** are synthetic, `copilot-fixture-a` and `copilot-fixture-b`, which the model-ID guard's heads do not match.
- **The README** gives one row per file: "synthetic, from @github/copilot 1.0.91 `<file>`", and what the file pins.
- **The fakes.**
  - A fake `copilot` is a Python script under `tmp_path`, named by an injectable binary path. It emits a fixture stream, writes a session folder, optionally traps SIGTERM, and reports whether it saw the lock descriptor and which token-shaped variables it received, by name only.
  - A fake headless server speaks Content-Length JSON-RPC, including session creation and the shell call the confinement probe uses.
  - **No test can run the real `copilot`, and that is enforced, not assumed.** The full suite reruns at task 9.1 after a real token exists in the default state root, so a test that missed a seam would spend credits without a go. An autouse fixture in `tests/unit/conftest.py` therefore points `copilot_cli`'s binary seam at a sentinel that raises, and sets `THESIS_PROPOSAL_DEV_STATE` to a `tmp_path` directory. A test that needs the fake binary, another state directory or the default one sets or removes them itself. An L0 case asserts that an unpatched `run_copilot` and `read_status` raise rather than spawn.

### 15. V-pass, live checks and USER ACTIONS

| Check | Who and how | Model call | Settles |
|---|---|---|---|
| CLI 1.0.91 | **USER ACTION** `yay -S github-copilot-cli-bin`; the agent then runs `copilot --version` in a scratch environment without network | no | D-C3 precondition |
| V-pass (P1b) | agent: reads the package unpacked into a scratch cache under `unshare -rn`: `app.js`, `runtime.node` strings, `schemas/`, the SDK's `rpc.d.ts`, `--help`, `copilot help <topic>` | no | every fact under Context at 1.0.91, plus the Copilot shell's exported variables, the sandbox events, the effort-unapplied event, the exact deny-list key path, `SANDBOX_TOOLS`, and whether a model-free shell call or a resolved-policy read runs inside the session's sandbox |
| K1 | agent: `host-status copilot`, then `--no-token`. **USER ACTION**: the `gh auth token` exit-code check in the run environment | no | the auth type (`env` or `token`, recorded so `TOKEN_AUTH_TYPES` can be narrowed to it) and host `github.com`; unauthenticated without the token; `gh` cut off |
| K2 | agent: `host-status copilot`, three times | no | the raw snapshot is present under the PAT; overage values with no budget; what `percent_remaining` means; the read makes no model call |
| K4 | agent: `host-status copilot --models` (run before K3, which needs the chosen id) | no | the candidate ids, their policies and efforts |
| K3 | agent: `poe dev check_report --host copilot --model <id from K4> --max-ai-credits 30 --preflight-only`, plus stderr, with `host-status copilot` before and after | no | settings accepted; the `config.json` key set and the `clean_after_reads` row; the rosters; `overage_count` and `remaining_pct` unchanged across the now-authenticated listings and probe |
| K6a | agent: `bwrap --ro-bind / / --dev /dev true; echo $?`, and `command -v` for each tool of `SANDBOX_TOOLS` | no | the sandbox tools are installed and `bwrap` works here |
| K6 | agent: the confinement probe through K3's `--preflight-only`, when the V-pass confirmed it (Decision 13) | no | the effective policy denies the token file, the server's environment, `~/.ssh`, `~/.config/gh`, `gh` and git authentication, and still runs the skills. This is the former K6c, now at $0 before P2 |
| P2 | **gated on the user's explicit go**, given by clearing the approval stop after K1–K6 passed: one `check_report` run on the model the user names from K4, with other Copilot clients closed | yes, credits | K5 and K6b, plus K7 if it times out |

K1's `gh` check needs the exact run environment. `copilot_cli.main(argv)` therefore offers one subcommand, `run-env -- <cmd…>`. It runs a command in a Copilot child's environment (scratch `HOME`, `DBUS_SESSION_BUS_ADDRESS=disabled:`, empty `GH_CONFIG_DIR`), without the token variable, and it is never used by a run. The user runs it, because a failing cut-off would hand the operator's `gh` token to whatever command it runs.

"No model call" is evidenced two ways. Statically, the V-pass shows which endpoints the two RPCs call. Live, K2 shows `remaining_pct` and `overage_count` unchanged across three reads.

## Risks / Trade-offs

- **[The V-pass finds that a 1.0.67 fact changed at 1.0.91]** → The change is revised through `openspec-update-change` before any fixture exists (task 1.3).
- **[The AUR package is no longer at 1.0.91 when the user upgrades]** → The pin is exact. A different version is a revision of D-C3 before the V-pass, never a silent bump.
- **[The raw `quota_snapshots` is absent under a PAT]** (copilot-sdk discussion 1532) → Every run refuses as an unavailable read, which is the fail-closed choice. K2 finds this at $0 before any model call. Reopening it is the user's decision.
- **[The reply's snapshot carries no `overage_entitlement`]** (the 1.0.91 SDK schema omits it, its Rust parser reads it) → Every run refuses as "budget possible", fail-closed. K2 finds this at $0; reopening the rule is the user's decision.
- **[The first `python3` on `PATH` lies under the account home]** (the repository's `.venv/bin` under `uv run`) → The deny list hides it inside the sandbox, and the probe's skill rows refuse every run as a precondition. K6 shows it at $0; the remedy is a reviewed change (a `PATH` for Copilot children without entries under the account home), never a wider deny-list hole.
- **[The PAT does not work with the teacher plan, or K1 shows a fallback credential]** → Every run refuses. K1 finds this at $0, and D-C2 reopens with the user.
- **[`skills_loaded` or the sandbox-active report never reaches the stream]** → P2 is untested by construction, and the kept events show what does arrive. Relaxing either check is a reviewed change in `record-copilot-streams`. The pre-run roster and the `--sandbox` flag stay.
- **[The sandboxed shell reads the token file or the CLI's environment]** → The probe refuses the run before it starts, `scrub` keeps the value out of everything saved, and a hit records an isolation stop. The token can make Copilot requests and nothing else. It expires, and it is revoked on its own with `host-logout copilot` plus revocation on GitHub. The exposure is of the same class as Claude's unsandboxed runs today.
- **[The pinned deny-list key is not the one the CLI reads]** → The CLI ignores an unknown sandbox key silently, so a wrong path would leave the whole account home readable. The V-pass derives the path from the 1.0.91 package, and K6 measures the effective policy at $0 before P2. A missing warning on stderr is never taken as proof.
- **[Denying the whole account home breaks the client's own tools or the skills]** → K6's skill line and the after-run tool results show it. The deny list is then revised through `openspec-update-change`, never carved open in code alone.
- **[The soft cap overshoots]** → No budget exists, so an overshoot can draw only included credits. More than twice the cap records a billing stop.
- **[The pool is shared with the operator's VS Code and CLI]** → The before/after reads compare overage only, and P2 runs with the other clients closed.
- **[Experimental RPC methods or the event schema change]** → The exact pin, and a V-pass at every bump.
- **[Server-managed settings override a pin, and telemetry to GitHub cannot be switched off]** → Accepted. A personal account carries no managed policy, and the local managed-settings file refuses.
- **[Training on inputs is on by default]** → The fixtures are synthetic, and workspaces never include the repository or the private proposals directory. The training opt-out is an optional USER ACTION.
- **[Terms on automated use]** → The `-p` mode is documented for automation. Runs are serial, a few a day, and never in CI. That is a reading of the terms, not a ruling.
- **[The teacher plan lapses into Free]** → The pinned model is no longer listed as enabled, so the model row refuses.
- **[macOS]** → Allowed, but unverified. The README says "verified on Linux only".
- **[Change 2 or 3 is revised after this proposal]** → Tasks 0.1 and 9.3 rebase the four blocks and recheck the three unmodified ones.

## Migration Plan

1. **Start: change 1 archived, changes 2 and 3 implemented with their spec text final.** Change 1 is necessarily archived by then, because change 2's own precondition requires it before change 2's code is written, so change 1's text is read from the archived main spec, never from its change folder. Only the archives of changes 2 and 3 may still be pending: change 2's waits on its L1, and change 3's on change 2's archive.
2. **Before the code.** The CLI upgrade (USER ACTION) and the V-pass. Then the fixtures, the tests, the code and the docs. One commit after `poe test`, `poe cov` and `poe specs` are green. No model call is involved.
3. **Account setup.** The USER ACTIONS (plan check, budget deletion, PAT, `host-login copilot`), then K1–K4, K6a and K6.
4. **P2,** on the user's explicit go, given by clearing the approval stop once every check of step 3 has passed.
5. **Archive,** after changes 1 to 3 are archived in order. P2 is either done, or marked deferred and carried into `record-copilot-streams`.

**Rollback.** A revert, after the USER ACTIONS `uv run poe host-logout copilot` and revoking the PAT on GitHub. Claude and Codex runs are unaffected either way.

## Open Questions

- **The variables a Copilot shell exports,** which become Copilot's agent markers. The V-pass reads them from `app.js`, and the guard does not depend on them.
- **The `config.json` key set a token-mode home develops** (K3). `MANAGED_STATE_KEYS` is `{firstLaunchAt}`, measured for the status read at task 7.4a; K3 confirms it for the listings and the probe through the `clean_after_reads` row, which refuses the same run when a read wrote more, and P2 for a `-p` run, whose writes the next run's clean check finds. Whether the disposable cache files land in the home is open the same way.
- **What `percent_remaining` measures on a credit plan** (K2). The threshold of 10 stays; only the README's wording may change.
- **The exit code after SIGTERM, and whether `session.shutdown` is still written** (K7). A missing shutdown is already a runner failure with a stop, so the answer changes no rule.
- **Whether `--no-custom-instructions` also covers user-level instructions** (K3). The home holds none, and the allow-list refuses them anyway.
