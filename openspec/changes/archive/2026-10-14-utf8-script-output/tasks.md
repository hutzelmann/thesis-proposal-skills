## 1. Tests first (red)

- [x] 1.1 Add `tests/unit/test_utf8_output.py` with the in-process layer (design D7): each of `check`, `search`, `snowball`, `validate_refs`, `publish`, `collect` and `install` runs `main(argv)` against cp1252-wrapped stdout (`strict`) and stderr (`backslashreplace`). The synthetic name `Łucja Musterfrau-Kővári` comes from data built in `tmp_path`, and network sources and lookups are stubbed. Verify: `uv run pytest tests/unit/test_utf8_output.py` fails before the fix, with `UnicodeEncodeError` on stdout, or with escaped `Ł` instead of UTF-8 on the installer's stderr.
- [x] 1.2 Add the subprocess layer: one test per family (`check.py`; `validate_refs.py` for `common.py`; `publish.py --handout`; `collect.py --dry-run --out`; `install.py --source <missing>`), run with `PYTHONIOENCODING=cp1252` in the child environment. Each test asserts the name's UTF-8 bytes and the documented exit code: 0, or 2 for the installer diagnostic. Verify: each fails before the fix, with a traceback and exit 1, or with escaped stderr for the installer.
- [x] 1.3 Add the pin layer: an AST scan asserts that every `main()` under `skills/*/scripts/` and in `install.py` calls its family's `utf8_output()` first (the installer: directly after its version gate), and that the five helper definitions are identical. Add the helper unit test: encoding switched, both non-default handlers kept (stdout opened `surrogateescape`, stderr `backslashreplace`, design D7), `\r\n` translation kept, `StringIO` and `None` untouched. Verify: fails before the fix because no helper exists, and fails against a helper that hardcodes `strict` for stdout.
- [x] 1.4 Add the captured-message layer (design D9): `publish.run()` against a child that writes `Ł` and a lone `0xFF` to stderr, exiting 0 and exiting 1, and a source rule in the pin layer that no `subprocess` call under `skills/*/scripts/` or in `install.py` runs in text mode without `encoding=`. Verify: all three fail before 2.6, with `UnicodeDecodeError` and with `publish.py:225` named.
- [x] 1.5 Move the fake home into `tests/helpers.py` (`fake_home()`, `fake_home_env()`, `FAKE_HOME_UNSET`) and use it from `test_install.py`, `test_troubleshoot_collect.py` and `test_utf8_output.py`, including the subprocess layer's child environment. Verify: those three files pass unchanged in count.

## 2. The fix (green)

- [x] 2.1 Add `utf8_output()` to `skills/proposal-check/scripts/check.py` and call it first in `main()`. Verify: the check entries of 1.1 and 1.2 pass.
- [x] 2.2 Add `utf8_output()` to `skills/proposal-lit-search/scripts/common.py`. Call `common.utf8_output()` first in the `main()` of `search.py`, `snowball.py` and `skills/proposal-import/scripts/validate_refs.py`. Verify: the lit-search and validate_refs entries of 1.1 and 1.2 pass.
- [x] 2.3 Add `utf8_output()` to `skills/proposal-publish/scripts/publish.py` and to `skills/proposal-troubleshoot/scripts/collect.py`, each called first in `main()`. Verify: their entries pass.
- [x] 2.4 Add `utf8_output()` to `install.py` and call it directly after the version gate, using only syntax the file already allows. Verify: the installer entries pass, and `test_the_installer_still_parses_on_an_old_interpreter` and `test_old_interpreter_gets_a_sentence_not_a_traceback` still pass.
- [x] 2.5 Run `python3 scripts/sync_shared.py` to regenerate the copies of `check.py` (5), `common.py` (2) and `validate_refs.py` (1). Verify: `python3 scripts/sync_shared.py --check` is clean, and the pin of 1.3 passes for every copy.
- [x] 2.6 In `skills/proposal-publish/scripts/publish.py`, make `run()` capture with `encoding="utf-8", errors="replace"` instead of `text=True` (design D9). Verify: the tests of 1.4 pass.

## 3. Consumers decode UTF-8

- [x] 3.1 Pass `encoding="utf-8"` instead of the platform default where in-repository code captures these scripts' output (design D6): `tests/unit/test_fixture_oracles.py` (both runs), `tests/unit/test_install.py` (installed-copy smoke), `tests/unit/test_lit_common.py` (unknown-source run), `harness/claude_runner.py` (`run_check`), and `scripts/install_check.py` (installer arm and smoke run). Verify: `uv run poe test` passes.

## 4. Gates

- [x] 4.1 From the worktree: `uv run poe test` exits 0; `uv run poe cov` holds the floor; `uv run poe specs` and `openspec validate utf8-script-output --strict` pass; `python3 scripts/sync_shared.py --check` is clean.

## 5. Manual note (not a task, not a gate)

`desktop-first-install` task 8.7 is the Windows session on a clean machine. None of its own steps prints a non-ASCII character, so the operator adds one: at 8.7's "ask for a check of a proposal", save that proposal as `Łucja-Test.md`, or ask for one literature search whose results include an author with `Ł` or `ő`. Confirm that the agent relays the check report, or the CSL-YAML, with the name intact and no traceback, and record the agent host and the Windows build in 8.7's notes. When `desktop-first-install` is next revised, its maintainer can add this step to 8.7 itself. The subprocess layer of 1.2 is the gate (design D8), so this change is archived as soon as sections 1–4 are done, without waiting for 8.7. That is why this note carries no checkbox.
