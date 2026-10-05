# Proposal

## Why

Every isolated Claude run links the operator's own stored login (`~/.claude/.credentials.json`, or `$CLAUDE_REAL_CONFIG_DIR`) into its temporary configuration. When the host refreshes there, the harness writes the result back into that file (`host_login.keep_login`). The harness and the operator therefore share one rotating refresh token, which leaves three faults:

- **The operator's login is at risk.** An interactive `claude` and an isolated run can refresh the same login at the same moment (R1). A hard kill between the host's rename and the write-back strands the token (R4). Either one logs the operator out of their own CLI.
- **The file goes stale while idle.** The desktop app never refreshes it (R6), so after every idle period the first isolated run is the one that refreshes.
- **The harness writes the operator's credentials file.** That is the closest the harness comes to the "store or intermediate" line in the terms (R5).

The judge builds its environment from a second allowlist, `claude_cli.ENV_KEEP`. It has drifted from the rig's `ADMITTED_ENV`: it lacks the proxy, certificate-trust, `SHELL` and `LANGUAGE` variables. When a judge call reaches its time limit, the harness also kills the host outright, without a termination request. The rig and the dev runner wait 5 s after their request (change 1's `follow_stream`), with no shared grace.

Money is kept out by the account setting, and the checks after each run are the backstop. Two runners do not stop after a billing signal. The routing rig checks no billing at all, so a sweep with extra usage on would bill overage on every case without a signal. `poe smoke` runs its next scenario after one that was untested for overage. The brief requires detection to stop the remaining runs of the invocation.

This is step A of decision D1(b), confirmed by the user on 2026-10-05. It lands after `close-claudeai-surfaces`, which keeps the claude.ai account's synced skills, plugins and connectors out of any configuration linked to that account. A harness login of the same account needs those opt-outs too. It is built only if change 1's live check L7 showed that they hold. If L7 failed, D1 falls back to (c), token mode, and this change is revised to that first.

## What Changes

- **A harness-owned Claude login home.** It lives at `${XDG_STATE_HOME:-~/.local/state}/thesis-proposal-dev/hosts/claude`, with macOS and Windows equivalents.
  - It has mode 0700, is outside the repository, and carries a `.harness-home` marker.
  - Before its first login it is seeded with change 1's pinned opt-out settings and an empty profile directory.
  - A `THESIS_PROPOSAL_DEV_STATE` override exists for tests. It is refused when it equals or contains `$HOME`, when it overlaps `~/.claude`, `$CLAUDE_CONFIG_DIR`, `~/.codex` or `$CODEX_HOME`, or when it lies inside the repository.
  - Its description is a per-host `HostLogin` record in `harness/host_login.py`. Only Claude's record exists; the Codex record is added by the later change `add-codex-dev-runner`.
- **Three commands.** They run through `host_login.main(argv)`:
  - `uv run poe host-login claude [--reset]` is run by the user only. It is interactive and runs `claude auth login --claudeai` in the home. It refuses without a terminal, and inside an agent session (`CLAUDECODE`, `CLAUDE_CODE_ENTRYPOINT`, `CLAUDE_CODE_SESSION_ID`, the Codex shell's markers). Both refusals are speed bumps. The `AGENTS.md` rule, which covers terminal tools, is the guard.
  - `uv run poe host-status` makes no model call and prints no account details. Agents may run it. It prints the home, its marker, the login state, the auth method and provider, the directory match, cleanliness, the access token's remaining time, and which login runs use.
  - `uv run poe host-logout claude` runs the client's own logout, in the home only.
  - `--reset` logs out, wipes the home (only a home that carries the marker), and logs in again.
  - Every logout runs in the login environment, so no inherited token, API key or profile directory can steer it at another login.
  - Until live check L3 has passed, every logout says that whether it logs out the operator's other Claude sessions is unverified.
- **A preflight that fails closed, with one remedy each.** Every isolated configuration that would link the harness login checks first that the home is in place, clean, logged in with the subscription, in the right directory and through Anthropic's own API. Otherwise the run is refused as untested.
  - The message uses one template: `untested: <cause>. <one remedy>. <login note>.`
  - The login note is "Your own Claude login is not affected". While L3 is unverified, a remedy naming `host-login` closes instead with "Whether this logs out your other Claude sessions is unverified (L3)".
  - It never falls back to the operator's login.
- **The link moves to the harness home.**
  - `routing.prepare_config` links the harness home's credentials. `keep_login` writes back only to the link's target, and the refresh claim now lives in the home.
  - `CLAUDE_REAL_CONFIG_DIR` becomes an explicit opt-in that links the named directory. It is labelled, never a fallback, and kept until live check L1 passes.
  - **BREAKING (dev-side):** `ROUTING_CONFIG_DIR` is removed. Setting it is refused, and the message names its replacement.
- **Login remedies follow the login that was used.** A login failure names `uv run poe host-login claude` for the harness login. It names `claude` → `/login` for an ambient run or the opt-in, and `claude setup-token` for a long-lived token. The run summary records which login a run used, and that login's directory, the one place a refresh is written back. An L0 test pins that this directory is the harness home under the default.
- **One environment builder.** `host_login.allowlisted_env` builds the environment of every Claude child that runs in an isolated configuration: rig cases, isolated dev runs, the judge and its preflight, and the harness login's status checks. It absorbs `routing.ADMITTED_ENV`, `routing.isolated_env`, `claude_cli.ENV_KEEP` and `claude_cli.child_env`, and applies change 1's connector switch and profile directory from `account_surfaces`. The Claude-only parts of the isolation requirements are scoped to Claude, so a client added later (Codex, change 3) is held to its own requirements and built by the same function from its own record.
- **Termination before kill.** One helper, `host_login.stop_child`, with a 10 s grace, replaces the 5 s sequence in change 1's `follow_stream`, which serves the rig and the dev runner. The judge's timeout now sends SIGTERM before SIGKILL, and so do the harness login's own client calls and the advisory audit pre-flight. This mitigates R4 only if the host finishes its credentials write on SIGTERM. Live probe L9 shows whether it even catches the signal, and the README keeps the R4 caveat on the opt-in either way.
- **The billing backstop stops the invocation.**
  - The routing rig applies the dev runner's billing checks to each case: an API-key source, overage, a refused or unknown rate-limit status, a report without its overage flag, a non-first-party provider, and no rate-limit report in a case that served a model turn. A routed case is read past its route and its tool results until the report arrives, the run ends, or the next turn's first assistant event arrives, since 2.1.284 writes the report after that turn's assistant events and, as recorded, after a `Read` or `Skill` call's tool result (for `Skill`, also after the skill's instructions; observed 2026-10-05) but before a `Glob` call's; why is inferred (design, Context). A case stopped for an account surface owes no report, before a model turn or after one; only a billing reason its stream shows voids the sweep.
  - A hit voids the sweep as change 1's surface voiding does: no further case starts, every case is an error, the report is unchanged, and the exit is 1.
  - `poe smoke` starts no later scenario after one untested for a billing reason.
- **Docs.**
  - `AGENTS.md` Commands lists the three tasks. Agents may run `host-status` and never run `host-login` or `host-logout`, through a terminal tool included.
  - `harness/README.md` gains a "Harness login" section and rewrites the link-hazard paragraphs.
- **Live checks** (tasks), in order:
  - the setup, then L3 at once and before any harness run: logout and re-login, after which the operator's own CLI and desktop app must still work;
  - L9, a no-model, no-credential SIGTERM probe;
  - one judged isolated dev run and one routing case on the harness login, both subscription runs;
  - L1, the first natural refresh after more than 8 hours idle, after which the operator's own CLI and desktop app must still work;
  - L2, the total login lifetime, as an observation.

  No check reads the modification time of the operator's own credentials file, which the operator's own CLI moves. The fallback order is token mode first and the `CLAUDE_REAL_CONFIG_DIR` opt-in last, with its R1 and R4 hazard.
- **Out of scope.** Step B (running directly in the harness home and deleting `keep_login`, the claim and `settle`) is the future change `run-isolated-in-harness-home`. That change also removes the `CLAUDE_REAL_CONFIG_DIR` opt-in. Codex is out of scope, and so are token-mode changes.

## Capabilities

### New Capabilities

None. The harness login is a new requirement in the existing `testing-harness` capability.

### Modified Capabilities

- `testing-harness`:
  - ADDED "Harness-owned host logins".
  - MODIFIED "Isolated measurement environment": link target, preflight, opt-in, override removal and remedy; the authentication and account-surface rules scoped to Claude; billing checks and sweep voiding in the rig.
  - MODIFIED "Isolated child environment": one builder, including the judge; scoped to Claude children.
  - MODIFIED "Subscription text roles (dev runner)": environment, preflight and remedy, termination before kill; smoke stops after a billing signal.
  - MODIFIED "Dev-runner cost and helper-agent telemetry": the login-failure remedy per login, and the login label with the login's directory.

  The first, second and fourth MODIFIED requirements are also modified by `close-claudeai-surfaces`. This change starts from that change's text as revised on 2026-10-05.

## Impact

- **Code.**
  - `harness/host_login.py`: records, location and guard, agent markers, login environment, home checks, preflight, remedies and the login note, `allowlisted_env`, `stop_child`, `main`.
  - `harness/routing.py`: `prepare_config`, `isolated_config`; `isolated_env` and `ADMITTED_ENV` removed; `follow_stream` stops through `stop_child`; the stream billing checks move here from `claude_cli`; `case_billing` and sweep voiding.
  - `harness/claude_runner.py`: `model_env`, summary `login` and `login_dir`, `billing` in the summary line, the smoke gate on `--summary-log`, remedies.
  - `harness/claude_cli.py`: `child_env` and `ENV_KEEP` removed; the billing checks imported from `routing`; `run_child` terminates before killing.
  - `harness/audit_llm_preflight.py`: its call terminates before it is killed.
  - `pyproject.toml`: the three poe tasks; the smoke comment.
- **Tests.** `tests/unit/test_host_login.py`, `test_host_login_cli.py`, `test_isolated_env.py`, `test_claude_cli.py`, `test_dev_runner_probe.py`, `test_install_probe.py`, `test_routing.py`, `test_audit_tooling.py` and `tests/conftest.py`. The fakes stay on `claude_runner.follow_stream`, where change 1 put them.
- **Docs.** `AGENTS.md` Commands, `harness/README.md`, module docstrings.
- **Precondition.** Change 1 is archived, and its recorded L7 passed (D1(b)). On a recorded failure (D1(c)), this change is revised to token mode before any code is written.
- **Operator setup, once.** In claude.ai, extra usage off; then **USER ACTION** `uv run poe host-login claude`. Until then, isolated runs, the rig, the judge, `poe smoke` and the install probe refuse with that remedy. An operator who exports `CLAUDE_CODE_OAUTH_TOKEN` is unaffected.
- **Platforms.** The step-A link needs a `.credentials.json`. That is Linux in practice, as today: macOS keeps the login in the Keychain, and Windows is unverified. macOS and Windows operators keep using token mode until step B.
- **Coexistence.** `desktop-first-install`'s install probe enters `isolated_config` and inherits the harness login unchanged. Change 1's `account_surfaces` constants are imported, not respelled.
