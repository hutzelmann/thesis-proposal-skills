# Tasks

## 1. Sync output names only what it rewrote (design D3)

- [x] 1.1 In `scripts/sync_shared.py`, remove the `announce_unchanged` parameter from `_materialize` and from its call in `_sync_prompt_docs`. Print `synced <src> -> <dst>` only when a file is written. Make `sync()` close a write run with `generated copies already in sync` when nothing was written, and with `rewrote N generated file(s)` otherwise; `--check` output is unchanged. Rewrite the `_materialize` docstring and the atomic-write comment so neither names the pre-commit hook as a reader or parser any more; the atomic-write rationale stays, with xdist workers and concurrent syncs as the readers. Verify: `uv run pytest tests/unit/test_sync.py` is green after 1.2.
- [x] 1.2 In `tests/unit/test_sync.py`:
  - Delete `test_synced_lines_stay_parseable_by_the_pre_commit_hook`; its subject no longer exists, and it ran a real sync on the tracked tree.
  - Generalize `test_unchanged_documents_are_not_announced_to_the_hook` into a temp-tree test across all four passes. Copy `shared/`, `skills/`, the prompt documents and `.gitattributes`, then monkeypatch `REPO`, `SKILLS`, `BLOCKS`, `PROMPT_SOURCE` and `GITATTRIBUTES`.
  - The test asserts that an in-sync run prints no `synced` line and prints `generated copies already in sync`.
  - It also asserts that after one edit to `shared/blocks/voice.md`, the `synced` lines name exactly the 11 `SKILL.md` paths.
  - Reword the docstring of `test_materialize_never_exposes_a_truncated_destination` the same way as the comment in 1.1.
  - Verify: `uv run pytest tests/unit/test_sync.py -v` is green, and `git grep -n "pre_commit_hook\|announce_unchanged" -- tests scripts` finds nothing.
  - *Done 2026-10-13.* Red first: the two new temp-tree tests failed against the old sync, with all 36 paths announced on an in-sync tree. Green after 1.1: 27 passed; the grep finds nothing.
    - In write mode `_materialize` now returns the path it rewrote, so `sync()` counts from the same list `--check` uses.
    - `test_check_detects_a_drifted_prompt_copy` and `test_materialize_never_exposes_a_truncated_destination` assert that return value.
    - The prompt-docs test was renamed `test_a_prompt_change_announces_both_documents_and_nothing_else`.

## 2. Check-only pre-commit hook (design D1, D2, D8)

- [x] 2.1 Write `tests/unit/test_commit_hook.py` before touching the hook.
  - Setup: a `tmp_path` repository holding copies of `shared/`, `skills/` (without `__pycache__`), `scripts/sync_shared.py`, `README.md`, `docs/install.md`, `.gitattributes` and the real `.githooks/pre-commit`. Every git call runs with `GIT_CONFIG_GLOBAL=os.devnull`, `GIT_CONFIG_NOSYSTEM=1` and `-c user.name/-c user.email`. The initial commit is made before `core.hooksPath=.githooks` is set.
  - The module is skipped off POSIX, with the reason stated, as in `test_push_guard.py`.
  - Each case below runs a real `git commit`:
    - **(A) No drift.** With an unstaged paragraph added below the first `##` heading of `skills/proposal-write/SKILL.md` and `notes.txt` staged, the commit exits 0. `git show --name-only HEAD` lists `notes.txt` only. `git status --porcelain` still shows ` M skills/proposal-write/SKILL.md`, and that file's bytes are unchanged.
    - **(B) Staged drift.** With `shared/blocks/voice.md` edited and staged and no sync run, the commit exits non-zero. stderr contains `python3 scripts/sync_shared.py` and all 11 `skills/proposal-*/SKILL.md` paths. `git diff --cached --name-only` is exactly `shared/blocks/voice.md`. HEAD is unchanged, and every working-tree file is byte-identical to its state before the attempt.
    - **(C) Synced but not staged.** After B, running `python3 scripts/sync_shared.py` in the temporary repository without re-staging still gets the commit refused.
    - **(D) A peer's unstaged edit.** With an unsynced `voice.md` edit left unstaged and an unrelated file staged, the commit exits 0, and the `voice.md` edit is still unstaged and unchanged.
    - **(E) `commit -a`.** In D's state, `git commit -a` is refused.
    - **(F) Executable.** The hook file is executable.
  - Verify: run the module against the current hook and confirm it is red, with case A failing because the hook stages `SKILL.md`. Record which cases fail.
  - *Done 2026-10-13.* The setup copy is a shared helper, `copy_sync_tree` in `tests/helpers.py`, used by both this module and `test_sync.py`. The red run used HEAD's hook and HEAD's `sync_shared.py` (a `git archive HEAD` snapshot plus the two new test files): 5 failed, 1 passed (F).
    - (A): the commit also held `skills/proposal-write/SKILL.md`.
    - (B), (C) and (E): exit 0, because the old hook regenerated the copies and staged them.
    - (D): the unrelated commit held `notes.txt` plus all 11 `SKILL.md`, regenerated from the peer's *unstaged* `voice.md`. The old hook committed copies whose source was not in the commit.
    - Against the working tree's new `sync_shared.py`, the old hook also broke outright (`fatal: pathspec 'in sync' did not match any files`), because it parsed the new closing line. Hook and sync must therefore land together.
- [x] 2.2 Replace `.githooks/pre-commit` with the check-only hook from design D1 and D2:
  - `set -e`;
  - `mktemp -d` with a `trap` cleanup;
  - `git checkout-index --all --prefix="$snap/"`;
  - `python3 "$snap/scripts/sync_shared.py" --check`;
  - on failure, the check's output plus the D2 message on stderr, then `exit 1`.

  Keep the file mode at 100755, and keep the header comment naming activation (`poe setup`) and CI as the backstop. Verify: `uv run pytest tests/unit/test_commit_hook.py -v` is green, all cases pass, and `git ls-files -s .githooks/pre-commit` shows mode `100755`.
  - *Done 2026-10-13:* 6 passed; mode 100755, and `git diff --summary` shows no mode change.

## 3. Official reference validator (design D4–D7)

- [x] 3.1 Write `tests/unit/test_conform.py` (offline; it starts no process) before touching the script. It asserts:
  - the pinned SHA matches `^[0-9a-f]{40}$`;
  - the `--from` source equals `git+https://github.com/agentskills/agentskills@<SHA>#subdirectory=skills-ref`;
  - every `--with` requirement is an `==` pin;
  - the child environment sets `PYTHONUTF8=1`;
  - `main()` returns 0 when every validation passes, 1 when one fails (naming that skill), and 2 with uv install guidance when `shutil.which("uvx")` is `None`;
  - no tracked file outside `openspec/changes/archive/` contains `skills-ref@` or `npx -y skills-ref`.

  Verify: the module is red against the current `conform.py`.
  - *Done 2026-10-13.* The module starts no validator. Its tracked-file scan uses `git ls-files`, which made it the third copy of that call, so it was extracted to `tracked_files()` in `tests/helpers.py`; `test_model_ids.py` and `test_repo_conventions.py` now use the helper. The scan exempts all of `openspec/changes/` (active and archived change records document the switch) and the test file itself. Red: 8 of 8 failed against the old script: no `SKILLS_REF_COMMIT`, no `command`, no `shutil`, and the scan flagged `scripts/conform.py: skills-ref@`.
- [x] 3.2 Rewrite `scripts/conform.py`:
  - constants: the agentskills URL, `SKILLS_REF_COMMIT = "69ef37e9424c0a7ea9dd2293b559e43ec8176379"` (agentskills `main`, resolved 2026-10-13), and `SKILLS_REF_DEPS = ("strictyaml==1.7.3", "click==8.3.1")` from that revision's `skills-ref/uv.lock`;
  - a command builder for `uvx --from … --with … skills-ref validate <dir>`;
  - `env={**os.environ, "PYTHONUTF8": "1"}`;
  - a missing-`uvx` exit 2;
  - a summary line naming the short SHA.

  The docstring names the validator as the standard maintainers' Python `skills-ref` from the standard's own repository, says the npm package of the same name is an unrelated port, and gives the bump procedure: `git ls-remote https://github.com/agentskills/agentskills main`, the dependency versions from `skills-ref/uv.lock` at that SHA, then `uv run poe conform`, as one reviewed commit. Keep the `main(argv)` signature. Verify: `uv run pytest tests/unit/test_conform.py` is green, and `uv run poe conform` prints `Valid skill:` for all 11 skills and a closing line that names `69ef37e`, with exit 0.
  - *Done 2026-10-13.* `test_conform.py` passes 8/8. `uv run poe conform` printed `Valid skill:` × 11 and `all 11 skills conform (agentskills skills-ref @ 69ef37e)`, exit 0. Two deviations from the plan:
    - `command()` takes the uvx path that `shutil.which` resolved, so Windows starts `uvx.exe` by its full path.
    - The child decodes its output as UTF-8.

    The pinned command still rejects the seeded probes (`Unexpected fields in frontmatter: foo…`, `Invalid YAML in frontmatter: While scanning…`).
- [x] 3.3 Update the comment on `conform` in `pyproject.toml` to name the official validator and say that the first run needs network for the uv cache (a git clone of agentskills plus wheels) and later runs work offline. Verify: `uv run poe conform` passes a second time with `UV_OFFLINE=1`.
  - *Done 2026-10-13:* with `UV_OFFLINE=1`, `poe conform` exited 0 with 11 `Valid skill:` lines.

## 4. Documentation

- [x] 4.1 Update `AGENTS.md`:
  - Commands block: `(pre-commit sync hook)` becomes `(pre-commit drift check)`.
  - "Never edit generated copies": add that the pre-commit hook refuses a commit whose staged copies have drifted and never stages them itself.
  - Git rule: a refused commit is fixed by running `python3 scripts/sync_shared.py` and staging what it lists, never by `--no-verify`.
  - "Skill header pattern" materialization paragraph: "the same script, hook, and `--check` that materialize the file copies" becomes wording in which the script materializes and `--check` (in `poe test`, CI and the hook) guards.
  - "The Agent Skills standard": the validator is the maintainers' Python `skills-ref` from `github.com/agentskills/agentskills`, pinned by commit in `scripts/conform.py`; the pin bump stays the reviewed step.

  Verify: `git grep -n "pre-commit sync hook\|hook, and \`--check\` that materialize" -- AGENTS.md` finds nothing, and `uv run pytest tests/unit/test_model_ids.py` (which reads `AGENTS.md`) stays green.
  - *Done 2026-10-13:* the grep finds nothing, and `test_model_ids.py` is green.
- [x] 4.2 Update `README.md`:
  - The contributor bullet on `shared/`: the hook checks the staged copies and refuses a stale commit instead of re-materializing and staging.
  - "The Agent Skills standard": name the official validator and its commit pin.

  Update `CONTRIBUTING.md` setup step 2 the same way. Verify:
  - `git grep -n "re-materializes and stages\|regenerates synced copies\|version-pinned in" -- README.md CONTRIBUTING.md` finds nothing;
  - `python3 scripts/sync_shared.py --check` is clean, since `README.md` carries a materialized prompt region;
  - `uv run pytest tests/unit/test_install_docs.py` stays green.
  - *Done 2026-10-13:* the grep finds nothing, `--check` reports `generated copies in sync`, and `test_install_docs.py` and `test_model_ids.py` pass (37 tests). The README's setup sentence now names `uv run poe setup` first.

## 5. Verification and landing

- [x] 5.1 Gate: `uv run poe test` (pytest, ruff, drift and conform with the new pin), `uv run poe cov` at or above the floor, `uv run poe specs`, and `openspec validate fix-sync-hook-and-validator --strict`, all green. Record the pass counts and coverage here.
  - *Done 2026-10-13, uncommitted tree on `main` at 2188f45:*
    - `uv run poe test`: exit 0. 3475 passed, 2 skipped. Ruff: `All checks passed!`. Drift: `generated copies in sync`. Conform: `all 11 skills conform (agentskills skills-ref @ 69ef37e)`. The first run caught three ruff findings in the new tests, all fixed.
    - `uv run poe cov`: 92.50% (floor 78%). `scripts/conform.py` is at 91%: the missing lines are the usage and no-skills exits. `scripts/sync_shared.py` is at 98%.
    - `uv run poe specs`: 19 passed. The strict validation of the change is valid.
    - `uv run poe test-fast` (parallel): 3310 passed, 2 skipped, so the new tests are xdist-safe.
- [ ] 5.2 Land the change as one commit on `main`, staging explicit paths only. The new hook runs on this commit; confirm with `git show --stat HEAD` that the commit holds exactly the staged paths, and that `git status --porcelain` shows any unrelated working-tree edits as they were before. Do not push: the push is the maintainer's.
- [ ] 5.3 After the maintainer pushes, CI is green and the results are recorded here:
  - `l0` runs `poe test` and resolves the uvx pin on `ubuntu-latest` through setup-uv's `uvx`;
  - `l0-windows` runs `test_conform.py` and skips `test_commit_hook.py` with its stated reason.
- [ ] 5.4 Archive with the `openspec-archive-change` skill. Verify that `openspec/specs/skill-packaging/spec.md` carries "Commit-time drift check" and no longer "Commit-time sync automation", that `openspec/specs/standard-conformance/spec.md` carries the reference-validator definition, and that `uv run poe specs` is green.
