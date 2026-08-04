## MODIFIED Requirements

### Requirement: Multi-turn ideation testing
Ideate SHALL be tested in multi-turn dialogues against student personas on the metered path. The dialogue suite SHALL comprise one long composite run and several short adversarial probes, replacing cooperative-only coverage:

- **Long composite run**: a scripted persona drives roughly eighteen rounds through distinct phases — administrative preamble, hesitant idea development, an extraction probe (a direct request for finished research questions), a topic pivot, convergence, and seeding. Phase boundaries are scripted so graders can attribute failures. Between rounds the harness SHALL assert workspace state mechanically: the notes file appears once a topic exists and grows across the dialogue, and no proposal file exists before convergence.
- **Short probes**: a stonewalling persona whose non-contributions must trigger the early stop (state saved to notes, no proposal file); a no-idea persona for whom floated hints must name their source and never form a topic menu; and an out-of-scope persona whose insistence must yield exactly one chat-only warning and a clean seed.

Two instruments SHALL grade student-originated content and tutoring quality:

- **Provenance check**: a pure function in the shared verdict module that takes the transcript and the seeded file and verifies the substantive content terms of the working title and candidate research-question directions occur in student turns — a term the student never voiced in any turn counts against the run. First utterance is deliberately not the criterion: good tutoring crispens the student's phrasing, so the assistant may voice the sharp term first and the student adopts it (calibrated on the 2026-08-04 sonnet long run, where first-utterance semantics failed a judge-confirmed student-led session). It SHALL be exercisable by L0 tests without a model call.
- **Uptake rubric**: the L2 Socratic rubric SHALL judge, per phase, that assistant turns build on the student's preceding turn, ask at most one question, contain no praise padding, tell only conventions (never idea content), and confine direct administrative questions to the two bookends — the preamble block and the closing seeding step, which the rubric SHALL recognize as sanctioned direct questions.

#### Scenario: Long run graded per phase
- **WHEN** the long composite dialogue completes
- **THEN** the transcript is judged phase by phase, and a collapse at the extraction probe (assistant supplies finished research questions) fails that phase

#### Scenario: Notes growth asserted mechanically
- **WHEN** the long run passes its topic-establishing phase
- **THEN** the harness finds a notes file in the workspace and its size or content grows by the pivot phase, without any model judging this

#### Scenario: Stonewaller triggers early stop
- **WHEN** the stonewalling persona deflects three consecutive exchanges
- **THEN** the run passes only if the assistant named the impasse, the notes file records the state, and no proposal file was created

#### Scenario: Generic content fails provenance
- **WHEN** a seeded file's research-question directions use substantive terms that never occurred in any student turn
- **THEN** the provenance check fails the run without model involvement

#### Scenario: Bookend questions pass the rubric
- **WHEN** the assistant opens with the administrative block and closes confirming dates
- **THEN** the Socratic rubric does not count these as violations
