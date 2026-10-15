# Proposal

## Why

The 0.9.0 stamp commit (67dedad) is red in CI on both `main` and `develop`, so the release that `adopt-proposal-folders` produced ships with a broken install check and a red Windows lane. Three independent defects surfaced, all in dev-side tooling and tests; none is in a shipped skill, so the fix can travel with release 0.9.0 by moving its tag without changing a single installed byte.

1. **Install check.** `scripts/install_check.py` spells the smoke fixture's path as `tests/fixtures/f15-format-broken/broken-format.md`, which the folder migration moved to `…/broken-format/broken-format.md`, so both install arms die with `FileNotFoundError`. Even with the path fixed, the smoke copies the proposal flat into its working directory, where the folder-aware check now reports `proposal-misplaced`, so the smoke would pass on a placement error rather than on the broken format it seeds. The fixture-path guard that exists to catch exactly this scans only `tests/` and `harness/`, so the spelled path in `scripts/` went unnoticed at L0.
2. **Windows snapshot sizes.** The `sandbox_ws` fixture in `tests/unit/test_eval_wiring.py` writes its files in text mode; on Windows each `\n` becomes `\r\n`, so the notes file is 96 bytes on disk against the 85 the test computes from the string.
3. **Windows merge hint.** `scripts/changelog.py` prints the checked-out-`main` hint with the worktree path exactly as `git worktree list` reports it (`C:/Users/...`), while the test expects the native spelling. The native spelling is only copyable quoted: bare, Git Bash strips its backslashes.

## What Changes

- `scripts/install_check.py`: the smoke resolves the f15 fixture's proposal through `harness/fixture_paths.py` instead of a spelled path, making `harness/` importable when run as `python3 scripts/install_check.py` (only when not already on `sys.path`, as `harness/lit_live.py` does for skill scripts). It stages the proposal as a workspace holds it, `<workdir>/<slug>/<slug>.md`, runs the installed check from `<workdir>` with the relative path, and requires exit 1 with exactly the fixture oracle's error rules, so a placement error can no longer pass as the seeded findings.
- `tests/unit/test_fixture_paths.py`: the spelled-path and corpus-walk guards also scan `scripts/`.
- `tests/unit/test_install_check.py`: a new offline L0 test runs the smoke against a real copy of `skills/proposal-check` as the installed root, in both install shapes (inside the workspace, as the skills CLI installs it, and in a separate home, as `install.py` does).
- `tests/unit/test_eval_wiring.py`: `sandbox_ws` writes bytes, so on-disk sizes match on every platform; the same pattern in `tests/unit/test_copilot_cli.py`'s staged skill tree (POSIX-only today) is aligned.
- `scripts/changelog.py`: the checked-out-`main` hint prints the worktree path in the platform's native spelling, quoted for the shell (double quotes on Windows, `shlex.quote` on POSIX), through a small formatting function a unit test exercises with `PureWindowsPath` and `PurePosixPath` on any OS; Linux output is unchanged for a path of safe characters. The end-to-end test compares the printed path with the checkout as paths, not as strings.
- `harness/README.md`: the install-check section says how the smoke stages the fixture and where it is covered offline.

Nothing under `skills/` changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None. The install check still satisfies skill-packaging's "Installed script smoke" scenario (the installed script exits with findings), now on the folder layout. Testing-harness's "Corpus walkers cover every proposal fixture" requires that no test or harness module spells a fixture file's path; extending the guard to `scripts/` enforces the same rule on more files without changing the requirement.

## Impact

- Code: `scripts/install_check.py`, `scripts/changelog.py`.
- Tests: `tests/unit/test_install_check.py`, `tests/unit/test_fixture_paths.py`, `tests/unit/test_eval_wiring.py`, `tests/unit/test_changelog_release.py`, `tests/unit/test_copilot_cli.py`.
- Docs: `harness/README.md`.
- CI: the `Install check` workflow and the `l0-windows` job turn green on the fixed commit.
- Release: no file under `skills/` changes, so installs of 0.9.0 stay byte-identical when its tag moves to the fixed commit.

Changelog: internal
