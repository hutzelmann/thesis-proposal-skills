## MODIFIED Requirements

### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order: "Introduction to the Topic", "Contribution to the State-of-the-Art", "Research Focus and Research Questions", "Methodology for Research: <Methodology>" where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, and "Timeline". Each methodology has a fixed set of required subsections. Exactly one methodology SHALL be used per proposal. Canonical German section titles SHALL be defined for all of the above.

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

### Requirement: Controlled experiments plan hypotheses, design, and analysis
The Controlled Experiment branch SHALL require the subsections "Hypotheses and Variables" / "Hypothesen und Variablen", "Design and Participants" / "Versuchsdesign und Teilnehmende", and "Statistical Analysis" / "Statistische Auswertung". The content contract SHALL require: in Hypotheses and Variables, the hypotheses being tested and, named separately, the independent variables with their treatments (what is manipulated) and the dependent variables with their measures (what is measured), plus the known confounding factors; in Design and Participants, the experiment design, how participants are recruited and assigned — random assignment, or a justified quasi-design — and the tasks or instruments used; in Statistical Analysis, the planned tests as a consequence of the chosen design, and the main threats to validity.

The guidance SHALL bound the User Study branch against this one: User Study covers observational, usability, and survey-style research with human participants; a study that manipulates a treatment to test a hypothesis belongs in Controlled Experiment.

#### Scenario: Variables named without hypotheses
- **WHEN** a Controlled Experiment proposal lists variables but states no hypothesis relating them
- **THEN** guidance-following tooling asks for the hypotheses the variables serve

#### Scenario: Manipulated and measured conflated
- **WHEN** the Hypotheses and Variables subsection lists variables without saying which are manipulated and which are measured
- **THEN** the guidance asks for the separation into independent variables with treatments and dependent variables with measures

#### Scenario: Tests unconnected to design
- **WHEN** the Statistical Analysis subsection names tests although no experiment design was stated
- **THEN** the guidance asks for the design the tests follow from

#### Scenario: Hypothesis-testing study declared as User Study
- **WHEN** a proposal declares the User Study methodology and its procedure manipulates a treatment to test a hypothesis
- **THEN** guidance-following tooling directs it to the Controlled Experiment branch
