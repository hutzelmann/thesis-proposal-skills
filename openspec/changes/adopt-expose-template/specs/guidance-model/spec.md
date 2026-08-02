## MODIFIED Requirements

### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order, mirroring the THI exposé template: "Introduction and Motivation", "Problem Statement and Research Questions", "Objectives", "Related Work", "Methodology: <Methodology>", "Expected Contributions and Results", and "Work Plan and Schedule" — where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Simulation Study, Empirical Model Evaluation, Mixed Methods. Each methodology has a fixed set of required subsections, every one of which begins with "Use Case Definition". Exactly one methodology SHALL be declared per proposal. Canonical German section titles SHALL be defined for all of the above.

#### Scenario: Two methodology sections
- **WHEN** a proposal declares two methodology sections
- **THEN** guidance-following tooling reports a violation of the one-declared-methodology rule

#### Scenario: Combined qualitative and quantitative strands
- **WHEN** a thesis combines a qualitative and a quantitative strand
- **THEN** the guidance directs it to the Mixed Methods branch with its Qualitative Strand, Quantitative Strand, and Integration subsections, rather than to two stacked methodology sections

### Requirement: Forbidden content
The default guidance SHALL forbid: supervisor sections in the body, deliverables/code fragments, personal data in the body (matriculation number, address, email, study program), preliminary thesis chapter structures, and confidentiality markers. Work plans, timelines, and expected results SHALL NOT be forbidden — they are required sections of the exposé template.

#### Scenario: Timeline present
- **WHEN** a proposal contains a schedule heading
- **THEN** tooling accepts it under default guidance, because the exposé template requires a work plan

#### Scenario: Supervisor named in the body
- **WHEN** a proposal contains a supervisor heading in the body
- **THEN** tooling reports it as forbidden content and points at the title-page metadata instead

## ADDED Requirements

### Requirement: Research question count
The default guidance SHALL permit one to three research questions, matching the exposé template's research-question table, and tooling SHALL report a count above the maximum.

#### Scenario: Four sub-questions
- **WHEN** a proposal declares four research questions
- **THEN** the check reports that at most three are allowed

### Requirement: Objectives distinct from research questions
The default guidance SHALL distinguish objectives from research questions: an objective states what the work will do and begins with an action verb, while a research question states what the work will find out and must be analytical. Construction goals ("how can X be built") SHALL belong to Objectives and SHALL NOT appear among the research questions.

#### Scenario: Construction goal phrased as a research question
- **WHEN** a research question reads "how can X be implemented"
- **THEN** the review flags it and suggests moving it to Objectives
