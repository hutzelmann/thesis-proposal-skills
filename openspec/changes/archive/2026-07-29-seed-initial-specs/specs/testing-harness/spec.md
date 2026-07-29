# Delta: testing-harness

## Purpose

Automated verification that all skills work as specified across models: a three-layer test pyramid with deterministic fixtures and model-graded rubrics.

## ADDED Requirements

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

#### Scenario: Release gate
- **WHEN** a release-gating eval is run
- **THEN** it executes on the metered authoritative path with per-model logs, not on the subscription dev runner

### Requirement: Fixture corpus with oracles
Fixtures SHALL follow the fixture blueprint: synthetic proposals covering both languages, both levels, all quality tiers, every mechanical check rule (tripped at least once and passed at least once), every methodology branch, clean controls, and workflow states — each with an `expected.json` ground-truth oracle consumed by L1/L2. Fixtures MUST NOT contain content from real proposals; personal data in fixtures is obviously fake.

#### Scenario: New check rule added
- **WHEN** a new mechanical rule enters the check skill
- **THEN** at least one fixture trips it and one passes it, encoded in their oracles
