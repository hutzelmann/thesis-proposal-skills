## ADDED Requirements

### Requirement: Systematic reviews assess primary-study quality
The SLR branch's second subsection SHALL be titled "Quality Assessment and Extracted Information" in English and "Qualitätsbewertung und extrahierte Informationen" in German, and its content contract SHALL cover both halves: how the quality of included primary studies is assessed and how that assessment is used (exclusion or weighting), alongside what is extracted and how deeply. The contract SHALL further require that the Synthesis subsection declares whether a formal meta-analysis is intended or the synthesis stays narrative, and that the review's type is declared: a mapping-style review, which legitimately omits per-study quality assessment, SHALL say so in the quality-assessment subsection and state why breadth replaces depth. The guidance SHALL recommend PICOC (population, intervention, comparison, outcome, context) as the shape for framing the review question and deriving search terms, scoped to this branch only.

#### Scenario: Review silent on study quality
- **WHEN** a proposal declares the SLR methodology and its quality-assessment subsection describes only what data is extracted
- **THEN** guidance-following tooling asks how primary-study quality is assessed and how the assessment is used

#### Scenario: Mapping-style review omits assessment with a reason
- **WHEN** the quality-assessment subsection states the review is a mapping-style survey of a field and quality assessment is omitted because classification, not evidence weighing, is the goal
- **THEN** the omission is compliant, because the branch requires the declaration rather than the assessment itself

#### Scenario: Old subsection title
- **WHEN** a proposal carries the former "Extracted Information" heading
- **THEN** the mechanical check reports the "Quality Assessment and Extracted Information" subsection as missing

#### Scenario: Synthesis type undeclared
- **WHEN** the Synthesis subsection describes combining findings without saying whether a formal meta-analysis is intended
- **THEN** the guidance asks for the declaration

### Requirement: Prototype evaluation names its empirical form
The Prototype Implementation contract SHALL require the Evaluation subsection to name the empirical form the evaluation takes — a benchmark against datasets or workloads, a controlled experiment, a case study, or a simulation — and to compare the prototype against state-of-the-art alternatives or state why such a comparison is impractical. Naming the form is a methodology-internal statement and SHALL NOT be read as declaring a second methodology.

#### Scenario: Evaluation names no form
- **WHEN** a Prototype Implementation proposal's Evaluation subsection promises that the prototype answers the research questions without saying by what kind of study
- **THEN** guidance-following tooling asks which empirical form the evaluation takes

#### Scenario: No alternatives addressed
- **WHEN** the Evaluation subsection measures only the prototype itself although comparable approaches exist in the cited literature
- **THEN** the guidance asks for a comparison or an explicit statement of why comparing is impractical

#### Scenario: Named form is not a second methodology
- **WHEN** a Prototype Implementation evaluation names a benchmark as its form
- **THEN** the single-methodology rule is not violated by that naming

### Requirement: Methodology sections justify method fit
The guidance SHALL require every methodology section to open with one or two sentences stating why the chosen methodology answers the research questions — the prose counterpart of the method-fit test, written by the student rather than judged only by a reviewer.

#### Scenario: Methodology opens without justification
- **WHEN** a methodology section starts directly with its first subsection and never says why this methodology fits these questions
- **THEN** guidance-following tooling asks for the opening justification

#### Scenario: Justification present
- **WHEN** a methodology section opens by stating that a user study is chosen because the research questions concern observed developer behavior rather than tool performance
- **THEN** the requirement is satisfied

### Requirement: Secondary-data ethics
The guidance SHALL cover, as advisory prose in the same style as the human-participants advisory and not as a required section or mechanical check, what a proposal working on mined, scraped, or third-party data is expected to address: where the data comes from and under what license or terms it may be used, whether it contains personal data and how that is handled, and whether redistribution or publication of derived data is permitted.

#### Scenario: Mining proposal silent on data provenance
- **WHEN** a proposal plans to mine public repositories and says nothing about licensing or personal data in commit metadata
- **THEN** the guidance identifies the omission as a question a supervisor will ask, while no mechanical check reports an error

#### Scenario: Advisory stays advisory
- **WHEN** a proposal addresses provenance and licensing in one sentence inside its methodology
- **THEN** that satisfies the guidance, and no separate data-ethics section is expected
