# Proposal

## Why

Isolated Claude runs are not isolated from the operator's claude.ai account. Account-level surfaces follow the login, not the configuration directory. Since host 2.1.273, every `/login` session downloads the account's synced skills and plugins in the background and fetches its claude.ai MCP connectors. The isolated configuration links that same login, so these surfaces reach every isolated run. A routing-rig case recorded on host 2.1.284 (cwd under `/tmp/routing-…`, so `isolated_config` was in force) shows all three surfaces:

| Signal in the recorded stream | What it shows |
|---|---|
| `system/init.mcp_servers` | `[{"name":"claude.ai Claude Docs","source":"claudeai","status":"pending"}]` |
| `system/init.skills` | 32 entries: the 11 `proposal-*` skills under test plus 21 host-bundled ones |
| two `system/commands_changed` events | 18 entries tagged "(claude.ai sync)" with aliases `anthropic-skills:*` (9 skills, twice): docs, docx, pdf, pptx, xlsx, google-workspace, import-memory, morning, skill-creator |

This breaks two existing promises:

- **Isolation** ("Isolated measurement environment"). Synced skills compete with the skills under test in exactly the routing decision being measured. The synced `docs` skill describes itself as the default for any proposal. Earlier isolated routing figures on hosts ≥ 2.1.273, including the tracked `docs/skill-routing.md`, were therefore measured with that competitor present. Routing runs from August on host 2.1.207 show `mcp_servers: []` and no synced entries.
- **Outward tools** ("Dev-runner cost and helper-agent telemetry"). The Claude Docs connector creates and edits documents on claude.ai, so it publishes. The dev runner skips permission prompts, and `OUTWARD_TOOLS` names only host tools, so a model under test could write to the operator's account. No recorded run has called an `mcp__` connector tool, but nothing prevents one.

This is fixed first, as its own change, because every later login layout depends on it. That includes the harness-owned login home in the next change: a home logged into the same account would sync the same surfaces.

## What Changes

- **Opt-out settings in every isolated configuration.** The configuration's `settings.json` holds the pinned object `{"syncClaudeAiSkills": false, "syncClaudeAiPlugins": false, "disableClaudeAiConnectors": true}` instead of `{}`. A configuration that does not hold exactly that object is refused before the run, and so is one that already holds synced skills or plugins. This covers a prepared directory passed through `ROUTING_CONFIG_DIR`, which used to be accepted as it was. The refusal never falls back to the ambient configuration.
- **A connector switch for every Claude child.** `ENABLE_CLAUDEAI_MCP_SERVERS=false` is set by the harness, replacing any inherited value, for each of these:
  - the isolated child (routing rig and `--isolated` dev runs, including the install probe);
  - the ambient model-under-test child;
  - the dev judge's child and its login preflight;
  - the advisory audit pre-flight's `claude -p`.

  The value is defined once and applied at each site.
- **The audit pre-flight drops billing variables.** Its `claude -p` receives the same environment as an ambient dev run: every inherited `ANTHROPIC_*` variable and `CLAUDE_CODE_USE_*` switch is removed before the switch is set. One function builds that ambient environment for both. An exported API key or gateway base URL then cannot bill pre-flight calls per token, and `AGENTS.md`'s sentence about the limitation is rewritten.
- **An empty Anthropic profile directory for isolated children.** `ANTHROPIC_CONFIG_DIR` points at an empty directory inside the isolated configuration, so that an Anthropic profile in `~/.config/anthropic` cannot become the login. Whether the host honours the variable is unverified (L8). The design gives a no-model probe for it and a fallback refusal (F8) if the probe does not settle it. The probe was inconclusive on 2026-10-05, so F8 is part of this change: an isolated run is refused while the default profile directory holds any entry, unless a long-lived token is in the environment.
- **Stream and directory checks fail closed.**
  - The dev runner reads the host's stream as it arrives, through one stream reader shared with the routing rig, and stops the host at the first event that shows a surface. A publishing connector is then not left live for the model's turns, which run with permissions skipped.
  - An isolated dev run is untested (exit 3) when either of these holds:
    - its stream shows any MCP server, a non-built-in plugin, or a skill tagged "(claude.ai sync)" or aliased `anthropic-skills:*`, in `system/init` or in any `system/commands_changed` event;
    - its configuration holds `skills/synced` or `plugins/synced` after the run.
  - An ambient run is untested when its stream shows a claude.ai-sourced MCP server, which means the switch failed.
  - The untested message also names any API-key source, overage use or refused rate-limit status the stream shows, so a surface never hides a billing problem.
  - A routing case showing a surface is stopped and recorded as an error, which outranks a recorded route.
  - When a sweep's shared configuration holds synced content afterwards, every case of the sweep is voided. The raw results are kept, the tracked report is left unchanged, and the run exits with a failure status.
- **A conditions change recorded automatically.** The routing report records the isolation conditions it was measured under. An outgoing report that records none, or records different ones, is presented as measured under different conditions, not as superseded. The operator no longer has to remember `--conditions-changed`. The run log records the same conditions.
- **The `ANTHROPIC_*` strip gets one exception.** The isolated child's only `ANTHROPIC_`-prefixed variable is the profile directory, which the harness sets itself. Every inherited one is still dropped.
- **Not in this change:**
  - The single env-allowlist builder that absorbs `claude_cli.ENV_KEEP` is placed in change 2 (`add-harness-claude-login`) by the brief's OpenSpec shape (§5) and fate table (§2.9). This change only adds one shared definition of the switch and one function for the ambient environment.
  - Moving the credentials link target to a harness home (Claude step A, D1(b)) is change 2. Step B is a later, separate change. Change 2 builds step A only if L7 passes here; if L7 fails, it is revised to token mode (D1(c)) first.
  - A stream check on the dev judge. The judge runs with `--safe-mode`, `--tools ""` and permission prompts, so it cannot call a connector tool headless. No change owns this check (design Open Questions).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: four requirements change.
  - "Isolated measurement environment": the pinned opt-out settings, the checks before and during a run (the dev runner stops the host at the first surface) and after it, and the routing-sweep voiding.
  - "Isolated child environment": the connector switch for every Claude child, the empty profile directory for isolated children, the judge carve-out narrowed accordingly, and the audit pre-flight's ambient environment without billing variables.
  - "Dev-runner cost and helper-agent telemetry": connectors added to the outward-surface denial, the stop at the first surface, the ambient connector check, the `ANTHROPIC_*` exception, and the untested outcome, whose message also names any billing reason.
  - "A conditions change invalidates comparison": isolation becomes a measurement condition, recorded and compared automatically.

## Impact

- **Code.**
  - `harness/account_surfaces.py` (new): the pinned settings, switch and billing-prefix constants, `ambient_env`, the pure surface checks, and the default-profile-directory check (F8).
  - `harness/routing.py`: `prepare_config`/`isolated_config` checks, `isolated_env`, the shared stream reader `follow_stream` extracted from `stream_events`, `stream_events`/`case_result`/`main` wiring, and the report's isolation line.
  - `harness/claude_runner.py`: `model_env`, and `run_claude` reading through `follow_stream` with the stop at the first surface and the post-run check.
  - `harness/claude_cli.py`: `child_env` and the public `billing_signals`.
  - `harness/audit_llm_preflight.py`: the child environment, built by `ambient_env`.
- **Tests.**
  - `tests/unit/test_isolated_env.py`, `test_claude_cli.py`, `test_dev_runner_probe.py`, `test_install_probe.py`, `test_host_login.py`, `test_routing.py` and `test_audit_tooling.py` are updated. Several of them pin exact environment key sets and the `{}` settings file, and three fake the dev runner's `subprocess.run`, which `follow_stream` replaces.
  - New L0 tests cover the surface checks and the stream reader. They run against a reduced recording added under `tests/unit/data/routing_streams/`, and against silent and stderr-heavy `sys.executable` children.
- **Docs.** `harness/README.md`: the isolation paragraphs, the billing paragraph's `ANTHROPIC_*` exception and the audit pre-flight, routing conditions, and the L7/L8 outcomes with the D1 branch they imply. Also `AGENTS.md`'s sentence on the audit pre-flight, the stream-fixture README and the module docstrings.
- **Live checks.**
  - L7: one isolated `poe dev check_report` on the Max subscription, plus one single-case routing measurement with `--no-report`. Both are subscription runs with no metered call. Both link the operator's own login, so no interactive `claude` runs alongside them (USER ACTION).
  - L8: a probe with no model call.
  - Change 2 reads the recorded L7 outcome before it is implemented.
- **Coexistence.** The open change `desktop-first-install` adds no requirement touched here. Its install probe runs under `isolated_config` and inherits the new checks unchanged.
- **Rollback.** If L7 shows that the settings opt-outs do not hold, isolated runs refuse instead of measuring a polluted configuration. The documented fallback is token mode (`claude setup-token`, already supported), as decided in D1, and change 2 is revised to it before it is implemented.
