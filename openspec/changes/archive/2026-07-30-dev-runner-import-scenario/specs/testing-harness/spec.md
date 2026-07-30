## MODIFIED Requirements

### Requirement: Inverted-hybrid runners

Authoritative runs (model matrix, release gates, judge models) SHALL execute over metered API providers with native multi-model comparison and spend caps. Subscription-based CLI runs serve as the cheap everyday dev loop and are not the source of record. CI executes only L0 and lint by default; metered eval runs are budget-capped.

Every L1 verdict SHALL be defined once as a pure function in the shared verdict module, taking plain values and returning a pass flag with an explanation, and both runners SHALL reach a scenario's verdict through it rather than reimplementing the assertions. Because the verdicts are pure, each SHALL be exercisable by L0 tests without a model call.

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
