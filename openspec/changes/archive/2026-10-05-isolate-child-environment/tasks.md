# Tasks

## 1. Tests first

- [x] 1.1 Write `tests/unit/test_isolated_env.py`. Its pure-function tests run against a synthetic desktop-session environment and cover these cases:
  - the dropped session, auth-path and host-tuning variables;
  - an unknown variable;
  - every admitted group;
  - `CLAUDE_CONFIG_DIR` overriding an inherited value;
  - the input left unmutated;
  - no output, with no fake value in it.

  Verify that they fail before the function exists. *(Failed at import; then 11/13 passed before wiring.)*
- [x] 1.2 Add wiring tests that capture the `env` passed by `run_claude`, with `subprocess.run` monkeypatched, and by `stream_events`, with `subprocess.Popen` monkeypatched. The cases are: isolated runner, ambient runner (`env=None`), and the routing rig. Verify that the isolated and rig cases fail against the current `dict(os.environ, ...)` call sites. *(Both failed; the ambient case passed. The wiring tests replace the whole process environment with the synthetic one, so a failing diff can print only fake values.)*

## 2. Implementation

- [x] 2.1 Add `ADMITTED_ENV` and `isolated_env(config, environ=None)` to the "isolated environment" section of `harness/routing.py`, with the groups and reasons from design.md. Verify that the tests from 1.1 pass.
- [x] 2.2 Use `isolated_env` in `routing.stream_events`, and in `claude_runner.run_claude` when a config is given. Ambient mode stays `env=None`. Verify that the tests from 1.2 pass.
- [x] 2.3 Update the `claude_runner.py` module docstring and the `--isolated` text in `harness/README.md` to say that isolated runs also allowlist the environment. Verify by reading the diff. *(Also updated: the `routing.py` module docstring and the README's routing-rig isolation paragraph.)*

## 2a. Reconcile with main (2026-10-05, after add-dev-runner-judge landed)

- [x] 2a.1 Rebase onto main 5437e66. Resolve the routing.py imports and section, and the claude_runner.py imports and docstring. `import os` stays, because main's runner still reads `os.environ`. Take main's harness README and re-add this change's two sentences.
- [x] 2a.2 `model_env`: isolated mode returns `isolated_env(config, environ)`; ambient mode keeps main's billing strip. Update the L0 tests to match:
  - `test_model_env_*` is split per mode.
  - `test_host_receives_the_stripped_environment[True]` now expects no inherited effort.
  - the ambient wiring test expects the operator's environment minus the billing variables.
  - the wiring tests' fake stream is subscription-shaped, as main's billing check requires.
- [x] 2a.3 Spec delta: MODIFY "Dev-runner cost and helper-agent telemetry" with the per-mode environment sentence and scenarios, and align the ambient sentence and scenario of the ADDED requirement. `openspec validate isolate-child-environment --strict` passes.
- [x] 2a.4 AGENTS.md "Metered model calls" and the harness README's billing paragraph no longer say the routing rig passes the launching shell's environment; they name only the audit preflight.

## 3. Verification

- [x] 3.1 Run `uv run poe test` and confirm it is green: pytest, ruff, drift, conform.
- [x] 3.2 Run `openspec validate --all --strict` (`uv run poe specs`) and confirm it is green.
- [x] 3.3 Live check, approved by the operator: one isolated dev run on haiku with a budget cap and a kept workspace (`uv run poe dev check_report --model haiku --isolated --keep --max-budget-usd 0.5`), started from a desktop session. Confirm that the run authenticates and completes, and that the child no longer records the desktop entrypoint. Print only booleans, enums and dates, never a path or an environment value.

  **Results, 2026-10-04, host 2.1.284:**

  - **The authenticated run completed.** L1 PASS, 4/6 oracle errors surfaced, file untouched. Cost $0.065, 5 turns, no helper agents. The stored login stayed valid until 2026-10-05 04:24 UTC, so the run did not refresh it, and nothing was stranded.
  - **The entrypoint is gone, confirmed by a probe.** A scratch probe started the child twice, each time in a config directory of its own that held empty settings and no credentials. One arm used the old `dict(os.environ, CLAUDE_CONFIG_DIR=…)`, the other `isolated_env`. Neither arm could authenticate, so neither made a model call; cost $0. Each child's transcript recorded the following:

    | Environment | Transcript `entrypoint` |
    |---|---|
    | old construction | `claude-desktop` (11 lines) |
    | `isolated_env` | `sdk-cli` (11 lines), the plain headless entrypoint |

  - **Two instruments that do not work, so nobody reaches for them again:**
    - **The isolated transcript.** It lands in the temp config directory, which the runner deletes. The `~/.claude/projects/-tmp-devrun-*/` transcripts that recorded `claude-desktop` came from ambient runs.
    - **The stream's `init` event.** Its `messaging_socket_path` names the child's own socket, which never equals the parent's, in runs before and after the change. Its `tools` list carries `ReportFindings` in both, so that tool does not come from the inherited variable. Neither field shows the leak.
