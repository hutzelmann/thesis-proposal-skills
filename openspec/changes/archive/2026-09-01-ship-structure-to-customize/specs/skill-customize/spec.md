## ADDED Requirements

### Requirement: Structured guidance data ships with the skill
The installed skill SHALL contain the structured guidance data (the machine-checkable skeleton) as a synchronized copy, so that every value the skill must reproduce verbatim — override key paths, default list contents, shipped methodology branch ids — is readable inside the skill itself. The skill SHALL NOT depend on a sibling skill's copy or on recalled knowledge for these values.

#### Scenario: Re-allowing one default-forbidden heading
- **WHEN** the user asks that one default-forbidden section be allowed again, which requires writing the full default forbidden list minus that entry because list overrides replace rather than append
- **THEN** the skill reads the default list from its own shipped copy of the structured guidance data and reproduces it exactly, rather than reconstructing it from memory

#### Scenario: Disabling a shipped branch by id
- **WHEN** the user asks that a shipped methodology no longer be acceptable
- **THEN** the skill resolves the branch id against its own shipped copy of the structured guidance data before writing `enabled = false`
