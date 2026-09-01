# Document degree-level sources

## Why

The skills deliberately treat Bachelor's and Master's proposals with one skeleton — degree level lives only in the subtitle wording and in `proposal-review`'s scope judgement — but nothing in the repo says why, or what the difference between the two thesis types actually is. A literature survey on 2026-09-01 (six source families: EU frameworks, German HQR, statutory descriptors, CS curricula and department documents, peer-reviewed assessment literature, methods textbooks) found the evidence base: the difference is graded, not structural, and converges on a small set of dimensions. Recording it gives "why doesn't the checker branch on level?" a citation instead of a shrug, exactly as `docs/methodology-sources.md` does for the methodology set.

## What Changes

- Add `docs/degree-level-sources.md`: per-dimension contrast (novelty, research-question origin, methodological rigor, independence, literature depth, scope, workload envelope) with the framework, statutory, curricular, institutional, and peer-reviewed sources behind each; how each difference surfaces in a proposal; convergence strength per claim; and the caveats (graded not categorical, jurisdictional flavor, proposals rarely level-differentiated institutionally).
- The document states the design consequence it grounds: same skeleton at both levels, differentiation is scope judgement (`proposal-review`) and workspace configuration, never a shipped structural default.
- No skill, script, guideline, or shared content changes.

## Capabilities

### New Capabilities

None — documentation only.

### Modified Capabilities

None. No spec-level behavior changes; `skip_specs: true` is set in `.openspec.yaml`.

## Impact

- New file `docs/degree-level-sources.md`; no other files touched.
- No code, tests, fixtures, or generated copies affected; `sync_shared.py` not involved.
