# testing-harness delta

## RENAMED Requirements

- FROM: `### Requirement: Supervise letter coverage`
- TO: `### Requirement: Supervise feedback coverage`

## MODIFIED Requirements

### Requirement: Supervise feedback coverage

The harness SHALL carry an L1 task that runs the supervise skill against a synthetic raw submission fixture and asserts the feedback contract with dedicated verdict functions: the feedback exists as the slug-named feedback file, it carries at most five curated points, it opens with one of the student-facing verdict tiers — including the idea-stage rendering in English and German — the feedback contains no personal data from the fixture, and every skill pointer in the feedback names a skill that exists in the set. The synthetic fixtures SHALL include at least one non-standard-format submission (pasted-text fragment or PDF-shaped input) so normalization is exercised, not bypassed. Non-interactive runs (the Inspect task and the dev runner) SHALL pre-answer the borderline deferral in the request so a single-turn run cannot stall waiting for the professor.

#### Scenario: Feedback contract asserted
- **WHEN** the supervise L1 task runs against a messy synthetic submission
- **THEN** the scorers report feedback presence, point count, verdict tier, personal-data absence, and skill-pointer validity as separate verdicts

#### Scenario: Personal data leak caught
- **WHEN** a run leaves the fixture's fake student name or matriculation number anywhere in the feedback
- **THEN** the personal-data verdict fails and names the leaking file

#### Scenario: Offline verdict coverage
- **WHEN** the L0 suite runs
- **THEN** every supervise verdict function is exercised by unit tests without model calls

#### Scenario: Idea-stage feedback recognized
- **WHEN** the feedback opens with the idea-stage rendering instead of the blunt review vocabulary
- **THEN** the tier verdict passes in both English and German

#### Scenario: Headless run does not stall
- **WHEN** the L1 task or dev runner drives a borderline submission single-turn
- **THEN** the request's pre-answer resolves the deferral and the run completes
