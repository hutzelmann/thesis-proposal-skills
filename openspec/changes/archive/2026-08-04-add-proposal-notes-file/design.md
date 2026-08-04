# Design — add-proposal-notes-file

## Context

See proposal.md — Why. Constraints shaping the approach:

- All three adopting skills are prose-only surfaces (`SKILL.md`); import and write additionally vendor generated copies under `scripts/`/`references/` that this change does not touch.
- The skill-header pattern pins each mandate paragraph byte-identically; the additions must slot below the mandates without moving them.
- `check.py` counts proposal `[TODO: …]` markers as the readiness signal; the split rule must not starve that signal (blocking gaps stay in the proposal).
- `l1_checks.select_draft` already excludes non-proposal markdown by exact name (`NON_PROPOSAL_MARKDOWN = ("guidelines.md",)`); the notes exclusion needs a suffix rule beside it.
- The formalization boundary (AGENTS.md / guidance-model spec): semantic structure stays prose; nothing about notes content becomes machine-checked data.
- The follow-up change `redesign-ideate-dialogue` makes ideate the primary notes producer; this change lands format + consumers first so the ideate change has stable ground.

## Goals / Non-Goals

**Goals:**

- One canonical definition of the notes file (name, sections, split rule) in proposal-file-format; skills reference behavior, not format details, to avoid drift.
- Consumers degrade gracefully: no notes file → prior behavior, no skeleton-file litter.
- Mechanical surface minimal: one suffix rule in `select_draft`, L0-tested.

**Non-Goals:**

- No ideate changes here (follow-up change owns them).
- No check.py rules over notes files — not even existence checks.
- No migration of existing workspaces: notes files appear as sessions produce them; old proposals without one stay valid forever.
- No fixture gains a notes file in this change (the ideate change adds dialogue-shaped fixtures that need them).

## Decisions

1. **Suffix `.notes.md`, same slug**: pairs visually in `ls`, exclusion is a one-line `endswith` check, and the pairing rule ("same basename up to the suffix") needs no registry. Alternative `knowledge/<slug>.md` rejected: breaks the flat-workspace convention and `select_draft`'s single-directory scan.
2. **Exclusion via suffix predicate, not name tuple**: `NON_PROPOSAL_MARKDOWN` stays for exact names; the selection filter gains `name.endswith(".notes.md")`. Keeps the tuple's semantics (exact names) clean.
3. **Sections as prose convention in the file-format spec**: named once, listed in each adopting skill only by the section they touch (write → Decisions/Log, lit-search → Excluded Literature, import → all five at seeding). Prevents each SKILL.md from restating the full format — the drift-guard lesson from the metadata contract applied proactively.
4. **Log keeps resolved TODOs**: move-not-delete gives an audit trail of gap closure at zero format cost. Alternative (strikethrough in place) rejected: clutters the buildable document the split exists to clean.
5. **Creation policy per skill**: import always creates (it always has unmapped content or gaps); write creates only when it has decisions to record; lit-search never creates. Prevents empty-skeleton litter while guaranteeing the file exists where it carries value.

## Risks / Trade-offs

- [Two files can drift (proposal says X, notes decision says Y)] → decisions steer drafting by instruction; the write skill re-records changed decisions in the same session that changes the proposal. Accepted residual: no mechanical consistency check, per the formalization boundary.
- [Skills over-log and the notes file bloats] → each adopting skill's prose bounds what it writes (one-line reasons, done entries, named sections); no skill is told to journal free-form.
- [Students mistake the notes file for the proposal] → the file-format spec bars it from proposal targeting; skills never offer it as a candidate.
- [`*.notes.md` shadowing a legitimate proposal named e.g. `field.notes.md`] → accepted: the suffix is now reserved by the format spec, documented in the skills that create the files.

## Migration Plan

Prose + one harness function + unit tests, all in one commit. No data migration, no rollout order. Rollback = revert the commit. The follow-up ideate change depends on this one landing first.
