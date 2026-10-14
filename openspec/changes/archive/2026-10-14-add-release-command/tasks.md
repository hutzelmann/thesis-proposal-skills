# Tasks

## 1. Command

- [x] 1.1 Add the pure functions from design D1–D4 to `scripts/changelog.py` (`bump_for`, `cut`, `set_project_version`, `set_lock_version`, `readiness_problems`, `model_support_line`, prose model names). Verify: ruff is clean and complexity is ≤ 12.
- [x] 1.2 Add the `release` subcommand (`--bump`, `--version`, `--date`, `--dry-run`) with the D5 refusals, write order, stamp, check, commit of explicit paths, and annotated tag. It prints the push and `gh release create` commands. Add `release = "python3 scripts/changelog.py release"` to `[tool.poe.tasks]`. Verify: `uv run poe release --dry-run` on the real tree prints 0.9.0 with its reasoning and leaves `git status` unchanged.

## 2. Tests

- [x] 2.1 `tests/unit/test_changelog_release.py`:
  - the bump table, including that a requested bump lower than the entries need is refused;
  - `cut` round-trips through `check`;
  - the version is set in `pyproject.toml` and `uv.lock`;
  - the readiness gate refuses on an open change and on an untested row;
  - the model-support line for added, retired and re-judged models;
  - prose names of every current roster ID stay clear of the model-ID guard's pattern;
  - an end-to-end release in a temporary git repo creates exactly one commit and one annotated tag, and touches nothing else.

  Verify: `uv run pytest tests/unit/test_changelog_release.py`.

## 3. Docs

- [x] 3.1 In `harness/README.md` "Audit pre-flight (publish pipeline)", replace the manual bump/stamp/commit step with `uv run poe release`, and add one line naming the 1.0.0 readiness gate. Update the `scripts/stamp_version.py` docstring to name its caller. Verify: `uv run pytest tests/unit -k "readme or harness_readme or stamp"` passes.

## 4. Gate

- [x] 4.1 `uv run poe test` and `uv run poe specs` pass; `openspec validate add-release-command --strict` is valid.
- [x] 4.2 Archive after `add-changelog` (whose `release-history` capability this extends), then commit once for this change.
