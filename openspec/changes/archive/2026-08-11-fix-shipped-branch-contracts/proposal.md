## Why

The 2026-08-11 literature survey checked the four shipped methodology branches against the method guidelines they compress (Kitchenham & Charters for systematic reviews, the ACM SIGSOFT Empirical Standards, Hevner's design-science guidelines) and found the compressions defensible with three concrete defects: the SLR branch has no home for study quality assessment, which Kitchenham treats as a mandatory protocol component; the Prototype branch's Evaluation subsection never asks which empirical form the evaluation takes, silently absorbing what the standards treat as a second methodology choice; and no branch asks the student to argue why the chosen methodology answers the research questions, which the SIGSOFT General Standard requires of every study.

## What Changes

- **BREAKING** — the SLR branch's second subsection is renamed from "Extracted Information" / "Extrahierte Informationen" to "Quality Assessment and Extracted Information" / "Qualitätsbewertung und extrahierte Informationen" in `structure.json`, giving quality assessment a mechanically checked home. Quality assessment and extraction happen on the same pass over the same papers, so they share a subsection rather than adding a fourth. Proposals written against the old heading will report a missing subsection until retitled.
- The SLR content contract gains: what quality assessment covers, that Synthesis declares whether a formal meta-analysis is intended, that the review type is declared (a mapping-style review states in the quality-assessment subsection why assessment is omitted), and that PICOC is the recommended shape for framing the review question and deriving search terms.
- The Prototype contract's Evaluation subsection now requires naming the empirical form the evaluation takes (benchmark, controlled experiment, case study, simulation) and comparing against state-of-the-art alternatives or justifying why comparison is impractical.
- Every methodology section opens with one or two sentences justifying why the chosen methodology answers the research questions — the prose counterpart of the method-fit test.
- The human-participants ethics advisory gains a sibling for secondary data: studies on mined, scraped, or third-party datasets address provenance, licensing, and personal data contained in the data.

Out of scope: new branches (later changes), provenance citations (the provenance change), any change to the User Study contract beyond what the Controlled Experiment change will bring.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: four added requirements — quality assessment in systematic reviews (carrying the subsection rename), prototype evaluation names its empirical form, methodology sections justify method fit, secondary-data ethics advisory.

## Impact

- `shared/structure.json` (subsection rename) and `shared/guidelines/guidelines.md`, plus all generated copies via `scripts/sync_shared.py`.
- Fixtures: `f05-slr-interviews` and `f13-pure-slr` retitle the subsection and stay at their current verdicts; `f09-llm-compliance-docs` deliberately keeps the old heading — it plays an imported legacy submission, and its oracle gains the `methodology-subsection-missing` error, which also gives the rename an L0 regression test.
- No check-script logic changes: subsection names flow from `structure.json`.
