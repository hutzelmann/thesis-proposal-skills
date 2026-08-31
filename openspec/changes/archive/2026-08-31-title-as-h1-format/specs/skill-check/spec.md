# skill-check Delta

## MODIFIED Requirements

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
