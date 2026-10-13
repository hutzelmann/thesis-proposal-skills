# Tasks

Ground rules for every task below:

- **Model calls.** No task before section 7 makes a model call of any kind: no `claude -p`, no `codex exec` against a login, no OpenRouter.
- **Logins.** Agents never run login commands. A step marked **USER ACTION** is run by the user, with the exact command given.
  - Agents may run `uv run poe host-status codex` and `uv run poe host-status codex --quota`. Neither makes a model call; the quota read is a GET of plan usage.
  - Agents never run `poe host-login` or `poe host-logout`.
- **Credentials.** Nobody opens or prints a credentials file (`auth.json`, `.credentials.json`). The one exception in code is change 2's expiry reader in `host_login`, which parses only the `expiresAt` field of the Claude home's `.credentials.json`. The Codex `auth.json` is never opened, by code or by an agent; its age comes from `stat`. Reports carry only booleans, counts, enums, version strings, file modification times (`stat`, never contents) and names. They never carry a credential, an environment value, an email address or an account identifier.
- **Workspaces.** Codex workspaces are temporary directories outside the repository. The private proposals directory is never a workspace.

## 0. Precondition

- [x] 0.1 Confirm that both earlier changes are implemented, with their spec text final.

  *Done 2026-10-06.* Both earlier changes are archived (main 526a1bf); `openspec list` shows neither, and `host_login` exposes every listed name. Change 2 was archived with a later text than the 2026-10-05 revision, so `openspec validate --strict` failed on four dropped scenario names ("Relative override refused", "Unmarked directory never adopted", "Failed logout stops a re-login", "Profile directory bars the login commands"). Rebased through `openspec-update-change`: the three shared blocks now start from the archived main spec (also folded in: the Claude status check without the token, the label following how the configuration was prepared, the install-probe label, a judge error naming its billing reason, and the two scenario THEN clauses change 2 extended). Choice: the default-profile-directory rule is scoped to Claude, because a Codex client reads no Anthropic profile (design Context notes the rebase). Both isolation requirements still scope their Claude clauses to Claude, so no further blocks were needed; the name-by-name check passes, and `openspec validate add-codex-dev-runner --strict` is valid with no INFO line, since change 2 is archived. Change 1 is already archived, because change 2's own precondition (its task 0.1) requires that before change 2's code is written. Only change 2's archive may still be pending: it waits for its L1, more than 8 h of idle time after its login (design, Migration Plan). Check:
  - `openspec list` no longer shows `close-claudeai-surfaces`;
  - both changes' code sections and gates are checked off in their `tasks.md` (change 1's in its archived copy);
  - `harness/host_login.py` exposes `HostLogin`, `RECORDS`, `allowlisted_env`, `login_env`, `AGENT_MARKERS`, `TERM_GRACE_S`, `stop_child`, `LoginProblem`, `refusal`, `login_note`, `L3_PASSED`, `login_remedy` and `main`, and `routing.follow_stream` stops through `stop_child`. `run_host` is not expected: this change adds it (task 3.1).

  Then:
  - If change 2's final text of "Harness-owned host logins", "Dev-runner cost and helper-agent telemetry" or "Subscription text roles (dev runner)" differs from what this change's MODIFIED blocks start from (change 2 as revised on 2026-10-05), rebase them through the `openspec-update-change` skill. Change 1's text, which change 2's blocks fold in, is the archived main spec's (`openspec/specs/testing-harness/spec.md`), never its change folder's.
  - Confirm that change 2's final text still scopes "Isolated child environment" and the authentication, opt-out and account-surface rules of "Isolated measurement environment" to Claude, and leaves a later client's child to the requirement that adds it. If it does not, add MODIFIED blocks for both through `openspec-update-change`, as design Decision 1 describes, before any code.
  - Repeat the name-by-name check: every scenario name of the three shared requirements, in change 2's final text, appears in this change's blocks.
  - Verify with `openspec validate add-codex-dev-runner --strict`. Until change 2 is archived, the only allowed INFO line is "Archive would refuse … Harness-owned host logins - not found"; task 8.2 requires it gone.

## 1. Fixtures

- [x] 1.1 Create `tests/unit/data/codex_streams/` with synthetic saved event lists.

  *Done 2026-10-06.* All listed files exist, with a README row each; `test_model_ids.py` stays green. Choices: each saved list ends with the runner's own `codex.harness` record (duration, exit status, stderr tail, the quota read before the run), so a faked `run_codex` still yields quota before and after; `__WS__` stands for the workspace and the tests substitute it; `quota-reached.json` keeps its window at 88 % so that it pins the reached-limit refusal rather than the 90 % one. Deviation: the feature listings are shaped after the brief's 0.133 default-on set, not captured from the local CLI, because this run starts no `codex` at all; X7 (task 6.2) confirms the format. Each file is exec events plus reduced `codex.*` records (design Decision 10), derived from the rust-v0.160.0 sources: `exec_events.rs`, `event_processor_with_jsonl_output.rs`, `protocol.rs`, and the `manager.rs` messages. Model names are `gpt-fixture-a` and `gpt-fixture-b`. Files:
  - `success.jsonl`;
  - `skill-read.jsonl` (`cat …/.agents/skills/proposal-check/SKILL.md`);
  - `helper-spawn.jsonl` (`collab_tool_call spawn_agent` with a verifier-brief prompt);
  - `mcp-call.jsonl`;
  - `foreign-skill.jsonl` (a `codex.skills` path under a home `.agents/skills`);
  - `cloud-skill-tool.jsonl`;
  - `provider-leak.jsonl` (`model_provider: "openrouter"`);
  - `no-rate-limits.jsonl`;
  - `credits-unreported.jsonl` (`rate_limits` without a credits block);
  - `credits-drawn.jsonl`;
  - `plan-free.jsonl` (`plan_type: "free"`);
  - `limit-reached.jsonl`;
  - `model-rerouted.jsonl`;
  - `effort-dropped.jsonl`;
  - `refresh-reused.jsonl`;
  - `restriction-logout.jsonl`;
  - `turn-failed.jsonl`;
  - `no-turn-completed.jsonl`.

  Add raw inputs:
  - `rollout-success.jsonl`, a raw session record with a `session_meta` that carries extra fields the reduction must drop;
  - the app-server answers `quota-ok.json` (Plus, zero balance), `quota-credits.json`, `quota-no-credits.json` (windows, no credits block), `quota-free.json` (`planType: "free"`), `quota-92.json`, `quota-reached.json`, `quota-no-window.json` and `quota-error.json`;
  - `features-ok.txt` and `features-extra-on.txt`, shaped from 0.133's local `codex features list`.

  Write `README.md` with one row per file: provenance (synthetic, with the source file and tag) and what it pins, following `../claude_cli_streams/README.md`. Verify that `uv run pytest tests/unit/test_model_ids.py` stays green, so the synthetic names need no allowlist entry.

## 2. Failing tests first

- [x] 2.1 Codex record and home, in `tests/unit/test_host_login.py`, as a new section. Use `THESIS_PROPOSAL_DEV_STATE` under `tmp_path`, and `check_location(..., tempdir=<a separate directory>)`. Cases:
  - **Default path.** The Codex home is `…/hosts/codex`.
  - **Temporary directory.** A root inside the passed `tempdir` is refused for `CODEX` and accepted for `CLAUDE`.
  - **Overlap.** An override equal to `~/.codex`, inside it, or containing `$CODEX_HOME` is refused.
  - **Seeding.** `config.toml` is written before the fake login argv runs (record the call order), and `tomllib.loads(PINNED_CONFIG_TOML) == PINNED_CONFIG`.
  - **`check_codex_home`.** It names a differing key path, an extra key, each forbidden entry (`AGENTS.md`, `AGENTS.override.md`, `.env`, `hooks.json`, `skills/x`, a `memories/` entry), and lets `skills/.system`, `log/`, `quota.json` and `.harness-run.lock` pass.
  - **`codex_status`.** It maps the ChatGPT, API-key, access-token, other and not-logged-in lines. The masked fragment of an API-key line appears nowhere in the parse result.
  - **`codex_version`.** It parses the version, and 0.159.9 is refused with the update remedy.
  - **Refusals and the login note**, parametrized over `X8_PASSED` False and True:
    - with `X8_PASSED` False, a Codex refusal whose remedy names `host-login codex` (with or without `--reset`) ends with "Whether this logs out your other ChatGPT sessions is unverified (X8)." and does not contain "not affected";
    - a Codex refusal with another remedy (the CLI update, a feature report) ends with "Your own Codex login is not affected.";
    - with `X8_PASSED` True, every Codex refusal ends with "Your own Codex login is not affected.";
    - `LoginProblem` built without `client` still renders change 2's Claude sentences, so change 2's `refusal` and `login_note` tests pass unmodified.

  Verify that the tests fail before the record exists.

  *Done 2026-10-06* (failed with `AttributeError` before 3.1). The seeding-order case lives with the CLI cases of 2.2.
- [x] 2.2 Codex commands, in the CLI section of `tests/unit/test_host_login.py`. Fake the binary through the runner seam, never the real `codex`. Cases:
  - **Login environment.** It drops `CODEX_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_BASE_URL` and every `CODEX_*`, keeps `DISPLAY`, and sets `CODEX_HOME=<home>`.
  - **Login argv.** It is `login`, with `--device-auth` passed through, and never `--with-api-key` or `--with-access-token`.
  - **Existing login.** Logout runs before login while the run lock is held.
  - **`--reset`.** It wipes the marked home and reseeds it.
  - **Messages.** With `X8_PASSED` False, the logout, reset and login-over-login paths print the X8 caveat before the fake logout runs. With it True, none does.
  - **Status.** `status codex` prints only the keys of design Decision 4, which are the spec's status list (`capsys`): `home`, `marker`, `logged_in`, `auth_method`, `config_pinned`, `clean`, `last_written`, `cli_version`, `min_version`, `features_ok`, `last_quota`, `runs_use`. No key fragment, email or account identifier appears. It exits 0 when ready and 3 when not.
  - **`auth.json` never opened.** A synthetic `auth.json` is given a known modification time with `os.utime`, and `builtins.open`, `io.open` and `Path.read_text`/`read_bytes` are patched to fail on that path. `last_written` reports the age from the modification time, and no patched opener is called for it.
  - **`status codex --quota`.** It takes the run lock and prints the parsed windows from a fake app-server beside `last_quota`. With `quota-free.json` it names the plan and exits 3.

  Verify that these fail before the change.

  *Done 2026-10-06* (failed before 3.1). Choice: the cases live in `tests/unit/test_host_login_cli.py`, which is where the CLI section actually is. The probes (`--version`, `login status`, `features list`) are faked at `codex_cli.probe` and the quota read at `codex_cli.read_quota`; the login and logouts at `host_login.run_client`. Added: a held run lock makes `logout codex` exit 3 with the one template, and `--device-auth`/`--quota` are usage errors for Claude.
- [x] 2.3 Run lock and stopping a child, in `tests/unit/test_codex_cli.py`, POSIX only and skipped on Windows. Cases:
  - **Waiting.** A second `run_lock` on a held lock raises `RunLockBusy` after a patched short `LOCK_WAIT_S`. Its `problem` is a `LoginProblem` with `client="codex"` whose cause names the held lock, and `refusal(err.problem)` renders it in the one template.
  - **The child holds the lock.** A fake child started with the descriptor in `pass_fds` keeps the lock after the parent's descriptor is closed, and releases it when it exits.
  - **Interrupt before kill.**
    - A SIGINT-trapping fake child writes a marker and exits, and is never killed.
    - A child that ignores SIGINT is killed after the patched grace.
    - `run_host` re-raises `TimeoutExpired`.
    - `stop_child(proc)` called without a signal still sends SIGTERM, so `routing.follow_stream` and change 2's `stop_child` tests are unchanged.
  - **Linux.** `preexec_fn` sets the parent-death signal (assert through a fake child that reads `/proc/self/status` or `prctl(PR_GET_PDEATHSIG)`).
  - **Windows guard.** On a platform without `fcntl` (patched), the Codex runner refuses with a usage error.

  Verify that these fail before the change.

  *Done 2026-10-06* (collection failed: no `codex_cli`). The pass-fds case runs a real child through `run_host` and checks the lock from a second open file description.
- [x] 2.4 Billing guard, in `tests/unit/test_codex_cli.py`. Cases:
  - **The builder.** `allowlisted_env(CODEX, home, environ)` plus `run_env`: no strip-family name survives, `CODEX_HOME`, `HOME`, `USERPROFILE` and the four XDG variables are set, `CLAUDE_CODE_OAUTH_TOKEN` is dropped, and `ignored_env` lists the names.
  - **The pre-spawn assertion, on the final environment.** `Popen` is patched to record calls.
    - With `host_login.allowlisted_env` monkeypatched to leak `CODEX_API_KEY`, then `CODEX_ACCESS_TOKEN`, then `CODEX_FOO`, `spawn()` raises `BillingEnvError` naming the variable (never its value) before any `Popen`, and the run is untested.
    - An environment whose only strip-family name is `CODEX_HOME`, set by `CODEX.child_vars`, passes and reaches `Popen`.
    - With `run_env` patched to add `OPENAI_API_KEY` after the builder, the assertion still fires.
  - **`parse_quota` and `quota_problem`.** Each `quota-*.json` gives the expected outcome:
    - `quota-ok.json` passes;
    - `quota-no-credits.json` is refused as an unavailable read;
    - `quota-credits.json` names the balance and emptying it as the one remedy;
    - `quota-free.json` names the plan;
    - `quota-92.json` names the window and its reset time;
    - `quota-reached.json`, `quota-no-window.json` and `quota-error.json` are refused.
  - **Quota timeout.** `read_quota` against a fake app-server that never answers is unavailable after a patched short `QUOTA_TIMEOUT_S`, and the child is stopped.
  - **`billing_problem`.** It gives the spec's message for each of `provider-leak`, `no-rate-limits` and `credits-unreported` (plan use cannot be confirmed), `plan-free` (names the plan), `credits-drawn` (names the credits and emptying the balance as the one remedy), `limit-reached` and `model-rerouted`.
  - **`failure_reason`.** For `refresh-reused` and `restriction-logout` it names `uv run poe host-login codex` and closes with the Codex login note, parametrized over `X8_PASSED`: the X8 caveat while False, the not-affected sentence while True. `turn-failed` carries Codex's message, and `no-turn-completed` says so.
  - **Quota snapshot.** It holds only windows, reset times and the plan type.

  Verify that these fail before the change.

  *Done 2026-10-06* (failed before 3.2). Added: the quota handshake against a fake app-server script on a `PATH` of its own (initialize, initialized, the read with id 1), a reader that cannot start, and `run_codex` refusing a leak before the quota read starts anything.
- [x] 2.5 Command, readers and canonical tool calls, in `tests/unit/test_codex_cli.py`. Cases:
  - **The `command()` template.**
    - `--json`, `--strict-config`, `--skip-git-repo-check`, `-C <ws>`, `-s workspace-write`, `-m` verbatim, and the prompt on stdin;
    - every `DISABLED_FEATURES` entry as `--disable`;
    - `multi_agent` disabled unless the scenario has helpers;
    - network only when `needs_network` holds. Table-test it over every `SCENARIOS` entry: `import_messy`, the `supervise_*` and the `ideate_scoped*` entries are true, the rest false;
    - never `--ephemeral`, `--ignore-user-config` or `--dangerously-bypass-approvals-and-sandbox`;
    - the effort `-c` only when requested.
  - **`features_problem`.** `features-ok.txt` passes, and `features-extra-on.txt` names the feature.
  - **`codex_tool_calls`.** It covers each mapping row of design Decision 11. Through `routing.tool_calls`, `route_from_events(skill-read)` returns `proposal-check`, `verdict_supervise_verifier` passes on `helper-spawn`, and `verdict_single_context(…, 0)` fails naming `Agent`. Claude streams give the same calls as before.
  - **`codex_read`.**
    - `final_text` is the last agent message, and `model` is `"unreported"`, or the reroute target in `model-rerouted` (*superseded by 7.3a: the turn context's model, `"unreported"` only without one*);
    - `cli_version` comes from `codex.session`;
    - `tokens_in = input − cached`, `cost_usd is None`, and `notional_basis` is `"unpriced"` for an unknown name and `"roster"` for a name the shipped registry prices under `openrouter/openai/`. Use a synthetic registry text, not a shipped slug;
    - `effort-dropped` makes the run untested for a precondition reason, naming both efforts;
    - `foreign-skill`, `cloud-skill-tool` and `mcp-call` are untested for isolation.
  - **`capture_rollout`.** Over `rollout-success.jsonl` placed under a fake home's `sessions/…`, it appends only the reduced records, drops the extra `session_meta` fields, writes `quota.json`, and deletes `sessions/`. With no record, the run is untested with "plan use cannot be confirmed".

  Verify that these fail before the change.

  *Done 2026-10-06* (failed before 3.2). The untested checks run through `codex_cli.run_problem(events, skill_root=, effort=)`, which `codex_read` does not call: a re-grade reads the same events and must not refuse. The notional figure comes from `claude_runner.codex_rates` (the registry lives outside `codex_cli`). Added: `run_codex` end to end against a fake `codex` (quota read, feature listing, exec with the scratch `HOME` and no `CODEX_API_KEY`, capture), and both pre-exec refusals.
- [x] 2.6 Host seam and CLI, in a new `tests/unit/test_hosts.py` plus `tests/unit/test_dev_runner_probe.py`. Cases:
  - **Default host.** `main([...])` without `--host` behaves exactly as before. Every existing test in `test_dev_runner_probe.py` passes unmodified, apart from the added `host` and `label` summary keys.
  - **Usage errors** (exit 2, nothing staged, no process started) for:
    - `--host codex` without `--model`;
    - a model containing `/`;
    - `--max-budget-usd` on Codex;
    - an install scenario on Codex;
    - `--effort` on Claude;
    - `--effort ultra`;
    - `--summary-log logs/evals/x.jsonl` on each host, parametrized over `HOSTS`.
  - **Staging.** `stage(..., skill_dir=(".agents","skills"))` installs the skill and siblings with no `evals/`.
  - **End to end on Codex**, with `codex_cli.run_codex` faked to return `success.jsonl`: the summary carries `host: codex`, the label "dev-runner (codex), not comparable to matrix", `config: isolated`, the Codex home as `config_dir`, `login: harness`, `cost_usd: null` and the quota before and after.
  - **The judge's isolation (the L0 pin).** A fake Codex run, plus a stubbed Claude harness-login preflight, plus a recording fake `claude_cli.judge_all`. The `config` the judge receives is a Claude isolated configuration whose `.credentials.json` link resolves into the Claude harness home. Neither that path nor the judge child environment (`host_login.allowlisted_env` recorded) contains the Codex home or `CODEX_HOME`. The judge is entered after the fake Codex run returned. `--judge` on Codex needs no `--isolated`.
  - **`--rejudge --host codex`** on a kept workspace holding `success.jsonl` reads the served model through `codex_read` and starts no Codex process.
  - **Preconditions are untested, not runner failures.** With `codex_cli.run_codex` faked to raise `RunLockBusy`, then to report a feature outside the allowlist, then to return `effort-dropped.jsonl`, `main([...])` exits with the untested status (3), never the runner-failure status, and the summary's reason names the lock, the feature or both efforts.

  Verify that these fail before the change.

  *Done 2026-10-06* (collection failed before 3.3). `test_dev_runner_probe.py` needed no edit: every existing test passes unmodified. Added: a billing refusal records `billing` (so the smoke gate's log logic applies), a stubbed preflight refusal is untested and labelled, and the real preflight refuses a state root under the system temporary directory and creates nothing.

## 3. Implementation

- [x] 3.1 In `harness/host_login.py`:
  - add the `HostLogin` fields `strip_suffixes`, `stop_signal`, `outside_tempdir` and `child_vars`, with defaults that keep `CLAUDE` byte-identical in behaviour;
  - add `CODEX`, `PINNED_CONFIG`, `PINNED_CONFIG_TOML`, `CODEX_MIN_VERSION`, `check_codex_home`, `codex_status`, `codex_version`, `run_lock`, `RunLockBusy` and `LOCK_WAIT_S`;
  - give `check_location` its `tempdir` parameter;
  - add `run_host(record, argv, *, cwd, env, timeout, input=None, pass_fds=())` per design Decision 7 (change 2 has none), give `stop_child` a signal parameter defaulting to SIGTERM so that `run_host` passes the record's stop signal, and add the Linux parent-death `preexec_fn`;
  - add `RECORDS["codex"]`;
  - make the login note client-aware (design Decision 4): `LoginProblem` gains `client: str = "claude"`; add `NOTES` and `X8_PASSED = False`; `login_note(remedy, client="claude")` and `refusal(problem)` read the client; `login_remedy(message, source, record=CLAUDE)` matches `record.failure` and closes with that client's note;
  - make `login_env` record-driven, so the Codex login and every Codex logout drop the strip families and set `CODEX_HOME`;
  - read the Codex `last_written` age with `os.stat` only; nothing in the module opens `auth.json`.

  Wire `main(argv)` for `login|status|logout codex`, `--device-auth` and `status --quota` per design Decision 4, mapping `RunLockBusy` to exit 3. Verify that 2.1, 2.2 and 2.3 pass, that `uv run ruff check harness/host_login.py` reports no C901, that `grep -n "auth.json" harness/host_login.py` shows no `open`/`read_text`/`json.load` on it, and that the Claude sections of `test_host_login.py` are unchanged and green.

  *Done 2026-10-06.* All three checks hold. Choices and deviations, none changing a rule:
  - `child_vars(config)` is a method of `HostLogin` derived from the existing `home_var`, `fixed_env` and `profile` fields rather than a callable field, which keeps `CLAUDE` byte-identical; `HostLogin` also gains `allowed` (for `skills/.system`), `stripped(name)`, and `login_command`/`reset_command`.
  - `stop_child(proc, sig=SIGTERM)` still calls `terminate()` for SIGTERM (and on Windows) and `send_signal` otherwise, so the routing tests' stand-in hosts, which offer only `terminate()`, stay unmodified.
  - `run_host` gains an optional `start` (the Codex runner passes the starter that asserts the final environment), re-raises `TimeoutExpired` carrying what the child wrote, and starts children with `child_preexec(record)` (Linux `PR_SET_PDEATHSIG`).
  - The lock file is opened with `Path.open("ab")` and set to 0600 rather than `os.open(…, 0o600)`, because `test_repo_conventions.py` reads any `.open(` without `encoding=` as text I/O.
  - `check_location(…, record=, tempdir=)`; callers fill `tempdir` from `system_tempdir()`, the seam the L0 tests replace. `profile_problem` applies to the Claude commands only (the rebased spec scopes it so).
  - `host_login.cmd_status_codex` imports `codex_cli` inside the function: `codex_cli` imports `host_login`, and the status needs its probes.
  - Added beside the listed names: `check_codex_login`, `check_codex_version`, `config_difference`, `codex_offenders`, `auth_age`, `client_lock`, `version_text`, `system_tempdir`.
- [x] 3.2 Create `harness/codex_cli.py`, stdlib-only and importing `host_login` only:
  - `DISABLED_FEATURES`, `needs_network`, `command`;
  - `run_env`, `ignored_env`, `assert_codex_env` (on the final environment, exempting exactly `CODEX.child_vars`), `spawn`;
  - `read_quota`, `parse_quota`, `Quota`/`Window`, `quota_problem`, `QUOTA_STOP_PERCENT`, `QUOTA_TIMEOUT_S`, `ALLOWED_PLANS`;
  - `features_problem`, `capture_rollout`, `codex_tool_calls`, `codex_read`, `failure_reason`, `billing_problem`;
  - `isolated_home(stack, args)`, which runs the preflight and yields the home;
  - `run_codex(...)`, which takes the lock, then runs the quota read, the features preflight, the spawn with `pass_fds`, the capture, and the release.

  Findings are frozen dataclasses, and failure tables are data, so complexity stays at 12 or below. Verify that 2.4 and 2.5 pass and that `uv run ruff check harness/codex_cli.py` is clean.

  *Done 2026-10-06.* Both hold. Choices:
  - `codex_cli` imports `host_login` and the shape module `hosts` (for `RunView`; `hosts` itself imports only `host_login`), never `routing` or `claude_cli`, so no cycle arises.
  - `start(argv, *, cwd, env, stdin, pass_fds)` is the single `Popen` of every Codex child and asserts the final environment first; `spawn` (the app-server, left running) and `run` (to completion, through `host_login.run_host(start=start)`) both build the environment with `child_env` and go through it. `probe` wraps the short model-free commands.
  - The feature allowlist is checked under the run lock just before the run (and by `host-status codex`), not a second time in `preflight`; `preflight` checks the location, the CLI version, the home and marker, the ChatGPT login, then cleanliness, in the spec's order.
  - The after-run checks live in `run_problem` (failure with any explicit billing signal, then the billing guard, the isolation, the served effort); the claude_runner adapter maps them, as it maps `RunLockBusy`, `CodexRefused` and `CodexRunFailed`, onto the runner's outcomes. `RunProblem`, `Quota`, `Window`, `Credits` and `Rates` are frozen dataclasses.
  - A failed run whose session record shows an explicit billing signal is untested for billing, naming both (the Claude runner's precedent); a missing report is no explicit signal there.
- [x] 3.3 Create `harness/hosts.py` with `Host`, `RunView` and `JudgeBackend`. In `harness/claude_runner.py`, add:
  - the late-bound `HOSTS` and `host_for`;
  - `--host`, `--effort`, and the `--model` default change;
  - the usage guards of design Decision 3, including the `logs/evals` summary-log guard;
  - the untested mapping of the Codex preconditions (`RunLockBusy`, the CLI minimum, `features_problem`, an effort not served), per design Decision 12;
  - `stage(skill_dir)`;
  - `host` and `label` in `summary` and `failure_summary`;
  - the judge isolation per backend in `completed_run`, and the `resolve_judge` gate;
  - the host-aware `rejudge_lines`.

  In `harness/routing.py`, make `tool_calls` append `codex_cli.codex_tool_calls(events)`. Verify that 2.6 passes, that the whole `tests/unit/test_dev_runner_probe.py`, `test_routing.py`, `test_install_probe.py` and `test_isolated_env.py` stay green, and that `grep -n '".claude", "skills"' harness/claude_runner.py` shows only the Claude host's `skill_dir`.

  *Done 2026-10-06.* All hold. Choices: `Host` also carries `label` (the login label) and `always_isolated` (Codex), so `summary` and `failure_summary` hold no host branch; `RunView` carries `model_check`. `--rejudge --host codex` needs no `--model`. The usage guards are one table (`usage_problem`), checked before staging, and include `--host codex` without POSIX file locks. Re-grade lines also carry `host`.
- [x] 3.4 Update the module docstrings and usage lines:
  - `claude_runner.py`: the `--host codex` usage, the Codex billing guard, and the not-comparable label;
  - `codex_cli.py`;
  - `hosts.py`;
  - `host_login.py`: the Codex record, the lock and the stop signal.

  Verify by reading the diff, and confirm with `grep -nE 'gpt-[0-9]' harness/*.py pyproject.toml` (empty) that no model slug entered the code.

  *Done 2026-10-06.* The grep is empty.

## 4. Documentation

- [x] 4.1 Update `harness/README.md`:
  - **A new "Codex dev runner" section:**
    - dev loop only, with the label, never fed to `report.py`;
    - the one-time setup (CLI ≥ 0.160; after Plus, credit balance 0 and auto-reload off; then `host-login codex`);
    - the home and the lock;
    - the D4(a) posture;
    - the billing guard and each refusal's remedy;
    - the Claude judge (D3(a));
    - what is out of scope (smoke, routing, install probe, ambient);
    - "verified on Linux only";
    - the X-check status lines.
  - **The "Which path to use" table** gains a Codex row.
  - **"Known limitations".** Replace the "other agents remain untested (spec risk S5)" line: the dev runner covers Claude Code and Codex CLI, and the Codex parsers are pinned on synthetic streams until `record-codex-streams`.

  Verify that `uv run poe test` stays green, since README text is pinned by some L0 tests.

  *Done 2026-10-06.* The X-check lines record every check as pending, with the installed CLI (0.133.0) named.
- [x] 4.2 Update the `AGENTS.md` Commands block:
  - `uv run poe dev <scenario> --host codex --model <slug>` (subscription; plan quota; never a matrix input);
  - `uv run poe host-login codex [--reset] [--device-auth]` (the user only);
  - `uv run poe host-status codex [--quota]` (agents may run it; no model call);
  - `uv run poe host-logout codex` (the user only).

  Also add one sentence: the first Codex model call after any login needs the user's explicit go, like a metered run. Verify by reading the diff and with `uv run poe test`.

  *Done 2026-10-06.*

## 5. Gate

- [x] 5.1 Run `uv run poe test` (not `test-fast`) and confirm it is green: pytest, ruff with the full rule set, `test_repo_conventions.py` (`main(argv)`, no `sys.path`, every `verdict_*` tested), the drift check and conform.

  *Done 2026-10-06:* green (pytest, ruff, drift, conform).
- [x] 5.2 Run `uv run poe cov` and confirm that the 78 % floor holds with the new modules counted.

  *Done 2026-10-06:* total 91 %; `codex_cli.py` 90 %, `hosts.py` 100 %, `host_login.py` 95 %, `claude_runner.py` 92 %.
- [x] 5.3 Run `uv run poe specs` and `openspec validate add-codex-dev-runner --strict`, and confirm both pass.

  *Done 2026-10-06:* 20 of 20 items valid; the change is valid.
- [x] 5.4 Apply the review findings of 2026-10-06 (autonomous; L0 only, no model call). Each finding was checked against the code; fixed unless marked otherwise:
  - **Windows CI (blocker).** The `fcntl` usage rule now comes last and exempts `--rejudge`; `run_lock` raises `RunLockUnsupported` (a `RunLockRefused`, exit 3) instead of `RuntimeError`, and `host-login`/`host-logout codex` refuse before creating anything. The Codex end-to-end tests skip on `host_login.fcntl is None` (`LOCKS`, `POSIX`, `POSIX_LOCKS`), the seeding test included. Checked with a scratch plugin that sets `host_login.fcntl = None` over the whole `test-fast` lane: green.
  - **Codex logout at its limit (major).** `run_client` takes the record's `stop_signal`; `_logout` and `read_status` pass it, so a Codex logout gets SIGINT. L0: a real `run_client` against a fake `codex` that traps SIGINT. `run_client` now also drains the pipe after the stop (a ResourceWarning the new test exposed).
  - **A timed-out run skipped the after-run checks (major).** `codex_cli.timeout_problem` applies the explicit billing signals and the isolation check to the session record captured before the raise; `claude_runner.run_codex` maps it. A failed run that shows a broken isolation is untested too (`_untested_failure`, formerly `_with_billing`).
  - **Plan use unconfirmed on a failed run.** Rebutted, recorded as a choice: a failed or timed-out run without a quota report stays a runner failure, because the scenario "Codex interrupted before kill" requires a runner failure naming the limit. The spec's "After every run" list now says so, with the new scenario "Timed-out run that drew credits", and design Decision 12 matches (revised through the `openspec-update-change` skill without its per-edit confirmation, as in 0.1; L0: `test_a_codex_run_at_its_limit_is_checked_like_any_other`).
  - **Fail-open quota parsing (major).** A credits block must carry boolean `hasCredits`/`has_credits` and `unlimited` and a balance that is absent, null or a finite number, else the read is unavailable (before) or plan use cannot be confirmed (after); a window without a numeric used percentage is unavailable.
  - **Status against unadopted homes (major, and the `--quota` minor).** `codex_cli.status` runs `login status`, `features list` and the quota read (and creates the lock file) only for an accepted location and a present, marked, owner-only, clean home; otherwise `logged_in: unknown` and `quota: not read`.
  - **Untested coverage gaps.** L0 cases for the usage-limit error (three event shapes, `billing` set), all three refresh-failure wordings (two event shapes, both `X8_PASSED` values), the timeout path end to end against a fake `codex` (session record captured and deleted, `codex.harness` last, lock free) and through `main` (exit 4 naming the limit, or 3 with the billing or isolation cause).
  - **Feature parser (minor).** Any non-blank line that is not one `name stage state` row refuses, naming the line.
  - **Lock descriptor (two minors).** The fake `codex` now reports whether it holds the lock's open file description, and the end-to-end test asserts it. A lingering model process keeping the lock is recorded for task 7.3; `RunLockBusy`'s cause names `fuser -v <lock>`.
  - **`CODEX_HOME` by value (minor).** `assert_codex_env(env, home)` refuses a missing `CODEX_HOME` or one naming another directory, naming the variable, never its value.
  - **Judge pin (minor).** The test now fakes `claude_cli.run_child` and records `host_login.allowlisted_env`, so the real judge path builds the children's environments.
  - **Re-grade label (minor).** `rejudge_lines` carries `label: host.run_label`.
  - **`kind` by substring and unused seam fields (minors).** `LoginProblem` gains `kind` (default `subscription`), set where the problem is built (`check_codex_version`, `features_problem`, the run lock: `precondition`); `CodexRefused.of(problem)` reads it. Deviation from design Decision 2's sketch: `JudgeBackend.call`/`preflight` and `Host.binary` are dropped, since nothing read them (the judge reaches `claude_cli.judge_all` through `run_judge`; a host's binary is its login record's). `RunProblem.kind` stays: the L0 tests pin the classification.
  - **Per-client branches (minor).** `HostLogin` gains `run_locked`, `login_in_status`, `offenders` and `status_command`; the profile rule follows `record.profile`; no `record.name ==` branch remains in `host_login`, and `wipe(home_dir, record)` is called the same way for every client (the Claude test's stub updated).
  - **Login and logout environment (minor).** Narrowed the docs rather than adding a check: `codex_cli.start`'s docstring and the README name the children the guard covers; the login and logouts run in `login_env`, which drops the same families by construction.
  - **Fixture provenance (minor).** Every README row names its source file and tag.

- [x] 5.5 Port the workspace check after the run from `add-copilot-dev-runner` (the user's decision D-d, 2026-10-06; design Decision 16; spec: the Codex isolation paragraph, the Codex clear option and status line, the run lock's "every clear", and the scenarios "Codex workspace entry the runner must not follow" and "Recorded Codex stop refuses later runs", mirrored into `add-copilot-dev-runner`'s MODIFIED blocks). L0 only, no model call.
  - *Done 2026-10-07: code, L0 and docs, as listed below.* The Copilot copies moved into `harness/workspace_guard.py` unchanged in behaviour (`copilot_cli.workspace_breach` wraps `breach` with its token scrub; the Copilot suite passes unchanged apart from the two constants it now reads from the shared module). Codex has no stop machinery before this task, so the isolation stop is new: `stop.json` beside `quota.json` (which `capture_rollout` overwrites), read in the preflight right after the location (before `codex --version`) and again under the run lock, cleared by `host-login codex --clear-stop`, printed by `host-status codex` (a new `stop` key). Unlike Copilot, Codex has no live watch and kills no process group, so a process the run left running could still change the workspace after the check (design, the risk row). L0: the stop store (append, damage, clear touching nothing else, the clean home with `stop.json`), a stop refusing in the preflight with no Codex process and under the lock with no quota read and no exec, planted links, a FIFO and a hard link removed unfollowed with both targets untouched and the stop recorded, a replaced workspace (the link in its place removed, its target untouched), a time-limited run with a planted link untested for isolation, a clean workspace no finding, an end-to-end run through the runner (exit 3, no verdict, the event file created afresh beside the removed link, the victim unchanged, the secret in no output, the stop recorded), and `--clear-stop` for Codex in `test_host_login_cli.py` (both speed bumps, the stop removed, every other file unchanged, no client call, the status line before and after). `CODEX_STATUS_KEYS` gains `stop`.
  - **Shared code:** `harness/workspace_guard.py` (stdlib-only) with `workspace_identity`, `unsafe_entry`, `workspace_entries`, `unsafe_entries`, `replaced` and `breach`; `copilot_cli` imports them and keeps its names.
  - **`codex_cli`:** the workspace's identity before the first child; `workspace_breach` right after the child (a time limit included), before the session capture, the save and any verdict; `workspace_breach` in `codex.harness`; `planted_problem` first in `run_problem` and `timeout_problem`; the stop store `stop.json` (`read_stop`, `record_stop`, `clear_stop`, `stop_problem`; a damaged record reads as a stop); the stop row after the location and before `codex --version` in `preflight`, again under the run lock in `run_codex`; the `stop` line of `host-status codex`.
  - **`host_login`:** `--clear-stop` for Codex (terminal and agent-marker refusals, the run lock, nothing else touched).
  - **L0 tests** (`test_codex_cli.py`, `test_host_login_cli.py`): planted links, a FIFO and a hard link removed unfollowed with their targets untouched, a replaced workspace, the run untested for isolation with a stop, a recorded or damaged stop refusing before any Codex process, the stop re-read under the lock, `--clear-stop` for Codex, the status line, and an end-to-end run through the fake `codex` that plants `broken-format.md → secret` and `.devrun-events.jsonl → victim`.
- [x] 5.6 Apply the review of task 5.5 (2026-10-07; design Decision 16, "Fail closed" and "A reset keeps the stop"; spec: the Codex isolation paragraph, the Codex clear option, and the scenarios "Codex workspace directory the runner cannot list" and "Codex reset keeps the isolation stop", mirrored into `add-copilot-dev-runner`'s MODIFIED blocks). L0 only, no model call.
  - *Done 2026-10-07: code, L0 and docs, as listed below (with `add-copilot-dev-runner` task 7.16, which shares the guard).* The closed-directory cases fail on the old guard (the root and the subdirectory case both read as no breach there). Gates as recorded under that task.
  - **`workspace_guard`** (shared with Copilot): the workspace and every directory found must be owner-`rwx`; a listing error (`os.walk`'s `onerror`) and an entry whose `lstat` fails are breaches; nothing is chmodded or reopened.
  - **`host_login`:** a Codex reset reads the isolation stop before the wipe and records it again in the reseeded home, cause and time unchanged.
  - **L0 tests:** a 0300 workspace root with a link and a 0300 subdirectory with a link, each untested for isolation with the stop recorded and no fixed name opened (`test_codex_cli.py`, and the same for Copilot in `test_copilot_cli.py`); a Codex reset with a recorded stop keeps it (`test_host_login_cli.py`); the end-to-end planted-workspace test now starts a second run and asserts it is refused by the stop, as its docstring claimed.

## 6. CLI update and rehearsal on the free plan (D6(b), no model call)

- [x] 6.1 **USER ACTION:** `sudo pacman -S openai-codex` (to 0.160 or later). The agent then runs `codex --version` and records the version string here. Pass: at or above `CODEX_MIN_VERSION`.

  ~~*Pending: user action (2026-10-06).* The installed CLI is 0.133.0, below the minimum; the preflight refuses it with the update remedy (pinned by `test_codex_version_parses_and_refuses_an_old_cli`).~~
  *Done 2026-10-13 (recorded late; the update itself ran 2026-10-05 23:20:39 +0200, pacman `upgraded openai-codex (0.133.0-1 -> 0.160.0-1)`): passed.* `codex --version` prints `codex-cli 0.160.0`, equal to `CODEX_MIN_VERSION` (0, 160, 0). No model call. ChatGPT Plus is not bought and no harness Codex home exists yet, so 6.2 (X7) is next and 6.3 onward wait on the user.
- [x] 6.2 X7, run by the agent, with no login and no network, so no model call is possible:
  1. Create an empty scratch `CODEX_HOME` at `${XDG_CACHE_HOME:-~/.cache}/thesis-proposal-dev/x7-probe`, holding only `PINNED_CONFIG_TOML`, and an empty scratch `HOME` beside it. The session scratchpad and its parent both lie under `/tmp`, where Codex refuses to place its helper binaries, so they are not used here. Before running, confirm that the resolved scratch `CODEX_HOME` lies neither inside the directory `python3 -c 'import tempfile; print(tempfile.gettempdir())'` prints nor inside the repository; if it does (for example because `XDG_CACHE_HOME` points into `/tmp`), stop and report.
  2. Run `unshare -rn env -i PATH="$PATH" HOME=<scratch-home> CODEX_HOME=<scratch-codex-home> codex features list <the run's --disable flags>`. Record each feature's name and state.
  3. Repeat once with an unknown nested key added to the scratch `config.toml`, passing `--strict-config` where the subcommand accepts it. Record whether it is refused.

  Pass: every pinned key is accepted, and only the allowlist reads enabled. Otherwise update `PINNED_CONFIG`/`DISABLED_FEATURES` (and their fixtures) through the `openspec-update-change` skill and rerun 5.1. Delete `${XDG_CACHE_HOME:-~/.cache}/thesis-proposal-dev/x7-probe` and the scratch `HOME`, and record the outcome in the README's X-check lines.

  ~~*Pending: live check (2026-10-06)*, after 6.1: X7 is meant for the 0.160 CLI, and this run starts no `codex`.~~
  *2026-10-13, codex-cli 0.160.0, run by the agent under `unshare -rn` with no login: FAILED on the feature listing; the config half passed.* Scratch homes `~/.cache/thesis-proposal-dev/x7-probe` and `x7-home` (outside `/tmp` and the repository), both deleted afterwards.
  - **Pinned keys:** accepted. `codex exec --json --strict-config` with `PINNED_CONFIG_TOML` loaded the config and got as far as the network (`failed to lookup address information`, no network in the namespace, no login), so no model call was possible.
  - **Unknown nested key:** `codex features list` does not take `--strict-config` ("unexpected argument") and ignores an unknown key; `codex exec --strict-config` refuses it: "unknown configuration field `history.x7_unknown`". The run passes `--strict-config` to `exec`, so a misspelled pinned key still fails visibly.
  - **Listing format:** 0.160 prints multi-word stages (`under development`), so those rows have four fields and `parse_features` returns them as unparsed. Every run would refuse with "printed a line the parser does not read".
  - **Allowlist:** with the run's `--disable` flags (every name accepted, exit 0), 25 features outside `ALLOWED_FEATURES` still read enabled: `auth_elicitation`, `browser_use_full_cdp_access`, `code_mode_host`, `compaction_image_budget`, `content_item_kinds`, `daemon_auto_start`, `enable_request_compression`, `guardian_reuse_parent_compaction`, `in_app_chat`, `in_app_dictation`, `in_app_local_automation`, `in_app_updates`, `mentions_v2`, `realtime_conversation`, `remote_plugin`, `shell_snapshot`, `skill_search`, `sleep_tool`, `system_proxy_fallback`, `tool_call_mcp_elicitation`, `unbounded_connection_retries`, `unified_exec_tty`, `view_image`, `worktrees`, `write_stdin_approval`. Nine `removed`-stage features also read true. With all of them added as `--disable` (exit 0), every non-removed one reads false; five `removed` ones stay true regardless (`item_ids`, `resize_all_images`, `terminal_resize_reflow`, `tool_search_always_defer_mcp_tools`, `tui_app_server`).
  - **Next:** through `openspec-update-change`: the parser reads a multi-word stage; `removed` features are ignored by the allowlist check (they do nothing); each of the 25 is either disabled or allowed with a reason. Then rerun 5.1 and X7.

  *Rerun 2026-10-13, after 6.2a, codex-cli 0.160.0, by the agent under `unshare -rn` with no login and no network, so no model call was possible: PASSED.* Scratch `CODEX_HOME` `~/.cache/thesis-proposal-dev/x7-probe` holding exactly `PINNED_CONFIG_TOML`, scratch `HOME` `~/.cache/thesis-proposal-dev/x7-home`; both resolved outside `tempfile.gettempdir()` (`/tmp`) and outside the repository, and both were deleted afterwards. Each listing was fed to the harness's own `features_problem` with `allowed_features(scenario)`.
  - **Without helpers** (`check_report`; `feature_flags` gives 33 `--disable` names, `multi_agent` among them): `codex features list` exit 0, 154 rows; `features_problem -> None`. Enabled at a stage other than `removed`: only the twelve `ALLOWED_FEATURES`.
  - **With helpers** (`supervise_scope`; 32 `--disable` names, no `multi_agent`): exit 0; `features_problem -> None`. The listing differs from the first only in `multi_agent stable true`.
  - In both, nine `removed` features read true and are ignored (`collaboration_modes`, `item_ids`, `resize_all_images`, `sqlite`, `steer`, `terminal_resize_reflow`, `tool_search_always_defer_mcp_tools`, `tui_app_server`, `unified_exec_zsh_fork`). The listing printed five stages: `under development` (60 rows), `stable`, `experimental`, `deprecated`, `removed`; the parser pins exactly that set.
  - The config half was not rerun: `PINNED_CONFIG_TOML` is unchanged since the first run.
- [x] 6.2a Apply the X7 findings (the user's decision Q7b, 2026-10-13; design Decision 5, spec scenarios "Multi-word feature stage", "Removed feature reading enabled", "Feature listing line the parser does not read"):
  - `parse_features` reads a row as name (first token), stage (the tokens between, one of `FEATURE_STAGES`: `under development`, `experimental`, `stable`, `deprecated`, `removed`) and state (last token, a known on/off word), and returns `{name: (stage, enabled)}`; every other non-blank line stays unparsed and refuses.
  - `features_problem` ignores a feature at the `removed` stage. *Narrowed 2026-10-13 by review:* only a `removed` row named in `REMOVED_ENABLED` (the nine X7 names reading true) is ignored; any other `removed` feature reading true refuses, and so does a `DISABLED_FEATURES` name reading true at any stage. Verified offline the same day (`unshare -rn`, scratch homes, deleted afterwards, no login): removed rows still follow the flags (`--disable steer`/`sqlite`/`collaboration_modes` turn them false, `--enable codex_git_commit` turns one true), so the stage alone does not show a feature is inert.
  - `DISABLED_FEATURES` gains `daemon_auto_start`, `remote_plugin`, `skill_search`, `mentions_v2`, `worktrees`, `browser_use_full_cdp_access`, `code_mode_host`, `realtime_conversation`, `in_app_chat`, `in_app_dictation`, `in_app_local_automation`, `in_app_updates`, `auth_elicitation`, `tool_call_mcp_elicitation`, `write_stdin_approval`; the 0.133 entries stay (every name accepted at 0.160, `plugin_hooks` at the `removed` stage included). *`code_mode_host` moved to `ALLOWED_FEATURES` by 7.3a.*
  - `ALLOWED_FEATURES` gains `shell_snapshot`, `unified_exec_tty`, `content_item_kinds`, `enable_request_compression`, `compaction_image_budget`, `unbounded_connection_retries`, `system_proxy_fallback`, `sleep_tool`, `view_image`, `guardian_reuse_parent_compaction`, each with a one-line reason comment.
  - L0 tests in `tests/unit/test_codex_cli.py`: a multi-word stage parses; a pinned `removed` feature reading true passes, an unpinned one (and `apps removed true`) refuses, and `REMOVED_ENABLED` holds no disabled name; an unknown enabled feature at every other stage refuses; garbage rows (five fields, an unknown stage, a stage with no name) refuse; the reduced 0.160 listing passes without helpers and, with `multi_agent` true, with helpers only. Fixture `tests/unit/data/codex_streams/features-0160-ok.txt` (63 of the rerun's 154 rows), with its README row.
  - The comments that said X7 would confirm the format and the key names (`codex_cli.py`, `host_login.py`, the fixtures README) now state the measured facts; `harness/README.md` records X7 and the CLI update as done.
  - Rerun 5.1 and X7 (record under 6.2).

  *Done 2026-10-13.* `uv run poe test` green; X7 rerun passed (under 6.2).
- [x] 6.3 X1, **USER ACTION:** in a terminal, `uv run poe host-login codex` with the free ChatGPT account. Add `--device-auth` only if it is enabled in the ChatGPT security settings. The agent then runs `uv run poe host-status codex`. Pass requires all of these: `marker: yes`, `logged_in: yes`, `auth_method: chatgpt`, `config_pinned: yes`, `clean: yes`, `features_ok: yes`. Record the values, booleans and enums only. From here on the home holds a free-plan login. Every `--host codex` run refuses on the plan rule before any `exec`, and no agent starts one before task 7.3.

  ~~*Pending: user action, then live check (2026-10-06).*~~
  *Done 2026-10-13: passed, on the Plus account directly.* The user had bought Plus, so the free-plan rehearsal was skipped and this login also serves 7.2. The user ran `uv run poe host-login codex` (browser flow, no `--device-auth`); `uv run poe host-status codex` read `marker: yes`, `logged_in: yes`, `auth_method: chatgpt`, `config_pinned: yes`, `clean: yes`, `features_ok: yes` (under the 9e0f48c feature policy), `cli_version: 0.160.0`, `stop: none`. The user's own `~/.codex/auth.json` mtime stayed 1780433511 (2026-06-02) before and after.
- [ ] 6.4 X8, **USER ACTION** (observation, no command beyond these):
  1. With a ChatGPT session open in the desktop app or on the web, run `uv run poe host-logout codex`, then `uv run poe host-login codex`.
  2. Confirm that the other session still works without a new sign-in.

  The agent records `stat -c %Y ~/.codex/auth.json` before and after (mtime only), and it must be unchanged. Pass: both hold. Then set `host_login.X8_PASSED = True`, which swaps the caveat for "Your own Codex login is not affected" in every message, and confirm that `uv run poe test` stays green. Do it here if this change is not yet archived, otherwise as a task in `record-codex-streams`. If the other session was signed out, keep `X8_PASSED = False`, document it in the README, and relay it to the user.

  *Pending: user action (2026-10-06).* `X8_PASSED` is False; the L0 tests cover both values.
- [x] 6.5 X4b, run by the agent, with no model call: `uv run poe host-status codex --quota`. Record:
  - whether the handshake answered;
  - the window durations and used percentages;
  - the plan type;
  - whether a credits block is present.

  On the free plan the command exits 3 by design, because the plan rule refuses; that is not a failure of X4b. Pass: an answer with at least one window. If the handshake fails, D2(a) makes Codex unusable. Record the failure and relay the D2 choice to the user. If the answer carries no credits block, record it and tell the user that every run will refuse on that read until the Plus answer in 7.2 shows the block, or a reviewed change relaxes the rule. Do not change either refusal on your own.

  ~~*Pending: live check (2026-10-06)*, after 6.1 and 6.3.~~
  *Done 2026-10-13: passed.* `uv run poe host-status codex --quota` exited 0: the handshake answered; `plan plus`; 5-hour window 0% used (resets 2026-10-13 14:21 UTC); weekly window 0% used (resets 2026-10-20 09:21 UTC); a credits block is present with no credits (`credits none`). No model call.

## 7. After Plus (gated)

If Plus has not been bought when sections 0 to 6 are done, mark each task here as deferred, and carry it into the proposal of `record-codex-streams` before archiving.

- [x] 7.1 **USER ACTION** (in ChatGPT settings, no command):
  - set the Codex credit balance to 0, with automatic reload off;
  - optionally turn "Improve the model for everyone" off.

  Confirm here, yes or no only.

  ~~*Pending: user action (2026-10-06).*~~ *2026-10-13: yes.* The user confirmed automatic reload is off; the quota read in 6.5 shows no credits.
- [x] 7.2 **USER ACTION:** `uv run poe host-login codex --reset`, so that the login carries the Plus plan. The agent runs `uv run poe host-status codex --quota`. Pass: ready (exit 0), the plan type reads `plus`, and a credits block is present with a zero balance and no credits available. Record the window usage. If the credits block is absent, every run refuses; record it and relay the choice to the user, whose relaxation of the rule would go through `openspec-update-change`. Do not proceed to 7.3 meanwhile.

  ~~*Pending: user action, then live check (2026-10-06).*~~
  *Done 2026-10-13: passed without a `--reset`.* The 6.3 login was made on the Plus account, so it already carries the plan: the 6.5 read is ready (exit 0), plan `plus`, the credits block present with no credits available, both windows at 0%.
- [ ] 7.3 The first Codex model call: **gated on the user's explicit go**, asked for in chat with the planned command. It uses plan quota, not money. Command: `uv run poe dev check_report --host codex --model <slug the user names> --keep`. Pass requires all of these:
  - the outcome is not untested for a billing, login or isolation reason;
  - the summary records the CLI version, `effort_served`, and quota before and after;
  - the kept events hold `codex.session`, `codex.turn_context` and `codex.token_count` with `rate_limits` and `plan_type` (X4);
  - `codex.skills` lists only the workspace's skill (X9): every locator resolves through its record's `roots` into `<ws>/.agents/skills` (added by 7.3a);
  - the run's tool calls reach the shell: no "code-mode host is disabled" error item, and the shell commands appear as `command_execution` items, which Decision 11 maps (added by 7.3a: unverified under code mode);
  - the summary's `model` names the turn context's model, not `unreported` (added by 7.3a);
  - once the run has ended, the run lock is free: `fuser -v <home>/.harness-run.lock` shows no holder (added by the review of 2026-10-06: the lock descriptor is inheritable, so a process the model left running could hold it).

  Record the results here, then delete the kept workspace after `record-codex-streams` has reduced it. Do not run a second Codex scenario, or `--judge`, without a new go.

  ~~*Pending: live check, gated on the user's explicit go (2026-10-06).*~~
  *Attempt 1, 2026-10-13, on the user's go in chat (Q18: "Go, gpt-6.1-sol (Recommended)"): FAILED, untested for isolation, exit 3.* Command `uv run poe dev check_report --host codex --model gpt-6.1-sol --keep`, 30 s (`duration_ms` 30022), one turn, exit 0 from `codex`. Message: "untested: the run offered skills outside /tmp/devrun-check_report-rs91a3mw/.agents/skills: r0/proposal-check/SKILL.md. The run's isolation did not hold". The kept workspace is `/tmp/devrun-check_report-rs91a3mw`, and its `.devrun-events.jsonl` holds the reduced events.
  - **Billing held.** Provider `openai`, CLI 0.160.0, plan `plus`, credits `has_credits: false`, `balance: "0"`. Usage: input 28182 tokens, of which 18304 were cached, output 240 (reasoning 14). Both quota windows read 0 % before and after. `host-status` reads clean afterwards, `stop: none`. The kept events hold `codex.session`, `codex.turn_context` and three `codex.token_count` with `rate_limits` and `plan_type`, the X4 shape. No model call was made in the analysis below.
  - **Cause 1: the tool host was disabled.** X7 had put `code_mode_host` in `DISABLED_FEATURES`, and Q7b accepted it on that proposal. The plan's catalog serves every listed model code-mode-only (design, Codex facts "Tool mode"). Every tool call failed: an `error` item said "Code Mode is unavailable because code-mode host is disabled …", stderr logged `error=code-mode host is disabled` twice, and the model answered that it could not access `broken-format.md` or the skill. The turn still completed, and `codex` exited 0. Only cause 2 kept the run from being graded as the model's failure.
  - **Cause 2: the skills locator was misread.** 0.160 offers skills as `(file: r0/proposal-check/SKILL.md)` under a `### Skill roots` table. The reduction kept the locator but not the table, and the isolation check resolved `r0/…` against the runner's own working directory, so it read the skill as foreign. The design's fact `(file: /abs/SKILL.md)` was wrong for 0.160. The refusal was fail-closed, but X9 stays unanswered for this attempt. `capture_rollout` deleted the session record as designed, and `thread_history_1.sqlite` keeps no developer message: read from a copy, it holds four items, the prompt, two agent messages and a reasoning item. So attempt 1's root table cannot be recovered.
  - **Cause 3: the served model was not read.** `codex.turn_context` carried `{"model": "gpt-6.1-sol", "effort": null}`, but the summary read `"model": "unreported"`. By design, only a reroute named the served model.
  - **Seen in passing, not acted on.** The harness home keeps the run's thread after `sessions/` is deleted. `state_5.sqlite` has a `threads` row naming the workspace, the model, the provider and the first user message, and `thread_history_1.sqlite` has the four items above. The prompts are synthetic, but "delete the session record" does not cover these copies.
  - **Next:** 7.3a, then the rerun on a new go. The command is unchanged.
- [x] 7.3a Apply the findings of 7.3 attempt 1. This is autonomous and L0 only, with no model call. The feature move falls under the user's Q7b rule ("plumbing allowed with a reason"). Design: Codex facts, Decisions 5, 10 and 12, and Risks. Spec: the isolation paragraph, the effort line, the served-model line, and the scenarios "Skill offered through a root alias" (new) and "Codex run reports no cost".
  - `code_mode_host` moves from `DISABLED_FEATURES` to `ALLOWED_FEATURES`, with its reason and the live evidence in the comment. Nothing else is enabled.
  - Offline check, 2026-10-13, under `unshare -rn` with scratch `CODEX_HOME` and `HOME` in `~/.cache/thesis-proposal-dev/offline-codemode-check`, no login, so no model call was possible. The directory was deleted afterwards.
    - `codex features list` under the new flags: exit 0, 154 rows. Enabled are `code_mode_host` (stable), the twelve earlier allowed features, and the nine pinned `removed` ones. `code_mode`, `code_mode_only`, `code_mode_interrupt` and `code_mode_prewarm` (under development) and `code_mode_buffered_exec` (removed) read false and stay outside the allowlist.
    - `codex-code-mode-host` is installed beside `codex` in `/usr/lib/openai-codex/bin/`, owned by `openai-codex 0.160.0-1`. `--help` lists only a transport (`stdio` by default) and two trace exporters. No extra install is needed.
    - `codex debug prompt-input` rendered the skills block with a workspace skill and a scratch-`HOME` skill: ``- `r0` = `<home>/.agents/skills` ``, ``- `r1` = `<ws>/.agents/skills` ``, and `(file: r1/proposal-check/SKILL.md)`.
  - The reduction keeps each skills message's own root table: `codex.skills` gains `roots`. `offered_skills` and `skill_path` resolve an `rN/` locator only through that table to an absolute root, take an absolute locator as it is, and return every other locator as unresolved. That covers an unknown alias, a relative root, an alias named twice, a bare relative path, and a record without `roots`. `isolation_problem` refuses unresolved locators as well as ones outside the skill directory. Attempt 1's kept record still refuses, now as unresolved.
  - `codex_read`: `model` is a reroute's target, else the last turn context's `model`, else `unreported`, with `model_check` when it differs from the requested name. `effort_served` is the turn context's effort, or `unreported`.
  - L0 tests in `tests/unit/test_codex_cli.py` and `tests/unit/test_hosts.py`:
    - the allowlist holds `code_mode_host` and the command no longer disables it, while each other code-mode feature reading enabled refuses;
    - ten locator cases: alias inside, absolute inside, attempt 1 without a table, unknown alias, relative root, bare relative, alias only, root outside, traversal, absolute outside;
    - per-message tables and a doubled alias in the reduction;
    - the turn-context model and effort, with and without a turn context, a differing model, the last turn context winning, and the reroute precedence.
  - Fixtures: `rollout-success.jsonl` carries the 0.160 skills block. `success.jsonl` and `foreign-skill.jsonl` carry `roots` and `rN/` locators. `features-0160-ok.txt` reads `code_mode_host` true and gains the five other `code_mode*` rows (68 rows). Each has its README row, and the README gains the rendering note.
  - Docs: `harness/README.md` and the `codex_cli.py` docstrings and comments.
  - Gates: `uv run poe test` (full), `openspec validate add-codex-dev-runner --strict`, `python3 scripts/sync_shared.py --check`.

## 8. Close

- [ ] 8.1 Commit the code, tests, fixtures, docs and this change folder as one commit for the completed change, off `main` until it is complete. Do not push. Verify with `git status` (clean) and `git show --stat HEAD`.

  *Pending: live checks (2026-10-06).* The L0 implementation (sections 0–5) is committed on branch `host-runners`, off `main`, not pushed; the closing commit follows sections 6 and 7.
- [ ] 8.2 Archive through the `openspec-archive-change` skill, after sections 0 to 6, with section 7 either done or marked deferred as its preamble says, and only once both earlier changes are archived (`openspec list` shows neither `close-claudeai-surfaces` nor `add-harness-claude-login`). Change 2's archive waits for its L1. Before archiving:
  - repeat task 0.1's rebase check, scoping check and name-by-name check against the archived main spec;
  - run `openspec validate add-codex-dev-runner --strict`, which must pass with no "Archive would refuse" line.

  Verify that `openspec validate --all --strict` is green afterwards. The follow-up change `record-codex-streams` (recorded fixtures, X4/X9 outcomes, and the `X8_PASSED` flip if it happens after this archive) is separate.

  *Pending: live checks (2026-10-06).* Both earlier changes are archived; this change stays open until sections 6 and 7 are done or deferred.
