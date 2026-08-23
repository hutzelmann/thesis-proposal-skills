## ADDED Requirements

### Requirement: Citation scanning excludes code and honours an escape
The citation scan SHALL ignore `@`-prefixed tokens inside fenced code blocks and inline code spans, and SHALL ignore a token escaped as `\@`. The `citation-undefined` message SHALL name both escapes, so a token the scan read wrongly has a markup remedy.

Marking a token as code is the only remedy the skill offers here: a `@Word` left unmarked in prose remains an undefined citation key, because an unmarked one is indistinguishable from a mistyped key. Rewriting the author's terminology is never the remedy, and the write skill's must-not-fix list carries that half.

#### Scenario: Java annotation written in prose
- **WHEN** the body contains `@Override` in plain prose and no reference declares that id
- **THEN** the check reports it as an undefined citation key and the message names the code-span and `\@` escapes

#### Scenario: Java annotation marked as code
- **WHEN** the same token is written inside an inline code span, inside a fenced code block, or escaped as `\@Override`
- **THEN** the check reports no citation finding for it

### Requirement: Document-shape defects are named, not only their consequences
When a document defect makes the parse fail wholesale, the check SHALL name that defect, not only the findings that follow from it. Two shapes SHALL be named: a metadata block placed at the top of the file instead of the end, and headings underlined in setext style instead of prefixed with `#`.

Both shapes arrive from outside this format — top frontmatter is what every other markdown tool expects, and underlined headings are what a word processor exports — so the student who produces one has done nothing careless, and a report of five missing sections or a reference list that is entirely undefined tells them nothing they can act on.

#### Scenario: Metadata block at the top of the file
- **WHEN** the file opens with a `---` block of metadata keys and does not end with one
- **THEN** the check reports the block's position and states that the remaining reference findings follow from it

#### Scenario: Headings underlined instead of prefixed
- **WHEN** the body carries no `#`-prefixed heading and its section titles are underlined with `===` or `---`
- **THEN** the check reports the heading style as an error naming one of the affected titles, alongside the section findings it causes

## MODIFIED Requirements

### Requirement: Warning-class pattern checks
The skill SHALL report as warnings (never hard failures, false positives acknowledged): first-person pronouns; three consecutive sentences starting with the same word; personal-data patterns (emails, matriculation numbers); an `author` key in the metadata block, since proposals are anonymous by default and the key is rendered verbatim on the title page; confidentiality markers in English and German ("confidential", "internal use only", "do not distribute", "NDA", "vertraulich", "nur für den internen Gebrauch"), because theses get published; author-in-text citations of references that declare neither an author nor an editor, because those render as a quoted title inside the sentence; an author surname of a cited reference typed in the prose immediately before that citation, because the typed name is a copy that stops tracking the reference entry; and a reference id that does not follow the documented key shape or reaches the documented length limit. The metadata `author` warning SHALL name the legitimate exception — a program that requires a named title page — because that exception is declared in workspace guidance prose and is therefore not machine-detectable. The skill SHALL NOT attempt to detect writer names in body prose; the typed-author-name check concerns cited authors only and SHALL be anchored to the surnames of the reference actually cited, never to a general capitalisation pattern.

Every warning in this class SHALL carry the line it fired on, and a warning matched on a pattern rather than a named key SHALL quote the text it matched. Acknowledging false positives is only honest if dismissing one is cheap; without a location, dismissing a warning costs a full read of the document.

The first-person check SHALL NOT read a lone capital `I` following a capitalised word as a pronoun. That shape is a Roman-numeral label — `Type I error` is required vocabulary in the Controlled Experiment subsection contract this project ships.

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

#### Scenario: Statistical vocabulary reads as a pronoun
- **WHEN** the statistical-analysis subsection states that the Type I error rate is controlled
- **THEN** no first-person warning is emitted

#### Scenario: A long number reads as a matriculation number
- **WHEN** the body states a corpus size of seven digits
- **THEN** the warning quotes that number and names its line, so the reader can dismiss it without searching for it

### Requirement: Read-only run enforced without file mutation
A check run SHALL NOT modify the proposal or any other workspace file — no fixes, no permission changes, no temporary alterations, however obvious the correction. A request that asks for the check and the fixes together SHALL be treated as two steps rather than as consent to edit during the check: the check ends at the report, and the fixes belong to the write skill and its rules on which findings must not be "fixed". The mechanical report SHALL include a content digest of the checked file. In a non-interactive run the skill SHALL verify the mandate by re-running the mechanical check as the final step of the check — before any editing step, including one the user has already asked for — and comparing digests; a differing digest SHALL be reported prominently as a violation. The skill SHALL NOT instruct or perform any command that mutates file permissions or content as an enforcement mechanism.

#### Scenario: Digest in the mechanical report
- **WHEN** the mechanical check runs on a proposal
- **THEN** its report contains a digest line identifying the exact file content that was checked

#### Scenario: Non-interactive run leaves the file untouched
- **WHEN** a non-interactive check run finishes and the final re-run reports the same digest as the first
- **THEN** the check reports its findings with the read-only mandate upheld

#### Scenario: File changed during a non-interactive run
- **WHEN** the final re-run reports a different digest than the first
- **THEN** the report states prominently that the file changed during the check, instead of presenting the results as a clean read-only run

#### Scenario: One request asks for the check and the fixes
- **WHEN** the user asks to check a proposal and fix whatever the check reports
- **THEN** the check run reports its findings and leaves the file byte-identical, and any fixing happens as a separate step under the write skill
