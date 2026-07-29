# Proposal: import-reference-validation

## Why

User decision (2026-07-29): imported proposals usually carry a bibliography of unknown quality — dead links, typo'd DOIs, incomplete metadata. Import currently converts references as-found; it should validate them against the academic APIs and complement missing fields, reusing the lit-search source clients. Spec lands now; implementation is deliberately deferred to a later change.

## What Changes

- skill-import gains a reference validation + enrichment requirement: DOIs verified (e.g. Crossref lookup), metadata completed (authors, year, venue, abstract) from the literature sources, unverifiable references marked rather than silently kept, results reported.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `skill-import`: adds reference validation/enrichment behavior (new requirement — existing requirements unchanged).

## Impact

- Spec-only change. Implementation later: vendor the needed lit-search clients into proposal-import via the sync map (mechanism exists), extend SKILL.md, add fixture coverage (imported-with-broken-refs case).
