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

