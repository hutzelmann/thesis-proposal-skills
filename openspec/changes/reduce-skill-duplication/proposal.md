# Reduce Skill Duplication

## Why

The self-containment packaging rule currently forces hard vendoring: 17 synced copies across skills (guidelines.md ×4, structure.json ×2, all 9 lit-search scripts into ideate, common+crossref into import), kept honest only by remembering to run `scripts/sync_shared.py` before committing. The heaviest case — ideate vendoring the entire lit-search script suite while its SKILL.md invokes only `search.py` for a handful of exploratory hits — buys almost nothing. Meanwhile the import skill already ships a softer, working pattern (use sibling file if installed, degrade gracefully otherwise), so the repo carries two contradictory self-containment philosophies. Separately, the single-file format prose (metadata block contract) is hand-duplicated across write/import/ideate SKILL.mds with no drift protection at all.

## What Changes

- **Redefine self-containment in the packaging spec**: a skill must be *functional* standalone, not *asset-complete* standalone. Two compliance paths: (a) synchronized vendored copy (as today), or (b) sibling-if-present reference with documented degradation when the sibling skill is not installed — generalizing the pattern the import skill already uses.
- **Drop all 9 vendored lit-search scripts from proposal-ideate**: ideate uses the sibling lit-search skill's scripts when installed, else falls back to agent-side API fetch (the fallback lit-search already documents). Spec-level ideate behavior (grounded ideation, explicit ungrounded notice) is unchanged. Synced copies shrink from 17 to 8.
- **Automate sync at commit time**: a pre-commit hook runs `sync_shared.py` in write mode so stale copies cannot be committed; CI `--check` stays as the backstop. Manual sync disappears as a workflow step.
- **Add drift protection for the single-file format prose**: an L0 test verifies that every SKILL.md describing the proposal file format states the canonical contract (metadata keys, trailing block, blank-line rule) consistently — same pattern as the existing rq-filter and structure-vs-prose drift tests.

Kept as-is (deliberate): guidelines.md and structure.json stay vendored (small, and their consumers need them for core function, not enrichment); import keeps its common/crossref copies (`validate_refs.py` imports them as Python modules — a missing sibling would crash the script rather than degrade).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-packaging`: "Self-contained skills via synchronized copies" requirement is rewritten to "self-contained skills via synchronized copies or declared sibling fallbacks" — functional-standalone definition, two compliance paths, degradation must be documented in the SKILL.md. Sync requirement extended: materialization SHALL be automated at commit time, with CI verification as backstop.
- `proposal-file-format`: new requirement — skill prose describing the single-file format SHALL NOT drift from the canonical contract; automated verification SHALL fail on divergence (mirrors the guidance-model drift requirement).

## Impact

- `scripts/sync_shared.py`: SYNC_MAP loses the 9 ideate script entries.
- `skills/proposal-ideate/`: 9 vendored scripts deleted; SKILL.md grounding section rewritten to sibling-if-present + agent-fetch fallback.
- New pre-commit hook (mechanism chosen in design.md) running sync in write mode.
- New L0 drift test under `tests/unit/` for format prose across write/import/ideate SKILL.mds.
- `.github/workflows/`: unchanged behavior (`sync_shared.py --check` remains the CI gate).
- `openspec/specs/skill-packaging/spec.md`, `openspec/specs/proposal-file-format/spec.md`: updated on archive.
