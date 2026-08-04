## MODIFIED Requirements

### Requirement: Conflict validation with consequences
When a requested customization conflicts with defaults (e.g. requiring a default-forbidden section, or loosening a default size constraint), the skill SHALL apply it only after explaining the conflict and its consequences for checks and reviews.

#### Scenario: Detailed work plan requirement
- **WHEN** the user asks for a required work plan with milestones
- **THEN** the skill explains that the default timeline is a single coarse sentence and that work-plan headings are forbidden by default, applies the detailed timeline mode on confirmation, and notes that checks will now accept a phase table

#### Scenario: Timeline asked to be removed
- **WHEN** the user says their program does not want any timeline at all
- **THEN** the skill explains that the timeline is required by default, and applies a required-section override that omits it only after confirmation
