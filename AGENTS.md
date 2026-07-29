# AGENTS.md

Instructions for AI agents working **on this repository** (skill development and testing). User-facing proposal guidance lives in `shared/guidelines/guidelines.md` and is a product artifact, not agent instructions.

## What this repo is

`thesis-proposal-skills`: eight `proposal-*` agent skills (under `skills/`) that help students write thesis proposals, plus the machinery to test them. Users install the skills into their own workspace; their proposals never live here. Real proposals and credentials sit in the untracked `confidential/` directory — never commit, copy, or quote its contents.

## Spec-first workflow (mandatory)

`openspec/specs/` is the source of truth, managed with OpenSpec. Any behavior change runs the loop: `/opsx:propose` (change folder with proposal, spec deltas, tasks) → human review → implement → `openspec archive`. Pure refactors/tooling/docs set `skip_specs: true` in the change's `.openspec.yaml`. Validate with `openspec validate --all --strict`. Agent integration files (`.claude/`) are not committed; regenerate with `openspec init --tools <agent>`.

## Hard rules

- **Skill scripts are user-side**: Python ≥ 3.11 standard library only, no pip installs, cross-platform. No general YAML parsing (narrow extraction only; TOML via `tomllib`, JSON via `json`). Dev-side tooling (tests, harness) may use the uv-managed environment freely.
- **Never edit generated copies.** Files marked GENERATED (skill `references/`, vendored scripts in `skills/proposal-ideate/scripts/`) come from `shared/` or sibling skills; edit the source, then run `python3 scripts/sync_shared.py`. CI fails on drift.
- **Fixtures are synthetic.** Nothing derived verbatim from real proposals; personal data obviously fake (`Erika Musterfrau`, matriculation `00000000`). Every fixture carries an `expected.json` oracle calibrated against `skills/proposal-check/scripts/check.py`.
- **Git**: work directly on `main`, no branches or worktrees; commit per completed OpenSpec change. Do not push and do not publish to skills.sh — both happen only on explicit request.
- **Credentials**: read from environment or `confidential/credentials.txt` locally; never hardcode, log, or commit them. User-side scripts resolve keys via environment then workspace `api-keys.env`.

## Commands

```sh
uv run pytest                      # L0: all tests, no model calls — must stay green
uv run ruff check .                # lint — must stay clean
python3 scripts/sync_shared.py --check   # generated-copy drift check
openspec validate --all --strict   # spec validity
uv run inspect eval harness/skill_evals.py@<task> --model openrouter/...   # L1/L2, metered
uv run python harness/claude_runner.py <scenario> --model haiku            # dev loop, subscription
```

Eval details, task list, and known limitations: `harness/README.md`. Model runs cost money or quota — run them deliberately, never in loops.

## Editing guidance content

`shared/structure.json` holds only the mechanically checkable skeleton (canonical titles en+de, methodology table, forbidden patterns); semantic rules stay prose in `shared/guidelines/guidelines.md`. Every structured title must appear verbatim in the prose (drift-guarded by an L0 test). The formalization boundary is deliberate — do not encode semantic quality rules as data.

## History

Migrated from a LaTeX proposal template on 2026-07-29; the tag `legacy-latex-template` preserves the old state, and the archived OpenSpec changes under `openspec/changes/archive/` document every step including eval findings.
