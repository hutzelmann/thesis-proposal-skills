## MODIFIED Requirements

### Requirement: Refinement preserves author content
When refining an existing proposal, the skill SHALL make minimal, surgical edits that preserve the author's substance and voice, and SHALL NOT re-write untouched sections wholesale.

When applying a review, the skill SHALL work through the review's proposal blockers and optional refinements item by item in the proposal, reporting per item what changed or why it was skipped, and SHALL record each clarify-early item — with its deferral record — under the notes file's Open Points instead of writing it into the proposal. A clarify-early item SHALL enter the proposal text only when the author asks for that item there; the skill SHALL NOT add a section, a work plan or protocol detail to carry such items.

#### Scenario: Improve research questions only
- **WHEN** the user asks to improve the research questions
- **THEN** only the research-question section (and directly dependent methodology references) changes

#### Scenario: Review applied without protocol creep
- **WHEN** the user asks to apply a review whose clarify-early section lists the exact model versions and the audit sample size
- **THEN** the proposal text gains neither, both are recorded under the notes file's Open Points with their deferral records, and the blockers and refinements are applied in the proposal

#### Scenario: Author asks for a deferred item in the text
- **WHEN** the author asks to state the model-selection rule in the methodology
- **THEN** the skill writes that one sentence and records nothing more of the item in the proposal

### Requirement: Notes file consumed and maintained while writing
When a companion `<slug>.notes.md` exists for the target proposal, the write skill SHALL read it before drafting and honor its content: recorded decisions steer the draft (they are not re-litigated), and the Next Focus section informs which gaps to work on first. Decisions the writing session itself produces SHALL be recorded in the notes Decisions section. When the session resolves a proposal `[TODO: …]` marker, the skill SHALL move it to the notes Log as a done entry rather than deleting it. When no notes file exists, the skill SHALL proceed as before and MAY create one only when it has decisions or clarify-early items from an applied review to record — never an empty skeleton.

#### Scenario: Prior decision honored
- **WHEN** the notes Decisions section records that a user study was rejected in favor of a prototype implementation
- **THEN** the draft builds on the prototype methodology and the skill does not re-open the methodology question

#### Scenario: Resolved marker logged
- **WHEN** the writing session fills the gap behind a proposal TODO marker
- **THEN** the marker is removed from the proposal and appears in the notes Log as done, with a note of what resolved it

#### Scenario: No notes file present
- **WHEN** the target proposal has no companion notes file and the session makes no recordable decision
- **THEN** the skill writes the proposal as usual and creates no notes file

#### Scenario: Notes file created for deferred items
- **WHEN** the target proposal has no notes file and an applied review carries clarify-early items
- **THEN** the skill creates the notes file with its five canonical sections and records the items under Open Points
