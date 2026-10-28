## ADDED Requirements

### Requirement: Ideation timing and tone graded
The Socratic dialogue rubric SHALL grade both failure directions in every ideation dialogue it judges. Beside its existing criteria it SHALL fail a transcript with a weakness verdict, an imagined adversary or prior work framed as covering the idea before the challenge-phase announcement; an "I don't know" answered with a harder question instead of kinds of answer; or more than three consecutive question-ending turns between the bookends.

#### Scenario: Skeptic invoked in the opening phase
- **WHEN** an assistant turn before any challenge-phase announcement asks the student to imagine a skeptical expert
- **THEN** the Socratic judge grades the transcript incorrect

#### Scenario: Gentle but supplying
- **WHEN** a transcript passes every timing and tone criterion but the assistant supplies a research question for the student's problem
- **THEN** the Socratic judge still grades it incorrect under the existing no-supply criterion

#### Scenario: Harder question after "I don't know"
- **WHEN** the student answers "I don't know" and the assistant's next turn asks a more abstract question without offering kinds of answer
- **THEN** the Socratic judge grades the transcript incorrect

### Requirement: Novice ideation dev scenario
A subscription dev-runner scenario SHALL replay a synthetic novice through scripted follow-up turns: workplace experience, short non-native English, a vague problem, thin answers to expert-level questions and one "I don't know", lookups declined. Its transcript SHALL be graded by the Socratic rubric with a criterion on the opening phase and the "I don't know" turn; the grade is dev-runner L2. A reactive novice persona for the matrix is a separate, cost-gated decision.

#### Scenario: Novice replay graded over the transcript
- **WHEN** the novice scenario runs with the dev judge
- **THEN** the judge grades the transcript of all turns against the Socratic rubric and the novice criterion, and the result is labelled as a dev-runner result

#### Scenario: Synthetic content only
- **WHEN** the novice scenario's turns are reviewed
- **THEN** they describe a synthetic topic and carry no sentence from any real student's session
