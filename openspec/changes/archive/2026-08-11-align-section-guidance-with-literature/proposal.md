## Why

A literature survey (2026-08-11: Punch; Locke, Spirduso & Silverman; Booth, Colomb & Williams; Shaw; Wieringa; Maxwell; FINER; plus a 13-template grey-literature sample) checked the shipped guidance against what the research-methods literature says a proposal must do. The five-section skeleton held up, but the survey found three proposal functions the literature treats as mandatory that the current prose gives no home, two rules the literature sharpens, and one place where the guidance should openly own a deliberate divergence from majority template practice instead of leaving it to look like ignorance.

## What Changes

- **Purpose stated early.** Punch and Locke both place a statement of what the study tries to achieve no later than the end of the introduction. The guidance currently permits referring to the thesis at the end of the introduction; it will require a purpose sentence there.
- **Significance and result type.** Punch's checklist carries a "Significance" heading and Locke makes "Providing a Rationale" a mandatory task; the delta over prior work ("what is missing") is not the same statement as significance ("why the answer will matter"). Shaw's result-type taxonomy says a proposal promises a kind of deliverable. The contribution section's closing gap statement gains both: why answering the questions matters beyond filling the gap, and what kind of thing the thesis will deliver.
- **Structured construction goals.** Wieringa's design-problem template (improve a context, by an artifact, such that requirements hold, in order to serve stakeholder goals) becomes the recommended shape for the construction goal in the contribution section, and design-flavored proposals are asked to derive their research questions visibly from the stated goal. Shaw's nuance — a "how can X be done" question is legitimate research when the answer is a generalizing method — is added to the goal-versus-question prose as reviewer guidance, without softening the student-facing rule.
- **Delta test reworded.** The delta test gains FINER's "confirms, refutes, or extends" formulation, which legitimizes replication-flavored contributions the current wording implicitly excludes.
- **Own the stance.** The survey's template sample shows the guidance's prohibitions (work plans, expected-results sections, named authors) invert majority template practice. One added sentence states that this is a deliberate stance of this guidance, so a student who finds a contradicting template reads a decision rather than an oversight.

Out of scope, per the approved plan: all methodology-branch content (later changes), any structured-data change, any new section.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: two added prose requirements (early purpose statement; significance and result type at the contribution's close, plus the deliberate-stance statement) and two modified ones (construction goals gain the goal template, the derivation link, and the generality nuance; the substance tests' delta test gains the confirms/refutes/extends wording).

## Impact

- `shared/guidelines/guidelines.md` and its five generated copies (`scripts/sync_shared.py`).
- No structured-data changes: every item is semantic and stays prose per the formalization boundary.
- No fixture or oracle changes — nothing here is mechanically checked.
- L0 prose-drift tests unaffected (no canonical title changes).
