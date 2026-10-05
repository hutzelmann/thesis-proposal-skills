# Tasks

Ground rules for every task below:

- **Model calls.** No task before section 7 makes a model call of any kind: no `claude -p`, no `codex exec` against a login, no OpenRouter.
- **Logins.** Agents never run login commands. A step marked **USER ACTION** is run by the user, with the exact command given.
  - Agents may run `uv run poe host-status codex` and `uv run poe host-status codex --quota`. Neither makes a model call; the quota read is a GET of plan usage.
  - Agents never run `poe host-login` or `poe host-logout`.
- **Credentials.** Nobody opens or prints a credentials file (`auth.json`, `.credentials.json`). The one exception in code is change 2's expiry reader in `host_login`, which parses only the `expiresAt` field of the Claude home's `.credentials.json`. The Codex `auth.json` is never opened, by code or by an agent; its age comes from `stat`. Reports carry only booleans, counts, enums, version strings, file modification times (`stat`, never contents) and names. They never carry a credential, an environment value, an email address or an account identifier.
- **Workspaces.** Codex workspaces are temporary directories outside the repository. The private proposals directory is never a workspace.

## 0. Precondition

- [ ] 0.1 Confirm that both earlier changes are implemented, with their spec text final. Change 1 is already archived, because change 2's own precondition (its task 0.1) requires that before change 2's code is written. Only change 2's archive may still be pending: it waits for its L1, more than 8 h of idle time after its login (design, Migration Plan). Check:
  - `openspec list` no longer shows `close-claudeai-surfaces`;
  - both changes' code sections and gates are checked off in their `tasks.md` (change 1's in its archived copy);
  - `harness/host_login.py` exposes `HostLogin`, `RECORDS`, `allowlisted_env`, `login_env`, `AGENT_MARKERS`, `TERM_GRACE_S`, `stop_child`, `LoginProblem`, `refusal`, `login_note`, `L3_PASSED`, `login_remedy` and `main`, and `routing.follow_stream` stops through `stop_child`. `run_host` is not expected: this change adds it (task 3.1).

  Then:
  - If change 2's final text of "Harness-owned host logins", "Dev-runner cost and helper-agent telemetry" or "Subscription text roles (dev runner)" differs from what this change's MODIFIED blocks start from (change 2 as revised on 2026-10-05), rebase them through the `openspec-update-change` skill. Change 1's text, which change 2's blocks fold in, is the archived main spec's (`openspec/specs/testing-harness/spec.md`), never its change folder's.
  - Confirm that change 2's final text still scopes "Isolated child environment" and the authentication, opt-out and account-surface rules of "Isolated measurement environment" to Claude, and leaves a later client's child to the requirement that adds it. If it does not, add MODIFIED blocks for both through `openspec-update-change`, as design Decision 1 describes, before any code.
  - Repeat the name-by-name check: every scenario name of the three shared requirements, in change 2's final text, appears in this change's blocks.
  - Verify with `openspec validate add-codex-dev-runner --strict`. Until change 2 is archived, the only allowed INFO line is "Archive would refuse … Harness-owned host logins - not found"; task 8.2 requires it gone.

## 1. Fixtures

- [ ] 1.1 Create `tests/unit/data/codex_streams/` with synthetic saved event lists. Each file is exec events plus reduced `codex.*` records (design Decision 10), derived from the rust-v0.160.0 sources: `exec_events.rs`, `event_processor_with_jsonl_output.rs`, `protocol.rs`, and the `manager.rs` messages. Model names are `gpt-fixture-a` and `gpt-fixture-b`. Files:
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

- [ ] 2.1 Codex record and home, in `tests/unit/test_host_login.py`, as a new section. Use `THESIS_PROPOSAL_DEV_STATE` under `tmp_path`, and `check_location(..., tempdir=<a separate directory>)`. Cases:
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
- [ ] 2.2 Codex commands, in the CLI section of `tests/unit/test_host_login.py`. Fake the binary through the runner seam, never the real `codex`. Cases:
  - **Login environment.** It drops `CODEX_API_KEY`, `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `OPENAI_BASE_URL` and every `CODEX_*`, keeps `DISPLAY`, and sets `CODEX_HOME=<home>`.
  - **Login argv.** It is `login`, with `--device-auth` passed through, and never `--with-api-key` or `--with-access-token`.
  - **Existing login.** Logout runs before login while the run lock is held.
  - **`--reset`.** It wipes the marked home and reseeds it.
  - **Messages.** With `X8_PASSED` False, the logout, reset and login-over-login paths print the X8 caveat before the fake logout runs. With it True, none does.
  - **Status.** `status codex` prints only the keys of design Decision 4, which are the spec's status list (`capsys`): `home`, `marker`, `logged_in`, `auth_method`, `config_pinned`, `clean`, `last_written`, `cli_version`, `min_version`, `features_ok`, `last_quota`, `runs_use`. No key fragment, email or account identifier appears. It exits 0 when ready and 3 when not.
  - **`auth.json` never opened.** A synthetic `auth.json` is given a known modification time with `os.utime`, and `builtins.open`, `io.open` and `Path.read_text`/`read_bytes` are patched to fail on that path. `last_written` reports the age from the modification time, and no patched opener is called for it.
  - **`status codex --quota`.** It takes the run lock and prints the parsed windows from a fake app-server beside `last_quota`. With `quota-free.json` it names the plan and exits 3.

  Verify that these fail before the change.
- [ ] 2.3 Run lock and stopping a child, in `tests/unit/test_codex_cli.py`, POSIX only and skipped on Windows. Cases:
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
- [ ] 2.4 Billing guard, in `tests/unit/test_codex_cli.py`. Cases:
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
- [ ] 2.5 Command, readers and canonical tool calls, in `tests/unit/test_codex_cli.py`. Cases:
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
    - `final_text` is the last agent message, and `model` is `"unreported"`, or the reroute target in `model-rerouted`;
    - `cli_version` comes from `codex.session`;
    - `tokens_in = input − cached`, `cost_usd is None`, and `notional_basis` is `"unpriced"` for an unknown name and `"roster"` for a name the shipped registry prices under `openrouter/openai/`. Use a synthetic registry text, not a shipped slug;
    - `effort-dropped` makes the run untested for a precondition reason, naming both efforts;
    - `foreign-skill`, `cloud-skill-tool` and `mcp-call` are untested for isolation.
  - **`capture_rollout`.** Over `rollout-success.jsonl` placed under a fake home's `sessions/…`, it appends only the reduced records, drops the extra `session_meta` fields, writes `quota.json`, and deletes `sessions/`. With no record, the run is untested with "plan use cannot be confirmed".

  Verify that these fail before the change.
- [ ] 2.6 Host seam and CLI, in a new `tests/unit/test_hosts.py` plus `tests/unit/test_dev_runner_probe.py`. Cases:
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

## 3. Implementation

- [ ] 3.1 In `harness/host_login.py`:
  - add the `HostLogin` fields `strip_suffixes`, `stop_signal`, `outside_tempdir` and `child_vars`, with defaults that keep `CLAUDE` byte-identical in behaviour;
  - add `CODEX`, `PINNED_CONFIG`, `PINNED_CONFIG_TOML`, `CODEX_MIN_VERSION`, `check_codex_home`, `codex_status`, `codex_version`, `run_lock`, `RunLockBusy` and `LOCK_WAIT_S`;
  - give `check_location` its `tempdir` parameter;
  - add `run_host(record, argv, *, cwd, env, timeout, input=None, pass_fds=())` per design Decision 7 (change 2 has none), give `stop_child` a signal parameter defaulting to SIGTERM so that `run_host` passes the record's stop signal, and add the Linux parent-death `preexec_fn`;
  - add `RECORDS["codex"]`;
  - make the login note client-aware (design Decision 4): `LoginProblem` gains `client: str = "claude"`; add `NOTES` and `X8_PASSED = False`; `login_note(remedy, client="claude")` and `refusal(problem)` read the client; `login_remedy(message, source, record=CLAUDE)` matches `record.failure` and closes with that client's note;
  - make `login_env` record-driven, so the Codex login and every Codex logout drop the strip families and set `CODEX_HOME`;
  - read the Codex `last_written` age with `os.stat` only; nothing in the module opens `auth.json`.

  Wire `main(argv)` for `login|status|logout codex`, `--device-auth` and `status --quota` per design Decision 4, mapping `RunLockBusy` to exit 3. Verify that 2.1, 2.2 and 2.3 pass, that `uv run ruff check harness/host_login.py` reports no C901, that `grep -n "auth.json" harness/host_login.py` shows no `open`/`read_text`/`json.load` on it, and that the Claude sections of `test_host_login.py` are unchanged and green.
- [ ] 3.2 Create `harness/codex_cli.py`, stdlib-only and importing `host_login` only:
  - `DISABLED_FEATURES`, `needs_network`, `command`;
  - `run_env`, `ignored_env`, `assert_codex_env` (on the final environment, exempting exactly `CODEX.child_vars`), `spawn`;
  - `read_quota`, `parse_quota`, `Quota`/`Window`, `quota_problem`, `QUOTA_STOP_PERCENT`, `QUOTA_TIMEOUT_S`, `ALLOWED_PLANS`;
  - `features_problem`, `capture_rollout`, `codex_tool_calls`, `codex_read`, `failure_reason`, `billing_problem`;
  - `isolated_home(stack, args)`, which runs the preflight and yields the home;
  - `run_codex(...)`, which takes the lock, then runs the quota read, the features preflight, the spawn with `pass_fds`, the capture, and the release.

  Findings are frozen dataclasses, and failure tables are data, so complexity stays at 12 or below. Verify that 2.4 and 2.5 pass and that `uv run ruff check harness/codex_cli.py` is clean.
- [ ] 3.3 Create `harness/hosts.py` with `Host`, `RunView` and `JudgeBackend`. In `harness/claude_runner.py`, add:
  - the late-bound `HOSTS` and `host_for`;
  - `--host`, `--effort`, and the `--model` default change;
  - the usage guards of design Decision 3, including the `logs/evals` summary-log guard;
  - the untested mapping of the Codex preconditions (`RunLockBusy`, the CLI minimum, `features_problem`, an effort not served), per design Decision 12;
  - `stage(skill_dir)`;
  - `host` and `label` in `summary` and `failure_summary`;
  - the judge isolation per backend in `completed_run`, and the `resolve_judge` gate;
  - the host-aware `rejudge_lines`.

  In `harness/routing.py`, make `tool_calls` append `codex_cli.codex_tool_calls(events)`. Verify that 2.6 passes, that the whole `tests/unit/test_dev_runner_probe.py`, `test_routing.py`, `test_install_probe.py` and `test_isolated_env.py` stay green, and that `grep -n '".claude", "skills"' harness/claude_runner.py` shows only the Claude host's `skill_dir`.
- [ ] 3.4 Update the module docstrings and usage lines:
  - `claude_runner.py`: the `--host codex` usage, the Codex billing guard, and the not-comparable label;
  - `codex_cli.py`;
  - `hosts.py`;
  - `host_login.py`: the Codex record, the lock and the stop signal.

  Verify by reading the diff, and confirm with `grep -nE 'gpt-[0-9]' harness/*.py pyproject.toml` (empty) that no model slug entered the code.

## 4. Documentation

- [ ] 4.1 Update `harness/README.md`:
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
- [ ] 4.2 Update the `AGENTS.md` Commands block:
  - `uv run poe dev <scenario> --host codex --model <slug>` (subscription; plan quota; never a matrix input);
  - `uv run poe host-login codex [--reset] [--device-auth]` (the user only);
  - `uv run poe host-status codex [--quota]` (agents may run it; no model call);
  - `uv run poe host-logout codex` (the user only).

  Also add one sentence: the first Codex model call after any login needs the user's explicit go, like a metered run. Verify by reading the diff and with `uv run poe test`.

## 5. Gate

- [ ] 5.1 Run `uv run poe test` (not `test-fast`) and confirm it is green: pytest, ruff with the full rule set, `test_repo_conventions.py` (`main(argv)`, no `sys.path`, every `verdict_*` tested), the drift check and conform.
- [ ] 5.2 Run `uv run poe cov` and confirm that the 78 % floor holds with the new modules counted.
- [ ] 5.3 Run `uv run poe specs` and `openspec validate add-codex-dev-runner --strict`, and confirm both pass.

## 6. CLI update and rehearsal on the free plan (D6(b), no model call)

- [ ] 6.1 **USER ACTION:** `sudo pacman -S openai-codex` (to 0.160 or later). The agent then runs `codex --version` and records the version string here. Pass: at or above `CODEX_MIN_VERSION`.
- [ ] 6.2 X7, run by the agent, with no login and no network, so no model call is possible:
  1. Create an empty scratch `CODEX_HOME` at `${XDG_CACHE_HOME:-~/.cache}/thesis-proposal-dev/x7-probe`, holding only `PINNED_CONFIG_TOML`, and an empty scratch `HOME` beside it. The session scratchpad and its parent both lie under `/tmp`, where Codex refuses to place its helper binaries, so they are not used here. Before running, confirm that the resolved scratch `CODEX_HOME` lies neither inside the directory `python3 -c 'import tempfile; print(tempfile.gettempdir())'` prints nor inside the repository; if it does (for example because `XDG_CACHE_HOME` points into `/tmp`), stop and report.
  2. Run `unshare -rn env -i PATH="$PATH" HOME=<scratch-home> CODEX_HOME=<scratch-codex-home> codex features list <the run's --disable flags>`. Record each feature's name and state.
  3. Repeat once with an unknown nested key added to the scratch `config.toml`, passing `--strict-config` where the subcommand accepts it. Record whether it is refused.

  Pass: every pinned key is accepted, and only the allowlist reads enabled. Otherwise update `PINNED_CONFIG`/`DISABLED_FEATURES` (and their fixtures) through the `openspec-update-change` skill and rerun 5.1. Delete `${XDG_CACHE_HOME:-~/.cache}/thesis-proposal-dev/x7-probe` and the scratch `HOME`, and record the outcome in the README's X-check lines.
- [ ] 6.3 X1, **USER ACTION:** in a terminal, `uv run poe host-login codex` with the free ChatGPT account. Add `--device-auth` only if it is enabled in the ChatGPT security settings. The agent then runs `uv run poe host-status codex`. Pass requires all of these: `marker: yes`, `logged_in: yes`, `auth_method: chatgpt`, `config_pinned: yes`, `clean: yes`, `features_ok: yes`. Record the values, booleans and enums only. From here on the home holds a free-plan login. Every `--host codex` run refuses on the plan rule before any `exec`, and no agent starts one before task 7.3.
- [ ] 6.4 X8, **USER ACTION** (observation, no command beyond these):
  1. With a ChatGPT session open in the desktop app or on the web, run `uv run poe host-logout codex`, then `uv run poe host-login codex`.
  2. Confirm that the other session still works without a new sign-in.

  The agent records `stat -c %Y ~/.codex/auth.json` before and after (mtime only), and it must be unchanged. Pass: both hold. Then set `host_login.X8_PASSED = True`, which swaps the caveat for "Your own Codex login is not affected" in every message, and confirm that `uv run poe test` stays green. Do it here if this change is not yet archived, otherwise as a task in `record-codex-streams`. If the other session was signed out, keep `X8_PASSED = False`, document it in the README, and relay it to the user.
- [ ] 6.5 X4b, run by the agent, with no model call: `uv run poe host-status codex --quota`. Record:
  - whether the handshake answered;
  - the window durations and used percentages;
  - the plan type;
  - whether a credits block is present.

  On the free plan the command exits 3 by design, because the plan rule refuses; that is not a failure of X4b. Pass: an answer with at least one window. If the handshake fails, D2(a) makes Codex unusable. Record the failure and relay the D2 choice to the user. If the answer carries no credits block, record it and tell the user that every run will refuse on that read until the Plus answer in 7.2 shows the block, or a reviewed change relaxes the rule. Do not change either refusal on your own.

## 7. After Plus (gated)

If Plus has not been bought when sections 0 to 6 are done, mark each task here as deferred, and carry it into the proposal of `record-codex-streams` before archiving.

- [ ] 7.1 **USER ACTION** (in ChatGPT settings, no command):
  - set the Codex credit balance to 0, with automatic reload off;
  - optionally turn "Improve the model for everyone" off.

  Confirm here, yes or no only.
- [ ] 7.2 **USER ACTION:** `uv run poe host-login codex --reset`, so that the login carries the Plus plan. The agent runs `uv run poe host-status codex --quota`. Pass: ready (exit 0), the plan type reads `plus`, and a credits block is present with a zero balance and no credits available. Record the window usage. If the credits block is absent, every run refuses; record it and relay the choice to the user, whose relaxation of the rule would go through `openspec-update-change`. Do not proceed to 7.3 meanwhile.
- [ ] 7.3 The first Codex model call: **gated on the user's explicit go**, asked for in chat with the planned command. It uses plan quota, not money. Command: `uv run poe dev check_report --host codex --model <slug the user names> --keep`. Pass requires all of these:
  - the outcome is not untested for a billing, login or isolation reason;
  - the summary records the CLI version, `effort_served`, and quota before and after;
  - the kept events hold `codex.session`, `codex.turn_context` and `codex.token_count` with `rate_limits` and `plan_type` (X4);
  - `codex.skills` lists only the workspace's skill (X9).

  Record the results here, then delete the kept workspace after `record-codex-streams` has reduced it. Do not run a second Codex scenario, or `--judge`, without a new go.

## 8. Close

- [ ] 8.1 Commit the code, tests, fixtures, docs and this change folder as one commit for the completed change, off `main` until it is complete. Do not push. Verify with `git status` (clean) and `git show --stat HEAD`.
- [ ] 8.2 Archive through the `openspec-archive-change` skill, after sections 0 to 6, with section 7 either done or marked deferred as its preamble says, and only once both earlier changes are archived (`openspec list` shows neither `close-claudeai-surfaces` nor `add-harness-claude-login`). Change 2's archive waits for its L1. Before archiving:
  - repeat task 0.1's rebase check, scoping check and name-by-name check against the archived main spec;
  - run `openspec validate add-codex-dev-runner --strict`, which must pass with no "Archive would refuse" line.

  Verify that `openspec validate --all --strict` is green afterwards. The follow-up change `record-codex-streams` (recorded fixtures, X4/X9 outcomes, and the `X8_PASSED` flip if it happens after this archive) is separate.
