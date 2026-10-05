# Design

## Context

Two call sites start an isolated host child:

- the routing rig's `stream_events`, which runs isolated every time;
- the dev runner's `run_claude`, which runs isolated only with `--isolated`.

Both build the child's environment as `dict(os.environ, CLAUDE_CONFIG_DIR=...)`, so the child gets the full launching environment. `claude_runner` already imports `prepare_config` from `routing`, which makes the "isolated environment" section of `routing.py` the shared home for isolation.

`scripts/install_check.py` has its own `isolated_env`. It strips every `CLAUDE*` variable and points `HOME` and the XDG base directories at a temp directory. Its child is `npx skills add`, not the host, and it needs the operator's npm and node settings to reach the registry. See proposal.md for the variables a desktop session exports.

## Goals / Non-Goals

**Goals:**

- One function decides what an isolated host child receives, and both call sites use it.
- A variable that no one has reviewed never reaches an isolated child.
- The child can still authenticate (linked credentials or `CLAUDE_CODE_OAUTH_TOKEN`), resolve binaries, reach the API through the machine's proxy and CA setup, and run the skills' scripts.

**Non-Goals:**

- **Ambient mode.** Without `--isolated`, the child keeps the operator's whole environment, including the desktop session's messaging socket and token. That mode exists to measure the operator's setup. The outward-tool deny list from `block-outward-tools-in-dev-runs` already keeps that child from using messaging tools.
- **`PATH` contents.** `PATH` is passed through as it is, so a run under `uv run` still finds the dev venv's `python3` first. That is a separate difference from a student's machine, and it predates this change.
- **`scripts/install_check.py`.** It keeps its own function: its child and its purpose are different, and it lives outside `harness/`.

## Decisions

### An allowlist, not a prefix denylist

`install_check`'s rule, dropping every `CLAUDE*` variable, would have been the smallest change. It misses half of what a desktop session sets. `DISABLE_MICROCOMPACT`, `API_TIMEOUT_MS`, `ANTHROPIC_BASE_URL`, `MCP_SERVER_CONNECTION_BATCH_SIZE` and `AI_AGENT` carry no `CLAUDE` prefix, and each one changes how the host behaves.

A denylist must list an open set: every variable the host reads, plus whatever the app adds next. When it misses one, the miss is silent, and the measurement changes with nothing to show for it. An allowlist lists a closed set: what a process needs in order to run on this machine. When it misses one, the miss is loud. A TLS failure or a missing binary fails the run, and the fix is one reviewed line.

For an instrument whose claim is "measures the default host", a loud miss is the acceptable failure mode.

Alternatives considered:

- **Strip `CLAUDE*` plus a list of known host variables.** This is still an open set, and it goes stale with every host release.
- **An empty environment plus `PATH` and `HOME`.** On this machine the host's TLS setup comes from `NIX_SSL_CERT_FILE` and `NODE_USE_SYSTEM_CA`, and a proxied network needs `HTTPS_PROXY`. The child would fail to reach the API for reasons that have nothing to do with the host.

### What the allowlist admits

Each group is admitted because it describes the machine, which a student's host shares, and not the launching session:

| Group | Names | Why |
|---|---|---|
| Mandated | `PATH`, `HOME` | Binaries; home-relative lookups, including the skills' `~/.config/thesis-proposal/api-keys.env` |
| Login | `CLAUDE_CODE_OAUTH_TOKEN` | The long-lived token path (keep-isolated-login): with it set, no credentials are linked |
| Identity, shell | `USER`, `LOGNAME`, `SHELL` | The host's Bash tool picks its shell from `SHELL` |
| Locale | `LANG`, `LANGUAGE`, every `LC_*` | Script I/O encoding, as on the student's machine |
| Temp | `TMPDIR`, `TMP`, `TEMP` | macOS sets a per-user `TMPDIR` |
| XDG base dirs | `XDG_CONFIG_HOME`, `XDG_DATA_HOME`, `XDG_STATE_HOME`, `XDG_CACHE_HOME`, `XDG_RUNTIME_DIR`, `XDG_CONFIG_DIRS`, `XDG_DATA_DIRS` | Tool caches (typst packages). This exposes nothing that `HOME` does not already reach |
| Proxy | `HTTP_PROXY`, `HTTPS_PROXY`, `NO_PROXY`, `ALL_PROXY`, and their lowercase spellings | The network route to the API |
| CA trust | `SSL_CERT_FILE`, `SSL_CERT_DIR`, `NIX_SSL_CERT_FILE`, `NODE_EXTRA_CA_CERTS`, `NODE_USE_SYSTEM_CA`, `REQUESTS_CA_BUNDLE`, `CURL_CA_BUNDLE` | TLS to the API and to literature services |
| Windows basics | `SYSTEMROOT`, `COMSPEC`, `PATHEXT`, `USERPROFILE`, `APPDATA`, `LOCALAPPDATA` | A Windows child process does not start without them |

The following are dropped on purpose:

- **`TERM`.** A desktop session does not set it and a terminal does. Keeping it would make the isolated child depend on where the runner was launched, which is the very difference isolation removes. A headless `-p` child does not need it.
- **`XDG_SESSION_*`** and other desktop-session variables.
- **`VIRTUAL_ENV`**, and every `ANTHROPIC_*` variable, `ANTHROPIC_API_KEY` included. An isolated run measures the subscription login it was prepared with, not whatever key happens to be in the shell.
- **The skills' own key variables**, such as `OPENCITATIONS_TOKEN`. These belong to the operator's ambient environment. A student's default host reads them from `api-keys.env`, which `HOME` still reaches.

### Where it lives and how it is called

`routing.isolated_env(config, environ=None) -> dict[str, str]` goes in the "isolated environment" section, next to `prepare_config`. `environ` defaults to `os.environ`. Tests pass a synthetic mapping and never touch the real environment.

`run_claude` keeps `env=None` in ambient mode and calls `isolated_env(config)` when a configuration is given. `stream_events` always calls it. The admitted names are a module constant, so a test can pin them and a reviewer sees any addition as a diff.

**Reconciled with main on 2026-10-05.** While this change waited for review, add-dev-runner-judge landed. Its `claude_runner.model_env(environ, config)` strips every `ANTHROPIC_*` variable and `CLAUDE_CODE_USE_*` switch from the model run in both modes, and keeps everything else, the effort setting included. Its spec requirement "Dev-runner cost and helper-agent telemetry" says the same, for isolated mode too. The two rules meet in `model_env`:

- **Isolated:** `model_env` returns `isolated_env(config, environ)`. The allowlist admits no billing variable, a fact `test_admitted_names_stay_reviewed` pins. So the billing rule holds, and the operator's effort and session settings stay out, which is the point of isolation.
- **Ambient:** `model_env` keeps main's billing strip. The ambient child is therefore no longer `env=None`; it gets the operator's environment minus the billing variables. The ambient requirement and scenario of this change say exactly that.

The spec delta MODIFIES "Dev-runner cost and helper-agent telemetry" so it carries this split. Its effort scenario becomes one scenario per mode. Two docs said the routing rig still hands the launching shell's environment to `claude -p`: AGENTS.md "Metered model calls" and the harness README's billing paragraph. Both now name only the audit preflight.

**Follow-up, not in scope:** add-dev-runner-judge also brought its own allowlist for the judge child, `claude_cli.ENV_KEEP` with `child_env`. It admits fewer machine variables than `ADMITTED_ENV`: no proxy, no CA-trust variables, no `SHELL`, no `LANGUAGE`. Two allowlists that should describe the same machine will drift. A later change can build the judge's environment from `isolated_env` too.

### Tests

There are two kinds, both in a new `tests/unit/test_isolated_env.py`:

- **Pure-function tests** over a synthetic desktop-session environment. Every value is a fake marker string. The tests cover:
  - the dropped variables named in the spec;
  - an unknown variable;
  - the admitted groups;
  - `CLAUDE_CONFIG_DIR` overriding an inherited value;
  - no mutation of the input;
  - no output (`capsys`), so no fake value ever appears in output.
- **Wiring tests.** They monkeypatch `subprocess.run` (the runner) and `subprocess.Popen` (the rig) to capture the `env` each call site passes, with no host started:
  - isolated runs receive the allowlisted environment;
  - an ambient run passes `env=None`.

## Risks / Trade-offs

- **[Risk] The allowlist drops a variable this machine's host needs, and isolated runs fail to start or to reach the API.** → Mitigation: the operator-approved haiku isolated dev run checks this before the change is archived. A failure fails loudly, and the fix is one admitted name with its reason.
- **[Risk] The isolated child no longer goes through the desktop app's `ANTHROPIC_BASE_URL` and auth refresh.** → This is the intent: the default host talks to the default endpoint with the linked login. If the linked login has expired, the child refreshes it itself. That is the behavior keep-isolated-login handles.
- **[Trade-off] Ambient mode still hands the messaging token to a child that runs with permission prompts skipped.** → This is out of scope. Ambient mode measures the operator's session, and the outward tools are denied. A follow-up can narrow it if wanted.
- **[Risk] Merge overlap with the unmerged keep-isolated-login change, which edits both call sites.** → `isolated_env` takes only the config path, so whichever change merges second puts the call back at the two sites. The spec delta here is an ADDED requirement, so it does not conflict with that change's spec edits.
