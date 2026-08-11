## Why

The 2026-08-11 literature survey found the industry-embedded thesis — a student inside one organisation studying a real system, process, or team — has no home in the shipped set: it builds nothing (not Prototype Implementation), manipulates nothing (not Controlled Experiment), and its participants are people doing their own work rather than recruits performing designed tasks (not User Study). Case study research is a core method in every surveyed taxonomy (Runeson & Höst's guidelines, the SIGSOFT CaseStudy standard, Oates), and at a university of applied sciences the industry-embedded thesis is a staple. The approved plan promotes it to a default branch.

Promoting it invalidates the `w04-methodology-branch` fixture, which exists to prove a workspace-declared branch is merged rather than ignored and uses Case Study as that branch. Its declaration switches to Action Research — a real method (Oates strategy, SIGSOFT ActionResearch standard) that is genuinely not shipped and not a promotion candidate.

## What Changes

- New default methodology branch **Case Study** / **Fallstudie** with subsections Case and Units of Analysis / Data Collection / Analysis (de: Fall und Analyseeinheiten / Datenerhebung / Auswertung), with a content contract derived from Runeson & Höst's plan elements: intentional case selection with a rationale, units of analysis, data sources with a triangulation plan and host-organisation consent, coding approach with the single-case limitation named.
- New fixture `f25-case-study` exercising the branch cleanly, adapted from the case-study proposal that previously lived in `w04`.
- `w04-methodology-branch` switches its workspace-declared branch to Action Research with a new proposal, keeping its role as the merge-mechanism positive control.

Not breaking for users: purely additive to the shipped set. The w04 rewrite is test-internal.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the canonical-structure enumeration gains Case Study; an added requirement pins the branch's subsection contract.

## Impact

- `shared/structure.json`, `shared/guidelines/guidelines.md`, generated copies via sync.
- `tests/fixtures/f25-case-study/` (new), `tests/fixtures/w04-methodology-branch/` (rewritten), `tests/fixtures/README.md`.
- No check-script changes.
