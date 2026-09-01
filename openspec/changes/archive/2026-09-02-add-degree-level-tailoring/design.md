# Design

## Context

See proposal.md — Why. The survey behind `docs/degree-level-sources.md` locates the Bachelor/Master difference in graded judgement (contribution, RQ origin, literature stance, scope), not structure. Five skills already ship `references/guidelines.md`; the subtitle already carries the level; nothing else does.

## Goals / Non-Goals

**Goals:** noticeable, level-appropriate behavior in ideate, write, review, supervise, lit-search from information the proposal already carries; one authoritative prose statement; both-direction bars.

**Non-Goals:** any level-dependent structure, check rule, or `structure.json` key; a methodology-justification requirement; new preamble or metadata; level-specific workload numbers (jurisdictional — workspace territory); README/customize changes (prose overrides already flow through the existing workspace `guidelines.md` chain).

## Decisions

1. **One canonical section, five pointers.** The "Degree level" section lives in `shared/guidelines/guidelines.md` and reaches ideate/write/review/supervise/customize via the existing sync. Per-skill SKILL.md touches stay to one or two sentences in body sections that defer to the guidelines — the first-statement-fixes-scope rule forbids restating. Alternative (per-skill full statements) rejected: four drifting restatements.
   - Placement: a `## Degree Level` section directly after "Proposal Structure", before the per-section guidance it colors.
2. **Subtitle is the single level source**, mirroring language inference exactly (exact wording match; TODO or nonstandard ⇒ unknown). No `level` key — the retired-key logic in check.py documents why declared metadata lost to inferred wording once already.
3. **Unknown level = neutral core + one visible line** (review/supervise) or one deferred question (write, at the contribution close) or silence (lit-search, ideate handles it in the preamble). Never guess, never block. Alternative (default to Bachelor bar) rejected: silent wrong bar for Master students.
4. **lit-search stays reference-free**: one self-contained sentence in its SKILL.md. Adding `references/guidelines.md` to it would put a 27KB file into a skill that needs one rule.
5. **Enforcement:** the both-directions bar sentence is pinned in `tests/unit/data/pinned_sentences/`; tailoring goes only into body sections so mandates and the three materialized blocks stay byte-identical; `sync_shared.py` propagates guidelines to the five reference copies.
6. **docs/degree-level-sources.md consequence section** is rewritten in the same change: the design consequence changes from "level is recorded in the subtitle and nowhere else" to "level is read from the subtitle and surfaces as graded judgement in five skills, never as structure".

## Risks / Trade-offs

- [Tailoring wording drifts into prohibition ("Bachelor must not…")] → both-directions bar pinned; Bachelor-side phrasing rule stated in the guidelines section itself.
- [Review starts demanding justification prose despite the contract] → the review delta names methodology fit as judgement explicitly; the guidelines section states no justification statement is required.
- [Guidelines section bloats the five reference copies for a marginal rule] → section capped at ~10 sentences; workload numbers and citations stay in `docs/degree-level-sources.md`.

## Deferred follow-up (named per convention)

**L1 level-mismatch probe** — a fixture pair with identical body and Bachelor vs Master subtitle; the review eval asserts the missing-novelty finding fires only for the Master variant. Cleared by a future change (working name `add-degree-level-review-probe`) when the next metered eval round runs; not built here because it spends metered runs and the model-support matrix is itself deferred.
