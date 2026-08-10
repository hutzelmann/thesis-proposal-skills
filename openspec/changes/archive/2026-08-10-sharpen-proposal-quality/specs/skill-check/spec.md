# skill-check Delta

## ADDED Requirements

### Requirement: Estimated length warning
The deterministic script SHALL estimate the rendered page count from the proposal's body word count using the documented words-per-page constant, judge it against the effective page limit (default or workspace `page_limit` override), and report an overrun as a warning, never an error. The warning SHALL name the estimated pages, the limit, and the fact that the number is an estimate from word count.

#### Scenario: Overlong proposal
- **WHEN** the body word count estimates to seven pages against the default limit of five
- **THEN** the check emits a warning naming the estimate and the limit, and the run does not fail

#### Scenario: Within the limit
- **WHEN** the estimate stays at or below the effective limit
- **THEN** no length warning is emitted

#### Scenario: Workspace override respected
- **WHEN** `guidelines.md` sets `page_limit = 8` and the estimate is six pages
- **THEN** no length warning is emitted

## MODIFIED Requirements

### Requirement: Two-bucket honest reporting
Results SHALL be presented in chat only (no file), split into "verified mechanically" and "flagged for the agent pass". The skill SHALL never claim semantic rules passed. The closing verdict line SHALL scope its claim explicitly: a mechanically clean result SHALL state that substance was not judged and SHALL point to the review skill for the substance verdict, so that "clean" is never readable as a statement about thesis potential.

#### Scenario: Clean mechanical run
- **WHEN** all mechanical checks pass
- **THEN** the report states mechanical success and explicitly defers semantic quality to review

#### Scenario: Verdict line scoped
- **WHEN** the check ends with its one-line verdict on a proposal without findings
- **THEN** the line states that the result is mechanical only, that substance was not judged, and that the review skill renders that verdict
