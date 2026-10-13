## ADDED Requirements

### Requirement: Writing pass hands over

A writing pass SHALL report what changed, what the check still reports and which markers remain, and SHALL close with the stage handoff (skill-packaging). Its route SHALL follow from what the pass changed, the first that applies:

- a decision the pass could not settle, which the student owes the proposal → that decision as an anchored choice, before any review, since a review would only raise it again;
- a pass that changed the research questions, the scope, the method, the contribution delta, or a passage a blocker of the review beside the proposal cites → that review is superseded, and the recommended step is a fresh review of the changed text;
- a complete draft with no review beside it → a review;
- a pass that changed wording only, beside a review that still covers the text with no blocker → the final check before the hand-in build;
- a reference shortfall the check reports → a literature search, recommended or as the alternative depending on whether it is what blocks the next milestone.

The skill SHALL NOT run a review, build or publish within the pass. Open `[TODO: …]` markers SHALL be sorted in the handoff into decisions the student owes the proposal and execution details whose deferral record (guidance-model, Readiness) can be filled. The decisions are what blocks the next milestone and are put as anchored decisions; the execution details MAY be proposed for the notes file's Open Points. Moving one is a writing step taken only on the user's approval: the marker leaves the proposal, its deferral record enters Open Points, and the Log records the move. A marker SHALL NOT otherwise be deleted to satisfy the check.

#### Scenario: Blockers applied
- **WHEN** the user asks to apply a review's blockers and the pass rewrites the passages they cite
- **THEN** the handoff says the review on file describes the earlier text and recommends a fresh review, and the review file is left unchanged

#### Scenario: Scope narrowed
- **WHEN** a pass reduces four research questions to two
- **THEN** the handoff recommends a fresh review of the narrowed draft, not merely that no current review exists

#### Scenario: Wording-only pass after a ready review
- **WHEN** a polishing pass changes sentences but no research question, scope, method, delta or blocker passage, and the review beside the proposal is ready
- **THEN** the handoff recommends the final check before the hand-in build, not another review

#### Scenario: Markers sorted after a first draft
- **WHEN** a first draft leaves a marker for the start month, one for whether indispensable data access is guaranteed, and three for model versions, audit sample size and log format
- **THEN** the handoff names the first two as decisions that block the next milestone and proposes moving the other three into the notes file, and no marker is moved in that pass

#### Scenario: Move approved
- **WHEN** the user approves moving the three execution-detail markers
- **THEN** they leave the proposal, each enters Open Points with its deferral record, and the Log records the move

## MODIFIED Requirements

### Requirement: Notes file consumed and maintained while writing
When a companion `<slug>.notes.md` exists for the target proposal, the write skill SHALL read it before drafting and honor its content: recorded decisions steer the draft (they are not re-litigated), and the Next Focus section informs which gaps to work on first. Decisions the writing session itself produces SHALL be recorded in the notes Decisions section. When the session resolves a proposal `[TODO: …]` marker, the skill SHALL move it to the notes Log as a done entry rather than deleting it. When no notes file exists, the skill SHALL proceed as before and MAY create one only when it has decisions, clarify-early items from an applied review, or markers the user approved moving to record — never an empty skeleton.

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

#### Scenario: Notes file created for approved marker moves
- **WHEN** the target proposal has no notes file and the user approves moving three execution-detail markers out of it
- **THEN** the skill creates the notes file with its five canonical sections and records the three under Open Points with their deferral records
