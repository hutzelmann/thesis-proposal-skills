## MODIFIED Requirements

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

#### Scenario: Verdict logic covered without a model
- **WHEN** an L1 verdict's failure modes are tested
- **THEN** L0 tests call the pure verdict function directly and no model is invoked

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
