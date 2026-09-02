# skill-troubleshoot Specification

## Purpose
Diagnoses problems a user hits while working with the proposal skills, resolves the causes that are not defects, and for the ones that are, assembles a bug report the user reviews and delivers themselves.
## Requirements
### Requirement: Triage precedes collection

The skill SHALL work through a fixed diagnostic ladder before it assembles or writes anything. The ladder SHALL be ordered cheapest-resolution-first: a stale install, then an unsupported model, then a workspace guidelines override, then a failing script, then a violated skill mandate, then dissatisfaction with correct output. The skill SHALL name which rung the problem landed on and SHALL state whether that rung is a defect.

A report SHALL NOT be assembled for a rung the skill resolved. Assembling one anyway is the failure mode this requirement exists to prevent: a maintainer's queue full of unsupported-model reports hides the real defects.

#### Scenario: Cause found on a resolvable rung

- **WHEN** the ladder identifies a cause the user can fix themselves
- **THEN** the skill names the rung, states the fix, and ends without assembling a report

#### Scenario: Cause is a defect

- **WHEN** the ladder reaches a failing script or a violated skill mandate
- **THEN** the skill names the rung as a defect and offers to assemble a report

#### Scenario: Ladder is inconclusive

- **WHEN** no rung explains the problem
- **THEN** the skill says so plainly and offers to assemble a report with the cause recorded as unidentified, rather than choosing a plausible rung

### Requirement: Stale install answered before anything else

The first rung SHALL be the possibility that the user's installed skills predate the fix for the problem they are reporting. The skill SHALL direct the user to update their installation and retry before any further diagnosis. It SHALL NOT attempt to establish whether the install is current by comparing version identifiers, because the installed copy carries none.

#### Scenario: Problem reported on an unknown revision

- **WHEN** a user reports a problem and the currency of their install is unknown
- **THEN** the skill's first instruction is to update the installed skills and retry

#### Scenario: Problem survives an update

- **WHEN** the user confirms they updated and the problem persists
- **THEN** the skill proceeds to the next rung and records in any resulting report that the install was updated first

### Requirement: Non-defect causes named as such

Four causes SHALL be reported as correct behavior rather than as defects: a model known to fail the task in question, a workspace `guidelines.md` override producing the behavior the user objects to, dissatisfaction with output that broke no stated rule, and a run that cost many times the usual while producing correct output because the host's effort or workflow mode fanned the task out into many agents — against the execution shape the skill states, where it states one. For each, the skill SHALL name the mechanism responsible and the user's available remedy — switch models, amend the overrides, use the review or customize skill, or use the host's own budget and effort controls.

An unsupported model SHALL remain reportable at the user's option, because a fresh failure on a known-weak model is evidence about that model rather than noise.

#### Scenario: Known-weak model on a task it fails

- **WHEN** the failing task is one the shipped support data records the running model as failing
- **THEN** the skill states that the model, not the skill, is the cause, names a remedy, and offers the report as optional model evidence

#### Scenario: Supervisor override is responsible

- **WHEN** a workspace `guidelines.md` override produces the behavior the user objects to
- **THEN** the skill names the override and states that it is winning as designed

#### Scenario: Output broke no rule

- **WHEN** the user's objection is to output quality and no stated rule was broken
- **THEN** the skill routes them to the review or customize skill and assembles no report

#### Scenario: Cost blowup under a fan-out host mode

- **WHEN** the user reports that a run cost many times the usual and its output was otherwise correct
- **THEN** the skill lands on the dissatisfaction rung, names the host's effort or workflow mode and its budget and effort controls as the mechanism and remedy, and assembles no report

### Requirement: Support verdicts shipped as skill data

The model-support verdicts the ladder consults SHALL ship inside the skill as committed machine-readable data. The skill SHALL NOT depend on network access or on the development repository to reach them, because it runs in a user's workspace which contains neither. When the shipped data has no entry for the running model or the task, the skill SHALL say the rung is unevaluated rather than treat absence as a pass.

#### Scenario: Verdicts consulted offline

- **WHEN** the ladder reaches the model rung with no network available
- **THEN** the verdicts are read from the skill's shipped data

#### Scenario: Model absent from the shipped data

- **WHEN** the running model has no entry in the shipped verdicts
- **THEN** the skill reports the rung as unevaluated for that model and continues down the ladder

### Requirement: Report stays local and is delivered by the user

An assembled report SHALL be written only into the user's own workspace, as files the user can read. The skill SHALL NOT transmit it, open an issue, post to any service, or offer to. Delivery — a public issue, an email, a hand-off to a supervisor — SHALL remain the user's decision and the user's action. When naming the issue option, the skill SHALL present a prefilled form URL for the repository's skill-defect issue template, constructed from the report's own short fields (which skill, the triage rung, what happened, the self-reported agent identity), URL-encoded as query parameters; fields too long for a URL SHALL be named as paste-in steps instead. The URL SHALL carry nothing beyond what the chosen disclosure level already placed into the report.

#### Scenario: Report finished

- **WHEN** the skill finishes assembling a report
- **THEN** the report exists as local files and the skill names the delivery options without performing any of them

#### Scenario: User asks the skill to submit it

- **WHEN** the user asks the skill to file the report for them
- **THEN** the skill states that it does not transmit reports and tells them where the files are

#### Scenario: Issue option carries a prefilled URL

- **WHEN** the report's self-reported fields are filled and the skill names the issue option
- **THEN** the option is a URL to the skill-defect issue form with the short fields prefilled from the report, the long fields named for pasting, and the user left to open, review, and submit it themselves

### Requirement: Graded redaction with the most protective default

The user SHALL choose how much of their proposal the report carries, from a graded set whose least-disclosing level carries no proposal prose at all — only structural counts, hashes, script output and environment facts. Intermediate levels add structure without body text; the most disclosing level adds proposal text with the personal-data rules already governing proposals applied to it.

The thesis title is proposal text, not structure, even though the format carries it as the leading `# ` heading: levels below the most disclosing one SHALL mask the title heading rather than print it, and structural counts that classify headings as canonical or custom SHALL exclude the title heading rather than report it as a permanently non-canonical entry.

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

### Requirement: Measured facts distinguished from self-reported ones

Every fact in the report SHALL be marked as either measured or self-reported. Facts a script established — interpreter and tool versions, operating system, file hashes, script exit codes and digests — are measured. Facts the agent supplies about itself or about what happened — its model identity, its harness, its account of the failing exchange — are self-reported.

The distinction SHALL be visible in the report itself. The agent assembling the report is the subject of the report, so a maintainer must be able to see which half of it is testimony without inferring it.

#### Scenario: Environment recorded

- **WHEN** interpreter and tool versions are collected by a script
- **THEN** they appear marked as measured

#### Scenario: Agent describes what it did

- **WHEN** the agent contributes its account of the failing exchange or its own model identity
- **THEN** that content appears marked as self-reported

### Requirement: Install identified from workspace evidence

The report SHALL carry enough to identify which revision of the skills produced the problem, drawn only from what the workspace already holds: the installer's own lock record where one exists, and a content hash of every installed skill file. Hashes SHALL cover shipped scripts and reference data, not only instruction files, because a changed script is as capable of causing the problem as changed instructions.

The repository SHALL provide a maintainer-side means of resolving a submitted hash set to the revision that produced it, and of naming any file that matches no known revision as locally modified. Identification SHALL NOT depend on data shipped inside the skills, because installs predating any such addition are exactly the ones most likely to be reported.

#### Scenario: Lock record present

- **WHEN** the workspace holds the installer's lock record
- **THEN** the report carries it unaltered alongside the recomputed hashes

#### Scenario: Lock record absent

- **WHEN** no lock record exists, as with a hand-copied install
- **THEN** the report still carries the per-file hashes and records that the install method is unknown

#### Scenario: Submitted hashes resolved by a maintainer

- **WHEN** a maintainer resolves a submitted hash set against the repository's history
- **THEN** the matching revision is named, and any file matching no revision is reported as locally modified

### Requirement: Reproduction seed only where reduction is possible

Where the defect is mechanically reproducible, the report SHALL carry a minimal reproduction: an input reduced until it stops triggering the defect and then restored by one step, plus the exact command. Reduction output SHALL be synthetic and SHALL obey the fixture rules already governing this repository's test corpus, so a submitted seed can enter it.

Where the defect is a matter of judgement rather than mechanism, the report SHALL carry prose only. A fabricated reproduction for a judgement defect is worse than none, because it invites a maintainer to chase a mechanism that does not exist.

#### Scenario: Deterministic defect

- **WHEN** the defect reproduces on demand from a file and a command
- **THEN** the report carries a reduced synthetic input and the command that triggers it

#### Scenario: Judgement defect

- **WHEN** the defect is that the agent produced unsound or invented content
- **THEN** the report carries the account and the artifacts, and no reproduction seed

#### Scenario: Reduction fails to isolate

- **WHEN** reduction cannot produce an input that still triggers the defect
- **THEN** the report records that reduction was attempted and did not isolate it

### Requirement: Collection confined to the report directory

Assembling a report SHALL create and write files only inside the report directory it creates in the user's workspace. It SHALL NOT modify the proposal, the companion notes file, the workspace guidelines, or any installed skill file. The skills that diagnose read-only SHALL therefore remain able to offer a report without breaching their own mandate.

#### Scenario: Report assembled during a read-only diagnosis

- **WHEN** a read-only skill's run ends in an offer that the user accepts
- **THEN** the files the read-only skill was examining are unchanged and only the report directory is new

#### Scenario: Report directory already exists

- **WHEN** a report directory from an earlier run is present
- **THEN** the skill asks before overwriting it rather than replacing its contents silently

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

