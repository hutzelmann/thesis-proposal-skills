# skill-check Specification

## Purpose
Low-level advisory quality gate: deterministic mechanical checks plus an agent pass, reported honestly in two buckets, results in chat only.
## Requirements
### Requirement: Deterministic mechanical checks
The skill SHALL verify deterministically, driven by the structured guidance data plus workspace overrides: required sections present with canonical titles; canonical sections appearing in the declared order; exactly one methodology from the closed set with its required subsections; forbidden headings absent; the timeline section staying within its size constraint; every declared research question referenced as `(RQn)` in the methodology section; citation-key consistency in both directions (cited-but-undefined is an error, defined-but-uncited a warning); duplicate reference ids; `min_references` satisfied; leftover `[TODO: …]` markers; and file-format guardrails (blank line before the trailing metadata block, exactly one metadata block, no boolean-literal keys).

Order verification and the timeline size constraint SHALL be errors, not warnings, matching the severity of a missing section. The timeline size constraint SHALL NOT be applied when the workspace selects the detailed timeline mode.

#### Scenario: Cited key missing from references
- **WHEN** the body cites `[@Kim24]` and no reference with id `Kim24` exists
- **THEN** the check reports it as a mechanical failure with the location

#### Scenario: RQ never referenced in methodology
- **WHEN** the proposal declares RQ3 and the methodology section never contains `(RQ3)`
- **THEN** the check reports the missing cross-reference

#### Scenario: Timeline section absent
- **WHEN** a proposal carries the four research sections but no timeline section
- **THEN** the check reports a missing required section as an error

#### Scenario: Section order violated
- **WHEN** the timeline section appears before the methodology section
- **THEN** the check reports an ordering error naming the misplaced section

#### Scenario: Timeline body too rich
- **WHEN** the timeline section contains a table, a list item, a subsection, or more than three non-empty lines
- **THEN** the check reports it as an error naming what was found

#### Scenario: Detailed timeline mode selected
- **WHEN** the workspace sets the detailed timeline mode and the timeline section carries a phase table
- **THEN** the check reports no timeline size error

### Requirement: Warning-class pattern checks
The skill SHALL report as warnings (never hard failures, false positives acknowledged): first-person pronouns; three consecutive sentences starting with the same word; personal-data patterns (emails, matriculation numbers); an `author` key in the metadata block, since proposals are anonymous by default and the key is rendered verbatim on the title page; confidentiality markers in English and German ("confidential", "internal use only", "do not distribute", "NDA", "vertraulich", "nur für den internen Gebrauch"), because theses get published; author-in-text citations of references that declare neither an author nor an editor, because those render as a quoted title inside the sentence; an author surname of a cited reference typed in the prose immediately before that citation, because the typed name is a copy that stops tracking the reference entry; and a reference id that does not follow the documented key shape or reaches the documented length limit. The metadata `author` warning SHALL name the legitimate exception — a program that requires a named title page — because that exception is declared in workspace guidance prose and is therefore not machine-detectable. The skill SHALL NOT attempt to detect writer names in body prose; the typed-author-name check concerns cited authors only and SHALL be anchored to the surnames of the reference actually cited, never to a general capitalisation pattern.

#### Scenario: Confidentiality stamp
- **WHEN** the body contains "vertraulich" as a document marker
- **THEN** the check emits a warning citing the publication rationale

#### Scenario: Author-in-text citation of an authorless reference
- **WHEN** the body cites a reference author-in-text and that reference declares no author and no editor
- **THEN** the check emits a warning naming the key and the line, stating that the rendered form is the quoted title, and suggesting the bracketed form instead

#### Scenario: Author-in-text citation of an editor-only reference
- **WHEN** the body cites a reference author-in-text and that reference declares editors but no authors
- **THEN** no warning is emitted, because the rendered label uses the editor surnames

#### Scenario: Bracketed citation of an authorless reference
- **WHEN** the body cites a reference in the bracketed form and that reference declares no author
- **THEN** no warning is emitted, because no author label is rendered

#### Scenario: Metadata block declares an author
- **WHEN** the metadata block declares `author: Erika Musterfrau` or `author: [TODO: add author]`
- **THEN** the check emits a warning to remove it unless the program requires a named cover page, and the run does not fail

#### Scenario: Anonymous proposal
- **WHEN** the metadata block declares no `author` key
- **THEN** no author-key warning is emitted

#### Scenario: Author surname typed before a bracketed citation
- **WHEN** the body reads "Smith et al. [@Smith26Deep] propose a detector" and `Smith` is an author of `Smith26Deep`
- **THEN** the check emits a warning naming the key and the line and suggesting the author-in-text form, which renders the name from the entry

#### Scenario: Author surname typed before an author-in-text citation
- **WHEN** the body reads "Smith et al. @Smith26Deep propose a detector"
- **THEN** the check emits a warning, because the rendered output repeats the name

#### Scenario: Unrelated proper noun before a citation
- **WHEN** a sentence ends in a proper noun that is not an author of the cited reference, as in "deployments in Germany [@Okafor24Carbon]"
- **THEN** no warning is emitted

#### Scenario: Author-in-text form used correctly
- **WHEN** the body cites a reference author-in-text with no name typed in the prose, including the possessor form "the detector of @key"
- **THEN** no warning is emitted

#### Scenario: Surname belongs to a different reference
- **WHEN** a surname appears before a citation of a reference that person did not author
- **THEN** no warning is emitted, because the check is anchored per key

#### Scenario: Reference key carries no year

- **WHEN** a reference id reads `RiveraYearSurvey`, with the literal word "Year" where the year belongs
- **THEN** the check emits a warning naming the key and the expected shape

#### Scenario: Reference key too long

- **WHEN** a reference id reaches the documented length limit
- **THEN** the check emits a warning

#### Scenario: Unusual but well-formed key

- **WHEN** a reference id follows the documented shape, including one built from an institutional or particle-bearing author name
- **THEN** no warning is emitted

### Requirement: Two-bucket honest reporting
Results SHALL be presented in chat only (no file), split into "verified mechanically" and "flagged for the agent pass". The skill SHALL never claim semantic rules passed.

#### Scenario: Clean mechanical run
- **WHEN** all mechanical checks pass
- **THEN** the report states mechanical success and explicitly defers semantic quality to review

### Requirement: Advisory, not blocking
Check gates nothing hard: other skills MAY run it first and surface failures, but SHALL proceed on user confirmation.

#### Scenario: Publish despite warnings
- **WHEN** the user confirms publishing a proposal with check warnings
- **THEN** publishing proceeds

### Requirement: Agent pass for non-mechanical issues
An agent pass SHALL cover typos/grammar and content-level forbidden material that regexes cannot catch (e.g. expected results embedded in prose), and SHALL confirm that the timeline section actually states a timeframe. The timeframe judgement SHALL accept the phrasings students genuinely use — semester labels, quarters, seasons, month names in either language — rather than a fixed set of date formats, and SHALL flag a phase breakdown or Gantt chart that the mechanical guard cannot see, including one supplied as an image.

#### Scenario: Hidden expected-results paragraph
- **WHEN** a methodology paragraph asserts concrete expected outcomes
- **THEN** the agent pass flags it as forbidden content

#### Scenario: Timeline states no timeframe
- **WHEN** the timeline section is present and within its size constraint but names no start, no end, and no as-soon-as-possible statement
- **THEN** the agent pass flags it

#### Scenario: Semester phrasing accepted
- **WHEN** the timeline section reads "The thesis runs from WS 2026/27 to SoSe 2027."
- **THEN** the agent pass accepts it

#### Scenario: Gantt chart embedded as a figure
- **WHEN** the timeline section stays within three lines but embeds a Gantt chart as an image
- **THEN** the agent pass flags it as forbidden work-plan content

### Requirement: Read-only run enforced without file mutation
A check run SHALL NOT modify the proposal or any other workspace file — no fixes, no permission changes, no temporary alterations, however obvious the correction. The mechanical report SHALL include a content digest of the checked file. In a non-interactive run the skill SHALL verify the mandate by re-running the mechanical check as its final step and comparing digests; a differing digest SHALL be reported prominently as a violation. The skill SHALL NOT instruct or perform any command that mutates file permissions or content as an enforcement mechanism.

#### Scenario: Digest in the mechanical report
- **WHEN** the mechanical check runs on a proposal
- **THEN** its report contains a digest line identifying the exact file content that was checked

#### Scenario: Non-interactive run leaves the file untouched
- **WHEN** a non-interactive check run finishes and the final re-run reports the same digest as the first
- **THEN** the check reports its findings with the read-only mandate upheld

#### Scenario: File changed during a non-interactive run
- **WHEN** the final re-run reports a different digest than the first
- **THEN** the report states prominently that the file changed during the check, instead of presenting the results as a clean read-only run

