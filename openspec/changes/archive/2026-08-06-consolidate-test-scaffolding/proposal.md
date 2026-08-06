## Why

`enforce-python-standards` put a gate in place and measured what is behind it. Three
numbers from that measurement drive this change:

- Twelve test files open with the same four-line `sys.path` preamble and the `# noqa: E402`
  it forces. The preamble is self-propagating: the next test file is written by copying the
  last one.
- `skills/proposal-check/scripts/check.py` — the most-asserted script in the repository —
  contributes **zero** measured coverage, because all seven of its test sites spawn it as a
  subprocess. `scripts/sync_shared.py` reports 0% for the same reason while its tests pass.
- Fifteen scorers in `harness/skill_evals.py` repeat the same six-line adapter, and two of
  them (`customize_l1`, `publish_l1`) hold their verdict logic inline instead of in
  `harness/l1_checks.py`. Those two are the only verdicts in the repository with no L0 test
  — the module docstring promises the opposite.

The gate cannot catch any of this on its own: a linter has no rule for "this file re-derives
what a conftest should provide". So this change removes the duplication and then pins the
result with L0 tests, the same way `test_skill_header_pattern.py` pins the skill headers.

## What Changes

- **`tests/conftest.py` becomes the single import and fixture root.** It provides the repo
  and fixture paths, a `run_check` helper, and a factory fixture for the copy-fixture-into-
  `tmp_path`-and-mutate pattern that appears more than fifty times in `test_check.py` alone.
  Every `sys.path.insert` and its `# noqa: E402` is deleted; `pythonpath` already carries
  the import roots.
- **Every script exposes `main(argv: list[str] | None = None) -> int`.** Fourteen of the
  sixteen currently read `sys.argv` implicitly. Tests then call them in-process, which is
  what makes their lines measurable. One subprocess test per script stays, to prove the CLI
  entry point itself works.
- **`matrix.main()` and `collect.main()` are split** into the steps they already perform in
  sequence (estimate / confirm / run / record; plan / write). Both currently exceed the
  complexity cap and are parked in `per-file-ignores`; this change clears those entries
  rather than carrying them.
- **`skill_evals.py` gets two factories**: a `verdict_scorer` adapter that turns a
  `(passed, explanation)` function into an Inspect scorer, and a `proposal_task` builder for
  the twelve near-identical `@task` bodies. This removes the 33 `ARG001` findings at their
  source — one adapter signature instead of fifteen — so that parked entry goes too.
- **`customize_l1` and `publish_l1` move to `l1_checks.py`** as `verdict_customize_override`
  and `verdict_publish`, each with L0 tests, closing the coverage gap that let them ship
  untested.
- **Three invariant tests** enforce what the linter cannot: no `sys.path` manipulation under
  `tests/`, `main(argv)` on every script, and an L0 test for every `verdict_*` function.
  These are the guards `AGENTS.md` currently describes as convention-only.
- **Coverage floor rises** to match what the in-process calls make visible.

No behavior changes: no skill instruction, script output, report format, or eval verdict is
touched. The scorers compute the same verdicts from the same inputs; the scripts print the
same text and return the same exit codes.

## Capabilities

### New Capabilities

None — `.openspec.yaml` sets `skip_specs: true`.

### Modified Capabilities

None. Test scaffolding, script entry-point signatures, and internal harness structure are
implementation, not behavior. Every requirement in `openspec/specs/` describes what the
skills do for a user, and none of that changes.

## Impact

- New `tests/conftest.py`; all 29 test files under `tests/unit/` lose their preambles, and
  the check-script tests move from `subprocess.run` to in-process calls.
- `main(argv)` signatures across `harness/`, `scripts/`, and `skills/*/scripts/`.
- `harness/skill_evals.py` roughly halves; `harness/l1_checks.py` gains two verdicts.
- `pyproject.toml`: three `per-file-ignores` entries removed (`skill_evals.py` ARG001,
  `matrix.py` and `collect.py` complexity, plus the now-stale `l1_checks.py` entry whose
  finding the previous change already fixed), and a raised `--cov-fail-under`.
- `AGENTS.md`: the "convention only until then" note is removed once its guards exist.
- The complexity entries for the three `check.py` copies stay, and are cleared by
  `structure-check-findings`.
