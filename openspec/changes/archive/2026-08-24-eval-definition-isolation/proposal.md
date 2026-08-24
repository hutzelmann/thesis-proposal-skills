# Eval-definition isolation

## Why

Since the skills started shipping `evals/evals.json` (agentskills-conformance-surface), the dev runner and the routing rig — which install skills by copying the whole folder — hand the model under test its own eval assertions. A measured run that can read what it will be graded on is contaminated. The Inspect path is unaffected (it stages a whitelist and always excluded `expected.json`); real user installs legitimately carry `evals/` per the standard.

## What Changes

- Dev runner and routing rig install skills without the `evals/` directory; everything else copies as before.
- L0 coverage: the staged measurement environments contain no eval definition file.
- README divergence list gains the one soft divergence still undocumented: eval input files are referenced by workspace name, not copied into `evals/files/` — they live in the repo's fixture corpus beside their oracles.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities
- `testing-harness`: gains the isolation requirement — no runner's staged environment contains eval definitions, oracles, or assertions.

## Impact

`harness/claude_runner.py`, `harness/routing.py` (one `ignore=` each), a new L0 test, README divergence table.
