## ADDED Requirements

### Requirement: Methodology branches are a customization
The skill SHALL treat a request to add, replace, or remove a methodology as a workspace customization rather than an unsupported request, writing the branch into the workspace declaration.

When writing a branch the skill SHALL require the user to say what belongs in each subsection, and SHALL NOT invent that guidance to satisfy the format. When the user cannot say, the skill SHALL stop rather than produce a branch whose headings have no content contract.

The skill SHALL explain, before disabling a shipped branch, that proposals already declaring it will begin failing the check.

#### Scenario: Supervisor requires a methodology the defaults lack
- **WHEN** the user says their supervisor expects a case-study methodology
- **THEN** the skill asks what belongs under each subsection and writes the branch with that guidance

#### Scenario: User cannot describe a subsection
- **WHEN** the user asks for a branch but cannot say what one of its subsections should contain
- **THEN** the skill stops and says the branch cannot be written without it, rather than filling it in

#### Scenario: Disabling a shipped branch
- **WHEN** the user asks that a shipped methodology no longer be acceptable
- **THEN** the skill explains that existing proposals declaring it will fail the check, and applies the change on confirmation
