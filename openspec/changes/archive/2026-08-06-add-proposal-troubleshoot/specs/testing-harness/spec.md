## ADDED Requirements

### Requirement: Support classification exported as data

The support classification the matrix produces SHALL be exportable as machine-readable data alongside the human-readable report, keyed by model and task, so it can be vendored into a skill that must consult it without network access or repository access. The export SHALL distinguish an untested cell from a failing one, because a skill treating "never measured" as "passes" would clear a model it knows nothing about.

#### Scenario: Verdicts exported after a matrix run

- **WHEN** the classification is regenerated from eval logs
- **THEN** a machine-readable export is produced alongside the report, keyed by model and task

#### Scenario: Cell never measured

- **WHEN** a model and task combination has no eval result
- **THEN** the export marks it untested rather than passing

### Requirement: Report offer discipline covered by tests

The uniform failure-path report offer SHALL have negative coverage: the offline suite SHALL fail when a skill's offer wording drifts from the set's, and the model-facing evals SHALL cover that a skill completing normally with findings does not offer a report. A false positive here is more damaging than a miss, because an offer on every ordinary run teaches users to ignore it.

#### Scenario: Skill reports findings on a flawed fixture

- **WHEN** a diagnostic skill runs against a fixture whose oracle expects findings
- **THEN** the eval fails the run if the skill offers a bug report

#### Scenario: Offer wording drifts in one skill

- **WHEN** one skill's offer wording no longer matches the set's
- **THEN** the offline suite fails naming that skill

### Requirement: Externally submitted reproduction seeds

A reproduction seed submitted with a bug report MAY enter the fixture corpus, subject to provenance rules distinct from session-derived fixtures: no committed session log backs it, so it SHALL be verified to contain no real proposal content and no personal data, SHALL be confirmed to still trigger the reported defect before entry, and SHALL receive an `expected.json` oracle encoding the corrected behavior rather than the observed one.

#### Scenario: Submitted seed accepted

- **WHEN** a submitted reproduction seed is verified synthetic and still triggers the defect
- **THEN** it enters the corpus with an oracle encoding the behavior the fix must produce

#### Scenario: Submitted seed no longer reproduces

- **WHEN** a submitted seed does not trigger the defect on the current revision
- **THEN** it is not added, and the report is answered with the revision that already fixed it

#### Scenario: Submitted seed carries real content

- **WHEN** a submitted seed contains recognizable real proposal content or personal data
- **THEN** it is rejected from the corpus regardless of its diagnostic value
