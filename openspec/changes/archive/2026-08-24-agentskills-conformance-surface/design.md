# Design — agentskills-conformance-surface

## Context

See proposal.md for motivation. Constraints that shape the approach:

- `scripts/sync_shared.py` runs stdlib-only (pre-commit hook, user machines after clone), while the harness truth for evals lives in Python modules that import `inspect_ai` (dev env only).
- `tests/unit/test_skill_frontmatter.py` deliberately avoids general YAML parsing; any new field must be admitted by narrow extraction.
- `METADATA_BUDGET` exists because name+description of every skill load into host context at startup. The new optional fields do not load at startup on any known host.
- The publish pipeline is already an explicit, multi-step, human-triggered process (`harness/README.md` "Audit pre-flight"); rolling release policy stays untouched.

## Goals / Non-Goals

**Goals:**
- Standard-format eval projections with zero second source of truth.
- Frontmatter fields admitted one by one, each with its own gate.
- Spec drift arrives as a visible diff (validator pin bump, annotated constants).

**Non-Goals:**
- No baseline/delta eval work (separate change).
- No `${CLAUDE_SKILL_DIR}` path migration (separate change).
- No semver, tags, or maintained old versions — the stamp is a snapshot label only.
- No `assets/` rename, no per-skill lockfile (recorded as deliberate divergences instead).

## Decisions

**D1 — Projection generator lives in the harness, sync stays stdlib.**
New `harness/eval_export.py` derives the standard's `evals.json` shape per skill: task→skill map from `models.toml` `[tasks.skills]`, prompts/fixture bindings from `skill_evals.py` task definitions and `sources.py`, assertions from L1 verdict explanations and L2 rubric criteria files. It runs under the uv env (`uv run python -m harness.eval_export`). `scripts/sync_shared.py` does not import it; the drift gate for the projection lives in the L0 chain (a test regenerates in-memory and compares against the committed files), which already runs under uv. Rationale: keeps the hook stdlib-only and the truth in the harness; alternative (declaring evals as data the harness reads) was rejected because it inverts the source of truth.

**D2 — Frontmatter admission by per-field rule, not set widening.**
The test keeps extracting keys narrowly and asserts: `name`/`description` as today; `license` present everywhere, value must equal the identifier derived from root `LICENSE.txt`; `compatibility` allowed only on `proposal-publish` and `proposal-lit-search`, 1–500 chars per the standard; `metadata` only with the single `version` key matching the stamp format. Everything else still fails. `METADATA_BUDGET` continues to measure name+description only (the context-loaded surface); new fields are excluded from it and bounded by the standard's own limits. Rationale: budget's stated reason is context load, which the new fields don't cause.

**D3 — Semantic version with pyproject as the single source (revised mid-implementation on user direction).**
The stamp is the suite's semver, read from `[project] version` in `pyproject.toml` — the one hand-edited version anywhere; `scripts/stamp_version.py` copies it into every SKILL.md's `metadata.version` during publish and refuses to re-stamp a version already present in history, keeping version → snapshot unique without any registry file. All skills share the suite version (per-skill versions would mean eleven sources of truth). `poe identify` gains a fast path: read the stamped `version:` line from the report (line shape required — bare `X.Y.Z` matches tool versions all over bug reports), `git log -S` finds the stamping commit; blob-hash comparison remains the fallback for locally-edited files and pre-stamp reports. Rejected alternatives: `<date>+<short-sha>` (first draft — carries no compatibility signal), per-skill semver (multiplies sources of truth for no consumer that exists).

**D4 — Validator pinned in one place, run via npx.**
`poe conform` runs the reference validator (`skills-ref`) at an exact pinned version over every `skills/*` directory; wired into `poe test` and CI. First local run needs network to populate the npx cache; afterwards offline. If implementation finds no published npm package, pin a git ref (`npx --yes github:agentskills/agentskills#<sha>` path or vendored equivalent) — same pin-bump-as-review property either way.

**D5 — Divergence list is one table, written twice deliberately.**
README ("For contributors" area) carries the user-facing stance; AGENTS.md carries the agent-facing one with pointers into history (dev-runner path bug 2026-07-31 for workspace-root script paths). Not materialized from `shared/blocks/` — the two audiences get different framing, and the list changes rarely.

## Risks / Trade-offs

- [Validator availability/shape unknown until implementation] → D4 fallback; if the tool cannot run at all, the conform task fails loudly rather than skipping.
- [Projection could drift from what L1/L2 actually assert if assertions are paraphrased] → derive assertion strings from the same objects the scorers use (verdict function docstrings/explanations, rubric criterion lines), never free-typed.
- [Stamp commits add noise to history] → one commit per publish, message conventionally `chore(publish): stamp <version>`; publishes are rare and explicit.
- [`evals.json` grows skill folder size for installers] → files are small JSON; acceptable, and the standard expects them there.
- [New frontmatter keys on skills.sh render page] → skills.sh renders frontmatter; license/version display is informative, not harmful.

## Migration Plan

1. Land generator + tests + frontmatter admission with `license`/`compatibility` committed.
2. `metadata.version` stays absent until the next publish; `poe identify` fast path activates on first stamped report. Rollback: remove fields, restore set-equality test — no data migration anywhere.
