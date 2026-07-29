# Proposal: implement-proposal-check

## Why

First real skill implementation. The skill-check spec is the most mechanically precise capability — a deterministic stdlib script plus an agent pass — and it unblocks fixture-driven testing for everything else (every later fixture's `expected.json` oracle runs through this script). Implements skill-check, parts of guidance-model (override consumption), and proposal-file-format guardrails.

## What Changes

- `skills/proposal-check/scripts/check.py`: stdlib-only (≥3.11) deterministic checker per the skill-check spec — format guardrails, canonical sections, methodology table, forbidden headings, `(RQn)` cross-refs, citation consistency, min_references, TODOs, warning-class patterns; two-bucket text report; workspace TOML override support.
- `skills/proposal-check/SKILL.md`: agent instructions — run script, add agent pass (typos/grammar, content-level forbidden material), report in chat only, advisory semantics.
- Fixtures: `f15-format-broken` (guardrail violations) and `w02-override-workspace` (TOML override oracle) per the blueprint.
- L0 tests running the script against f00 (clean), f15 (violations), and the override workspace.
- `skip_specs: true` — implements existing requirements.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- New: check script + SKILL.md, two fixture sets, one test module.
- Later skills reuse the script's narrow-extraction helpers via their own copies if needed (sync map extension decided then).
