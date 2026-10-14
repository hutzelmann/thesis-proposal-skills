# skill-check Specification

## Purpose
Low-level advisory quality gate: deterministic mechanical checks plus an agent pass, reported honestly in two buckets, results in chat only.

## Requirements

### Requirement: Deterministic mechanical checks
The skill SHALL verify deterministically, driven by the structured guidance data plus workspace overrides: required sections present with canonical titles; canonical sections appearing in the declared order; exactly one methodology from the closed set with its required subsections; forbidden headings absent; the timeline section staying within its size constraint; the number of declared research questions staying within the configured bounds; every declared research question referenced as `(RQn)` in the methodology section; citation-key consistency in both directions (cited-but-undefined is an error, defined-but-uncited a warning); duplicate reference ids; `min_references` satisfied; leftover `[TODO: …]` markers; and file-format guardrails (the leading `# <title>` line as the file's first content line and only H1; the emphasized subtitle paragraph beneath it; the closing references section present, last, and empty; blank line before the trailing metadata block, exactly one metadata block, no boolean-literal keys; retired metadata keys — `title`, `subtitle`, `lang`, `author` — flagged when present). The title heading SHALL be excluded from required-section, ordering, forbidden-pattern, and methodology matching. The proposal's language SHALL be inferred per the file-format contract; when it is undeterminable the check SHALL report that as a finding and emit its own messages in English.

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

#### Scenario: Second H1 in the body
- **WHEN** the body carries a second H1 heading below the title line
- **THEN** the check reports it as an error naming the leading-H1 rule

#### Scenario: Title heading resembles a methodology heading
- **WHEN** the title line begins with the methodology heading prefix
- **THEN** no methodology-multiple finding is produced, because the title heading is excluded from methodology matching

#### Scenario: Subtitle paragraph missing or unemphasized
- **WHEN** the block after the title line is absent, is not a paragraph, or is not wrapped entirely in `*…*` emphasis
- **THEN** the check reports the subtitle finding naming the expected shape

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
The deterministic script SHALL inspect the title carried by the leading `# ` line and report as warnings, never as errors: an implementation-framing opener in English or German; a term from the closed buzzword list in English or German; a trailing question mark; and a word count outside the documented bounds. Each finding SHALL name the matched tell and state that the title reaches the study certificate. These findings SHALL be warnings because the patterns can fire on a legitimate title and because the script cannot judge whether a named technology is the object of study.

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
- **WHEN** a German proposal carries a compound title shorter than the English minimum but at or above the German one
- **THEN** no word-count warning is emitted

#### Scenario: Title line absent
- **WHEN** the file carries no leading `# ` title line
- **THEN** the check reports the missing title as its own finding and applies no title tells, because there is no title to inspect

#### Scenario: Title written as a block scalar
- **WHEN** the metadata block still carries a retired `title:` key whose value is a YAML folded or literal block indicator
- **THEN** no title tell is applied to that value — the title is read from the leading `# ` line, and the key only produces the retired-key finding

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

### Requirement: Reference-density advisory warning
The deterministic script SHALL judge the number of defined references against a length-scaled expectation: the body word count (the same count the length estimate uses) times the effective reference-density constant (default or workspace `[references] min_per_1000_words` override) per thousand words, rounded up. A proposal defining fewer references than the expectation SHALL receive a warning, never an error. The warning SHALL name the reference count, the word count, the effective density, and the resulting expectation, so the student sees why the number moved with the document's length.

The warning SHALL be suppressed while the reference-floor error fires, so one defect never produces two findings. A density of zero SHALL disable the advisory. An override value that is not a non-negative finite number SHALL be reported as a mechanical error and SHALL degrade to the default density, never crash the run or silently disable the rule. The effective density SHALL be capped at one reference per word (1000 per 1000 words), so an extreme but valid override cannot overflow the computation. Structured guidance data that predates the constant SHALL disable the advisory rather than fail the run.

#### Scenario: Full-length proposal with a thin bibliography
- **WHEN** a proposal's body is 2500 words and it defines 6 references at the default density of 4 per 1000 words
- **THEN** the check emits a warning naming 6 references against an expectation of 10, and the run does not fail

#### Scenario: Short draft is not nagged
- **WHEN** a proposal's body is short enough that the expectation is at or below the reference floor
- **THEN** no density warning is emitted

#### Scenario: Floor error suppresses the advisory
- **WHEN** a proposal defines fewer references than the floor
- **THEN** the floor error is the only reference-count finding

#### Scenario: Workspace override respected
- **WHEN** `guidelines.md` sets `[references] min_per_1000_words = 8` and the proposal's density sits between 4 and 8 per 1000 words
- **THEN** the density warning fires against the workspace value

#### Scenario: Zero disables the advisory
- **WHEN** `guidelines.md` sets `[references] min_per_1000_words = 0`
- **THEN** no density warning is emitted regardless of length

#### Scenario: Invalid override degrades to the default density
- **WHEN** `guidelines.md` sets `[references] min_per_1000_words = "4"`, a negative value, or a non-finite value such as `inf`
- **THEN** the check reports a mechanical error naming the invalid value, judges the proposal against the default density, and the report still completes

#### Scenario: Extreme but valid override cannot crash the run
- **WHEN** `guidelines.md` sets the density to a finite but absurd value (a huge float or an arbitrary-precision TOML integer)
- **THEN** the run completes, with the effective density capped at one reference per word

#### Scenario: Older structured data disables the advisory
- **WHEN** the structured guidance data carries no reference-density constant and no workspace override sets one
- **THEN** no density finding is emitted and the run completes normally

### Requirement: Two-bucket honest reporting
Results SHALL be presented in chat only (no file), split into "verified mechanically" and "flagged for the agent pass". The skill SHALL never claim semantic rules passed. The closing verdict line SHALL scope its claim explicitly: a mechanically clean result SHALL state that substance was not judged, so that "clean" is never readable as a statement about thesis potential, and the stage handoff that follows SHALL name the review as the step that renders the substance verdict whenever no current review covers the text.

#### Scenario: Clean mechanical run
- **WHEN** all mechanical checks pass
- **THEN** the report states mechanical success and explicitly defers semantic quality to review

#### Scenario: Verdict line scoped
- **WHEN** the check ends with its one-line verdict on a proposal without findings and no current review
- **THEN** the line states that the result is mechanical only and that substance was not judged, and the handoff's `Next:` line recommends a review of the draft without naming a skill

### Requirement: Advisory, not blocking
Check gates nothing hard: other skills MAY run it first and surface failures, but SHALL proceed on user confirmation.

#### Scenario: Publish despite warnings
- **WHEN** the user confirms publishing a proposal with check warnings
- **THEN** publishing proceeds

### Requirement: Agent pass for non-mechanical issues
An agent pass SHALL cover typos/grammar and content-level forbidden material that regexes cannot catch (e.g. expected results embedded in prose), and SHALL confirm that the timeline section actually states a timeframe. An expected result is an outcome asserted as though already obtained; an anticipated outcome phrased as an expectation — "the thesis expects", "it is hypothesized" — is the form the guidance requires (guidance-model, "Anticipated outcomes are stated as expectations") and SHALL NOT be flagged. The timeframe judgement SHALL accept the phrasings students genuinely use — semester labels, quarters, seasons, month names in either language — rather than a fixed set of date formats, and SHALL flag a phase breakdown or Gantt chart that the mechanical guard cannot see, including one supplied as an image.

#### Scenario: Hidden expected-results paragraph
- **WHEN** a methodology paragraph asserts concrete expected outcomes
- **THEN** the agent pass flags it as forbidden content

#### Scenario: Expectation stated as an expectation
- **WHEN** the analysis says "The thesis expects a configuration effect smaller than the model effects that repair studies report; a negligible effect would refute the premise"
- **THEN** the agent pass raises no finding on it, and the handoff of a proposal with a current ready review does not make rewording it a step before hand-in

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

### Requirement: Override file resolution chain
The check SHALL resolve the workspace override file through a fixed chain: an explicitly passed path wins; otherwise a `guidelines.md` beside the proposal; otherwise a `guidelines.md` in the working directory. The first file found governs the whole run — later chain positions are never consulted to fill in keys the found file lacks. The chain SHALL NOT search ancestor directories or any other location, and a workspace with the proposal beside its `guidelines.md` SHALL behave exactly as it did before the chain existed.

#### Scenario: Proposal in a configured subdirectory
- **WHEN** the workspace root holds `guidelines.md`, the proposal lives in the configured proposal subdirectory, and the check runs from the root without an explicit override path
- **THEN** the root `guidelines.md` governs the run and its overrides are honored

#### Scenario: Flat workspace unchanged
- **WHEN** `guidelines.md` sits beside the proposal in the working directory
- **THEN** resolution and results are identical to the behavior before the chain existed

#### Scenario: Both chain positions occupied
- **WHEN** a `guidelines.md` exists beside the proposal and a different one exists in the working directory
- **THEN** the one beside the proposal governs the whole run and the working-directory file is not consulted

#### Scenario: No override file anywhere
- **WHEN** neither position holds a `guidelines.md` and no explicit path is passed
- **THEN** pure defaults apply, silently, as today

### Requirement: Proposal-location value validated, misplacement reported
The check SHALL validate a configured proposal-location value: it must be a string naming a relative directory inside the workspace — not absolute, not home-anchored, not escaping the root through parent references. An invalid value SHALL be reported as an error finding and the default SHALL apply for the rest of the run. An unknown key under the paths table SHALL be reported through the existing unknown-override-key error, never ignored.

When the governing `guidelines.md` configures a proposal location and the checked proposal does not live in that directory relative to the governing file's own directory, the check SHALL report an error naming the expected directory, so a half-migrated workspace fails loudly instead of skills silently disagreeing about where files live.

#### Scenario: Invalid proposal-location value
- **WHEN** the workspace sets the proposal-location path to an absolute path, a parent-escaping path, or a non-string
- **THEN** the check reports an error finding naming the constraint, and the default location applies for the rest of the run

#### Scenario: Unknown paths key
- **WHEN** the workspace sets a key under the paths table that does not resolve to an overridable leaf
- **THEN** the check reports it through the unknown-override-key error, and it is not applied

#### Scenario: Misplaced proposal
- **WHEN** the governing `guidelines.md` sets the proposal-location path to a subdirectory and the checked proposal lives outside that directory
- **THEN** the check reports an error naming the configured directory the proposal is expected in

#### Scenario: Unset key raises no location finding
- **WHEN** the workspace sets no proposal-location path
- **THEN** no misplacement finding is possible, wherever the proposal lives

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
When a document defect makes the parse fail wholesale, the check SHALL name that defect, not only the findings that follow from it. Four shapes SHALL be named: a metadata block placed at the top of the file instead of the end, headings underlined in setext style instead of prefixed with `#`, content preceding the leading `# <title>` line, and the retired layout with the title in the metadata block and canonical sections at H1.

These shapes arrive from outside this format — top frontmatter is what every other markdown tool expects, underlined headings are what a word processor exports, a stray line above the title is what an import leaves behind, and the retired layout is what this toolchain itself used to produce — so the student who produces one has done nothing careless, and a report of five missing sections or a reference list that is entirely undefined tells them nothing they can act on.

#### Scenario: Metadata block at the top of the file
- **WHEN** the file opens with a `---` block of metadata keys and does not end with one
- **THEN** the check reports the block's position and states that the remaining reference findings follow from it

#### Scenario: Headings underlined instead of prefixed
- **WHEN** the body carries no `#`-prefixed heading beyond the title line and its section titles are underlined with `===` or `---`
- **THEN** the check reports the heading style as an error naming one of the affected titles, alongside the section findings it causes

#### Scenario: Content above the title line
- **WHEN** a paragraph or comment precedes the leading `# <title>` line
- **THEN** the check names the misplaced title as the defect and states that the build would silently produce a document without a title

#### Scenario: Retired layout diagnosed
- **WHEN** a file carries a `title:` key in its metadata block and its canonical sections at H1
- **THEN** the check names the retired layout and the new locations, rather than reporting only a missing title line and flagged keys

### Requirement: Hindsight leakage reported as a warning
The skill SHALL report as warnings (never hard failures, false positives acknowledged) prose that states the proposal's own work as already done: result verbs in the first person or with the work as subject — showed, found, demonstrated, outperformed, and their German equivalents — and quantitative outcomes stated as findings. A proposal describes work that has not happened, so such a sentence is either a draft written after the work began or a proposal derived from a finished thesis.

The check SHALL fire only on sentences that are not attributed to prior work. Reporting what prior work established is what the Contribution section is for, and a rule that cannot tell "@Rivera23 showed that scheduling reduces water use" from "we showed that scheduling reduces water use" would fire on every correctly written proposal. A sentence is attributed when it carries a citation, or when it continues an attributed run: the preceding sentence in the same paragraph is attributed, and the sentence opens with a back-reference cue — a pronoun, possessive, or noun phrase referring to the cited work or its authors, in English and in German. The cue SHALL stand at the start of the sentence: first, after a single connective set off by a comma, after a preposition introducing a possessive or "the authors", or, in German verb-second order, as the subject directly after the finite verb. A cue in object position does not open a sentence. A reporting clause that names the cited authors as reporters ("…, they report, …", "so die Autoren") SHALL count as a cue wherever it stands, because it attributes the sentence explicitly. "It" counts as a cue unless it opens an expletive construction ("It is shown …", "It was found …"); the possessive "its" always counts. A sentence that speaks in the first person, or that names the work with the words the guidance prescribes for the thesis itself ("the study", "die Studie"), SHALL never count as a continuation. A blank line or a heading ends a run, and so does any sentence that is neither cited nor cued. Sentences are delimited by sentence punctuation outside citation brackets, not by line breaks. The guidance asks for exactly this form of continuation instead of a repeated citation, so the check SHALL NOT reward re-citing a source in the next sentence over referring back to it. An uncited, uncued sentence after a cited one keeps the warning, because its reader cannot tell that it reports prior work either. Each warning SHALL carry its line, quote the text it matched, and name both admissible fixes: attributing the result, by a citation or by a back-reference cue continuing a cited sentence, or writing it as a plan.

The skill SHALL NOT attempt to judge whether a research question is a settled claim in disguise. That reading requires knowing what the work found, which the document does not state; it belongs to the review skill's agent pass and to the reader.

#### Scenario: Result claim without a citation
- **WHEN** the body states that the work demonstrated an effect, in a sentence carrying no citation and continuing no attributed run
- **THEN** the check emits a warning citing the line and quoting the matched text

#### Scenario: Result attributed to prior work
- **WHEN** the same claim is attributed to a cited reference
- **THEN** no warning is emitted

#### Scenario: Result reported in a cued continuation
- **WHEN** a sentence citing a publication is followed, in the same paragraph, by a sentence that opens with a back-reference to that work or its authors and reports its result
- **THEN** no warning is emitted, because the continuation is attributed

#### Scenario: Uncued continuation
- **WHEN** a sentence citing a publication is followed, in the same paragraph, by a sentence that reports a result without a citation and without a back-reference cue
- **THEN** the check emits a warning naming the cue and the citation as fixes

#### Scenario: Run ends at the paragraph
- **WHEN** a sentence opening with a back-reference cue reports a result at the start of a paragraph that follows the cited sentence's paragraph
- **THEN** the check emits a warning, because attribution does not cross a paragraph break

#### Scenario: Run broken by the thesis's own sentence
- **WHEN** an uncited, uncued sentence stands between a cited sentence and a cued sentence reporting a result
- **THEN** the check emits a warning on the cued sentence, because the intervening sentence ended the run

#### Scenario: Attribution carried by a reporting clause or a referential pronoun
- **WHEN** a cited sentence is followed by "Most projects, they report, merge them unreviewed.", then "It uses three features.", then "Its score dropped by 30 %."
- **THEN** no warning is emitted, because every sentence continues the attributed run

#### Scenario: Own result naming the cited work as object
- **WHEN** a sentence after a cited one reports the thesis's own result while mentioning the cited work as an object, such as "We outperformed their baseline by 20 %."
- **THEN** the check emits a warning, because the sentence does not open with a back-reference and speaks in the first person

#### Scenario: The thesis named as the guidance prescribes
- **WHEN** a sentence after a cited one opens with "The study" or "Die Studie" and reports a result
- **THEN** the check emits a warning, because these words name the thesis itself in the prescribed third-person style

#### Scenario: German cued continuation
- **WHEN** a German proposal follows a cited sentence with a sentence opening with a German back-reference such as "Ihre Auswertung" that reports a result
- **THEN** no warning is emitted

#### Scenario: Quantitative outcome stated as a finding
- **WHEN** the body reports a measured improvement as an achieved number, in a sentence carrying no citation and continuing no attributed run
- **THEN** the check emits a warning

#### Scenario: Planned measurement
- **WHEN** the body states what will be measured and against which baseline
- **THEN** no warning is emitted, because the sentence describes a plan rather than an outcome

#### Scenario: Research question that reads like a conclusion
- **WHEN** a research question is phrased so that it presupposes its own answer
- **THEN** the mechanical check stays silent and the judgment is left to the review skill

### Requirement: Single-agent execution

A check run SHALL be two steps by one agent: the shipped script runs once — and a second time only for the digest comparison the read-only mandate requires of a non-interactive run — and the agent pass is one reading of the file by the same agent. Nothing in a check run SHALL be delegated to helper agents — not per finding category, per section, or per finding — and the fallback of performing the script's checks by hand when Python is missing is likewise that agent's own single reading. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, and the whole section SHALL be pinned verbatim offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the agent pass as one helper per category
- **THEN** the run performs the script step once (twice non-interactively, for the digest) and the agent pass once, in one context, and reports both in one chat message

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section or moves it below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

### Requirement: Repeated citations reported as a warning
The skill SHALL report as a warning (never a hard failure, false positives acknowledged) every sentence that cites exactly the same set of references as the sentence before it. Sentences are compared within a paragraph and across consecutive items of one list; a blank line, a heading or a table row ends the comparison. Turning repeated citations into bullet points therefore does not hide them. Sentences are delimited by sentence punctuation outside citation brackets, not by line breaks: a sentence wrapped across lines is one sentence, and a page locator such as `[@key, S. 12]` never splits one. Code spans and fenced blocks SHALL be ignored, as they are for every citation scan. A sentence whose set of cited references differs from its predecessor's SHALL NOT be reported, because a change of source is what the guidance asks to cite. Each finding SHALL carry its line and name the repeated references, and its message SHALL name the fix: cite the publication once, opening with the author-in-text form, and refer back to it in words.

The finding reports the surface pattern only. Whether a sentence without a citation still reads as attributed stays a judgement for the agent and the reader.

#### Scenario: Same reference on adjacent sentences
- **WHEN** two adjacent sentences in one paragraph each cite the same single reference
- **THEN** the check emits a warning for the second sentence, citing its line and naming the reference

#### Scenario: Same group on adjacent sentences
- **WHEN** two adjacent sentences each cite the same two references, in any order
- **THEN** the check emits a warning naming both references

#### Scenario: Source switch
- **WHEN** one sentence cites one reference and the next cites that reference together with another
- **THEN** no warning is emitted

#### Scenario: New paragraph
- **WHEN** the last sentence of one paragraph and the first sentence of the next cite the same reference
- **THEN** no warning is emitted, because the guidance asks to cite again at a new paragraph

#### Scenario: Repetition moved into bullet points
- **WHEN** consecutive items of one list each cite the same reference
- **THEN** the check emits a warning for every item after the first

#### Scenario: Page locators and wrapped lines
- **WHEN** two adjacent sentences cite the same reference with different page locators, or the second sentence wraps onto a following line before its citation
- **THEN** the check still emits the warning

### Requirement: Proposal status on request

The check skill SHALL own the question where a proposal stands and what to do next, asked without a stage in progress. It SHALL answer it by running the mechanical check as usual and then reading, beside the proposal, the review file and the companion notes file where they exist, and SHALL close with the stage handoff (skill-packaging) placing the proposal on the milestone ladder. The status read SHALL stay within the check's read-only mandate and SHALL render no substance verdict: the only content judgement it adds is whether an existing review still covers the current text, judged on the research questions, scope, method, contribution delta and the passages the review's blockers cite.

Open `[TODO: …]` markers SHALL be sorted in the handoff into decisions the student owes the proposal and execution details whose deferral record (guidance-model, Readiness) can be filled; the handoff MAY propose moving the execution details into the notes file as clarify-early items, which is a writing step the user approves, never a step the check performs.

Routes, the first that applies: mechanical errors → a writing pass that fixes them; open markers that are decisions the student owes the proposal → those decisions, put as anchored choices, before any review; no errors and no review, or a superseded one → a fresh review; no errors and a current review with blockers → a revision of those blockers; no errors and a current review with no blocker → the hand-in build.

#### Scenario: Status asked in a fresh session
- **WHEN** the user asks where their proposal stands and the workspace holds a mechanically clean draft with no review file
- **THEN** the check runs, the proposal file stays byte-identical, and the handoff places it at complete draft and recommends a review of it

#### Scenario: Review beside the proposal judged an earlier scope
- **WHEN** the review file beside a clean draft judged research questions and a scope the current text no longer carries
- **THEN** the handoff says the review judged an earlier version and recommends a fresh review, and no review is written during the check

#### Scenario: Current ready review
- **WHEN** the draft is mechanically clean and the review beside it covers the current text with no blocker
- **THEN** the handoff places the proposal at ready for supervisor discussion and recommends building the hand-in, without building anything

#### Scenario: Open markers sorted
- **WHEN** the draft carries two markers that need the student's decision and three that are execution details
- **THEN** the handoff names the two as what blocks the next milestone, recommends settling them — the one with options in the student's text as an anchored choice — before a review, proposes moving the three into the notes file, and no file is modified

### Requirement: Orphaned companions reported as a warning
The check SHALL list the directory that holds the checked proposal, including its `img/` folder. When the governing `guidelines.md` configures a proposal location, the check SHALL also list the workspace root.

A file is family-shaped when its name has one of the family shapes of proposal-file-format "Proposal family under one handle" under a slug of the form Content-derived slug filenames sets: lowercase ASCII, hyphen-separated. A slug is sheltered when a proposal, a notes file or a harvest record carrying it sits in the proposal location; a harvest record shelters an idea skill-reverse has not yet written, a notes file one that has not been seeded. A `-review` or `-feedback` markdown file whose base slug has no proposal and which ends in a metadata block is itself a proposal, for example `ml-code-review.md`; a file of another family shape carrying the base slug does not count as its proposal. The checked proposal is a proposal whatever its name. A `-handout` file is a companion by its suffix alone.

The check SHALL report a warning, under one stable rule identifier, for each of the following:

- each family-shaped file under an unsheltered slug that carries an unambiguous companion (a review, feedback, handout or figure) or, when the slug has at least two words as Content-derived slug filenames requires, at least two kept files;
- when a proposal location is configured, each family-shaped file at the workspace root, other than a proposal, whose slug is sheltered in the proposal location;
- each figure the checked proposal links under `img/` whose file name does not start with the proposal's own slug followed by `-`.

Built outputs (`.pdf`, `.typ`, `.tex`, `.docx`) SHALL NOT make a slug reportable on their own, SHALL be reported only together with a reportable slug's other files, and SHALL never be reported while a workspace build definition sits beside the proposal. The check SHALL never report any of these:

- `ideation.notes.md`;
- the workspace-level files, the troubleshooting captures and the installer-managed files of proposal-file-format "Working material stays out of the workspace";
- workspace build definitions;
- hidden files or folders, `.gitignore` files included;
- an `img/` file whose name resolves to no reportable slug.

The finding SHALL be a warning and SHALL NOT change the exit code. For this finding, the check SHALL open another file only to tell a proposal from a companion, and SHALL change nothing. The message SHALL name the file and the slug it carries. It SHALL also say that a rename which moved only part of the family is the usual cause, and that a file the user placed there on purpose can be left as it is. For a stale figure link, the message SHALL name the linked path and the proposal's own slug, and SHALL name the old slug only when it resolves against a family-shaped file present.

#### Scenario: Leftovers of a partial rename
- **WHEN** the directory holds `<new>.md` beside a kept file and a review under `<old>`, with no `<old>.md`, no `<old>.notes.md` and no `<old>.harvest.md`
- **THEN** the check reports one orphan warning per leftover file, each naming `<old>`, and the exit code is what the proposal's other findings make it

#### Scenario: Idea not yet seeded
- **WHEN** the directory holds `<idea>.notes.md` and `<idea>.reading-list.md` and no `<idea>.md`
- **THEN** no orphan warning names either file

#### Scenario: Harvest awaiting inspection
- **WHEN** the directory holds `<thesis>.harvest.md` written by a reverse run that stopped for inspection, and no `<thesis>.md`
- **THEN** no orphan warning names it

#### Scenario: Stale figure link with a resolvable old slug
- **WHEN** the checked proposal links `img/<old>-pipeline.png` while its own slug is `<new>`, and a review `<old>-review.md` is present
- **THEN** the check reports an orphan warning for the link that names the linked path, `<new>` and `<old>`

#### Scenario: Stale figure link without a resolvable old slug
- **WHEN** the checked proposal links `img/<old>-pipeline.png` while its own slug is `<new>`, and no other file carries `<old>`
- **THEN** the check reports an orphan warning for the link that names the linked path and `<new>`, and names no other slug

#### Scenario: Workspace, build and installer files ignored
- **WHEN** the directory holds `guidelines.md`, `api-keys.env`, `bug-report/`, `proposal-build.sh`, `faculty.typ`, `proposal.pdf`, `check-output.txt`, `.gitignore`, `.agents/skills/`, `skills-lock.json` and `ideation.notes.md`
- **THEN** none of them is reported

#### Scenario: Source documents and project files ignored
- **WHEN** the directory holds `submission.pdf`, `expose.docx`, `thesis.pdf`, `vite.config.ts`, `data.tar.gz` and `img/screenshot.png`, each the only file under its name
- **THEN** none of them is reported

#### Scenario: Proposal whose name ends like a companion
- **WHEN** `ml-code-review.md` ends in a metadata block and no `ml-code.md` exists beside it
- **THEN** it is treated as a proposal and is not reported

#### Scenario: Companion-shaped proposal beside a file under its base slug
- **WHEN** `ml-code-review.md` ends in a metadata block, no `ml-code.md` exists beside it, and `ml-code.pdf` or `ml-code.candidates.yaml` does
- **THEN** neither file is reported

#### Scenario: Tool files under a one-word name
- **WHEN** the directory holds a LaTeX build's `thesis.tex`, `thesis.pdf`, `thesis.synctex.gz` and `thesis.run.xml`, or a code repository's `tsconfig.app.json` and `tsconfig.spec.json`
- **THEN** none of them is reported

#### Scenario: Dump at the workspace root
- **WHEN** the governing `guidelines.md` sets the proposal location to `proposals/`, the proposal `<slug>.md` sits there, and `<slug>.candidates.yaml` sits at the workspace root
- **THEN** the check reports an orphan warning for the root file naming `<slug>`

#### Scenario: Read-only listing
- **WHEN** the check runs over a directory holding orphaned companions
- **THEN** every file in the directory is byte-identical afterwards and none was moved

### Requirement: Review currency warning
The deterministic script SHALL read the review file the review skill writes for the checked proposal (skill-review, Persisted, actionable output; proposal-file-format, Proposal family under one handle), and no other file for this purpose. When that review carries a research-questions record (skill-review, Research questions recorded in the review), the script SHALL compare the record with the research questions the proposal currently declares. This read is part of the check's read-only run: the script SHALL NOT write to the review.

The proposal's questions SHALL be the items of the ordered list in its research-questions section, found exactly as the research-question count rule finds them. The record's questions SHALL be the items, ordered or bulleted, of the first list under the last heading in the review titled `Research questions reviewed` or `Begutachtete Forschungsfragen` — either title whatever the proposal's language, at any heading level, in any letter case. That list SHALL end at the next heading, at a thematic break, or at the first line after a blank line that is neither a list item nor indented, so text below the record, list-shaped or not, never counts as a recorded question. On both sides an item SHALL start at an unindented list marker of the kind that side accepts and run to the next such marker, a blank line, or the section's end; indented lines, nested list items included, continue it. Both sides SHALL be compared item by item, in order, after removing every invisible format character (Unicode general category Cf, such as the soft hyphen, the zero-width space, the word joiner and the byte-order mark), normalizing Unicode compatibility forms, collapsing every run of whitespace, line breaks included, into one space, and folding typographic variants to one form each: straight and curly single quotes, including their low-9 and reversed forms, to one single quote; straight and curly double quotes, including their low-9 and reversed forms, to one double quote; and the hyphen-minus, hyphen, non-breaking hyphen, en dash, em dash and minus sign to one dash. List-marker style, numbering, invisible format characters, and which of those quote or dash variants is used SHALL NOT count; wording, letter case, every other punctuation mark and order SHALL.

When the two lists differ, the script SHALL report exactly one warning carrying the stable identifier `review-questions-changed`. Its message SHALL name the review file and each position that differs, as changed, added or removed (for example `RQ4 removed`), SHALL say that the review may describe an earlier version of the proposal, and SHALL say that a fresh review replaces it while the review file is left as it is, so an agent that runs the check after its own pass is never steered into editing the record or reverting a question to silence the warning. It SHALL NOT quote any question's text, so a report that leaves the workspace carries no proposal wording through it. The finding SHALL be a warning, never an error: it SHALL NOT change the exit code in either output mode, and the reported digest SHALL continue to identify the proposal file alone.

The script SHALL report nothing about the review when:

- no review file exists;
- the review cannot be read, or cannot be read as UTF-8 text;
- the review carries no record, or a record with no list item — every review written before the record existed included;
- the proposal declares no ordered-list research question, which other findings already cover.

The review file SHALL never cause the script to fail.

When the user asks where the proposal stands, the check skill SHALL take this warning as settling the research-question part of its judgement whether the review still covers the text: any `review-questions-changed` warning means the review judged other research questions and is superseded, whatever the size of the difference, and the routes treat it as a superseded review (a fresh review once no earlier route applies). A review without a record SHALL be judged from its content, as before.

#### Scenario: Scope narrowed after the review
- **WHEN** the review's record lists four research questions and the proposal now declares the first three of them unchanged
- **THEN** the check reports one `review-questions-changed` warning naming RQ4 as removed, and the exit code is the one the proposal's other findings give

#### Scenario: Question reworded
- **WHEN** the record's second question differs from the proposal's second question in one word
- **THEN** the warning names RQ2 as changed and its message contains neither version of the question

#### Scenario: Same questions, different layout
- **WHEN** the record lists the proposal's questions with different line wrapping, bullet markers instead of numbers, and non-breaking spaces where the proposal has plain ones
- **THEN** no review finding is reported

#### Scenario: Quotes and dashes typeset differently
- **WHEN** the record has straight quotes and a hyphen-minus where the proposal's questions have curly quotes and an en dash, and the wording is otherwise identical
- **THEN** no review finding is reported

#### Scenario: Invisible format characters
- **WHEN** a proposal's question carries a soft hyphen inside a word and the record copies it without one, or the record carries a zero-width space the proposal's question lacks, and the wording is otherwise identical
- **THEN** no review finding is reported

#### Scenario: Letter case changed
- **WHEN** the record's first question differs from the proposal's first question only in the case of one letter
- **THEN** the warning names RQ1 as changed

#### Scenario: Nested item stays inside its question
- **WHEN** the proposal declares three research questions, the second continuing on an indented sub-bullet, and the record copies all three with the same sub-bullet beneath the second
- **THEN** no review finding is reported, and the count rule still counts three research questions

#### Scenario: Review written before the record existed
- **WHEN** a review beside the proposal carries verdict and findings but no record section
- **THEN** no review finding is reported

#### Scenario: Notes below the record
- **WHEN** the review's record matches the proposal's questions and is followed, without a heading of its own, by a paragraph of notes with a bulleted list, or by a thematic break
- **THEN** no review finding is reported

#### Scenario: German record beside an English proposal
- **WHEN** the record is titled `## Begutachtete Forschungsfragen` and lists exactly the questions of an English proposal
- **THEN** no review finding is reported

#### Scenario: Review that cannot be read
- **WHEN** a directory, or a file that is not valid UTF-8, stands at the review's path
- **THEN** no review finding is reported, the script completes, and the exit code is the one the proposal's findings give

#### Scenario: Status asked after a narrowing
- **WHEN** the user asks where the proposal stands and the script reports `review-questions-changed`
- **THEN** the handoff says the review judged other research questions and recommends a fresh review with a phrase to send, and neither the proposal nor the review file is modified

#### Scenario: Errors beside a superseded review
- **WHEN** the user asks where the proposal stands and the script reports a mechanical error together with `review-questions-changed`
- **THEN** the handoff's next step is the writing pass that fixes the errors, the review is named as superseded rather than current, and neither file is modified

#### Scenario: Typo corrected in a question
- **WHEN** the user asks where the proposal stands and the only difference behind `review-questions-changed` is a corrected typo in RQ2
- **THEN** the handoff still treats the review as superseded and recommends a fresh review
