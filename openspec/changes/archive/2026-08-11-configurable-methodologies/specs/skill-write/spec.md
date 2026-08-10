## ADDED Requirements

### Requirement: The methodology set comes from the merged guidance
The write skill SHALL take the acceptable methodologies and their required subsections from the merged guidance — shipped defaults with the workspace declaration applied — rather than from the shipped set alone. When a proposal uses a workspace-declared branch, the skill SHALL fill its subsections from the guidance that branch declares, and SHALL NOT substitute the content contract of a shipped branch with a similar name.

#### Scenario: Writing into a workspace branch
- **WHEN** the workspace declares a methodology branch and the user chooses it
- **THEN** the skill writes that branch's declared subsections and follows the guidance declared for each

#### Scenario: Disabled branch not offered
- **WHEN** the workspace has disabled a shipped methodology
- **THEN** the skill does not offer it when the methodology is chosen
