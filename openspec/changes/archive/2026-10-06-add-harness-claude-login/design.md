# Design

## Context

**Order.** This change lands after `close-claudeai-surfaces` (change 1) and builds on its code:

- `harness/account_surfaces.py` holds `CONNECTORS_OFF`, `PINNED_SETTINGS`, `PROFILE_DIR` and the surface checks;
- `prepare_config` writes the pinned settings and an empty `<config>/anthropic-empty/`;
- `isolated_config` refuses a configuration that fails `isolation_problem`;
- `routing.isolated_env` and `claude_cli.child_env` set the connector switch and the profile directory;
- `routing.follow_stream` reads a host's stream as it arrives, for the rig and the dev runner alike, and stops the host with terminate, a 5 s grace, then kill;
- `claude_cli.billing_signals` returns the explicit billing reasons a partial stream carries;
- `account_surfaces.profile_store_problem` (fallback F8, added by change 1's task 5.3 because L8 was inconclusive) refuses an isolated run while the default Anthropic profile directory holds an entry, unless a token is exported. This change keeps it unchanged and runs it beside the harness login's preflight; the spec delta carries its paragraph and scenario from change 1's archived text (rebased 2026-10-05, task 0.1).

**Gate.** Change 2 is step A of D1(b), and D1 falls back to (c), token mode, if L7 fails. Change 1 lands either way, and records its L7 and L8 outcomes and the D1 branch they imply in its tasks (5.1, 5.5, 5.6, 5.8, 5.9) and in `harness/README.md`. This change is built only on the step-A branch. If change 1 recorded D1(c), this change is first revised to token mode through `openspec-update-change`, before any of its code is written (task 0.1). Building step A on a login whose opt-outs are known not to hold would sync account content into the persistent home on the first login. A token, for its part, bypasses the harness login entirely.

Three of the four requirements modified here are also modified by change 1. Their MODIFIED blocks start from change 1's text as revised on 2026-10-05, not from today's main spec. That revision added the stop at the first surface, billing reasons beside a surface, and the audit pre-flight's ambient environment. "Subscription text roles (dev runner)" is untouched by change 1 and starts from today's text. If change 1 is revised again before it is archived, these blocks have to be rebased on its new text. See proposal.md (Why) for the motivation.

**State after change 1, before this change:**

| Concern | Where | Behaviour |
|---|---|---|
| Link source | `routing.prepare_config` | `$CLAUDE_REAL_CONFIG_DIR/.credentials.json`, default `~/.claude`; `ROUTING_CONFIG_DIR` replaces the whole directory (checked by change 1) |
| Write-back and claim | `host_login.keep_login`, `acquire_claim` | settles to the link's target; `.devrun-refresh.claim` beside it |
| Child environment | `routing.isolated_env` (`ADMITTED_ENV`), `claude_cli.child_env` (`ENV_KEEP` + `LC_`/`XDG_` prefixes) | two allowlists; the judge's lacks proxy, CA trust, `SHELL`, `LANGUAGE` |
| Login remedy | `host_login.login_remedy`, `RELOGIN` | always "`claude` → `/login`", whatever login the run used |
| Stopping a child | rig and dev runner `routing.follow_stream` / judge `run_child` | terminate, 5 s, kill / `process.kill()` with no termination request |
| Billing checks | dev runner and judge (`claude_cli.billing_problem`) / rig / `poe smoke` | after each run / none / each step untested on its own, and the next step still runs |

**Host facts this design relies on** (2.1.284; brief §2.1–2.6, dossier §B):

- **One claude.ai login per configuration directory.** The docs say so under "Log in with multiple accounts". On Linux the login is `<dir>/.credentials.json` (0600). On macOS it is a Keychain entry keyed to the directory.
- **`claude auth status --json`.** It reports `loggedIn`, `authMethod`, `apiProvider` and, from 2.1.268, `configDirectory`. It does not refresh tokens.
- **Login and logout.** `claude auth login --claudeai` is the subscription login (`--claudeai` is the default). `--console` is API billing. `claude auth logout` logs out the directory it runs in.
- **Unverified, and settled by live checks below.** Whether a second login of the same account leaves the first one working (L1). The login's total lifetime (L2). Whether logout revokes only its own grant (L3). Whether the host finishes a pending credentials write when it receives SIGTERM (L9).
- **Event order.** The rate-limit report's place changed between host versions. On 2.1.207 it arrived right after `system/init`, before the first assistant event (`logs/routing/events-litsearch-*.jsonl`, recorded 2026-08-10). On 2.1.284 it arrives after the first turn's assistant events, and its place relative to that turn's tool result varies with the tool: after a `Glob` call it came before the tool result (`events-write-polish-collision.jsonl`, 2026-10-05: three assistant events, the report, then the result); after a `Read` call it came after the tool result and before the next turn's first event (three dev-run streams, 2026-10-04, subscription); after the routing `Skill` call it came after the tool result and after a second `user` event, the skill's instructions the host adds to the conversation, and before the next turn's first assistant event (diagnostic run of task 5.7's case `review-canonical`, sonnet, 2026-10-05, read to its `result`: the report 5 ms after the tool result and 1.07 s before the next turn's first assistant event, which carried a new message id; committed reduced as `route-before-report.jsonl`). That run carried exactly one report across its four model responses and seven turns, none at a turn's end, and its `result` event carries no rate-limit field. Task 5.7's first attempt stopped at the `Skill` call's tool result, two events before the report (`skill-result-unreported.jsonl`). The reading consistent with all of these, inferred from the timing rather than proven: the host writes the report once, when the first response's stream ends, while a fast local tool may finish during the response, so its result can come first; the next turn's request starts only after the response has ended. A 2.1.284 case stopped at its route, at the routing turn's tool result or at the skill's instructions may therefore not have read it yet. *Corrected 2026-10-05 after review: the first draft attributed the 2.1.207 order to 2.1.284, which would have voided every 2.1.284 sweep (Decision 10). Corrected again 2026-10-05 after task 5.7: the second draft assumed the report always precedes the routing turn's tool result, which holds for `Glob` but not for `Skill`. The `Skill` order was then observed in full (task 2.11).*
- **A rejected login is an assistant event too.** The host records a failed API call, an expired login among them, as an assistant event of its own: model `<synthetic>`, `isApiErrorMessage` set, its text the failure (2.1.258 session transcripts). No model served it, and it carries no rate-limit report.

## Goals / Non-Goals

**Goals:**

- The harness never links, refreshes, writes or logs out the operator's own Claude login unless the operator opts in explicitly for that run.
- Every way the harness login can be unusable is detected before a run, without a model call, and named with exactly one remedy. No run falls back to the operator's login.
- No message claims that the operator's login is unaffected by a command whose effect on it is unverified.
- Exactly one function builds the environment of every child that runs in an isolated configuration.
- No host child the harness starts is SIGKILLed without a termination request first.
- A billing signal seen after one Claude run stops the rest of the invocation: the rest of a routing sweep, and the rest of `poe smoke`.
- Each check is a pure function over a directory listing, a parsed status object or an environment mapping, so it can be tested offline.

**Non-Goals:**

- **Step B: running directly in the harness home.** It would delete `keep_login`, `settle`, the claim and their tests, and it is gated on L1, L6 and L7. It is the future change `run-isolated-in-harness-home`, which also removes the `CLAUDE_REAL_CONFIG_DIR` opt-in once L1 has passed.
- **Codex.** Its `HostLogin` record, `.harness-run.lock`, quota read and the judge-isolation-per-backend seam for D3(a) belong to change 3, `add-codex-dev-runner`. This change only shapes `HostLogin` and `allowlisted_env` so that record fits without a signature change. It also scopes "Isolated child environment" and the authentication and account-surface rules of "Isolated measurement environment" to Claude, so that change 3 need not modify either (Decision 1).
- **The ambient default.** Plain `poe dev` stays ambient and `--isolated` stays opt-in (D5(b)).
- **Token mode.** `CLAUDE_CODE_OAUTH_TOKEN` still passes through and still means nothing is linked.
- **Moving the profile directory.** It stays per configuration (Decision 8).
- **A stream check on the dev judge.** Change 1 records it as an open question with no owner: the judge runs with `--safe-mode` and `--tools ""`, so a connector tool would need a permission the headless judge cannot be granted. This change does not take it up.

## Decisions

### 1. Spec shape

- **One ADDED requirement**, "Harness-owned host logins", owns the home, the commands, the preflight, the refusal template and the rule for stopping a child.
- **Four MODIFIED requirements.** The brief's §5 names three. The fourth, "Dev-runner cost and helper-agent telemetry", is added because it holds both the login-failure remedy ("`claude` → `/login`") and the run label. Leaving it unmodified would leave the spec contradicting the new remedy.
- **Claude scope.** "Isolated child environment" and the authentication, opt-out and account-surface rules of "Isolated measurement environment" now name Claude children and Claude configurations.
  - The reason: change 3 makes every Codex run isolated and gives its children a different environment (`CODEX_HOME`; no connector switch, profile directory or settings file). Unscoped, both requirements would demand Claude's variables and settings of a Codex child.
  - Both requirements are MODIFIED here anyway, and change 3's Decision 1 declines to modify them a third time. Each now says that a client added later is held to the requirements that add it, and that the same builder makes that client's environment from its own record.
- **The billing backstop goes where its runners are.** The rig's billing checks and the sweep voiding go into "Isolated measurement environment", next to the rig's surface voiding. The smoke stop goes into "Subscription text roles (dev runner)", which holds the smoke task (Decision 10).
- **New scenarios.**
  - In "Harness-owned host logins": "Login refused inside an agent session" and "Logout caveat until L3"; after review (2026-10-05) also "Relative override refused", "Unmarked directory never adopted", "Failed logout stops a re-login" and "Profile directory bars the login commands".
  - In "Isolated measurement environment": "Billing signal in a routing case" and "Unreported rate limit in a routing case"; after review also "Rate-limit report after the route".
  - In "Isolated child environment", after review: "Status check reports the home's own login".
  - In "Subscription text roles (dev runner)": "Smoke stops after a billing signal".
  - In "Dev-runner cost and helper-agent telemetry": "Write-back target labelled".
- **Scenario names are kept.** OpenSpec 1.7 refuses a MODIFIED block that drops a scenario name the main spec holds, and change 1's scenario names will be in the main spec by the time this change archives. So every name from today's spec and from change 1 is kept, and the bodies are rewritten:
  - "Judge child outside this requirement" now asserts the reverse.
  - "Prepared configuration without the opt-outs" now asserts the override's refusal.
  - "Time limit kills the child" now describes termination before the kill.

  Renaming them needs a requirement-level RENAMED or a later cleanup. It is not worth a second requirement churn here.

### 2. `HostLogin` records live in `harness/host_login.py`

`host_login.py` already owns "the stored login as an isolated configuration links it". It grows to own the harness login too:

- `HostLogin`, a frozen dataclass with these fields:
  - `name`, `binary`, `home_var`;
  - `login_argv`, `status_argv`, `logout_argv`;
  - `admitted` (names) and `admitted_prefixes`;
  - `login_strip_prefixes`;
  - `seed` (relative path → content; a trailing `/` makes a directory);
  - `forbidden` (relative paths and globs);
  - `failure` (the host's login-failure regex, today's `LOGIN_FAILURE`).
- One record, `CLAUDE`, with `login_argv = ("auth", "login", "--claudeai")`. `--claudeai` is passed explicitly, so that a changed host default can never turn the harness login into a console login.
- `RECORDS = {"claude": CLAUDE}`. Change 3 adds `"codex"`.

The module stays stdlib-only and imports `account_surfaces`. It does not import `routing` or `claude_cli`; both of those import it.

*Alternative:* a new `harness/host_homes.py` (dossier §Recommendation). Rejected because the brief's fate table (§2.9) keeps login handling in one module. The keeper, the claim and the harness home share the "linked login" concept, and step B deletes the keeper half in place. Complexity stays ≤ 12 through small helpers: one check per row of the fail-closed table.

### 3. Location, guard, marker, seeding

- **`state_root(environ, platform, home) -> Path`** is pure:
  - `THESIS_PROPOSAL_DEV_STATE` if set;
  - else on darwin `~/Library/Application Support/thesis-proposal-dev`;
  - else on win32 `%LOCALAPPDATA%\thesis-proposal-dev`;
  - else `${XDG_STATE_HOME}/thesis-proposal-dev` when `XDG_STATE_HOME` is absolute (a relative one is ignored, per the XDG spec), otherwise `~/.local/state/thesis-proposal-dev`.
- **`home(record) = state_root/hosts/<name>`.**
- **`check_location(root, environ, repo) -> LoginProblem | None`** applies the guard to every resolved root, not only to the override. It refuses:
  - a root that is not absolute: a relative override would resolve against whichever directory a command runs in (the home itself, for a login), and an isolated configuration's link to it would dangle;
  - a root that equals or contains `Path.home()`;
  - a root that equals, contains or lies inside `~/.claude`, `$CLAUDE_CONFIG_DIR`, `~/.codex` or `$CODEX_HOME`;
  - a root inside the repository.

  Containment is tested on resolved paths, so a symlink cannot route around it. The default root lies inside `$HOME` and passes, because only "equals or contains" is refused (critique 1's correction).
- **No temp-directory exclusion for Claude.** The brief's "outside `tempfile.gettempdir()`" exists because Codex refuses helper binaries under the temp directory. That rule arrives with the Codex record. Without it here, L0 tests can point the override at `tmp_path`.
- **Marker.** `.harness-home` holds one fixed line naming the repository and saying it is safe to delete with `--reset`. `wipe(home)` deletes only when the marker is present and `home` is not a symlink. Otherwise it refuses and names the directory.
- **Seeding** happens before the login. The home is created with mode 0700 and gets the marker, `settings.json` = `json.dumps(PINNED_SETTINGS)`, and an empty `anthropic-empty/`. The mode check is skipped on Windows, where POSIX bits do not apply.

### 4. Commands: `main(argv)` with three subcommands

Three poe tasks, so each one reads as a single command:

```toml
host-login  = "python harness/host_login.py login"    # uv run poe host-login claude [--reset]
host-status = "python harness/host_login.py status"   # uv run poe host-status [claude]
host-logout = "python harness/host_login.py logout"   # uv run poe host-logout claude
```

**`login <client> [--reset]`:**

1. **Two speed bumps.** Refuse unless `sys.stdin.isatty()`; the message says to run the command in a terminal. Then refuse when `agent_session_markers(os.environ)` finds any name from `AGENT_MARKERS`:
   - Claude Code's `CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT` and `CLAUDE_CODE_SESSION_ID`, all three exported into this repository's own agent sessions;
   - the Codex shell's `CODEX_SANDBOX` and `CODEX_SANDBOX_NETWORK_DISABLED`. Whether that set is complete is unverified (Open Questions); change 3 pins it with the Codex record.

   The message names the variables found, never their values, and says to run the command in a terminal outside any agent session. Neither check is a guard. An agent with a terminal tool, or one that wraps the call in `script -qc`, has a TTY, and a marker can be unset. The guard is the `AGENTS.md` rule, which says that terminal tools are covered by it (task 3.1). The two checks only make an accidental agent call fail before anything is created.
2. `check_location` and the F8 check (`profile_problem`, below), then create and seed the home if it is missing. A path that exists without the marker, or is a symbolic link, is refused with `wipe`'s remedy ("move it aside"), with or without `--reset`: the marker is what proves the harness made the home, so a login never adopts, reseeds or logs out a directory it did not make, and a later reset can never delete one.
3. On an existing home that holds a login — its `.credentials.json`, or, where the login is no file (the macOS Keychain), the host's own `auth status` — or on an existing home with `--reset`:
   - print the logout note, if a login is held: while `L3_PASSED` is False, "whether this logs out your other Claude sessions is unverified (L3)";
   - take the refresh claim;
   - run `claude auth logout` with the login environment, if a login is held. A non-zero exit stops the command here, naming the exit status: logging in over, or wiping, a login whose logout did not go through could orphan a live grant;
   - `wipe` (only with `--reset`), seed again, then release the claim.
4. Run `claude auth login --claudeai` with the login environment, inheriting the terminal.
5. Run `status` for that client, then exit 0 if ready, else 3.

**The login environment** is `login_env(record, home, environ)`, a pure function. Every login and every logout uses it: the standalone logout, the one before a login, and the one inside `--reset`. It is `environ`:

- minus `ANTHROPIC_*`, `CLAUDE_CODE_*`, `CLAUDECODE`, `CLAUDE_PID` and `CLAUDE_CONFIG_DIR`;
- plus `CLAUDE_CONFIG_DIR=<home>`, `CONNECTORS_OFF` and `ANTHROPIC_CONFIG_DIR=<home>/anthropic-empty`.

This is not the run allowlist, because the browser needs `DISPLAY`, `WAYLAND_DISPLAY`, `DBUS_SESSION_BUS_ADDRESS` and `BROWSER` (critique 2, last minor item). `CLAUDE_CODE_*` covers the billing switches, the long-lived token and the desktop session's auth-refresh and entrypoint variables; `CLAUDE_PID`, the desktop session's other binding variable, is named on its own. The logout needs no browser, but it gets the same environment for a different reason. With the operator's full environment, `claude auth logout` would see an exported `ANTHROPIC_*` variable, a long-lived token, and the default Anthropic profile directory, which ranks near `/login` (change 1, Context). Which login it would then act on is unspecified.

**The F8 check for the login commands.** Setting `ANTHROPIC_CONFIG_DIR` hides the default profile directory only if the host honours it exclusively, which L8 left unverified. So the login, every logout and the status check start no client while the default directory holds an entry (`host_login.profile_problem`, built on change 1's `profile_store_problem`). Token mode does not lift it here, since none of them carries the token; the one remedy is to move the profiles aside. Isolated runs apply change 1's check before `prepare_config`, so it also precedes the preflight's status check.

**`status [client]`** reads the home locally and runs `claude auth status --json` under `allowlisted_env(CLAUDE, home)` without the long-lived token, so it reports the home's own login even when a token is exported. It prints `key: value` lines:

- `home`;
- `marker` (yes/no);
- `logged_in`, `auth_method`, `api_provider`;
- `config_dir_matches` (yes/no);
- `clean` (yes, or the offending names);
- `access_expires` ("in 5h", "expired 2h ago"), from `expiresAt` only;
- `runs_use`: `harness`, `token (CLAUDE_CODE_OAUTH_TOKEN exported)` or `operator (CLAUDE_REAL_CONFIG_DIR)`.

These are exactly the items the spec's status list names; `marker` is one of them. The status JSON is parsed to exactly the four fields the checks read, and nothing else is ever printed. Exit codes: 0 ready, 3 not ready (with the refusal text), 2 usage.

**`logout <client>`** prints the logout note while `L3_PASSED` is False, takes the claim, and runs `claude auth logout` with the login environment. The marker and settings are kept, so the next `login` needs no reseeding.

**Exit 3** matches the dev runner's untested status, so a script can treat "harness login not ready" like an untested run.

*Alternatives:*
- One `host` task with subcommands (`poe host login claude`): rejected. The brief and `AGENTS.md` text name `host-login` and `host-status`, and a separate task makes "agents may run host-status" a rule about one task name.
- `host-login` that refuses on an existing login and points at `--reset`: rejected. Then the remedy for "login died mid-run" would differ from "not logged in". Logging out first keeps the remedy one command, and, because a failed logout stops the command, does not orphan a grant.

### 5. Preflight and refusals are data

- **`LoginProblem(cause: str, remedy: str)`** is a frozen dataclass. Findings are dataclasses (`AGENTS.md`).
- **The pure checks** are `check_location`, `check_presence(home)` (the home exists, carries the marker, and has mode 0700), `check_home(record, home)` (clean) and `check_status(status, home)`. Each returns the first problem or None, in the order of the list in the ADDED requirement. A missing home, marker or mode names `uv run poe host-login claude`, and a dirty home names the entry or `--reset`.
- **`read_status(record, home)`** spawns the status command. Tests monkeypatch it.
- **`preflight(record)`** returns the first problem.
- **`refusal(problem) -> str`** renders the one template: `untested: <cause>. <remedy>. <login note>.`
- **`login_note(remedy) -> str`** picks the closing sentence:
  - "Your own Claude login is not affected" by default;
  - while `L3_PASSED` is False and the remedy names `host-login`: "Whether this logs out your other Claude sessions is unverified (L3)".

  `login_remedy` (Decision 7) closes the harness-login remedy with the same note.
- **`L3_PASSED = False`** is a module constant. Task 5.4 flips it once L3 passes, and the L0 tests are parametrized over both values, so the flip needs no test edit.

*Why a caveat rather than the claim:* every re-login logs out first (Decision 4), and that logout is the named remedy for most refusals. Whether it revokes only the harness grant is L3, which is unverified until task 5.4. Change 3 treats the same risk for Codex with its X8 caveat.

`check_home` refuses on any of these:

- settings ≠ `PINNED_SETTINGS`;
- any entry under `skills/`, `agents/`, `commands/` or `output-styles/`;
- `CLAUDE.md`;
- a non-empty installed-plugins record.

Marketplace caches, `projects/`, `.claude.json` and other host state are allowed. The check uses a forbidden list rather than an allowed list, because the host creates state directories freely.

**Where it runs.** `prepare_config` runs the preflight when it is about to link the harness home, and only then: not with a token, not under the opt-in. A problem exits through `sys.exit(refusal(problem))`. That is the existing refusal path, which `enter_isolation` maps to untested and the rig to a diagnostic exit. It runs once per `isolated_config` entry, so once per sweep, dev run, install probe or `--rejudge` isolation. The cost is one `claude auth status` start, about a second.

*Why check cleanliness in step A, when runs never load the home's settings or skills.* A dirty home means the opt-outs failed under the same account. Change 1's per-run checks would then fail too, and step B depends on a clean home. Refusing early names the cause where it arose. *Alternative:* report it only through `host-status`. Rejected because the contract is fail-closed (brief §2.6), and the check is cheap.

**Missing `configDirectory`** is refused with its own remedy (update Claude Code). A field the host stops reporting must not read as "matches".

### 6. Link source: harness by default, opt-in explicit, override refused

`prepare_config(base)` decides in this order:

1. **`ROUTING_CONFIG_DIR` set:** refuse. The message says the override is no longer read and names `uv run poe host-login claude`. Change 1's checks on that override go away with it.
2. **`CLAUDE_CODE_OAUTH_TOKEN` set:** write the pinned settings and the profile directory, link nothing (unchanged).
3. **`CLAUDE_REAL_CONFIG_DIR` set:** the opt-in. Link `<dir>/.credentials.json`. Refuse if it is absent, with "`claude` → `/login`" for that directory.
4. **Otherwise:** run the preflight, then link `<harness home>/.credentials.json`.

`keep_login` is unchanged in mechanism. It writes back to the link's target, and the claim lives beside it, which is now inside the harness home. Under the opt-in it writes back to the opted-in directory. That is today's behaviour, and it is the reason the opt-in exists only until L1.

*Why refuse `ROUTING_CONFIG_DIR` rather than ignore it:* an ignored override lets an operator believe their prepared directory was measured. This mirrors the workspace-override rule in `AGENTS.md`: a setting that silently stopped applying is worse than one that fails.

*Why keep `CLAUDE_REAL_CONFIG_DIR` at all:* it is the last fallback, behind token mode. If L1 or L3 fails, meaning the harness grant breaks the operator's login, token mode keeps isolated runs working without a revert and links nothing. The opt-in serves an operator who cannot use token mode, and it brings back R1 and R4 for the login it names. Its meaning changes from "source, defaulting to `~/.claude`" to "explicit opt-in". An operator who exported it keeps today's behaviour, now labelled. The README states the R1 and R4 hazard beside it (task 3.2).

### 7. The login source decides the remedy and the label

- **`LoginSource`** is an enum: `AMBIENT`, `HARNESS`, `OPERATOR`, `TOKEN`.
- **`login_source(config, environ)`** is pure:
  - no config → `AMBIENT`;
  - otherwise the login `prepare_config` links for `environ` (`planned_source`): token exported → `TOKEN`; the opt-in set → `OPERATOR`; else `HARNESS`.

  It reads how the configuration was prepared, never the link's current state. The label is computed after the run, and during a refresh the host's own file stands where the link was until the keeper restores it; a link-based label would then read as the operator's opt-in. *Revised 2026-10-05 after review; the first draft classified any configuration without a link into the home as `OPERATOR`.*
- **`login_remedy(message, source)`** appends that source's one remedy when the message matches `CLAUDE.failure`:
  - `HARNESS` → `uv run poe host-login claude` and `login_note` (Decision 5);
  - `AMBIENT` and `OPERATOR` → `claude` → `/login`;
  - `TOKEN` → `claude setup-token`.

It replaces `RELOGIN` at every call site:

- `claude_runner.host_failure` gets the source from the run's configuration;
- the rig computes it once per sweep and passes it to `case_result`;
- `claude_cli.check_auth_status`, `parse_stream` and `call` get it through `judge_all`'s options.

The source is a required parameter everywhere, because a default would lie for one caller or another.

**Records.** The dev-run summary gains `login` and `login_dir` beside `config` and `config_dir`. The routing raw payload records both too. They are not a routing condition: change 1, Decision 6 already established that the link target does not change what the selector sees.

- **`login_dir`** is the directory of the link's resolved target, or null for `AMBIENT` and `TOKEN`. While the host's file stands in place of the link, it is the resolved directory of the login the configuration was prepared to link. `keep_login` writes a refresh only to `login_dir/.credentials.json`.
- **The install probe always isolates**, without `--isolated`. When its configuration cannot be prepared, its line is labelled with the login it would have linked, as an `--isolated` run's is.
- **An L0 test pins both halves.** Under the default, `login_dir` resolves inside the harness home. `keep_login`'s write-back target equals `login_dir/.credentials.json`.
- **Why a recorded target, not a timestamp.** The live checks need a way to show that a run never wrote the operator's login. The modification time of `~/.claude/.credentials.json` cannot show it: the operator's own CLI refreshes that file during the hours L1 spans, and the operator's own CLI check moves it too (R6). A changed mtime would then send the operator to a fallback for nothing. The recorded target names where the run could write, and the L0 test pins that this is the only place it writes. The operator's own observation that their CLI and desktop app still work is the real live check.

### 8. One builder: `host_login.allowlisted_env(record, config, environ=None)`

For `CLAUDE`, the builder produces:

- the admitted names: today's `ADMITTED_ENV`, moved, with its comment;
- `LC_*`;
- `CLAUDE_CONFIG_DIR = config`;
- `CONNECTORS_OFF`;
- `ANTHROPIC_CONFIG_DIR = config / PROFILE_DIR`.

It is applied to the rig, the isolated dev run, the judge's call and preflight, and the home's status check. It replaces `routing.ADMITTED_ENV`, `routing.isolated_env`, `claude_cli.ENV_KEEP`, `ENV_KEEP_PREFIXES` and `child_env`. All of those are deleted. Callers reach it as `host_login.allowlisted_env`, a module attribute, so one monkeypatch reaches every site. The wiring tests use that.

- **The judge's set changes.**
  - It gains proxy, CA trust, `SHELL` and `LANGUAGE`, which is the drift the brief names.
  - It loses `XDG_*` names beyond the seven base directories (for example `XDG_SESSION_TYPE` and `XDG_CURRENT_DESKTOP`). They describe the desktop session, not the machine. If a judge call ever needs one, the existing rule applies: admit that name, with its reason.
- **The judge's config becomes required.** The spec already requires isolation for judging, and the `config=None` path was only exercised by tests.
- **The record is a parameter** because change 3's Codex record is the builder's third user. Taking it now saves a signature change then.
- **`model_env`'s ambient branch is unchanged**: inherited, minus billing, plus `CONNECTORS_OFF`.
- **The profile directory stays inside the configuration**, so the home's own status check uses `<home>/anthropic-empty`. The brief placed it under the state root; change 1's Decision 3 already records that this change keeps it per configuration, for three reasons:
  - a per-configuration directory is created fresh at 0700 and cannot accumulate content;
  - the judge already shares the run's configuration;
  - a persistent shared directory would need its own emptiness check and a guard.

### 9. Termination before kill

Change 1 already moves the dev runner off `subprocess.run(timeout=…)`. Both the rig and the dev runner read their host through `routing.follow_stream`, which stops it with terminate, a 5 s grace, then kill, at a surface, a route or the deadline. What is left is one shared grace and the judge.

- **`TERM_GRACE_S = 10`.** This is judgment: the brief uses the same grace for Codex, and it bounds the worst case only.
- **`stop_child(proc)`** handles `Popen`. It sends `terminate()`, waits up to the grace, then calls `kill()` and waits again.
- **Call sites:**
  - `routing.follow_stream` replaces its terminate, 5 s, kill sequence with `stop_child`. That is the one place change 1 names for it, and it serves the rig, the dev runner and the install probe;
  - the judge's `run_child` (anyio) terminates, waits in a shielded `move_on_after(TERM_GRACE_S)`, then kills. Today it kills outright;
  - the harness login's own `auth status` and `auth logout` calls (`host_login.run_client`) at their time limit;
  - the advisory audit pre-flight (`harness/audit_llm_preflight.py`), which used `subprocess.run(timeout=…)`. It runs on the operator's own login, so a kill part-way through a refresh there would strand that login. *Added 2026-10-05 after review; task 2.5 had first left it as a follow-up.*
- **Windows:** `terminate()` is `TerminateProcess`, so the kill is the request.

*What this does and does not buy.* The risk is R4: a host stopped after receiving a rotated refresh token but before writing it strands the login it links. A termination request mitigates R4 only if the host finishes its credentials write when it receives SIGTERM, and then exits. A host that exits at once on SIGTERM, part-way through a refresh, loses the rotated token just as it would under SIGKILL. Whether Claude Code does either is unverified.

- **L9 probes it** without a model call or a credential (Decision 11, task 5.5). It starts the host in a scratch configuration with no login, waiting on standard input, and reads whether the process catches SIGTERM (the `SigCgt` mask in `/proc/<pid>/status`). It then sends SIGTERM and records the exit status and time.
  - A caught signal shows a handler. Whether that handler finishes a credentials write is still not shown, and nothing short of a forced refresh could show it, which the brief rules out.
  - An uncaught signal shows that termination before kill does not mitigate R4 for Claude.
- **Either way, the README keeps the R4 caveat on the `CLAUDE_REAL_CONFIG_DIR` opt-in**, which links the operator's own login (task 3.2). L9's outcome only sets the caveat's wording. On the harness login, a stranded token costs a `host-login`, not the operator's own login.
- `keep_login`'s exit settle picks up a write the host did finish.

*Test impact:* the fakes stay on `claude_runner.follow_stream`, where change 1 moved them. The new tests drive `stop_child` with real POSIX children and a recording fake `Popen`.

### 10. The billing backstop stops the invocation

Money is kept out by the account setting (extra usage off). The checks are the backstop, and for Claude they can only run after a run (brief §0, §1.3). The dev runner and the judge already check every stream (`billing_problem`), and an unavailable judge call stops further calls. Two runners did not stop after a billing signal.

**The routing rig.**

- **`case_billing(events) -> str | None`** is pure. It returns the first of:
  - `billing_signals(events)` (change 1): an API-key source, a non-first-party provider where the stream reports one, overage in use, or a refused or unknown rate-limit status;
  - "rate limit reported without an overage flag", when a report lacks `isUsingOverage`, as the dev runner's `_rate_problem` refuses: a renamed field must not pass in the rig where it refuses in the dev runner;
  - "rate limit not reported, overage cannot be ruled out", when the stream holds a model turn but no rate-limit report, and no account surface stopped the case (Precedence below). A model turn is an assistant event other than the host's own API-error message (`model_turns`: model `<synthetic>` or `isApiErrorMessage`, Context). Without that exception a login rejected mid-case would void the sweep as billing and lose its `host-login` remedy.
- **Reading past the route.** On 2.1.284 the report follows the routing turn's assistant events, and may follow its tool results too (Context), so a case stopped at the route, or at the routing turn's tool result, would hold no report and its sweep would be voided. The rig's stop condition (`_case_decided`) therefore accepts a route only at the first of: a rate-limit report read, the run's `result` event, or an assistant event of a later turn, one whose message id differs from the routing event's. The routing turn's `user` events (its tool result, and after a `Skill` call the skill's instructions) and a later block of the routing response (same message id) never end the read. The later-turn stop bounds the read at the next turn's first output, which the host starts only after the routing turn's response, and so its report, has ended; a host that writes no report by then voids the sweep visibly. `CASE_TIMEOUT_S` still bounds the case. On 2.1.207 the report was already read when the route arrived, so the stop is unchanged there.
  - *Recorded for a `Skill` route (2.1.284, 2026-10-05, Context).* The order was `init`, the `Skill` call, its tool result, the skill's instructions, the report, then the next turn. The rule stops at the report, the fifth event, 2.2 s into the run. Three alternatives were weighed against it. Stopping at the routing turn's first `user` event, the rule before task 2.10, comes two events before the report and voids every such case. Stopping only at `result` comes 23 events and 30 s later, after a whole skill run of seven turns, and gains nothing, since the run carried one report and its `result` none. Stopping at the next turn's first assistant event without a report is no false void in that run: no report arrived after that turn began. One run cannot show that a report is never missing, so a missing one keeps voiding the sweep visibly.
  - *Revised 2026-10-05 after review:* the first draft stopped at the route, on the false premise that 2.1.284 reports first. *Revised again 2026-10-05 after task 5.7 (task 2.10):* the second draft stopped at the routing turn's `user` (tool-result) event, which a `Skill` call's result reaches before the report. *Confirmed 2026-10-05 by the diagnostic run (task 2.11):* the stop was replayed over the recorded stream and stops at the report, and `case_billing` finds no reason there or over the whole stream.
- **Precedence.** A case stopped at `init` for a surface holds no model turn, so it is never reported for a missing rate-limit report. A case stopped for a surface after a model turn is not held to the report either: the surface cut its read short, and a surface errors only its own case, so `case_billing` returns only a billing reason the stream shows (an explicit signal, or a report without its overage flag) and the sweep is not voided for the missing report. On 2.1.284 the surfaces arrived only before the first assistant event, so this case is latent; reading past the route widens its window. *Added 2026-10-06 after review (task 2.12).* `case_result`'s precedence becomes surface > billing > route > host error > stream error.
- **Voiding.** The first case with a billing reason sets a stop flag. Cases not yet started then return without starting a host, as errors naming the billing reason. After the pool, `main` turns every result into an error naming that reason, exactly like change 1's surface voiding: raw results persist, the report is unchanged, and the exit is 1.
- **No import cycle.** `claude_cli` imports `routing`, so the pure stream checks behind `billing_problem` and `billing_signals` move into `routing`, beside `result_event` and `error_result_reason`. `claude_cli` already imports those two from there. `_source_problem`'s embedded `RELOGIN` goes with the other call sites (Decision 7). Behaviour is otherwise unchanged, and the existing L0 tests follow the move.

**`poe smoke`.** It is a poe `sequence` with `ignore_fail`, and a sequence cannot stop on one kind of failure. The gate therefore lives in the runner:

- The summary line gains `billing`: the billing reason when the run is untested for billing, else null.
- A run given `--summary-log` reads that log before it starts a host. If a line from an earlier step carries `billing`, it starts nothing. It records its own line as untested, "not run: <scenario> reported <reason>", and exits with the untested status.
- `--summarize` removes the log at the end of the sequence, so the gate spans one smoke invocation. A log left behind by a sequence that died before `--summarize` makes the next smoke refuse every step. That is fail-closed, and the message names the log and `--summarize` as the way to clear it.
- `pyproject.toml`'s smoke comment ("a failing step does not stop the others") gains the exception.

*Alternatives:*
- A distinct exit status for billing-untested, read by the sequence: rejected. Poe's `ignore_fail` cannot branch on it, and the spec fixes four outcomes.
- A Python smoke driver that calls `claude_runner.main` in-process: it would work, but it rewrites a task that works, for one condition.

### 11. Live checks: what settles each, and what follows

All of these run on the subscription, with no metered call, and in this order. L3 comes right after the setup and before any harness run, because it costs nothing and every later remedy may run the harness logout. Reports record only booleans, counts, enums, file mtimes inside the harness home, and names.

| Check | How | Pass | If it fails |
|---|---|---|---|
| Gate | task 0.1 reads change 1's record | L7 passed (D1(b)); L8 settled positive, or F8 implemented | L7 failed: revise this change to D1(c) through `openspec-update-change` before any code |
| Setup | **USER ACTION** `uv run poe host-login claude`, then the agent runs `uv run poe host-status` | `marker: yes`, `logged_in: yes`, `auth_method: claude.ai`, `api_provider: firstParty`, `config_dir_matches: yes`, `clean: yes` | `clean: no` naming `skills/synced` or `plugins/synced`: an L7 regression. Stop and report it; the rule is never relaxed for synced content. Any other entry: the host rewrote its own state, and the clean rule is adjusted for that entry through `openspec-update-change` |
| L3 | **USER ACTION** `uv run poe host-logout claude`, then **USER ACTION** `uv run poe host-login claude`; the agent reruns `host-status`; **USER ACTION**: one prompt in your own CLI, and the desktop app, still work without a new login | ready again, and both still work. Then `L3_PASSED` is flipped and the caveat gives way to the not-affected sentence | keep the caveat and go to the fallback (task 5.10) |
| L9 | agent: the SIGTERM probe of Decision 9, scratch configuration, no credentials | recorded as caught, uncaught or inconclusive | — (it sets the README's R4 wording) |
| Run on the harness login | one judged isolated dev run, then one routing case | `login: harness`, and `login_dir` equals the home `host-status` prints. The routing run is not voided for billing | fix, or take the fallback |
| L1 (gates removal of the opt-in, in step B) | the first isolated run after the home's access token has expired, more than 8 h after login | the run passes, its `login_dir` is the harness home, and the home's credentials mtime moves (write-back). **USER ACTION**: own CLI and desktop app keep working without a new login | the harness strategy is invalid for the same account: document it, take the fallback, and open a follow-up change |
| L2 | observation | — | recorded in `harness/README.md` when the login's end or an "expires in N days" warning appears |

**The fallback, in this order.** First, token mode: **USER ACTION** `claude setup-token`, then export `CLAUDE_CODE_OAUTH_TOKEN` in the shell that starts the harness. Last, only if token mode is not possible: the `CLAUDE_REAL_CONFIG_DIR=~/.claude` opt-in. It links the operator's own login again, so it brings back R1 (a concurrent refresh) and R4 (a stop mid-refresh), and the operator must accept both.

"Natural" refresh means no forced expiry. The brief replaced the forced-expiry probe with waiting, so that nothing ever edits a credentials file by hand.

*Why the operator's own credentials file has no mtime check.* The operator's own CLI refreshes `~/.claude/.credentials.json` during the hours L1 spans, and the operator's CLI check in L3 can move it too (R6). The check would fail when nothing is wrong, and its failure path would be the opt-in, which reintroduces the fault this change removes. The recorded `login_dir`, pinned by an L0 test as the only write-back target, takes its place (Decision 7).

## Risks / Trade-offs

- **[Change 1's L7 failed, but step A is built anyway.]** → The first `host-login` would sync account content into the persistent home, and every run would then refuse. Task 0.1 reads change 1's recorded L7 outcome and stops on a failure, and the change is revised to D1(c) first. Task 5.3 treats synced content in a fresh home as an L7 regression, never as a reason to relax the clean rule.
- **[A second login of the same account revokes the operator's grant (L1 negative).]** → The operator watches their own sessions right after login and after the first refresh. Token mode is the first fallback. The opt-in, `CLAUDE_REAL_CONFIG_DIR=~/.claude`, is the last, because it brings back R1 and R4.
- **[The harness logout revokes the operator's other sessions (L3 negative).]** → Every message about a command that logs out carries the unverified-L3 caveat instead of the not-affected claim until L3 passes. L3 runs before any harness run, at no cost.
- **[The host rewrites the home's `settings.json` at login, so every run refuses "home not clean".]** → The setup task's `host-status` shows it immediately. The fix is a reviewed spec adjustment for that entry, never a silent relaxation, and never for synced skills or plugins.
- **[Isolated runs, the rig, the judge and `poe smoke` refuse until the operator logs in.]** → The refusal names the one command, and token-mode operators are unaffected. The README's "Which path to use" table gains the one-time setup row.
- **[An agent tries `poe host-login`.]** → The `AGENTS.md` rule, which covers terminal tools, is the guard. The terminal check and the agent-marker check are speed bumps: they stop an accidental call before anything is created, but an agent with a terminal tool passes the first, and a marker can be unset.
- **[The operator's own terminal carries an agent marker]** (for example a terminal panel inside the desktop app). → `host-login` refuses there, and the message names the variable and says to use a terminal outside any agent session.
- **[Termination before kill does not save a refresh in progress.]** → L9 shows whether the host even catches SIGTERM. The harness login's loss is one `host-login`. The opt-in keeps its R4 caveat in the README.
- **[A billing signal in one routing case voids the whole sweep.]** → Intended: the account setting has then failed, and every later case would bill. Raw results persist for diagnosis.
- **[A stale smoke summary log blocks the next smoke.]** → Fail-closed. The message names the log and `--summarize` as the way to clear it.
- **[`--reset` deletes the wrong directory.]** → The location guard, the marker, and refusal of a symlinked home.
- **[The judge loses a desktop-session `XDG_*` variable it needed.]** → L0 wiring tests plus the live judged run. Admitting a name is a one-line, reasoned change.
- **[macOS and Windows operators cannot use step A]** (macOS keeps the login in the Keychain, not a `.credentials.json`; symlinks need a privilege on Windows, and whether Windows writes the file is unverified). → As today. A logged-in home without the file is refused with token mode as the remedy, and a re-login there asks the host's status whether the home holds a login before logging out. Token mode works there, and step B removes the link.
- **[The model under test can read the harness credentials]** (runs are unsandboxed; brief §2.8). → This is no worse than today, when it can read `~/.claude`'s. The grants are separate, so `host-logout` contains a leak without touching the operator's login.
- **[One more process start per isolated invocation.]** → About a second. It buys a refusal before any model token is spent.
- **[Change 1 is revised after this proposal.]** → The three shared MODIFIED blocks must be rebased on change 1's final text before this change validates against the archived spec. The validator's scenario-name check catches dropped names.

## Migration Plan

1. Change 1 is implemented and archived first, so its constants and checks exist, and its recorded L7 outcome selects D1(b). This change's tasks assume both.
2. Land the code, tests and docs as one commit after `poe test`, `poe cov` and `poe specs` are green.
3. The operator turns extra usage off (change 1's task 5.4) and runs `uv run poe host-login claude` (**USER ACTION**).
4. Live checks, as in Decision 11: L3 first, then L9, then the harness runs. L1 needs more than 8 h of idle time after the login. *Revised 2026-10-05 (user decision): archiving does not wait for L1 or L2. Both are recorded follow-up observations; L1 gates step B's removal of the opt-in, as the table in Decision 11 already says, not step A's landing (tasks 5.8, 6.1).*

**Rollback** is a revert. Run `uv run poe host-logout claude` first, so the harness grant is revoked rather than orphaned. The home then stays on disk with no login and is harmless. An operational fallback without a revert is token mode (`CLAUDE_CODE_OAUTH_TOKEN`), and last the `CLAUDE_REAL_CONFIG_DIR=~/.claude` opt-in, with its R1 and R4 hazard.

## Open Questions

- **L2, the login's total lifetime.** It is observed, not provoked. It only sets how often the operator reruns `host-login`.
- **Does Claude Code finish a pending credentials write on SIGTERM?** Termination before kill mitigates R4 only if it does. A host that exits at once on SIGTERM mid-refresh loses the rotated token just as under SIGKILL. L9 shows whether the host catches the signal at all; that a handler completes the write stays unobserved, because observing it would need a forced refresh. Until then the README keeps the R4 caveat on the opt-in.
- **The exact name and shape of the host's installed-plugins record** in a configuration directory. The implementation pins it against a synthetic fixture shaped like the 2.1.284 file; that it is empty in a fresh home is checked by the setup task.
- **Does `claude auth status` create `.claude.json` or other state in a fresh home?** Harmless either way, because neither is forbidden.
- **The complete set of Codex agent-session markers.** `CODEX_SANDBOX` and `CODEX_SANDBOX_NETWORK_DISABLED` are set only by Codex's sandboxed shell, and an unsandboxed Codex shell may export none. Change 3 pins the set with the Codex record. The guard does not depend on it.
- **Does the desktop app's own terminal panel export Claude Code's session markers?** If it does, `host-login` refuses there, and the operator runs it in a terminal emulator outside the app. The refusal says so.
- **Rate-limit report order in future hosts.** The report moved from before the first assistant event (2.1.207) to after the first turn's assistant events, before or after that turn's tool results (2.1.284). The rig reads a routed case to the report, the run's result, or the next turn's first assistant event, so each recorded order passes. A host that moves the report past the next turn's first output, or stops sending it, voids sweeps visibly, never silently passes them. That a `Skill` call's report lands after the skill's instructions and before the next turn was observed once, on 2026-10-05 (Context). Whether a normal subscription run can carry no report at all stays open, since one run cannot rule it out. If one ever does, the sweep is voided as designed.
- **Does the host emit `isApiErrorMessage` in stream-json, or only in its session transcripts?** The model check (`<synthetic>`) covers either; both are read.
- **The brief's temp-directory exclusion for homes** collides with L0 tests that use `tmp_path`. This is change 3's concern when it adds the Codex record.
