## ADDED Requirements

### Requirement: Handoff stays in chat

The stage handoff (skill-packaging) of a supervise run SHALL address the professor in chat and SHALL NOT enter the feedback file, whose closing note stays the only closing text the student receives. Its `Where it stands:` line SHALL carry the verdict tier and the number of numbered points; the recommended step is the professor's own — edit and send the draft through their own channel — and a resubmission is named as the next run, which reads this round as its earlier one. The handoff SHALL NOT promise a meeting, an approval or any other commitment on the professor's behalf.

#### Scenario: Feedback drafted
- **WHEN** a needs-revision feedback with two numbered points is written
- **THEN** the chat closes with a handoff naming the tier and the two points and recommending that the professor edit and send the draft, and the feedback file contains no handoff lines

#### Scenario: Ready feedback
- **WHEN** the feedback is ready with no numbered point
- **THEN** the handoff names the ready tier and recommends sending the draft, and promises nothing on the professor's behalf
