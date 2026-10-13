# Tasks

## 1. Confirm the runtime path already matches the delta (no edits, design D2)

- [x] 1.1 Confirm that `skills/proposal-troubleshoot/SKILL.md` rung 1 carries the model-subject pin (the model that produced the failure, your own or the one the user names) and the model-rule pin (a date stamp with year, month and day). Verify with `uv run pytest tests/unit/test_pinned_sentences.py -q`, which must pass with no file changed under `skills/`.
- [x] 1.2 Confirm that `MODEL_DATE_RE` in `skills/proposal-troubleshoot/scripts/collect.py` strips a compact, `@`-prefixed or dashed year-month-day stamp and nothing shorter. Verify with `uv run pytest tests/unit/test_troubleshoot_collect.py -q -k "cloud_and_variant or no_wider"`, which must pass unchanged.

## 2. Pin the snapshot assumption's boundaries (design D4, D5)

- [x] 2.1 Add one test to `tests/unit/test_troubleshoot_collect.py` on a `write_support` file of synthetic `lab/example-*` keys. It asserts three things: an undated spelling resolves to a single dated key of the same version; two dated keys of one version resolve to `(None, {})`; and a key with a short snapshot token (`-0813`) resolves from its own spelling but not from the spelling without the token. Verify that it passes with `collect.py` unchanged.

## 3. Gates

- [x] 3.1 Run `uv run poe specs` and verify that every item passes `--strict`, this change included.
- [x] 3.2 Run `uv run poe test` and verify that the whole L0 chain is green: pytest, ruff, drift check and conformance.

## 4. Archive and commit

- [ ] 4.1 Archive through the `openspec-archive-change` skill. Verify that `openspec/specs/skill-troubleshoot/spec.md` now defines the running model as the model that produced the failure, names the year-month-day date stamp, and holds the two new scenarios. Also verify that `grep -nE 'claude|gpt-|deepseek|qwen|kimi|gemini' openspec/specs/skill-troubleshoot/spec.md` prints nothing (archived D8).
- [ ] 4.2 Re-run `uv run poe specs` and `uv run poe test` on the archived tree, then make one commit for the change on the worktree branch. Merging to `main` and pushing stay with the maintainer.
