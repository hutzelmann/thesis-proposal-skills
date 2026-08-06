## 1. Lint configuration

- [x] 1.1 Extend `[tool.ruff.lint] select` with `C90`, `PLR0912`, `PLR0915`, `SIM`, `RET`, `C4`, `PTH`, `ARG`, `PT`, `RUF`; add `[tool.ruff.lint.mccabe] max-complexity = 12`
- [x] 1.2 Reduce `ignore` to `RUF001`, `RUF002` (deliberate typographic unicode in user-facing prose), with a comment stating why; remove `E501` and `E741`
- [x] 1.3 Add `[tool.ruff.lint.per-file-ignores]` parking the structural findings, each entry commented with the change that clears it: `ARG001` for `harness/skill_evals.py` (→ consolidate-test-scaffolding); `C901`/`PLR0912`/`PLR0915` for the three `check.py` copies (→ structure-check-findings), `harness/matrix.py`, `harness/l1_checks.py`, `skills/proposal-troubleshoot/scripts/collect.py` (→ consolidate-test-scaffolding)
- [x] 1.4 Verify the parked set is exactly the structural findings and nothing mechanical slipped in: `uv run ruff check .` reports zero findings only after section 2 completes

## 2. Mechanical fixes

- [x] 2.1 Apply the safe autofixes: `uv run ruff check --fix .` (RUF100 stale `noqa`, RUF005, SIM300, SIM905, PT001)
- [x] 2.2 Rename the 19 `E741` `l` loop variables to `line` (or `lineno` where the value is an index) across `harness/`, `scripts/`, `skills/`, `tests/`
- [x] 2.3 Replace `zip(xs, xs[1:], strict=False)` with `itertools.pairwise` where RUF007 fires
- [x] 2.4 Split the 28 `PT018` composite assertions into one assertion per claim so failures name the half that broke
- [x] 2.5 Prefix unused stub parameters with `_` in `tests/unit/test_validate_refs.py`, `test_lit_parsers.py`, `test_troubleshoot_collect.py` (ARG001/ARG005)
- [x] 2.6 Fix the remaining findings: `PT006` parametrize name types, `RUF043` raises pattern, `RUF059` unused unpacked variables, `SIM103`, `RET` findings
- [x] 2.7 Rewrap the 63 lines exceeding 100 columns at sentence or argument boundaries
- [x] 2.8 Edit `skills/proposal-check/scripts/check.py` as the sync source only, then run `python3 scripts/sync_shared.py`; never hand-edit the `proposal-import` / `proposal-write` copies

### Findings from section 2

Two autofixes degraded deliberate formatting and were reverted by hand:

- `SIM905` flattened `harness/l1_checks.py`'s provenance stopword list — prose wrapped at
  sentence width, read and amended by hand — into a single 1517-character list literal. It
  is now a named `_PROVENANCE_STOPWORD_TEXT` constant that is `.split()`, which satisfies
  the rule (the rule only fires on a literal) without making the word list unreviewable.
- `RUF005` collapsed `publish.py`'s LaTeX pandoc arguments onto one 179-character line,
  losing the flag/value pairing. Restored as a multi-line list with `*base` unpacking.

The lesson for the follow-up changes: `ruff --fix --unsafe-fixes` across a whole tree needs
its diff read, not just its exit code. Both cases were caught by `E501` firing on the
result, which is an argument for keeping that rule enabled rather than raising the limit.

## 3. Pytest configuration

- [x] 3.1 Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]`, `addopts = "--strict-markers --strict-config"`, `markers = ["slow: spawns pandoc or typst"]`, `filterwarnings = ["error"]`
- [x] 3.2 Add `pythonpath` covering `harness`, `scripts`, and the skill script directories the tests import from, so the follow-up change can delete the `sys.path.insert` preambles
- [x] 3.3 Mark the pandoc/typst-spawning tests with `@pytest.mark.slow`: `test_export_matrix.py` (the builder matrix and the three typst-source content tests), `test_author_intext.py`, `test_todo_filter.py`, `test_rq_filter_citations.py`
- [x] 3.4 Confirm `filterwarnings = ["error"]` leaves the suite green — it does; no `ignore` entry was needed

`pythonpath` lists `skills/proposal-lit-search/scripts` before `skills/proposal-import/scripts`
deliberately: both ship `common.py` and `crossref.py`, and the lit-search pair is the sync
source while import's is the generated copy.

## 4. Coverage and fast lane

- [x] 4.1 Add `pytest-cov` and `pytest-xdist` to the `dev` dependency group
- [x] 4.2 Add `[tool.coverage.run]` with `source = ["harness", "scripts", "skills"]` and `omit` for `harness/skill_evals.py` and `harness/claude_runner.py` (metered-only, never executed at L0), each with a comment
- [x] 4.3 Add a `cov` poe task running the suite with `--cov --cov-report=term-missing --cov-fail-under=70`
- [x] 4.4 Add a `test-fast` poe task: `pytest -n auto -m "not slow"`; leave `poe test` running everything so the gate stays complete
- [x] 4.5 Record the measured baseline in this file

### Measured baseline

- Coverage with the metered-only modules omitted: **75.32%**, against a 70% floor.
  (60% before the omissions — that figure counted 497 statements of eval definitions
  that no L0 test can execute by design.)
- `poe test`: 567 tests, ~150s. `poe test-fast`: 454 tests, **2.6s**.
- `skills/proposal-check/scripts/check.py` and `scripts/sync_shared.py` still report **no
  coverage at all** despite being covered by passing tests, because every one of those
  tests spawns a subprocess. This is the concrete measurement behind the `main(argv)`
  convention and the reason `structure-check-findings` exists.

## 5. House style

- [x] 5.1 Add a "Python conventions" section to `AGENTS.md`: `main(argv: list[str] | None = None) -> int` on every script; verdict functions return `(passed, explanation)` and live in `harness/l1_checks.py`; tests import through `conftest.py`, never `sys.path.insert`; findings are dataclasses, not prefixed strings; extract at the third repetition; complexity cap and how exceptions are annotated
- [x] 5.2 State in that section that each rule is enforced by a linter rule or an L0 test, and name which — including the explicit note that the `main(argv)` and no-`sys.path` guards arrive with `consolidate-test-scaffolding` and are convention only until then
- [x] 5.3 Note in `AGENTS.md` Commands that `poe test` is the complete gate, `poe test-fast` the inner loop, and `poe cov` the coverage floor

## 6. Verification

- [x] 6.1 `uv run poe test` green: 567 tests passing, ruff clean, no generated-copy drift
- [x] 6.2 `uv run poe cov` green against the 70% floor (75.32%)
- [x] 6.3 `openspec validate --all --strict` passes (17 items)
- [x] 6.4 Confirmed no user-facing string changed: every string edit under `skills/` is a concatenation split that reconstructs the identical text, and `test_fixture_oracles.py` pins those strings exactly and passes. The only new bytes users see are the two-line GENERATED banner, split so it fits the line-length limit whatever the source path is.
- [x] 6.5 Commit the change
