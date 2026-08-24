## ADDED Requirements

### Requirement: Measured environments carry no eval definitions
No runner SHALL stage eval definitions, oracles, or assertion text into the environment the model under test can read: not the fixture oracles, and not the eval projections the skills ship for the standard's sake. A skill installed for a real user legitimately carries its eval projection; a skill installed for measurement SHALL NOT, because a model that can read what it will be graded on is not being measured.

#### Scenario: Dev runner stages a skill
- **WHEN** the dev runner installs a skill into its temp workspace
- **THEN** the installed copy contains no eval definition file, while scripts, references, and templates copy as shipped

#### Scenario: Routing rig stages the skill set
- **WHEN** the routing rig installs the skills into its isolated configuration
- **THEN** no installed skill carries an eval definition file

#### Scenario: Inspect staging stays a whitelist
- **WHEN** an Inspect task stages a fixture and a skill's assets
- **THEN** only the skill's references, scripts, and templates enter the sandbox, and the fixture's oracle never does
