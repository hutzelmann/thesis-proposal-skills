# Proposal

## Why

The dev runner drives only Claude Code. Every student who installs the skills through ChatGPT's Codex runs them on a host the harness has never exercised. Codex expands no `${CLAUDE_SKILL_DIR}`, has no Skill tool, sandboxes the network by default, and starts subagents through its own tool. The only GPT measurement today is the metered Inspect path, which inlines `SKILL.md` and exercises none of those differences. The operator plans a ChatGPT Plus plan as a second subscription. A Codex dev runner then gives a $0 GPT dev loop and moves load off Max, which peaked at 84 % of its weekly cap.

There is no safe way to run `codex exec` today. The operator's `~/.codex/config.toml` routes to OpenRouter, so any ambient call is metered. An exported `CODEX_API_KEY` outranks every stored login in `exec`. A Codex login copied into a second home is stranded at its first refresh. The user's decisions of 2026-10-05 settle the shape:

- **Dev loop only.** No Codex result fills the matrix.
- **Two runners, Claude primary.** Both hosts sit behind one runner.
- **Logins.** Each client has its own login home, owned by the harness.
- **Judge.** The Claude dev judge grades Codex runs (D3(a)).
- **Quota.** A pre-run quota read that is unavailable refuses the run (D2(a)).
- **Sandbox.** Network and subagents are allowed only where a scenario needs them (D4(a)).
- **Rehearsal.** The Codex login is rehearsed on the free ChatGPT plan, with no model call (D6(b)).

This change lands after `close-claudeai-surfaces` and `add-harness-claude-login`, and builds on their `HostLogin`, `allowlisted_env`, `login_env`, `host-*` commands, refusal template and login note. Its implementation starts once both are implemented with their spec text final; change 1 is archived by then, because change 2's own precondition requires it. Its archive waits until change 2 is archived too, and change 2's archive waits for its live check L1.

## What Changes

- **A Codex login home owned by the harness.** It is a second `HostLogin` record at `…/thesis-proposal-dev/hosts/codex`, outside the system temporary directory.
  - **Seeding and validation.** `host-login codex` writes a pinned `config.toml` before it logs in: OpenAI provider, `forced_login_method = "chatgpt"`, file credential store, and web search, update check, history, analytics, feedback and bundled skills off. Every run validates that file with `--strict-config` and compares it key by key.
  - **Commands.** `uv run poe host-login codex [--reset] [--device-auth]` is for the user only. `uv run poe host-status codex [--quota]` makes no model call and never opens `auth.json`; the login's age is the file's modification time. `uv run poe host-logout codex` is for the user only.
  - **Login note.** Change 2's refusal template becomes client-aware. Until live check X8 passes, every Codex message whose remedy is `host-login codex` or `--reset` says that its effect on the operator's other ChatGPT sessions is unverified, instead of claiming they are not affected.
  - **Minimum CLI.** `CODEX_MIN_VERSION = 0.160.0`. An older CLI is refused.
- **Serial runs under a lock the child also holds.** Runs take `flock` on `<home>/.harness-run.lock`, and the lock's descriptor is passed to `codex exec`. The quota read and every `host-*` write take the same lock. On Linux the child also receives a parent-death signal. A timeout sends SIGINT, then SIGKILL after change 2's grace.
- **A plan billing guard.**
  - **Environment.** It is built by change 2's `allowlisted_env` with the Codex record, which is its third user. A per-run scratch `HOME` and XDG directories hide `~/.agents/skills`, shell rc files and key files. Every `CODEX_*`, `OPENAI_*`, `OPENROUTER_*` and `*_API_KEY` variable is stripped, and its name is recorded. An assertion on the final child environment, just before each spawn, refuses one that still carries such a variable; only `CODEX_HOME`, which the harness sets, is exempt. L0 tests pin both halves.
  - **Before the run.** Under the lock, the runner reads the plan quota through `codex app-server`'s `account/rateLimits/read`, which is not a model call. It refuses when the read is unavailable (an answer without a credits block counts as unavailable), when any credits exist, when the plan is not Plus or Pro, when either window is at 90 % or more, or when a limit has been reached. The plan rule makes the free-plan rehearsal's login refuse every run.
  - **After the run.** The runner checks the session rollout for the provider, the plan report and its credits state, the plan type, credits drawn, the limit state, refresh failures, a model reroute and a dropped effort. Every refusal is untested (exit 3) and uses the one refusal template.
- **One runner, one adapter per host.** `harness/hosts.py` adds `Host`, `RunView` and `JudgeBackend`, bound late so that existing monkeypatches keep working.
  - **Selection.** `--host {claude,codex}` is added, with `claude` as the default. `stage()` takes the host's skill directory, and Codex stages into `<ws>/.agents/skills/`.
  - **Scenario requirements.** `--host codex` requires `--model`, refuses `--max-budget-usd` (Codex has no cap) and refuses the install-probe scenarios.
  - **Plain `poe dev`.** It stays ambient on Claude (D5(b)). Codex has no ambient mode.
- **`harness/codex_cli.py`.** It holds:
  - `command()`;
  - `run_codex()`, which handles the lock, the stop signals, rollout capture and `quota.json`;
  - `failure_reason()` and the billing guard;
  - `codex_tool_calls()`. Codex items map to the canonical tool names (`Bash`, `Skill`, `Edit`, `Agent`, `mcp__s__t`, `WebSearch`), so the existing L1 verdicts and `routing.route_from_events` work unchanged;
  - telemetry with no cost.
- **Judge isolation follows the judge.** The Claude judge grades Codex runs inside a fresh Claude isolated configuration of its own. It never runs in the Codex home. An L0 test pins this.
- **Labelled, never a source of record.** Summaries carry `host` and the label "dev-runner (<host>), not comparable to matrix". Codex has no registry role, model default or currency alert. A `--summary-log` under `logs/evals` is refused.
- **L0 coverage on synthetic streams.** The streams are derived from the Codex 0.160 source and live in `tests/unit/data/codex_streams/`, labelled synthetic until the follow-up change `record-codex-streams` replaces them with recordings.
- **USER ACTIONS** (agents never log in):
  - update the Codex CLI to 0.160 or later;
  - D6(b) rehearsal on the free plan, which settles X1, X8, X4b and X7 with no model call;
  - after buying Plus: credit balance 0 and auto-reload off, then `uv run poe host-login codex --reset`.

  The first live `check_report` on a Plus model is the first Codex model call. It uses plan quota, not money, and waits for the user's explicit go.
- **Out of scope:** `smoke-codex`, because the smoke requirement demands a hard per-run budget cap. Also out of scope: a Codex routing rig, a Codex judge (`add-codex-dev-judge`), anything that feeds `report.py` or the matrix, and Claude step B.

## Capabilities

### New Capabilities

None. Codex enters the existing `testing-harness` capability.

### Modified Capabilities

- `testing-harness`:
  - ADDED "Dev-runner host adapters": host selection, the shared core, canonical tool calls, the Codex invocation and isolation checks.
  - ADDED "Codex plan billing guard": environment, pre-spawn assertion, pre-run quota read, post-run rollout checks, and the synthetic fixtures.
  - MODIFIED "Harness-owned host logins" (added by change 2; starting from its text as revised on 2026-10-05): the Codex home, commands, status items, preflight, lock, stop signal, the per-client login note with its X8 caveat, and a Codex login that is never opened.
  - MODIFIED "Inverted-hybrid runners": per-host labels; no dev-runner host writes where the support report reads.
  - MODIFIED "Measured environments carry no eval definitions": staging into the host's skill directory, `.agents/skills` for Codex.
  - MODIFIED "Dev-runner cost and helper-agent telemetry" (starting from change 2's revised text): Codex stream, no cost, spawn mapping, outward features, the budget cap only where the host offers one, the Codex login remedy, and a third untested reason for a Codex run's preconditions.
  - MODIFIED "Subscription text roles (dev runner)" (starting from change 2's revised text): judge isolation per backend; the smoke stays on Claude.
  - Not modified: "Isolated child environment" and "Isolated measurement environment". Change 2 scopes their Claude clauses to Claude children and configurations, and leaves a later client's child to the requirement that adds it.

## Impact

- **Code.**
  - New: `harness/hosts.py` and `harness/codex_cli.py`.
  - `harness/host_login.py`: the `CODEX` record, its checks, the lock, a new `run_host` with input, `pass_fds` and the record's stop signal (change 2 has none; its Claude children go through change 1's `routing.follow_stream`), and `stop_child` taking that signal.
  - `harness/claude_runner.py`: host selection, `stage(skill_dir)`, the judge isolation seam, summary labels.
  - `harness/routing.py`: `tool_calls` adds the Codex shape.
- **Tests.**
  - New: `tests/unit/test_codex_cli.py`, `test_hosts.py`, `tests/unit/data/codex_streams/` and its README.
  - Extended: `test_host_login.py`, `test_dev_runner_probe.py`, `test_routing.py`.
- **Docs.** A "Codex dev runner" section in `harness/README.md`, its known-limitations line, and the `AGENTS.md` Commands.
- **No model calls** in this change's gates. Live Codex runs refuse until a ChatGPT Plus or Pro login exists in the harness home. The free-plan login the rehearsal leaves there refuses every run on its plan, before any `exec`.
- **Never in CI.** A ChatGPT login does not belong in a public repository's CI.
