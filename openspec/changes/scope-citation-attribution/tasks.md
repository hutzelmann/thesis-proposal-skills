# Tasks

## 1. Measurement instruments (first commit, no behaviour change)

- [x] 1.1 Add `citation_blocks`, `repeated_citation_runs`, `verdict_citation_runs` and `verdict_citation_repair` to `harness/l1_checks.py` (design D4); verify with new L0 tests covering: identical key set on adjacent sentences fails with its line; key-set change (`[@a]` → `[@a; @b]`) passes; paragraph break resets; "et al." / "z. B." do not split sentences; metadata block ignored; repair fails when a key cited in the input is cited nowhere in the output
- [x] 1.2 Create synthetic fixture `tests/fixtures/w08-rich-seed/` (design D5: ideate-style seed, eleven references, one central source with several note-form findings, fresh topic, fake DOIs); calibrate `expected.json` against `skills/proposal-check/scripts/check.py` and verify the fixture-oracle tests pass
- [x] 1.3 Create synthetic fixture `tests/fixtures/f27-citation-runs/` (design D5: complete proposal, one key on four consecutive sentences, a two-key group on three adjacent sentences, a one-source summary paragraph, result verbs inside the repeated-citation sentences, every reference needed); calibrate `expected.json` and verify the fixture-oracle tests pass and `verdict_citation_runs` fails on it while `verdict_citation_repair(f27, f27)` reports only the runs
- [x] 1.4 Add dev-runner scenarios `write_rich_seed` and `write_repair_citations` to `harness/claude_runner.py` with table-based verdict dispatch (design D6); verify `uv run ruff check harness` stays under the complexity cap and an L0 test exercises the dispatch on staged fixture text without a model
- [x] 1.5 Add `harness/rubrics/citation_practice.txt`, the `CRITERIA` entries and Inspect tasks `write_rich_seed` / `write_repair_citations` with scorers `<task>_l1`, `<task>_l2_citation_scope`, `<task>_l2_synthesis` to `harness/skill_evals.py`; update `tests/unit/test_eval_wiring.py`, regenerate the `proposal-write` `evals/evals.json` projection, and verify the projection drift test passes
- [x] 1.6 Document both scenarios and tasks in `harness/README.md` (on-demand measurement instruments, not matrix tasks); verify `uv run poe test` is green and commit the instruments as the branch's first commit

## 2. Baseline measurement

- [ ] 2.1 Run the dev runner on the instruments commit: sonnet and haiku × `write_rich_seed` and `write_repair_citations` × 3 runs (subscription, `--keep`); record per-run L1 verdicts, repeated-run counts, host version and kept workspace paths in `measurement.md`

## 3. Stage A — rule text and hindsight

- [x] 3.1 Replace the consecutive-citation bullet in `shared/guidelines/guidelines.md` "Literature and Citations" with the attribution-scope rule (design D1, guidance-model "Citation scope"); run `python3 scripts/sync_shared.py` and verify `python3 scripts/sync_shared.py --check` reports no drift
- [x] 3.2 Extract the citation-key pattern and a `citation_keys` helper in `skills/proposal-check/scripts/check.py`, used by `scan_citations` and the hindsight rule (design D3); verify all existing fixture oracles still pass unchanged
- [x] 3.3 Rewrite `rule_hindsight_leakage` to walk prose blocks with cue-anchored attribution runs and the extended message (design D2, skill-check "Hindsight leakage reported as a warning"); verify with L0 tests for every spec scenario: cited, cued continuation (EN and DE), uncued continuation, run ended by paragraph, run broken by an own sentence, planned measurement, "It was shown" / "Es zeigte sich" / "This study" not accepted as cues
- [x] 3.4 Sync the generated `check.py` copies and verify `uv run poe test` is green, including the shared-input tests that pin `l1_checks` block splitting to `check.py`'s
- [x] 3.5 Commit stage A

## 4. After measurement

- [ ] 4.1 Re-run the 12 dev runs of 2.1 on the stage-A commit; record results beside the baseline in `measurement.md`
- [ ] 4.2 Show the Inspect cost estimate for sonnet and haiku × both tasks × 2 epochs and wait for the user's approval (pipeline stop 1); run, then record L1/L2 scores, judge explanations and actual cost in `measurement.md`
- [ ] 4.3 Evaluate the bar (design D7): L1 cells solid on both models; L2 citation scope passing on both epochs for both models; L2 synthesis passing on both epochs for sonnet, haiku reported; record the verdict per criterion in `measurement.md`

## 5. Ladder (only if 4.3 fails — routed by failing criterion)

- [ ] 5.1 If repetition fails: amend the change via `openspec-update-change` (skill-check warning class, guidance-model formalization boundary), add the `citation-repeated` warning to `check.py` with L0 tests and a trip/pass oracle pair (f27 trips, f00 passes), sync, re-run the L1 dev runs and record; otherwise mark this task N/A in `measurement.md` with the reason
- [ ] 5.2 If scope or synthesis fails on sonnet: amend the change via `openspec-update-change` (skill-write requirement), add the pinned drafting clause to `skills/proposal-write/SKILL.md`, sync, re-run the affected runs and record; otherwise mark N/A with the reason
- [ ] 5.3 If the bar still fails after 5.2: stop escalating and record the outcome as it stands in `measurement.md`

## 6. Review and close

- [ ] 6.1 Run the pre-commit adversarial verification over the branch diff (spec conformance, regressions, fixture synthetic-ness, generated-copy drift); fix confirmed findings and verify `uv run poe test` and `uv run poe specs` are green
- [ ] 6.2 Present the measurement table and two to three before/after paragraphs from kept workspaces to the user (pipeline stop 2) and record the verdict in `measurement.md`
- [ ] 6.3 After approval: archive the change with `openspec archive`, commit, merge the branch into `main`, re-run `python3 scripts/sync_shared.py` and `uv run poe test` on `main`; no push
