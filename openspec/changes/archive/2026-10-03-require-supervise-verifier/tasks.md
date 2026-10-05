# Tasks

## 1. Measurement instruments (before any skill change)

- [x] 1.1 Save the host event stream to `.devrun-events.jsonl` in the run's workspace from `harness/claude_runner.py`. Verify: an L0 test that `save_events` writes one JSON object per line and that the workspace `*.md` globs do not see the file.
- [x] 1.2 Add `verdict_supervise_verifier(calls)` to `harness/l1_checks.py`. It passes on an `Agent`/`Task` call whose input mentions the verifier brief (file name or opening marker) and fails on none or on unrelated helpers. Verify: L0 tests cover no helper, an unrelated helper, a brief by path, and a brief by content.
- [x] 1.3 Add `verdict_supervise_verification_declared(review)`. A `Verified by:` / `Geprüft von:` line in the verification section names a fresh verifier or inline checks. Verify: L0 tests in both languages, plus a missing line and a missing section.
- [x] 1.4 Score both verdicts in `supervise_verdict` for the supervise scenarios, passing the events. Verify: dispatch L0 tests on synthetic workspaces and streams.
- [x] 1.5 Baseline, with the skill text as committed in eecd8db: three runs each of `supervise_feedback` and `supervise_scope` on sonnet, `--isolated --keep`. Record the spawn and declaration verdicts, cost, and the agent's stated reason when it skipped (read from the saved stream) in `measurement.md`. Verify: six rows recorded.

## 2. Skill changes

- [x] 2.1 Write `skills/proposal-supervise/references/verifier-brief.md`. It is addressed to the verifier and covers its inputs, the six checks, that the offline checks need no network, the untrusted-data rule, writing nothing, and the return shape. Verify: an L0 test that the file exists and names each of the six checks.
- [x] 2.2 Rewrite `## Execution shape`: shape only, plus the brief named, the offline sentence, and inline allowed only without a subagent tool. Update `proposal-supervise--execution-shape.txt` in the same edit. Verify: `test_execution_shape.py` and `test_pinned_sentences.py` pass.
- [x] 2.3 In Verify before hand-over, add the ordered steps (ledger, start the verifier with the brief, decide and re-check, record) and the `Verified by:` line. Pin the offline sentence as `proposal-supervise--verifier-offline.txt`. The baseline's second skip reason ("I couldn't ask you anything") added a clause: the verifier asks the professor nothing. Verify: pinned-sentence test, plus the body-size test (3,924 of 3,950 words).

## 3. Re-measure and close

- [x] 3.1 Repeat 1.5 on the changed skill. Record the same columns and compare with the baseline against the target of at least 5 spawns in 6 runs. Result: 6 of 6 against 3 of 6. One harness defect surfaced and was fixed: the literature verdict counted the student's own cited DOI as woven literature; it now leaves out DOIs that the normalized proposal carries, with an L0 test and the Inspect scorer wired the same way. Verify: rows recorded, with the comparison stated.
- [x] 3.2 `uv run poe test`, `uv run poe specs`, `uv run poe cov` green.
- [x] 3.3 Note the scored verifier verdict in `harness/README.md`. Verify: by reading it.
