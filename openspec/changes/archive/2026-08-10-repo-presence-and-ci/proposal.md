# Proposal: repo-presence-and-ci

## Why

The GitHub-facing surface trails the repository's actual rigor. CI restates the steps of `poe test` instead of calling it (a task-definition change would silently escape CI), never runs the coverage floor, and floats `@fission-ai/openspec@latest` — the one unpinned dependency in an otherwise deliberately pinned workflow. A fresh clone silently has no pre-commit hook; a human contributor finds no setup instructions (PR #1 proves external contributors exist). And three documented facts have drifted from the code: AGENTS.md says the coverage floor is 70 (it is 78), `audit_status.py` still checks "all eight skills" while the repo ships nine (`proposal-troubleshoot` is silently unmonitored), and `harness/README.md`'s task roster is three tasks behind `skill_evals.py`.

## What Changes

- **CI mirrors poe.** The `l0` job becomes `uv run poe test` + `uv run poe cov` + `uv run poe specs`; the openspec pin (1.7.0) lives in the new poe `specs` task, one place for CI and developers alike.
- **`poe setup`** bootstraps a clone: `uv sync --dev` + `git config core.hooksPath .githooks`.
- **README badge row** under the title: CI status, license, last-commit (standard `img.shields.io/github/*`), and a static skills.sh link badge.
- **CONTRIBUTING.md** (thin pointer): human setup steps, the spec-first loop in two sentences, "rules live in AGENTS.md". **PR template** with the checklist a good PR already follows.
- **`audit_status.py`** derives its roster from the `skills/proposal-*` directories (as `audit_scan.py` already does), treats a 404 verdict fetch as an explicit `"unpublished"` baseline entry instead of a fetch failure, and drops the stale "eight". L0 tests cover roster derivation and 404 handling.
- **Doc drift fixes:** AGENTS.md floor 70→78 and Commands section gains `setup`/`specs`; `harness/README.md` roster prose gains `review_hollow`, `ideate_probing`, `troubleshoot_model_rung`.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

(none — tooling, CI, and documentation only; `skip_specs: true`)

## Impact

- `.github/workflows/ci.yml`, `pyproject.toml`
- `README.md` (badge row only), `CONTRIBUTING.md` (new), `.github/PULL_REQUEST_TEMPLATE.md` (new)
- `scripts/audit_status.py`, `tests/unit/` (new audit_status tests)
- `AGENTS.md`, `harness/README.md`
