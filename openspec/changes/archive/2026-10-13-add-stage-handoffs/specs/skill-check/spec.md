## ADDED Requirements

### Requirement: Proposal status on request

The check skill SHALL own the question where a proposal stands and what to do next, asked without a stage in progress. It SHALL answer it by running the mechanical check as usual and then reading, beside the proposal, the review file and the companion notes file where they exist, and SHALL close with the stage handoff (skill-packaging) placing the proposal on the milestone ladder. The status read SHALL stay within the check's read-only mandate and SHALL render no substance verdict: the only content judgement it adds is whether an existing review still covers the current text, judged on the research questions, scope, method, contribution delta and the passages the review's blockers cite.

Open `[TODO: …]` markers SHALL be sorted in the handoff into decisions the student owes the proposal and execution details whose deferral record (guidance-model, Readiness) can be filled; the handoff MAY propose moving the execution details into the notes file as clarify-early items, which is a writing step the user approves, never a step the check performs.

Routes, the first that applies: mechanical errors → a writing pass that fixes them; open markers that are decisions the student owes the proposal → those decisions, put as anchored choices, before any review; no errors and no review, or a superseded one → a fresh review; no errors and a current review with blockers → a revision of those blockers; no errors and a current review with no blocker → the hand-in build.

#### Scenario: Status asked in a fresh session
- **WHEN** the user asks where their proposal stands and the workspace holds a mechanically clean draft with no review file
- **THEN** the check runs, the proposal file stays byte-identical, and the handoff places it at complete draft and recommends a review of it

#### Scenario: Review beside the proposal judged an earlier scope
- **WHEN** the review file beside a clean draft judged research questions and a scope the current text no longer carries
- **THEN** the handoff says the review judged an earlier version and recommends a fresh review, and no review is written during the check

#### Scenario: Current ready review
- **WHEN** the draft is mechanically clean and the review beside it covers the current text with no blocker
- **THEN** the handoff places the proposal at ready for supervisor discussion and recommends building the hand-in, without building anything

#### Scenario: Open markers sorted
- **WHEN** the draft carries two markers that need the student's decision and three that are execution details
- **THEN** the handoff names the two as what blocks the next milestone, recommends settling them — the one with options in the student's text as an anchored choice — before a review, proposes moving the three into the notes file, and no file is modified

## MODIFIED Requirements

### Requirement: Two-bucket honest reporting
Results SHALL be presented in chat only (no file), split into "verified mechanically" and "flagged for the agent pass". The skill SHALL never claim semantic rules passed. The closing verdict line SHALL scope its claim explicitly: a mechanically clean result SHALL state that substance was not judged, so that "clean" is never readable as a statement about thesis potential, and the stage handoff that follows SHALL name the review as the step that renders the substance verdict whenever no current review covers the text.

#### Scenario: Clean mechanical run
- **WHEN** all mechanical checks pass
- **THEN** the report states mechanical success and explicitly defers semantic quality to review

#### Scenario: Verdict line scoped
- **WHEN** the check ends with its one-line verdict on a proposal without findings and no current review
- **THEN** the line states that the result is mechanical only and that substance was not judged, and the handoff's `Next:` line recommends a review of the draft without naming a skill

### Requirement: Agent pass for non-mechanical issues
An agent pass SHALL cover typos/grammar and content-level forbidden material that regexes cannot catch (e.g. expected results embedded in prose), and SHALL confirm that the timeline section actually states a timeframe. An expected result is an outcome asserted as though already obtained; an anticipated outcome phrased as an expectation — "the thesis expects", "it is hypothesized" — is the form the guidance requires (guidance-model, "Anticipated outcomes are stated as expectations") and SHALL NOT be flagged. The timeframe judgement SHALL accept the phrasings students genuinely use — semester labels, quarters, seasons, month names in either language — rather than a fixed set of date formats, and SHALL flag a phase breakdown or Gantt chart that the mechanical guard cannot see, including one supplied as an image.

#### Scenario: Hidden expected-results paragraph
- **WHEN** a methodology paragraph asserts concrete expected outcomes
- **THEN** the agent pass flags it as forbidden content

#### Scenario: Expectation stated as an expectation
- **WHEN** the analysis says "The thesis expects a configuration effect smaller than the model effects that repair studies report; a negligible effect would refute the premise"
- **THEN** the agent pass raises no finding on it, and the handoff of a proposal with a current ready review does not make rewording it a step before hand-in

#### Scenario: Timeline states no timeframe
- **WHEN** the timeline section is present and within its size constraint but names no start, no end, and no as-soon-as-possible statement
- **THEN** the agent pass flags it

#### Scenario: Semester phrasing accepted
- **WHEN** the timeline section reads "The thesis runs from WS 2026/27 to SoSe 2027."
- **THEN** the agent pass accepts it

#### Scenario: Gantt chart embedded as a figure
- **WHEN** the timeline section stays within three lines but embeds a Gantt chart as an image
- **THEN** the agent pass flags it as forbidden work-plan content
