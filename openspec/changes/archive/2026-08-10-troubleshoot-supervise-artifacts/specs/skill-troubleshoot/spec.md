# skill-troubleshoot Delta

## ADDED Requirements

### Requirement: Companion artifacts inventoried at hash level

When a proposal file is named, the report SHALL inventory the companion artifacts beside it — the review file and the supervise send-package — recording presence, file count, byte size, and content hash, with the slug-bearing names replaced by the proposal placeholder. The content of these artifacts SHALL NOT enter the report at any disclosure level: the letter derives from a student's unpublished submission, and the graded-redaction levels govern the proposal only.

#### Scenario: Supervise workspace reported
- **WHEN** a report is assembled for a proposal that has a send-package directory beside it
- **THEN** the report records the package's files with sizes and hashes under placeholder names, and none of their text

#### Scenario: Student workspace unchanged
- **WHEN** no review file or package directory exists beside the proposal
- **THEN** the report carries no companion-artifact lines

#### Scenario: Full disclosure still excludes companions
- **WHEN** the user chooses the most disclosing level
- **THEN** the proposal text enters the report under the personal-data rules while the letter and review file remain hash-only
