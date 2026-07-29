# Proposal: build-fixture-corpus

## Why

The testing-harness spec requires the full fixture corpus per `fixtures-blueprint.md` — synthetic proposals covering both languages, all quality tiers, every mechanical rule tripped and passed, every methodology branch — each with an `expected.json` oracle. f00 (clean en), f15 (format-broken), and w02 (override workspace) exist; the remaining 16 fixtures and the oracle-driven L1 test do not.

## What Changes

- Author fixtures f01–f14, f16, f17, w01, w03 per the blueprint (invented prose, seeded defects, obviously fake personal data; corpus-derived ones follow the blueprint's altered topics — no real-proposal content).
- `expected.json` oracle per fixture: check exit code + error/warning substrings (calibrated against the actual check script) + semantic expectations for L2.
- Oracles for the existing f00/f15/w02 as well.
- PDF renderings for the import-robustness fixtures (f03, f09, f11, f16 incl. two embedded images).
- `tests/unit/test_fixture_oracles.py`: every fixture's mechanical oracle holds against check.py — the corpus becomes executable ground truth.
- `skip_specs: true` — implements the testing-harness fixture requirement.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- ~20 new fixture directories under `tests/fixtures/`; one new test module; no runtime code changes.
