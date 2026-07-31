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
Ideate SHALL be tested in multi-turn dialogues against student personas (e.g. hesitant, over-scoped, idea-already-solved), judged for Socratic compliance — the skill must never have asked directly for missing input.

#### Scenario: Persona run
- **WHEN** a persona-driven ideation dialogue completes
- **THEN** the transcript is judged for Socratic style and for a correctly seeded proposal file

### Requirement: Inverted-hybrid runners
Authoritative runs (model matrix, release gates, judge models) SHALL execute over metered API providers with native multi-model comparison and spend caps. Subscription-based CLI runs serve as the cheap everyday dev loop and are not the source of record. CI executes only L0 and lint by default; metered eval runs are budget-capped.

Every L1 verdict SHALL be defined once as a pure function in the shared verdict module, taking plain values and returning a pass flag with an explanation, and both runners SHALL reach a scenario's verdict through it rather than reimplementing the assertions. Because the verdicts are pure, each SHALL be exercisable by L0 tests without a model call.

A verdict that asserts a produced file is in the standard format SHALL establish that by running the mechanical check over it and judging the reported errors, never by inspecting the text for characteristic substrings. Errors that follow from information the scenario's input did not carry MAY be tolerated, and the tolerated set SHALL be explicit. Where a defect makes the file unbuildable but is invisible to the mechanical check — which extracts narrowly rather than parsing YAML — the verdict SHALL assert it directly, and SHALL be narrow enough to admit the shapes that do build.

The dev-runner scenario set SHALL cover the import skill. It SHALL therefore support scenarios that stage no proposal file and instead supply a source document in the request, and that assert against a file the skill creates — whose name the skill chooses — rather than one staged in advance.

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

