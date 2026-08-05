# testing-harness Specification

## Purpose
Automated verification that all skills work as specified across models: a three-layer test pyramid with deterministic fixtures and model-graded rubrics.
## Requirements
### Requirement: Three-layer pyramid
Testing SHALL provide: L0 unit tests for all shipped scripts (no model calls, CI-safe); L1 structural tests running each skill against fixture workspaces per model with deterministic artifact assertions; L2 rubric tests grading semantic quality via model judges (analytical RQ phrasing, Socratic compliance, review actionability, German quality).

#### Scenario: Script regression
- **WHEN** a check-script rule breaks
- **THEN** an L0 test fails without any model involvement

#### Scenario: Semantic regression
- **WHEN** a model under test produces implementation-goal research questions
- **THEN** the L2 rubric scores it below threshold and the run fails

### Requirement: Multi-turn ideation testing
Ideate SHALL be tested in multi-turn dialogues against student personas on the metered path. The dialogue suite SHALL comprise one long composite run and several short adversarial probes, replacing cooperative-only coverage:

- **Long composite run**: a scripted persona drives roughly eighteen rounds through distinct phases — administrative preamble, hesitant idea development, an extraction probe (a direct request for finished research questions), a topic pivot, convergence, and seeding. Phase boundaries are scripted so graders can attribute failures. Between rounds the harness SHALL assert workspace state mechanically: the notes file appears once a topic exists and grows across the dialogue, and no proposal file exists before convergence.
- **Short probes**: a stonewalling persona whose non-contributions must trigger the early stop (state saved to notes, no proposal file); a no-idea persona for whom floated hints must name their source and never form a topic menu; and an out-of-scope persona whose insistence must yield exactly one chat-only warning and a clean seed.

Two instruments SHALL grade student-originated content and tutoring quality:

- **Provenance check**: a pure function in the shared verdict module that takes the transcript and the seeded file and verifies the substantive content terms of the working title and candidate research-question directions occur in student turns — a term the student never voiced in any turn counts against the run. First utterance is deliberately not the criterion: good tutoring crispens the student's phrasing, so the assistant may voice the sharp term first and the student adopts it. It SHALL be exercisable by L0 tests without a model call.
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

### Requirement: Inverted-hybrid runners
Authoritative runs (model matrix, release gates, judge models) SHALL execute over metered API providers with native multi-model comparison and spend caps. Subscription-based CLI runs serve as the cheap everyday dev loop and are not the source of record. CI executes only L0 and lint by default; metered eval runs are budget-capped.

Every L1 verdict SHALL be defined once as a pure function in the shared verdict module, taking plain values and returning a pass flag with an explanation, and both runners SHALL reach a scenario's verdict through it rather than reimplementing the assertions. Because the verdicts are pure, each SHALL be exercisable by L0 tests without a model call.

A verdict that asserts a produced file is in the standard format SHALL establish that by running the mechanical check over it and judging the reported errors, never by inspecting the text for characteristic substrings. Errors that follow from information the scenario's input did not carry MAY be tolerated, and the tolerated set SHALL be explicit. Where a defect makes the file unbuildable but is invisible to the mechanical check — which extracts narrowly rather than parsing YAML — the verdict SHALL assert it directly, and SHALL be narrow enough to admit the shapes that do build.

The dev-runner scenario set SHALL cover the import skill. It SHALL therefore support scenarios that stage no proposal file and instead supply a source document in the request, and that assert against a file the skill creates — whose name the skill chooses — rather than one staged in advance.

Wherever a scenario's skill is licensed to choose the produced file's name — including scenarios that stage a seed the skill may replace with a fresh `<slug>.md` — the verdict SHALL locate the produced proposal in the workspace rather than assume a staged filename. The selection SHALL be a pure function in the shared verdict module, exercisable by L0 tests without a model call, and both runners SHALL grade the file it selects.

#### Scenario: Release gate
- **WHEN** a release-gating eval is run
- **THEN** it executes on the metered authoritative path with per-model logs, not on the subscription dev runner

#### Scenario: Verdict reached from both runners
- **WHEN** a scenario's L1 assertions are evaluated on the metered path and on the dev runner
- **THEN** both call the same shared verdict function and reach the same pass flag for the same produced artifact

#### Scenario: Import iterated without metered spend
- **WHEN** import guidance is being iterated on
- **THEN** the dev runner can exercise the import skill end to end, pasting the source document into the request and judging the file the skill creates

#### Scenario: Structurally broken output rejected
- **WHEN** a produced file contains the expected substrings but leaves the metadata block unclosed and the reference list malformed
- **THEN** the verdict fails on the mechanical check's errors rather than passing on the substrings

#### Scenario: Unbuildable file the mechanical check cannot see
- **WHEN** a produced file places a TODO marker as a bare line inside the metadata block, so the document converter rejects the block while the mechanical check reports no error
- **THEN** the verdict fails on that defect

#### Scenario: Marker shapes that do build are accepted
- **WHEN** the same marker appears as the value of a key, quoted or unquoted
- **THEN** the verdict does not fail, because those shapes parse

#### Scenario: Tolerated shortfall
- **WHEN** the source document carries fewer references than the guidance requires
- **THEN** the reference-count error alone does not fail the verdict, because the skill must not invent sources

#### Scenario: Verdict logic covered without a model
- **WHEN** an L1 verdict's failure modes are tested
- **THEN** L0 tests call the pure verdict function directly and no model is invoked

#### Scenario: Draft written to a fresh filename
- **WHEN** a write scenario's model creates a new `<slug>.md` instead of editing the staged seed in place
- **THEN** the verdict grades the created file, not the untouched seed

### Requirement: Publish filter regression coverage
The harness SHALL cover the publish skill's pandoc filters with regression tests, including at least one fixture whose research-question list contains an in-text citation; the filter output MUST contain the citation resolved rather than an unprocessed citation key. Tests requiring external converters SHALL be skipped cleanly when those tools are absent.

#### Scenario: Citation inside a research question
- **WHEN** the rq-filter regression test runs with pandoc available
- **THEN** the typst output wraps each research question and contains no unresolved citation keys

### Requirement: Session-derived fixtures
Fixtures MAY be curated from real skill-session output when the session used a synthetic topic. Such fixtures MUST be audited against the committed session log, MUST NOT contain personal data, and follow the same oracle rules as invented fixtures.

#### Scenario: Fixture curated from a demo session
- **WHEN** a session-derived fixture is added to the corpus
- **THEN** its content traces to a committed session log, contains no personal data, and ships with an `expected.json` oracle

### Requirement: Fixture corpus with oracles
Fixtures SHALL follow the fixture blueprint: synthetic proposals covering both languages, both levels, all quality tiers, every mechanical check rule (tripped at least once and passed at least once), every methodology branch, clean controls, and workflow states — each with an `expected.json` ground-truth oracle consumed by L1/L2. Fixtures MUST NOT contain content from real proposals; personal data in fixtures is obviously fake.

#### Scenario: New check rule added
- **WHEN** a new mechanical rule enters the check skill
- **THEN** at least one fixture trips it and one passes it, encoded in their oracles

### Requirement: Prose-relaying verdicts match without regard to case

A verdict that judges whether a skill relayed given content into its chat answer SHALL match case-insensitively. Sentence capitalisation is a property of prose, not of the finding being relayed, so a correct relay SHALL NOT fail on it.

#### Scenario: Relay begins a sentence with the finding

- **WHEN** the skill reports a finding as "Duplicate reference id `Lee24Index`" and the oracle records it as "duplicate reference id"
- **THEN** the verdict counts it as relayed

#### Scenario: Finding genuinely absent

- **WHEN** the skill's answer never mentions a finding the oracle records
- **THEN** the verdict does not count it, and enough missing findings still fail the scenario

### Requirement: Export paths are verified by building real documents

Automated verification SHALL build real documents on every export path the publish skill can resolve, over the full fixture corpus, and SHALL assert that each build completes and produces its declared outputs. A test that only exercises path selection, argument assembly, or offline helpers SHALL NOT be treated as coverage of a build path.

Such a test SHALL drive the shipped build entry point rather than reassembling the converter invocation, so that a defect in how the shipped code constructs that invocation is caught rather than reproduced.

#### Scenario: A broken tier fails the suite

- **WHEN** a change makes one output tier unable to produce a document
- **THEN** the export verification fails for that tier, naming it, without any model involvement

#### Scenario: Selection logic alone is not coverage

- **WHEN** the only test touching a tier verifies which engine would be chosen
- **THEN** that tier counts as unverified, because no document was produced

### Requirement: CI provides the document toolchain

Continuous integration SHALL provide the converter and engines the export verification needs, so those tests execute rather than skip. Toolchain provisioning SHALL use pre-built published images at pinned versions, so a failing run always indicates a change in this repository rather than an upstream update. Where an image cannot host the test runner, the export path it covers MAY be exercised by a script, and that script's invocation SHALL be guarded against divergence from the shipped build path by a test requiring no toolchain.

#### Scenario: Toolchain absent locally

- **WHEN** a contributor without the toolchain runs the suite
- **THEN** the build tests skip and the rest of the suite passes, while CI still executes them

#### Scenario: Script and shipped build diverge

- **WHEN** the shipped build path gains a converter filter that a CI build script does not
- **THEN** the divergence guard fails, independently of whether any toolchain is installed

### Requirement: Notes files excluded from draft selection
The shared draft-selection function SHALL treat files ending in `.notes.md` as non-proposal markdown, alongside the existing non-proposal names, so no verdict ever grades a notes file as the produced proposal. The exclusion SHALL be covered by L0 tests without a model call. Fixtures MAY ship notes files; a notes file carries no `expected.json` oracle obligations of its own.

#### Scenario: Notes file never selected as the draft
- **WHEN** a scenario workspace contains `energy-attack.notes.md` and `energy-attack.md`
- **THEN** draft selection returns `energy-attack.md` even when the notes file sorts first

#### Scenario: Exclusion tested without a model
- **WHEN** the L0 suite runs
- **THEN** a unit test exercises the `.notes.md` exclusion through the pure selection function


### Requirement: Title-alarm coverage
The corpus SHALL carry at least one fixture whose title trips several title tells at once, with the tells encoded in its `expected.json` oracle, alongside the existing fixtures whose titles trip none. The agent-judgment half of the title rule — recognising that a proper noun names a tool carried as the instrument, and offering abstracted alternatives — is not reachable by any offline test, so it SHALL be covered by a metered L2 eval task scoring whether the skill raises the title, names the certificate consequence, and offers alternatives without silently rewriting the title.

#### Scenario: Bad-title fixture
- **WHEN** the corpus is exercised against the deterministic check
- **THEN** the bad-title fixture reports its title tells as warnings, matching its oracle, and the run does not fail on them

#### Scenario: Clean-title control
- **WHEN** a fixture whose title names a contribution and its object is checked
- **THEN** no title warning is emitted and its oracle records none

#### Scenario: L2 title alarm scored
- **WHEN** the metered title eval runs against a proposal whose title carries a tool name as the instrument
- **THEN** the score reflects whether the skill raised the title, named the certificate consequence, and offered abstracted alternatives rather than replacing the title unannounced
