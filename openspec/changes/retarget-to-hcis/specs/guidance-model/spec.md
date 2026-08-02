## MODIFIED Requirements

### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order: "Introduction to the Topic", "Contribution to the State-of-the-Art", "Research Focus and Research Questions", and "Methodology for Research: <Methodology>" where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Simulation Study, Empirical Model Evaluation, Mixed Methods. Each methodology has a fixed set of required subsections. Exactly one methodology SHALL be declared per proposal. Canonical German section titles SHALL be defined for all of the above.

#### Scenario: Two methodology sections
- **WHEN** a proposal declares two methodology sections
- **THEN** guidance-following tooling reports a violation of the one-declared-methodology rule

#### Scenario: Combined qualitative and quantitative strands
- **WHEN** a thesis combines a qualitative and a quantitative strand
- **THEN** the guidance directs it to the Mixed Methods branch with its Qualitative Strand, Quantitative Strand, and Integration subsections, rather than to two stacked methodology sections

## ADDED Requirements

### Requirement: Human-participant research guidance
The default guidance SHALL address ethics approval, informed consent, and personal-data handling for methodologies involving human participants (User Study, Controlled Experiment, and Mixed Methods with a human strand). This guidance SHALL be advisory prose only: it SHALL NOT introduce a required section or subsection, and the mechanical check SHALL NOT enforce it.

#### Scenario: Proposal omits consent and data handling
- **WHEN** a controlled-experiment proposal says nothing about consent or personal-data handling
- **THEN** the mechanical check reports no error, and the content review may raise it as missing substance
