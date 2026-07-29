# Proposal: expand-eval-coverage

## Why

Four of eight skills have no eval task (import, customize, publish, lit-search) and no eval exercises German despite the de rubric dimension and fixtures. The testing-harness spec's per-skill ambition needs the missing tasks.

## What Changes

- New Inspect tasks in harness/skill_evals.py: customize_override (f00 + supervisor requirements to TOML), publish_build (f00 to PDF via the real pipeline), import_messy (pasted messy text to standard format, personal data stripped), litsearch_expand (w03 snowball/search, live network), review_fixture_de (f04, German review file).
- Scorers reuse l1_checks where possible; new checks stay host-side and deterministic.
- harness/README.md task list updated (litsearch_expand marked network-dependent).
- Smoke runs of the cheap tasks validate wiring.
- skip_specs: true — extends the implemented testing-harness capability.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

Eval coverage: all eight skills plus German.
