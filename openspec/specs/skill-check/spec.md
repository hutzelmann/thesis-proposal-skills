# skill-check Specification

## Purpose
Low-level advisory quality gate: deterministic mechanical checks plus an agent pass, reported honestly in two buckets, results in chat only.
## Requirements
### Requirement: Deterministic mechanical checks
The skill SHALL verify deterministically, driven by the structured guidance data plus workspace overrides: required sections present with canonical titles; canonical sections appearing in the declared order; exactly one methodology from the closed set with its required subsections; forbidden headings absent; the timeline section staying within its size constraint; the number of declared research questions staying within the configured bounds; every declared research question referenced as `(RQn)` in the methodology section; citation-key consistency in both directions (cited-but-undefined is an error, defined-but-uncited a warning); duplicate reference ids; `min_references` satisfied; leftover `[TODO: …]` markers; and file-format guardrails (blank line before the trailing metadata block, exactly one metadata block, no boolean-literal keys).

Order verification, the timeline size constraint, and the research-question count bound SHALL be errors, not warnings, matching the severity of a missing section. The timeline size constraint SHALL NOT be applied when the workspace selects the detailed timeline mode.

#### Scenario: Cited key missing from references
- **WHEN** the body cites `[@Kim24]` and no reference with id `Kim24` exists
- **THEN** the check reports it as a mechanical failure with the location

#### Scenario: RQ never referenced in methodology
- **WHEN** the proposal declares RQ3 and the methodology section never contains `(RQ3)`
- **THEN** the check reports the missing cross-reference

#### Scenario: Too many research questions
- **WHEN** the proposal declares more research questions than the configured upper bound
- **THEN** the check reports an error naming the count found and the bound applied

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

### Requirement: Title tells reported as warnings
The deterministic script SHALL inspect the metadata `title:` value and report as warnings, never as errors: an implementation-framing opener in English or German; a term from the closed buzzword list in English or German; a trailing question mark; and a word count outside the documented bounds. Each finding SHALL name the matched tell and state that the title reaches the study certificate. These findings SHALL be warnings because the patterns can fire on a legitimate title and because the script cannot judge whether a named technology is the object of study.

#### Scenario: Implementation opener
- **WHEN** the title opens with an implementation-framing phrase such as an English development opener or its German equivalent
- **THEN** the check emits a warning naming the opener and the certificate rationale, and the run does not fail on that finding

#### Scenario: Buzzword present
- **WHEN** the title carries a term from the documented buzzword list
- **THEN** the check emits a warning naming the term

#### Scenario: Question-form title
- **WHEN** the title ends in a question mark
- **THEN** the check emits a warning naming the certificate rationale

#### Scenario: Word count out of bounds
- **WHEN** the title falls below the documented minimum for the proposal's language or above the documented maximum word count
- **THEN** the check emits a warning naming the count, the bound it crossed, and the certificate rationale

#### Scenario: German title at the German minimum
- **WHEN** a `lang: de` proposal carries a compound title shorter than the English minimum but at or above the German one
- **THEN** no word-count warning is emitted

#### Scenario: Title written as a block scalar
- **WHEN** the metadata `title:` carries a YAML folded or literal block indicator and its text continues on the following lines
- **THEN** no title tell is applied, because the value the check can read is not the title

#### Scenario: Clean academic title
- **WHEN** the title names a contribution and its object within the bounds and matches no tell
- **THEN** no title warning is emitted

#### Scenario: Title findings never fail the run
- **WHEN** the only findings are title tells
- **THEN** the run reports them under warnings and exits successfully

### Requirement: Agent pass judges title quality
The agent pass SHALL judge the title against the guidance classes the patterns cannot reach — above all whether a proper noun in the title names a tool, product, vendor, or company carried as the instrument, and whether the title names a research field rather than a thesis. Where it flags the title, the skill SHALL offer between one and three abstracted alternatives and SHALL state that a named technology is acceptable only where the student can say it is the object of study. The skill SHALL report title judgement under the agent-pass bucket, never as mechanically verified.

#### Scenario: Tool name carried as instrument
- **WHEN** the title names a framework or product used to build the artefact and no pattern matched it
- **THEN** the agent pass flags it with abstracted alternatives, under the flagged-for-the-agent-pass bucket

#### Scenario: Named technology as object of study
- **WHEN** the proposal's research questions are about the named technology itself
- **THEN** the agent pass says so and does not flag the title

### Requirement: Estimated length warning
The deterministic script SHALL estimate the rendered page count from the proposal's body word count using the documented words-per-page constant, judge it against the effective page limit (default or workspace `page_limit` override), and report an overrun as a warning, never an error. The warning SHALL name the estimated pages, the limit, and the fact that the number is an estimate from word count. An override value that is not a positive number SHALL be reported as a mechanical error and SHALL degrade to the default limit, never crash the run or silently disable the rule.

#### Scenario: Overlong proposal
- **WHEN** the body word count estimates to seven pages against the default limit of five
- **THEN** the check emits a warning naming the estimate and the limit, and the run does not fail

#### Scenario: Within the limit
- **WHEN** the estimate stays at or below the effective limit
- **THEN** no length warning is emitted

#### Scenario: Workspace override respected
- **WHEN** `guidelines.md` sets `page_limit = 8` and the estimate is six pages
- **THEN** no length warning is emitted

#### Scenario: Invalid override degrades to the default
- **WHEN** `guidelines.md` sets `page_limit = "5"` or a non-positive value
- **THEN** the check reports a mechanical error naming the invalid value, judges the estimate against the default limit, and the report still completes

### Requirement: Two-bucket honest reporting
Results SHALL be presented in chat only (no file), split into "verified mechanically" and "flagged for the agent pass". The skill SHALL never claim semantic rules passed. The closing verdict line SHALL scope its claim explicitly: a mechanically clean result SHALL state that substance was not judged and SHALL point to the review skill for the substance verdict, so that "clean" is never readable as a statement about thesis potential.

#### Scenario: Clean mechanical run
- **WHEN** all mechanical checks pass
- **THEN** the report states mechanical success and explicitly defers semantic quality to review

#### Scenario: Verdict line scoped
- **WHEN** the check ends with its one-line verdict on a proposal without findings
- **THEN** the line states that the result is mechanical only, that substance was not judged, and that the review skill renders that verdict

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

### Requirement: Findings carry stable identifiers

Every mechanical finding the deterministic script reports SHALL carry a stable identifier
naming the rule that produced it, in addition to its severity and its human-readable
message. Identifiers SHALL be drawn from a closed set defined by the script and SHALL remain
stable when a message is reworded, so that a consumer distinguishes "this check fired" from
"this check phrased its finding this way".

The human-readable message SHALL remain the primary output for a student, and its wording
SHALL stay free to change without notice. Consumers that need to identify a finding SHALL
use the identifier and SHALL NOT match against message text.

#### Scenario: A reworded message keeps its identifier

- **WHEN** a finding's human-readable message is rephrased without changing what it detects
- **THEN** the finding SHALL continue to report the same identifier
- **AND** a consumer keyed on that identifier SHALL be unaffected

#### Scenario: Distinct rules are distinguishable

- **WHEN** two different checks report findings whose messages share a common phrase
- **THEN** each finding SHALL carry the identifier of the rule that produced it
- **AND** a consumer SHALL be able to tell the two findings apart

### Requirement: Machine-readable output mode

The deterministic script SHALL offer an output mode that emits its findings as structured
data rather than as the human report. The structured output SHALL carry, for each finding,
its severity, its rule identifier, and its message; and SHALL carry the content digest of
the checked file and the exit code the run produced.

The structured mode SHALL be opt-in. Invoked without it, the script SHALL emit the human
report exactly as before, and the exit code SHALL be identical in both modes: non-zero only
when at least one error-level finding was reported.

#### Scenario: Structured output requested

- **WHEN** the script is invoked in its machine-readable output mode over a proposal
- **THEN** it SHALL emit the findings as structured data with severity, identifier, and
  message for each
- **AND** it SHALL include the checked file's content digest
- **AND** it SHALL NOT emit the human two-bucket report

#### Scenario: Default invocation is unchanged

- **WHEN** the script is invoked without requesting structured output
- **THEN** it SHALL emit the human two-bucket report as it did before
- **AND** the exit code SHALL match the one the structured mode reports for the same file

#### Scenario: Advisory status is preserved

- **WHEN** a run reports warning-level findings but no error-level findings
- **THEN** the exit code SHALL indicate success in both output modes,
  because the check gates nothing on warnings

### Requirement: Retired override keys are reported, never ignored
The check SHALL report a workspace override key from the pre-migration vocabulary as a configuration error naming the key path that replaces it. A retired key SHALL NOT be honoured, and SHALL NOT be passed over in silence — a workspace whose overrides stopped applying without saying so is worse than one that fails.

The check SHALL apply the same treatment to any override key that is not part of the overridable set, because a typo in an override key is indistinguishable from a retired one from the user's side, and both mean the workspace is not getting what it asked for.

#### Scenario: Workspace uses a retired key
- **WHEN** a workspace `guidelines.md` sets the old flat reference-minimum key
- **THEN** the check reports an error naming the nested key path that replaces it, and the default minimum applies

#### Scenario: Workspace uses an unknown key
- **WHEN** a workspace `guidelines.md` sets a key that is not overridable
- **THEN** the check reports an error naming the unknown key

### Requirement: Workspace methodology declarations are validated and merged
The check SHALL merge a workspace methodology declaration over the shipped set before applying any methodology rule, so the accepted set, the required subsections, and the message listing acceptable methodologies all reflect the workspace.

The check SHALL report as a configuration error a declared branch that is missing a title in either language, that declares no subsections, that declares a subsection missing a title in either language, that declares a subsection without guidance, or that carries a key the declaration format does not define. An invalid branch SHALL NOT be applied, and the rest of the file SHALL still be checked — one malformed branch does not invalidate a workspace.

#### Scenario: Proposal uses a workspace branch
- **WHEN** a proposal declares a methodology the workspace added, with that branch's subsections present
- **THEN** the check reports no methodology finding

#### Scenario: Proposal misses a workspace branch's subsection
- **WHEN** a proposal declares a workspace branch and omits one of its declared subsections
- **THEN** the check reports the missing subsection by its declared title

#### Scenario: Unknown methodology lists the workspace set
- **WHEN** a proposal declares a methodology no branch matches
- **THEN** the error lists the accepted methodologies including workspace-declared ones and excluding disabled ones

#### Scenario: Malformed branch declaration
- **WHEN** a workspace declares a branch without per-subsection guidance
- **THEN** the check reports a configuration error naming that branch, and every other rule still runs

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

### Requirement: Hindsight leakage reported as a warning
The skill SHALL report as warnings (never hard failures, false positives acknowledged) prose that states the proposal's own work as already done: result verbs in the first person or with the work as subject — showed, found, demonstrated, outperformed, and their German equivalents — and quantitative outcomes stated as findings. A proposal describes work that has not happened, so such a sentence is either a draft written after the work began or a proposal derived from a finished thesis.

The check SHALL fire only on sentences carrying no citation. Reporting what prior work established is what the Contribution section is for, and a rule that cannot tell "@Rivera23 showed that scheduling reduces water use" from "we showed that scheduling reduces water use" would fire on every correctly written proposal. Each warning SHALL carry its line and quote the text it matched.

The skill SHALL NOT attempt to judge whether a research question is a settled claim in disguise. That reading requires knowing what the work found, which the document does not state; it belongs to the review skill's agent pass and to the reader.

#### Scenario: Result claim without a citation
- **WHEN** the body states that the work demonstrated an effect, in a sentence carrying no citation
- **THEN** the check emits a warning citing the line and quoting the matched text

#### Scenario: Result attributed to prior work
- **WHEN** the same claim is attributed to a cited reference
- **THEN** no warning is emitted

#### Scenario: Quantitative outcome stated as a finding
- **WHEN** the body reports a measured improvement as an achieved number, in a sentence carrying no citation
- **THEN** the check emits a warning

#### Scenario: Planned measurement
- **WHEN** the body states what will be measured and against which baseline
- **THEN** no warning is emitted, because the sentence describes a plan rather than an outcome

#### Scenario: Research question that reads like a conclusion
- **WHEN** a research question is phrased so that it presupposes its own answer
- **THEN** the mechanical check stays silent and the judgment is left to the review skill

