## ADDED Requirements

### Requirement: Review hands over a bounded revision path

The chat summary of a review SHALL close with the stage handoff (skill-packaging), its route set by the verdict:

- **needs revision**: the recommended step is a revision of the proposal blockers, named briefly, followed by a fresh review of the changed text; the optional refinements worth taking MAY be one alternative, by number, and are never part of the recommended step. Where a blocker can only be resolved by a choice of the student's, that choice is put as an anchored decision.
- **ready**: the proposal stands at ready for supervisor discussion; the recommended step is the final check of language, title and timeline before the hand-in build, and the hand-in export MAY be the alternative. The clarify-early agenda is named as the thesis's first weeks, never as a step before hand-in.
- **no viable thesis core**: the recommended step is reworking the idea, put as an anchored question about the object or contribution the draft lacks; a sentence-level revision is never recommended.

The review SHALL NOT apply a finding, start a revision or run any other step: on approval, the revision follows the writing skill's instructions. When the user asks what to do with the feedback, the answer SHALL state the remaining path to the next milestone in at most a few sentences — at most the revision and one fresh review, whose earlier-round rules keep the findings from growing — and close with the handoff.

#### Scenario: Needs revision
- **WHEN** the review finds two proposal blockers and four optional refinements
- **THEN** the handoff recommends revising the two blockers followed by a fresh review, lists refinements only as an alternative, and the proposal file is unchanged

#### Scenario: Asked what to do with the feedback
- **WHEN** after a needs-revision review the user asks "What do we do now with that feedback?"
- **THEN** the answer states that one revision of the blockers and one fresh review stand between the draft and supervisor discussion, closes with the handoff, and leaves the proposal unchanged

#### Scenario: Blocker needs the student's choice
- **WHEN** a blocker states that a research question cannot fail as phrased and the methodology already names two measures the student could commit to
- **THEN** the handoff quotes the research question, says that choosing the measure decides what the thesis must show, offers the two measures and a way out, and does not ask an unanchored question

#### Scenario: Ready
- **WHEN** the review is ready with three clarify-early items
- **THEN** the handoff places the proposal at ready for supervisor discussion, recommends the final check before the hand-in build, and does not recommend settling the clarify-early items first

#### Scenario: No viable thesis core
- **WHEN** the verdict is no viable thesis core
- **THEN** the handoff recommends reworking the idea and does not recommend revising sentences of the draft
