# guidance-model Specification

## Purpose
Defines how proposal-writing guidance is stored, which parts are machine-readable, and how users customize it per workspace without touching installed skills.
## Requirements
### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order, mirroring the THI exposé template: "Introduction and Motivation", "Problem Statement and Research Questions", "Objectives", "Related Work", "Methodology: <Methodology>", "Expected Contributions and Results", and "Work Plan and Schedule" — where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Simulation Study, Empirical Model Evaluation, Mixed Methods. Each methodology has a fixed set of required subsections, every one of which begins with "Use Case Definition". Exactly one methodology SHALL be declared per proposal. Canonical German section titles SHALL be defined for all of the above.

#### Scenario: Two methodology sections
- **WHEN** a proposal declares two methodology sections
- **THEN** guidance-following tooling reports a violation of the one-declared-methodology rule

#### Scenario: Combined qualitative and quantitative strands
- **WHEN** a thesis combines a qualitative and a quantitative strand
- **THEN** the guidance directs it to the Mixed Methods branch with its Qualitative Strand, Quantitative Strand, and Integration subsections, rather than to two stacked methodology sections

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

### Requirement: Human-participant research guidance
The default guidance SHALL address ethics approval, informed consent, and personal-data handling for methodologies involving human participants (User Study, Controlled Experiment, and Mixed Methods with a human strand). This guidance SHALL be advisory prose only: it SHALL NOT introduce a required section or subsection, and the mechanical check SHALL NOT enforce it.

#### Scenario: Proposal omits consent and data handling
- **WHEN** a controlled-experiment proposal says nothing about consent or personal-data handling
- **THEN** the mechanical check reports no error, and the content review may raise it as missing substance

### Requirement: Forbidden content
The default guidance SHALL forbid: supervisor sections in the body, deliverables/code fragments, personal data in the body (matriculation number, address, email, study program), preliminary thesis chapter structures, and confidentiality markers. Work plans, timelines, and expected results SHALL NOT be forbidden — they are required sections of the exposé template.

#### Scenario: Timeline present
- **WHEN** a proposal contains a schedule heading
- **THEN** tooling accepts it under default guidance, because the exposé template requires a work plan

#### Scenario: Supervisor named in the body
- **WHEN** a proposal contains a supervisor heading in the body
- **THEN** tooling reports it as forbidden content and points at the title-page metadata instead

### Requirement: Workspace override file
A user-owned `guidelines.md` in the workspace SHALL override/extend defaults. It consists of a machine-readable fenced TOML block (keys include `required_sections`, `forbidden_sections`, `page_limit`, `min_references`) plus freeform prose. Merge semantics: a user key wins over the default per key; list values replace defaults entirely; un-forbidding a default-forbidden section is allowed. Absent file means pure defaults.

#### Scenario: Supervisor forbids a section the default permits
- **WHEN** `guidelines.md` adds `timeline` to `forbidden_sections`
- **THEN** checks reject a Timeline heading in that workspace even though the default template permits it

#### Scenario: Raised reference minimum
- **WHEN** `guidelines.md` sets `min_references = 14`
- **THEN** a proposal with 10 references fails the reference-count check

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, and research-question list conventions. All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy) SHALL remain prose guidance for agents.

#### Scenario: Semantic rule stays prose
- **WHEN** a rule concerns argument quality rather than document skeleton
- **THEN** it appears only in prose guidance and is never encoded as structured check data

### Requirement: Structured data and prose must not drift
Every canonical title present in the structured guidance data SHALL appear verbatim in the prose guidance. Automated verification SHALL fail when they diverge.

#### Scenario: Title renamed in prose only
- **WHEN** a section title is changed in prose guidance but not in the structured data
- **THEN** the consistency verification fails

