# Proposal

## Why

Two dev-side gates do something different from what the repository says they do.

**The pre-commit hook stages files nobody asked it to stage.** `.githooks/pre-commit` runs `python3 scripts/sync_shared.py` and `git add`s every path on a `synced <src> -> <dst>` line. The SKILL.md, copy and `.gitattributes` passes call `_materialize` with the default `announce_unchanged=True`, so unchanged destinations get a line too. Every commit therefore stages 36 paths: 11 `SKILL.md` files, 24 generated copies and `.gitattributes`. Any unstaged hand edit in one of those files goes into the commit. In a shared checkout, another session's work in progress goes in as well. The hook also writes the working tree: an unstaged edit inside a materialized region is silently reverted before the commit.

Both effects were reproduced on a scratch copy of `main` (2188f45):

- An unstaged paragraph added to `skills/proposal-write/SKILL.md` went from ` M` to `M ` after the hook ran.
- An edit at the end of the same file's report-offer region disappeared from the working tree.

The design that introduced the hook (2026-07-30 `reduce-skill-duplication`) rested on one premise: destinations are generated files and never hand-edited, so auto-staging is safe. That premise stopped holding on 2026-08-23 (`dedupe-skill-header-blocks`), when regions were first materialized into the hand-written `SKILL.md` files. `desktop-first-install` fixed the same flaw for `README.md` and `docs/install.md` only (`announce_unchanged=False`).

**The conformance canary runs a third-party port.** `scripts/conform.py` pins `npx skills-ref@0.1.5`. `npm view skills-ref` shows:

- author `YanchaoMa <crazyyanchao@gmail.com>`, maintainer `yc.ma`
- `repository: null`, `homepage: null`
- six versions, 0.1.0 to 0.1.5, all published 2025-12-26/27

It is a JavaScript re-implementation. The standard's reference validator is the Python package `skills-ref` in `github.com/agentskills/agentskills` (subdirectory `skills-ref`, authored by the standard's maintainers). That repository has no tags and is not on PyPI. The `standard-conformance` spec, `AGENTS.md`, `README.md` and the `conform.py` docstring all call the pinned tool "the standard's reference validator", which is not true. The 2026-08-24 design (`agentskills-conformance-surface`, D4) assumed the npm package was the published reference. Meanwhile, unreviewed third-party npm code runs on every `poe test` and in CI.

Both validators were run read-only on `main` on 2026-10-13. Each accepts all 11 skills, so switching changes no current verdict. On seeded copies the official validator proved stricter about YAML: it rejects a flow-style mapping that the port accepts. design.md, "Validator comparison", has the exact outputs.

## What Changes

- **`.githooks/pre-commit` becomes check-only.** It exports the staged snapshot to a temporary directory and runs that snapshot's own `scripts/sync_shared.py --check` there. If the check fails, it refuses the commit, prints the drifted paths and the exact repair (`python3 scripts/sync_shared.py`, then stage the files it lists), and exits non-zero. It never stages, writes or reverts anything. CI's `--check` remains the backstop for bypassed hooks.
- **`scripts/sync_shared.py` announces only what it rewrote.** The `announce_unchanged` parameter is removed, and an in-sync run says so in one closing line. "Stage the files it lists" is then always a safe instruction.
- **`scripts/conform.py` runs the official validator.** The command becomes `uvx --from git+https://github.com/agentskills/agentskills@<sha>#subdirectory=skills-ref skills-ref validate <dir>`, pinned by a full commit SHA. The validator's two direct dependencies are pinned to the upstream lock's versions, and the child runs in UTF-8 mode. Proposed pin: `69ef37e9424c0a7ea9dd2293b559e43ec8176379`, agentskills `main` on 2026-10-13 (commit dated 2026-08-09). Bumping the pin stays the reviewed step.
- **Docs and wording.** `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, the `conform.py` docstring, the `pyproject.toml` comment and the `sync_shared.py` docstrings stop describing a repairing hook and stop calling the npm port the reference validator. A refused commit is fixed by running the sync, never by `--no-verify`.
- **Tests.**
  - New L0 subprocess tests drive the real hook through `git commit` in a temporary repository.
  - New offline tests cover `conform.py`.
  - `test_sync.py::test_synced_lines_stay_parseable_by_the_pre_commit_hook` is replaced, because nothing parses those lines any more.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-packaging`: the requirement "Commit-time sync automation" is renamed to "Commit-time drift check" and rewritten:
  - The commit-time step checks the staged snapshot and refuses on drift, instead of materializing and staging.
  - It never modifies the index or the working tree.
  - The regeneration command names only the files it rewrote.
- `standard-conformance`: the requirement "External conformance validator as a canary" now pins down what "the standard's reference validator" means: the maintainers' implementation from the standard's own repository, never a port. It must be pinned by an immutable identifier together with the dependency versions that decide what it accepts.

## Impact

- **Code:** `.githooks/pre-commit`, `scripts/sync_shared.py` (`_materialize`, `sync`, docstrings), `scripts/conform.py`.
- **Tests:**
  - `tests/unit/test_sync.py` (one test removed, one generalized)
  - new `tests/unit/test_commit_hook.py` (POSIX-only, like `test_push_guard.py`)
  - new `tests/unit/test_conform.py` (offline)
- **Docs:** `AGENTS.md` (Commands block, the Git rule, "The Agent Skills standard", "Skill header pattern" materialization paragraph), `README.md` (contributor bullets, standard section), `CONTRIBUTING.md` setup step, `pyproject.toml` comment on `conform`.
- **Workflow:**
  - Contributors with an activated hook now get a refused commit, where they used to get an auto-staged sync.
  - Partial commits (`git add -p`) and shared checkouts become safe.
  - A merge that leaves stale copies is caught at the next commit.
- **Dependencies:**
  - Conform no longer needs Node/npx. CI still needs it for `poe specs` (`npx @fission-ai/openspec`).
  - Conform now needs `uv`/`uvx` and `git` on PATH, and network on first run (about 1 MB clone plus 5 wheels). After that it runs from the uv cache, `--offline` included.
- **CI:** the `l0` job already has `astral-sh/setup-uv`, `git` and network, so `poe test` (which includes `conform`) needs no workflow edit. The `l0-windows` job runs `poe test-fast`, which excludes `conform`.
- **Specs:** `openspec/specs/skill-packaging/spec.md`, `openspec/specs/standard-conformance/spec.md` (on archive).
- **Not affected:** user-side skill scripts and anything shipped to students.
