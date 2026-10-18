# Tasks

## 1. Guard first

- [x] 1.1 Rewrite `tests/unit/test_script_paths.py` per design D3: forbid `${CLAUDE_SKILL_DIR}` and any `${…}` or `$VAR/scripts/` reference in shipped `SKILL.md` files, require every `python3 …scripts/…` invocation to start with `<skill-dir>/scripts/`, and find the fallback paragraph by the D2 definition marker instead of "leaves it unexpanded". Keep the interpreter-clause, workspace-root, `<location>` and no-relocation guards. Update the module docstring. Verify that `uv run pytest tests/unit/test_script_paths.py` fails on all eight skills before task 2.1 and passes after it.

## 2. Skills

- [x] 2.1 In the eight script-bearing `SKILL.md` files (check, import, lit-search, publish, reverse, supervise, troubleshoot, write), change every `${CLAUDE_SKILL_DIR}/scripts/` invocation to `<skill-dir>/scripts/`. Open each fallback paragraph with the D2 definition sentence, keeping the per-skill content (workspace-root stake, `<location>`, not-found rule, interpreter clause). Verify that `grep -rn 'CLAUDE_SKILL_DIR' skills/` prints nothing and that task 1.1's tests pass.
- [x] 2.2 Regenerate the evals projections and generated copies (`python3 scripts/sync_shared.py`), and check that no materialized block or pinned sentence changed. Verify that `python3 scripts/sync_shared.py --check` reports in sync and that `tests/unit/test_skill_header_pattern.py`, `test_execution_shape.py`, `test_handoff_block.py`, `test_workspace_files_block.py` and `test_report_offer.py` pass.

## 3. Metered path

- [x] 3.1 Change `harness/skill_evals.py::skill_prompt` per design D4: no substitution in the body, and an intro that gives the base directory in host wording without explaining `<skill-dir>`. Update `harness/README.md`: the sandbox paragraph says skills reach the model unsubstituted with their base directory named, and that matrix logs for script-running tasks before this change are not comparable cell by cell. The Codex and Copilot sections stop saying "expands no `${CLAUDE_SKILL_DIR}`". Verify that `uv run pytest tests/unit/test_eval_wiring.py tests/unit/test_runner_check_root.py` passes and that `grep -n CLAUDE_SKILL_DIR harness/` prints nothing.

## 4. Documentation and spec gate

- [x] 4.1 Add the README divergence row (design D5) and rewrite AGENTS.md's script-path sentence in "The Agent Skills standard" to name `<skill-dir>`, keeping the 2026-07-31 lesson. Verify that `grep -n 'CLAUDE_SKILL_DIR' README.md` prints nothing, that AGENTS.md names the variable only as the form never to use, and that `uv run pytest tests/unit/test_install_docs.py` passes.
- [x] 4.2 Record this change's two MODIFIED requirements in `openspec/long-requirements.json` under `changes/host-neutral-script-paths` at their measured lengths, each no longer than its predecessor (design D6). Verify that `uv run poe specs` passes.
- [x] 4.3 Run the full L0 gate. Verify that `uv run poe test` is green.
  - 2026-10-18: in the shared checkout pytest reported 99 failures, all from 42 untracked files under `tests/fixtures/` (flat-layout proposal copies from before `adopt-proposal-folders`, plus `f16-figures-import/img/`). None of these files is part of this change. On a clean export of HEAD plus this change's diff: 5925 passed, 3 skipped. One `test_copies_in_sync` failure appeared only under an ad hoc `-n auto` run and passed alone (29/29). `ruff check .` is clean, `sync_shared.py --check` reports in sync, and `poe conform` passes (11 skills).

## 5. Live checks (Claude subscription, $0)

- [x] 5.1 `uv run poe dev check_report --model haiku`, then `--model sonnet`. Pass: the script ran (oracle errors reported, file untouched). Record both results here. A haiku failure that traces to the placeholder sends the D2 wording back before archive.
  - 2026-10-18, `--isolated`, harness subscription login. haiku: PASS, 7 turns. Its first Bash call was `python3 .claude/skills/proposal-check/scripts/check.py broken-format/broken-format.md`, so `<skill-dir>` was filled in correctly with no failed attempt. The run reported 6 errors and 5 warnings, and the file was untouched. sonnet: PASS, 5 turns, the same first-call fill-in, the same 6 errors and 5 warnings, and "I changed no file". Both workspaces also held a stray root `broken-format.md` that staging copied from an untracked fixture leftover (see 4.3). Both models flagged it as a duplicate; it did not affect the verdicts.
- [x] 5.2 `uv run poe dev import_messy --model sonnet`. Pass: the imported folder and checks land in the workspace, and nothing is written into the skill directory. Record the result here.
  - 2026-10-18, `--isolated`: PASS. The model set `S=.claude/skills/proposal-import/scripts` from the base directory, then ran `validate_refs.py` and `check.py` from the workspace root. `irrigation-controller/irrigation-controller.md` and `notes.md` landed in the workspace. The skill directory received no artifact. Python's own bytecode cache did appear there (`scripts/__pycache__/common.cpython-313.pyc`, written when `validate_refs.py` imports `common`). That predates this change and is independent of the path form: no shipped script sets `sys.dont_write_bytecode`. It is left for a change of its own.

## Workflow follow-up

- One Codex `check_report` run (`uv run poe dev check_report --host codex --model <name>`) only after the maintainer's explicit go, since it draws on the ChatGPT plan quota.
  - 2026-10-18, run on the maintainer's go: `uv run poe dev check_report --host codex --model gpt-6.1-sol --keep`. Codex CLI 0.160.0, Plus plan, served model `gpt-6.1-sol`. PASS in 23 s with no workspace breach; quota stayed at 0% (5-hour and weekly) before and after, with no credits. Codex read `.agents/skills/proposal-check/SKILL.md`, then ran `python3 .agents/skills/proposal-check/scripts/check.py broken-format/broken-format.md` from the workspace root. So it filled in `<skill-dir>` from the listed SKILL.md path with no failed attempt. It reported the same 6 errors and 5 warnings as the Claude runs and changed no file. The stray root `broken-format.md` from the fixture leftovers (task 4.3) was staged here too.
- Archive gate: archive only after `desktop-first-install` is archived. If that change's `skill-packaging` delta changed in the meantime, redo this change's delta on top of it first (design D6).
- At archive, move the `Changelog:` line under `[Unreleased]` → Changed, and run `python3 scripts/changelog.py check`.
