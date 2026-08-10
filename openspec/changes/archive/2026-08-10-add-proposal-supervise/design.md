# Design: add-proposal-supervise

## Context

Nine student-facing skills exist; the packaging spec fixes the opening structure (purpose, workflow line, voice block, pinned mandate), demands functional self-containment with sibling names as orientation only, and already contains the tenth-skill scenario: every existing workflow line is updated when the set grows. Vendoring runs through `scripts/sync_shared.py` (`SYNC_MAP`), with two established reuse patterns: synchronized copies for core-function scripts (import/write vendor `check.py`) and sibling-fallback for optional enrichment (ideate). Normalization logic lives mostly in `proposal-import`'s SKILL.md prose plus its scripts (`check.py`, `common.py`, `crossref.py`, `validate_refs.py`, `structure.json`).

## Goals / Non-Goals

**Goals:**
- One professor-side command per submission: raw input → curated draft letter + continuable artifact.
- Zero new quality rubric: check and review stay the sources of truth for what a defect is.
- The tenth-skill machinery lands complete in one change (workflow lines, header pattern, mandate pin, report offer, sync entries, L0+L1 coverage).

**Non-Goals:**
- No sending, no student registry, no retention management.
- No model-support matrix run; supervise ships as untested-tier in `shared/model-support.json` until the next metered run.
- No supervisor-specific guideline content; the workspace `guidelines.md` override (proposal-customize) is the only requirements source beyond the shared guidelines.

## Decisions

**D1 — Normalization: delegate to sibling import, degrade inline.** When `proposal-import` is installed beside supervise (the normal case — the set publishes together), supervise follows its procedure for extraction, personal-data strip, and gap marking. When absent, supervise falls back to a short inline normalization section in its own SKILL.md (extract text, strip personal data per the same rules, mark gaps) — functional but less thorough, mirroring ideate's sibling-fallback precedent. Alternative rejected: vendoring import's SKILL.md prose — `sync_shared.py` maps whole files, and a second full copy of the import procedure would drift or demand new machinery.

**D2 — Findings engine: vendored `check.py` + review rubric from vendored guidelines.** New `SYNC_MAP` entries: `shared/guidelines/guidelines.md` → `skills/proposal-supervise/references`, `shared/structure.json` → `skills/proposal-supervise/references`, `skills/proposal-check/scripts/check.py` → `skills/proposal-supervise/scripts`. The skill runs check.py mechanically, applies the review rubric (substance tests, title dimension, density rule) from the guidelines, then curates. Curation logic is SKILL.md prose: rank by substance-test impact, cap at five, phrase as directions.

**D3 — Workspace layout: slug conventions matching existing skills.** `<slug>.md` (normalized proposal, beside the professor's other proposals), `<slug>-review.md` (full review, professor-only, same naming as proposal-review), `<slug>-package/` (send-package: `letter.md` + a copy of `<slug>.md`). The package directory makes "attach exactly this" unambiguous and keeps professor-only content structurally outside it.

**D4 — Getting-started snippet: skill-local source file.** `skills/proposal-supervise/references/getting-started.md` with an English and a German section, quoted verbatim into the letter. Single consumer, so it is a source file, not a `shared/` sync target. Contains the skills.sh install pointer and the continue-with-proposal-write instruction.

**D5 — Verdict phrasing map in SKILL.md.** The three review tiers map to fixed letter phrasings: ready → "no substantial revisions needed from my side"; needs revision → address points and resubmit; no viable core → honest re-grounding statement plus ideation redirect. The map lives in the mandate-adjacent body so the pinned mandate covers the no-commitment rule.

**D6 — Testing: L0 through existing rosters, one new L1 task.** Header-pattern, report-offer, and mandate tests extend by their existing discovery/roster mechanisms; new pinned mandate at `tests/unit/data/skill_mandates/proposal-supervise.txt`. New verdict functions in `harness/l1_checks.py` (letter exists, ≤5 points, verdict tier, personal-data absence, skill pointers resolve), each with L0 unit tests; scorers in `harness/skill_evals.py` are thin adapters; one L1 task over a synthetic pasted-email fixture carrying fake personal data (`Erika Musterfrau`, matriculation `00000000`). `tests/unit/test_eval_wiring.py` gains the new task's scorer names.

## Risks / Trade-offs

- [Inline fallback drifts from import's canonical procedure] → fallback kept to a few lines stating the same three guarantees; import remains named as the canonical path; personal-data strip is additionally caught by the L1 verdict.
- [Letter tone (honest, never crushing) is not L0-checkable] → covered by the L1 rubric direction only at the next metered matrix run; until then tone rests on SKILL.md wording review.
- [Workflow-line churn touches all nine skill pages] → mechanical and fully enforced by `test_skill_header_pattern.py`; done in one commit with the pinned copies updated in the same diff.
- [Model-support data has no supervise entry until the next matrix run] → `shared/model-support.json` / troubleshoot show it as untested, which the harness already renders honestly (untested, not failing).
