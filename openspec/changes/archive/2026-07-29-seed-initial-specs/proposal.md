# Proposal: seed-initial-specs

## Why

The repository is migrating from a LaTeX proposal template to `thesis-proposal-skills` — a skills.sh-distributed, agent-agnostic skill set for writing thesis proposals. The complete design exists in `rewrite.md` (17 locked decisions, verified against live tooling) and `fixtures-blueprint.md`, but no living specs exist yet. This change converts those planning documents into the initial `openspec/specs/` capability specs so all further implementation runs spec-first (D17) and the specs — not the plan document — become the source of truth.

## What Changes

- Create the initial capability specs covering: the proposal file format, guidance/customization model, all eight `proposal-*` skills, skill packaging/distribution, the test harness, and user onboarding.
- Specs encode the *behavioral requirements* distilled from rewrite.md D1–D17 and the skill descriptions; implementation details (tool choices, spike outcomes) stay in design docs of later changes.
- No code is written by this change; its "implementation" is authoring the spec files themselves (delta specs merged into `openspec/specs/` on archive).
- `rewrite.md` is retained as the historical founding document; after this change, requirement edits happen via spec deltas only.

## Capabilities

### New Capabilities

- `proposal-file-format`: single-file proposal format (markdown + trailing CSL-YAML pandoc metadata block), slug naming, flat multi-proposal workspace, `img/` convention, proposal targeting/detection.
- `guidance-model`: default guidance shipped in skills, workspace `guidelines.md` override (TOML block + prose), merge semantics, formalization boundary (`structure.json` scope), canonical English/German section structure.
- `skill-ideate`: Socratic, literature-grounded ideation seeding the proposal file.
- `skill-lit-search`: multi-source academic literature search (keyword + snowballing modes, source tiers, key handling, CSL-YAML output).
- `skill-write`: writing/refining proposals per guidance and literature.
- `skill-import`: importing existing proposals (PDF), personal-data stripping, robustness.
- `skill-check`: deterministic low-level checks + agent pass, two-bucket reporting, warning classes (incl. confidentiality markers).
- `skill-review`: high-level content review to `<slug>-review.md`, format-agnostic, grammar hint rule.
- `skill-publish`: optional pandoc build (typst-first, fallbacks), templates, hand-in export, artifact hygiene.
- `skill-customize`: dialog-driven `guidelines.md` management with conflict validation.
- `skill-packaging`: skills.sh distribution, `proposal-*` naming in frontmatter, self-containment, `shared/` sync with committed copies, release policy.
- `testing-harness`: test pyramid (L0/L1/L2), inverted-hybrid runners (OpenRouter authoritative, `claude -p` dev), fixtures per `fixtures-blueprint.md` with `expected.json` oracles.
- `user-onboarding`: README for AI newcomers, getting-started walkthroughs, zero-build quick start.

### Modified Capabilities

<!-- none — repository has no existing specs -->

## Impact

- New directory content under `openspec/changes/seed-initial-specs/specs/` (13 delta specs), merged to `openspec/specs/` on archive.
- No runtime code, no user-facing files touched.
- Later changes (Phase 0 spikes, migration steps 1–9 from rewrite.md) will reference and refine these capabilities.
