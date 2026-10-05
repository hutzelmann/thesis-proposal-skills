# Tasks

Agents never run login commands. A step marked **USER ACTION** is run by the user, with the exact command given. Live checks run on the Max subscription and make no metered call. Report only booleans, counts, enums and names, never an environment value, a credential, an email address or an org.

## 1. Fixtures and failing tests first

- [x] 1.1 Add stream fixtures under `tests/unit/data/routing_streams/`:
  - `claudeai-surfaces.jsonl`, a reduced recording from the local, gitignored `logs/routing/events-write-polish-collision.jsonl` (host 2.1.284). Keep:
    - `system/init`, reduced to `mcp_servers`, `plugins`, `skills`, a short `slash_commands` subset, `apiKeySource` and `claude_code_version`;
    - two `system/commands_changed` events, each with two tagged entries (description containing "(claude.ai sync)", alias `anthropic-skills:*`) and one `proposal-*` entry.

    Drop `session_id`, `uuid`, `cwd`, `messaging_socket_path`, `scratchpad_path` and `memory_paths`.
  - `clean-init.jsonl`, synthetic in the 2.1.284 shape: `mcp_servers: []`, only `@builtin` plugins, and no tagged entry.
  - `ambient-user-mcp.jsonl`, synthetic: one MCP server with source `user` and one with source `claudeai`.

  Add a provenance row for each file to the README in that directory. Verify that `jq -c . <file>` parses every line, and that `grep -c 'session_id\|/tmp/\|socket' <file>` prints 0.

  Done: the recording was reduced with one `jq -s` program; descriptions are cut to their first 60 characters plus their trailing tag. The two `commands_changed` events keep tagged entries 1–2 and 3–4 of each event's list, so three distinct synced skills appear (`docs`, `google-workspace`, `import-memory`). All three files parse line by line; the grep prints 0 for each.
- [x] 1.2 Write `tests/unit/test_account_surfaces.py` for the new module from design Decision 1. Cases:
  - `stream_surfaces`, isolated mode: the recorded file yields the connector and every tagged skill by name. The clean file yields nothing. A non-`@builtin` plugin and an `anthropic-skills:` name in `init.skills` each yield a leak.
  - `stream_surfaces`, ambient mode: only the `claudeai` server counts, and the `user` server does not.
  - `config_surfaces`: a `tmp_path` configuration holding `skills/synced/x` or `plugins/synced/y` yields a leak each; a clean one yields none.
  - `isolation_problem`: it returns None for pinned settings plus an empty `anthropic-empty/`. It names the problem for `{}` settings, for extra keys, for a missing or non-empty profile directory, and for synced content.
  - `surface_reason`: it names each kind and name, says the opt-outs did not hold, names token mode as the fallback, and prints nothing (`capsys`).
  - `ambient_env`: from a synthetic environment carrying `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL`, `ANTHROPIC_AUTH_TOKEN`, `CLAUDE_CODE_USE_BEDROCK`, `ENABLE_CLAUDEAI_MCP_SERVERS=true`, an effort setting and `PATH`, it returns none of the billing variables, the switch set to `false`, and the effort setting and `PATH` unchanged. The input mapping is not modified.

  Verify that the file fails at import before the module exists.

  Done: `ModuleNotFoundError: No module named 'account_surfaces'` before 2.1.
- [x] 1.3 Update the existing tests to the new contracts. Verify that each fails against the current code for the stated reason, not for an import or fixture error.
  - `tests/unit/test_isolated_env.py`:
    - the key set is the machine set plus `CLAUDE_CONFIG_DIR`, `ENABLE_CLAUDEAI_MCP_SERVERS` and `ANTHROPIC_CONFIG_DIR`;
    - an inherited `ENABLE_CLAUDEAI_MCP_SERVERS=true` and an inherited `ANTHROPIC_CONFIG_DIR` are replaced;
    - the wiring tests for the rig and the isolated runner see both variables;
    - the ambient wiring test sees the switch and no inherited `ANTHROPIC_*` value.
  - `tests/unit/test_claude_cli.py`:
    - `child_env` always sets the switch, and sets the profile directory only when a configuration is given. The preflight test sees both.
    - `billing_signals`: a stream stopped at `init` with no rate-limit report yields none. An API-key source, a non-first-party provider, and a rate-limit report with overage in use or a refused status each yield their reason.
  - `tests/unit/test_dev_runner_probe.py`, `tests/unit/test_install_probe.py` and `tests/unit/test_isolated_env.py`: switch the fakes that patch `claude_runner.subprocess.run` to patch `claude_runner.follow_stream`, so `check.py`'s own `subprocess.run` runs unpatched. Then, in `test_dev_runner_probe.py`:
    - `model_env` in both modes carries no inherited `ANTHROPIC_*` value;
    - in isolated mode `ANTHROPIC_CONFIG_DIR == config/anthropic-empty`, and in ambient mode the switch is off;
    - the stop condition `run_claude` hands to `follow_stream` fires on the recorded file's `init` when isolated and on the `claudeai` server when ambient, and does not fire on the `user` server when ambient;
    - `run_claude`, with `follow_stream` faked to report a stop, raises an untested `RunnerFailure` naming the surface, without a host-failure reason and without "rate limit not reported";
    - it raises untested when the isolated configuration holds `skills/synced` after a stream that ran to its end;
    - a configuration leak plus a host error result yields the surface message with the host reason appended;
    - a stream that carries both a surface and a rate-limit report with `isUsingOverage: true` yields a message naming both (design Decision 4, "Billing is never hidden").
  - `tests/unit/test_host_login.py` (the `prepare_config` section):
    - `prepare_config` writes exactly the pinned settings and an empty `anthropic-empty/`;
    - `isolated_config` refuses a `ROUTING_CONFIG_DIR` override with `{}` settings, and its `SystemExit` message names the settings and the profile directory;
    - `enter_isolation` maps that refusal to untested.
  - `tests/unit/test_routing.py`:
    - `follow_stream`, with a recording fake `Popen`, stops at the first event the stop condition accepts, reads no further line, and calls terminate before any kill;
    - `follow_stream`, with a real `sys.executable` child that writes nothing and sleeps, and a timeout of 0.5 s, returns `timed_out` within the grace;
    - `follow_stream`, with a real `sys.executable` child that writes about 200 KB to stderr before its first stdout line, returns that line and does not block;
    - `case_result` records a surface as an error even when a route exists;
    - `stream_events`, with `subprocess.Popen` monkeypatched to emit `init`, then `commands_changed`, then a `proposal-*` Skill call, stops before the Skill call and returns the surface error;
    - with the `offline_rig` fixture, `main` turns every result into an error when the configuration holds `plugins/synced` after the sweep, leaves the report unchanged, persists the raw results and exits 1;
    - the report carries an `- isolation:` line, and the raw payload carries the same conditions;
    - an outgoing report without that line, or with a different one, yields "measured under different conditions, not comparable", without `--conditions-changed`;
    - the same line yields "supersedes".
  - `tests/unit/test_audit_tooling.py`: `audit_skill`, with `subprocess.run` monkeypatched, passes an environment whose `ENABLE_CLAUDEAI_MCP_SERVERS` is `false` even when the launching environment says `true`. It carries no `ANTHROPIC_API_KEY`, `ANTHROPIC_BASE_URL` or `CLAUDE_CODE_USE_*` variable from a launching environment that sets them, and keeps `PATH` and an unrelated variable.

  Done. Notes:
  - The fake reader is one helper, `tests/helpers.py::followed`, used by the three files that fake the host (third-repetition rule). It applies the stop condition event by event as the real reader does, so the fakes exercise the stop `run_claude` hands over.
  - Red run: `routing.Followed` (the data shape only) was added first, because `tests/helpers.py` is imported by `conftest.py`. Against that, 48 tests failed and 10 errored for the stated reasons: `claude_runner` has no `follow_stream` (35), `claude_cli` has no `billing_signals` (6), and the switch, profile directory and pinned settings were missing. `test_routing.py` failed at import on the new names `ISOLATION_CONDITIONS`, `follow_stream` and `previous_isolation`. That was a choice, not a necessity: the file already imports `routing`, so reaching the new names as `routing.follow_stream` and so on would have made each test fail on its own. The import-time red run does not show that each of its tests fails for the stated reason.
  - `offline_rig` also points `routing.REPO` at `tmp_path`: `write_report` prints the report path relative to it, and the new report tests are the first to write a report through `main`.

## 2. Implementation

- [x] 2.1 Create `harness/account_surfaces.py` (stdlib only), per design Decisions 1–3. It holds `CONNECTORS_OFF`, `BILLING_PREFIXES` (moved from `claude_runner`), `ambient_env(environ)`, `PINNED_SETTINGS`, `PROFILE_DIR`, the frozen `SurfaceLeak(kind, name)`, `stream_surfaces(events, isolated)`, `config_surfaces(config)`, `isolation_problem(config)` and `surface_reason(leaks)`. Its module docstring cites the recorded evidence and the spec requirement "Isolated measurement environment". Verify that 1.2 passes, and that `uv run ruff check harness/account_surfaces.py` reports no C901 (complexity ≤ 12, so split per-event-kind helpers if needed).

  Done, with per-event-kind helpers. Beside the named items the module holds `SETTINGS_FILE`, `PROFILE_VARIABLE` and `profile_dir(config)`, so the profile path is spelled once for `prepare_config`, `isolated_env` and `child_env`. `CONNECTORS_OFF` and `PINNED_SETTINGS` are read-only mappings. Settings are compared as JSON text, so `0` never passes for `false`.
- [x] 2.2 In `harness/routing.py`:
  - `prepare_config` writes `PINNED_SETTINGS` and creates `anthropic-empty/` (mode 0700);
  - `isolated_config` calls `isolation_problem` for every configuration, the override included, and exits with the message;
  - `isolated_env` applies `CONNECTORS_OFF` and sets `ANTHROPIC_CONFIG_DIR` after the allowlist;
  - extract `follow_stream(command, *, cwd, env, timeout, stop)` and the frozen `Followed` dataclass from the loop in `stream_events` (design Decision 4, "One stream reader"). It keeps the terminate, 5 s grace, kill sequence, adds a timer that stops a silent host at the deadline, and writes stderr to a temporary file.

  Verify that the `test_host_login.py` and `test_isolated_env.py` cases and the `follow_stream` cases from 1.3 pass.

  Done. The terminate, grace, kill sequence is one function, `routing.halt` (grace `STOP_GRACE_S = 5`), used by the reader's stop and by its deadline timer; change 2's termination helper replaces it there. A host that closes its stream is waited for, not terminated, and the timer still bounds it.

  Review fix (2026-10-05): a process the host started that inherited its stdout held the read open past the deadline. A scratch probe returned after the child's 8 s, not at the 0.5 s deadline; `subprocess.run(timeout=…)` had returned at the deadline. On POSIX the host now starts in a process group of its own (`process_group=0`), and the deadline timer kills what is left of the group after `halt` (`_own_group`, `_end_group`). The group kill sits outside `halt`, so change 2's `stop_child` replaces only the stop sequence. New L0 case: `test_follow_stream_deadline_holds_against_a_child_that_inherited_stdout`, red at 30 s before the fix.
- [x] 2.3 In `harness/claude_runner.py`, per design Decision 4:
  - import `BILLING_PREFIXES` from `account_surfaces` instead of defining it;
  - `model_env`'s ambient branch returns `ambient_env(environ)`;
  - `run_claude` starts the host through `follow_stream` (task 2.2) with `stream_surfaces(events, isolated=config is not None)` as the stop condition, instead of `subprocess.run`. The timeout message stays as it is;
  - a stopped stream raises `RunnerFailure(surface_reason(...) + billing_signals, untested=True, events=events)`, with no host-failure reason;
  - a stream that ran to its end gets `config_surfaces(config)` when isolated, before `host_failure` and `billing_problem`. A hit raises the same untested failure, with any host-failure reason and the billing signals appended.

  Verify that the `test_dev_runner_probe.py` cases from 1.3 pass, that the install-probe tests stay green, and that `uv run ruff check harness/claude_runner.py` reports no C901.

  Done. Deviations:
  - `BILLING_PREFIXES` is not imported back into `claude_runner`: once `model_env` delegates to `ambient_env`, nothing there reads it, and a dead import fails ruff (F401). The one definition is `account_surfaces.BILLING_PREFIXES`.
  - The surface failure is composed by `surface_failure(leaks, events, host_reason)`, shared by the stopped and the configuration paths.
  - The stop condition checks only the newest event, since a surface always shows in a single event. This keeps the per-line cost constant on long dev-run streams.
  - A timed-out run's `RunnerFailure` now carries the events read so far, so a kept workspace holds them. The message is unchanged.

  Review fixes (2026-10-05):
  - A timed-out isolated run skipped the configuration check, so synced content was reported as an ordinary timeout (exit 4). The check now runs before the timeout raise, and a hit raises the untested surface failure with the timeout appended. New L0 case: `test_synced_content_outranks_a_timeout`.
  - An ambient run stopped for a claude.ai connector was told that the pinned settings did not hold, though an ambient run never gets them. `surface_reason` and `surface_failure` now take the mode. An ambient message names the connector switch as the opt-out that failed. `test_a_claudeai_connector_stops_an_ambient_run` and `test_an_ambient_reason_blames_only_the_connector_switch` pin the wording.
- [x] 2.4 In `harness/claude_cli.py`:
  - `child_env` applies `CONNECTORS_OFF`, and sets `ANTHROPIC_CONFIG_DIR = config / PROFILE_DIR` when a configuration is given;
  - add the public `billing_signals(events) -> list[str]`: the reasons of `_source_problem` and `rate_refusal` that the stream carries, readable from a partial stream.

  Verify that the `test_claude_cli.py` cases from 1.3 pass.

  Done. `billing_signals` reads the source check only when the stream carries an `init` event, so an empty or pre-`init` stream yields nothing.
- [x] 2.5 In `harness/audit_llm_preflight.py`, `audit_skill` passes `env=ambient_env(os.environ)`: the dev runner's billing strip, then the switch (design Decision 5). Verify that the audit-tooling case from 1.3 passes.
- [x] 2.6 Routing rig, per design Decision 4:
  - `stream_events` calls `follow_stream` (task 2.2), stops the case at the first event with a route or a surface, and returns `surface_reason` as its error for a surface;
  - `case_result` puts a surface above a route;
  - `main` runs `config_surfaces(config)` inside the `isolated_config` block after the pool finishes, and on a hit replaces every result's route with an error naming the content.

  Verify that the `test_routing.py` reader, stream, case and `main` cases from 1.3 pass, that the existing `StalledHost` deadline test stays green, and that `uv run ruff check harness/routing.py` reports no C901.

  Done. The voiding is `routing.voided(results, leaks)`. A malformed `Skill` call still raises out of the reader as before; this change does not alter that path.

  Review fix (2026-10-05): `voided` dropped each case's route and its own error, so the persisted log did not hold the raw results the spec promises. Each voided result now keeps its route, with the case's own error after the voiding reason. `classify` skips every errored result, so no count changes. `test_synced_content_after_the_sweep_voids_every_case` asserts both, and that the totals stay 0/0.
- [x] 2.7 Routing report, per design Decision 6:
  - add `ISOLATION_CONDITIONS` and the `- isolation: …` line in `render_report`;
  - add the conditions field in the raw payload;
  - add `previous_isolation(path)`;
  - in `write_report`, set `conditions_changed` when an outgoing score exists and its isolation differs from the current one, or when the flag is given.

  Verify that the report cases from 1.3 pass and that `test_a_conditions_change_is_not_a_comparison` stays green.

  Done. `render_report` takes `isolation` (default `ISOLATION_CONDITIONS`). `--render` from a saved run log passes the log's own `isolation` field, so a log written before this change re-renders without the line.

## 3. Documentation

- [x] 3.1 Update `harness/README.md`:
  - **Billing paragraph.** `ANTHROPIC_CONFIG_DIR` is the one `ANTHROPIC_*` name an isolated child carries. The audit pre-flight now drops the same billing variables as an ambient dev run.
  - **Dev runs (`--isolated`).** The configuration holds the pinned opt-outs and an empty profile directory, and every Claude child gets `ENABLE_CLAUDEAI_MCP_SERVERS=false`. The runner reads the stream as it arrives and stops the host at the first claude.ai account surface in an isolated run, or the first claude.ai connector in an ambient run. Either makes the run untested, with any billing reason the stream shows and the token-mode fallback named.
  - **Skill routing isolation paragraph.** The opt-outs, the per-case stop, the sweep voiding, and the `ROUTING_CONFIG_DIR` override's new preconditions.
  - **Routing conditions.** The report's isolation line and the automatic comparison.
  - **Date boundary.** Isolated dev-run and routing results on hosts ≥ 2.1.273, before this change, were measured with the account's synced skills offered (and, in routing, the Claude Docs connector).

  Verify by reading the diff. `uv run poe test` must stay green, because README text is pinned by some L0 tests.

  Done. Besides the listed paragraphs: the exit-status table's untested row names the isolation reason, the `ROUTING_CONFIG_DIR` sentence spells out the exact settings object it must hold, the audit pre-flight section names its environment, and the routing section's L0-coverage sentence names `test_account_surfaces.py`. `--conditions-changed` had no README mention before; the new "Measurement conditions" paragraph introduces it.
- [x] 3.2 Update the module docstrings of `routing.py` (isolated environment section), `claude_runner.py` (the `--isolated` and billing text, lines 37–47), `claude_cli.py` and `audit_llm_preflight.py` to say what they now set and check. In `AGENTS.md` ("Metered model calls"), rewrite the sentence that says the audit preflight hands the launching shell's environment to `claude -p`: it now drops every `ANTHROPIC_*` variable and `CLAUDE_CODE_USE_*` switch, as the dev runner does. Keep the rest of that paragraph. Verify by reading the diff and by `grep -n 'audit preflight' AGENTS.md`.

  Done. The dev runner's `--isolated` help text no longer says "settings emptied". The `ADMITTED_ENV` comment in `routing.py` says that the account-surface variables are set, never admitted.

## 4. Gate

- [x] 4.1 Run `uv run poe test` (not `test-fast`) and confirm it is green: pytest, ruff with the full rule set, `test_repo_conventions.py`, drift and conform.

  Done: exit 0. 2729 passed, 1 skipped; ruff "All checks passed!"; generated copies in sync; all 11 skills conform.
- [x] 4.2 Run `uv run poe cov` and confirm that the coverage floor of 78% holds.

  Done: 90.68% total. `account_surfaces.py` is at 98%. Two reader tests (a non-JSON line, a reader that raises) were added afterwards to cover the new code's remaining paths.
- [x] 4.3 Run `uv run poe specs` and `openspec validate close-claudeai-surfaces --strict`, and confirm both pass.

  Done: 22 passed, 0 failed; "Change 'close-claudeai-surfaces' is valid".

## 5. Live checks (after 4)

- [x] 5.1 L8 probe, with no model call and no credentials (an agent may run it). Create two scratch configurations under the session scratchpad, each holding `PINNED_SETTINGS` and nothing else, plus a scratch `XDG_CONFIG_HOME`.
  - Arm A: run `claude auth status --json` under `routing.isolated_env(<config>)`, which sets `ANTHROPIC_CONFIG_DIR` to the configuration's empty directory.
  - Arm B: run the same with that variable removed.

  Drive both arms from one scratch script under the session scratchpad, not inline Python.

  Pipe the output through `jq '{loggedIn, authMethod}'`. List names only, never contents, of `<config>/anthropic-empty` and `<scratch-xdg>/anthropic`, before and after each arm. Record the result here as settled positive, settled negative or inconclusive, using design Decision 7's criteria.

  Done 2026-10-05, host 2.1.284: **inconclusive**. No `strace`, so each arm ran twice, from one scratch script. In the first run both directories were absent, and creating one counts as a touch. In the second both were present, empty and aged an hour, and a listing counts as a touch through the access time. A control showed that the access-time method detects an `ls`.
  - Both arms: `loggedIn: false`, `authMethod: "none"`, exit 1.
  - Arm A had the variable set and arm B did not. In neither arm did the host create or list `anthropic-empty` or `<scratch-xdg>/anthropic`. Both directories' name lists stayed empty.

  A file opened inside a directory is invisible to this method. 5.3 applies.

  Rerun once on 2026-10-05, after 5.3, from the same scratch script: the same result in all four arm runs, and the control again detected the `ls`.
- [ ] 5.2 **USER ACTION** (optional, only if 5.1 is inconclusive): `sudo pacman -S strace`. Then rerun 5.1 with `strace -f -e trace=%file -o <scratchpad>/l8-<arm>.trace`, and count, with `grep -c`, the lines naming `<scratch-xdg>/anthropic` and `anthropic-empty` in each trace. Record the counts here.

  Not run (2026-10-05): the optional install was not taken, and `strace` is still absent. F8 (5.3) covers the inconclusive outcome.
- [x] 5.3 Conditional: if L8 is not settled positive, implement fallback F8 from design Decision 7. It refuses an isolated run whose default Anthropic profile directory, as the child would resolve it, holds any entry; it names the directory and never its contents. Add L0 tests with `tmp_path`, extend the spec delta through the `openspec-update-change` skill, and repeat 4.1–4.3. If L8 is settled positive, mark this task "not needed" with the 5.1 evidence.

  Done, since L8 was inconclusive.
  - **Code.** `account_surfaces.default_profile_store(environ)` resolves `${XDG_CONFIG_HOME:-$HOME/.config}/anthropic`. `profile_store_problem(environ)` refuses while that directory holds any entry or cannot be listed, unless a long-lived token is in the environment. `routing.isolated_config` calls it with `os.environ` after `isolation_problem`. The rig's, the dev run's and the judge's children take `HOME` and `XDG_*` from that environment.
  - **L0 tests.** In `test_account_surfaces.py`: the resolution, absent, empty or file, an entry named without its contents, unlistable, and the token. In `test_host_login.py`: `isolated_config` refuses. The `stored_dir` fixture points `XDG_CONFIG_HOME` at `tmp_path`, so no test reads the operator's directory.
  - **Artifacts.** The spec delta (Isolated measurement environment: the refusal and the scenario "Anthropic profile in the default directory"), design Decisions 1, 3 and 7, and the proposal, all updated through `openspec-update-change`.
  - **Gates repeated.** 4.1 green: 2740 passed, 1 skipped; ruff clean; drift in sync; 11 skills conform. 4.2: 90.77%. 4.3: 22 passed, and the change validates.
- [x] 5.4 Preconditions for 5.5–5.7, both **USER ACTION** with no command:
  - confirm that extra usage is off in the claude.ai account's usage settings (exact page unverified). The run's own overage check stays the backstop.
  - close every interactive `claude` session in a terminal, and start none until 5.6 has ended. Both L7 runs link your own stored login with write-back, and a concurrent refresh could log your CLI out (design Decision 7, "Precautions"). A desktop-app session does not refresh that file (change 2's R6) and may stay open.

  Done 2026-10-05. The user confirmed both in chat; the desktop app stayed open. The agent could check only the second: `ps` showed no terminal-attached `claude` process before 5.5 or after 5.6. The streams of 5.5 and 5.7 reported `isUsingOverage: false` and status `allowed`. After 5.7, `claude auth status` still reported `loggedIn: true`, and no refresh claim file was left in `~/.claude`.
- [x] 5.5 L7 dev run, subscription, run once: `uv run poe dev check_report --model haiku --isolated --keep --max-budget-usd 0.5`.
  - If it reports an expired login: **USER ACTION** `claude`, then enter `/login`, then exit that session; rerun once.
  - If the host is stopped for a surface, the run is untested and L7 has failed. Record the named surfaces and go to 5.8.
  - Pass requires all of these:
    - the outcome is not untested for an account surface;
    - in the kept `.devrun-events.jsonl`, `jq` shows `init.mcp_servers | length == 0`, every plugin source ends in `@builtin`, and no `commands_changed` command carries "(claude.ai sync)" or an `anthropic-skills:` alias;
    - `init.skills` holds no name beyond the staged skills and the 21 host-bundled names of the 2.1.284 recording.

  Record booleans and counts here, then delete the kept workspace.

  Done 2026-10-05, host 2.1.284, served model `claude-haiku-4-5`: **passed**. No expired login.
  - Outcome PASS (exit 0), L1 6/6. Not untested, so the configuration check after the run found no `skills/synced` or `plugins/synced`.
  - `init.mcp_servers | length == 0`: true. Plugins: 2, all ending in `@builtin`: true.
  - `commands_changed` events: 0. Lines carrying "(claude.ai sync)" or `anthropic-skills:`: 0.
  - `init.skills`: 19 names, none beyond the staged one (`proposal-check`) and the recording's 21 other names. 18 of those 21 appeared; `artifact-capabilities`, `artifact-diagramming` and `slides` did not. They are untagged in the recording, so whether they follow the opt-outs is not established.
  - `apiKeySource: none`; rate limit `allowed`, `isUsingOverage: false`. Notional cost reported by the host: $0.061.

  Kept workspace deleted.
- [x] 5.6 L7 routing case, subscription: `uv run poe routing --case review-canonical --epochs 1 --no-report --keep-events`. Pass: the case is not an error for a surface, the sweep is not voided, and `logs/routing/events-review-canonical.jsonl` passes the same `jq` checks as 5.5. Record here.

  Done 2026-10-05, host 2.1.284, sonnet: **passed**. "1/1 correct", exit 0. The raw result records route `proposal-review` and no error, so the case was neither stopped for a surface nor voided. The raw log carries the isolation field.
  - `init.mcp_servers | length == 0`: true. Plugins: 2, all `@builtin`: true.
  - `commands_changed` events: 0. Tagged or `anthropic-skills:` lines: 0.
  - `init.skills`: 29 names, none beyond the 11 staged skills and the recording's 21 other names. The same three names as in 5.5 were absent.
  - `apiKeySource: none`. The rig stops at the route, after one assistant event, so the stream carries no rate-limit report and no cost.
- [x] 5.7 Ambient observation, subscription, run once: `uv run poe dev check_report --model haiku --keep --max-budget-usd 0.5`. This is the first run that tests the connector switch on its own; 2.3's stop at the first claude.ai connector is in place, so a failing switch costs one process start. Record whether the host was stopped for a `claudeai` server (expected: no), and whether the operator's own non-claude.ai servers still appear in `init.mcp_servers` (design Open Question 1). Delete the kept workspace.

  Done 2026-10-05, host 2.1.284, served model `claude-haiku-4-5`.
  - Stopped for a `claudeai` server: **no**. `init.mcp_servers` held 0 servers with source `claudeai`.
  - The operator's own servers: **still present**. One server with source `user`, status `connected`. Open Question 1: the switch leaves the operator's own servers in place.
  - `commands_changed` events: 0. As expected in ambient mode, `init` carried the operator's own configuration: 2 plugins not ending in `@builtin`, and 18 `anthropic-skills:` entries across `init.skills` and `init.slash_commands`. Neither counts as a surface in an ambient run (design Decision 2).
  - `apiKeySource: none`; rate limit `allowed`, `isUsingOverage: false`. Notional cost: $0.069.
  - The run itself ended FAIL, exit 1: L1 "only 0/6 oracle errors surfaced". The chat summarised the six errors in its own words rather than relaying the check's messages. This is a verdict on the ambient-mode answer, not on a surface.

  Kept workspace deleted.
- [x] 5.8 Conditional: if 5.5 or 5.6 fails, record which surface appeared. Keep the fail-closed checks; they are the improvement either way.
  - Fallback: **USER ACTION** `claude setup-token`, then export `CLAUDE_CODE_OAUTH_TOKEN` in the shell that starts the harness (never into a committed file).
  - Rerun 5.5 once in token mode and record whether the surfaces are absent.
  - Note `--setting-sources project,local` as a follow-up change.
  - Record that D1 falls back to (c): `add-harness-claude-login` is revised to token mode through `openspec-update-change` before any of its code is written (design Decision 7).

  If 5.5 and 5.6 pass, mark this task "not needed".

  Not needed: 5.5 and 5.6 passed on 2026-10-05 with no surface. L7 passed, so D1 stays (b), step A, and `add-harness-claude-login` is not revised to token mode.
- [x] 5.9 Record the live-check outcomes where change 2 reads them. In `harness/README.md`, add one dated line each for:
  - L8: settled positive, settled negative or inconclusive (from 5.1/5.2), and whether F8 was implemented (5.3);
  - L7: passed or failed (5.5, 5.6), with the surfaces named on a failure;
  - the D1 branch this implies: step A (D1(b)) if L7 passed, token mode (D1(c)) if it failed.

  Booleans, enums, counts and names only. Verify by reading the diff, and confirm that the same outcomes are recorded in 5.1, 5.5, 5.6 and 5.8 of this file.

  Done 2026-10-05: three dated lines under "Live checks of the opt-outs" in the routing section, beside the account-surface paragraphs. They match 5.1 (inconclusive, F8 implemented), 5.5 and 5.6 (passed, no surface) and 5.8 (not needed, D1(b)).

## 6. Close

- [x] 6.1 Commit the code, tests, docs and this change folder as one commit for the completed change, off `main` until it is complete. Do not push. Verify with `git status` (clean) and `git show --stat HEAD`.

  Done 2026-10-05: one commit on `main` after the archive, with the change complete. Staged by explicit path; the untracked folders of the later changes stay out of it. Not pushed.
- [x] 6.2 Archive through the `openspec-archive-change` skill. Verify that `openspec validate --all --strict` is green afterwards. The first routing sweep after this change marks the tracked report's earlier figure as not comparable on its own; no sweep is part of this change.

  Done 2026-10-05 with `openspec archive close-claudeai-surfaces --yes`, then `python3 scripts/sync_shared.py`, `uv run poe test` and `uv run poe specs` on the archived tree. 5.2 stays open: it is the optional strace install, not taken, and F8 (5.3) covers the inconclusive L8.
