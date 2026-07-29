# Proposal: upgrade-dev-runner

## Why

claude_runner.py is a single-prompt wrapper — no fixture staging, no scoring, no skill loading; it cannot exercise what skill_evals tests, so the "subscription dev loop" leg of D11 is currently hollow. Separately, harness/README.md accumulated a dated findings log that belongs in eval logs and archived change docs, not in a usage doc.

## What Changes

- Factor the L1 verdict logic into `harness/l1_checks.py` as pure filesystem/text functions, shared by the Inspect scorers and the dev runner.
- Rewrite `harness/claude_runner.py`: stages a fixture into a temp workspace, installs the skill under test into `<ws>/.claude/skills/` (real Claude Code skill discovery), runs headless `claude -p` with the user request, applies the shared L1 checks, prints a verdict. Scenarios: check_report, review_fixture, write_from_seed.
- Replace harness/README.md's findings log with a stable known-limitations note; dated findings live in the archived changes.
- `skip_specs: true` — dev tooling refinement of the existing testing-harness capability.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

Real-binary skill testing on the Max subscription becomes possible; Inspect/OpenRouter remains the authoritative path.
