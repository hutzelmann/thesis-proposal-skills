# Design

## Context

**Order.** This change lands after `close-claudeai-surfaces` (change 1) and `add-harness-claude-login` (change 2). It builds on what they leave in place:

- **From change 1:** `harness/account_surfaces.py`, the pinned Claude settings, the connector switch, and the account-surface checks.
- **From change 2:**
  - `harness/host_login.py` with the frozen `HostLogin` record and `RECORDS = {"claude": CLAUDE}`;
  - `state_root`, `home`, `check_location`, marker, seed and `wipe`;
  - `LoginProblem(cause, remedy)`, a frozen dataclass that the pure checks return (they never raise it), and `refusal(problem) -> str`, which renders `untested: <cause>. <remedy>. <login note>.`;
  - `login_note(remedy)`, which closes with "Your own Claude login is not affected", or, while `L3_PASSED` is False and the remedy names `host-login`, with the L3 caveat. Both the sentence and the caveat name Claude, and `LoginProblem` carries no client, so this change makes both client-aware (Decision 4);
  - `login_env(record, home, environ)`, the login environment of every login and logout, and the agent-marker speed bump (`AGENT_MARKERS`, `agent_session_markers`);
  - `allowlisted_env(record, config, environ)`, the single env-allowlist builder, which already takes a record "because change 3's Codex record is the builder's third user";
  - `LoginSource` and `login_remedy(message, source)`;
  - `TERM_GRACE_S` and `stop_child(proc)`, which sends `terminate()`, waits the grace and then kills. Change 1's `routing.follow_stream` stops the rig's and the dev runner's Claude host through it. Change 2 has no `run_host`: its revised Decision 9 dropped it once `follow_stream` read every Claude host stream. This change therefore adds `run_host` for Codex children and gives `stop_child` the record's stop signal (Decision 7);
  - `host_login.main(argv)` behind the poe tasks `host-login`, `host-status` and `host-logout`;
  - "Isolated child environment" and the authentication, opt-out and account-surface rules of "Isolated measurement environment", scoped to Claude children and Claude configurations. Both now say that a client added later is held to the requirements that add it, and that the same builder makes that client's child environment from its own record.

Three of the five MODIFIED requirements here are also modified by change 2: "Harness-owned host logins" (added by change 2), "Dev-runner cost and helper-agent telemetry" and "Subscription text roles (dev runner)". Their blocks start from change 2's text as revised on 2026-10-05, which already folds in change 1's. That revision added the login note and its L3 caveat, the agent-marker refusal, logouts in the login environment, the marker in the status list, the stop at the first surface, the write-back target in the label, and the smoke stop after a billing signal. Each block reproduces that text and adds only the Codex parts. If either earlier change is revised again before it is archived, these blocks must be rebased (tasks 0.1 and 8.2). **Rebased 2026-10-06 (task 0.1):** change 2 was archived with a later text — a relative override refused, an unmarked directory never adopted, a failed logout stopping a re-login, the default Anthropic profile directory barring the Claude commands, the Claude status check without the token, the label following how the configuration was prepared, and a judge error naming its billing reason. The three blocks now start from the archived main spec. The profile-directory rule is scoped to Claude, because a Codex client reads no Anthropic profile; no Codex decision changed. See proposal.md (Why) for the motivation.

**Codex facts this design relies on.** They come from the 0.160 source at `rust-v0.160.0`, the docs, and local `--help` and `features list` output from 0.133 (dossier sections CODEX-CLI, REPO and LOGIN).

- **`codex exec --json` stream.**
  - Events: `thread.started{thread_id}`, `turn.completed{usage}`, `turn.failed{error.message}`, `item.*{item}` and a top-level `error`.
  - Item types: `agent_message`, `command_execution`, `file_change`, `mcp_tool_call`, `collab_tool_call` (`spawn_agent`, …), `web_search`, `todo_list` and `error`.
  - Missing from the stream: the model ID, the CLI version, cost, rate limits and the auth mode.
  - A model swap appears only as an error item, `model rerouted: A -> B (…)`.
  - `usage.input_tokens` includes `cached_input_tokens` (`TokenUsage::non_cached_input`).
- **The session record.** It lives at `$CODEX_HOME/sessions/YYYY/MM/DD/rollout-*.jsonl` and is not written under `--ephemeral`.
  - `session_meta` carries `cli_version` and `model_provider`.
  - `turn_context` carries `model` (the requested one) and `effort`.
  - `event_msg` of type `token_count` carries `rate_limits{primary, secondary, credits, plan_type, rate_limit_reached_type}`.
  - The skills block lists every offered skill as `(file: /abs/SKILL.md)`.
- **Auth.**
  - `CODEX_API_KEY` beats every stored login in `exec`. With `forced_login_method = "chatgpt"`, `enforce_login_restrictions` then logs the home out.
  - `auth.json` is written by truncate+write.
  - Refresh happens in place, guarded only by an in-process lock plus a reload.
  - `codex login` revokes the previous refresh token held in its home, and `codex logout` revokes too.
  - `codex login status` writes to stderr: `Logged in using ChatGPT`, `Logged in using an API key - <masked>`, or `Not logged in`.
- **Skills.**
  - Discovered under `<cwd…project-root>/.agents/skills`, `$HOME/.agents/skills`, `$CODEX_HOME/skills/.system`, `/etc/codex/skills`, and from plugins.
  - There is no Skill tool. The model opens `SKILL.md` through the shell.
- **SIGINT.** `exec` turns it into a turn interrupt and exits 1.
- **The quota read.** `codex app-server` speaks JSONL over stdio. After `initialize` and `initialized`, `account/rateLimits/read` performs a GET to `backend-api/wham/usage`, which is not a model call. The handshake is UNVERIFIED (X4b).
- **Where `CODEX_HOME` cannot live.** Under the system temporary directory, Codex refuses to create its helper binaries.

## Goals / Non-Goals

**Goals:**

- One runner with one adapter per host, Claude and Codex in this change. Every existing Claude test passes unchanged, apart from the seams named in the tasks.
- Under no environment, configuration or account state can a Codex run bill anything but plan quota. Every way it could is refused before the run, or marked untested after it.
- Every Codex check is a pure function over a stream, a quota answer, a directory listing or an environment mapping, tested offline on synthetic streams derived from the source.
- No agent and no test ever needs a ChatGPT login. Live runs refuse until the user has logged in, and they keep refusing while the login's plan is not Plus or Pro, so the free-plan rehearsal can never lead to a model call.

**Non-Goals:**

- **Recorded Codex streams and the X-check outcomes.** These belong to the follow-up change `record-codex-streams`, after Plus.
- **A Codex judge** (`add-codex-dev-judge`, only if D3 changes), **a Codex smoke**, and **a Codex routing rig.**
- **Anything that feeds `report.py`**, a host column, or a Codex registry role.
- **Ambient Codex.** The operator's `~/.codex` routes to OpenRouter.
- **Claude step B** (`run-isolated-in-harness-home`).
- **Changing the ambient default for Claude** (D5(b)).
- **A Codex install probe.**

## Decisions

### 1. Spec shape

- **Two ADDED and five MODIFIED requirements**, as brief §5 item 3 lays out.
- **"Harness-owned host logins" is MODIFIED, not added.** The brief says "ADDED: Codex in 'Harness-owned host logins'", but the requirement will exist in the main spec once change 2 is archived. Extending it keeps one requirement for all client homes, which its own text anticipates ("A client added later gets its own home under the same rules").
  - Today `openspec validate --strict` passes with an INFO line: "Archive would refuse this delta … not found". That is expected until change 2 is archived (task 8.2).
- **"Isolated child environment" and "Isolated measurement environment" are not modified a third time.** Change 2's revision scopes both to Claude: the allowlist, the configuration-directory variable, the connector switch and the profile directory govern Claude children; the authentication, opt-out and account-surface rules govern Claude configurations; and a later client's child environment is left to the requirement that adds it, built by the same function from that client's record. A Codex child therefore falls under neither requirement's Claude clauses. The Codex child's environment is specified in "Codex plan billing guard", which requires it to be built by the same function, and the Codex home's rules sit in "Harness-owned host logins". That keeps the env rules per client next to the checks that rely on them, and it avoids a third rebase of two requirements changes 1 and 2 already rewrite.
  - Task 0.1 checks that change 2's final text of both requirements still carries that scoping, and task 8.2 checks the archived text again. If it does not, this change adds MODIFIED blocks for both, starting from that text and carving out Codex children and the Codex home, pointing to "Codex plan billing guard" and "Harness-owned host logins". Before any code is written, Decision 1 and task 0.1 then name five shared blocks instead of three.
- **Every scenario name from change 2's text, change 1's text and the main spec is kept.** OpenSpec refuses a MODIFIED block that drops one. A name-by-name comparison against change 2's text as revised on 2026-10-05 found none missing (tasks 0.1 and 8.2 repeat it).
- **Host-generic wording.** The ADDED and MODIFIED text names a host only where the rule is that host's own: Claude's tool denial and connector switch, and Codex's invocation, billing guard, skill directory, label and judge scenarios. Everywhere else it says "every host", "the host's skill directory", "a host that offers none" or "every non-Claude host", and never counts the hosts. A later host's change (`add-copilot-dev-runner`) therefore need not modify "Inverted-hybrid runners", "Measured environments carry no eval definitions" or "Subscription text roles (dev runner)" again. The rewording changes no Codex rule: each generic sentence still names Codex where its rule depends on it, and every scenario name is kept.
- **New scenarios in the shared blocks.** "Harness-owned host logins" gains "Codex stored login never opened" and "Codex login note until X8" beside its other Codex scenarios. "Dev-runner cost and helper-agent telemetry" gains "Codex precondition is untested, not a runner failure". "Codex plan billing guard" carries "Only the Codex home variable is exempt", "Credits state missing", "Plan outside the allowed set" and "Credits drawn during a run".

### 2. One runner: `harness/hosts.py`

```python
@dataclass(frozen=True)
class RunView:            # pure readers over the saved event list
    final_text: str
    model_requested: str
    model: str | None     # Codex: "unreported" unless a reroute names one
    cli_version: str | None
    telemetry: dict

@dataclass(frozen=True)
class JudgeBackend:
    host: str             # the host whose CLI grades: "claude"
    call: Callable; preflight: Callable
    isolation: Callable[[ExitStack], Path]

@dataclass(frozen=True)
class Host:
    name: str; binary: str
    skill_dir: tuple[str, str]          # (".claude","skills") | (".agents","skills")
    run: Callable[..., list[dict]]      # run_claude | codex_cli.run_codex
    read: Callable[[list[dict], argparse.Namespace], RunView]
    isolation: Callable[[ExitStack, argparse.Namespace], Path | None]
    login: HostLogin
```

- **Where the hosts are built.** `HOSTS` is built in `claude_runner`, not in `hosts.py`, because the Claude callables live there. Each callable is a lambda over the module attribute, for example `run=lambda *a, **k: run_claude(*a, **k)`. That keeps every existing monkeypatch working: `claude_runner.run_claude`, `claude_runner.isolated_config`, `claude_runner.follow_stream` (where change 1 moved the dev runner's fakes and change 2 kept them), and `claude_cli.call`/`preflight`.
- **Selection.** `host_for(args)` returns `HOSTS[getattr(args, "host", "claude")]`, so the test `ARGS` namespace without `host` stays valid. `summary`, `failure_summary`, `identity`, `completed_run`, `dev_run` and `rejudge_lines` read through it.
- **Staging.** `stage(scenario, ws, install_skill, skill_dir)` replaces the `.claude/skills` literal.
- **Complexity.** Host branches live only in the `Host` objects. `dev_run` gains no branch.

*Alternative:* a separate `codex_runner.py`. Rejected: it would be about 1,300 copied lines, the failure mode `AGENTS.md` names.

### 3. CLI surface

| Flag | Claude | Codex |
|---|---|---|
| `--host {claude,codex}` | default | opt-in |
| `--model` | default stays `haiku`. The argparse default becomes `None` and resolves to `haiku` for Claude only, so an explicit model can be told apart | required. A value containing `/` is refused (usage error, exit 2) before staging. Passed verbatim to `-m` |
| `--effort` | refused (usage) | optional, one of `low`, `medium`, `high`, `xhigh` or `max`. `ultra` is not a choice, because it hands work to subagents (the 2026-09-02 fan-out class) |
| `--max-budget-usd` | passed through | refused: Codex has no cap |
| `--isolated` | opt-in (D5(b)) | implied, and accepted without effect |
| `--judge` | requires `--isolated` | the judge enters its own Claude isolation (Decision 11) |
| install scenarios | as today | refused (usage) |
| `--summary-log` | refused under `logs/evals/` | same |

- **Model IDs.** There is no Codex model slug anywhere in harness code, `pyproject.toml` or the registry (Rule A). `support.is_subscription_model` and `model_currency` are untouched.
- **The summary-log guard.** It enforces the existing "SHALL NOT be written where the support report reads" clause, for every host. `report.py` reads `logs/evals`.
- **What a Claude invocation gains.** Exactly two things, both named in "Dev-runner host adapters": the `host` and `label` summary keys, and the summary-log guard. `--effort` on Claude is a usage error, as an unknown flag already is today, so it changes no outcome.

### 4. The Codex `HostLogin` record

`HostLogin` gains three fields. Each has a default that leaves `CLAUDE` unchanged:

- `strip_suffixes`;
- `stop_signal` (default SIGTERM);
- `outside_tempdir` (default False).

`child_vars(config)` becomes a record field, so that change 2's Claude-only constants (the connector switch and the profile directory) move into `CLAUDE`'s value. It is used in three places: `allowlisted_env` adds it to the admitted names, the record-driven `login_env` adds it to the stripped operator environment, and its names are the exact exemption set of the pre-spawn assertion (Decision 8). The `CODEX` record:

| Field | Value |
|---|---|
| `binary`, `home_var` | `codex`, `CODEX_HOME` |
| `login_argv` / `status_argv` / `logout_argv` | `("login",)` (+ `--device-auth` on request) / `("login","status")` / `("logout",)` |
| `admitted` | `CLAUDE.admitted` minus `CLAUDE_CODE_OAUTH_TOKEN` |
| `login_strip_prefixes`, `strip_suffixes` | `CODEX_`, `OPENAI_`, `OPENROUTER_`; `_API_KEY` |
| `seed` | `config.toml` = `PINNED_CONFIG_TOML` |
| `forbidden` | `AGENTS.md`, `AGENTS.override.md`, `.env`, `hooks.json`, `skills/*` except `skills/.system`, any entry in `memories/` |
| `failure` | the three refresh messages (`manager.rs:206-208` @0.160), the restriction logout line, `Not logged in` |
| `stop_signal`, `outside_tempdir` | SIGINT, True |
| `child_vars(home)` | `{"CODEX_HOME": str(home)}` |

- **`check_location`** gains a `tempdir` parameter, which callers fill from `tempfile.gettempdir()`. For a record with `outside_tempdir`, a root at or inside it is refused. L0 tests pass a `tempdir` that does not contain `tmp_path`. This resolves the collision change 2 left open: the rule applies only to Codex, and the pure function takes the temporary directory as an argument rather than reading it.
- **`check_codex_home(home)`** compares the `tomllib`-parsed `config.toml` with the pinned dictionary, naming the first differing key path. It then checks the forbidden list. The allowed host state is marketplace and plugin caches, `log/`, `*.sqlite`, `installation_id`, the models cache, `shell_snapshots/`, `skills/.system`, `.harness-run.lock` and `quota.json`.
- **`codex_status(stderr)`** is pure and maps the status line to `chatgpt`, `api-key`, `access-token`, `other` or `none`. It never retains the line, so the masked key fragment is dropped at the parse.
- **`codex_version(stdout)`** parses `codex-cli X.Y.Z`. `CODEX_MIN_VERSION = (0, 160, 0)`, because the 0.160 catalog is the first that serves the current Plus models.
- **Status.** `host-status codex` prints exactly the keys the spec's status list names, and nothing else:
  - `home`, `marker`, `logged_in`, `auth_method`;
  - `config_pinned` and `clean` (the list's cleanliness item, which for Codex also says whether the configuration equals the pinned one);
  - `last_written`, the age of `auth.json` taken from `os.stat(...).st_mtime`. The file is never opened. Codex rewrites it on every login and refresh (`storage.rs:206-223`), so its modification time is the Codex counterpart of change 2's `expiresAt`;
  - `cli_version`, `min_version`, `features_ok`;
  - `last_quota`, the snapshot from `quota.json` (windows, reset times, plan type);
  - `runs_use: harness`.

  `--quota` adds a live read under the lock (Decision 7), printed as `quota` beside the snapshot. It is the list's "only on request" item. Exit codes are change 2's: 0 ready, 3 not ready, 2 usage. With `--quota`, a read that `quota_problem` refuses (Decision 9) is "not ready", so on the free plan the rehearsal's status exits 3 by design.
- **Login.** `host-login codex` follows change 2's sequence:
  1. the two speed bumps, unchanged: the terminal check and change 2's agent-marker check (`AGENT_MARKERS` keeps change 2's two Codex names; see Open Questions);
  2. location check;
  3. seed;
  4. take the run lock;
  5. logout first if logged in, wipe on `--reset`;
  6. run `codex login`.

  `login_env` becomes record-driven. For `CODEX` it is `os.environ` minus the strip families (`CODEX_*`, `OPENAI_*`, `OPENROUTER_*`, `*_API_KEY`) and the session variables, plus `CODEX_HOME`. Every Codex logout uses it, as every Claude logout does. The logout and reset messages carry the X8 caveat before they log out, until X8 passes.
- **The login note per client.** Change 2's `login_note` and `refusal` name Claude. This change makes them client-aware without touching Claude's text:
  - `LoginProblem` gains `client: str = "claude"`. The default keeps every change 2 call site and test unchanged;
  - `NOTES` maps each client to its not-affected sentence, its caveat and its pass flag: `"claude"` → ("Your own Claude login is not affected", the L3 caveat, `L3_PASSED`); `"codex"` → ("Your own Codex login is not affected", "Whether this logs out your other ChatGPT sessions is unverified (X8)", `X8_PASSED`);
  - `login_note(remedy, client="claude")` picks the caveat while that client's flag is False and the remedy names `host-login <client>`, with or without `--reset`. `refusal(problem)` passes `problem.client`;
  - `login_remedy(message, source, record=CLAUDE)` becomes record-aware: it matches `record.failure` and closes the harness remedy with `login_note(..., record.name)`;
  - `X8_PASSED = False` is a module constant. Task 6.4 flips it once X8 passes, and the L0 tests are parametrized over both values, so the flip needs no test edit.

  Until X8 passes, every Codex message whose remedy is `uv run poe host-login codex`, with or without `--reset`, therefore carries the caveat instead of the not-affected claim: the preflight refusals, the login-failure rows of `failure_reason`, and the logout and reset notes. Every `codex login` revokes the refresh token the home held before (`cli_login.rs:122-153`), so the remedy is exactly the command whose reach X8 settles.

### 5. Pinned configuration, strict validation, feature allowlist

```toml
model_provider = "openai"
forced_login_method = "chatgpt"
cli_auth_credentials_store = "file"
web_search = "disabled"
check_for_update_on_startup = false
[history]
persistence = "none"
[analytics]
enabled = false
[feedback]
enabled = false
[skills.bundled]
enabled = false
```

- **One text, one parse.** The stdlib has no TOML writer. `PINNED_CONFIG_TOML` is therefore a fixed text, and an L0 test asserts that `tomllib.loads(PINNED_CONFIG_TOML) == PINNED_CONFIG`. The key names are UNVERIFIED for 0.160 (X7).
- **Pins live in the file, not in `-c`.** `-c` silently accepts unknown keys; a critic showed that `-c 'not_a_real.key=false'` exits 0. Every run passes `--strict-config`. Two `-c` keys remain per run, and both are harmless if silently dropped:
  - `model_reasoning_effort` is checked after the run against `turn_context.effort`;
  - `sandbox_workspace_write.network_access=true` falls back to off, so a network scenario fails visibly.
- **No `--ignore-user-config`.** The home's `config.toml` is the harness's own, and it is the file `--strict-config` validates.
- **Features.**
  - `DISABLED_FEATURES` is pinned from `codex features list` at `CODEX_MIN_VERSION`. It starts from the 0.133 default-on set and is confirmed in X7: `browser_use_external`, `in_app_browser`, `plugin_hooks`, `plugin_sharing`, `tool_suggest`, `skill_mcp_dependency_install`, `workspace_dependencies`, `guardian_approval`, `goals`, `fast_mode`, `apps`, `plugins`, `hooks`, `memories`, `image_generation`, `browser_use`, `computer_use`.
  - Each feature is passed as `--disable <name>`, which rejects unknown names.
  - `multi_agent` is disabled unless the scenario declares `helpers`. `shell_tool` and `unified_exec` stay on.
  - Before each run, and under the lock, `codex features list` runs with the same flags. `features_problem(listing, allowed)` refuses when anything outside the allowlist reads enabled. A newer CLI that adds a default-on feature is therefore refused until `DISABLED_FEATURES` is updated by a reviewed change.

### 6. Command template and sandbox posture (D4(a))

```
<allowlisted env; CODEX_HOME=<home> HOME=<scratch> XDG_{CONFIG,CACHE,DATA,STATE}_HOME=<scratch>/…>
codex exec --json --strict-config --skip-git-repo-check -C <ws> -s workspace-write
  -m <model> [-c 'model_reasoning_effort="<e>"']
  [-c sandbox_workspace_write.network_access=true]
  --disable <each of DISABLED_FEATURES> [--disable multi_agent]
  -            # prompt on stdin
```

- **Network.** `needs_network(scenario)` is pure. It is true when the scenario has `serve`, or when its skill or siblings intersect `{proposal-import, proposal-lit-search, proposal-reverse}`. Among today's scenarios that covers `import_messy`, the three `supervise_*` (lit-search and import siblings) and the three `ideate_scoped*` (served fixture).
- **No `--ephemeral`.** The session record is the only source of the provider, the CLI version, the served effort and the quota (Decision 8).
- **Scratch `HOME`.** It is a temporary directory per run, next to the workspace under the system temporary directory. That location is allowed for `HOME`; only `CODEX_HOME` is barred. It hides `~/.agents/skills` (`grill-me` leaked into a local render), shell rc files and `api-keys.env`. The sandbox treats the temporary directory as writable, so pandoc and typst caches under `XDG_CACHE_HOME` can be written (UNVERIFIED for publish; there is no publish scenario today).
- **The workspace** comes from `tempfile.mkdtemp` and lies outside any git repository, so Codex's project root is the workspace itself.

*Alternatives:* D4(b), bypassing the sandbox with subagents always on, was rejected by the user. D4(c), network always off, would fail the network scenarios by design.

### 7. Serial runs: `host_login.run_lock(home, wait)`

- **The lock.** `run_lock` is a context manager. It opens `<home>/.harness-run.lock` (0600), polls `fcntl.flock(LOCK_EX | LOCK_NB)` for up to `LOCK_WAIT_S = 30`, and yields the descriptor. On timeout it raises `RunLockBusy`, a dedicated exception that carries a `LoginProblem(cause="another Codex run holds the harness home (<lock path>)", remedy="rerun after it ends", client="codex")`. `LoginProblem` itself stays a value that checks return, as change 2 defines it. `run_codex` maps `RunLockBusy` to an untested `RunnerFailure` through `refusal(err.problem)`, and `host_login.main` maps it to exit 3.
- **The child holds it.** This change adds `host_login.run_host(record, argv, *, cwd, env, timeout, input=None, pass_fds=())`, which runs a Codex child to completion: `Popen`, then `communicate(input, timeout)`; at the timeout it calls `stop_child(proc, record.stop_signal)` and re-raises `TimeoutExpired`. Change 2 has no `run_host`, because its Claude children are read through change 1's `routing.follow_stream`. `stop_child` therefore gains a signal parameter that defaults to SIGTERM, sent through `send_signal`, so `follow_stream` and change 2's tests behave as before. The Codex child receives the lock descriptor through `pass_fds`. `flock` binds to the open file description, so the lock is held while the child lives, even after the harness is killed.
- **Parent death.** On Linux, `preexec_fn` calls `prctl(PR_SET_PDEATHSIG, SIGINT)` through `ctypes`. SIGINT and not SIGKILL, so that a pending `auth.json` write finishes.
- **What runs under one hold.** The quota read, the features preflight, the run and the session-record capture all happen under a single hold, so nothing else can draw quota between the check and the run. The judge runs after the lock is released.
- **Who else takes it.** `host-login`, `host-logout`, `--reset` and `host-status --quota`.
- **Platforms.** `fcntl` does not exist on Windows. `codex_cli` refuses there with a usage error naming POSIX file locks. On macOS there is no parent-death signal, so the runner works but is unverified.
- **Why 30 s.** It is judgment, not a host constant. Runs are serial by design, and a waiter is a second invocation the operator started. It should fail fast rather than queue behind a ten-minute run.

*Alternative:* change 2's claim file with stale timings. Rejected, because the kernel releases a `flock` on the last close, so there is no stale-claim race.

### 8. Environment and the pre-spawn assertion

- **Building it.** `allowlisted_env(CODEX, home, environ)` builds the base environment, which change 2's builder makes record-driven. `run_env(env, scratch)` then sets `HOME`, `USERPROFILE` and the four XDG directories, following the install-probe precedent. `ignored_env(environ, CODEX)` returns the sorted names of inherited strip-family variables, for the summary's `ignored_env`.
- **`assert_codex_env(env)`** raises `BillingEnvError` naming the variable, never its value. It runs on the final child environment, after `allowlisted_env` and `run_env` have been applied, and it fires when any key matches the strip families, except exactly the names in `CODEX.child_vars(home)`, which is `CODEX_HOME` alone. The exemption is the set of names the harness itself sets, not a prefix rule, so `CODEX_API_KEY`, `CODEX_ACCESS_TOKEN` and an unknown `CODEX_FOO` all fire. `codex_cli.spawn()` is the single function that starts any Codex child (`exec`, `login status`, `features list`, `app-server`). It builds the final environment and calls the assertion on it immediately before `Popen`.
  - It is load-bearing. `exec` honours `CODEX_API_KEY` above everything (`exec/src/lib.rs:726`; `manager.rs:1499-1505`), and `enforce_login_restrictions` would then delete the harness `auth.json`.
  - The L0 pins:
    - with `host_login.allowlisted_env` monkeypatched to leak `CODEX_API_KEY`, then `CODEX_ACCESS_TOKEN`, then `CODEX_FOO`, no `Popen` happens and the outcome is untested;
    - with an environment holding only `CODEX_HOME` from the strip families, the spawn proceeds;
    - with `run_env` patched to add a strip-family name after the builder, the assertion still fires, which shows that it checks the final environment.
- **Third user, no new copy.** This is the third user of the builder `AGENTS.md` asks to be extracted at its third copy. Change 2 extracted it. This change adds no new allowlist.

### 9. The pre-run quota read (D2(a))

- **`read_quota(home, env)`** spawns `codex app-server` under the lock and sends:
  1. `initialize` with `clientInfo {name: "thesis-proposal-dev-runner", …}`;
  2. the `initialized` notification;
  3. `{"method": "account/rateLimits/read", "id": 1}`.

  It reads JSONL until the response with id 1 arrives or `QUOTA_TIMEOUT_S = 20` passes, then stops the child with SIGINT and the grace.
- **`parse_quota(answer)`** is pure and returns a `Quota` dataclass: two `Window(used_percent, window_minutes, resets_at)`, `credits` (`has_credits`, `unlimited`, `balance`, or None when absent), `plan_type` and `reached_type`. It prefers `rateLimitsByLimitId["codex"]` and falls back to `rateLimits`. The session record's `token_count.rate_limits` has the same content in snake case, so one normalizer serves both.
- **`quota_problem(quota)`** is pure and refuses in these cases:
  - the read is unavailable: no answer, an error answer, no primary window, or no credits block;
  - a positive balance, `has_credits`, or `unlimited`;
  - no `plan_type`, or one outside `ALLOWED_PLANS = ("plus", "pro")`. The protocol's values include `free`, `go`, `plus` and `pro` (`protocol/src/account.rs:12-26`); Plus and Pro are the personal plans whose included Codex quota this runner is meant to spend;
  - either window at `QUOTA_STOP_PERCENT = 90` or more;
  - any `reached_type`.
- **An absent credits block refuses.** D2(a) is strictly fail-closed, and a read that cannot say whether credits exist cannot rule out a draw. It is therefore treated as an unavailable read. The account setting (balance 0, auto-reload off) stays the guarantee; this is the backstop. If X4b, and the first Plus read in task 7.2, show that the client never sends the block on Plus, relaxing this rule is a reviewed `openspec-update-change`, never a code edit alone.
- **The plan rule is what keeps the rehearsal harmless.** After X1 the harness home holds a working free-plan login. Without the rule, nothing but process would stand between an agent and a free-plan model call (D6(c), which needs the user's go). With it, every run refuses before any `exec` until task 7.2 logs in again with Plus.
- **The snapshot.** After the run, the session record's last `rate_limits` is written to `<home>/quota.json` by `os.replace`. It holds the windows, reset times and plan type only.

*Alternatives:* D2(b), falling back to the snapshot, leaves the first run of each window unguarded. D2(c), detecting only after the run, can draw credits before anyone notices. The user chose (a).

### 10. Session-record capture and reduction

- **`capture_rollout(home, thread_id)`** finds the run's record, `sessions/**/rollout-*<thread_id>*.jsonl`. The path pattern is UNVERIFIED. The fallback is the one record created during the run whose `session_meta.payload.id` equals the thread id. Then:
  - it reduces the record and appends the results to the event list;
  - it writes `quota.json`;
  - it deletes the whole `sessions/` subtree.
- **The reduced records:**
  - `{"type":"codex.session","id","cli_version","model_provider"}`;
  - `{"type":"codex.turn_context","model","effort"}`;
  - `{"type":"codex.token_count","usage","rate_limits"}`;
  - `{"type":"codex.skills","files":[…]}`, the paths parsed from the skills block;
  - `{"type":"codex.tool","name"}`, for tool calls the exec stream drops (dynamic tools, the `skills.*` namespace);
  - `{"type":"codex.error","message"}`.
- **Why reduce.** `session_meta` can carry base instructions and environment details. Keeping only the fields the readers use means a kept workspace never holds an unknown field, and `save_events`, `load_events` and `--rejudge` keep working on a `list[dict]`.
- **No record found.** The run then has no `codex.session` or `codex.token_count`, and the billing guard reports "plan use cannot be confirmed" (untested).

### 11. Canonical tool calls

- **`codex_cli.codex_tool_calls(events)`** is a dictionary dispatch over `item.completed` events, de-duplicated by item id:
  - `command_execution` becomes `("Bash", {"command"})`. It also becomes `("Skill", {"skill": name})` when the command applies a reader (`cat`, `sed`, `head`, `tail`, `less`, `more`, `bat`, `awk`, `nl`) to `…/.agents/skills/(proposal-[a-z-]+)/SKILL.md`. This mirrors Codex's own invocation heuristic (`core-skills/src/invocation_utils.rs`);
  - `file_change` becomes `("Edit", {"changes"})`;
  - `collab_tool_call` with `spawn_agent` becomes `("Agent", {"prompt"})`, and the other collab tools become `("collab:<tool>", {})`;
  - `mcp_tool_call` becomes `(f"mcp__{server}__{tool}", arguments)`;
  - `web_search` becomes `("WebSearch", {"query"})`.
- **`routing.tool_calls`** returns the Claude shape followed by `codex_cli.codex_tool_calls(events)`. The shapes never collide (`assistant` against `item.completed`). `HELPER_TOOLS`, `VERIFIER_SPAWN_TOOLS`, `verdict_supervise_verifier`, `containment_inputs`, `summary` and `route_from_events` therefore work unchanged.
- **Imports.** `codex_cli` imports `host_login` only and never `routing` or `claude_cli`, so the import has no cycle.
- **The skill read is a heuristic.** No dev-runner verdict depends on a `Skill` call; the routing rig, which does, stays Claude-only.

### 12. Readers, telemetry and failures

- **`codex_read(events, args) -> RunView`:**
  - `final_text` is the last completed `agent_message`;
  - `model_requested` is `args.model`;
  - `model` is `"unreported"`, unless a reroute item names the served model;
  - `cli_version` comes from `codex.session`.
- **Telemetry:**
  - `cost_usd = None`;
  - `notional_usd` comes from the roster row `openrouter/openai/<model>` when `support.parse_registry` finds one. `notional_basis` is `"roster"` in that case and `"unpriced"` otherwise;
  - `tokens_in = input − cached_input`, `tokens_out`, `tokens_cache_read = cached_input`, `tokens_cache_write = cache_write_input` (0.160+), `tokens_reasoning`;
  - `num_turns` is the count of `turn.completed`, and `duration_ms` is measured by the runner;
  - `effort_requested` and `effort_served`;
  - `quota_before` from the read and `quota_after` from `codex.token_count`;
  - `ignored_env`.
- **`failure_reason(events, rc, stderr)`.** An ordered table of `(pattern, cause, remedy, untested)` rows is checked first:
  - the refresh messages and the restriction logout, which name the Codex harness login remedy through `login_remedy(message, LoginSource.HARNESS, CODEX)`, closed by the Codex login note (the X8 caveat until X8 passes);
  - "Not logged in";
  - usage-limit text (UNVERIFIED wording; the session record's `rate_limit_reached_type` is the primary signal).

  After that come `turn.failed` or `error`, a non-zero exit with the stderr tail, and finally the absence of `turn.completed`: "codex emitted no completed turn". A timeout is a runner failure that names the limit. A failed or timed-out run whose captured session record shows an explicit signal (rows 1 and 3–6 below) or a broken isolation is untested instead, naming both (`_untested_failure`, `timeout_problem`; review of 2026-10-06); row 2 alone leaves it a runner failure.
- **`billing_problem(events, effort)`** walks the reduced records in the order of the spec's after-run list:
  1. a provider other than `openai`;
  2. plan use unconfirmed: no `codex.token_count`, no `rate_limits`, no credits block, or no `plan_type`;
  3. a `plan_type` outside `ALLOWED_PLANS`;
  4. credits drawn: `has_credits`, `unlimited`, or a positive balance, with emptying the balance as the one remedy;
  5. a reached limit;
  6. a reroute.

  An isolation check follows it: `codex.skills` outside `<ws>/.agents/skills`, any `codex.tool` in the `skills` namespace, any `mcp__` call. The table form keeps every function at complexity 12 or below.
- **Three kinds of untested.** The exit-status contract names three reasons, and the reason text the summary already carries for an untested run names the condition:
  - `subscription`: a login or billing refusal (preflight login rows, `quota_problem`, `billing_problem`, `failure_reason`'s login rows);
  - `isolation`: a foreign skill, a cloud-skill tool or an MCP call;
  - `precondition`: `RunLockBusy`, a CLI below `CODEX_MIN_VERSION`, `features_problem`, or an effort the host did not serve.

  All three exit with the untested status. None is a runner failure.

### 13. The judge's isolation belongs to the judge (D3(a))

- **The backend.** `JudgeBackend` for Claude carries `isolation = lambda stack: enter_isolation(stack, "devjudge-config-")`.
- **`completed_run`.** When the run's host is the judge's host and the run was isolated, it reuses `config` (today's path). Otherwise it calls `judge.backend.isolation(stack)`. `--rejudge` already does this (`claude_runner.py:1189`). It runs after `run_codex` has returned, so the Codex lock is released and the Codex child has exited.
- **`resolve_judge`.** The `--isolated` requirement applies on the Claude host only. A Codex run's judge never needs it.
- **The L0 pin.** It combines a fake `codex_cli.run_codex`, a stubbed Claude harness-login preflight and a recording fake `claude_cli.judge_all`. The configuration the judge receives must be a Claude isolated configuration whose credentials link resolves into the Claude harness home. Neither its path nor the judge's environment may contain the Codex home.
- **`self_graded`.** It stays `served == judge.model`, which is always false on Codex.

### 14. Synthetic streams: `tests/unit/data/codex_streams/`

- **Content.** Each file is a saved event list: exec events plus reduced `codex.*` records. A few raw `rollout-*.jsonl` and app-server answer files exist to test reduction and parsing.
- **The README.** It gives one table row per file, with its provenance ("synthetic, from `codex-rs/exec/src/exec_events.rs` @ rust-v0.160.0", and so on) and what it pins.
- **Model names** are synthetic (`gpt-fixture-a`, `gpt-fixture-b`), which the model-ID guard's `gpt-\d` head does not match, so no allowlist entry is needed. This follows the `claude-fixture-…` precedent in `claude_cli_streams/README.md`.
- **The fakes.**
  - A fake `codex` is a Python script written under `tmp_path` and named by an injectable binary path. It emits a fixture stream, writes a session record into `CODEX_HOME/sessions/…`, optionally traps SIGINT, and reports whether it saw the lock descriptor.
  - A fake app-server speaks the JSONL handshake.

  No test can run the real `codex`.
- **The replacement.** `record-codex-streams` swaps in reduced recordings after the first approved Plus run, as `recorded-result.jsonl` was for Claude.

### 15. Live checks and USER ACTIONS (D6(b))

| Check | Who / how | Model call | Settles |
|---|---|---|---|
| CLI ≥ 0.160 | **USER ACTION** `sudo pacman -S openai-codex`; agent `codex --version` | no | precondition |
| X7 | agent: empty scratch `CODEX_HOME` at `${XDG_CACHE_HOME:-~/.cache}/thesis-proposal-dev/x7-probe`, holding only `PINNED_CONFIG_TOML`, no credentials, `unshare -rn` (no network); `codex features list` with the run flags; then once with an unknown nested key added under `--strict-config`; the directory is removed afterwards | impossible: no login, no network | key names, nested-key strictness, `DISABLED_FEATURES` |
| X1 | **USER ACTION** `uv run poe host-login codex` with the free ChatGPT account; agent `uv run poe host-status codex` | no | login into a fresh home. The home then holds a free-plan login, and every run refuses on the plan rule (Decision 9) |
| X8 | **USER ACTION**: with a ChatGPT session open in the desktop app or on the web, `uv run poe host-logout codex`, then `uv run poe host-login codex`; observe the other session | no | revoke scope; a pass flips `X8_PASSED` |
| X4b | agent `uv run poe host-status codex --quota` (GET `wham/usage`) | no | app-server handshake, the answer's fields, whether a credits block is sent. On the free plan the status exits 3 by design, because the plan rule refuses |
| after Plus | **USER ACTION**: credit balance 0, auto-reload off (optionally "Improve the model" off); `uv run poe host-login codex --reset` | no | the plan claim reads `plus`, and the credits block is present (else the change is revised first) |
| first live run | gated on the user's explicit go: `uv run poe dev check_report --host codex --model <slug the user names> --keep` | yes, plan quota | X4, X9 (feeds `record-codex-streams`) |

- **Where X7's scratch home lives.** Codex refuses to place its helper binaries under the system temporary directory, and this session's scratchpad and its parent both lie under `/tmp`. X7 therefore uses a cache path outside `$TMPDIR` and outside the repository, and checks both against `tempfile.gettempdir()` and the repository root before it runs, so a failure cannot come from the location.
- **If X7 shows that `--strict-config` misses nested keys,** the key-by-key comparison in `check_codex_home` is already the backstop, and nothing changes.
- **If X4b shows the handshake cannot work,** D2(a) makes Codex unusable. Reopening D2 is then the user's decision, through `openspec-update-change`.
- **If the Plus read in task 7.2 carries no credits block,** every run refuses as an unavailable read. Relaxing that is likewise the user's decision through `openspec-update-change`, made with the X4b and 7.2 answers in hand.

### 16. The workspace after the run (parity with `add-copilot-dev-runner`; the user's decision D-d, 2026-10-06)

Codex's sandbox (`--sandbox workspace-write`, Decision 6) lets the model's shell write the workspace, and making a link never touches its target. So a run can leave, in the workspace, a link (to `~/.ssh/id_ed25519`, to the harness's own files), a FIFO, a socket, a device, a hard link to a file elsewhere, or the workspace itself replaced by a link or another directory. The harness is not sandboxed, and after the run it reads the workspace (`read`, `workspace_markdown`, `l2_artifact` and `judge_criteria` for the verdicts and the judge's prompt) and writes into it (`save_events`). `add-copilot-dev-runner` measured the same pattern on Copilot (its Decision 13, "the workspace after the run") and closed it; this decision ports that check to Codex, as the user decided.

- **The shared code.** `harness/workspace_guard.py`, stdlib-only and imported by both hosts: `workspace_identity` (the directory's `(st_dev, st_ino)`, taken before any Codex child starts in it), `unsafe_entry`, `workspace_entries` (a walk with `os.walk(followlinks=False)` and `os.lstat`), `unsafe_entries`, `replaced` and `breach(ws, identity)`. `copilot_cli` keeps its names (`workspace_breach` wraps `breach` with the token scrub).
- **When.** `codex_cli._exec` checks the workspace right after the Codex child has exited, on a time limit too, and before `_closing` captures the session record, before `save_events` and before any verdict reads a file. A breach goes into the runner's own record (`codex.harness`, `workspace_breach`).
- **What it does.** A workspace that is no longer the directory the run started in (a link in its place is unlinked, never followed) is a breach, and nothing in it is read. Otherwise every link, FIFO, socket or device, and every regular file with `st_nlink > 1`, is a breach and is unlinked without being followed: the link goes, its target stays untouched. The message names at most five entries and reads none.
- **Fail closed** (revised 2026-10-07, review of task 5.5). `os.walk` drops a directory it cannot list, and the `lstat` errors were suppressed, so a run that left the workspace, or a directory in it, at mode 0300 (write and search, no read) hid every link in it, `breach` returned None, and the harness then opened a fixed name there (`read(ws / scenario["proposal"])`, `l2_artifact`) through the link (measured on the shared module with a harmless target). Now the workspace and every directory found must still be owner-`rwx`, and a listing error (`os.walk`'s `onerror`) or an entry whose `lstat` fails counts as well: each is a breach, named and never chmodded or reopened, so the run is untested for isolation with an isolation stop and no fixed name is read. Copilot shares the change (`add-copilot-dev-runner` Decision 13, the workspace after the run).
- **A reset keeps the stop** (revised 2026-10-07, review of task 5.5). `host-login codex --reset` wipes the home, and `stop.json` with it, so a reset silently cleared a recorded isolation stop, and Codex, which has no approval stop, could then run at once. The reset now reads the stop before the wipe and records it again, cause and time unchanged, in the reseeded home; the clear option stays its one remedy. *Chosen over* stating that a reset clears it, as Copilot's does: Copilot's reset records an approval stop in its place, Codex's would leave nothing.
- **The outcome.** `run_problem` and `timeout_problem` put the breach first: the run is untested for isolation (`planted_problem`), and no verdict reads its files. The event file is already created afresh, never through a link (`claude_runner.save_events`, every host).
- **The isolation stop (new on Codex).** A breach records an isolation stop in the Codex home (`stop.json`, `{kind, cause, at}`; a second cause is appended), at the moment the check finds it. While it is recorded, every later Codex run is refused as untested for isolation before any Codex process starts: the stop is read right after the location check, before `codex --version`, and again under the run lock, since another run may have recorded one while this one waited. A stop file that cannot be read, is not a JSON object, or whose `stop` is not a non-empty object, reads as a recorded stop. Its one remedy: read the run's findings, then `uv run poe host-login codex --clear-stop`, which carries the login's terminal and agent-marker refusals, takes the run lock, removes the stop and changes nothing else. `host-status codex` prints the `stop` line and is not refused by it. *Chosen over* a stop in `quota.json`, which `capture_rollout` replaces with every snapshot; `stop.json` is not on the Codex home's forbidden list, so the clean check accepts it.
- **What stays different from Copilot.** Codex has no live watch (its child runs to completion under `run_host`), no token to scrub, and no billing or approval stop: the isolation stop is the one kind. The first Codex model call after a login still waits for the user's go in chat, as before.

## Risks / Trade-offs

- **[The synthetic streams diverge from what 0.160 emits.]** → They are derived field by field from the tagged source and labelled synthetic. Live runs refuse until a login exists. X7 and X4b check the non-model parts first, and `record-codex-streams` replaces the fixtures.
- **[A pinned config key is misspelled for 0.160.]** → `--strict-config` fails the run visibly, and X7 finds it before any login.
- **[The app-server handshake fails on the real CLI, and D2(a) makes Codex unusable.]** → X4b on the free plan finds this before Plus is bought. The fallback is the user's choice.
- **[The sandboxed shell plants a link, a FIFO or a hard link in the workspace, or replaces it]** (making a link never touches its target, so the sandbox lets it through) → `workspace_breach` checks the workspace right after the child, before anything there is read or written, unlinks each such entry unfollowed, makes the run untested for isolation and records an isolation stop that holds every later Codex run until the operator clears it (Decision 16, D-d). A process the run left running could still change the workspace between the check and the reads, as on Copilot; Codex's child runs to completion and its process group is not killed, so that residual is wider here.
- **[The model under test reads `<home>/auth.json`]**, because the sandbox does not confine reads (brief §2.8). → Prompts are synthetic, and there are no outward features and no MCP server. The grant is separate, so `host-logout codex` contains a leak without touching the operator's logins. Claude has the same posture.
- **[Re-login revokes more than the harness grant (X8 negative).]** → Every message whose remedy is `host-login codex` or `--reset` carries the X8 caveat instead of the not-affected claim until X8 passes, pinned by an L0 test over both values of `X8_PASSED`. The rehearsal on the free plan exposes it at $0.
- **[The client sends no credits block on Plus, so every run refuses as an unavailable read.]** → That is the fail-closed choice of D2(a). X4b shows the free-plan answer and task 7.2 the Plus answer before any model call. Relaxing the rule is a reviewed `openspec-update-change`.
- **[The free-plan rehearsal leaves a working ChatGPT login in the harness home.]** → The plan rule refuses every run whose read reports a plan other than Plus or Pro, before any `exec`, and the session record's plan type is checked again after a run.
- **[A future CLI adds a default-on feature or renames one.]** → The features preflight refuses, and `--disable` rejects unknown names. Either way the run fails loudly, and the pin is updated by a reviewed change.
- **[The skill-read heuristic misses a read done another way]** (`python`, `rg`). → No dev-runner verdict depends on the `Skill` call. Recorded streams will show how often this happens.
- **[The Codex child keeps running after the harness dies on macOS]**, where there is no parent-death signal. → The child still holds the lock, so nothing interleaves. The Codex runner is verified on Linux only, as the README states.
- **[Plus quota is small.]** → Runs are serial, stop at 90 %, and have no Codex smoke. The summary reports quota before and after, so the cost of each scenario becomes visible.
- **[Plus traffic may be used for training.]** → Fixtures are synthetic, and workspaces are temporary directories outside the repository. The private proposals directory can never be a Codex workspace.
- **[The EU Terms of Use extraction clause]** is read as not covering the official `codex exec`. → That reading is an interpretation. Only the official client is used, never in CI, and the token never leaves Codex.
- **[Changing `--model`'s default to `None`]** could affect callers. → It resolves to `haiku` for Claude in `main()`. The test `ARGS` sets the model explicitly, and `poe smoke` passes its model.
- **[Change 1 or 2 is revised after this proposal.]** → Tasks 0.1 and 8.2 rebase the three shared blocks and recheck the Claude scoping of the two isolation requirements. The validator's scenario-name check catches dropped names.

## Migration Plan

1. **Start: change 1 archived, change 2 implemented with its spec text final.** Change 1 is necessarily archived by then: change 2's own precondition requires change 1 to be implemented and archived before change 2's code is written. Change 1's text is therefore read from the archived main spec, never from its change folder. This change's tasks assume `HostLogin`, `allowlisted_env`, `login_env`, `login_note`, `TERM_GRACE_S`, `stop_child`, change 1's `routing.follow_stream` and the `host-*` tasks in the code. `run_host` is not among them: this change adds it (Decision 7). Only change 2's archive may still be pending. It waits for its live check L1, which needs more than 8 h of idle time after its login, and blocking this change's L0 work on that would contradict the brief's phasing (P1, "now", L0 only).
2. Land code, tests, fixtures and docs as one commit after `poe test`, `poe cov` and `poe specs` are green. No model call is involved.
3. USER ACTIONS: CLI update, then the D6(b) rehearsal (X1, X8). The agent runs X7 and X4b, which make no model call.
4. **Archive: after changes 1 and 2 are archived**, and once sections 1 to 6 of the tasks are done. "Harness-owned host logins" exists in the main spec only after change 2's archive, so this change's MODIFIED block for it cannot be archived earlier (`openspec validate` reports that today as an INFO line). Task 8.2 reruns the rebase check and the validator then. Live runs after Plus are a gated section. If Plus has not been bought by then, its tasks are marked deferred and carried into `record-codex-streams`.

**Dependency stated.** This change's implementation depends on change 1's archive and change 2's implementation, and its archive on change 2's archive, which depends on change 2's L1. Only this change's archive waits on L1; no task before it does.

**Rollback** is a revert, after the USER ACTION `uv run poe host-logout codex`, so that the harness grant is revoked rather than orphaned. Claude runs are unaffected either way.

## Open Questions

- **The session-record path pattern** at 0.160, and whether the thread id appears in the file name. The `session_meta.payload.id` fallback covers either case.
- **Whether 0.160 still loads `$CODEX_HOME/.env` at start-up** (`arg0.rs:248-268` @0.133). It stays forbidden either way.
- **The usage-limit error wording.** The session record's `rate_limit_reached_type` is the primary signal. X4 records the text.
- **Whether the app-server answer and the exec session record carry a credits block on Free and on Plus** (X4b, task 7.2, X4). Its absence refuses today, before and after a run. If Plus never sends it, relaxing that rule is the user's decision through `openspec-update-change`.
- **The complete set of Codex agent-session markers**, which change 2 hands to this change. `AGENT_MARKERS` keeps change 2's `CODEX_SANDBOX` and `CODEX_SANDBOX_NETWORK_DISABLED`. No live check here can observe an unsandboxed Codex shell's exports without running Codex as an agent, which is a model call. The guard does not depend on the set: the `AGENTS.md` rule is the guard.
- **Whether `ALLOWED_PLANS` names every plan the operator might use.** It holds `plus` and `pro`. A Business or Edu seat may draw on workspace credits, so adding one is a reviewed change.
- **The exact `codex features list` output format at 0.160.** The parser is pinned on a fixture shaped from 0.133's local output, and X7 confirms it.
- **Whether `codex exec` exits promptly on SIGINT** while a tool call runs. The grace bounds the worst case.
- **X3**, the refresh lifetime and family revocation, and **X5**, credit draw at the limit. Both are observed over weeks and never provoked.
- **Whether a free-plan token's plan claim updates by itself after the purchase.** Running `--reset` after Plus makes the answer irrelevant for the login itself. If the claim updates before task 7.1 has confirmed the account settings, the plan rule stops refusing, because it reads the plan from each quota read. What still refuses then is the credits rule: any balance, `has_credits`, `unlimited`, or no credits block. The first model call also stays gated on the user's explicit go in task 7.3, which comes after 7.1 and 7.2.
