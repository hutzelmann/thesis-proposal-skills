# Proposal: register-task-runner

## Why

The repo's dev commands (pytest, ruff, drift check, dev runner, audit scan, metered evals) are long raw invocations documented in prose; there is no single registered entry point, so triggering "the tests" means copying commands out of AGENTS.md. A declarative task runner unifies them under `uv run poe <task>` with zero handwritten glue code.

## What Changes

- Add `poethepoet` to the dev dependency group.
- Add `[tool.poe.tasks]` to `pyproject.toml`:
  - `test` — L0 suite: pytest + ruff + `sync_shared.py --check` (free, sequence task).
  - `dev` — passthrough to `harness/claude_runner.py` (subscription dev loop).
  - `audit` — `scripts/audit_scan.py` pre-publish gate.
  - `audit-status` — `scripts/audit_status.py`.
- Update AGENTS.md Commands section and harness/README.md to name the poe entry points alongside the raw commands.
- No skill, harness, or spec behavior changes — tooling only (`skip_specs: true`). Matrix-related tasks (`smoke`, `matrix`, `report`) are added by the follow-up model-support-matrix change, not this one.

## Capabilities

### New Capabilities

None — tooling only.

### Modified Capabilities

None — no spec-level behavior changes.

## Impact

- `pyproject.toml` (dev-dependency + task table), `uv.lock`.
- Docs: `AGENTS.md`, `harness/README.md`.
- No user-side skill files touched; nothing ships to skills.sh.
