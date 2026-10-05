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

- [ ] 0.1 Confirm that changes 1–3 are implemented, with their spec text final. Change 1 is already archived, because change 2's own precondition (its task 0.1) requires that before change 2's code is written; read change 1's text from the archived main spec (`openspec/specs/testing-harness/spec.md`), never from its change folder. Only the archives of changes 2 and 3 may still be pending: change 2's waits for its L1, and change 3's for change 2's archive. Check two things:
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

- [ ] 1.1 **USER ACTION:** `yay -S github-copilot-cli-bin`, which must install 1.0.91.
  - **Check the package.** The agent runs `pacman -Q github-copilot-cli-bin` and records the version.
  - **Check the binary.** The agent creates a scratch directory outside the repository with `mktemp -d`, then runs:

    ```sh
    unshare -rn env -i PATH="$PATH" HOME=<scratch>/home COPILOT_HOME=<scratch>/copilot-home \
      COPILOT_CACHE_HOME=<scratch>/cache COPILOT_AUTO_UPDATE=false copilot --version
    ```

    That unpacks the package into `<scratch>/cache`. The agent never runs this with the real `HOME` or `~/.copilot`.
  - **Pass:** both read 1.0.91.
  - **On another version:** stop, and relay to the user that the exact pin needs a revision of D-C3 through `openspec-update-change`.
- [ ] 1.2 The V-pass, run by the agent locally with no network. It reads the files under `<scratch>/cache/pkg/linux-x64/1.0.91/`: `app.js`, the `runtime.node` strings and `schemas/`. It also reads the output of `--help` and `copilot help <topic>`, each run as in 1.1. It re-derives the following at 1.0.91, with a byte offset, a string or a help line for each:
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
- [ ] 1.3 Compare the V-pass with the 1.0.67 facts the spec and design rely on.
  - If any change alters a rule, revise the change through `openspec-update-change` before section 2. Relay the change to the user when it touches D-C1–D-C4.
  - In particular: if 1.2 finds no model-free call that runs inside the session's sandbox, remove the confinement probe from the spec and design through `openspec-update-change`, move it back to `record-copilot-streams`, and tell the user that P2's go will then rest on the after-run checks alone. If the client's own tools need the package cache inside the sandbox, revise the deny list the same way.
  - Otherwise, record "no rule changed at 1.0.91" in `design.md`.

  Verify with `openspec validate add-copilot-dev-runner --strict`.

## 2. Fixtures

- [ ] 2.1 Create `tests/unit/data/copilot_streams/` with synthetic saved event lists. Each list holds stdout events plus reduced `copilot.*` records, derived from the 1.0.91 V-pass. Model names are `copilot-fixture-a` (requested) and `copilot-fixture-b` (other). Files:
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

- [ ] 3.1 The record and the home, in `tests/unit/test_host_login.py`, as a new Copilot section. Cases:
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
- [ ] 3.2 The token-file commands, in the CLI section of `test_host_login.py`. `getpass.getpass` is patched; no real `copilot` runs. Cases:
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
- [ ] 3.3 The environment and the pre-spawn assertion, in a new `tests/unit/test_copilot_cli.py` and in `tests/unit/test_isolated_env.py`. Cases:
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
- [ ] 3.4 The status read and the billing guard, in `test_copilot_cli.py`. Cases:
  - **`parse_status`.** It keeps exactly the listed values, and no fake login, organization or token survives it.
  - **`choose_snapshot`.** It picks `chat` for `status-free-chat.json`.
  - **`status_problem`.** Each `status-*.json` gives the spec's outcome and remedy: the missing overage field, the missing entitlement field, the budget, the entitlement, the drawn overage, legacy billing, low quota, no user, auth errors, `gh-cli`, enterprise, and error.
  - **`read_status` timeout.** Against a fake server that never answers, the read is unavailable after a patched `STATUS_TIMEOUT_S`, and the child is stopped.
  - **`quota.json`.** It holds only the listed values.
  - **`billing_after`.** It flags and stops on: overage grew, `after=None` (the read after the run unavailable, also driven end to end with a fake server that answers before the run and not after), `over-cap`, `zero-nano`, `no-shutdown`, `soft-cap` and `session-limits`. `quota-error` is untested without a stop.
  - **The stops.** `record_stop` of each kind (billing, isolation, approval) makes the next preflight refuse with that kind's remedy, before any `Popen`, and maps to its untested reason (subscription, isolation, precondition). `--preflight-only` prints the stop and is not refused by it.
  - **The credit cap.** A missing `--max-ai-credits`, or one below 30, is a usage error.

  Verify that the cases fail before the change.
- [ ] 3.5 The command, the scan, the rosters and the sandbox, in `test_copilot_cli.py`. Cases:
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
- [ ] 3.6 The readers, in `test_copilot_cli.py` and `tests/unit/test_routing.py`. Cases:
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
- [ ] 3.7 The host seam and the CLI, in `tests/unit/test_hosts.py` and `tests/unit/test_dev_runner_probe.py`. Cases:
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

- [ ] 4.1 In `harness/host_login.py`:
  - add the `HostLogin` fields `credential` and `token_env`, with defaults that keep `CLAUDE` and `CODEX` unchanged. `child_vars` keeps change 3's signature `child_vars(home)`;
  - add `COPILOT` (whose `child_vars(home)` holds only home-derived and constant variables, design Decision 5), `token_path`, `pinned_settings`, `account_home`, `MANAGED_STATE_KEYS` and `check_copilot_home`, and extend `check_location`;
  - add the token-file branches of `main`: login (with `--reset` and `--clear-stop`, and the approval stop), logout, and status with `--models` and `--no-token`. Each imports `copilot_cli` lazily;
  - add `NOTES["copilot"]` and `RECORDS["copilot"]`.

  Verify that 3.1 and 3.2 pass, that `uv run ruff check harness/host_login.py` reports no C901, that `grep -n "copilot.token\|token_path" harness/*.py` shows reads only in the login, the logout and `token_env`, and that the Claude and Codex sections stay green.
- [ ] 4.2 Create `harness/copilot_cli.py`, stdlib-only, importing `host_login` only. It holds:
  - **Constants:** `COPILOT_PINNED_VERSION`, `STATUS_TIMEOUT_S`, `BUILTIN_SKILLS`, `BUILTIN_MCP`, `SANDBOX_TOOLS` and `SKILL_HOSTS`, and the binary seam the conftest sentinel patches.
  - **Environment:** `run_env` (scratch `HOME` and XDG variables), `token_env`, `scrub`, `ignored_env`, `assert_copilot_env` and `spawn`.
  - **Status:** `read_status`, `parse_status`, `choose_snapshot` and `status_problem`.
  - **Preflight:** `scan_parents`, `roster_problem`, `sandbox_problem`, `confinement_probe`, `probe_problem` and `preflight`, in design Decision 6's order.
  - **Command and readers:** `url_hosts`, `command`, `reduce_session`, `copilot_tool_calls`, `copilot_read`, `isolation_after`, `billing_after`, `failure_reason` and `record_stop(home, kind, cause)`.
  - **Run:** `run_copilot`, which takes the lock; then the preflight and the read before; the spawn with `pass_fds` and the parent-death signal; the capture, `scrub` and reduction; the read after; the prune; and the release.
  - **`main(argv)`** with the `run-env` subcommand (design Decision 15).

  Findings are frozen dataclasses, and failure and status tables are data, so complexity stays at 12 or below. Verify that 3.3 to 3.6 pass and that `uv run ruff check harness/copilot_cli.py` is clean.
- [ ] 4.3 Wire the host in. In `harness/claude_runner.py`:
  - add the `copilot` entry of `HOSTS`, `--host copilot`, `--max-ai-credits` and `--preflight-only`;
  - add the usage guards of task 3.7;
  - map the Copilot findings to the three untested reasons and the runner-failure status (design Decision 11).

  In `harness/routing.py`, make `tool_calls` append `copilot_cli.copilot_tool_calls(events)`. Verify that 3.7 passes, and that `test_dev_runner_probe.py`, `test_routing.py`, `test_install_probe.py`, `test_isolated_env.py`, `test_codex_cli.py` and `test_hosts.py` stay green.
- [ ] 4.4 Update the module docstrings and usage lines of `claude_runner.py`, `copilot_cli.py`, `hosts.py` and `host_login.py`: the Copilot host, the token file, the billing guard and stop, the sandbox, and the not-comparable label. Verify by reading the diff. Confirm with `grep -nE 'gpt-[0-9]|claude-(haiku|sonnet|opus)-[0-9]' harness/copilot_cli.py` (empty) that no model slug entered the code.

## 5. Documentation

- [ ] 5.1 Update `harness/README.md`:
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
- [ ] 5.2 Update the `AGENTS.md` Commands block:
  - `uv run poe dev <scenario> --host copilot --model <id> --max-ai-credits <N>` (included credits; never a matrix input);
  - `uv run poe host-login copilot [--reset | --clear-stop]` (the user only);
  - `uv run poe host-status copilot [--models | --no-token]` (agents may run it; no model call);
  - `uv run poe host-logout copilot` (the user only).

  Add one sentence: every Copilot login records an approval stop, and only the user clears it, from a terminal, which is the explicit go for the next model call; agents never read the token file, `/proc/<pid>/environ` of a Copilot child, or `ps e` output while one runs. Verify by reading the diff and with `uv run poe test`.

## 6. Gate

- [ ] 6.1 Run `uv run poe test` (not `test-fast`) and confirm it is green: pytest, ruff with the full rule set, `test_repo_conventions.py`, the drift check and conform.
- [ ] 6.2 Run `uv run poe cov` and confirm that the 78 % floor holds with `copilot_cli.py` counted.
- [ ] 6.3 Run `uv run poe specs` and `openspec validate add-copilot-dev-runner --strict`, and confirm both pass.

## 7. Account setup and the $0 live checks (no model call)

- [ ] 7.1 **USER ACTION:** at github.com/settings/copilot, confirm that the account's Copilot plan is the free Copilot Pro for verified teachers (D-C1). Answer yes or no here. On "no", stop: D-C1 reopens with the user.
- [ ] 7.2 **USER ACTION** at github.com/settings/billing, under "Budgets and alerts":
  1. Delete every budget that covers Copilot, AI credits, the cloud agent or premium requests. Delete it; do not set it to $0.
  2. Turn on the 90 % and 100 % included-usage alerts.
  3. Optionally, at github.com/settings/copilot/features, turn off "Allow GitHub to use my data for AI model training".

  Answer yes or no for each step here. Step 1 is a hard stop: on "no", or if any budget remains, stop here. No later task in sections 7 and 8 runs until step 1 reads "yes". A "no" on steps 2 or 3 is recorded and does not stop.
- [ ] 7.3 **USER ACTION:** create the fine-grained token at github.com/settings/personal-access-tokens/new:
  - **Token name:** `thesis-proposal-dev-runner`.
  - **Resource owner:** your personal account.
  - **Expiration:** a fixed date, at most 90 days out. Never "No expiration".
  - **Repository access:** "Public repositories" (read-only).
  - **Permissions:** under Account permissions, set "Copilot Requests". Leave every other account and repository permission at "No access".

  Keep the token only in the clipboard, for task 7.4's hidden prompt. Never paste it into chat, a file, `.env` or a shell variable. Answer "created" here, nothing else.
- [ ] 7.4 **USER ACTION:** in a terminal outside any agent session, run `uv run poe host-login copilot`, and paste the token at the hidden prompt. It must exit 0. The user does not run `--clear-stop` yet: that is the go of task 8.1. The agent then runs `uv run poe host-status copilot` and records the values, booleans, enums and numbers only. Pass requires all of these:
  - `marker: yes`, `token_present: yes`, `clean: yes`;
  - `stop: approval` (first run not yet approved), and no other stop;
  - `auth_type: env`, `host_ok: yes`;
  - `cli_version: 1.0.91`, and every sandbox tool found;
  - `token_based_billing: yes`.

  On a fail, stop and relay the failing keys to the user.
- [ ] 7.5 K1.
  1. The agent runs `uv run poe host-status copilot --no-token`. Pass: `logged_in: no`, which shows the CLI finds no stored or `gh` credential.
  2. **USER ACTION:** run

     ```sh
     uv run python harness/copilot_cli.py run-env -- sh -c 'gh auth token --hostname github.com >/dev/null 2>&1; echo $?'
     ```

     and report the printed number only. Pass: a non-zero number, and nothing else printed.

  On a fail, stop. Every run stays refused, and the finding goes to the user.
- [ ] 7.6 K2. The agent runs `uv run poe host-status copilot` three times, a minute apart. Record `overage_permitted`, `overage_entitlement`, `overage_count`, `remaining_pct` and `reset_date`.
  - **Pass:** the raw snapshot is present; `overage_permitted` is false; `overage_entitlement` is 0; and `remaining_pct` and `overage_count` are unchanged across the three reads, which together with the V-pass's endpoint reading shows that the read makes no model call.
  - **If the snapshot is absent,** every run refuses by design. Record it and relay it to the user. Do not relax the rule.
- [ ] 7.7 K4. The agent runs `uv run poe host-status copilot --models` and records each id, its policy state and its efforts. The user names the model for tasks 7.8 and 8.1: the cheapest one that is enabled. Model ids appear only on command lines, never in code.
- [ ] 7.8 K3. The agent runs `uv run poe dev check_report --host copilot --model <id from 7.7> --max-ai-credits 30 --preflight-only`, which prints every pre-run check. Then it runs the same for one `supervise_*` scenario, whose roster includes siblings. Pass requires all of these:
  - every row passes, apart from the stop row, which reads the approval stop and nothing else;
  - the settings were accepted, with no unknown-key warning on stderr. That alone does not show a key is read (design Decision 3); K6 checks the effective policy;
  - both rosters equal the staged skills plus the bundled ones.

  Record the top-level key names of `<home>/config.json`, read with `jq -r 'keys[]'` (names only). If a fresh token-mode home develops keys outside `MANAGED_STATE_KEYS`, list their names to the user. Widen the set only after the user agrees, and record it in design Decision 6 through `openspec-update-change`. On any other fail, stop and relay it to the user.
- [ ] 7.9 K6a. The agent runs `bwrap --ro-bind / / --dev /dev true; echo $?`, and `command -v <tool> >/dev/null; echo $?` for each tool of `SANDBOX_TOOLS`. Pass: 0 for every line. Record each in the README's K-check lines. On a fail, stop: the user installs the named tool (**USER ACTION**, through the package manager), and the task is repeated.
- [ ] 7.10 K6, the confinement probe at $0, if task 1.3 kept it. The agent reads the probe rows of task 7.8's `--preflight-only` output. Pass requires all of these:
  - the token file, `/proc/<pid>/environ` of the client process, the real `~/.ssh` and `~/.config/gh` read `denied`;
  - `gh auth token` over the real session bus, and `git credential fill` for `github.com`, exit non-zero;
  - `python3` and the skill script's `--help` run.

  Record each line, words and exit codes only, in the README's K-check lines. On a fail, stop. Every run stays refused by the same probe, and the finding goes to the user; a deny-list change goes through `openspec-update-change`. If task 1.3 dropped the probe, mark this task "not available at 1.0.91" and name K6 as unverified in task 8.1's go request.

## 8. First live run (gated; spends included credits)

If the user has not given the go by the time sections 0 to 7 are done, mark the tasks here as deferred, and carry them into the proposal of `record-copilot-streams` before archiving.

- [ ] 8.1 P2, the first Copilot model call, **gated on the user's explicit go**.
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
  - the K5, K6b and K7 outcomes;
  - the reduced recording that replaces the synthetic fixtures;
  - the deny-path probe (formerly K6c), with its own go, only if task 1.3 dropped it from this change;
  - D-C4(c), if the sandboxed shell had no network;
  - any check that 8.1 showed needs relaxing.

  Delete the kept workspace once its events are reduced into that change's fixtures. Verify that the list is in the README's K-check lines.

## 9. Close

- [ ] 9.1 Rerun the gates: `uv run poe test`, `uv run poe cov`, `uv run poe specs` and `openspec validate add-copilot-dev-runner --strict`. Confirm that all four are green.
- [ ] 9.2 Commit the code, tests, fixtures, docs and this change folder as one commit for the completed change, off `main` until it is complete. Do not push. Verify with `git status` (clean) and `git show --stat HEAD`.
- [ ] 9.3 Archive through the `openspec-archive-change` skill. Archive only after sections 0 to 7, with section 8 either done or marked deferred as its preamble says, and only once `close-claudeai-surfaces`, `add-harness-claude-login` and `add-codex-dev-runner` are archived, in that order (`openspec list` shows none of them). Before archiving:
  - repeat task 0.1's rebase, host-counting and scenario-name checks against the archived main spec;
  - run `openspec validate add-copilot-dev-runner --strict`, which must pass with no "Archive would refuse" line.

  Afterwards, verify that `openspec validate --all --strict` is green.
