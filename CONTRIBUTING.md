# Contributing

Thanks for looking under the hood. This file covers setup; the rules live in
[AGENTS.md](AGENTS.md), which is written for AI agents but binds humans the same
way — read it before changing anything.

## Setup

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/).
2. `uv run poe setup` — syncs the dev environment and enables the repo's
   pre-commit hook (regenerates synced copies so CI's drift check stays green).
3. `uv run poe test` — the full L0 gate (pytest + ruff + generated-copy drift).
   It must be green before and after your change.

## How changes work

This repository is spec-first: behavior changes start as an OpenSpec change
folder under `openspec/changes/` (proposal, spec deltas, tasks) and end
archived; pure tooling/docs changes declare `skip_specs: true` instead.
The [PR template](.github/PULL_REQUEST_TEMPLATE.md) lists what a reviewable PR
carries — most importantly: edit sync sources (`shared/`, the source skill),
never the files `scripts/sync_shared.py` writes, and keep every fixture
synthetic (`Erika Musterfrau`, matriculation `00000000`).

Real proposals, credentials, and any other private material never enter this
repository.
