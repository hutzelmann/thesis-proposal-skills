# skill-customize Specification

## Purpose
Dialog-driven management of the workspace `guidelines.md` override file, translating supervisor requirements into the guidance model safely.
## Requirements
### Requirement: Dialog-driven override management
The skill SHALL create or edit `guidelines.md` from a conversation about the user's or supervisor's requirements, writing the machine-readable TOML block and prose sections per the guidance model.

The skill SHALL write override keys at the key path the value occupies in the structured guidance data, and SHALL NOT invent shorter or flatter spellings. When it encounters an existing workspace file using a retired key, it SHALL migrate that key rather than leaving it in place, and SHALL say which keys it moved.

#### Scenario: Page limit request
- **WHEN** the user says the supervisor wants at most 3 pages
- **THEN** the skill writes the page limit at its structure key path inside the TOML block

#### Scenario: Existing file uses retired keys
- **WHEN** the workspace `guidelines.md` predates the key migration
- **THEN** the skill rewrites those keys at their current paths and reports what it moved

### Requirement: Conflict validation with consequences
When a requested customization conflicts with defaults (e.g. requiring a default-forbidden section, or loosening a default size constraint), the skill SHALL apply it only after explaining the conflict and its consequences for checks and reviews.

#### Scenario: Detailed work plan requirement
- **WHEN** the user asks for a required work plan with milestones
- **THEN** the skill explains that the default timeline is a single coarse sentence and that work-plan headings are forbidden by default, applies the detailed timeline mode on confirmation, and notes that checks will now accept a phase table

#### Scenario: Timeline asked to be removed
- **WHEN** the user says their program does not want any timeline at all
- **THEN** the skill explains that the timeline is required by default, and applies a required-section override that omits it only after confirmation

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

### Requirement: Structured guidance data ships with the skill
The installed skill SHALL contain the structured guidance data (the machine-checkable skeleton) as a synchronized copy, so that every value the skill must reproduce verbatim — override key paths, default list contents, shipped methodology branch ids — is readable inside the skill itself. The skill SHALL NOT depend on a sibling skill's copy or on recalled knowledge for these values.

#### Scenario: Re-allowing one default-forbidden heading
- **WHEN** the user asks that one default-forbidden section be allowed again, which requires writing the full default forbidden list minus that entry because list overrides replace rather than append
- **THEN** the skill reads the default list from its own shipped copy of the structured guidance data and reproduces it exactly, rather than reconstructing it from memory

#### Scenario: Disabling a shipped branch by id
- **WHEN** the user asks that a shipped methodology no longer be acceptable
- **THEN** the skill resolves the branch id against its own shipped copy of the structured guidance data before writing `enabled = false`

