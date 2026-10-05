# Design

## Context

See proposal.md (Why) for the leak and its evidence. Today's spawn points for the `claude` binary:

| Child | Built by | Environment today | Configuration |
|---|---|---|---|
| Routing-rig case | `routing.stream_events` | `routing.isolated_env` (allowlist plus `CLAUDE_CONFIG_DIR`) | `isolated_config`, one shared directory per sweep |
| Dev run, `--isolated` (install probe included) | `claude_runner.run_claude` | `model_env` → `isolated_env` | `isolated_config`, one per run |
| Dev run, ambient | `claude_runner.run_claude` | `model_env`: inherited, minus `ANTHROPIC_*` and `CLAUDE_CODE_USE_*` | operator's own |
| Dev judge and its `auth status` preflight | `claude_cli.call` / `preflight` | `claude_cli.child_env` (`ENV_KEEP` allowlist) | the dev run's isolated configuration |
| Audit pre-flight | `audit_llm_preflight.audit_skill` | inherited unchanged | operator's own |

The relevant facts:

- **The settings file.** `prepare_config` writes `settings.json` as `{}`. `ROUTING_CONFIG_DIR` bypasses preparation entirely.
- **Opt-out names.** The 2.1.284 binary contains `syncClaudeAiSkills`, `syncClaudeAiPlugins`, `disableClaudeAiConnectors` and `ENABLE_CLAUDEAI_MCP_SERVERS` (brief §2.1, §2.3). The docs describe what they do, but that they work in `-p` mode is unverified (L7).
- **Init event.** In the recorded leak run (host 2.1.284), `system/init` lists the claude.ai connector, two plugins (`agents-md@builtin`, `telemetry@builtin`), and 32 skills: 11 under test plus 21 host-bundled.
- **Synced entries.** The synced skills arrive in two `system/commands_changed` events, the first events after `init` and before any assistant event. Each entry carries "(claude.ai sync)" in its description and an `anthropic-skills:<name>` alias.
- **Older runs.** The August routing recordings on 2.1.207 have `mcp_servers: []`, no plugins, and 27 skills.
- **Anthropic profiles.** An Anthropic profile directory outside `CLAUDE_CONFIG_DIR` is the default `${XDG_CONFIG_HOME:-~/.config}/anthropic`, and it ranks near `/login` (brief §2.3, critique 1). It is absent on this machine today, so the gap is latent. `ANTHROPIC_CONFIG_DIR` relocates it per the docs; that the host honours it is unverified. The L8 probe on 2026-10-05 was inconclusive, so fallback F8 is part of this change (Decision 7).

## Goals / Non-Goals

**Goals:**

- No isolated run is measured while an account surface is present. Either the opt-outs hold, or the run is refused or reported untested. It never silently passes.
- No surface stays live for a run's model turns. The host is stopped at the event that announces it, not found after the run.
- No Claude child the harness starts fetches claude.ai connectors, and none the harness starts in ambient mode inherits a billing variable.
- The checks are pure functions over recorded streams and directory listings, testable offline. Exactly one definition of each pinned value exists.
- The next routing report flags the earlier figure as non-comparable without anyone remembering a flag.

**Non-Goals:**

- **The shared env-allowlist builder** that absorbs `claude_cli.ENV_KEEP` (and fixes its drift on proxy, CA, `SHELL` and `LANGUAGE`). The brief's OpenSpec shape (§5, change 2) and fate table (§2.9) put it in `add-harness-claude-login`. This change applies one shared definition of the switch at each site and builds no new allowlist.
- **The harness-owned login home and the link-target move** (Claude step A, D1(b)). That is change 2. Step B is a later, separate change.
- **A stream check on the dev judge.** The judge runs with `--safe-mode` (skills disabled) and `--tools ""`, and without skipping permissions, so a connector tool would need a permission the headless judge cannot be granted. It gets the switch and shares the run's opted-out configuration. No change takes up a judge stream check; it is an Open Question with no owner.
- **Codex.** Not touched.
- **A new routing sweep.** None is run here; the next one records the conditions change automatically.

## Decisions

### 1. One module owns the surface rules: `harness/account_surfaces.py`

The new module is stdlib-only. It holds:

- `CONNECTORS_OFF = {"ENABLE_CLAUDEAI_MCP_SERVERS": "false"}`;
- `BILLING_PREFIXES = ("ANTHROPIC_", "CLAUDE_CODE_USE_")`, moved from `claude_runner`. Once `model_env` delegates to `ambient_env`, nothing in `claude_runner` reads it, so it is not imported back; this module holds its one definition;
- `ambient_env(environ)`: the inherited environment less every variable with a billing prefix, with `CONNECTORS_OFF` applied. The ambient dev run and the audit pre-flight both call it (Decision 5);
- `PINNED_SETTINGS = {"syncClaudeAiSkills": False, "syncClaudeAiPlugins": False, "disableClaudeAiConnectors": True}` and `SETTINGS_FILE = "settings.json"`. `CONNECTORS_OFF` and `PINNED_SETTINGS` are read-only mappings, and settings are compared as JSON text, so `0` never passes for `false`;
- `PROFILE_DIR = "anthropic-empty"`, `PROFILE_VARIABLE = "ANTHROPIC_CONFIG_DIR"` and `profile_dir(config)`, so the profile path is spelled once for `prepare_config`, `isolated_env` and `child_env`;
- for fallback F8 (Decision 7): `PROFILE_STORE = "anthropic"`, `default_profile_store(environ)` and `profile_store_problem(environ)`;
- a frozen `SurfaceLeak(kind, name)` dataclass;
- the pure `stream_surfaces(events, isolated)`, `config_surfaces(config)` and `isolation_problem(config)`, and `surface_reason(leaks, *, isolated)`, which composes the one message and remedy. The mode decides which opt-outs the message says failed: in an isolated run the pinned settings and the connector switch; in an ambient run, which keeps the operator's own settings, the connector switch alone.

It is imported by `routing`, `claude_runner`, `claude_cli` and `audit_llm_preflight`.

*Why a module:*

- `claude_cli` imports `routing`, so the rules cannot live in `claude_cli` without a cycle.
- `routing.py` is already about 680 lines and mixes rig logic with isolation.
- `host_login.py` is about the stored login's bytes.

A dedicated module is where the next writer looks for "what counts as a leak". Change 2's `allowlisted_env` imports from it instead of re-spelling the values.

*Why the billing prefixes move here:* otherwise the audit pre-flight would import the whole dev runner for one tuple. The ambient environment is also the other half of what a host child must not inherit.

*Findings are dataclasses* (AGENTS.md). The dev runner and the rig both turn the same `SurfaceLeak` list into their own failure shape, and neither parses a message.

*Alternatives:*
- Constants in `routing.py`: rejected; the audit pre-flight would import the whole rig.
- A verdict in `l1_checks.py`: rejected. It is not a verdict on a skill but a validity condition of the measurement, like `billing_problem`.

### 2. Detection is tag-based, not a skills allowlist

**Isolated runs.** A surface is any of these:

- any entry in `init.mcp_servers`. Isolated runs configure none, so any server is foreign, whatever its `source`;
- any `init.plugins` entry whose `source` does not end in `@builtin`;
- any skill or command name or alias beginning with `anthropic-skills:`, found in `init.skills`, `init.slash_commands` or a `commands_changed` command;
- any `commands_changed` command whose description contains `(claude.ai sync)`.

**Ambient runs.** Only an MCP server with `source == "claudeai"` counts. Ambient runs measure the operator's own configuration otherwise.

*Alternative rejected:* comparing `init.skills` against the staged set plus a pinned list of host-bundled skills. The bundled set went from 17 to 21 entries between 2.1.207 and 2.1.284, with members both added and dropped, so the pin would break on every host bump and teach people to update it blindly.

*Known gap:* a synced skill loaded from disk at `init` might carry no tag. Decision 4 covers that gap with the directory check.

### 3. Pinned settings are written and verified; the profile directory lives inside the configuration

- **Preparation.** `prepare_config` writes `PINNED_SETTINGS` and creates the empty directory `<config>/anthropic-empty/` (mode 0700).
- **Verification.** `isolated_config` calls `isolation_problem(config)` after preparation, for every configuration, the `ROUTING_CONFIG_DIR` override included. It reports:
  - settings that are not exactly the pinned object;
  - a missing or non-empty profile directory;
  - any `config_surfaces` hit (`skills/synced`, `plugins/synced`).

  It then calls `profile_store_problem(os.environ)` (F8, Decision 7).
- **Refusal.** A problem exits through `sys.exit(message)`, the existing refusal path. `enter_isolation` already maps it to untested, and the rig to a diagnostic exit.
- **The variable.** `isolated_env(config)` and `claude_cli.child_env(environ, config)` set `ANTHROPIC_CONFIG_DIR = str(config / PROFILE_DIR)` whenever a configuration is given, so neither needs a new parameter.

*Alternatives for the profile directory:*

| Option | Why not |
|---|---|
| The brief's persistent `…/thesis-proposal-dev/anthropic-empty/` | Needs the state root, its override guard and marker, all of which are change 2. Change 2 keeps the directory per configuration too (its Decision 8), so the location chosen here stays. |
| A sibling of the configuration in the temp base | Cannot be derived from an override path. |
| A fixed directory under the system temp directory | Shared, so another user could plant a profile there. |

*Override:* an operator-prepared directory without the pinned settings and an empty `anthropic-empty/` is refused, with the missing parts named. The override is retired in change 2.

### 4. Where the checks run, and what they outrank

**Dev runner** (`run_claude`):
- **Reading.** The host's stream is read as it arrives, through `routing.follow_stream` (below), with `stream_surfaces(events, isolated=config is not None)` as the stop condition. The first event that shows a surface stops the host. In the recording, `init` and `commands_changed` precede every assistant event, so a connector the stream announces is not left live for the model's turns, which run with permissions skipped. Today's `subprocess.run` returns only after the whole run, so a publishing connector would stay live for every turn and be found only afterwards.
- **A stopped stream** raises `RunnerFailure(surface_reason(leaks, isolated=…) + billing, untested=True, events=events)`. No host-failure reason is appended, because the exit status of a host the harness stopped is the harness's own.
- **A stream that ran to its end, or hit the deadline,** gets `config_surfaces(config)` when isolated, before the timeout, `host_failure` and `billing_problem`. A hit raises the same untested failure, with the timeout or the host's failure reason appended when there is one. Both failures are composed by one helper, `surface_failure(leaks, events, host_reason, *, isolated)`.
- The stop condition checks only the newest event, since a surface always shows in a single event; the per-line cost stays constant on long dev-run streams.
- A timed-out run's `RunnerFailure` carries the events read so far, so a kept workspace holds them. The timeout message is unchanged.
- **Billing is never hidden.** Both failures append `claude_cli.billing_signals(events)`: the explicit billing reasons a stream carries, partial or not. These are an API-key source or a non-first-party provider (today's `_source_problem`), and overage in use or a refused or unknown rate-limit status (`rate_refusal`). The full `billing_problem` is not used here: its "rate limit not reported" would fire on every stream stopped at `init` and would say nothing about billing.
- A polluted run's other failures say nothing about the skill, so the leak comes first.
- The config check runs before `isolated_config` deletes the directory. That makes L7's "no `skills/synced` or `plugins/synced`" condition an automatic per-run check, not a manual inspection.

**One stream reader:** `routing.follow_stream(command, *, cwd, env, timeout, stop)`.
- It is extracted from the rig's `stream_events` loop, which becomes a call to it with the stop condition "a route is decided or a surface is present".
- It returns a frozen `Followed(events, returncode, stderr, stopped, timed_out)` dataclass.
- It stops the host as the rig does today: `terminate()`, a 5 s grace (`STOP_GRACE_S`), then `kill()`, in one function, `routing.halt`, used by the reader's stop and by its deadline timer. Change 2's termination helper later replaces that sequence in this one place. A host that closes its stream is waited for, not terminated, and the timer still bounds it.
- **Deadline.** A timer stops the host at the deadline even when it writes nothing. The rig's loop checks its deadline only when a line arrives, and `subprocess.run(timeout=…)` no longer bounds the dev run.
- **Process group.** On POSIX the host starts in a process group of its own (`process_group=0`). At the deadline, after `halt`, the timer kills what is left of that group. A process the host started that inherited its stdout would otherwise keep the read open past the deadline, for as long as it lives; `subprocess.run(timeout=…)` returned at the deadline in that case. The group kill stays separate from `halt`, so change 2's replacement of the stop sequence keeps it. Windows ignores the parameter and keeps today's behaviour.
- **stderr** goes to a temporary file, not a pipe, so a host that writes a lot to stderr cannot block while stdout is being read.
- `claude_runner` imports it with its other `routing` names. The fakes that patch `claude_runner.subprocess.run` (`test_dev_runner_probe.fake_host`, `test_install_probe`, `test_isolated_env`) patch `claude_runner.follow_stream` instead, so `check.py`'s own `subprocess.run` runs unpatched.

*Why the stop belongs in this change:* L7's isolated run (task 5.5) and the ambient observation (5.7) are model runs whose connector state is unknown until they run. Ambient runs rely on the switch alone, which L7 never tests by itself. Without the stop, either run could leave a publishing connector live for its whole duration.

*Alternatives:*
- A no-model probe that settles the switch before 5.7: rejected as the only protection, because it covers neither the isolated L7 run, where both opt-outs are still untested, nor a later host bump.
- A deny pattern for `mcp__` tool names: rejected. Whether `--disallowed-tools` accepts a wildcard is unverified, and the names depend on the account.

**Routing rig:**

| Where | What changes |
|---|---|
| `stream_events` | Calls `follow_stream`, which checks each new event and stops the case at the first surface. `init` and `commands_changed` precede every assistant event in the recording, so a polluted case costs one process start and no turns. |
| `case_result` | New precedence: surface > route > host error > stream error. A route chosen with synced competitors present is not a measurement. |
| `main` | Calls `config_surfaces(config)` after the pool finishes and before the `with isolated_config` block closes. A hit turns every result into an error naming the content (`voided(results, leaks)`), so that "Nothing measured" applies: raw results persist, the report is unchanged, and the exit is 1. Each voided result keeps the route it measured, and its own error after the voiding reason, so the persisted log shows what was measured; an errored result counts toward no total. Voiding the whole sweep is deliberate: cases started after the content landed may have loaded it with no tag (Decision 2). |

### 5. The switch is applied at each spawn site from the one definition

| Site | How |
|---|---|
| `isolated_env` | `env.update(CONNECTORS_OFF)` after the allowlist |
| `model_env`, ambient branch | `ambient_env(environ)`: the billing strip, then the switch |
| `claude_cli.child_env` | `env.update(CONNECTORS_OFF)`, so the judge's preflight and calls both get it |
| `audit_llm_preflight.audit_skill` | `env=ambient_env(os.environ)`: the same billing strip as an ambient dev run, then the switch |

Each value replaces an inherited one. The isolated sites merge a shared constant, and the two ambient sites call one function, so no builder is repeated and the third-copy extraction rule is not triggered. The isolated allowlist builder is change 2's (Non-Goals).

*Why the audit pre-flight's billing strip lands here:* it is the same line that gains the switch. Without it, an exported API key, gateway base URL or cloud-provider switch outranks the login and bills every pre-flight call per token with no gate (`AGENTS.md`, "Metered model calls"). An agent session that launches the pre-flight can export a gateway base URL itself. With the strip, the pre-flight runs on the subscription login or fails with the host's login message. The `AGENTS.md` sentence that documents the limitation is rewritten (task 3.2).

`ANTHROPIC_CONFIG_DIR` is the one `ANTHROPIC_*` name an isolated child carries. It is set after the allowlist, so the billing strip still removes every inherited one.

### 6. Conditions are recorded in the report, not remembered

- **Constant.** `routing.ISOLATION_CONDITIONS` is a short human-readable string, for example `"claude.ai account surfaces closed"`.
- **Records.** It is written as a report line, `- isolation: …`, and into the run's raw JSON payload.
- **Comparison.** `previous_isolation(REPORT_FILE)` reads the outgoing line. `write_report` passes `conditions_changed = args.conditions_changed or (previous score exists and previous isolation != current)`.
- **Effect.** The tracked report, which has no isolation line today, is marked not comparable by the first sweep after this change.
- **When to change the string.** Only when what the selector can see changes. Change 2's link-target move does not change it.

*Alternatives:*
- Rely on `--conditions-changed` at the next sweep: rejected. It depends on memory, and the next sweep may be weeks away.
- Hand-edit `docs/skill-routing.md`: rejected, because the file is generated.

Earlier isolated dev-run results have no tracked report. `harness/README.md` records the date boundary instead: runs on hosts ≥ 2.1.273, before this change, were offered synced skills.

### 7. Live checks: what settles L7 and L8, and the fallbacks

**L7 (gates acceptance).** The settings opt-outs and the connector switch hold in `-p` mode on 2.1.284. After implementation, run one isolated dev run (`uv run poe dev check_report --model haiku --isolated --keep --max-budget-usd 0.5`, subscription) and one routing case (`uv run poe routing --case <one canonical case> --epochs 1 --no-report --keep-events`, subscription).

Pass means:
- neither run is untested or errored for a surface;
- the kept streams show `init.mcp_servers == []`, only `@builtin` plugins, and no tagged `commands_changed` entry;
- `init.skills` is the staged skills plus the host-bundled ones seen in the recording.

Report booleans, counts and names only.

**Precautions.** Until change 2 moves the link target, both L7 runs link the operator's own stored login, with write-back. Two faults could then log the operator out of their own CLI (change 2's R1 and R4): an interactive `claude` refreshing the same login at the same moment, or a host stopped between receiving a rotated token and writing it. A stop at `init`, which this change adds, falls in the window where a startup refresh is most likely. The mitigations:
- The user closes every interactive `claude` session before 5.5 and starts none until 5.6 has ended (USER ACTION).
- Every stop this change adds goes through the existing terminate, grace, kill sequence. `keep_login`'s end-of-run check picks up a write the host finished.
- A stop at `init` fires only when a surface is present, which means the opt-outs have already failed.

The residual is a host stopped mid-refresh. Its remedy is `/login`.

*Why L7 stays in this change rather than moving to change 2's live runs on the harness login:* change 2 builds step A only if the opt-outs hold. D1 is (b), with (c) as the fallback if L7 fails, so L7's outcome must be known before change 2 is implemented.

**Recording.** The L7 and L8 outcomes go into this change's tasks (5.1, 5.5, 5.6, 5.8) and into `harness/README.md`, together with the D1 branch they imply: step A (D1(b)) if L7 passed, token mode (D1(c)) if it failed (task 5.9). Change 2's precondition reads that record.

**If L7 fails**, the change still lands, because fail-closed is already the improvement. Every isolated run then refuses instead of measuring a polluted configuration.
- The remedy text names token mode. A `CLAUDE_CODE_OAUTH_TOKEN` session neither syncs nor fetches connectors, per the docs. It is already supported (`prepare_config` links nothing), and the user generates it (USER ACTION, `claude setup-token`).
- Change 2 is then revised to D1(c) through `openspec-update-change` before any step-A code is written. Its step A would otherwise be built and live-checked on a login whose opt-outs are known not to hold, and a token bypasses the harness login entirely.
- `--setting-sources project,local` (effect on auth unverified) is left to a follow-up change.

**L8 (no model call).** The host takes its Anthropic profiles from `ANTHROPIC_CONFIG_DIR`. The probe uses two scratch configurations, each with the pinned settings and no credentials, so no model call can happen. In each, run `claude auth status --json` under the isolated environment, with `XDG_CONFIG_HOME` pointed at a scratch directory:
- arm A sets `ANTHROPIC_CONFIG_DIR` to an empty directory;
- arm B does not set it.

Observe which directory the host creates or touches. List names only, before and after. If `strace` is available, the user may install it (USER ACTION, optional: `sudo pacman -S strace`), and then `strace -f -e trace=%file` gives the file paths opened.

| Outcome | Reading |
|---|---|
| Settled positive | Arm B touches `<scratch-xdg>/anthropic`, and arm A touches only the empty directory. |
| Settled negative | Arm A still touches `<scratch-xdg>/anthropic`. |
| Inconclusive | Neither arm touches either directory. |

**If L8 is negative or inconclusive**, implement fallback F8 before archiving and record it in the spec with `openspec-update-change`.
- **What F8 refuses.** An isolated run (rig, dev run, judge), when the default profile directory `${XDG_CONFIG_HOME:-$HOME/.config}/anthropic`, as the child would resolve it, holds any entry.
- **What the message says.** It names the directory and never its contents. The remedy is to move the profiles aside or use token mode.
- **Cost here.** It never fires on this machine, where the directory is absent.
- **Why not unconditional.** Implemented unconditionally, it would refuse operators who use Anthropic profiles for other tools, even when the variable works.

**L8 outcome (2026-10-05, host 2.1.284): inconclusive.** Without `strace`, the probe ran each arm twice: once with both candidate directories absent, where creating one counts as a touch, and once with both present, empty and aged an hour, where a listing counts as a touch through the access time. A control confirmed that the access-time method detects a listing. Neither arm created or listed either directory, and both reported `loggedIn: false`, `authMethod: "none"`. A file opened inside a directory is not visible to this method. F8 is therefore implemented:
- `isolated_config` calls `account_surfaces.profile_store_problem(os.environ)` after `isolation_problem`. The rig's children, the dev run's model child and the judge's child all take `HOME` and the `XDG_*` variables from that environment, so it resolves the directory as they do. The install probe's child gets a scratch `HOME`, so for it the check may refuse more than it needs to, never less.
- A directory that exists but cannot be listed is refused too, since it is not known to be empty. A path that is absent or is not a directory passes.
- A long-lived token in the environment lifts the refusal, because token mode is the stated remedy.

## Risks / Trade-offs

- **The opt-out keys are not honoured, or are renamed in a later host.** → Isolated runs become untested, not polluted. The message names the surfaces and the token-mode fallback, and L7 is rerun after a host bump that changes the counts.
- **`ENABLE_CLAUDEAI_MCP_SERVERS=false` might also suppress the operator's own MCP servers in ambient runs.** → Ambient measurement moves slightly further from the operator's setup. This is accepted, because a publishing connector in a run with skipped permissions is the larger harm. The first ambient run's `init.mcp_servers` shows which happened.
- **Tag-based detection misses an untagged synced skill.** → The configuration check, plus voiding the whole sweep in the rig. L7 also compares `init.skills` with the recording by hand.
- **The background sync writes after the host exits.** → The write is lost with the temporary configuration, and the run it would have affected has already ended. The next run starts from a fresh configuration.
- **The `ROUTING_CONFIG_DIR` override is refused until it is re-prepared.** → The message names what is missing, and the override is retired in change 2.
- **Ambient runs become untested if the switch fails.** → Intended. A run with a claude.ai connector was never a safe measurement.
- **Connector and skill names appear in runner messages.** → These are names, never values, and they go to gitignored logs. They are needed to diagnose which opt-out failed.
- **Every isolated run refuses after a failed L7, blocking `poe smoke` and the rig.** → Token mode is the documented fallback (D1(c)), and the remedy names it. Change 2 is revised to D1(c) before it is implemented (Decision 7).
- **The L7 runs link the operator's own stored login.** → No interactive `claude` from 5.5 to the end of 5.6 (USER ACTION). Every new stop terminates before it kills, and `keep_login` settles a write the host finished. The residual, a host stopped mid-refresh, costs a `/login`.
- **The dev runner's new stream reader changes how a run ends.** → The deadline timer, the stop at the first surface, and stderr written to a file are L0-tested with a fake `Popen` and a silent real child. The deadline's group kill is L0-tested with a real child that leaves a process holding its stdout. The timeout message is unchanged.
- **The host now leads its own process group on POSIX, so a terminal's Ctrl+C no longer reaches it directly.** → The interrupt reaches the harness, whose reader stops the host through `halt` on any exception, as before.
- **F8 refuses operators who keep Anthropic profiles in the default directory.** → Accepted while L8 is unsettled. The message names the directory and both remedies, and a later probe that settles L8 positive can retire it.
- **The audit pre-flight no longer sees an exported API key.** → Intended. It runs on the subscription login, or fails with the host's login message if there is none.

## Migration Plan

Dev-side only; no workspace or skill changes.

1. Implement the code, tests and docs, with `poe test` and `poe specs` green.
2. Run L8, then L7, after the USER ACTION that closes interactive `claude` sessions.
3. If L8 is not settled positive, add F8 through `openspec-update-change` before archiving. (Done: L8 was inconclusive on 2026-10-05.)
4. Record the L7 and L8 outcomes, and the D1 branch they imply, in `harness/README.md`. Change 2 starts from that record.
5. Commit everything as one commit for the completed change, then archive.

**Rollback** is a revert. No credentials or user files are written by this change beyond the temporary configuration's settings and empty directory.

## Open Questions

- **Ambient connector switch.** Does it hide non-claude.ai MCP servers in ambient runs? The first ambient run's `init` answers it; the approach does not change either way.
- **Ambient profile directory.** Ambient runs still strip an inherited `ANTHROPIC_CONFIG_DIR`, so they read the default profile directory. This is left as is, since ambient measures the operator's auth setup. Whether an Anthropic-profile login shows a non-`"none"` `apiKeySource`, which the existing billing check would catch, is unverified.
- **Synced-plugin `source` spelling.** It is unknown; the "not `@builtin`" rule covers any spelling.
- **Judge stream check.** The judge's stream is parsed but not checked for account surfaces (Non-Goals). No change owns such a check. It would matter only if the judge's flags stopped excluding skills and tool calls.
- **Where `init` falls relative to the first request.** The stop at the first surface assumes, from the recording, that `init` and `commands_changed` precede every assistant event. A host that emitted them later would shorten, not remove, the protection; the stop still fires at the first event that shows a surface.
- **Earliest affected run.** The local, gitignored `logs/routing/*.json` and events files carry host versions. The first affected sweep can be dated from them if a write-up needs it; the automatic conditions record does not depend on that date.
