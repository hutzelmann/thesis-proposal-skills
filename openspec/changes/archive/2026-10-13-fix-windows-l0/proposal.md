## Why

The first Windows CI run in six weeks (GitHub Actions run 38385444225, job `l0-windows`) failed 23 L0 tests that pass on Linux. They have three causes. One is a real defect: on Windows the dev-run summary and the routing record labelled the harness login's directory in extended-length form (`\\?\C:\...`), and a stale-claim refusal named the operator's remedy for the harness login.

## What Changes

- **Golden prompts checked out with CRLF (16 tests).** The tests compare `tests/unit/data/l2_prompts/*.txt` byte for byte with a prompt built through `read_text()`, which folds CRLF to LF. git for Windows ships `core.autocrlf=true` and checks these files out with CRLF. A hand-written line above the generated block of `.gitattributes` now pins them to `text eol=lf`. The committed blobs were already LF, so `git add --renormalize` staged nothing. No other test compares checked-out text as bytes. The new `tests/unit/test_line_endings.py` replays a Windows checkout of every byte-compared file: a fresh repo with `core.autocrlf=true` and the repository's `.gitattributes`, plus a control file that proves the replay converts line endings.
- **Link targets in extended-length form (5 tests; production fix).** On Windows `os.readlink` returns `\\?\C:\...`, and `Path.resolve()` keeps a prefix it is given. `host_login.link_target` passed that prefix on, so `writeback_target` and `login_dir` carried it. The `login_dir` label in the dev-run summary and in the routing record therefore carried it too. `_target_source` compared the prefixed target with the plain harness home and classified the harness login as the operator's. The new `host_login.plain_path` strips `\\?\` and `\\?\UNC\`. `link_target` applies it, because that is the one place a readlink result enters. The tests now compare through `link_target` instead of a raw `readlink()`. New tests patch `Path.readlink` to answer as Windows does, then check the summary label, the write-back target, the source classification and a refresh write-back. Unit cases cover `plain_path` itself.
- **Case-insensitive process environment (2 tests; test fix).** Windows' `os.environ` holds names upper-cased, so the synthetic desktop session's `https_proxy` and `HTTPS_PROXY` are one variable there. The tests expected the process environment to hold both. The allowlist itself is unaffected: every name it admits from a Windows environment is admitted in upper case. The `desktop_session` fixture now runs every test twice, once natively and once with a case-folding stand-in for Windows' `os.environ`. It returns what the process environment holds, and the two tests compare with that instead of the literal.

No spec-level behavior changes. The write-back label scenario already names the harness home as the login's directory, and this change makes Windows meet it. Hence `skip_specs: true`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None.

## Impact

- `.gitattributes` (hand-written line), `harness/host_login.py` (`plain_path`, `link_target`), `tests/unit/test_host_login.py`, `tests/unit/test_isolated_env.py`, `tests/unit/test_line_endings.py` (new).
- Dev runs and routing records on Windows label the login directory as `C:\...`. A refusal there names the harness login's remedy for the harness login.
