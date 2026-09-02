## 1. Guard first

- [x] 1.1 Add `absolute_posix_path_literals(tree)` and `test_no_absolute_posix_path_literal` to the cross-platform section of `tests/unit/test_repo_conventions.py`, scanning `PATH_FILES`, matching a `Path(...)` call whose single argument is a string constant starting with `/`; the docstring names the `l0-windows` run this comes from.
- [x] 1.2 Run the rule and confirm it reports exactly `tests/unit/test_dev_runner_probe.py:162` — one hit, no others.

## 2. Fix the test

- [x] 2.1 In `test_summary_labels_an_isolated_run`, bind the config path once (from the `tmp_path` fixture, so no absolute literal returns) and assert `out["config_dir"] == str(config)`; leave the other four assertions and `harness/claude_runner.py` untouched.
- [x] 2.2 Confirm the new rule is green and `test_summary_labels_an_isolated_run` still passes.

## 3. Verify

- [x] 3.1 `uv run poe test` green (pytest + ruff + drift + conform).
- [x] 3.2 `uv run poe cov` holds the floor; `uv run poe specs` validates.
- [x] 3.3 The guard reports zero hits tree-wide and the diff touches tests only — `harness/claude_runner.py` unchanged, so `config_dir` still renders the native path. The `l0-windows` job on the pushed commit is the remaining out-of-tree confirmation.
