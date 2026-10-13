## ADDED Requirements

### Requirement: Readiness coverage
The fixture corpus SHALL test proportionate review in both directions with fixtures that differ only where the judgement under test differs:

- an **overblocking control**: a check-clean proposal whose substance tests pass while it leaves bounded execution decisions open — the compared models chosen at the thesis start by a stated rule with no version named, an optional expert assessment that no research question depends on and whose organisational arrangements are not stated, and a sample size to be fixed by a pilot;
- an **underblocking control**: the same proposal with one change, making a research question answerable only through access to a partner organisation that is still to be negotiated;
- a **convergence workspace**: the overblocking control's text beside an earlier review whose blockers that text resolves and which lists a clarify-early item about a passage the text leaves unchanged.

Each proposal fixture SHALL carry an `expected.json` encoding its check-clean state. Over them, dev-runner scenarios and registered Inspect tasks SHALL assert with pure verdict functions, each exercised by L0 tests without a model call: the overblocking control's review opens with the ready verdict, its blocker section holds no item, and its clarify-early section — the early-thesis agenda — holds at least one; the underblocking control's review opens with the needs-revision verdict and carries a blocker concerning the doubtful access; the convergence review opens ready, carries an earlier-round section marking the earlier blockers resolved, and lists no blocker about the unchanged passage; and a supervise run over the overblocking control produces feedback that opens with the ready tier, carries no numbered point, carries a clarify-early block of at most five items, and promises no meeting. A model-graded rubric SHALL judge the review each of the three review scenarios produces against the readiness classification: each blocker names its failed test and why it must be settled before approval, no blocker rests on an element merely being unspecified, each clarify-early item carries its deferral record, and no requirement exceeds the applicable guidelines. These scenarios run on the subscription dev runner; a metered run of the Inspect tasks is a separate cost-gated decision.

#### Scenario: Overblocking caught
- **WHEN** the review of the overblocking control opens with "needs revision" or lists the unnamed model versions as a blocker
- **THEN** the readiness verdict fails without model involvement

#### Scenario: Underblocking caught
- **WHEN** the review of the underblocking control opens with "ready"
- **THEN** the dependency verdict fails without model involvement

#### Scenario: Escalation caught
- **WHEN** the convergence review raises the earlier clarify-early item as a blocker or omits the earlier-round section
- **THEN** the convergence verdict fails and names which property broke

#### Scenario: Controls stay check-clean
- **WHEN** the mechanical check runs over each readiness fixture
- **THEN** it reports exactly what the fixture's oracle encodes

## MODIFIED Requirements

### Requirement: Supervise feedback coverage

The harness SHALL carry an L1 task that runs the supervise skill against a synthetic raw submission fixture and asserts the feedback contract with dedicated verdict functions:

- the feedback exists as the slug-named feedback file;
- it carries at most five curated points, and carries none only when it opens with the ready tier or its lettered scope options carry its only blocker;
- it opens with one of the student-facing verdict tiers, including the idea-stage rendering in English and German;
- it contains no personal data from the fixture;
- every skill pointer in it names a skill that exists in the set;
- it carries the shared closing note verbatim in the language it was written in;
- any literature it cites is woven rather than listed: every DOI sits inside a numbered point or a prose block rather than a bulleted or bare citation list, is recorded in the companion notes file, and at most three distinct papers are cited; a feedback that cites no literature passes that verdict;
- it carries no format lecture — no sentence that pairs a document-convention subject (name or cover data, Gantt chart or phase list, chapter outline, timeline length, page count, reference link style) with an instruction to remove, shorten or restyle it;
- its markup stays light — no heading line, no blockquote line, no backtick;
- every standard or regulation designation it names that the normalized proposal does not carry has a URL in the paragraph of its first mention.

The closing-note verdict SHALL fail on a paraphrase, on the wrong language's snippet, and on a closing note that arrives with markup the shared snippet does not carry. The points verdict SHALL count numbered items only, so lettered scope options and the clarify-early block do not count as points. The synthetic fixtures SHALL include at least one non-standard-format submission (pasted-text fragment or PDF-shaped input) so normalization is exercised, not bypassed, and at least one over-scoped raw submission carrying a phase-by-phase work plan, a work package whose input size the submission never states, and claims about public regulations. Over that fixture, a dev-runner scenario SHALL assert, in addition to the feedback contract, that the feedback offers at least two lettered cut options with the choice left to the student, and that the review file carries a work-package table with a scope verdict and a verification section. Non-interactive runs (the Inspect task and the dev runner) SHALL pre-answer the borderline deferral and the lookup approval in the request so a single-turn run cannot stall waiting for the professor.

#### Scenario: Feedback contract asserted
- **WHEN** the supervise L1 task runs against a messy synthetic submission
- **THEN** the scorers report feedback presence, point count, verdict tier, personal-data absence, skill-pointer validity, closing-note fidelity, literature placement, format-lecture absence, markup and locators as separate verdicts

#### Scenario: Ready feedback without points passes
- **WHEN** a produced feedback opens with the ready tier and carries no numbered point
- **THEN** the points verdict passes, while the same feedback opening with needs revision fails it

#### Scenario: Negated tier is not the verdict
- **WHEN** a produced feedback or review opens "not yet ready — needs revision"
- **THEN** the tier read is needs revision, so a pointless feedback with that opening fails the points verdict

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
