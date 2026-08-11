## MODIFIED Requirements

### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order: "Introduction to the Topic", "Contribution to the State-of-the-Art", "Research Focus and Research Questions", "Methodology for Research: <Methodology>" where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Empirical Model Evaluation, and "Timeline". Each methodology has a fixed set of required subsections. Exactly one methodology SHALL be used per proposal. Canonical German section titles SHALL be defined for all of the above.

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

### Requirement: Model evaluations fix data, baselines, and analysis in advance
The Empirical Model Evaluation branch SHALL require the subsections "Data and Baselines" / "Daten und Baselines", "Experimental Setup" / "Versuchsaufbau", and "Analysis" / "Auswertung". The content contract SHALL require: in Data and Baselines, which datasets are used, where they come from and under what license, and which state-of-the-art baselines the models are compared against — or a justification why no baseline exists; in Experimental Setup, the train/validation/test protocol including how leakage between splits is prevented, and the models, features, and infrastructure involved; in Analysis, which metrics answer the research questions and why those metrics, plus how variance across runs is handled. The guidance SHALL state that benchmark-style comparisons of existing models or tools use this branch.

#### Scenario: No baselines named
- **WHEN** an Empirical Model Evaluation proposal evaluates only its own model configurations against each other
- **THEN** guidance-following tooling asks for state-of-the-art baselines or an explicit justification of their absence

#### Scenario: Split protocol silent on leakage
- **WHEN** the Experimental Setup subsection names a train/test split without saying how leakage is prevented
- **THEN** the guidance asks for the leakage discussion

#### Scenario: Metrics unjustified
- **WHEN** the Analysis subsection lists metrics without connecting them to the research questions
- **THEN** the guidance asks why these metrics answer these questions

#### Scenario: Benchmark study homed here
- **WHEN** a proposal compares existing published models on a public benchmark without training a new one
- **THEN** the guidance accepts Empirical Model Evaluation as the fitting branch
