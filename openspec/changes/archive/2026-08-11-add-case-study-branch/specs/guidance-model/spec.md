## MODIFIED Requirements

### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order: "Introduction to the Topic", "Contribution to the State-of-the-Art", "Research Focus and Research Questions", "Methodology for Research: <Methodology>" where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Empirical Model Evaluation, Case Study, and "Timeline". Each methodology has a fixed set of required subsections. Exactly one methodology SHALL be used per proposal. Canonical German section titles SHALL be defined for all of the above.

The declared order SHALL be enforced, not merely the presence of each section: a proposal whose canonical sections appear in a different order than the guidance declares SHALL be reported as a violation. Under a workspace override that declares its own required-section list, the order of that list SHALL be the enforced order.

#### Scenario: Mixed methodologies
- **WHEN** a proposal combines two methodologies
- **THEN** guidance-following tooling reports a violation of the single-methodology rule

#### Scenario: Canonical sections out of order
- **WHEN** a proposal carries all five canonical sections but places the timeline before the introduction
- **THEN** guidance-following tooling reports an ordering violation

#### Scenario: Override list defines the order
- **WHEN** a workspace declares its own required-section list in a different order than the default
- **THEN** the workspace's order is the one enforced, and the default order is not applied

## ADDED Requirements

### Requirement: Case studies declare their case, sources, and limits
The Case Study branch SHALL require the subsections "Case and Units of Analysis" / "Fall und Analyseeinheiten", "Data Collection" / "Datenerhebung", and "Analysis" / "Auswertung". The content contract SHALL require: in Case and Units of Analysis, what the case is and its context, the units of analysis within it, why this case suits the research questions — case selection is intentional (a typical, critical, or revelatory case), never a sample — and what access exists; in Data Collection, which sources are drawn on and how each is recorded, with more than one source so findings can be triangulated, and with consent and confidentiality toward the host organisation addressed; in Analysis, how the material is coded and synthesised into answers, and what a single case can and cannot show.

#### Scenario: Case selection unexplained
- **WHEN** a Case Study proposal describes an organisation without saying why this case suits the research questions
- **THEN** guidance-following tooling asks for the selection rationale

#### Scenario: Single data source
- **WHEN** the Data Collection subsection names interviews as the only source
- **THEN** the guidance asks for a second source or an acknowledgment that findings cannot be triangulated

#### Scenario: Generalization unbounded
- **WHEN** the Analysis subsection promises conclusions about industry practice in general from one case
- **THEN** the guidance asks for the single-case limitation to be stated

#### Scenario: Observation versus intervention
- **WHEN** a proposal plans to change the studied organisation's process and evaluate the change
- **THEN** the guidance notes that intervening in the case is action research, which the shipped set does not contain, and points at the workspace mechanism
