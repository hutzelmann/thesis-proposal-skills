## Why

The external fork that prompted the methodology survey happened because a supervisor whose method was missing had no way to learn that adding it is a config file rather than a fork. The mechanism exists (workspace methodology declarations, since `2026-08-11-configurable-methodologies`), but nothing user-facing says so, and authoring a branch from scratch — both-language titles, subsections, per-subsection guidance — is real work the survey has already done for the common non-default methods.

## What Changes

- New `docs/methodology-catalog.md`: ready-to-paste TOML branch declarations, in the exact format `proposal-customize` produces, for the methodologies the survey judged legitimate but not default-worthy — Action Research, Simulation Study, Systematic Mapping Study, Repository Mining, Replication Study, and Mixed Methods (the last with an explicit scope warning and an integration-plan subsection that forces the point of interface to be named at proposal time). Each entry says when to use it, cites its source, and notes Design Science Research as a rename of Prototype Implementation rather than an entry.
- The README's "For supervisors" section states explicitly that the methodology set is per-workspace configurable — add a branch, replace one, disable one — and points at `proposal-customize`, the catalog, and the `tests/fixtures/w04-methodology-branch/guidelines.md` working example.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `user-onboarding`: the supervisor-facing documentation SHALL disclose methodology-set configurability and provide ready-made branch declarations for common non-default methods.

## Impact

- `docs/methodology-catalog.md` (new), `README.md` (supervisors section).
- No guidance, structured-data, fixture, or script changes.
