# Proposal

## Why

A dev-runner run of `import_messy` on 2026-10-18 (`uv run poe dev import_messy --model sonnet --isolated --keep`) left `.claude/skills/proposal-import/scripts/__pycache__/common.cpython-313.pyc` behind: `validate_refs.py` imports its sibling `common`, and Python caches the bytecode of every module it imports beside the module's file. Three shipped scripts do this, and none switches the cache off, so every run writes into a skill's install directory — the folder the import spec calls read-only territory. For a project-scope install the folder sits inside the student's workspace, where the cache shows up as an untracked folder in their own version control.

## What Changes

- The three shipped scripts that import a sibling module — `proposal-lit-search`'s `search.py` and `snowball.py`, and `proposal-import`'s `validate_refs.py` (with its synchronized copy in `proposal-reverse`) — switch off Python's bytecode cache before their first sibling import, and only when they run as the program, so a test suite or harness that imports them keeps its own setting.
- A new offline test runs every shipped script that can run as a program, from a copy of its skill's folder, and fails when a `__pycache__` folder appears in that copy. A future script that imports a sibling without the switch fails the suite.
- The new packaging requirement also records what already holds: an interpreter cache in an installed skill folder is not an installed skill file. The troubleshoot collector already leaves `__pycache__` out of its hashes and the installer already replaces a skill folder whole; neither changes.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-packaging`: adds the requirement "Scripts write nothing into the install directory": a shipped script never writes into its skill's install directory, a script that imports a sibling switches off the bytecode cache when it runs as the program, and an offline check guards it.

## Impact

- `skills/proposal-lit-search/scripts/search.py`, `skills/proposal-lit-search/scripts/snowball.py`, `skills/proposal-import/scripts/validate_refs.py` (source), and the generated copy `skills/proposal-reverse/scripts/validate_refs.py` via `scripts/sync_shared.py`.
- New test `tests/unit/test_script_bytecode.py`.
- No SKILL.md changes: the documented commands stay as they are, which keeps this change clear of the open `host-neutral-script-paths` change that rewrites those command paragraphs.
- No dependency, interpreter-version or platform change: `sys.dont_write_bytecode` exists on every supported Python.

Changelog: Running the literature search or the reference validation no longer leaves a `__pycache__` folder inside the installed skill.
