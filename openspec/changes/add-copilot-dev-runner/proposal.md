# Proposal

## Why

Students who install the skills into GitHub Copilot run them on a host the harness has never exercised. Copilot has its own skill tool, its own skill discovery, which climbs every parent folder of a workspace that is not a git repository, its own subagent tool, and its own billing in AI credits. The dev runner drives Claude and, after `add-codex-dev-runner`, Codex. The operator's account holds the free Copilot Pro plan for teachers, about 1,500 credits a month, so a Copilot dev runner adds a third $0 dev loop on a host students actually use.

There is no safe way to run `copilot -p` today:

- **The login.** A Copilot OAuth login sits in the OS keyring, keyed independently of `COPILOT_HOME`, with the scopes `repo` and `gist`. It can be revoked only together with the operator's own CLI logins.
- **The shell.** The model's shell can run `gh`, and `gh` reaches the operator's keyring token over D-Bus whatever the environment says.
- **The quota read.** The CLI's own quota call coerces missing billing fields to "no overage".
- **Discovery.** Skill discovery reads every parent folder.

The user's decisions of 2026-10-05 settle the shape:

- **D-C1, plan.** Teacher Pro: pinned models, no auto-only variant.
- **D-C2(a), credential.** A fine-grained PAT carrying only "Copilot Requests", kept in a 0600 file beside the harness home (never inside it) and handed to Copilot children alone. The chained login requirement gains a per-record credential kind.
- **D-C3(b), version.** The CLI is upgraded to 1.0.91, the runner pins that version exactly, and a local V-pass re-derives every 1.0.67 fact at the pin before any fixture is written.
- **D-C4(b), sandbox.** The OS sandbox is required, with a pinned deny list built by construction and a $0 confinement probe before every run. Network limits per scenario are a follow-up.

This change lands after `close-claudeai-surfaces`, `add-harness-claude-login` and `add-codex-dev-runner`, and builds on their `HostLogin` records, `allowlisted_env(record, …)`, `hosts.py` (`Host`, `RunView`), `run_lock`, the `read_quota` seam, `stop_child`, the refusal template, the exit statuses, judge isolation per backend, the `poe host-login`/`host-status`/`host-logout` tasks and `--host`.

## What Changes

- **A Copilot host behind the existing runner.**
  - `--host copilot` selects a `Host` whose skill directory is `.agents/skills`, the folder layout `install.py --scope folder` writes and that Copilot lists as project skills.
  - New module `harness/copilot_cli.py`. No second runner.
  - Dev loop only, labelled "dev-runner (copilot), not comparable to matrix". It never writes to `logs/evals`, has no registry role and no currency alert. `--model` is required and `auto` is refused. Install scenarios are refused, `--max-budget-usd` is refused, and `--max-ai-credits N` (N ≥ 30, a soft cap) is required.
- **A third `HostLogin` record with a new credential kind.**
  - `credential: "client-login" | "token-file"` and `token_env`; Claude and Codex keep `client-login`.
  - `uv run poe host-login copilot [--reset | --clear-stop]` is for the user only. It seeds the home, reads the PAT with `getpass`, refuses anything but a `github_pat_` prefix, writes `<state>/hosts/copilot.token` at 0600 beside the home, and records an approval stop. Clearing that stop from a terminal is the user's go, which the runner records: it covers one canary and, only once that canary passed, one skill run, whose start records the approval stop again (the user's decision D-c, enforced since 2026-10-07).
  - `host-logout copilot` deletes that file and says where to revoke the token.
  - `host-status copilot [--models] [--no-token]` makes no model call, and agents may run it.
  - The harness reads exactly one token file, hands its value only to Copilot children as `COPILOT_GITHUB_TOKEN`, inspects only its prefix, scrubs the value from everything a child produced before saving or forwarding it, and never prints or logs it. Every child gets `--no-auto-login`, and every child that carries the token names it with `--auth-token-env`, because at 1.0.91 `--no-auto-login` leaves an unnamed environment token unread (measured after the first login, task 7.4b).
- **Isolation.**
  - Seeding and environment:
    - a pinned `settings.json` with the sandbox block (`allowBypass:false`, `allowDevToolAccess:false`, `auth.git/gh:false`, and a deny list built by construction: the operator's whole real home, `/run/user/<uid>`, the shared `/tmp` and the harness's own temporary directory (added 2026-10-06, the user's decision D-b, after K6 measured the sandboxed shell reading and writing `/tmp`), the state root where it lies outside that home, the token file, and, since 2026-10-13 (the second canary, the user's decision D-e), on Linux the sandbox's own init process directory `/proc/1`, whose environment is the client's, and the Copilot children's process-log directory beside the home, which the client otherwise binds into the sandbox). The deny list's settings path is contradicted between the docs and the 1.0.67 package, so the V-pass derives it from the 1.0.91 package;
    - a home checked against an allow-list;
    - the workspace and every scratch directory in the Copilot work directory, never in the system temporary directory: under the state root where it lies outside the home, otherwise under `/run/user/<uid>` (D-b);
    - scratch `HOME` and XDG directories, `DBUS_SESSION_BUS_ADDRESS=disabled:`, an empty `GH_CONFIG_DIR`, `COPILOT_AUTO_UPDATE=false` and `--no-auto-update`.
  - Closed surfaces: the built-in GitHub MCP server, custom instructions, remote sessions and export, memory, `gh` and `git push` in the shell, and, since 2026-10-13 (the first skill run), the client's own file and search tools, which refuse the workspace under the deny list's denied ancestor; the model reads and writes files through the sandboxed shell.
  - Before the run:
    - a scan of the workspace and every parent folder;
    - `skill list` and `mcp list` roster checks, which make no model call;
    - a refusal on Windows, or when any tool the sandbox needs is missing, or, on Linux, when the kernel's Yama ptrace scope is missing or below 1 (read, never set; since 2026-10-13);
    - a confinement probe through the headless server's model-free shell call, which refuses the run when the sandboxed shell can reach the token file, the harness's process environment, `~/.ssh`, `~/.config/gh`, or `gh` or git authentication, or finds a token in any process environment or command line it can see (by content since 2026-10-13: the sandbox has its own pid namespace, and its init holds the client's environment). The headless server never puts a session it creates in the sandbox (K6, 2026-10-06), so the probe first checks that the client reads the pinned sandbox block from the home and applies it to its session as prompt mode does; only then do its commands run. It also refuses when the sandboxed shell reads a file in the host's `/tmp` or writes one there that the host sees (refusing since D-b), and records, without refusing, whether it shares the host's network namespace.
  - During the run, the child is stopped at its first shell call the client does not report as sandboxed, at a sandbox warning, or at a file tool pointed outside the workspace, so a run whose shell is not confined does not go on with the skill prompt; whatever ends a child, its process group is stopped with it. Prompt mode applies the sandbox itself, after resolving the block natively, so that its confinement can only be observed in the run; the probe's evidence covers the same block applied through the same call, unresolved.
  - After the run, before anything in the workspace is read, a link, FIFO, socket, device or hard link the sandboxed shell left there, or a replaced workspace, is removed unfollowed and marks the run untested with an isolation stop; so do a run stopped by the watch, a sandbox reported ignored or not active, the token's value in the child's output, and the token's value or any GitHub token in the probe's or the run's process log, which the harness scans and deletes (since 2026-10-13). A run is also untested when its loaded skills cannot be confirmed: the client's loaded-skills report never reaches a prompt-mode run, so the confirmation rests on the skill listing recorded before the child and on the session file's skill records, never on the report's absence (since 2026-10-13, the first skill run).
  - Everything above lives in the repository's code and the harness's own state directory: no system setting, package or file outside them changes, and the Linux-only parts apply on Linux only (the user's constraint, 2026-10-13).
- **A Copilot plan billing guard.**
  - The operator keeps a $0 budget on "All AI Credit SKUs" with "Stop usage" on, and never deletes it: GitHub's Budgets page states that a product with no budget has unlimited usage, and K2 measured `overage_permitted: true` with every budget deleted and `false` once the $0 Stop-usage budget was set (corrected 2026-10-06, the user's decision D-a).
  - Under the run lock, a headless RPC status read, with no model call, reads the raw `quota_snapshots` before and after each run, never the coerced `getQuota` values. Any possible or drawn overage (a missing overage field included), legacy billing, low quota, or an unavailable read refuses the run.
  - Consumption comes from the session's `totalNanoAiu`. Any of these marks the run untested:
    - a soft-cap stop;
    - overage growth, or a status read after the run that is unavailable;
    - consumption above twice the cap.

    A missing shutdown record leaves the consumption unreadable and is a runner failure instead. Each of these cases records a billing stop in the home, which refuses every later run until the user clears it with `host-login copilot --clear-stop`. `poe dev` runs one scenario per invocation, so "the remaining scenarios" are the later invocations. Isolation stops and the approval stop work the same way.
- **Readers.** The stdout JSON events plus the reduced session events file give the following, mapped to the canonical tool names: `final_text`, the served model and effort report, tokens, credits, and skill calls (the `skill` tool, confirmed by `skill.invoked`).
- **Judge.** The Claude sonnet-5.5 dev judge grades Copilot runs in its own isolation. The token never reaches it.
- **L0 coverage on synthetic streams and RPC replies** derived from the pinned 1.0.91 package, labelled synthetic until the follow-up `record-copilot-streams`.
- **USER ACTIONS** (agents never log in):
  - the CLI upgrade to 1.0.91;
  - a $0 budget with "Stop usage" on "All AI Credit SKUs" (not deleting budgets, which lifts the cap);
  - creating the PAT;
  - `host-login copilot`;
  - the `gh` check of K1.

  K1–K4, K6a and K6, the confinement probe, cost $0. The first live run, one `check_report` on a cheap model, spends credits. It runs only after every $0 check has passed and a canary (the probe's fixed commands in one script the harness writes, run by one fixed command that is the whole prompt, the shell alone, the minimum cap) has passed under the same go, and only once the user has cleared the approval stop from a terminal, after a go request that names the soft cap and every confinement item still unverified, the prompt-mode sandbox among them: that run is the first to observe it, and its live watch stops it at the first shell call not reported sandboxed.
- **Out of scope:**
  - `smoke-copilot`, because the credit cap is soft;
  - routing on Copilot;
  - the auto-only plan variant;
  - per-scenario sandbox network policy (D-C4(c));
  - a usage-file telemetry source.

## Capabilities

### New Capabilities

None. Copilot enters the existing `testing-harness` capability.

### Modified Capabilities

- `testing-harness`:
  - ADDED "Copilot plan billing guard": the environment and its pre-spawn assertion, the raw status read before and after each run, the required credit cap, consumption checks, the stops that persist across invocations (billing, isolation and approval), and the synthetic fixtures.
  - MODIFIED "Harness-owned host logins", starting from `add-codex-dev-runner`'s text. It gains the per-record credential kind and the token-file limits (scrubbing among them), plus the Copilot home, its deny list, commands, status items, preflight, run lock and login note. Its Claude credential-kind sentence now names the harness write-back.
  - MODIFIED "Dev-runner host adapters", starting from `add-codex-dev-runner`'s text. It gains the Copilot host, its model and effort rules, invocation, canonical tool calls, isolation scan, rosters, sandbox with its confinement probe, and scope. Change 3's "Invocation." and "Isolation." labels read "Invocation on Codex." and "Isolation on Codex.", wording only.
  - MODIFIED "Isolated child environment", starting from `add-harness-claude-login`'s text, which `add-codex-dev-runner` does not modify. A token-file client's credential is added after the builder, for that client's children only.
  - MODIFIED "Dev-runner cost and helper-agent telemetry", starting from `add-codex-dev-runner`'s text. It gains the Copilot stream, credits instead of cost, the outward surfaces, the soft cap, the token remedy, and the Copilot rows of the exit statuses.
  - Not modified: "Inverted-hybrid runners", "Measured environments carry no eval definitions", "Subscription text roles (dev runner)" and "Isolated measurement environment". `add-codex-dev-runner` words the first three for every host, and change 2 scopes the fourth to Claude configurations.

## Impact

- **Code.**
  - New: `harness/copilot_cli.py`.
  - `harness/host_login.py`: the `COPILOT` record, the `credential` and `token_env` fields, the token-file login, logout and status branches, `check_copilot_home`, and the status read.
  - `harness/claude_runner.py`: the host entry, the flags `--max-ai-credits` and `--preflight-only`, the usage guards and the untested mappings.
  - `harness/routing.py`: `tool_calls` adds the Copilot shape.
- **Tests.**
  - New: `tests/unit/test_copilot_cli.py` and `tests/unit/data/copilot_streams/` with its README.
  - Extended: `test_host_login.py`, `test_hosts.py`, `test_dev_runner_probe.py`, `test_routing.py` and `test_isolated_env.py`.
  - `tests/unit/conftest.py` gains an autouse fixture that points the Copilot binary seam at a sentinel that raises, and the state directory at `tmp_path`, so no test can start the real client.
- **Docs.** A "Copilot dev runner" section in `harness/README.md`, which carries the suggested per-model credit caps and the K-check status lines, plus the `AGENTS.md` Commands section.
- **No model calls** in this change's gates. Live Copilot runs refuse until a token file exists. The first run spends included credits, never money, and waits for the user's go.
- **Never in CI.** A Copilot token does not belong in a public repository's CI.
