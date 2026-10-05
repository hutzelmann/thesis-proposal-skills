# Tasks

Ground rules for every task below:

- Agents never run login commands. A step marked **USER ACTION** is run by the user, with the exact command given.
- Agents may run `uv run poe host-status`, which makes no model call. They never run `poe host-login` or `poe host-logout`.
- Live checks run on the Max subscription and make no metered call.
- Reports carry only booleans, counts, enums, file modification times (`stat`, never contents) and names. They never carry a credential, an environment value, an email address or an org.
- Nobody reads or prints a credentials file.

## 0. Precondition

- [x] 0.1 Confirm that `close-claudeai-surfaces` is implemented and archived, and read the live-check outcomes it recorded.
  - **Archived.** Check that `harness/account_surfaces.py` exists with `CONNECTORS_OFF`, `PINNED_SETTINGS` and `PROFILE_DIR`, that `routing.follow_stream` and `claude_cli.billing_signals` exist, and that `openspec list` no longer shows that change.
  - **L7 and L8.** Read change 1's dated lines in `harness/README.md` (its task 5.9) and its archived tasks 5.1, 5.5, 5.6 and 5.8. Record here the L7 outcome, the L8 outcome, whether F8 was implemented, and the D1 branch.
  - **If L7 failed, or the record names D1(c):** stop. Revise this change to token mode through the `openspec-update-change` skill before any code is written. Step A would otherwise be built and live-checked on a login whose opt-outs are known not to hold, and tasks 5.6 and 5.7 require `login: harness`, which a token makes impossible.
  - **If L8 is not settled positive:** confirm that F8 is in place. If it is not, stop and report it.
  - **Rebase.** If change 1's archived text differs from the text this change's three shared MODIFIED blocks start from, rebase those blocks through the `openspec-update-change` skill.

  Verify with `openspec validate add-harness-claude-login --strict`.

  Done 2026-10-05. Archived as `openspec/changes/archive/2026-10-05-close-claudeai-surfaces/` (commit a4e1b68); `harness/account_surfaces.py` holds `CONNECTORS_OFF`, `PINNED_SETTINGS` and `PROFILE_DIR`; `routing.follow_stream` and `claude_cli.billing_signals` existed; `openspec list` no longer shows it. Recorded outcomes (its tasks 5.1, 5.3, 5.5, 5.6, 5.8 and the dated `harness/README.md` lines): **L7 passed**, **L8 inconclusive**, **F8 implemented** (`account_surfaces.profile_store_problem`), **D1 branch (b), step A** — so no token-mode revision. Rebase: `openspec validate` refused the delta because "Isolated measurement environment" lacked change 1's F8 scenario. The delta was rebased on the archived text (autonomous run, applied without the per-edit confirmation the update skill asks for): the F8 paragraph (scoped to Claude runs) and its scenario "Anthropic profile in the default directory" added, "Synced content left in the configuration" and "Connector in an ambient run" taken over with change 1's final wording; design.md Context names F8. `openspec validate add-harness-claude-login --strict` is valid.

## 1. Failing tests first

- [x] 1.1 Harness home, in `tests/unit/test_host_login.py`, new section. Use synthetic directories under `tmp_path`, `THESIS_PROPOSAL_DEV_STATE` and a monkeypatched `host_login.read_status`. Cases:
  - **`state_root`** for linux (absolute `XDG_STATE_HOME`; relative one ignored; unset), darwin and win32, given as pure inputs.
  - **The location guard.** It refuses a root that equals `Path.home()`, one that contains it, one inside `~/.claude`, one containing `$CLAUDE_CONFIG_DIR`, one equal to `~/.codex`, one inside `$CODEX_HOME`, and one inside the repository. The default root passes. A symlink pointing into `~/.claude` is refused.
  - **Wipe.** It refuses an unmarked home and a symlinked home, naming the directory, and deletes a marked one.
  - **Seeding.** `settings.json == PINNED_SETTINGS` and an empty `anthropic-empty/` exist before the fake login argv runs. Record call order to show it.
  - **`check_presence`.** Missing home, missing marker, and mode wider than 0700 (POSIX only) each name `uv run poe host-login claude`.
  - **`check_home`.** Each forbidden entry is named: a skill (including `skills/synced/x`), an agent, a command, an output style, `CLAUDE.md`, a non-empty installed-plugins record, and settings with an extra key. A marketplace cache and `projects/` pass.
  - **`check_status`.** It refuses each of: not logged in; `authMethod` `api_key`, `api_key_helper` and `third_party`; `apiProvider` other than `firstParty`; `configDirectory` ≠ home (remedy names the redirect); `configDirectory` absent (remedy: update the host). A good status passes.
  - **`refusal` and `login_note`.** Parametrize over `L3_PASSED` False and True. A refusal starts with `untested: ` and carries exactly one remedy.
    - With `L3_PASSED` False, a refusal whose remedy names `host-login` (with or without `--reset`) ends with "Whether this logs out your other Claude sessions is unverified (L3)." and does not contain "not affected".
    - A refusal with another remedy (the redirect, the host update) ends with "Your own Claude login is not affected."
    - With `L3_PASSED` True, every refusal ends with "Your own Claude login is not affected."
    - A status payload holding a placeholder email and org yields a message containing neither.

  Verify that the new tests fail at import before the functions exist.

  Done 2026-10-05: new sections in `tests/unit/test_host_login.py`; they failed at import (`AGENT_MARKERS`, `CLAUDE`, … missing) before 2.1. (Review, 2026-10-05: the `$CLAUDE_CONFIG_DIR` case first used a root that also contained the synthetic home, so the home check refused it and the configuration-directory branch went unexercised; each guard case now asserts the overlap its cause names — task 2.9.) `state_root` cases use `tmp_path` paths rather than POSIX literals (`test_repo_conventions.py` forbids `Path("/…")`, and a `/fake` path is not absolute on Windows). `check_location` takes an optional `user_home` so the guard is testable without the real home. A new autouse fixture in `tests/conftest.py` (`_harness_login_offline`) points every test at an absent state root and clears `CLAUDE_REAL_CONFIG_DIR` and `ROUTING_CONFIG_DIR`, so no test can reach a real login or start a client.
- [x] 1.2 CLI, in `tests/unit/test_host_login.py` or a new `tests/unit/test_host_login_cli.py`. Fake the client binary through the module's runner seam, never a real `claude`. Cases:
  - **Terminal guard.** `main(["login", "claude"])` with a non-tty stdin returns non-zero, says to run it in a terminal, creates nothing and spawns nothing.
  - **Agent-marker guard.** With a tty stdin faked and each of `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SESSION_ID`, `CODEX_SANDBOX` and `CODEX_SANDBOX_NETWORK_DISABLED` set in turn (synthetic values), `main(["login", "claude"])` returns non-zero, names the variable, never prints its value, creates nothing and spawns nothing. With none set it proceeds.
  - **Login environment.** `login_env` drops `ANTHROPIC_*`, every `CLAUDE_CODE_*` (the long-lived token included), `CLAUDECODE` and an inherited `CLAUDE_CONFIG_DIR`. It keeps `DISPLAY`, and sets `CLAUDE_CONFIG_DIR=<home>`, the connector switch and `<home>/anthropic-empty`.
  - **Login argv.** It contains `--claudeai` and never `--console`.
  - **Existing login.** Logout runs before login, while the claim is held.
  - **`--reset`.** It wipes the marked home and reseeds it.
  - **Every logout uses the login environment.** The standalone `logout`, the logout before a login over an existing login, and the logout inside `--reset` each receive exactly `login_env(CLAUDE, home, environ)`. Launch them from an environment carrying `ANTHROPIC_API_KEY`, `CLAUDE_CODE_OAUTH_TOKEN`, `ANTHROPIC_CONFIG_DIR` and another `CLAUDE_CONFIG_DIR`; none of those values reaches the fake client.
  - **Logout note.** With `L3_PASSED` False, all three logout paths print "whether this logs out your other Claude sessions is unverified (L3)" before the fake logout runs. With it True, none does.
  - **Status output.** `status` prints only the listed keys (`capsys`): `home`, `marker`, `logged_in`, `auth_method`, `api_provider`, `config_dir_matches`, `clean`, `access_expires`, `runs_use`. It shows no email and no org, exits 0 when ready and 3 when not, and on a missing home neither creates the home nor spawns the client.
  - **Token mode.** With a token exported, `status` reports `runs_use: token`.

  Verify that these fail before `main` exists.

  Done 2026-10-05 in a new `tests/unit/test_host_login_cli.py`, faking the client at `host_login.run_client` (one seam for login, logout and `auth status`); failed at import before 2.6. An existing login is detected by `.credentials.json` in the home (Linux, step A), so a login on a fresh home starts no status call first.
- [x] 1.3 One builder. Retarget the builder tests in `tests/unit/test_isolated_env.py` and the `child_env` tests in `tests/unit/test_claude_cli.py` to `host_login.allowlisted_env(CLAUDE, config, environ)`. Add these:
  - **One environment.** The rig (`stream_events` with `Popen` faked), the isolated dev run (`model_env`), the judge's `call` and its `preflight`, each given the same configuration and launching environment, all produce the same mapping. Patch `host_login.allowlisted_env` once and assert that every site received the sentinel.
  - **The judge's set.** The judge child now carries the proxy, CA-trust, `SHELL` and `LANGUAGE` variables, and drops `XDG_SESSION_TYPE`.
  - **Replaced values.** An inherited `ENABLE_CLAUDEAI_MCP_SERVERS=true` and an inherited `ANTHROPIC_CONFIG_DIR` are replaced.
  - **Quiet.** Nothing is printed.
  - **Old names gone.** `routing` has no `ADMITTED_ENV` or `isolated_env`, and `claude_cli` has no `ENV_KEEP`, `ENV_KEEP_PREFIXES` or `child_env`.

  Verify that each fails against the current code for the stated reason.

  Done 2026-10-05. `test_isolated_env.py` builds through `allowlisted_env(CLAUDE, …)`; `every_site` collects the rig's, the isolated dev run's, the judge's call and preflight, and the harness status check's environment (the status check alone drops the long-lived token, see 2.1); one monkeypatch of `host_login.allowlisted_env` reaches all five. The `child_env` tests in `test_claude_cli.py` became judge-environment tests through `claude_cli.call`. Run against a `git archive HEAD` snapshot, every changed test file failed at collection (the new names do not exist there).
- [x] 1.4 Link source, in the `prepare_config` section of `tests/unit/test_host_login.py`. Replace the `stored_dir` fixture with a harness-home fixture and an opt-in fixture. Cases:
  - **Default.** The config links `<harness home>/.credentials.json`, with the preflight stubbed to pass.
  - **Preflight problem.** It raises `SystemExit` carrying the refusal text and creates no link.
  - **`ROUTING_CONFIG_DIR` set.** It raises `SystemExit`, naming the removal and `uv run poe host-login claude`.
  - **`CLAUDE_REAL_CONFIG_DIR` set.** The config links that directory, and no preflight runs.
  - **Long-lived token.** Nothing is linked, `read_status` is never called, and the home is not created.
  - **Write-back.** `isolated_config` writes a synthetic refresh back to the harness home. A stand-in operator credentials file keeps its bytes and mtime.
  - **Untested mapping.** `enter_isolation` maps a preflight refusal to an untested `RunnerFailure`.

  Verify that these fail before the change.

  Done 2026-10-05: `stored_dir` replaced by `harness_home`/`linked_home` and `opted_in` fixtures; the two `ROUTING_CONFIG_DIR` tests now assert the refusal; the untested mapping is exercised with the real preflight on an unmarked home. Failed before the change (snapshot run, as in 1.3).
- [x] 1.5 Login source and remedies.
  - **`login_source`.** It covers each of its four outcomes.
  - **`login_remedy(message, source)`.** For each source it appends exactly that source's remedy: `host-login` plus the not-affected sentence, `/login`, `/login`, `claude setup-token`. It appends nothing to a message that is not a login failure.
  - **`tests/unit/test_dev_runner_probe.py`.** An authentication-failure stream under the harness source names `uv run poe host-login claude` and closes with `login_note`; under the ambient source it names `/login`. The summary carries `login` and `login_dir`.
  - **The write-back target.** For an isolated configuration prepared under the default (harness-home fixture), `login_dir` resolves inside the harness home, and `keep_login`'s write-back target equals `login_dir/.credentials.json`. Under the opt-in fixture, `login_dir` is the opted-in directory. Under a token, `login_dir` is null.
  - **`tests/unit/test_routing.py`.** `case_result` with the harness source names `host-login`, and the raw payload carries `login` and `login_dir`.
  - **`tests/unit/test_claude_cli.py`.** `check_auth_status` and `parse_stream` give the remedy per source.

  Verify that these fail before the change.

  Done 2026-10-05. The source is required everywhere; the existing tests pass it through thin local wrappers (`case_result`, `host_failure`, `parse_stream` in the test modules) defaulting to the operator's or the ambient login, so their `/login` expectations stand. Failed before the change (snapshot run).
- [x] 1.6 Termination before kill. The fakes stay on `claude_runner.follow_stream`, where change 1 put them. Add these:
  - **POSIX children** (`sys.executable` scripts written under `tmp_path`, with `TERM_GRACE_S` patched small), driven through `stop_child`:
    - a child that traps SIGTERM, writes a marker file and exits is never killed;
    - a child that ignores SIGTERM is killed after the grace.
  - **`follow_stream`.** With a recording fake `Popen`, at a stop condition and at the deadline, it calls `stop_child`: terminate, then wait for `TERM_GRACE_S`, then kill only if the wait times out. No literal 5 s grace remains.
  - **The judge.** `run_child`, given a SIGTERM-trapping child and a short timeout, leaves the marker file.

  Mark the POSIX tests to skip on Windows. Verify that they fail before the change.

  Done 2026-10-05: the two POSIX children in `test_host_login.py`; the shared grace at a stop condition (both branches) and at the deadline with the recording host in `test_routing.py`, plus a check that no `STOP_GRACE_S` or literal 5 s wait remains; the judge's SIGTERM-trapping child in `test_claude_cli.py`. Failed before the change (snapshot run).
- [x] 1.7 The billing backstop.
  - **`case_billing`** (in `tests/unit/test_routing.py`, synthetic streams). It returns a reason for each of: an API-key source in `init`; a rate-limit report with overage in use; a refused status; a non-first-party provider in a result's model usage; a stream with an assistant event and no rate-limit report. It returns none for a stream stopped at `init` with no rate-limit report, and none for a clean routed stream shaped like the recorded `events-litsearch-oblique.jsonl` (report before the first assistant event).
  - **Precedence.** `case_result` gives surface > billing > route > host error > stream error.
  - **Voiding.** A sweep of three fake cases whose first reports overage: the cases not yet started never call `follow_stream`, every result is an error naming the overage, the raw payload is written, the tracked report is unchanged, and `main` returns 1.
  - **The move.** The existing `billing_problem` and `billing_signals` tests pass unchanged against the functions' new home, imported through `claude_cli` callers.
  - **Smoke gate** (in `tests/unit/test_dev_runner_probe.py`). A summary log whose earlier line carries `billing` makes `main([<scenario>, "--isolated", "--summary-log", log])` start no host, record a line "not run: <scenario> reported <reason>" with the untested status, and exit untested. A log whose lines carry no `billing` lets the run proceed. A run untested for overage writes `billing` into its line. `summarize` lists the not-run scenarios.

  Verify that these fail before the change.

  Done 2026-10-05. New fixture `tests/unit/data/routing_streams/reported-route.jsonl` (synthetic, the order of `events-litsearch-oblique`: `init`, rate-limit report, then the selection), listed in that folder's README. (Review, 2026-10-05: that recording is 2.1.207, not 2.1.284 as first written; on 2.1.284 the report follows the routing turn — task 2.9.) `expired-login.jsonl`'s `init` gained `apiKeySource: "none"`: without it the rig's source check would read a dead login as an API-key source (fail-closed, but the wrong remedy). The reduced routing fixtures predate the rate-limit report, so the case-result tests that hold a model turn get the `REPORTED` prefix. The voiding test runs the real `measure` with only `routing.follow_stream` faked. Failed before the change (snapshot run).

## 2. Implementation

- [x] 2.1 In `harness/host_login.py`, implement design Decisions 2, 3 and 5:
  - `HostLogin`, `CLAUDE`, `RECORDS`;
  - `state_root`, `home`, `check_location`;
  - marker, seed and `wipe`;
  - `check_presence`, `check_home`, `check_status`;
  - `LoginProblem` (a frozen dataclass), `refusal`, `login_note`, `L3_PASSED = False`, `read_status`, `preflight`.

  The module stays stdlib-only, imports `account_surfaces`, and builds every path from `Path.home()` or the environment, never an absolute literal. Verify that 1.1 passes and that `uv run ruff check harness/host_login.py` reports no C901.

  Done 2026-10-05; 1.1 passes, no C901. Deviations, each what the design implies: (a) `account_surfaces` used to import `LONG_LIVED_TOKEN` from `host_login`, which would make Decision 2's import a cycle, so the constant is now defined in `account_surfaces` and re-exported by `host_login` (one definition). (b) `HostLogin` carries four fields beyond Decision 2's list — `plugin_record`, `fixed_env`, `profile` and `credentials` — so `allowlisted_env` and the clean check read everything Claude-specific from the record, as the Codex record will need. (c) `read_status` drops `CLAUDE_CODE_OAUTH_TOKEN` from the allowlisted environment, so `host-status` reports the home's own login even when a token is exported; the preflight never runs under a token anyway. (d) A `.credentials.json` missing from a logged-in home (the macOS Keychain; whether Windows writes the file is unverified) is refused with token mode as the remedy instead of a dangling link.
- [x] 2.2 Move `ADMITTED_ENV` into `host_login`, with its comment, as `CLAUDE.admitted`. Implement `allowlisted_env(record, config, environ=None)` per design Decision 8. Then:
  - delete `routing.ADMITTED_ENV` and `routing.isolated_env`;
  - delete `claude_cli.ENV_KEEP`, `ENV_KEEP_PREFIXES` and `child_env`;
  - have `stream_events`, `model_env`'s isolated branch, and `claude_cli.call` and `preflight` call `host_login.allowlisted_env(host_login.CLAUDE, …)` through the module attribute. The judge's `config` becomes required.

  Verify that 1.3 passes.

  Done 2026-10-05 as `host_login.CLAUDE_ADMITTED` (with its comment); the old names are gone and 1.3 passes.
- [x] 2.3 Rewrite `routing.prepare_config` in the order of design Decision 6: the override refusal, the token, the opt-in, then the preflight followed by the harness link. Remove change 1's override check on `ROUTING_CONFIG_DIR`. `keep_login` and the claim stay unchanged in mechanism. Verify that 1.4 passes and that `tests/unit/test_install_probe.py` stays green.

  Done 2026-10-05; 1.4 passes and `test_install_probe.py` is green unchanged (the probe still layers HOME/USERPROFILE over the isolated environment in `run_claude`). The `ROUTING_CONFIG_DIR` refusal uses the refusal template; its remedy names `host-login`, so it closes with the L3 caveat. `isolation_problem`'s message no longer mentions the override.
- [x] 2.4 Add `LoginSource`, `login_source` and `login_remedy(message, source)`, and replace every `RELOGIN` remedy site with the source-aware call:
  - `routing.case_result`;
  - `claude_runner.host_failure` and `run_claude`;
  - `claude_cli.check_auth_status`, `parse_stream`, `call`, `preflight` and `judge_all`'s options.

  Add `login` and `login_dir` to the dev-run summary and to the routing raw payload. Verify that 1.5 passes and that `uv run ruff check harness/` stays clean.

  Done 2026-10-05; 1.5 passes, ruff clean. `run_claude` and `run_judge` compute the source from the run's configuration; the rig computes it once per sweep (`routing.sweep`). An isolated run whose configuration could not be prepared is labelled with the login it would have linked (`host_login.planned_source`), `login_dir` null. `keep_login`'s write-back target is exposed as `host_login.writeback_target`, and the claim-wait and write-back-failure messages name the remedy for the link's target. `_source_problem` (an API-key source) no longer embeds `/login`: the billing checks stay source-free, so its reason names both remedies without naming a login — unset the key or key helper, or log in again with the subscription login, never an API key (wording revised in 2.9).
- [x] 2.5 Add `TERM_GRACE_S` and `stop_child` per design Decision 9. Replace the terminate, 5 s, kill sequence in `routing.follow_stream` with `stop_child`, and wire `claude_cli.run_child` to terminate, then a shielded grace, then kill. Verify that 1.6 passes. Also run `grep -n 'kill()' harness/*.py` and confirm that every kill sits after a termination request and its grace.

  Done 2026-10-05; 1.6 passes. The grep finds `host_login.stop_child` and `claude_cli._stop` (each after `terminate()` and the grace) and `routing._end_group`'s `killpg`, which reaps what is left of a host's group after the host itself went through `stop_child`. `host_login.run_client` stops a timed-out `auth status`/`auth logout` through `stop_child` too. Found outside this change's call sites: `harness/audit_llm_preflight.py` started its ambient `claude -p` with `subprocess.run(timeout=…)`, which SIGKILLs on the time limit without a termination request, on the operator's own login. First left as a follow-up; routed through `Popen` and `stop_child` in 2.9, so the design Goal holds for every host child.
- [x] 2.6 Add `host_login.main(argv)` with the `login`, `status` and `logout` subcommands per design Decision 4, with `AGENT_MARKERS`, `agent_session_markers` and `login_env`, and the logout note on all three logout paths. Add the poe tasks `host-login`, `host-status` and `host-logout` to `pyproject.toml`. Verify that 1.2 passes and that `tests/unit/test_repo_conventions.py` sees a `main` taking `argv`. Then run `uv run poe host-status` once; an agent may. Before any login it must:
  - exit 3;
  - print `logged_in: no` or a missing home, with the remedy `uv run poe host-login claude`;
  - leave the home uncreated (`test -e` on the printed path is false).

  Done 2026-10-05; 1.2 passes and `test_repo_conventions.py` sees `main(argv)`. `uv run poe host-status`, run once: exit 3, `marker: no`, `logged_in: no`, `runs_use: harness`, and on stderr "untested: the harness login home …/.local/state/thesis-proposal-dev/hosts/claude does not exist. Run `uv run poe host-login claude`. Whether this logs out your other Claude sessions is unverified (L3)."; `test -e` on the home and on the state root is false. The key lines go to stdout and the refusal to stderr, so the status output is exactly the listed keys.
- [x] 2.7 Update the module docstrings:
  - `host_login.py`: the harness home, the records, the preflight, the login note, the builder and `stop_child`;
  - `routing.py`: the isolated-environment section, `prepare_config`, and the billing checks and voiding;
  - `claude_runner.py`: the `--isolated`, billing and login text at lines 37–47, and the smoke gate;
  - `claude_cli.py`: the environment and the remedy.

  Verify by reading the diff.

  Done 2026-10-05, read in the diff.
- [x] 2.8 Implement the billing backstop per design Decision 10:
  - move the pure stream checks behind `billing_problem` and `billing_signals` from `claude_cli` into `routing`, and import them back into `claude_cli`;
  - add `routing.case_billing`, the precedence in `case_result`, the stop flag that keeps unstarted cases from starting a host, and the voiding in `main`;
  - add `billing` to the dev-run summary line, and the `--summary-log` gate in `claude_runner` that starts no host after an earlier line carrying `billing`;
  - add the billing exception to the smoke comment in `pyproject.toml`.

  Verify that 1.7 passes and that `uv run ruff check harness/` reports no C901.

  Done 2026-10-05; 1.7 passes, no C901. `routing.main` delegates the pool to a new `sweep()`, which holds the stop flag (`BillingStop`), the voiding (`void`, which `voided` now uses too) and the login record. `claude_cli` re-exports `billing_signals` and `rate_refusal` from `routing`. The judge's stream counts too: `SubscriptionUnavailable` and `JudgeRun` carry the billing reason, so a judged smoke step whose judge reports overage writes `billing` and stops the later steps — the requirement names any scenario untested for billing, and the first smoke step is judged.

- [x] 2.9 Apply the review findings of 2026-10-05 (autonomous run; the artifacts were revised through the `openspec-update-change` skill without its per-edit confirmation, as in 0.1). Each finding was checked against the code and the recordings; all were confirmed and fixed:
  - **Event order (blocker).** The design's premise that 2.1.284 writes the rate-limit report before the first assistant event was wrong: `logs/routing/events-litsearch-*.jsonl` are 2.1.207; on 2.1.284 `events-write-polish-collision.jsonl` has the report after three assistant events, and `events-review-canonical.jsonl` (stopped at its route) holds none. Task 5.7 would have voided its sweep. `routing._case_decided` now reads a routed case on until the report arrives or the routing turn ends (a `user` or `result` event), and stops there. New fixture `route-before-report.jsonl` (2.1.284 order); `reported-route.jsonl`'s provenance and version corrected to 2.1.207; spec paragraph and scenario "Rate-limit report after the route"; design Context, Decision 10 and Open Questions; `routing.py` docstrings; README Skill-routing text. *Superseded 2026-10-05 by 2.10: task 5.7 showed that a `Skill` call's tool result arrives before the report, so the stop at the routing turn's `user` event voided the case; the premise "report before the tool results" holds for `Glob`, not for `Skill`.*
  - **A rejected login is no billing signal (major).** The host writes its own assistant event for a failed API call (model `<synthetic>`, `isApiErrorMessage`; 2.1.258 transcripts), so a login rejected mid-case read as an unreported rate limit, voided the sweep and lost its `host-login` remedy. `routing.model_turns` skips it; `expired-login.jsonl` gained that event; a sweep test with the real `measure` shows the remedy survives and nothing is voided.
  - **Token mode turned the gate red (major).** The autouse fixture `_harness_login_offline` now also clears `CLAUDE_CODE_OAUTH_TOKEN`; the touched suites pass with a placeholder token exported.
  - **Overage flag in the rig.** `case_billing` refuses a report without `isUsingOverage`, as the dev runner does.
  - **Unmarked homes.** A plain login no longer adopts a directory without the marker (it wrote the marker, replaced settings and logged out a foreign login); every command refuses it with `wipe`'s "move it aside", `check_presence` included. Seeding happens only for a missing home.
  - **Logout failures.** A re-login or reset whose logout exits non-zero stops before logging in or wiping, naming the exit status. Where the login is no file, the host's status decides whether an existing home holds one (the macOS gap); a reset of a home without a login logs nothing out.
  - **F8 for the login commands.** `host_login.profile_problem` (change 1's check, token not exempt) runs before the login, every logout, the status check and the preflight; `isolated_config` now runs change 1's check before `prepare_config`.
  - **Relative override.** `check_location` refuses a state root that is not absolute.
  - **`CLAUDE_PID`** is stripped from the login environment.
  - **Labels.** `login_source` follows how the configuration was prepared (`planned_source`), not the link's state, which the host replaces during a refresh; `login_dir` falls back to the planned login's resolved directory. The install probe labels a refused isolation with the planned login.
  - **Billing on failed runs.** The dev runner's failure path and the judge's error-result path carry every explicit signal (`billing_signals`: an API-key source and a foreign provider too), so the smoke gate stops after them.
  - **`_source_problem`** names both remedies again (unset the key or helper, or log in again with the subscription login).
  - **Audit pre-flight** terminated before kill (see 2.5).
  - **Tests and wording.** The location-guard cases assert the overlap they name; the write-back test points HOME at the stand-in operator login; new L0 cases for the `auth login` call's environment and argv, the macOS no-file refusal, logout on a missing home and on an overlapping root, the login location refusal and a wipe failure in a reset; the no-file message names macOS only. Spec: status check without the token ("Status check reports the home's own login"), "Relative override refused", "Unmarked directory never adopted", "Failed logout stops a re-login", "Profile directory bars the login commands", the label rule, and the judge's billing reason beside an error.

  Verify with `uv run poe test`, `uv run poe cov` and `uv run poe specs` (4.1–4.3, rerun).

  Done 2026-10-05; the second review reran the gate after it: `poe test` 2909 passed, 1 skipped, ruff clean, in sync, 11 skills conform; `poe cov` 91.11% (host_login 95%, routing 95%, claude_cli 97%, claude_runner 92%); `poe specs` 21/21; the change valid. Its event-order fix did not hold live (5.7); see 2.10.
- [x] 2.10 Revise the routed-case stop condition after task 5.7's failure (design Decision 10, "Reading past the route"; spec paragraph and scenarios "Rate-limit report after the route" and "Unreported rate limit in a routing case", revised through the `openspec-update-change` skill, autonomous as in 2.9). Also apply the second review's minor findings of 2026-10-05.
  - **Stop condition.** `routing._case_decided` accepts a route only at the first of: a rate-limit report read, the run's `result` event, or an assistant event of a later turn (a message id other than the routing event's). Remove `TURN_END`. Update the docstrings of the module, `case_billing`, `_case_decided` and `stream_events`, and the README's Skill-routing text.
  - **Fixtures.** Rebuild `route-before-report.jsonl` in the order recorded for a fast tool on 2.1.284 (the routing turn's tool result, then the report, then the next turn), with message ids. Add `skill-result-unreported.jsonl`, the 5.7 stream reduced (init, the `Skill` call, its tool result, no report), so the provenance cites a committed file rather than a gitignored log that later runs overwrite. Correct the folder README.
  - **L0.** `_case_decided` does not stop at the routing turn's tool result while no report has been read; it stops at the report, at `result`, and at the next turn's first assistant event; a case stopped there without a report is voided as unreported.
  - **Minor findings.** End `BillingStop.voiding()` with a period, so the case's own error reads as its own sentence. Make `host-logout` refuse an existing home without the marker with the move-aside remedy (exit 3), as the README says of every command, with an L0 case. Record the 5.2/5.4 login time from the harness home's file modification times (no contents read). Note 5.6's side observation as a follow-up.

  Verify with `uv run poe test`, `uv run poe cov` and `uv run poe specs` (4.1–4.3, rerun). Task 5.7 reruns after this task; it is the live observation of where a `Skill` call's report lands.

  Done 2026-10-05 (offline; no model call). Evidence beyond 5.7's stream: three subscription dev-run streams of 2026-10-04 (2.1.284, `apiKeySource` none) put the report after a `Read` call's tool result, followed by `system/task_summary` and then the next turn; 5.7's recorded `Skill` call carries `stop_reason` null, so its result came while the response was still streaming. `_case_decided` now stops a routed case at the report, at `result`, or at an assistant event whose message id differs from the routing event's (`_routing_event`, `_later_turn`); `TURN_END` is gone; module, `case_billing`, `_case_decided` and `stream_events` docstrings and the README's Skill-routing verdict and Billing text follow. `route-before-report.jsonl` rebuilt in the fast-tool order with placeholder message ids; the `Glob` order is a reordering in the tests; `skill-result-unreported.jsonl` added (5.7's stream, reduced); folder README corrected. New L0: the recorded prefix never stops a case; the routing response's own later block does not stop it; without a report the case stops at the next turn's first assistant event or at `result` and is voided as unreported; the report stops it in both orders. `BillingStop.voiding()` ends with a period (asserted in the billing-void test). `host-logout` refuses an existing unmarked directory or a symbolic link with the move-aside remedy, exit 3, nothing logged out (new L0, foreign files and foreign login); a missing home still has nothing to log out. 5.2, 5.4 and 5.6 records amended; 5.9 closed. Gate green (4.1–4.3 reruns). Whether a `Skill` call's report lands before the next turn is inferred from the `Read` order and stays for 5.7's rerun to show. (Observed 2026-10-05 before that rerun; see 2.11.)
- [x] 2.11 Ground the routed-case stop condition in the observed `Skill` order (design Context "Event order" and Decision 10, "Reading past the route"; spec paragraph, scenarios "Rate-limit report after the route" and "Unreported rate limit in a routing case" revised, new scenario "Rate-limit report after a skill's instructions"; revised through the `openspec-update-change` skill, autonomous as in 2.9). Source: the diagnostic run recorded under 5.7, which read task 5.7's case to its `result`. Its order was `init`, the `Skill` call, its tool result, a second `user` event with the skill's instructions, the one rate-limit report, then the next turn's first assistant event with a new message id.
  - **Stop condition.** `_case_decided` (2.10) already stops at the report there. Keep the rule, and confirm with the recorded stream that it stops neither at the routing turn's tool result nor at the skill's instructions. Cite the observed order in the docstrings of the module, `case_billing`, `_case_decided` and `stream_events`, and in the README's Skill-routing text. No code path may read a routed case past the next turn's first assistant event, and `CASE_TIMEOUT_S` still bounds it.
  - **Fixtures.** Rebuild `route-before-report.jsonl` as the reduced recording of that run: every event in order, with its type, subtype, message-id grouping (placeholder ids), model, `stop_reason`, block kinds, the skill name, and the report's status and overage flag. All text, tool inputs other than the skill name, and tool results are synthetic. Its 2.10 version was a synthetic order shaped like the `Read` dev runs, with a `system/task_summary` and no skill-instructions event; that order was never observed after a `Skill` call. Correct the folder README's rows for it and for `skill-result-unreported.jsonl`, which is the prefix the old rig read: the report arrives two events later in the full stream.
  - **L0.** The `Skill` order, read through the rig: the case stops at the report (fifth event), is counted with its route, and is not voided. The whole recorded run carries one report and no billing reason. The same stream without its report stops at the next turn's first assistant event and is voided as unreported; without a later turn, it stops at `result` and is voided. A report between the route and its tool result (the `Glob` order) stops the case at the report. A routed case with no report by its deadline is a timeout whose stream is voided as unreported.

  Verify with `uv run poe test` and `openspec validate add-harness-claude-login --strict`; then rerun 5.7.

  Done 2026-10-06 (offline; the observation run had already been recorded under 5.7). The stop rule is unchanged from 2.10. Replayed over the recorded stream it stops at the report, event 4 (the fifth read). `TURN_END` stays gone. Docstrings (module, `case_billing`, `_case_decided`, `stream_events`) and the README's Skill-routing verdict and Billing text now cite the recorded `Skill` order and the 2 s against 30 s it saves. `route-before-report.jsonl` was rebuilt from the recording: all 28 events, their types, subtypes, message-id grouping, models, `stop_reason`, block kinds and tool names, and the report's fields. A `jq` comparison of the fixture's shape against the recording matched line for line. The folder README rows for it and for `skill-result-unreported.jsonl` are corrected. New and revised L0 in `test_routing.py`:
  - the `Skill` order read through `stream_events` stops at the report and is counted, 1/1;
  - the `Glob` order (the report moved between the route and its tool result) stops at the report;
  - the recording holds one report, which follows the first `user` event, so the pre-2.10 rule stopped before it;
  - the run without its report stops at the next turn's first assistant event and is voided; ending in `result` instead, it stops there and is voided;
  - a routed case whose deadline passes after the skill's instructions is a timeout, voided as unreported;
  - `case_billing` finds nothing over the whole recorded run, and names the missing report for the prefixes and for the run without it.

  Gate: `poe test` 2920 passed, 1 skipped, ruff clean, in sync, 11 skills conform; `poe cov` 91.12% (routing 95%); `poe specs` 21/21; the change valid.
- [x] 2.12 Apply the pre-archive review findings of 2026-10-06 (autonomous, as in 2.9; the artifacts revised through the `openspec-update-change` skill without its per-edit confirmation).
  - **Surface after a model turn.** `case_billing` no longer names the missing report for a case stopped for an account surface, so `measure` trips the sweep's stop only on a billing reason the stream shows (an explicit signal, or a report without its overage flag); the case keeps its surface error and the next case starts. Spec: the rule's list item and the scenario "Unreported rate limit in a routing case"; design Decision 10 (`case_billing`, Precedence); proposal; README Billing. New L0: such a stream owes no report but keeps an overage signal; through the real `measure`, the case records the surface and not billing, and the next case is counted.
  - **Observed, not classified.** The README Billing text, the `_case_decided` docstring, a test comment and the proposal state the recorded order (after a `Read` or `Skill` call's result, before a `Glob` call's) and point to design Context for the inferred reason, instead of a fast/slow tool rule.
  - **Fixture provenance.** The `route-before-report.jsonl` row says the `Skill` call's tool result keeps the host's fixed launch line.
  - **5.10.** A decision note records why it stays open at archive.

  Done 2026-10-06 (offline; no model call). Gate rerun before archiving (6.2).

## 3. Documentation

- [x] 3.1 Update `AGENTS.md` Commands:
  - add `uv run poe host-login claude [--reset]` (the user only, interactive), `uv run poe host-status` (agents may run it; no model call) and `uv run poe host-logout claude` (the user only);
  - add one sentence after the block: agents never run `host-login` or `host-logout`, not through Bash and not through a terminal tool or a TTY wrapper such as `script`, and relay a refusal naming them to the user as a USER ACTION. The command's terminal and agent-marker refusals are speed bumps; this rule is the guard.

  Verify by reading the diff, and confirm that `uv run poe test` stays green.

  Done 2026-10-05; `poe test` green (4.1).
- [x] 3.2 Update `harness/README.md`:
  - **A new "Harness login" section:**
    - the location and the override guard;
    - the one-time setup (extra usage off, then `host-login`);
    - status, logout and reset;
    - the fail-closed list with each remedy, and the L3 caveat that closes a `host-login` remedy until L3 passes;
    - the fallbacks in order: token mode first, then the `CLAUDE_REAL_CONFIG_DIR` opt-in, which lasts until L1. Beside the opt-in, the R1 and R4 caveat: it links your own login, so a concurrent refresh, or a stop part-way through a refresh, can log your own CLI out. Termination before kill helps only if the host finishes its write on SIGTERM, which is unverified (L9);
    - the L1, L2, L3 and L9 status lines.
  - **The "Which path to use" table** gains a one-time setup row.
  - **Rewrites.** Rewrite the Skill-routing isolation and link-hazard paragraphs: the harness home replaces `~/.claude`, `ROUTING_CONFIG_DIR` is gone, and the claim now lives in the home. Also rewrite the Dev-runs `--isolated` sentence, the judge's preflight bullet and the install-probe paragraph ("keeps the linked stored login current").
  - **Billing.** In the Skill-routing section: a billing signal in any case voids the sweep. In the smoke paragraph: a scenario untested for billing stops the remaining scenarios, and a stale summary log is cleared with `--summarize`.
  - **Date boundary.** Before this change, isolated runs linked and refreshed `~/.claude`.

  Verify that `uv run poe test` stays green, since README text is pinned by some L0 tests.

  Done 2026-10-05: a "Harness login (isolated Claude runs)" section before "Dev runs" (location and guard, setup, status/logout/reset, the fail-closed table with remedies and the L3 note, the fallbacks with the R1/R4 caveat on the opt-in and the L9 condition, L1/L2/L3/L9 status lines marked not yet run, the 2026-10-05 date boundary); the setup row in "Which path to use"; the routing isolation, link-hazard, billing, judge, `--isolated`, smoke and install-probe paragraphs rewritten. The L9 wording stays conditional until 5.5 records an outcome. `poe test` green.

## 4. Gate

- [x] 4.1 Run `uv run poe test` (not `test-fast`) and confirm it is green: pytest, ruff with the full rule set, `test_repo_conventions.py`, drift and conform.

  Done 2026-10-05: 2875 passed, 1 skipped; ruff clean; generated copies in sync; all 11 skills conform. Rerun after 2.10: 2916 passed, 1 skipped; ruff clean; in sync; all 11 skills conform. Rerun after 2.11 (2026-10-06): 2920 passed, 1 skipped; ruff clean; in sync; all 11 skills conform.
- [x] 4.2 Run `uv run poe cov` and confirm that the 78% floor holds.

  Done 2026-10-05: 90.92% (host_login 92%, routing 94%, claude_cli 97%, claude_runner 92%). Rerun after 2.10: 91.12% (host_login 95%, routing 95%, claude_cli 97%, claude_runner 92%). Rerun after 2.11: the same.
- [x] 4.3 Run `uv run poe specs` and `openspec validate add-harness-claude-login --strict`, and confirm both pass.

  Done 2026-10-05: `poe specs` 21 passed, 0 failed; the change is valid. Rerun after 2.10: the same. Rerun after 2.11: the same.

## 5. Live checks (after 4)

Paused here on 2026-10-05, uncommitted and unarchived: 5.1 and 5.2 are USER ACTIONs (confirm extra usage is off; run `uv run poe host-login claude` in a terminal outside any agent session). Until 5.2 runs, every isolated run, routing sweep, judged run, `poe smoke` and the install probe refuse with that remedy, unless `CLAUDE_CODE_OAUTH_TOKEN` is exported. 5.3, 5.4 and 5.6–5.9 need the login from 5.2. 5.5 (L9) needs no login and no model call; it waits only for its place in Decision 11's order, after the 5.4 USER ACTION. (Later on 2026-10-05: 5.5 ran during the logins, see its record; what gates 6.1 and 6.2 is recorded under 6.1.)

- [x] 5.1 **USER ACTION** (precondition, no command): confirm that extra usage is still off in the claude.ai account's usage settings. It was confirmed in change 1, task 5.4.

  Done 2026-10-05: the user confirmed extra usage off earlier the same day (change 1, task 5.4) and changed nothing since.
- [x] 5.2 **USER ACTION:** in a terminal outside any agent session, run `uv run poe host-login claude` and complete the browser login. Record the date and time of the login here.

  Done 2026-10-05 (user-reported, same session; time approximate, during this session's pause after 4.3): the user ran `uv run poe host-login claude` and completed the browser login with the normal claude.ai account. Time from the harness home's modification times (no contents read): the marker was written at 23:14:44 +0200, when the login command seeded the home just before this login, so the login was at about 23:15 +0200; its credentials file was replaced by 5.4's re-login.
- [x] 5.3 Run `uv run poe host-status`. Record each key's value (booleans and enums only) and `access_expires`.
  - Pass requires all of these: `marker: yes`, `logged_in: yes`, `auth_method: claude.ai`, `api_provider: firstParty`, `config_dir_matches: yes` and `clean: yes`.
  - **If `clean: no` names `skills/synced`, `plugins/synced`, or any other synced skill or plugin:** stop. This is an L7 regression: change 1's opt-outs did not hold in the persistent home. Report it to the user and run none of 5.4 to 5.9. Never relax the clean rule for synced content. The D1(c) revision through `openspec-update-change` follows.
  - **If `clean: no` names another entry:** the host rewrote its own state. Record the entry, and adjust the clean rule for that entry only through `openspec-update-change` before continuing.
  - No modification time of your own `~/.claude/.credentials.json` is recorded, here or later (design Decision 11).

  Done 2026-10-05: **pass.** The status was read after the 5.4 re-login (the user ran 5.2 and 5.4's steps 1–2 back to back), so this reading stands for 5.3 and for 5.4 step 3; an agent reran it before 5.6 with the same values. Exit 0; `home` the default harness home under `~/.local/state/thesis-proposal-dev/hosts/claude`; `marker: yes`, `logged_in: yes`, `auth_method: claude.ai`, `api_provider: firstParty`, `config_dir_matches: yes`, `clean: yes`, `access_expires: in 7h`, `runs_use: harness`. No synced or other entry was named, so the clean rule stands unchanged.
- [x] 5.4 L3: logout revokes only the harness grant. Run it now, before any harness run.
  1. **USER ACTION:** `uv run poe host-logout claude`. Its output carries the L3 caveat.
  2. **USER ACTION:** in a terminal outside any agent session, `uv run poe host-login claude`.
  3. Run `uv run poe host-status`, which must read ready as in 5.3.
  4. **USER ACTION** (observation, no command beyond your own use): send one prompt in your own Claude Code CLI and open the desktop app. Both work without a new login.

  Pass requires all four. On a pass, set `host_login.L3_PASSED = True`, which swaps the caveat for "Your own Claude login is not affected", and confirm that `uv run poe test` stays green. Record the result and the date and time of this login here. The observation in 5.8 re-confirms it over the following hours. On a failure, keep `L3_PASSED = False`, record what failed, and go to 5.10.

  Done 2026-10-05: **pass, all four steps.** (1) The user ran `uv run poe host-logout claude`; (2) then `uv run poe host-login claude` in a terminal outside any agent session and completed the browser login with the normal claude.ai account (user-reported, same session, right after 5.2; at 23:15:56 +0200, the harness home's `.credentials.json` modification time, read with `stat` only — `access_expires: in 7h` afterwards rules out a refresh since, so the earliest start of 5.8 is 2026-10-06 about 07:16 +0200); (3) `host-status` read ready, as recorded under 5.3; (4) the user then sent a prompt in their own Claude Code CLI and opened the desktop app: both kept working without a new login. `host_login.L3_PASSED` is now True; the README's L3 status line and login-note paragraph say so. `uv run poe test` green afterwards (the L0 tests are parametrized over both values, no test edit).
- [x] 5.5 L9: the SIGTERM probe. An agent may run it: no model call, no credentials.
  - **Setup.** Create a scratch configuration under the session scratchpad holding `PINNED_SETTINGS` and an empty `anthropic-empty/`, with no credentials.
  - **The probe.** Drive it from one scratch script under the scratchpad, not inline Python.
    1. Start `claude -p --output-format stream-json --verbose` under `host_login.allowlisted_env(CLAUDE, <config>)`, with `CLAUDE_CODE_OAUTH_TOKEN` removed. Its standard input is a pipe that is held open and never written to.
    2. After 2 s, if the process is still running, read the `SigCgt` line of `/proc/<pid>/status` and test the SIGTERM bit.
    3. Send SIGTERM. Record the exit status and the time to exit, bounded by `TERM_GRACE_S`, after which the script kills the process.
  - **Outcome.** Record here one of:
    - caught;
    - uncaught;
    - inconclusive: the process exited before the read, or the PID is a wrapper rather than the host.

  Set the README's R4 wording from it (task 3.2). The caveat on the opt-in stays either way.

  Done 2026-10-05: **caught.** Claude Code 2.1.284, one scratch script under the session scratchpad (`l9/probe.py`), a scratch configuration holding only `PINNED_SETTINGS` and an empty `anthropic-empty/`, no credentials before or after. After 2 s the PID was the host itself (`/proc/<pid>/exe` = `/opt/claude-code/bin/claude`; `/usr/bin/claude` is a shell wrapper that `exec`s, so not a wrapper PID). `SigCgt: 0000000173806cff`, SIGTERM bit (1<<14) set; `SigIgn: 0000000000001000` (SIGPIPE only), `SigBlk` empty. On SIGTERM the host exited with status 143 after 0.264 s, well inside `TERM_GRACE_S` = 10, so no kill; nothing on stdout or stderr. A handler exists and ends the process itself; whether it finishes a refresh write in progress stays unobserved (design Decision 9). README R4 wording and L9 status line set accordingly; the opt-in keeps its R4 caveat. It ran before the 5.4 USER ACTION, out of Decision 11's order, while the 5.2–5.4 logins were in progress: it touches neither the harness home nor any login, so the order does not affect it. `poe test` green.
- [x] 5.6 Run a judged isolated dev run on the subscription, once: `uv run poe dev write_from_seed --model haiku --isolated --judge --keep --max-budget-usd 1 --max-notional 1`.
  - Pass requires all of these:
    - the summary's `login` is `harness`, and its `login_dir` is the `home` that `host-status` printed;
    - the outcome is not untested for a login, environment, account-surface or billing reason;
    - the judge produced grades.
  - If the run is refused for a login reason, relay the named remedy to the user as a USER ACTION and rerun once.
  - Record the result here, then delete the kept workspace.

  Done 2026-10-05: **pass**, first run, no refusal. Summary: `config: isolated`, `login: harness`, `login_dir` the `home` from 5.3, `billing: null`; model `claude-haiku-4-5-20251001`, Claude Code 2.1.284, 14 turns, 66 s, no helper agents (`single_context` PASS), `cost_usd` 0.156 (notional, subscription). L1 PASS. The judge (`claude-sonnet-5-5`, effort medium, 2.1.284) produced grades for both criteria — `write_l2_rq_quality` PASS, `write_l2_density` FAIL — with `notional_usd` 0.042 and `rate_limit` `allowed` (five-hour window). The outcome is therefore FAIL, exit 1: a graded L2 criterion, a skill-quality verdict and none of the untested reasons, so it does not bear on this check. The temporary configuration was gone after the run; the kept workspace was deleted. Side observation, outside this change: proposal-write's closing message told the student to run `/code-review`, a host command, not a proposal skill (the skill's text names no such command; haiku's own addition). Recorded as a follow-up for proposal-write's closing guidance.
- [x] 5.7 Run one routing case on the subscription: `uv run poe routing --case review-canonical --epochs 1 --no-report`.
  - Pass requires all of these:
    - the case is not an error for a login or billing reason, and the sweep is not voided;
    - the newest `logs/routing/*.json` payload records `login: harness`, with `login_dir` the harness home.
  - Record the result here.

  Run 2026-10-05: **fail, not ticked.** The login half holds: the payload (`logs/routing/20261005-232214.json`) records `login: harness` and `login_dir` the harness home, and no login error occurred. The billing half does not: the case errored with "not a subscription result: rate limit not reported, overage cannot be ruled out (Claude Code 2.1.284)", the sweep was voided ("a billing signal voids every case of the sweep … no further case was started"), `route` null in the payload, exit 1. One diagnostic rerun of the same case with `--keep-events` (subscription, one host start) failed identically and recorded the stream the rig read: `system/init`, one `assistant` event holding only the `Skill` call for `proposal-review`, then the `user` event with its tool result — and no `rate_limit_event`. On 2.1.284 a `Skill` call's tool result arrives before the turn's rate-limit report, so `_case_decided` stops at that `user` event (`TURN_END`) before the report can arrive, and `case_billing` voids every routed case. 2.9's premise (the report before the routing turn's tool results) holds for `write-polish-collision`'s first turn (a `Glob` call: report, then the tool result) but not for a `Skill` call; the synthetic `route-before-report.jsonl` encodes the order that does not occur here. Where the report lands after a `Skill` call's result (before the next model event, or only at the turn's or run's end) was not observed, since the rig stops at the result. The fix is a revision of Decision 10's stop condition through `openspec-update-change`; 5.7 reruns after it. (The rerun replaced the earlier gitignored `logs/routing/events-review-canonical.jsonl`, which held the same prefix without the `user` event.) The stream is committed reduced as `tests/unit/data/routing_streams/skill-result-unreported.jsonl` (2.10). Rerun pending after 2.10 (an agent may run it; one subscription host start): the same command, with `--keep-events` so the stream shows where the report landed.

  Diagnostic observation 2026-10-05, after 2.10 and before the rerun: one subscription run of `review-canonical` (sonnet, 2.1.284, `apiKeySource` none). It used the rig's own isolated configuration, workspace, environment and command line, with only the stop condition replaced to stop at a surface or at `result`, so the whole order was recorded. It ran from a scratch script under the session scratchpad, wrote no repo file and no `--keep-events` log, and removed its configuration and workspace afterwards. Result: `result` after 32.2 s, no error, no surface, route `proposal-review`, 28 events. The single rate-limit report (`allowed`, no overage) was event 4: after the `Skill` call (1), its tool result (2) and the skill's instructions (3, a second `user` event), and before the next turn's first assistant event (5, a new message id). The `result` event carried no rate-limit field. Replayed over the stream, 2.10's `_case_decided` stops at event 4, and `case_billing` is None both there and over the whole stream. The rule before 2.10 stopped at event 2. Recorded, reduced, as `route-before-report.jsonl` (2.11). A second observation run was not needed.

  Rerun 2026-10-06 00:03 +0200, after 2.11 and its gate: **pass.** `host-status` read ready beforehand (`marker`, `logged_in`, `clean` yes, `auth_method` claude.ai, `api_provider` firstParty, `config_dir_matches` yes, `runs_use: harness`). The exact command ran once on the subscription, without `--keep-events`, which the observation run had made unnecessary. Output: "routing: 1/1 correct", exit 0, about 3 s wall-clock. The rig stopped at the report instead of reading the 30 s skill run. Payload `logs/routing/20261006-000317.json`: `login: harness`, `login_dir` the harness home that `host-status` prints, `review-canonical` with route `proposal-review` and `error` null. No login or billing error, and the sweep was not voided.
- [ ] 5.8 L1: the first natural refresh.
  1. Wait until `uv run poe host-status` shows `access_expires: expired …`, at least 8 hours after the login in 5.4, with no harness run since the access token expired.
  2. Record `M1 = stat -c %Y <harness home>/.credentials.json`. That is the harness home's file, which only the harness touches.
  3. Run `uv run poe dev check_report --model haiku --isolated --max-budget-usd 0.5` once (subscription).

  Pass requires all of these:
  - the run is not untested for a login reason;
  - its summary's `login_dir` is the harness home;
  - the home's credentials mtime is now later than M1, which shows the write-back;
  - **USER ACTION** (observation over the following hours, no command): your own CLI and the desktop app keep working without a new login.

  Record the result here. If it fails, go to 5.10.

  Decision 2026-10-05 (user): L1 is a recorded follow-up observation and does not gate 6.1 or 6.2; neither does L2 (5.9). L1 still gates step B (`run-isolated-in-harness-home`), which removes the `CLAUDE_REAL_CONFIG_DIR` opt-in. That is the scope the design brief §2.11 already gave L1, and Decision 11's table row ("gates removal of the opt-in, in step B"); only the Migration Plan's "archiving waits for it" said otherwise, and it now carries the same note. The README's L1 and L2 status lines say they are pending observations. If L1 later fails, 5.10's fallback and documentation apply through a follow-up change, since this one will be archived by then.
- [x] 5.9 L2: the login's total lifetime. Add one line to the "Harness login" section of `harness/README.md` with the login date from 5.4 and what to note when it happens: the date of an "expires in N days" warning or of the login's end. The observation continues outside this change. Verify that the line is present.

  Decision 2026-10-05 (user): a follow-up observation that does not gate 6.1 or 6.2 (see 5.8).

  Done 2026-10-05: the README's L2 status line now carries the login date (2026-10-05, about 23:15 +0200, from 5.4) and what to note: the date of an "expires in N days" warning, or of the day the login stops working. The line is present; the observation itself continues outside this change.
- [ ] 5.10 Conditional: if 5.4 or 5.8 showed your own login affected, record what failed.
  - **Fallback, in this order. First, token mode:** **USER ACTION** `claude setup-token`, then export `CLAUDE_CODE_OAUTH_TOKEN` in the shell that starts the harness.
  - **Last, only if token mode is not possible:** **USER ACTION** export `CLAUDE_REAL_CONFIG_DIR=~/.claude`. It links your own login again, so a concurrent refresh in your own CLI (R1), or a run stopped part-way through a refresh (R4), can log your own CLI out.
  - Never write either into a committed file.
  - Document the failure under "Known limitations" in `harness/README.md`.
  - Propose a follow-up change through the `openspec-propose` skill.

  If 5.4 and 5.8 passed, mark this task "not needed".

  Decision 2026-10-05 (recorded 2026-10-06): 5.4 passed; this task stays open with 5.8, a follow-up observation, and does not gate 6.1 or 6.2. If L1 fails later, the follow-up change carries the fallback.

## 6. Close

- [x] 6.1 Commit the code, tests, docs and this change folder as one commit for the completed change, off `main` until it is complete. Do not push. Verify with `git status` (clean) and `git show --stat HEAD`.

  Decision 2026-10-05 (user): 6.1 and then 6.2 run once 5.2–5.4 (login and L3), 5.6 and 5.7 have passed; 5.5 is done. 5.8 (L1) and 5.9 (L2) are recorded follow-up observations and do not gate either; L1 still gates step B (see 5.8).

  Done 2026-10-06: 5.2–5.7 passed (5.7 on its 2026-10-06 rerun), 2.12 applied, gate green. One commit of this change's files only, made after the archive (6.2) so it carries the archived folder and the synced main spec; the operator's unrelated untracked files and other change folders stay out. Not pushed. 5.8 and 5.10 stay open as recorded follow-ups.
- [x] 6.2 Archive through the `openspec-archive-change` skill. Verify that `openspec validate --all --strict` is green afterwards. Step B (`run-isolated-in-harness-home`, which removes `keep_login`, the claim and the `CLAUDE_REAL_CONFIG_DIR` opt-in) is a separate future change. It is not part of this one.

  Done 2026-10-06: gated first (`sync_shared.py --check`, `poe test`, `poe specs`, `poe cov`), then archived with `openspec archive add-harness-claude-login --yes`; `sync_shared.py`, `poe test` and `poe specs` rerun green on the archived tree.
