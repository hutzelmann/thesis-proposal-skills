# Proposal: implement-import-ref-validation

## Why

The skill-import spec gained the reference validation/enrichment requirement (archived change import-reference-validation); this implements it.

## What Changes

- `skills/proposal-import/scripts/validate_refs.py` (stdlib): extracts reference entries from the proposal's metadata block, verifies DOIs via Crossref lookup, identifies DOI-less entries via Crossref search with confident title matching, and prints a per-reference report (verified / enriched / unverifiable) plus completed CSL-YAML for the agent to apply.
- Sync map vendors `common.py` and `crossref.py` into proposal-import (self-containment).
- SKILL.md gains the validation step: run the script after conversion, apply enrichments, mark unverifiables with `[TODO: verify reference …]`, report per reference, degrade gracefully offline.
- Offline unit tests with canned Crossref responses cover the three spec scenarios.
- `skip_specs: true` — implements the already-merged requirement.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

proposal-import gains scripts/; no other skills affected.
