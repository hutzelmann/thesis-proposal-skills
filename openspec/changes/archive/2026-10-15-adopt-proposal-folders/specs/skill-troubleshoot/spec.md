# Spec Delta

## ADDED Requirements

### Requirement: Proposal handle redacted in every path
At every disclosure level below the most disclosing one, the report and the script outputs it stores SHALL carry the proposal's slug nowhere: every occurrence, the proposal folder's name in a path included, SHALL be replaced by the proposal placeholder. Role names inside the folder carry nothing about the user and SHALL be kept as they are. The report directory SHALL stay at the workspace root.

#### Scenario: Check output relayed with folder paths
- **WHEN** the stored check output names `energy-attack-detection/energy-attack-detection.md` and `energy-attack-detection/review.md`
- **THEN** the report carries `<proposal>/<proposal>.md` and `<proposal>/review.md`, and no word of the slug

#### Scenario: Report directory placement
- **WHEN** a report is assembled for a proposal in its folder, with the workspace root as working directory
- **THEN** the report directory is created at the workspace root, not in the proposal's folder

## MODIFIED Requirements

### Requirement: Graded redaction with the most protective default

The user SHALL choose how much of their proposal the report carries, from a graded set whose least-disclosing level carries no proposal prose at all — only structural counts, hashes, script output and environment facts. Intermediate levels add structure without body text; the most disclosing level adds proposal text with the personal-data rules already governing proposals applied to it.

The leading `# ` title heading is proposal text: levels below the most disclosing one SHALL mask it, and the canonical-heading tally SHALL exclude it.

Of the notes file the report SHALL store only the Log section, with the proposal's handle replaced by the placeholder below the most disclosing level; a notes file without a Log section contributes nothing.

The default SHALL be the least-disclosing level. Before writing anything, the skill SHALL state what the chosen level includes and what the next level up would add, so the choice is informed rather than inferred. The proposal is an unpublished research idea, so silence about disclosure is not an acceptable default.

#### Scenario: User does not state a level

- **WHEN** a report is assembled without the user naming a disclosure level
- **THEN** the least-disclosing level is used

#### Scenario: Disclosure stated before writing

- **WHEN** the skill is about to write a report
- **THEN** it first states what the chosen level includes and what the next level would add

#### Scenario: Most disclosing level chosen

- **WHEN** the user chooses the level that carries proposal text
- **THEN** the personal-data rules that govern proposals are applied to that text before it enters the report

#### Scenario: Structure level does not disclose the title

- **WHEN** a report is assembled at a level that lists headings
- **THEN** the leading `# ` title heading appears masked, never verbatim, and the canonical-heading tally does not count it

#### Scenario: Notes log stored without the handle

- **WHEN** a report is assembled below the most disclosing level and a line of the notes file's Log section names `energy-attack-detection/energy-attack-detection.md`
- **THEN** the stored Log excerpt carries `<proposal>/<proposal>.md` and no word of the slug, the name's form with undecodable bytes replaced included, and nothing of the notes file outside its Log section

#### Scenario: Notes file without a Log section

- **WHEN** the proposal's notes file has no Log section
- **THEN** nothing of it is stored at any level, and the report records that the notes file has no Log section

### Requirement: Companion artifacts inventoried at hash level

When a proposal file is named, the report SHALL inventory the companion artifacts in its folder — the review file, the supervise feedback file, and any workspace build definition — recording presence, byte size, and content hash under their role names, which carry nothing about the user. The content of these artifacts SHALL NOT enter the report at any disclosure level: the feedback derives from a student's unpublished submission, the build definition is the user's own code and may name institutional paths, and the graded-redaction levels govern the proposal only.

A workspace build definition SHALL be recorded under its own name rather than the placeholder, because that name comes from the fixed set the publish skill recognizes and therefore carries nothing about the user. Recording it is what keeps a report from a workspace-built document from reading as a report about the shipped pipeline.

#### Scenario: Supervise workspace reported
- **WHEN** a report is assembled for a proposal that has a supervise feedback file in its folder
- **THEN** the report records `feedback.md` with size and hash, and none of its text

#### Scenario: Student workspace unchanged
- **WHEN** no review file, feedback file, or build definition exists in the proposal's folder
- **THEN** the report carries no companion-artifact lines

#### Scenario: Full disclosure still excludes companions
- **WHEN** the user chooses the most disclosing level
- **THEN** the proposal text enters the report under the personal-data rules while the feedback file, the review file and the build definition remain hash-only

#### Scenario: Workspace build definition present
- **WHEN** a report is assembled for a proposal with a workspace build definition in its folder
- **THEN** the report records that definition by name with its size and hash, so a maintainer can see the document was not built by the shipped pipeline
