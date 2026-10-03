## MODIFIED Requirements

### Requirement: Supervise feedback coverage

The harness SHALL carry an L1 task that runs the supervise skill against a synthetic raw submission fixture and asserts the feedback contract with dedicated verdict functions:

- the feedback exists as the slug-named feedback file;
- it carries at most five curated points;
- it opens with one of the student-facing verdict tiers, including the idea-stage rendering in English and German;
- it contains no personal data from the fixture;
- every skill pointer in it names a skill that exists in the set;
- it carries the shared closing note verbatim in the language it was written in;
- any literature it cites is woven rather than listed: every DOI sits inside a numbered point or a prose block rather than a bulleted or bare citation list, is recorded in the companion notes file, and at most three distinct papers are cited; a feedback that cites no literature passes that verdict;
- it carries no format lecture — no sentence that pairs a document-convention subject (name or cover data, Gantt chart or phase list, chapter outline, timeline length, page count, reference link style) with an instruction to remove, shorten or restyle it;
- its markup stays light — no heading line, no blockquote line, no backtick;
- every standard or regulation designation it names that the normalized proposal does not carry has a URL in the paragraph of its first mention.

The closing-note verdict SHALL fail on a paraphrase, on the wrong language's snippet, and on a closing note that arrives with markup the shared snippet does not carry. The points verdict SHALL count numbered items only, so lettered scope options do not count as points. The synthetic fixtures SHALL include at least one non-standard-format submission (pasted-text fragment or PDF-shaped input) so normalization is exercised, not bypassed, and at least one over-scoped raw submission carrying a phase-by-phase work plan, a work package whose input size the submission never states, and claims about public regulations. Over that fixture, a dev-runner scenario SHALL assert, in addition to the feedback contract, that the feedback offers at least two lettered cut options with the choice left to the student, and that the review file carries a work-package table with a scope verdict and a verification section. Non-interactive runs (the Inspect task and the dev runner) SHALL pre-answer the borderline deferral and the lookup approval in the request so a single-turn run cannot stall waiting for the professor.

#### Scenario: Feedback contract asserted
- **WHEN** the supervise L1 task runs against a messy synthetic submission
- **THEN** the scorers report feedback presence, point count, verdict tier, personal-data absence, skill-pointer validity, closing-note fidelity, literature placement, format-lecture absence, markup and locators as separate verdicts

#### Scenario: Personal data leak caught
- **WHEN** a run leaves the fixture's fake student name or matriculation number anywhere in the feedback
- **THEN** the personal-data verdict fails and names the leaking file

#### Scenario: Paraphrased closing note caught
- **WHEN** a run rewrites the closing note instead of quoting the shared snippet
- **THEN** the closing-note verdict fails and says the snippet was not carried verbatim

#### Scenario: Standalone literature list caught
- **WHEN** a produced feedback carries its papers as a bulleted list or as bare citation lines rather than inside the points
- **THEN** the literature verdict fails and names the offending DOI

#### Scenario: Unrecorded or excess literature caught
- **WHEN** a produced feedback cites a DOI absent from the notes file, or cites more than three distinct papers
- **THEN** the literature verdict fails and says which rule was broken

#### Scenario: Literature-free feedback passes the literature verdict
- **WHEN** a produced feedback cites no DOI
- **THEN** the literature verdict passes, because literature is conditional on approval and findings

#### Scenario: Format lecture caught
- **WHEN** a produced feedback tells the student that the Gantt chart and the chapter outline do not belong in the proposal
- **THEN** the format verdict fails and quotes the sentence

#### Scenario: Gantt chart cited as scope evidence passes
- **WHEN** a produced feedback says the plan's Gantt chart fits five dependent packages into fourteen weeks
- **THEN** the format verdict passes, because the chart is used as evidence and nothing asks for its removal

#### Scenario: Heavy markup caught
- **WHEN** a produced feedback carries a heading line or a skill name in backticks
- **THEN** the markup verdict fails and names the offending line

#### Scenario: Unlocated regulation caught
- **WHEN** a produced feedback names a regulation the normalized proposal does not carry, with no URL in that paragraph
- **THEN** the locator verdict fails and names the designation

#### Scenario: Later mention needs no second locator
- **WHEN** a produced feedback locates a new regulation at its first mention and names it again in a later point without a URL
- **THEN** the locator verdict passes

#### Scenario: Closing note is not the student's choice
- **WHEN** a produced feedback offers lettered cuts but only its closing note speaks of the student's decisions
- **THEN** the scope-options verdict fails, because the closing note is left out of the choice search

#### Scenario: Scope options asserted on the over-scoped fixture
- **WHEN** the scope scenario runs against the over-scoped raw submission
- **THEN** the verdicts report the lettered options, the student's choice, the review's work-package table with its scope verdict, and the verification section, alongside the feedback contract

#### Scenario: Offline verdict coverage
- **WHEN** the L0 suite runs
- **THEN** every supervise verdict function is exercised by unit tests without model calls

#### Scenario: Idea-stage feedback recognized
- **WHEN** the feedback opens with the idea-stage rendering instead of the blunt review vocabulary
- **THEN** the tier verdict passes in both English and German

#### Scenario: Headless run does not stall
- **WHEN** the L1 task or dev runner drives a borderline submission single-turn
- **THEN** the request's pre-answers resolve the deferral and the lookup approval, and the run completes

### Requirement: Dev-runner cost and helper-agent telemetry

The dev runner SHALL read the host's event stream rather than its plain text output. Beside each run's L1 verdict it SHALL report:

- the run's cost, number of turns and duration;
- the input and output token counts, with the cache read and cache write counts;
- the helper-agent tool calls observed (`Agent`, `Task`, `Workflow`);
- for scenarios that produce a supervise feedback, the feedback body's word count, excluding URLs and the closing note.

A dedicated verdict function SHALL pass when a run spawned no more helper agents than its scenario allows — none unless the scenario declares an allowance, which a supervise scenario does for its single verifier — and SHALL name the spawning calls when it exceeds the allowance. The runner SHALL report it as a separately labelled advisory verdict that does not change the scenario's exit status.

The runner SHALL accept a hard budget cap passed through to the host, and SHALL label each run as measuring the ambient host configuration or an isolated one prepared for the run, naming the isolated directory. Failures SHALL be reported as follows:

- a host result event marked as an error — a budget overrun among them — SHALL end the run as a runner failure whose message carries the host's subtype, its errors, and the cost and turns so far;
- a non-zero host exit without such an event SHALL report the host's stderr;
- a stream with no result event SHALL be a runner failure, never a silent success with empty telemetry.

The chat the verdicts read SHALL be the result event's final text and nothing else. All of this logic — the verdict, the event parsing, the telemetry, the command the runner builds and the summary it prints — SHALL be covered by L0 tests against recorded and synthetic event streams, and the telemetry and final-text readers SHALL be pinned against a recorded result event of the host, so a host field rename fails a test rather than blanking the line.

#### Scenario: Telemetry printed beside the verdict
- **WHEN** a dev-runner scenario completes
- **THEN** its summary carries cost, turns, duration, token counts including the cache pair, the helper-call list, the single-context verdict, and the configuration label

#### Scenario: Helper spawn detected from a recorded stream
- **WHEN** a recorded event stream contains a `Task` or `Agent` or `Workflow` tool call and the scenario allows none
- **THEN** the single-context verdict fails and names the call, without a model run

#### Scenario: Allowance respected
- **WHEN** a supervise scenario that allows one helper records exactly one `Agent` call
- **THEN** the single-context verdict passes, and a second call makes it fail naming both

#### Scenario: Feedback length reported
- **WHEN** a supervise scenario completes
- **THEN** the summary carries the feedback body's word count, without URLs and the closing note, as information that changes no verdict

#### Scenario: Budget cap passed through
- **WHEN** the runner is invoked with a budget cap and the host ends the run with an error result for exceeding it
- **THEN** the run ends as a runner failure whose message names the host's subtype, its errors, and the cost and turns so far — not as a skill failure and not with an empty message

#### Scenario: No result event
- **WHEN** the host exits without emitting a result event
- **THEN** the runner fails saying so, and no verdict is computed over partial narration

#### Scenario: Recorded shape pinned
- **WHEN** the host renames a result-event field the telemetry reads
- **THEN** the L0 test against the recorded result event fails naming the field

#### Scenario: Isolated run labelled
- **WHEN** the runner is invoked in isolated mode
- **THEN** the child runs against a configuration holding only settings and linked credentials, kept outside the workspace, and the summary labels the run as isolated and names that directory; without the flag it labels the run as ambient
