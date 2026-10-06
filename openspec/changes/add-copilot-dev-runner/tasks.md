# Tasks

Ground rules for every task below:

- **Model calls.** No task before section 8 makes a model call of any kind: no `copilot -p`, no `codex exec`, no `claude -p`, no OpenRouter.
  - The headless status read, the `skill list`/`mcp list` rosters, `--version`, `--help` and `copilot help <topic>` make none.
  - Before a login exists, every Copilot command an agent runs here also runs under `unshare -rn`, with no network at all.
- **Logins.**
  - Agents never run `poe host-login` (any option) or `poe host-logout`, and never create, paste or handle a token. A step marked **USER ACTION** is run by the user, with the exact command given.
  - Agents may run `uv run poe host-status copilot`, with or without `--models` or `--no-token`, and `uv run poe dev … --host copilot … --preflight-only`. None of these makes a model call.
- **Credentials.**
  - Nobody opens, prints, copies or `cat`s the token file `<state>/hosts/copilot.token`, the operator's `~/.copilot`, `~/.config/github-copilot`, `~/.config/gh` or the OS keyring. Nobody reads `/proc/<pid>/environ` of a Copilot child or runs `ps e` (or any `ps` showing environments) while one runs. In code, only the login command, the logout and `token_env` touch the token file.
  - The token is never pasted into chat, a file, `.env` or a shell variable.
  - Reports carry only booleans, counts, enums, version strings, file names and top-level key names. They never carry a token, a login name, an email address, an organization or an environment value.
- **Workspaces.** Copilot workspaces are temporary directories outside the repository and outside the operator's home. The private proposals directory is never a workspace.

## 0. Precondition

- [x] 0.1 Confirm that changes 1–3 are implemented, with their spec text final.
  - *Done 2026-10-06.* Changes 1 and 2 are archived (`2026-10-05-close-claudeai-surfaces`, `2026-10-06-add-harness-claude-login`); change 3's sections 0–5 are ticked on this branch (8cb2f56, bbd7003). Every name the list below asks for exists in the code. Rebase: the "Isolated child environment" block now carries the archived main spec's status-check sentence, the long-lived-token exception and the scenario "Status check reports the home's own login"; the other three blocks carry change 3's revisions since bbf6ab2 (relative override, no adoption of an unmarked directory, a failed logout stops a re-login or reset, the Claude status check without the long-lived token, the default profile directory rule and rows, the two extra stop cases, the split marker rows, "the same refresh claim", the label that follows how the configuration was prepared, and the connector and write-back scenario wording), with the Copilot rows in the same pattern. Host-counting: the three unmodified blocks name no count of hosts. Scenario names: all 86 of the four base blocks appear. `openspec validate add-copilot-dev-runner --strict` passes with only the allowed INFO line. Change 1 is already archived, because change 2's own precondition (its task 0.1) requires that before change 2's code is written; read change 1's text from the archived main spec (`openspec/specs/testing-harness/spec.md`), never from its change folder. Only the archives of changes 2 and 3 may still be pending: change 2's waits for its L1, and change 3's for change 2's archive. Check two things:
  - each change's code sections and gates are checked off in its `tasks.md` (change 1's in its archived copy);
  - the code exposes what this change builds on:
    - `harness/hosts.py`: `Host`, `RunView`, `JudgeBackend`;
    - `harness/host_login.py`: `HostLogin` with `strip_suffixes`, `stop_signal`, `outside_tempdir` and `child_vars`; `RECORDS`, `allowlisted_env`, `login_env`, `AGENT_MARKERS`, `LoginProblem(client=…)`, `NOTES`, `refusal`, `login_note`, `login_remedy(…, record)`, `run_lock`, `RunLockBusy`, `run_host`, `stop_child(proc, sig)`, `TERM_GRACE_S` and `main`;
    - `harness/codex_cli.py`: `read_quota`;
    - `claude_runner`: `HOSTS`, `host_for` and `stage(…, skill_dir)`.

  Then check the spec text:
  - **Rebase.** Compare the four MODIFIED blocks' base with the final text. "Harness-owned host logins", "Dev-runner host adapters" and "Dev-runner cost and helper-agent telemetry" start from `add-codex-dev-runner`; "Isolated child environment" starts from `add-harness-claude-login`. Rebase any that differ through the `openspec-update-change` skill.
  - **Host-counting.** Confirm that "Inverted-hybrid runners", "Measured environments carry no eval definitions" and "Subscription text roles (dev runner)" in change 3's final text still name no count of hosts. If one does, add a MODIFIED block for it through `openspec-update-change` before any code.
  - **Scenario names.** Every scenario name of the four base blocks must appear in this change's blocks.
  - **Validation.** `openspec validate add-copilot-dev-runner --strict` passes. Its only allowed INFO line is "Archive would refuse … not found".

## 1. CLI upgrade and V-pass (D-C3(b), no model call)

- [x] 1.1 **USER ACTION:** `yay -S github-copilot-cli-bin`, which must install 1.0.91.
  - *Done 2026-10-06 (the install by the user, the checks by the agent).* `pacman -Q github-copilot-cli-bin` reads `1.0.91-1`; the binary, run exactly as below, prints `GitHub Copilot CLI 1.0.91.` and unpacked `pkg/linux-x64/1.0.91/`. Pass. The workflow brief said 1.0.92 was installed and asked for a 1.0.92 pin; that 1.0.92 is the operator's auto-update download in `~/.cache/copilot/pkg/`, which a harness child (auto-update off, its own cache) never runs, so the pin stays 1.0.91 as D-C3(b) planned (design, Facts at 1.0.91). Bumping to 1.0.92 is one constant plus its own V-pass.
  - *Re-checked 2026-10-06 (second implementation session).* The workflow brief again asked for a 1.0.92 pin, recorded as a deviation from 1.0.91. Re-run, task 1.1's exact command (`unshare -rn`, scratch homes, auto-update off) prints `GitHub Copilot CLI 1.0.91.`; `pacman -Q` reads `1.0.91-1`; `/var/log/pacman.log` shows the upgrade 1.0.67 → 1.0.91 at 2026-10-05 22:37:09, and `~/.cache/copilot/pkg/linux-x64/1.0.92` appeared 24 s later (the operator's own CLI auto-updating). A 1.0.92 pin would refuse every harness run at the version row, so the pin stays 1.0.91 (deviation from the brief, not from D-C3(b)). A differential check of the 1.0.92 package found no pinned fact changed (design, Facts at 1.0.91, "The version"); the bump is one constant once the package ships 1.0.92.
  - **Check the package.** The agent runs `pacman -Q github-copilot-cli-bin` and records the version.
  - **Check the binary.** The agent creates a scratch directory outside the repository with `mktemp -d`, then runs:

    ```sh
    unshare -rn env -i PATH="$PATH" HOME=<scratch>/home COPILOT_HOME=<scratch>/copilot-home \
      COPILOT_CACHE_HOME=<scratch>/cache COPILOT_AUTO_UPDATE=false copilot --version
    ```

    That unpacks the package into `<scratch>/cache`. The agent never runs this with the real `HOME` or `~/.copilot`.
  - **Pass:** both read 1.0.91.
  - **On another version:** stop, and relay to the user that the exact pin needs a revision of D-C3 through `openspec-update-change`.
- [x] 1.2 The V-pass, run by the agent locally with no network.
  - *Done 2026-10-06.* Recorded as "Facts at 1.0.91" in `design.md` (Context). Every row cites 1.0.91 by byte offset, string, schema definition, help line or an offline `skill list`/`mcp list` measurement (no token, `unshare -rn`, scratch homes), or says what is absent at 1.0.91. The deny-list path follows the package: `sandbox.userPolicy.filesystem.deniedPaths` (`runtime.node` 7851854); the docs' `sandbox.userPolicy.deniedPaths` occurs nowhere in the package. The scratch directory is deleted. It reads the files under `<scratch>/cache/pkg/linux-x64/1.0.91/`: `app.js`, the `runtime.node` strings and `schemas/`. It also reads the output of `--help` and `copilot help <topic>`, each run as in 1.1. It re-derives the following at 1.0.91, with a byte offset, a string or a help line for each:
  - **Streams.**
    - the stdout filter set and the `result` writer;
    - the `session.shutdown`, `skill.invoked` and `session.model_change` fields;
    - the event that reports an effort as left unapplied;
    - the sandbox-active and sandbox-ignored events, and the warning text.
  - **Flags.**
    - the hidden flags `--headless`, `--stdio`, `--no-auto-login` and `--sandbox`;
    - every flag of design Decision 8;
    - what `--no-custom-instructions` disables.
  - **Status RPC.**
    - the method names, the handshake, and the endpoints those methods call;
    - the `copilotUser.quota_snapshots` fields, the `EZ` coercion equivalent, the snapshot selection, and the `total_nano_aiu` default;
    - the `session.error` types and codes, `session_limits` and `ai_credit_soft_cap_exhausted` among them.
  - **Tools and skills.**
    - the tool names of design Decision 10;
    - the parent-folder skill walk, the `COPILOT_HOME` gate on `~/.agents/skills`, the bundled skill names, and the built-in MCP server names.
  - **Configuration and process.**
    - every settings key of `pinned_settings`, with `sandbox.allowBypass`, `sandbox.allowDevToolAccess` and `sandbox.auth` defaults;
    - **the exact settings path of the deny list.** Derive it from the `runtime.node` strings and the settings schema at 1.0.91, never from the docs: at 1.0.67 the package names only `sandbox.userPolicy.filesystem.deniedPaths`, while the docs say `sandbox.userPolicy.deniedPaths` (design Decision 3). Record both readings; the pinned block follows the package;
    - **every tool the Linux sandbox needs** on `PATH` (at 1.0.83: `bwrap`, `slirp4netns`, `nsenter`, `iptables`, `ip6tables`, `iptables-restore`, `ip6tables-restore`), which becomes `SANDBOX_TOOLS`;
    - **a model-free way to check confinement:** whether the headless server's `session.shell.exec` or `shell.executeUserRequested` runs a command inside the session's sandbox without a model call, and whether any call returns the session's resolved sandbox policy;
    - whether the client's own tools (`grep`, `glob`, the bundled `rg`) run inside the sandbox and read the package cache;
    - the managed-settings path;
    - the signal handlers;
    - the variables the shell tool exports, which become the Copilot agent markers.

  Record the results as a "Facts at 1.0.91" table in `design.md` (Context), through the `openspec-update-change` skill. Pass: every row cites 1.0.91, or says "absent at 1.0.91". Delete the scratch directory afterwards.
- [x] 1.3 Compare the V-pass with the 1.0.67 facts the spec and design rely on.
  - *Done 2026-10-06.* No rule changed at 1.0.91, and none of D-C1–D-C4 (design, "Rule changes at 1.0.91"). The confinement probe stays: `session.shell.executeUserRequested` is a model-free shell call, and every completion reports `sandboxed`, which the probe now requires per command (fail-closed). Constants and readings changed: `--reasoning-effort` for `--effort`; `SANDBOX_TOOLS` gains `unshare`; `BUILTIN_SKILLS` = `customize-cloud-agent`, `github-pr-media`; `BUILTIN_MCP` = `github-mcp-server`, `githubiq`; the managed paths add `/etc/github-copilot/policy.d`; the sandbox warning texts; the sandbox-active report is `tool.execution_complete.sandboxed`. Spec wording only: "bundled skills" (plural), and the Sandbox paragraph's rationale now says the pinned version fails sandboxed commands where earlier versions ran them unconfined. For the user: the reply may omit `overage_entitlement` (every run then refuses until K2 shows it), and a `python3` under the account home fails the probe's skill rows (design, Risks). `openspec validate add-copilot-dev-runner --strict` passes.
  - If any change alters a rule, revise the change through `openspec-update-change` before section 2. Relay the change to the user when it touches D-C1–D-C4.
  - In particular: if 1.2 finds no model-free call that runs inside the session's sandbox, remove the confinement probe from the spec and design through `openspec-update-change`, move it back to `record-copilot-streams`, and tell the user that P2's go will then rest on the after-run checks alone. If the client's own tools need the package cache inside the sandbox, revise the deny list the same way.
  - Otherwise, record "no rule changed at 1.0.91" in `design.md`.

  Verify with `openspec validate add-copilot-dev-runner --strict`.

## 2. Fixtures

- [x] 2.1 Create `tests/unit/data/copilot_streams/` with synthetic saved event lists.
  - *Done 2026-10-06.* All 51 files listed below exist; `README.md` has one row per file (checked by diffing the file list against the table), each "synthetic, from @github/copilot 1.0.91 `<source>`". Fake tokens are `github_pat_SYNTHETIC_TEST_ONLY` and `github_pat_FIXTURE_REPLY_ONLY`; models `copilot-fixture-a`/`-b` (plus `-c`, `-d` in `models.json` for the disabled and unconfigured policies). `test_model_ids.py` is green with no allowlist entry. Each list holds stdout events plus reduced `copilot.*` records, derived from the 1.0.91 V-pass. Model names are `copilot-fixture-a` (requested) and `copilot-fixture-b` (other). Files:
  - **Runs:** `success.jsonl` (a `skill` call naming `proposal-check`, a `skill.invoked` with source `project`, a shutdown under the cap, the sandbox-active event) and `exit0-error.jsonl` (a `model_call` session error with exit 0).
  - **Skills and tools:** `skill-failed.jsonl`, `skill-file-view.jsonl`, `helper-spawn.jsonl` (a `task` call carrying the verifier brief, `subagent.started`, and `modelMetrics` naming both models), `unknown-tool.jsonl`.
  - **Isolation:** `mcp-call.jsonl`, `mcp-connected.jsonl`, `foreign-skill.jsonl` (source `inherited`), `skills-unreported.jsonl`, `hook-event.jsonl`, `sandbox-ignored.jsonl`, `sandbox-unreported.jsonl`.
  - **Model and effort:** `model-differs.jsonl`, `model-switch.jsonl` (`rate_limit_auto_switch`), `effort-unapplied.jsonl`.
  - **Errors and limits:** `auth-error.jsonl`, `quota-error.jsonl`, `soft-cap.jsonl`, `session-limits.jsonl`.
  - **Consumption:** `over-cap.jsonl` (more than twice a 30-credit cap), `zero-nano.jsonl`.
  - **Missing records:** `no-result.jsonl`, `no-shutdown.jsonl`.
  - **Token leak:** `token-in-output.jsonl`, whose events and stderr carry the synthetic token's value.

  Raw inputs:
  - **Session file:** `events-raw.jsonl`, a session events file carrying `system.message` and extra fields the reduction must drop.
  - **Status replies.** Every reply carries fake `login`, `organization_list` and `token` fields, which the parse must drop:
    - `status-ok.json` (`premium_interactions`, permission false, entitlement 0, count 0, 80 % remaining, token-based billing);
    - `status-no-overage-field.json`, `status-no-entitlement-field.json`, `status-budget.json`, `status-entitlement.json`, `status-overage-drawn.json`;
    - `status-legacy.json`, `status-low.json`, `status-free-chat.json`;
    - `status-no-user.json`, `status-auth-error.json`, `status-gh-cli.json`, `status-enterprise.json`, `status-error.json`;
    - `models.json`.
  - **Rosters:** `skills-ok.json`, `skills-extra.json`, `mcp-ok.json` and `mcp-extra.json`.
  - **Confinement probe results:** `probe-ok.json`, `probe-token-readable.json`, `probe-environ-readable.json`, `probe-gh-token.json`, `probe-git-credential.json` and `probe-skill-fails.json`.

  Write `README.md` with one row per file, following `../claude_cli_streams/README.md`: "synthetic, from @github/copilot 1.0.91 `<source file>`", and what it pins. Verify that `uv run pytest tests/unit/test_model_ids.py` stays green with no allowlist entry.

## 3. Failing tests first

- [x] 3.1 The record and the home, in `tests/unit/test_host_login.py`, as a new Copilot section. Cases:
  - *Done 2026-10-06.* Section "the Copilot record and home": default path and token file, the location guard for every record (`~/.copilot`, `~/.config/github-copilot`, inherited `COPILOT_HOME`), a refused override that starts no child and creates nothing, the deny list from a patched password entry and uid (with `$HOME` pointed elsewhere), a state root inside the account home, `check_copilot_home` (settings key path, `config.json` key, each forbidden entry, every allowed entry), the login note and the unchanged Claude/Codex records. The seed-before-prompt order is pinned in the CLI section (`test_the_copilot_login_writes_the_token_file_beside_the_home`). Applies to 3.1–3.7: tests and code landed together across two sessions, so the red-before-green step was not reproduced for every case; the boxes were ticked without it.
  - *Red checks, 2026-10-06 (review follow-up), applying to 3.1–3.7.* The security-relevant cases were shown to fail, each by mutating the guarded line in the working tree, running the guarding tests, and restoring the line (`grep -n MUTATION` empty afterwards); no real `copilot` ran (the sentinel run kept `Popen` patched):
    - the pre-spawn assertion removed from `start`: the three `test_a_leaking_builder_starts_no_process` cases and `test_run_env_adding_a_token_variable_still_fires_the_assertion` fail;
    - `scrub_tree` made a no-op: `test_scrub_tree_rewrites_workspace_files`, `test_a_token_in_the_output_is_scrubbed_and_stops`, the end-to-end `test_a_leaked_token_reaches_no_summary_no_kept_file_and_no_judge` and the new fail-closed test fail; `scrub` made a no-op: the two scrub unit tests and both end-to-end scrub tests fail;
    - no probe target counted as reached: all five isolation cases of `test_probe_problem_refuses_naming_the_target` fail; the per-command `sandboxed` flag ignored: `test_probe_problem_passes_a_clean_probe_and_refuses_unsandboxed_or_missing` fails;
    - the conftest sentinel removed: `test_an_unpatched_run_or_status_read_raises_rather_than_spawns` fails (it reaches the patched `Popen` instead of the sentinel);
    - a new snapshot dropping the stop: `test_the_status_snapshot_holds_no_secret` and the damaged-record cases fail.

    The review follow-up's own new cases were written first and failed against the code before their fix (31 failures, each for its stated reason, e.g. the recorded-stop test showing `[fake-copilot.py, --version]` in `Popen`). The remaining cases of 3.1–3.7 stay ticked without a red step.
  - **Location.**
    - The default path is `…/hosts/copilot`, and the token file is `…/hosts/copilot.token`, beside it.
    - The location refuses `~/.copilot`, `~/.config/github-copilot` and an inherited `COPILOT_HOME`, for every record.
    - A refused state-directory override starts no child (`Popen` records nothing) and leaves the override's directory without a `cache/` or any other new entry: the location check runs before `copilot --version`.
  - **Seeding.**
    - `pinned_settings(home, account_home)` writes the deny list by construction from a patched `pwd` entry and uid, not from `$HOME`: the account home, `/run/user/<uid>`, the state root when it lies outside the account home, and the token file.
    - The sandbox block carries `allowBypass: false`, `allowDevToolAccess: false` and `auth.git`/`auth.gh` false, and puts the deny list at the path task 1.2 fixed.
    - The seed comes before the token prompt (record the call order).
  - **`check_copilot_home`.**
    - It names a differing settings key path.
    - It names a `config.json` key outside `MANAGED_STATE_KEYS`.
    - It names a `copilot-instructions.md`, `skills/`, `mcp-config.json`, `pkg/` and a token file inside the home, and a non-empty `session-state/` or `gh/`.
    - It lets every allow-listed entry pass.
  - **Login note.** `NOTES["copilot"]` renders "Your own Copilot login is not affected." for every remedy.
  - **Unchanged sections.** The Claude and Codex sections pass unmodified.

  Verify that the new cases fail before the change.
- [x] 3.2 The token-file commands, in the CLI section of `test_host_login.py`. `getpass.getpass` is patched; no real `copilot` runs. Cases:
  - *Done 2026-10-06.* In `tests/unit/test_host_login_cli.py` (the repository's CLI test file), section "the Copilot token-file commands", with a fake status read that records the token it got and whether the run lock was held. Added this session: a missing sandbox tool makes the login (and the status command) exit 3 naming the tool, because the login reports ready only when the read passes the preflight (`copilot_cli.machine_problem`: managed settings and sandbox tools).
  - **Login.**
    - It refuses without a terminal, and with an agent marker.
    - It refuses `ghp_…`, and any prefix other than `github_pat_`, before writing anything; the message echoes no part of the value.
    - It writes the token file beside the home, at 0600 with `O_EXCL`, and nothing inside the home holds the token.
    - It records the approval stop, and a following live run is refused before any `Popen`, naming the approval stop and the `--clear-stop` remedy.
    - No client login argv runs.
    - The synthetic token appears in no `capsys` output.
    - It exits 0 with a fake `status-ok.json` despite the approval stop it recorded, and 3 with `status-auth-error.json`.
  - **`--reset`.** It deletes the token file, wipes the marked home, reseeds it, prompts again and records a new approval stop.
  - **`--clear-stop`.** It carries the same speed bumps, takes the lock, removes the `stop` entry from `quota.json` whatever its kind (billing, isolation, approval), and leaves the token file and settings untouched.
  - **Logout.** It unlinks only the token file, prints the revocation page, runs no client logout, and carries no caveat.
  - **Status.**
    - It prints exactly the keys of design Decision 6, `overage_count` and the stop's kind among them. `--models` adds the model rows. `--no-token` runs the read in the same environment less `COPILOT_GITHUB_TOKEN` (the fake records the names it received) and prints `logged_in: no` with a fake that sees no token.
    - A recorded stop of any kind does not refuse the status command.
    - No login name, organization or token from the fake reply appears.
    - The status read holds the run lock.

  Verify that the cases fail before the change.
- [x] 3.3 The environment and the pre-spawn assertion, in a new `tests/unit/test_copilot_cli.py` and in `tests/unit/test_isolated_env.py`. Cases:
  - *Done 2026-10-06.* Added this session: the end-to-end `scrub` case through `claude_runner.main` (`test_a_leaked_token_reaches_no_summary_no_kept_file_and_no_judge`): a fake child prints the token on stdout and stderr and writes it into the draft; the summary line, the printed output, every file of the kept workspace and the judge prompts of a later `--rejudge` carry no part of it, the run exits 3 for isolation and records an isolation stop.
  - **The built environment.** `allowlisted_env(COPILOT, home, environ)` plus `copilot_cli.run_env(env, scratch)` plus `token_env`. `COPILOT.child_vars(home)` keeps change 3's signature, and the `CLAUDE` and `CODEX` records and `allowlisted_env`/`login_env` are called exactly as before:
    - `HOME`, `XDG_*` and `XDG_RUNTIME_DIR` point to scratch, set by `run_env`, not by `child_vars`;
    - `DBUS_SESSION_BUS_ADDRESS` is `disabled:` and `GH_CONFIG_DIR` is the empty `<home>/gh`;
    - `COPILOT_HOME`, `COPILOT_CACHE_HOME` and `COPILOT_AUTO_UPDATE=false` are set, and `TERM=dumb` and `NO_COLOR=1`;
    - `CLAUDE_CODE_OAUTH_TOKEN` is dropped;
    - `ignored_env` names `GH_TOKEN`, `GITHUB_TOKEN`, `COPILOT_PROVIDER_BASE_URL`, `OTEL_EXPORTER_OTLP_ENDPOINT`, `BASH_ENV` and `SSH_AUTH_SOCK`, by name only.
  - **The assertion.** With `Popen` recording calls:
    - a builder monkeypatched to leak `GH_TOKEN`, then `COPILOT_PROVIDER_BASE_URL`, then `XYZ=github_pat_…`, starts no process;
    - `run_env` patched to add `GITHUB_TOKEN` still fires the assertion;
    - the record's names plus the token pass.
  - **Isolation of the token.**
    - The builder's own output for `COPILOT` carries no token.
    - The judge child's and its login check's environment carries neither `COPILOT_GITHUB_TOKEN` nor the synthetic value.
  - **`scrub`.** Over `token-in-output.jsonl` and a stderr carrying the synthetic token, the saved events, the `RunnerFailure` text, the printed summary and the judge's recorded input carry no part of the value; the run is untested for isolation and an isolation stop is recorded. A stream without the value passes unchanged.

  Verify that the cases fail before the change.
- [x] 3.4 The status read and the billing guard, in `test_copilot_cli.py`. Cases:
  - *Done 2026-10-06.* Every listed case, including the end-to-end "read after the run unavailable" against a fake headless server that answers once.
  - *Review follow-up, 2026-10-06.* "Before any `Popen`" was not measured: the stop tests stubbed `installed_version`, and the stop row ran after `copilot --version`. The stop row now precedes the version row (design Decision 6), and the tests run against the fake client with a recording `Popen` and the fake's own call log (`test_a_recorded_stop_refuses_the_next_run_before_any_child`; in the CLI file, `test_after_a_login_a_live_run_waits_for_the_approval` puts the real version read back, so a spawn would hit the sentinel). Added: a stop recorded, or the token replaced, while the run waited on the lock refuses it, or reaches every child, under the lock (`test_a_stop_recorded_while_the_run_waited_on_the_lock_refuses_it`, `test_the_token_is_read_under_the_lock`); a damaged `quota.json` refuses as a billing stop and survives a new snapshot until `--clear-stop`; a shutdown without a readable `totalNanoAiu` is untested with a billing stop and null credits; the soft-cap and limit results read in the refusal template, and the soft-cap stop names the cap and the credits used; a read after the run that raises, and any after-run step that raises, still record a billing stop (the latter after scrubbing the workspace); `Rpc` answers into a closed stream without raising.
  - **`parse_status`.** It keeps exactly the listed values, and no fake login, organization or token survives it.
  - **`choose_snapshot`.** It picks `chat` for `status-free-chat.json`.
  - **`status_problem`.** Each `status-*.json` gives the spec's outcome and remedy: the missing overage field, the missing entitlement field, the budget, the entitlement, the drawn overage, legacy billing, low quota, no user, auth errors, `gh-cli`, enterprise, and error.
  - **`read_status` timeout.** Against a fake server that never answers, the read is unavailable after a patched `STATUS_TIMEOUT_S`, and the child is stopped.
  - **`quota.json`.** It holds only the listed values.
  - **`billing_after`.** It flags and stops on: overage grew, `after=None` (the read after the run unavailable, also driven end to end with a fake server that answers before the run and not after), `over-cap`, `zero-nano`, `no-shutdown`, `soft-cap` and `session-limits`. `quota-error` is untested without a stop.
  - **The stops.** `record_stop` of each kind (billing, isolation, approval) makes the next preflight refuse with that kind's remedy, before any `Popen`, and maps to its untested reason (subscription, isolation, precondition). `--preflight-only` prints the stop and is not refused by it.
  - **The credit cap.** A missing `--max-ai-credits`, or one below 30, is a usage error.

  Verify that the cases fail before the change.
- [x] 3.5 The command, the scan, the rosters and the sandbox, in `test_copilot_cli.py`. Cases:
  - *Done 2026-10-06.* Added this session: `test_the_rosters_and_the_probe_run_under_the_run_lock` (each listing and the probe find the lock held). Choice recorded: the checks before the lock run location, marker and mode, the clean home, the token, then `--version` (design Decision 6 lists the version third): every Copilot child carries the token, and nothing spawns before location, marker and mode pass, which the test pins. *Superseded 2026-10-06 (review follow-up):* the recorded stop now sits between the token and `--version`, and design Decision 6 lists the order as built.
  - *Review follow-up, 2026-10-06.* `SKILL_HOSTS`: the test also accepts the hosts of `NOT_CONTACTED`, which is now recorded in design Decision 8 with its rule (a host no request reaches, with its reason). The probe gains a `harness_environ` row (design Decision 13), with `probe-harness-environ-readable.json`; the fake client tells the two `/proc/<pid>/environ` commands apart by its own pid and its parent's, so a wrong pid leaves the row unanswered. `--preflight-only` now goes on past refused stop, sandbox-tools, status, model and roster rows and ends at the rows that make a later start unsafe (`test_preflight_only_goes_on_past_rows_that_leave_the_later_reads_safe`, `test_preflight_only_ends_at_a_row_that_makes_a_later_start_unsafe`; design Decision 7, spec Scope). The sandbox finding no longer exempts a run a session error ended without a shell call (`test_a_run_with_no_shell_call_records_an_isolation_stop_whatever_ended_it`; design Decision 13).
  - **`command()`.** Table-test it over every `SCENARIOS` entry against design Decision 8:
    - the task tools appear only with `helpers`;
    - `web_fetch` and `--allow-url` appear only when `needs_network` holds;
    - the URL hosts are those of `url_hosts`;
    - it never carries `--allow-all-urls`, `--add-dir`, `--plugin-dir`, `--allow-all-paths`, `--enable-memory`, `--share`, `--agent`, `--resume` or `--continue`;
    - it always carries `--no-auto-login`, `--sandbox`, `--secret-env-vars=COPILOT_GITHUB_TOKEN` and `--max-ai-credits`;
    - `--effort` appears only when requested.
  - **`SKILL_HOSTS`.** Every `https?://host` found in `skills/proposal-{import,lit-search,reverse}/scripts/` appears in the table.
  - **`scan_parents`.** It reports each listed file at a parent level and at the workspace level, and a workspace under the real home or the repository. The staged `.agents/skills` passes.
  - **`roster_problem`.** It names the extra skill in `skills-extra.json` and the extra server in `mcp-extra.json`; the `-ok` files pass.
  - **Sandbox.** A patched `sys.platform == "win32"` is a usage error. For each tool of `SANDBOX_TOOLS` in turn, a patched `which` that misses that tool is untested (precondition) with a remedy naming it. `sandbox-ignored` and `sandbox-unreported` are untested for isolation and record an isolation stop.
  - **`probe_problem`.** `probe-ok.json` passes. `probe-token-readable`, `probe-environ-readable`, `probe-gh-token` and `probe-git-credential` refuse for isolation, naming the target; `probe-skill-fails` refuses as a precondition. No refusal carries any probe output. Against the fake headless server, the probe's session folder is deleted afterwards.
  - **Preflight order.** With a recording `spawn`, nothing is spawned before the location, marker and mode checks pass, and the confinement probe runs after the rosters, under the lock.
  - **Prompts.** No `SCENARIOS` prompt contains `/proposal-`.

  Verify that the cases fail before the change.
- [x] 3.6 The readers, in `test_copilot_cli.py` and `tests/unit/test_routing.py`. Cases:
  - *Done 2026-10-06.* Added this session: the `result` line's session is cross-checked against the harness-chosen `--session-id` (design Decision 9, step 4); another session is a runner failure (`session_problem`).
  - *Review follow-up, 2026-10-06.* The two cross-checks design Decision 10 names were missing although 4.2 was ticked; both are now findings, untested for a precondition: a `task` call and `subagent.started` that do not pair up by `toolCallId` (`helper_after`, `test_each_task_call_is_cross_checked_with_its_subagent`), and a session CLI version other than the pinned one (`version_after`, `test_the_session_version_is_cross_checked_with_the_pinned_one`). `token_present` in `host-status copilot` now follows the token file's state rather than a word in the refusal's cause (`test_the_token_line_follows_the_token_file_not_the_wording_of_its_cause`).
  - **`copilot_tool_calls`.** It covers every row of design Decision 10. `skill-failed` is an attempt, not a `Skill` call. `skill-file-view` is a `Read` flagged `skill_file_read`. `unknown-tool` is untested.
  - **Through `routing.tool_calls`:**
    - `route_from_events(success)` returns `proposal-check`;
    - `verdict_supervise_verifier` passes on `helper-spawn`;
    - `verdict_single_context(…, 0)` fails naming `Agent`;
    - Claude and Codex streams give the same calls as before.
  - **`copilot_read`:**
    - `final_text` is the last top-level message, and the model set comes from messages and `modelMetrics`;
    - creation options are never evidence: a stream with no model reads "unreported", and the effort reads "requested, not verified";
    - credits come from `totalNanoAiu / 1e9`, `cost_usd is None`, and the notional basis is labelled.
  - **`reduce_session`.** Over `events-raw.jsonl`, it drops `system.message` and the extra fields.
  - **Untested outcomes.**
    - `isolation_after`: `foreign-skill`, `skills-unreported`, `mcp-call`, `mcp-connected` and `hook-event`.
    - `model-differs`, `model-switch` and `effort-unapplied` are untested for a precondition reason. `helper-spawn`'s second model does not make the run untested.
  - **The exit mapping:**
    - `auth-error` names the PAT remedy and the not-affected note;
    - `exit0-error` follows the event, not the exit code;
    - `no-result` is a runner failure;
    - `no-shutdown` is a runner failure, exit 4 and never 3, and it records a billing stop;
    - `token-in-output` exits 3 for isolation and records an isolation stop.

  Verify that the cases fail before the change.
- [x] 3.7 The host seam and the CLI, in `tests/unit/test_hosts.py` and `tests/unit/test_dev_runner_probe.py`. Cases:
  - *Done 2026-10-06.* All in `test_hosts.py` (`test_dev_runner_probe.py` only takes the shared `CLEAN_DRAFT` from `tests/helpers.py` now). The autouse sentinel lives in `tests/conftest.py`, the repository's one conftest (there is no `tests/unit/conftest.py`); its existing `_harness_login_offline` already points `THESIS_PROPOSAL_DEV_STATE` at a temporary directory for every test. Added this session: `--summary-log logs/evals/x.jsonl` among the usage errors, and a held lock or a refused child environment under `--preflight-only` exits 3, not 4. Choice recorded: the Windows refusal is the last Copilot usage rule (so every other usage error reads the same on every platform, as the `fcntl` rule's comment asks) and exempts `--rejudge`, which starts no Copilot process; the Windows CI job runs `test-fast`, and the tests that need locks or a fake child skip there.
  - *Review follow-up, 2026-10-06.* `--preflight-only` with `--rejudge` (which made a judge call), `--judge` or `--keep` is now a usage error (three more cases of `test_copilot_usage_errors_stage_nothing_and_start_nothing`). The synthetic token, the stream and reply loaders (`tests/helpers.py`) and the seeded Copilot home with its account home (`copilot_home`, `copilot_account` in `tests/conftest.py`) are shared instead of repeated in four files.
  - **Usage errors** (exit 2: nothing staged, no process started) for:
    - `--host copilot` without `--model`, with `auto`, or with a model containing `/`;
    - no `--max-ai-credits`, or 29;
    - `--max-budget-usd`;
    - an install scenario;
    - a patched Windows platform;
    - `--preflight-only` on another host;
    - `--summary-log logs/evals/x.jsonl`.
  - **End to end,** with `copilot_cli.run_copilot` faked to return `success.jsonl`. The summary carries:
    - `host: copilot` and the label "dev-runner (copilot), not comparable to matrix";
    - `config: isolated`, the Copilot home as `config_dir` and `login: harness`;
    - `cost_usd: null`, the credits, the cap, and the overage and remaining values before and after.
  - **The judge pin.** Change 3's L0 pin is extended to a fake Copilot run: the judge's configuration links the Claude harness login, and neither the Copilot home nor `COPILOT_GITHUB_TOKEN` reaches the judge.
  - **`--rejudge --host copilot`** reads through `copilot_read` and starts no Copilot process.
  - **Untested preconditions.** `RunLockBusy`, a version other than 1.0.91, a missing sandbox tool, a model listed under a policy other than enabled, the approval stop, `model-differs` and `effort-unapplied` exit 3, never 4.
  - **`--preflight-only`** starts no `-p` child, leaves no new `session-state/` entry, and prints a recorded approval stop without being refused by it.
  - **No real `copilot` in any test.** An autouse fixture in `tests/unit/conftest.py` points `copilot_cli`'s binary seam at a sentinel that raises, and sets `THESIS_PROPOSAL_DEV_STATE` to a `tmp_path` directory (design Decision 14). A test calling an unpatched `run_copilot` or `read_status` gets the sentinel's error, and `Popen` records nothing. Existing tests that rely on the default or another state directory set or remove the variable themselves, and the Claude and Codex suites stay green.

  Verify that the cases fail before the change.

## 4. Implementation

- [x] 4.1 In `harness/host_login.py`:
  - *Done 2026-10-06.* `HostLogin` gains `credential`, `token_env`, and, with the same leave-Claude-and-Codex-unchanged defaults, `strip_names` (`BASH_ENV`, `SSH_AUTH_SOCK`), `home_env` (Copilot's `COPILOT_CACHE_HOME` and `GH_CONFIG_DIR`, so `child_vars(home)` keeps its signature) and `dynamic_seed` (the settings carry absolute deny paths). `COPILOT`'s `login_argv`/`status_argv`/`logout_argv` are empty tuples rather than `None` (the field type), and `main` dispatches on `credential`. The token file is created with `touch(mode=0o600, exist_ok=False)` (`os.open` with `O_CREAT|O_EXCL`, mode 0600) and then written as bytes: a direct `os.open` call trips the repository's text-encoding scan in `test_repo_conventions.py`. `run_lock` takes `record=` for its message. Verified: ruff clean (no C901); `grep -n "copilot.token\|token_path" harness/*.py` shows the one read in `copilot_cli.token_env`, the write and deletes in the login and the logout, and path uses in the deny list and the probe's target; the Claude and Codex sections are green.
  - add the `HostLogin` fields `credential` and `token_env`, with defaults that keep `CLAUDE` and `CODEX` unchanged. `child_vars` keeps change 3's signature `child_vars(home)`;
  - add `COPILOT` (whose `child_vars(home)` holds only home-derived and constant variables, design Decision 5), `token_path`, `pinned_settings`, `account_home`, `MANAGED_STATE_KEYS` and `check_copilot_home`, and extend `check_location`;
  - add the token-file branches of `main`: login (with `--reset` and `--clear-stop`, and the approval stop), logout, and status with `--models` and `--no-token`. Each imports `copilot_cli` lazily;
  - add `NOTES["copilot"]` and `RECORDS["copilot"]`.

  Verify that 3.1 and 3.2 pass, that `uv run ruff check harness/host_login.py` reports no C901, that `grep -n "copilot.token\|token_path" harness/*.py` shows reads only in the login, the logout and `token_env`, and that the Claude and Codex sections stay green.
- [x] 4.2 Create `harness/copilot_cli.py`, stdlib-only, importing `host_login` only. It holds:
  - *Done 2026-10-06.* Stdlib-only; it imports `host_login` and the shape module `hosts` (for `RunView` and `needs_network`, which moved from `codex_cli` to `hosts` so both hosts share one predicate; `codex_cli` imports it from there, and since the review follow-up no longer re-exports `NETWORK_SKILLS`, which nothing read). Names as listed, with `spawn` built on `start` (the single `Popen`), the preflight split into `preflight_checks` (before the lock) and `gate_checks` (status, model, rosters, probe under the lock), `assess` combining the after-run findings, `machine_problem` for the status command, and `session_problem` for the result line's session. `uv run ruff check harness/copilot_cli.py` is clean.
  - **Constants:** `COPILOT_PINNED_VERSION`, `STATUS_TIMEOUT_S`, `BUILTIN_SKILLS`, `BUILTIN_MCP`, `SANDBOX_TOOLS` and `SKILL_HOSTS`, and the binary seam the conftest sentinel patches.
  - **Environment:** `run_env` (scratch `HOME` and XDG variables), `token_env`, `scrub`, `ignored_env`, `assert_copilot_env` and `spawn`.
  - **Status:** `read_status`, `parse_status`, `choose_snapshot` and `status_problem`.
  - **Preflight:** `scan_parents`, `roster_problem`, `sandbox_problem`, `confinement_probe`, `probe_problem` and `preflight`, in design Decision 6's order.
  - **Command and readers:** `url_hosts`, `command`, `reduce_session`, `copilot_tool_calls`, `copilot_read`, `isolation_after`, `billing_after`, `failure_reason` and `record_stop(home, kind, cause)`.
  - **Run:** `run_copilot`, which takes the lock; then the preflight and the read before; the spawn with `pass_fds` and the parent-death signal; the capture, `scrub` and reduction; the read after; the prune; and the release.
  - **`main(argv)`** with the `run-env` subcommand (design Decision 15).

  Findings are frozen dataclasses, and failure and status tables are data, so complexity stays at 12 or below. Verify that 3.3 to 3.6 pass and that `uv run ruff check harness/copilot_cli.py` is clean.
- [x] 4.3 Wire the host in. In `harness/claude_runner.py`:
  - *Done 2026-10-06.* `HOSTS["copilot"]`, `--max-ai-credits`, `--preflight-only` (`copilot_preflight_only`), the usage rules (`_host_rules` shared with Codex, `_copilot_rules`), and the mapping of `CopilotRefused`, `RunLockRefused`, `CopilotRunFailed` and `RunProblem` to untested or runner failure; `routing.tool_calls` appends `copilot_cli.copilot_tool_calls`. The listed suites are green.
  - add the `copilot` entry of `HOSTS`, `--host copilot`, `--max-ai-credits` and `--preflight-only`;
  - add the usage guards of task 3.7;
  - map the Copilot findings to the three untested reasons and the runner-failure status (design Decision 11).

  In `harness/routing.py`, make `tool_calls` append `copilot_cli.copilot_tool_calls(events)`. Verify that 3.7 passes, and that `test_dev_runner_probe.py`, `test_routing.py`, `test_install_probe.py`, `test_isolated_env.py`, `test_codex_cli.py` and `test_hosts.py` stay green.
- [x] 4.4 Update the module docstrings and usage lines of `claude_runner.py`, `copilot_cli.py`, `hosts.py` and `host_login.py`:
  - *Done 2026-10-06.* Read in the diff; the slug grep on `copilot_cli.py` is empty. the Copilot host, the token file, the billing guard and stop, the sandbox, and the not-comparable label. Verify by reading the diff. Confirm with `grep -nE 'gpt-[0-9]|claude-(haiku|sonnet|opus)-[0-9]' harness/copilot_cli.py` (empty) that no model slug entered the code.

## 5. Documentation

- [x] 5.1 Update `harness/README.md`:
  - *Done 2026-10-06.* New section "Copilot dev runner (real Copilot CLI, included AI credits)", a "Which path to use" row, and the Known-limitations line. Caps: 30 for a cheap model or a short check, about 40 for a sonnet-class model (a typical run ≈ 37 credits), 80 or more for an opus-class model or a supervise scenario. Status lines for the V-pass (done) and K1–K7 (pending). `uv run poe test` is green.
  - **A new "Copilot dev runner" section:**
    - dev loop only, with the label, never fed to `report.py`;
    - the one-time setup, with the exact USER ACTIONS of section 7;
    - the home, the token file beside it (`<state>/hosts/copilot.token`, not inside the home), and where the token must never live (not in `.env`, and never under `COPILOT_GITHUB_TOKEN`, `GH_TOKEN` or `GITHUB_TOKEN` in a shell file);
    - the run lock;
    - the sandbox posture: the deny list built by construction, the confinement probe before every run, `scrub`, and the residual risk until K6 passes;
    - the billing guard, each refusal's remedy, and the three kinds of stop (billing, isolation, approval) with `--clear-stop`; clearing the approval stop is the go for the first run after a login;
    - suggested credit caps per model class, with roughly 37 credits for a typical sonnet-class run. They live in the README, not in code;
    - the Claude judge;
    - what is out of scope;
    - "verified on Linux only";
    - status lines for the V-pass and K1–K7.
  - **"Which path to use"** gains a Copilot row.
  - **"Known limitations"** names Copilot beside Claude and Codex, with the synthetic-fixture note until `record-copilot-streams`.

  Verify that `uv run poe test` stays green, since some README text is pinned.
- [x] 5.2 Update the `AGENTS.md` Commands block:
  - *Done 2026-10-06.* The four lines and the approval-stop sentence, read in the diff; `uv run poe test` is green.
  - `uv run poe dev <scenario> --host copilot --model <id> --max-ai-credits <N>` (included credits; never a matrix input);
  - `uv run poe host-login copilot [--reset | --clear-stop]` (the user only);
  - `uv run poe host-status copilot [--models | --no-token]` (agents may run it; no model call);
  - `uv run poe host-logout copilot` (the user only).

  Add one sentence: every Copilot login records an approval stop, and only the user clears it, from a terminal, which is the explicit go for the next model call; agents never read the token file, `/proc/<pid>/environ` of a Copilot child, or `ps e` output while one runs. Verify by reading the diff and with `uv run poe test`.

## 6. Gate

- [x] 6.1 Run `uv run poe test` (not `test-fast`) and confirm it is green: pytest, ruff with the full rule set, `test_repo_conventions.py`, the drift check and conform.
  - *Done 2026-10-06.* 3403 passed, 2 skipped; ruff clean; generated copies in sync; all 11 skills conform.
- [x] 6.2 Run `uv run poe cov` and confirm that the 78 % floor holds with `copilot_cli.py` counted.
  - *Done 2026-10-06.* Total 92.35 %; `copilot_cli.py` 96 %, `host_login.py` 95 %, `claude_runner.py` 93 %.
- [x] 6.3 Run `uv run poe specs` and `openspec validate add-copilot-dev-runner --strict`, and confirm both pass.
  - *Done 2026-10-06.* 20/20 specs valid; the change is valid with only the allowed INFO line ("Archive would refuse … Dev-runner host adapters … not found", until change 3 is archived).

## 7. Account setup and the $0 live checks (no model call)

- [ ] 7.1 **USER ACTION:** at github.com/settings/copilot, confirm that the account's Copilot plan is the free Copilot Pro for verified teachers (D-C1). Answer yes or no here. On "no", stop: D-C1 reopens with the user.
  - *2026-10-06: pending: user action.* The workflow brief reports the teacher academic plan (free Copilot Pro); the user's own answer goes here.
- [ ] 7.2 **USER ACTION** at github.com/settings/billing, under "Budgets and alerts":
  - *2026-10-06: pending: user action.* Step 1 (every budget deleted) is the hard stop for everything after it.
  1. Delete every budget that covers Copilot, AI credits, the cloud agent or premium requests. Delete it; do not set it to $0.
  2. Turn on the 90 % and 100 % included-usage alerts.
  3. Optionally, at github.com/settings/copilot/features, turn off "Allow GitHub to use my data for AI model training".

  Answer yes or no for each step here. Step 1 is a hard stop: on "no", or if any budget remains, stop here. No later task in sections 7 and 8 runs until step 1 reads "yes". A "no" on steps 2 or 3 is recorded and does not stop.
- [ ] 7.3 **USER ACTION:** create the fine-grained token at github.com/settings/personal-access-tokens/new:
  - *2026-10-06: pending: user action.* The workflow brief reports a fine-grained "Copilot Requests" token already created and kept in the user's password manager; the user confirms the settings below (name, owner, expiry ≤ 90 days, public repositories read-only, only Copilot Requests) and answers "created" here. Nobody else handles the token.
  - **Token name:** `thesis-proposal-dev-runner`.
  - **Resource owner:** your personal account.
  - **Expiration:** a fixed date, at most 90 days out. Never "No expiration".
  - **Repository access:** "Public repositories" (read-only).
  - **Permissions:** under Account permissions, set "Copilot Requests". Leave every other account and repository permission at "No access".

  Keep the token only in the clipboard, for task 7.4's hidden prompt. Never paste it into chat, a file, `.env` or a shell variable. Answer "created" here, nothing else.
- [ ] 7.4 **USER ACTION:** in a terminal outside any agent session, run `uv run poe host-login copilot`, and paste the token at the hidden prompt. It must exit 0. The user does not run `--clear-stop` yet: that is the go of task 8.1. The agent then runs `uv run poe host-status copilot` and records the values, booleans, enums and numbers only. Pass requires all of these:
  - *2026-10-06: pending: user action (`uv run poe host-login copilot`), then pending: live check (`host-status copilot`).* Since this session the login exits 0 only when the managed-settings and sandbox-tool rows pass too, so a missing sandbox tool (see 7.9) makes it exit 3 after writing the token file; installing the tool and rerunning `host-status copilot` is then enough, no second login.
  - `marker: yes`, `token_present: yes`, `clean: yes`;
  - `stop: approval` (first run not yet approved), and no other stop;
  - `auth_type: env`, `host_ok: yes`;
  - `cli_version: 1.0.91`, and every sandbox tool found;
  - `token_based_billing: yes`.

  On a fail, stop and relay the failing keys to the user.
- [ ] 7.5 K1.
  - *2026-10-06: pending: live check (step 1, after 7.4) and user action (step 2, `run-env`).*
  1. The agent runs `uv run poe host-status copilot --no-token`. Pass: `logged_in: no`, which shows the CLI finds no stored or `gh` credential.
  2. **USER ACTION:** run

     ```sh
     uv run python harness/copilot_cli.py run-env -- sh -c 'gh auth token --hostname github.com >/dev/null 2>&1; echo $?'
     ```

     and report the printed number only. Pass: a non-zero number, and nothing else printed.

  On a fail, stop. Every run stays refused, and the finding goes to the user.
- [ ] 7.6 K2. The agent runs `uv run poe host-status copilot` three times, a minute apart. Record `overage_permitted`, `overage_entitlement`, `overage_count`, `remaining_pct` and `reset_date`.
  - *2026-10-06: pending: live check (needs the login of 7.4).*
  - **Pass:** the raw snapshot is present; `overage_permitted` is false; `overage_entitlement` is 0; and `remaining_pct` and `overage_count` are unchanged across the three reads, which together with the V-pass's endpoint reading shows that the read makes no model call.
  - **If the snapshot is absent,** every run refuses by design. Record it and relay it to the user. Do not relax the rule.
- [ ] 7.7 K4. The agent runs `uv run poe host-status copilot --models` and records each id, its policy state and its efforts. The user names the model for tasks 7.8 and 8.1: the cheapest one that is enabled. Model ids appear only on command lines, never in code.
  - *2026-10-06: pending: live check (needs the login of 7.4), then user action (naming the model).*
- [ ] 7.8 K3. The agent runs `uv run poe dev check_report --host copilot --model <id from 7.7> --max-ai-credits 30 --preflight-only`, which prints every pre-run check. Then it runs the same for one `supervise_*` scenario, whose roster includes siblings. Pass requires all of these:
  - *2026-10-06: pending: live check (needs 7.4 and the model of 7.7).*
  - every row passes, apart from the stop row, which reads the approval stop and nothing else;
  - the settings were accepted, with no unknown-key warning on stderr. That alone does not show a key is read (design Decision 3); K6 checks the effective policy;
  - both rosters equal the staged skills plus the bundled ones.

  Record the top-level key names of `<home>/config.json`, read with `jq -r 'keys[]'` (names only). If a fresh token-mode home develops keys outside `MANAGED_STATE_KEYS`, list their names to the user. Widen the set only after the user agrees, and record it in design Decision 6 through `openspec-update-change`. On any other fail, stop and relay it to the user.
- [ ] 7.9 K6a. The agent runs `bwrap --ro-bind / / --dev /dev true; echo $?`, and `command -v <tool> >/dev/null; echo $?` for each tool of `SANDBOX_TOOLS`. Pass: 0 for every line. Record each in the README's K-check lines. On a fail, stop: the user installs the named tool (**USER ACTION**, through the package manager), and the task is repeated.
  - *2026-10-06: pending: live check.* Observed in passing (`which`, no `bwrap` run): `slirp4netns` is not on `PATH` on this machine, the other seven tools are. Expect K6a to fail on it until the user installs it (**USER ACTION**, e.g. `pacman -S slirp4netns`); until then every Copilot run and the login's readiness refuse as a precondition naming it.
- [ ] 7.10 K6, the confinement probe at $0, if task 1.3 kept it. The agent reads the probe rows of task 7.8's `--preflight-only` output. Pass requires all of these:
  - *2026-10-06: pending: live check (task 1.3 kept the probe; it needs 7.8).*
  - the token file, `/proc/<pid>/environ` of the client process and of the harness process, the real `~/.ssh` and `~/.config/gh` read `denied`;
  - `gh auth token` over the real session bus, and `git credential fill` for `github.com`, exit non-zero;
  - `python3` and the skill script's `--help` run.

  Record each line, words and exit codes only, in the README's K-check lines. On a fail, stop. Every run stays refused by the same probe, and the finding goes to the user; a deny-list change goes through `openspec-update-change`. If task 1.3 dropped the probe, mark this task "not available at 1.0.91" and name K6 as unverified in task 8.1's go request.

## 8. First live run (gated; spends included credits)

If the user has not given the go by the time sections 0 to 7 are done, mark the tasks here as deferred, and carry them into the proposal of `record-copilot-streams` before archiving.

- [ ] 8.1 P2, the first Copilot model call, **gated on the user's explicit go**.
  - *2026-10-06: pending: live check, gated on 7.1–7.10 and the user's go (`--clear-stop`).*
  - **Precondition.** Tasks 7.1 to 7.10 all passed, with 7.2 step 1 (every budget deleted) answered "yes", and `host-status copilot` shows the approval stop and no other. If any of these does not hold, do not ask for the go.
  - **The go request.** Ask in chat, stating:
    - the planned command and the model from 7.7:

      ```sh
      uv run poe dev check_report --host copilot --model <id> --max-ai-credits 30 --keep
      ```

    - the cap of 30 credits, and that it is soft: one model call can overshoot it, and only more than twice the cap records a billing stop;
    - every confinement item still unverified at this point: the sandbox-active event (K6b), whether the sandboxed shell reaches the network, and, if task 7.10 was not available, the deny list, the token file and the client process's environment (formerly K6c);
    - that the go is given by running `uv run poe host-login copilot --clear-stop` in a terminal outside any agent session, and nothing else.
  - **The run.** Only after `host-status copilot` shows `stop: none`, run the command with the user's other Copilot clients (VS Code, other CLI sessions) closed. Record:
  - the outcome and its reason;
  - `cli_version`, the credits consumed against the cap, and the overage count and `remaining_pct` before and after;
  - K5: which events reached stdout and which only the session file (`skills_loaded`, `mcp_servers_loaded`, `session.start`, `result`); whether the model names match the request; whether the `--deny-tool` forms and the URL handling were accepted;
  - K6b: whether the sandbox-active event arrived and no "ignored" warning;
  - K7, if the run timed out: the exit code, and whether `session.shutdown` was written.

  If the run is untested only because `skills_loaded` or the sandbox-active report is missing, record which events did arrive and stop; a missing sandbox-active report has also recorded an isolation stop, which stays until the user reads the findings and clears it. Relaxing either check is a reviewed change in `record-copilot-streams`. Do not run a second scenario, `--judge`, or another model without a new go.
- [ ] 8.2 Write the hand-off list for `record-copilot-streams`:
  - *2026-10-06: pending: live check (needs 8.1's outcomes).*
  - the K5, K6b and K7 outcomes;
  - the reduced recording that replaces the synthetic fixtures;
  - the deny-path probe (formerly K6c), with its own go, only if task 1.3 dropped it from this change;
  - D-C4(c), if the sandboxed shell had no network;
  - any check that 8.1 showed needs relaxing.

  Delete the kept workspace once its events are reduced into that change's fixtures. Verify that the list is in the README's K-check lines.

## 9. Close

- [ ] 9.1 Rerun the gates: `uv run poe test`, `uv run poe cov`, `uv run poe specs` and `openspec validate add-copilot-dev-runner --strict`. Confirm that all four are green.
  - *2026-10-06: pending: live check (the close follows sections 7 and 8); the same four gates are green at the L0 commit (6.1–6.3).*
- [ ] 9.2 Commit the code, tests, fixtures, docs and this change folder as one commit for the completed change, off `main` until it is complete. Do not push. Verify with `git status` (clean) and `git show --stat HEAD`.
  - *2026-10-06: pending: live check.* The L0 work (sections 0–6) is committed on branch `host-runners` ("feat(harness): Copilot dev runner behind the host seam (L0)"), off `main`, not pushed; the closing commit follows sections 7–8.
- [ ] 9.3 Archive through the `openspec-archive-change` skill.
  - *2026-10-06: pending: live check (sections 7–8) and the archive of `add-codex-dev-runner`.* Archive only after sections 0 to 7, with section 8 either done or marked deferred as its preamble says, and only once `close-claudeai-surfaces`, `add-harness-claude-login` and `add-codex-dev-runner` are archived, in that order (`openspec list` shows none of them). Before archiving:
  - repeat task 0.1's rebase, host-counting and scenario-name checks against the archived main spec;
  - run `openspec validate add-copilot-dev-runner --strict`, which must pass with no "Archive would refuse" line.

  Afterwards, verify that `openspec validate --all --strict` is green.
