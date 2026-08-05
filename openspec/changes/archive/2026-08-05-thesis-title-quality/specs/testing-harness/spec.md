## ADDED Requirements

### Requirement: Title-alarm coverage
The corpus SHALL carry at least one fixture whose title trips several title tells at once, with the tells encoded in its `expected.json` oracle, alongside the existing fixtures whose titles trip none. The agent-judgment half of the title rule — recognising that a proper noun names a tool carried as the instrument, and offering abstracted alternatives — is not reachable by any offline test, so it SHALL be covered by a metered L2 eval task scoring whether the skill raises the title, names the certificate consequence, and offers alternatives without silently rewriting the title.

#### Scenario: Bad-title fixture
- **WHEN** the corpus is exercised against the deterministic check
- **THEN** the bad-title fixture reports its title tells as warnings, matching its oracle, and the run does not fail on them

#### Scenario: Clean-title control
- **WHEN** a fixture whose title names a contribution and its object is checked
- **THEN** no title warning is emitted and its oracle records none

#### Scenario: L2 title alarm scored
- **WHEN** the metered title eval runs against a proposal whose title carries a tool name as the instrument
- **THEN** the score reflects whether the skill raised the title, named the certificate consequence, and offered abstracted alternatives rather than replacing the title unannounced
