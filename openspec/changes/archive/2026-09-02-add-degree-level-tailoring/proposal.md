# Add degree-level tailoring

## Why

The skills treat Bachelor's and Master's proposals identically except for the subtitle wording and one vague review clause, yet `docs/degree-level-sources.md` (survey of 2026-09-01) documents a converged, citable set of graded differences: contribution expectation, research-question origin, literature stance, and scope-per-months. Students and supervisors currently get no benefit from the level the proposal already declares. The tailoring stays judgement-side prose — the survey's own conclusion is that the difference is graded, not structural — so `structure.json`, `check.py`, and the document skeleton remain level-blind.

## What Changes

- New "Degree level" section in `shared/guidelines/guidelines.md`: the four graded dimensions in ~2 sentences each, a framing sentence that everything else is identical by design (citing the sources doc), and the both-directions bar (demanding a novelty claim from a Bachelor proposal is the same error as accepting its absence from a Master proposal). Bachelor-side wording is always "not required", never "not allowed". No explicit methodology-justification requirement anywhere: the proposal states one methodology and supports it as a whole; method fit is a review lens, not required text.
- **proposal-ideate**: the already-collected level steers the Socratic session — Bachelor toward well-bounded application/evaluation (deriving from the group's topic named as level-appropriate), Master toward a gap. No new questions.
- **proposal-write**: drafting the contribution close and research questions consults the level from the subtitle; when the subtitle is a TODO, the skill asks once, at the moment the contribution close is drafted.
- **proposal-review**: the generic "scope risks for the thesis level" clause becomes the four dimension lenses plus the fit lens (Master: methodology follows from the RQs with limits acknowledged; Bachelor: correct application planned). Unknown level → level-neutral review plus one line naming the unset subtitle.
- **proposal-supervise**: the feedback letter is calibrated to the level bar — never asks a Bachelor proposal for a novelty claim, always asks a Master proposal missing one. Unknown level → neutral bar plus the same one-line note.
- **proposal-lit-search**: one self-contained sentence (Bachelor: textbook/survey anchors legitimate; Master: prioritize recent primary work that can yield a gap). No new reference wiring.
- The subtitle is the single source of the level, exactly as it is for language; no new metadata key, never guessed, never blocking.
- `docs/degree-level-sources.md` design-consequence section updated: level is no longer "recorded in the subtitle and nowhere else" — the graded dimensions now surface as tailored judgement in five skills, still never as structure.
- One load-bearing sentence (the both-directions bar) pinned in `tests/unit/data/pinned_sentences/`.
- The L1 probe (identical body, Bachelor vs Master subtitle, review flags the missing novelty claim only for Master) is deferred and named in `design.md` as the follow-up.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: guidelines gain the degree-level section (four graded dimensions, both-directions bar, level-blind-skeleton framing).
- `skill-ideate`: level steers ideation scope Socratically.
- `skill-write`: contribution close and RQ drafting honor the level; single deferred question when the level is a TODO.
- `skill-review`: level-dependent review lenses replace the generic clause; unknown-level fallback defined.
- `skill-supervise`: letter feedback calibrated to the level bar; unknown-level fallback defined.
- `skill-lit-search`: literature stance sentence per level.

## Impact

- `shared/guidelines/guidelines.md` + generated copies in five skills (via `sync_shared.py`).
- SKILL.md bodies of ideate, write, review, supervise, lit-search — body sections only, no mandate edits, no touched materialized blocks.
- `docs/degree-level-sources.md` (consequence section), `tests/unit/data/pinned_sentences/` (+1), the pinned-sentence test list if enumeration is explicit.
- Untouched by design: `shared/structure.json`, `check.py`, fixtures and their `expected.json` oracles, mandates, workflow/voice/report-offer blocks, harness.
