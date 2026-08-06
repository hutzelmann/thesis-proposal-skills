## 1. Script entry points

- [x] 1.1 Give every script in `harness/`, `scripts/`, and `skills/*/scripts/` the signature `main(argv: list[str] | None = None) -> int`, passing `argv` to `parse_args`; leave `sys.argv` to the `__main__` block only
- [x] 1.2 Split `harness/matrix.py`'s `main` into the steps it already runs in sequence (`build_parser`, `print_estimate`, `confirm_spend`, `run_matrix`, `collect_usage`, `record_spend`)
- [x] 1.3 Split `skills/proposal-troubleshoot/scripts/collect.py`'s `main` into a `Plan` object, `plan_bundle`, `write_bundle`, and `clear_existing`, keeping `--dry-run` as the path that stops after planning
- [x] 1.4 Verify both files pass `C901`/`PLR0912`/`PLR0915` with their `per-file-ignores` entries removed

`validate_refs.py` gained an `argparse` parser: it read `sys.argv[1]` directly, so a missing
argument raised `IndexError` instead of a usage message. That is a strict improvement and no
test depended on the old behaviour.

`print_estimate` is deliberately separate from `confirm_spend`. Folding them together forced
`--estimate-only` to fake a `yes=True` namespace to reuse the printing half — the estimate is
always shown, and only the prompt is conditional.

## 2. Test scaffolding

- [x] 2.1 Add `tests/conftest.py` (fixtures) and `tests/helpers.py` (plain callables)
- [x] 2.2 Delete every `sys.path.insert` and the `# noqa: E402` it forced from the 12 test files that carried them
- [x] 2.3 Convert the check-script test sites to the in-process `run_check` helper: `test_check.py`, `test_timeline_section.py`, `test_title_tells.py`
- [x] 2.4 Keep `test_fixture_oracles.py` on its subprocess call, and add an explicit CLI-entry test to `test_sync.py`, so the interpreter boundary stays covered
- [x] 2.5 Convert `test_sync.py` and `test_validate_refs.py` and `test_support_matrix.py`'s matrix cases to in-process `main(argv)` calls

Correction to the plan: 2.3 originally listed six files. Only three spawn `check.py`;
`test_author_intext.py`, `test_todo_filter.py` and `test_rq_filter_citations.py` spawn
`pandoc`, which is an external tool and correctly stays a subprocess.

The split between `conftest.py` and `helpers.py` was not in the design: `run_check` as a
fixture would have forced itself into the signature of roughly forty tests for no gain, since
it needs nothing pytest provides. Fixtures live in `conftest.py`, plain callables in
`helpers.py`, and `tests` joined `pythonpath`.

## 3. Harness structure

- [x] 3.1 Add the `verdict_scorer` adapter and route all fifteen scorers through it
- [x] 3.2 Add the `proposal_task` factory and route the twelve single-turn tasks through it
- [x] 3.3 Write L0 tests for the current inline behaviour of `customize_l1` and `publish_l1` before moving them
- [x] 3.4 Move that logic to `harness/l1_checks.py` as `verdict_customize_override` and `verdict_publish`, keeping the fixture-specific constants as defaulted parameters
- [x] 3.5 Remove the `harness/skill_evals.py` `ARG001` entry and confirm the findings are gone at their source
- [x] 3.6 Add `tests/unit/test_eval_wiring.py`: every task builds, stages one sample, and registers exactly the scorer names it registered before

Three further verdicts came out of the scorers while they were being converted, because they
were the same kind of inline logic: `verdict_notes_progress` (the largest, ~30 lines of
snapshot assertions), `verdict_review_localized`, and `verdict_litsearch_expanded`. All three
now have L0 tests.

The scorer name is the subtle part. `harness/support.py` decides whether a scorer counts
toward a model-support cell by looking for `l1` in its **registered** name, and the adapter
turns that name from a function name into an argument. `test_eval_wiring.py` pins the full
task→scorer-name map so a rename cannot silently change published verdicts.

## 4. Invariant tests

- [x] 4.1 `tests/unit/test_repo_conventions.py`: no file under `tests/` manipulates `sys.path`
- [x] 4.2 Same file: every script `main` takes `argv` with a `None` default — checked with `ast`
- [x] 4.3 Same file: every `verdict_*` in `harness/l1_checks.py` is referenced by a test under `tests/unit/`
- [x] 4.4 Confirmed each fails when violated

4.3 failed on first run and found **six** untested verdicts, three of them pre-existing:
`verdict_draft`, `verdict_review`, `verdict_seed`, plus the three extracted in section 3.
All six now have tests — that is 33 assertions of behaviour that previously only a metered
eval run could exercise. The guard paid for itself before it was committed.

4.4 was verified by deliberate violation: a `sys.path.insert` appended to
`test_lit_common.py` failed the import guard, and stripping `argv` from `harness/report.py`
failed the signature guard. Both were reverted.

## 5. Configuration and docs

- [x] 5.1 Remove the cleared `per-file-ignores` entries (`skill_evals.py`, `matrix.py`, `collect.py`, and the stale `l1_checks.py` entry the previous change had already fixed); only the three `check.py` copies remain, owned by `structure-check-findings`
- [x] 5.2 Raise `--cov-fail-under` from 70 to 78
- [x] 5.3 Replace the "convention only until then" sentence in `AGENTS.md` with the tests that now enforce each rule

The floor is 78, not the 80 the design named. 81% is the measured figure, and a floor one
point below it turns every unrelated change into a coverage negotiation — the same reasoning
the design gave for not tuning the floor to the current commit.

### Measured

| | before | after |
|---|---|---|
| tests | 567 | 700 |
| coverage (metered-only omitted) | 75% | **81%** |
| `check.py` | not measured at all | 93% |
| `sync_shared.py` | 0% (tests passing) | 90% |
| `l1_checks.py` | 91% | 99% |
| `poe test-fast` | — | 587 tests, 4.0s |

## 6. Verification

- [x] 6.1 `uv run poe test` green: 700 tests, ruff clean, no generated-copy drift
- [x] 6.2 `uv run poe cov` green at 81.13% against the 78% floor
- [x] 6.3 `openspec validate --all --strict` passes (17 items)
- [x] 6.4 No behavior change under `skills/`: signature and structure edits only, no output string or exit code altered; the fixture oracles and the 86 check tests pass unchanged
- [x] 6.5 Commit and archive

### Defect found by the fast lane

Running the suite in parallel exposed a pre-existing race that serial execution had hidden:
`test_check_detects_tampering` edits tracked files in place to provoke a drift report, while
`test_copies_in_sync` reads those same files. On separate xdist workers they interleave and
the in-sync check fails. Fixed with `@pytest.mark.xdist_group` plus `--dist loadgroup`, which
keeps them on one worker; verified stable over three consecutive runs. Worth recording: the
race was always there, and the only reason it was never seen is that nothing had ever run the
suite concurrently.
