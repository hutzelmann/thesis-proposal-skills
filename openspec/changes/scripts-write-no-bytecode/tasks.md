# Tasks

## 1. Guard first

- [x] 1.1 Add `tests/unit/test_script_bytecode.py`. It discovers every `skills/*/scripts/*.py` with a `__main__` block, runs each one with `--help` from a copy of its skill folder (child environment without `PYTHONDONTWRITEBYTECODE`/`PYTHONPYCACHEPREFIX`, working directory outside the copy), and asserts exit 0 and no `__pycache__` in the copy, naming the script and the cache files on failure. Verify that, before the fix, it fails for exactly `search.py`, `snowball.py` and both `validate_refs.py` copies.
- [x] 1.2 In the same file, add the companion test: `python -c "import search"` against a copied lit-search scripts folder prints `sys.dont_write_bytecode` as `False` and leaves a `__pycache__` in the copy. This is the import-side scenario and the negative control. Verify that it passes before and after the fix.

## 2. Switch the cache off in the entry scripts

- [x] 2.1 In `skills/proposal-lit-search/scripts/search.py` and `snowball.py`, add a commented `if __name__ == "__main__": sys.dont_write_bytecode = True` block after the standard-library imports and before the first sibling import. Verify that `uv run ruff check skills/proposal-lit-search` passes and that the 1.1 cases for both scripts turn green.
- [x] 2.2 Make the same edit in `skills/proposal-import/scripts/validate_refs.py` (the source), placed before `import common`, then run `python3 scripts/sync_shared.py` to regenerate `skills/proposal-reverse/scripts/validate_refs.py`. Verify that `python3 scripts/sync_shared.py --check` is clean and that the 1.1 cases for both copies turn green.

## 3. Pin what the collector and installer already do

- [x] 3.1 Confirm that `test_hashes_cover_scripts_and_references_not_only_instructions` (`tests/unit/test_troubleshoot_collect.py`) pins the collector's `__pycache__` skip. Add a case where an installed skill folder holds a `scripts/__pycache__/*.pyc` and the report's `hashes.txt` leaves it out, unless an existing test already covers that. Verify with `uv run pytest tests/unit/test_troubleshoot_collect.py`.
- [x] 3.2 Add two installer tests to `tests/unit/test_install.py`. In the first, a directory source whose skill folder holds `__pycache__/x.pyc` installs without it. In the second, a cache planted in an installed skill folder is gone after a rerun. Verify with `uv run pytest tests/unit/test_install.py`.

## 4. Integration

- [x] 4.1 Run `uv run poe test` on a clean tree and verify it is green.
- [x] 4.2 Run `uv run poe specs` and verify that it passes and that the new requirement stays under the 500-character limit.

## Workflow follow-up

- Maintainer review of the change and the diff; commit to `develop` only on their OK.
- Archive after review: the `Changelog:` sentence goes under `### Fixed` in `CHANGELOG.md` `[Unreleased]`, committed together with the archive.
