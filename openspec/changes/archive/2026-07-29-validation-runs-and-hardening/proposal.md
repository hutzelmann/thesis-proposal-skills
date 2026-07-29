# Proposal: validation-runs-and-hardening

## Why

Five eval tasks have never been executed live (write_from_seed, review_fixture, import_messy, review_fixture_de, litsearch_expand), the ideate references-fix is unvalidated, the check skill's read-only hardening exists only as a noted option, and import reference-validation lacks a dedicated fixture.

## What Changes

- Check SKILL.md gains the non-interactive hardening: when no user is present, make the proposal read-only for the duration of the run (chmod/attrib), restore afterwards — an edit attempt then fails loudly instead of silently succeeding. New eval variant check_report_hardened measures it.
- New fixture f18-broken-refs (mixed reference quality: real DOI, enrichable DOI-less entry, dead DOI, unidentifiable entry) with oracle; serves as the live target for validate_refs.
- All unrun evals executed; results and fixes recorded.
- skip_specs: true — validation plus a skill-instruction hardening within existing requirements.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

Eval scoreboard for every task; hardening either proves out or gets documented as insufficient.
