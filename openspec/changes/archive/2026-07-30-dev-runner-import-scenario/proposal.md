## Why

The import skill can only be exercised on the metered Inspect path. The dev runner — the cheap everyday loop, and the one the harness documents as having the highest execution fidelity — has no `import_messy` scenario, so every iteration on import guidance costs API spend and runs in the agent loop the harness itself flags as an imperfect approximation of a real agent.

The cause is structural: `import_l1` is the only L1 verdict still written inline in the Inspect scorer instead of in the shared pure module. `harness/README.md` already states that L1 verdict logic is shared between both runners via `l1_checks.py`; for import that is not true. A direct consequence is that the import verdict — including the newly added check for an author name typed beside a bracketed citation — has no L0 coverage, because there is no pure function to unit-test.

## What Changes

- The import L1 verdict moves into the shared pure module as `verdict_import()`, taking the produced proposal text and returning the same (passed, explanation) pair as every other verdict. The Inspect scorer calls it instead of reimplementing it.
- The dev runner gains an `import_messy` scenario, so import can be iterated on the subscription runner at no metered cost.
- The dev runner supports scenarios that stage no fixture proposal and instead paste a source document into the request, and that assert against a file the model *creates* rather than one staged in advance. Import is the first such scenario; the source document moves out of the Inspect scorer into a module both runners can import without pulling in the eval framework.
- The import verdict gains L0 unit tests covering each failure mode it reports: no file produced, wrong format, leaked personal or confidential data, a kept timeline heading, and an author name typed beside a bracketed citation.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `testing-harness`: the runner requirement gains the rule that every L1 verdict lives in the shared pure module and is reachable from both runners, and that the dev-runner scenario set covers the import skill including source-document scenarios that produce a new file rather than mutating a staged one.

## Impact

- `harness/l1_checks.py`: new `verdict_import()`, moved verbatim in behavior from the Inspect scorer and extended only by being callable.
- `harness/sources.py` (new): the pasted messy source document, currently a string literal inside `skill_evals.py`. It stays out of `tests/fixtures/` because it is a source document to be imported, not a proposal with a mechanical oracle, and the fixture corpus requirement is written for the latter.
- `harness/skill_evals.py`: `import_l1()` becomes a thin wrapper; `MESSY_SOURCE` moves out.
- `harness/claude_runner.py`: optional `fixture`, new `paste` and `produces` scenario keys, produced-file discovery in `verdict()`.
- `tests/unit/test_harness_helpers.py`: unit tests for `verdict_import()`.
- `harness/README.md`: dev-runner usage gains the new scenario.
- No change to any skill, and no change to what the metered eval asserts — the same verdict, reached by both paths.
