# Tasks — retarget-to-hcis

## 1. Ownership

- [x] 1.1 Install command in `README.md` and `docs/getting-started.md` (×2) → `ignacioalvmar/thesis-proposal-skills`
- [x] 1.2 HTTP user-agent in `skills/proposal-lit-search/scripts/common.py`; re-sync the vendored import copy
- [x] 1.3 CSL style `<id>` and self `<link>` in `skills/proposal-publish/templates/compact-numeric.csl`
- [x] 1.4 `LICENSE.txt`: keep Thomas Hutzelmann as original author, add the fork copyright; add a Credits section to `README.md`

## 2. Sync tooling bug (blocker for everything below)

- [x] 2.1 `scripts/sync_shared.py` emitted the GENERATED header path with `Path.relative_to`, producing backslashes on Windows — `--check` failed on every Windows clone and a Windows sync would have rewritten the committed headers. Use `.as_posix()`
- [x] 2.2 Confirm `sync_shared.py --check` and `tests/unit/test_sync.py` pass on Windows

## 3. Methodology set (guidance-model)

- [x] 3.1 Add `controlled_experiment`, `simulation_study`, `empirical_evaluation`, `mixed_methods` to `shared/structure.json` with en/de titles and subsections
- [x] 3.2 Mirror every new title verbatim into the `shared/guidelines/guidelines.md` title table (`tests/unit/test_structure_drift.py` is the gate)
- [x] 3.3 Replace "Never combine methodologies" with the one-declared-methodology rule plus the Mixed Methods routing and its overuse warning
- [x] 3.4 Add per-branch Methodology Content prose for the four new branches
- [x] 3.5 Add the "Choosing between the branches" selection guidance
- [x] 3.6 Add the advisory human-participant section (ethics route, consent, GDPR, risk bounding, compensation), stating explicitly that it is not a required section and not mechanically enforced
- [x] 3.7 Add standards-as-sources and venue-family guidance to Literature and Citations
- [x] 3.8 Run `scripts/sync_shared.py`; confirm the four `references/guidelines.md` copies and `references/structure.json` refresh

## 4. Review skill

- [x] 4.1 Rewrite the single-methodology bullet in `skills/proposal-review/SKILL.md` as methodology-declaration plus Integration-substance judgement
- [x] 4.2 Split scope risk into its own bullet so an added strand is flagged on merit, not by category

## 5. Fixture corpus re-domaining

- [x] 5.1 f00, f01, f02, f03, f04 — rewrite into HCIS topics, preserving seeded defects
- [x] 5.2 f05, f06, f07, f08, f09, f10 — same
- [x] 5.3 f11, f12, f13, f14, f15, f16, f17 — same; rename `f16`'s `img/` files to the new slug
- [x] 5.4 f18 — rebuild with real, network-verified references so VERIFIED / ENRICHED / UNVERIFIABLE × 2 all still reproduce; confirm by running `validate_refs.py`
- [x] 5.5 w01, w02, w03 — same; w03 gains real resolvable DOIs and becomes the Controlled Experiment branch fixture
- [x] 5.6 Update the 8 `expected.json` oracles whose pinned reference ids or TODO strings changed
- [x] 5.7 f19 — deliberately left on its original topic; record the reason in `tests/fixtures/README.md`

## 6. New branch fixtures

- [x] 6.1 `f20-simulation-study` (en, MSc, compliant) with oracle
- [x] 6.2 `f21-empirical-evaluation` (de, MSc, compliant) with oracle
- [x] 6.3 `f22-mixed-methods` (en, MSc, compliant) with oracle
- [x] 6.4 Confirm every methodology branch now has a compliant fixture

## 7. Harness and tests

- [x] 7.1 Re-domain `harness/personas/hesitant-bachelor.txt` and `anecdote-master.txt`, keeping the behavioural structure the Socratic rubric grades
- [x] 7.2 Update fixture filenames in `harness/skill_evals.py` and `harness/claude_runner.py`; re-domain `MESSY_SOURCE`
- [x] 7.3 Update hardcoded filenames and content strings in `tests/unit/test_check.py`
- [x] 7.4 Rewrite `tests/fixtures/README.md` blueprint: topics, new fixtures, branch coverage, the f19 exception, the stale-PDF note, the real-DOI production rule

## 8. Verification

- [x] 8.1 `uv run pytest` — 70 passed, 1 skipped
- [x] 8.2 `uv run ruff check .` — clean
- [x] 8.3 `uv run python scripts/sync_shared.py --check` — in sync
- [ ] 8.4 `openspec validate --all --strict` — **not run**: the `openspec` CLI is not installed in the implementation environment. Spec deltas were authored by hand against the archived format and applied to `openspec/specs/` directly. Validate before archiving this change.

## 9. Deferred (documented in proposal.md)

- [ ] 9.1 Regenerate the `f03`, `f09`, `f11`, `f16` PDF renderings — needs pandoc + typst, absent here. No automated test consumes them
- [ ] 9.2 Re-record `docs/demo/` on an HCIS topic and re-derive `f19` from the new session log — the `demo-recording` spec forbids invented output, so this needs a real session
