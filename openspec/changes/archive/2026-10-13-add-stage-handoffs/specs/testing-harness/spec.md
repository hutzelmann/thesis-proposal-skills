## ADDED Requirements

### Requirement: Handoff coverage
The harness SHALL test the stage handoff in conversations, including the two failures that motivated it: a user left to ask what to do with feedback, and a review that no longer covers the text being announced instead of a fresh one being recommended.

- **Follow-up turns**: a dev-runner scenario MAY list follow-up user turns. Each SHALL be sent to the same host session in the same workspace and the same configuration, under the same budget cap — which the host applies to the session's running total, so the conversation as a whole stays within it — with every billing and account-surface check applied per turn. A first turn whose stream carries no session identifier SHALL end the run as a runner failure, never as a single-turn pass. The verdict SHALL read the final turn's chat; the transcript of every turn SHALL be saved with the run.
- **Format verdict**: a pure function in the shared verdict module SHALL check the closing lines of a chat in English and German: exactly one position line, exactly one next-step line, at most two alternatives (as lines, or as list items under one empty alternative label; a list under any other label continues that label's line), none of them empty, no text after them, no skill identifier and no skill named as one in them, and a length cap. It SHALL be exercised by L0 tests without a model call. Every dev run SHALL report it as an advisory field that never changes the exit status.
- **Scenarios** on the subscription dev runner, each asserted with pure verdict functions:
  - a review followed by the turn "What do we do now with that feedback?" — the final chat passes the format verdict and the proposal is byte-identical after both turns;
  - a narrowed draft beside a review of its broader predecessor, asked where it stands — the first sentence of the next-step line recommends a fresh review, not merely mentions one, with a phrase to send; a sentence about the review says it judged an earlier version; and the proposal and review files are byte-identical;
  - a draft beside a review with a blocker, asked where it stands, then the approval of the revision with the decision it needs — the revision ran under the writing skill's instructions, the proposal changed, the review file is byte-identical, the check reports no errors, and the next-step line recommends a fresh review with a phrase to send;
  - a draft beside a current ready review, asked what comes next — no file is added or changed, and the next-step line recommends the final check or the hand-in build with a phrase to send, recommends no further review, and makes none of the review's clarify-early items a step;
  - a complete draft with two decision markers and three execution-detail markers, asked where it stands — the proposal is byte-identical and the chat passes the format verdict.
- **Rubric**: a model-graded rubric SHALL judge each scenario's transcript against its fixture's `semantic` list: the position is stated accurately, the recommended step is the one that unblocks the next milestone and its reason is given, a superseded review is recognised and a fresh one recommended, a decision step quotes the student's text and offers options from the student's material with a way out, nothing was done unasked, and no checklist is repeated. Its grades are dev-runner L2, not comparable to matrix results.
- **Routing**: the routing dataset SHALL carry the status moment — where a proposal stands, what to do next — expecting the check skill, and the canonical continuation phrases the handoffs suggest, each expecting the skill that owns the step.
- **Fixtures**: every new proposal fixture SHALL carry an `expected.json` oracle calibrated against the mechanical check.

Inspect twins and matrix cells for these scenarios are a separate, cost-gated decision.

#### Scenario: Follow-up turn sent to the same session
- **WHEN** a scenario lists the follow-up "What do we do now with that feedback?"
- **THEN** the runner sends it to the session the first turn opened, in the same workspace, and the verdict reads the reply to it

#### Scenario: Session identifier missing
- **WHEN** the first turn's stream carries no session identifier and the scenario lists a follow-up
- **THEN** the run ends as a runner failure naming the missing identifier

#### Scenario: Two next steps offered
- **WHEN** a chat closes with two `Next:` lines
- **THEN** the format verdict fails without model involvement

#### Scenario: Skill named in the handoff
- **WHEN** a chat's `Next:` line reads "use proposal-review on the narrowed draft"
- **THEN** the format verdict fails and names the skill identifier

#### Scenario: Advisory probe on an unrelated scenario
- **WHEN** a check-report dev run's chat ends without handoff lines
- **THEN** the summary reports the format verdict as failed and the run's exit status is unchanged

#### Scenario: Silent revision after "what now"
- **WHEN** the reply to "What do we do now with that feedback?" edits the proposal
- **THEN** the scenario verdict fails because the proposal is no longer byte-identical

#### Scenario: Approved revision carried out as a bare edit
- **WHEN** after the status answer the student approves the revision and the run edits the proposal without loading the writing skill
- **THEN** the scenario verdict fails, naming the skills the approval turn invoked

#### Scenario: Superseded review announced, not recommended
- **WHEN** the reply on the narrowed draft says only that no current review exists and recommends no review
- **THEN** the scenario verdict fails
