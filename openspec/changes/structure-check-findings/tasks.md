## 1. Capture the baseline

- [x] 1.1 Render the human report for all 25 fixture proposals with the pre-change script and store the output
- [x] 1.2 Record each fixture's exit code alongside its report

## 2. Findings as values

- [x] 2.1 Add a frozen `Finding` dataclass (`level`, `rule`, `message`), the `error`/`warn` constructors, and `RULE_IDS` — the closed set of 42 identifiers, grouped and commented in one place
- [x] 2.2 Convert the accumulators to `list[Finding]`, keeping every message string exactly as it was
- [x] 2.3 Render the report from the findings in `render_report`, preserving both buckets, the `- ERROR:` / `- WARNING:` prefixes, the digest line, and the deferred-to-the-agent note verbatim

## 3. Rules as functions

- [x] 3.1 Split `check()` into 16 rule functions over a `Context` derived once
- [x] 3.2 Put them in the `RULES` registry, whose order is the report's order
- [x] 3.3 Verify byte-identity against the 1.1 baseline for all 25 fixtures, with matching exit codes
- [x] 3.4 Confirm the file passes `C901`/`PLR0912`/`PLR0915` at the repository cap with no exemption

`check()` survives as a four-line wrapper returning the two message lists, because
`harness/l1_checks.py` and the eval scorers still read that shape. `check_findings()` is the
new primary entry point.

One ordering bug was introduced and caught by the byte-identity check before it could ship:
validating the timeline mode inside `build_context` moved `timeline-detail-unknown` ahead of
the metadata errors. It is now `rule_timeline_mode` in its proper registry slot, with the
context falling back to the default silently. This is exactly what the baseline was for.

## 4. Structured output

- [x] 4.1 Add `--json`, emitting `file`, `digest`, `exit_code`, and `findings` with level, rule, and message
- [x] 4.2 Confirm the exit code is identical with and without `--json`, and that warnings alone still exit 0
- [x] 4.3 Confirm `--json` suppresses the human report and emits parseable JSON

## 5. Consumers stop grepping prose

- [x] 5.1 Add `disallowed_rules(findings, allowed=("min-references",))` to `harness/l1_checks.py`
- [x] 5.2 Keep `disallowed_errors` for the eval scorers, which read the script's stdout from inside a sandbox where the JSON mode is not reachable — both paths documented as to which is which
- [x] 5.3 Add a `check.rules` block to all 25 oracles, generated from `--json` and reviewed as a diff
- [x] 5.4 `test_fixture_oracles.py` now asserts both: `errors_contain` fragments as before, plus exact set equality on the rule identifiers

The identifier assertion is exact set equality, unlike the fragment assertions, so a check
that stops firing fails even when its message text still appears elsewhere in the report.
That was the specific hole the fragments left.

## 6. Per-rule tests

- [x] 6.1 `tests/unit/test_check_rules.py` — 30 tests calling the rules directly
- [x] 6.2 `test_every_declared_identifier_is_reachable`: every id in the closed set is produced by a fixture oracle or by a named unit test, with the unit-test set listed explicitly rather than the assertion weakened to a subset check
- [x] 6.3 `test_rule_identifiers_are_unique`, plus `test_every_emitted_identifier_is_declared` for the inverse — a rule may not invent an id outside the set

6.2 found `title-too-long` reachable by no fixture and no test; a case was added rather than
the identifier removed, since the rule is live.

## 7. Cleanup and verification

- [x] 7.1 `[tool.ruff.lint.per-file-ignores]` is gone — the repository now carries no lint exemption at all
- [x] 7.2 `python3 scripts/sync_shared.py` regenerated the import and write copies
- [x] 7.3 `uv run poe test` green: 756 tests, ruff clean, no drift. `uv run poe cov` at 82.04% against the 78% floor
- [x] 7.4 `openspec validate --all --strict` passes
- [x] 7.5 Commit and archive

### Measured

| | before | after |
|---|---|---|
| `check()` | 252 lines, 72 locals, 64 branches, 140 statements | 16 rule functions, all under the cap |
| lint exemptions | 3 files | **none** |
| tests | 700 | 756 |
| coverage | 81% | 82% |
| `check.py` coverage | 93% | 97% |

Acceptance evidence: the human report is byte-identical for all 25 fixtures across all three
shipped copies of the script (`proposal-check`, and the generated `proposal-import` and
`proposal-write` copies), with unchanged exit codes.
