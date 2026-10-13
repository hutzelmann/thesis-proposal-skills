## ADDED Requirements

### Requirement: Build hands over to the student

A completed build or hand-in export — through the built-in pipeline or a workspace build definition — SHALL close with the stage handoff (skill-packaging), naming the pipeline that produced the document. The route SHALL follow the proposal's position: with no open markers and a review of the current text with no blocker, the proposal stands at handed in and the recommended step is the student's own — rename the document to carry their name and send it to the supervisor — after which supervisor feedback, once it arrives, becomes the next revision; with open markers in the document, the recommended step is resolving them, sending it as a draft for discussion the alternative; with no current review, a review before sending is recommended and sending as it is the alternative. A failed or refused build keeps its existing rules and is not followed by a handoff that suggests another pipeline.

#### Scenario: Ready proposal built
- **WHEN** the PDF of a proposal with a current ready review and no markers is built
- **THEN** the handoff names the pipeline, places the proposal at handed in, and recommends renaming and sending it, with no quoted continuation phrase required for a step that is the student's own

#### Scenario: Built before any review
- **WHEN** a clean draft without a review beside it is built
- **THEN** the handoff recommends a review before sending and names sending it as it is as the alternative

#### Scenario: Workspace build failed
- **WHEN** a workspace build definition fails
- **THEN** the failure is reported and no handoff recommends the built-in pipeline
