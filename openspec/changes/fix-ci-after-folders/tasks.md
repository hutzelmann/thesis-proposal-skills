# Tasks

## 1. Install check on the folder layout

- [x] 1.1 Extend `offending_lines` in `tests/unit/test_fixture_paths.py` to scan `scripts/` (design D4); verify red first: `test_no_module_spells_a_fixture_files_path` names `scripts/install_check.py:42`
- [x] 1.2 Add an offline L0 test to `tests/unit/test_install_check.py` that runs `run_smoke` against a real copy of `skills/proposal-check` as the installed root, once inside the workspace (npx shape) and once in a separate home (installer shape), and expects ok; verify red first (`FileNotFoundError` on the flat fixture path)
- [x] 1.3 In `scripts/install_check.py`, make `harness/` importable only when not already on `sys.path` (design D3), resolve the fixture's proposal and oracle through `fixture_paths`, stage it as `<workdir>/<slug>/<slug>.md`, run the installed check with `--json` and the relative path from `<workdir>`, and require exit 1 with the oracle's error rules (design D1, D2); verify 1.1 and 1.2 turn green and `python3 scripts/install_check.py --help` imports cleanly outside pytest
- [x] 1.4 Update the install-check section of `harness/README.md` (folder-shaped smoke, oracle comparison, offline coverage in `tests/unit/test_install_check.py`); verify by reading the section against the code

## 2. Platform-independent byte sizes

- [x] 2.1 Make `sandbox_ws` in `tests/unit/test_eval_wiring.py` write bytes (design D5), and align `_staged_tree` in `tests/unit/test_copilot_cli.py`; verify `test_the_snapshot_sizes_walk_the_folders` and the sandbox tests pass, and a repo-wide search finds no other test that writes text mode and then compares byte sizes or digests

## 3. Native path in the release hint

- [x] 3.1 Add a unit test in `tests/unit/test_changelog_release.py` that renders the checked-out-`main` hint for `C:/Users/dev/main-checkout` with `PureWindowsPath` and for a POSIX path with `PurePosixPath`; verify red first (no formatting function yet)
- [x] 3.2 Extract `checkout_hint(path, flavour=Path)` in `scripts/changelog.py` and call it from `fast_forward_main` (design D6); verify 3.1 and `test_main_checked_out_elsewhere_is_left_for_the_maintainer` pass on Linux with unchanged output
- [x] 3.3 Review finding (the bare native path is uncopyable in Git Bash): extend the 3.1 test so a Windows path renders double-quoted (`"C:\Users\dev\main-checkout"`, and one with a space stays one argument), a POSIX path of safe characters renders byte-identical, and a POSIX path with a space renders single-quoted; verify red first
- [x] 3.4 Quote in `checkout_hint` (design D6), and make `test_main_checked_out_elsewhere_is_left_for_the_maintainer` compare the printed path with the checkout as paths (`samefile`) instead of as a string; verify 3.3 and the end-to-end test pass on Linux

## 4. Gates

- [x] 4.1 Run `uv run poe test` (exit 0), `uv run poe specs`, `python3 scripts/sync_shared.py --check`, `python3 scripts/changelog.py check` and `openspec validate fix-ci-after-folders --strict`; verify each passes
- [x] 4.2 Verify `git diff --stat -- skills/` is empty, so installs of 0.9.0 stay byte-identical when its tag moves

## Workflow follow-up

- Commit, archive, and move the `v0.9.0` tag to the fixed commit: the maintainer's steps, not this change's.
- Confirm the `Install check` workflow and the `l0-windows` job are green on the pushed commit; the Windows newline and path behavior has no other proof than that lane and the cross-platform unit tests.
