# Tasks: register-task-runner

## 1. Task runner

- [x] 1.1 Add `poethepoet` to the `dev` dependency group (`uv add --group dev poethepoet`), lockfile updated
- [x] 1.2 Add `[tool.poe.tasks]` to `pyproject.toml`: `test` (sequence: pytest, ruff check, `sync_shared.py --check`), `dev` (passthrough to `harness/claude_runner.py`), `audit` (`scripts/audit_scan.py`), `audit-status` (`scripts/audit_status.py`)
- [x] 1.3 Verify `uv run poe test` runs the full L0 chain green and `uv run poe dev --help`-equivalent passthrough works

## 2. Docs

- [x] 2.1 Update AGENTS.md Commands block: poe entry points first, raw invocations kept for reference
- [x] 2.2 Update harness/README.md dev-runs section with `uv run poe dev <scenario> --model <m>`
