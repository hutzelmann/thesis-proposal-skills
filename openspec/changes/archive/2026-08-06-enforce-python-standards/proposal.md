## Why

The Python in this repository is almost entirely AI-written, and it has accumulated the
failure modes that come with that: a 250-line `check()` procedure, twelve test files that
each re-derive their own `sys.path` preamble, and two eval scorers whose verdict logic sits
inline where nothing tests it. None of it was caught, because nothing was configured to
catch it. There is no `[tool.pytest.ini_options]` block at all, no coverage measurement, no
type checker, and the lint configuration is partly decorative — `line-length = 100` sits
next to `ignore = ["E501"]`, so it enforces nothing.

The repository already knows how to prevent drift: `scripts/sync_shared.py --check` guards
generated copies, and `tests/unit/test_skill_header_pattern.py` pins skill mandates so a
reword shows up as a reviewable diff. Code structure simply never got the same treatment.
This change gives it that treatment first, so the two refactors that follow land against a
gate rather than into the same vacuum that produced the bloat.

## What Changes

- **Lint gate widened.** Add `C90` (mccabe, `max-complexity = 12`), `PLR0912`, `PLR0915`,
  `SIM`, `RET`, `C4`, `PTH`, `ARG`, `PT`, and `RUF` to `select`. Drop `E741` from `ignore`
  and rename the `l` loop variables it flags — ambiguous in files that index lines by
  number. Drop `E501` from `ignore` and rewrap the 63 lines over the existing 100-column
  limit, so `line-length` becomes a real setting instead of a decorative one.
- **Known violations parked, not hidden.** The structural findings this change does not fix
  (`C901`/`PLR0912`/`PLR0915` on `check()`, `collect.main()`, `matrix.main()`; `ARG001` on
  the 33 Inspect scorer signatures in `harness/skill_evals.py`) go into
  `per-file-ignores`, each annotated with the follow-up change that removes it. New code is
  gated from day one; the backlog is visible in the config rather than absent from it.
- **`RUF001`/`RUF002` ignored globally.** The user-facing report prose deliberately uses
  `—`, `×` and typographic quotes. Ambiguous-unicode warnings are wrong here by design.
- **Pytest gets a configuration.** Add `[tool.pytest.ini_options]` with `testpaths`,
  `pythonpath` (removing the need for `sys.path.insert` in tests), `--strict-markers`,
  `--strict-config`, `filterwarnings = ["error"]`, and a registered `slow` marker.
- **Coverage measured with a floor.** Add `pytest-cov` and a `poe cov` task with
  `--cov-fail-under`, so untested additions fail rather than pass silently — the gap that
  let `customize_l1` and `publish_l1` ship with no L0 coverage.
- **Fast lane.** Add `pytest-xdist`; the `slow` marker plus `-n auto` cuts the 73-second L0
  loop, which is dominated by ~30 pandoc/typst builds in `test_export_matrix.py`.
- **House style written down.** A short "Python conventions" section in `AGENTS.md`:
  `main(argv=None) -> int`; verdict functions return `(passed, explanation)` and live in
  `harness/l1_checks.py`; tests import via `conftest.py`, never `sys.path`; findings are
  dataclasses, not prefixed strings; the third repetition gets extracted. Every rule is one
  a linter or an L0 test can check, so none of it depends on being remembered.

No behavior changes: no skill instruction, script output, report format, or eval verdict is
touched. Renames and rewraps only.

## Capabilities

### New Capabilities

None — `.openspec.yaml` sets `skip_specs: true`.

### Modified Capabilities

None. This change adds tooling configuration, developer documentation, and mechanical
renames. The behavior every existing spec describes is unchanged, so no spec should change
either.

## Impact

- `pyproject.toml`: `[tool.ruff.lint]`, new `[tool.ruff.lint.per-file-ignores]`,
  `[tool.ruff.lint.mccabe]`, new `[tool.pytest.ini_options]`, `dev` dependency group
  (`pytest-cov`, `pytest-xdist`), new `cov` and `test-fast` poe tasks.
- `AGENTS.md`: new "Python conventions" section.
- Mechanical edits across `harness/`, `scripts/`, `skills/*/scripts/`, and `tests/unit/`:
  `l` → `line` renames, 63 line rewraps, composite-assert splits, `_`-prefixed stub
  parameters, `itertools.pairwise`, and other autofixable findings.
- `skills/proposal-check/scripts/check.py` is a sync source; its copies in
  `proposal-import` and `proposal-write` are regenerated with `scripts/sync_shared.py`.
- Follow-up changes remove the parked ignores: the test-scaffolding change clears the
  `ARG001` block, the check-findings change clears the complexity block.
