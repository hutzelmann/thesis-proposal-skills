## Why

On Windows, a script an agent runs writes to a pipe, and Python encodes a pipe in the ANSI code page, which is cp1252 on a Western-European machine. A character outside that code page aborts the script with `UnicodeEncodeError`. The literature search hits this as soon as a candidate has an author such as `Łukasz` in its CSL-YAML. The check script hits it on a file name such as `Łucja.md`. On a machine whose code page lacks the em dash (cp932, for example), it hits it on its own report headings. File I/O is already explicit UTF-8 everywhere; stdout and stderr are affected, and so is one reader. `publish.py` decodes the messages of pandoc and typst in the same code page, while both tools write UTF-8, so a converter warning that quotes `Łukasz` aborts the build report with `UnicodeDecodeError`, even after a successful build. Reproduced on Linux with `PYTHONIOENCODING=cp1252` on 2026-10-13: `check.py` exits 1 with a traceback instead of printing its report.

## What Changes

- **Each user-side script family gets one helper, `utf8_output()`, called at the start of `main()`.** It reconfigures `sys.stdout` and `sys.stderr` to UTF-8 and keeps each stream's current error handler, because `reconfigure(encoding=...)` alone resets it to `strict` and stderr's is `backslashreplace`. Newline handling, line buffering and write-through are unchanged. A stream without `reconfigure()`, such as a test's `StringIO` or the `None` of a windowless interpreter, is left alone. The families:
  - `skills/proposal-check/scripts/check.py`, which also covers its five generated copies;
  - `skills/proposal-lit-search/scripts/common.py`, called by `search.py`, `snowball.py` and `validate_refs.py`, with its vendored copies in `proposal-import` and `proposal-reverse`;
  - `skills/proposal-publish/scripts/publish.py`;
  - `skills/proposal-troubleshoot/scripts/collect.py`;
  - the root `install.py`. Its call comes after the version gate and uses only syntax that still parses on Python 3.7.
- **`publish.py` decodes its tools' messages as UTF-8.** Its `run()` captures pandoc and typst with `encoding="utf-8", errors="replace"` instead of `text=True`. A byte that is not UTF-8 becomes a replacement character in the diagnostic rather than a traceback.
- **In-repository consumers decode UTF-8.** Tests and harness code that run these scripts as subprocesses and read their output pass `encoding="utf-8"` instead of the platform default. Otherwise the Windows CI job would decode the new UTF-8 output as cp1252.
- **Tests.** In-process tests run each entry point's `main()` against cp1252-wrapped streams. A subprocess test per family runs the real script with `PYTHONIOENCODING=cp1252`, which reproduces the Windows pipe on every platform and runs for real on the Windows CI job. An AST pin requires every user-side `main()` to call its family's helper first, and requires the five helpers to stay identical. A second scan fails on any user-side `subprocess` call in text mode without an explicit encoding, and a test runs `publish.py`'s `run()` against a child writing `Ł` and a byte that is not UTF-8.
- **Unchanged:** every message's wording, exit codes, file I/O, the shipped `SKILL.md` files, and `install.py`'s Python 3.7 parse guarantee.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-packaging`: an ADDED requirement, "Script output encoding". A shipped user-side script writes its stdout and stderr as UTF-8 whatever the platform's pipe or console encoding, keeps each stream's error handler, leaves streams it cannot reconfigure alone, and decodes the messages of programs it starts as UTF-8. "User-side script constraints" is not modified, because the open change `desktop-first-install` owns its delta.

## Impact

- User-side scripts: `skills/proposal-check/scripts/check.py`, `skills/proposal-lit-search/scripts/{common,search,snowball}.py`, `skills/proposal-import/scripts/validate_refs.py`, `skills/proposal-publish/scripts/publish.py`, `skills/proposal-troubleshoot/scripts/collect.py`, `install.py`. `scripts/sync_shared.py` regenerates `check.py` (five copies), `common.py` (two copies) and `validate_refs.py` (one copy).
- Tests: a new `tests/unit/test_utf8_output.py`. The fake home that `test_install.py` and `test_troubleshoot_collect.py` each built moves into `tests/helpers.py`, since the new file needs it a third time. The subprocess readers in `tests/unit/test_fixture_oracles.py`, `tests/unit/test_install.py` and `tests/unit/test_lit_common.py` decode UTF-8.
- Dev-side consumers: `harness/claude_runner.py` (`run_check`) and `scripts/install_check.py` (its installer and smoke runs) decode UTF-8.
- No new dependency. No `SKILL.md` changes, so no collision with the open changes' prose edits. `desktop-first-install`'s Windows session (task 8.7) sees the fix on a real Windows pipe, but it is not a gate.
