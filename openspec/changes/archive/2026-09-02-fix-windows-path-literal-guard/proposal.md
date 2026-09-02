# Fix the Windows-only path-literal assertion and guard its class

## Why

CI on `ed6290d` is red in `l0-windows` alone: `test_summary_labels_an_isolated_run` builds `Path("/tmp/cfg")`, hands it to `summary()`, and asserts the returned `config_dir` equals the POSIX literal `/tmp/cfg`. `summary()` renders it with `str(config)`, which is `\tmp\cfg` on Windows, so the assertion fails there and nowhere else. The runner is right — `config_dir` is a path a developer pastes into their own shell, and no code parses it — the test is wrong. This is the second Windows-only escape in three commits (`test_sync.py` file modes was the first), and each one costs a full CI round-trip to see, because nothing on a Linux clone can fail on it.

The existing guard `test_relative_paths_render_as_posix` does not cover this: it flags stringified `relative_to()`, the class that broke `sync_shared.py`. An absolute POSIX literal handed to `Path(...)` is a different class with the same failure mode, and the tree contains exactly one — the line that is red right now.

## What Changes

- `tests/unit/test_dev_runner_probe.py::test_summary_labels_an_isolated_run` binds the config path once and asserts `out["config_dir"] == str(config)`, so the expectation renders on whatever host runs it. `harness/claude_runner.py` is untouched.
- `tests/unit/test_repo_conventions.py` gains a rule flagging an absolute POSIX string literal passed to `Path(...)` anywhere under the scanned script directories and `tests/`. It fails on a Linux clone today against that one line and goes green with the fix, which is the point: the class becomes visible where the work happens instead of one CI round-trip later.

## Capabilities

### New Capabilities

(none — test and tooling fix, `skip_specs: true`)

### Modified Capabilities

(none — no shipped behavior changes; `summary()` keeps rendering the native path)

## Impact

- `tests/unit/test_dev_runner_probe.py` (one test), `tests/unit/test_repo_conventions.py` (one new rule plus its helper)
- No skills, no `shared/`, no scripts, no harness runtime. `poe test` and the `l0-windows` job are the only observers.
