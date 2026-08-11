## Why

The 2026-08-11 literature survey identified the machine-learning evaluation thesis — train or select models, evaluate against baselines on datasets — as the strongest candidate for a default methodology branch: it maps almost one-to-one onto the ACM SIGSOFT Data Science standard, has its own methodological literature (Raschka's model-evaluation treatise, the NeurIPS reproducibility checklist, the data-leakage pitfalls literature), and describes a large and growing share of CS theses. The shipped set cannot express it: no artifact is contributed (not Prototype Implementation), no humans participate (not User Study), and the vocabulary of treatments and participants misses what such a proposal must fix in advance — data provenance, split discipline, baselines, metric justification.

## What Changes

- New default methodology branch **Empirical Model Evaluation** / **Empirische Modellevaluation** with subsections Data and Baselines / Experimental Setup / Analysis (de: Daten und Baselines / Versuchsaufbau / Auswertung), with a content contract derived from the SIGSOFT Data Science standard and the ML evaluation-pitfalls literature: data provenance and licensing, state-of-the-art baselines or their justified absence, split protocol and leakage prevention, metric justification, variance across runs.
- Benchmark-style comparisons of existing models or tools use this branch; the guidance says so rather than leaving benchmark studies homeless.
- New fixture `f24-model-evaluation` with a calibrated oracle.

Not breaking: purely additive.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the canonical-structure enumeration gains Empirical Model Evaluation; an added requirement pins the branch's subsection contract.

## Impact

- `shared/structure.json`, `shared/guidelines/guidelines.md`, generated copies via sync.
- `tests/fixtures/f24-model-evaluation/` (new) and `tests/fixtures/README.md`.
- No check-script changes.
