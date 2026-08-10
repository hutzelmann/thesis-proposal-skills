# Tasks — prove-quality-gates

## 1. Fixture

- [x] 1.1 Write `tests/fixtures/f22-hollow-generic/` proposal: check-clean by construction, every sentence generic, no object of study, contribution restates the field; `expected.json` oracle encoding zero errors / zero warnings, calibrated by running check.py
- [x] 1.2 Confirm the oracle rides the existing fixture-oracle L0 parametrization (f22 picked up automatically; oracle test green)

## 2. Persona + ideate task

- [x] 2.1 Write `harness/personas/probing-pat.txt`: agreeable, vague, extraction-minded standing rules (no numbered script), 1–3 sentence replies, never a concrete contribution
- [x] 2.2 Add `verdict_no_generic_seed` (or reuse `verdict_early_stop` if signature fits) in `harness/l1_checks.py`; L0 tests for its failure modes
- [x] 2.3 Add task `ideate_probing` in `harness/skill_evals.py`: persona dialogue, `ideate_l1_no_generic_seed` + `ideate_l2_socratic` with probing criterion (swap test voiced, no generated specifics, impasse named)

## 3. Review verdict task

- [x] 3.1 Add `verdict_hollow_review` pure function in `harness/l1_checks.py` (proposal untouched, verdict line "no viable thesis core" case-insensitive, ≥2 substance-test names cited); L0 tests on crafted review texts
- [x] 3.2 Add task `review_hollow` in `harness/skill_evals.py`: stages f22, scorers `review_hollow_l1` + `review_hollow_l2` (judge: states what would change the verdict, no softening)

## 4. Density scorer + tone criteria

- [x] 4.1 Write `harness/rubrics/density.txt` (template contract; filler classes named; length never a criterion); add `write_l2_density` scorer to `write_from_seed`
- [x] 4.2 Add tone conduct rules to `harness/rubrics/review_quality.txt` criterion (no praise of student/draft, no self-congratulation, neutral wording)
- [x] 4.3 Update `tests/unit/test_eval_wiring.py` scorer-name pins for the new scorers

## 5. Registration

- [x] 5.1 `harness/models.toml`: `review_hollow` into matrix set + task→skill map (+ priors if the section pattern requires); `ideate_probing` into the extended on-demand set with the audit rationale comment

## 6. Verify + calibrate

- [x] 6.1 `uv run poe test` green (includes new L0 verdict tests, oracle calibration, wiring pins, repo-convention checks)
- [x] 6.2 `openspec validate --all --strict` green
- [x] 6.3 Calibration runs (metered, cheapest roster model, 1 epoch each): `review_hollow`, `write_from_seed`, `ideate_probing`; record findings + any instrument fixes here
  - `ideate_probing` (haiku-4.5): both scorers C — no seed, notes present, swap test + impasse voiced. Gate holds even on the cheapest model.
  - `review_hollow` (haiku-4.5): `review_hollow_l1` I with "review modified the proposal" — the known red-by-design byte-identity probe on the Inspect path, same as `review_fixture`; `excluded_l1` registration is correct. `review_hollow_l2` I: judge correctly caught haiku softening the verdict instead of writing "no viable thesis core" — instrument discriminates; haiku fails the new bar (matrix signal, not an instrument bug).
  - `write_from_seed` density (haiku-4.5): first run flagged an elaborating-but-specific sentence — rubric tuned once (elaboration with new specifics ≠ restatement; flag only swap-test failures; when unsure, not filler). Re-run still I, now citing a genuinely generic sentence ("methods differ in sensitivity and computational cost") haiku's density pass should have deleted. Instrument correct after tuning; cheap model fails the sharpened bar.
- [x] 6.4 Adversarial verify workflow over the full diff; fix confirmed findings
  - Five findings (judged inline after the workflow's judge stage hit the session limit), all fixed: (1) dev runner gained a `review_hollow` scenario so the pure L1 verdict gates a real path without model-graded scoring (`excluded_l1` on the Inspect path is the known byte-identity artifact); (2) `review_quality.txt` now binds its `[Criterion]` in the grading list instead of only rendering it; (3) fixture README gained the f22 row, f21's "every remaining title is silent" claim scoped to the deterministic tells; (4) f22 oracle records the deliberately field-vague title as a semantic defect; (5) probing-pat's opener quote corrected to the staged `IDEATE_REQUEST` wording — the wrong quote pre-supplied "AI proposal" framing and risked breaking reply-1 anchoring.
