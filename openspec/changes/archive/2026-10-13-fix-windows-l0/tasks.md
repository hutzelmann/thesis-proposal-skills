# Tasks

## 1. Golden prompts keep LF

- [x] 1.1 Add `tests/unit/data/l2_prompts/*.txt text eol=lf` above the generated block of `.gitattributes`, with its reason. Verify: `git check-attr text eol` reports `set`/`lf` for a golden file, and `python3 scripts/sync_shared.py --check` reports no drift.
- [x] 1.2 `git add --renormalize -- 'tests/unit/data/l2_prompts/*.txt'`. Verify: `git ls-files --eol` shows `i/lf w/lf attr/text eol=lf` for every golden file; nothing staged, because the blobs were already LF.
- [x] 1.3 Grep the tests for other byte comparisons of checked-out text (`read_bytes()`, `"rb"`, `newline=`, digests). Verify: every other hit compares bytes the test wrote itself, or bytes from the same checkout on both sides.
- [x] 1.4 `tests/unit/test_line_endings.py`: replay a Windows checkout of every byte-compared file, with a control file that must come back CRLF. Verify: it passes, and fails with the `.gitattributes` line removed.

## 2. Link targets without the extended-length prefix

- [x] 2.1 `host_login.plain_path` strips `\\?\` and `\\?\UNC\` and keeps the path type; `link_target` applies it to the readlink result. Verify: the unit cases in `test_host_login.py` pass.
- [x] 2.2 A `windows_readlink` fixture patches `Path.readlink` to answer with the prefix. Under it, `link_target`, `writeback_target`, `login_dir`, `claude_runner.login_label` and `_target_source` name the plain harness home, and a refresh is still written back. Verify: these tests fail without 2.1 and pass with it.
- [x] 2.3 Compare link targets in `test_host_login.py` through `link_target`, not a raw `readlink()`. Verify: `uv run pytest tests/unit/test_host_login.py tests/unit/test_dev_runner_probe.py tests/unit/test_routing.py`.

## 3. Case-insensitive process environment

- [x] 3.1 Parametrize `desktop_session` over the native `os.environ` and a case-folding stand-in for Windows'; return the environment the process holds. Verify: before 3.2 the two tests fail under `case-folding` on Linux, with `https_proxy` as the only difference, matching the Windows log.
- [x] 3.2 `test_defaults_to_the_process_environment` and `test_ambient_runner_inherits_the_operator_environment_minus_billing` compare with what the process holds. Verify: `uv run pytest tests/unit/test_isolated_env.py` passes in both flavours.

## 4. Gate

- [x] 4.1 `uv run poe test` and `uv run poe specs` green; `openspec validate fix-windows-l0 --strict`.
