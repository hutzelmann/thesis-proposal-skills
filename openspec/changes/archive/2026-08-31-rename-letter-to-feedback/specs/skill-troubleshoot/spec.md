# skill-troubleshoot delta

## MODIFIED Requirements

### Requirement: Companion artifacts inventoried at hash level

When a proposal file is named, the report SHALL inventory the companion artifacts beside it — the review file, the supervise feedback file, and any workspace build definition — recording presence, byte size, and content hash, with the slug-bearing names replaced by the proposal placeholder. The content of these artifacts SHALL NOT enter the report at any disclosure level: the feedback derives from a student's unpublished submission, the build definition is the user's own code and may name institutional paths, and the graded-redaction levels govern the proposal only.

A workspace build definition SHALL be recorded under its own name rather than the placeholder, because that name comes from the fixed set the publish skill recognizes and therefore carries nothing about the user. Recording it is what keeps a report from a workspace-built document from reading as a report about the shipped pipeline.

#### Scenario: Supervise workspace reported
- **WHEN** a report is assembled for a proposal that has a supervise feedback file beside it
- **THEN** the report records the feedback file with size and hash under a placeholder name, and none of its text

#### Scenario: Student workspace unchanged
- **WHEN** no review file, feedback file, or build definition exists beside the proposal
- **THEN** the report carries no companion-artifact lines

#### Scenario: Full disclosure still excludes companions
- **WHEN** the user chooses the most disclosing level
- **THEN** the proposal text enters the report under the personal-data rules while the feedback file, the review file and the build definition remain hash-only

#### Scenario: Workspace build definition present
- **WHEN** a report is assembled for a proposal with a workspace build definition beside it
- **THEN** the report records that definition by name with its size and hash, so a maintainer can see the document was not built by the shipped pipeline
