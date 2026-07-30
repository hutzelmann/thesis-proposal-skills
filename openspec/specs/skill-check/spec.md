# skill-check Specification

## Purpose
Low-level advisory quality gate: deterministic mechanical checks plus an agent pass, reported honestly in two buckets, results in chat only.
## Requirements
### Requirement: Deterministic mechanical checks
The skill SHALL verify deterministically, driven by the structured guidance data plus workspace overrides: required sections present with canonical titles; exactly one methodology from the closed set with its required subsections; forbidden headings absent; every declared research question referenced as `(RQn)` in the methodology section; citation-key consistency in both directions (cited-but-undefined is an error, defined-but-uncited a warning); duplicate reference ids; `min_references` satisfied; leftover `[TODO: …]` markers; and file-format guardrails (blank line before the trailing metadata block, exactly one metadata block, no boolean-literal keys).

#### Scenario: Cited key missing from references
- **WHEN** the body cites `[@Kim24]` and no reference with id `Kim24` exists
- **THEN** the check reports it as a mechanical failure with the location

#### Scenario: RQ never referenced in methodology
- **WHEN** the proposal declares RQ3 and the methodology section never contains `(RQ3)`
- **THEN** the check reports the missing cross-reference

### Requirement: Warning-class pattern checks
The skill SHALL report as warnings (never hard failures, false positives acknowledged): first-person pronouns; three consecutive sentences starting with the same word; personal-data patterns (emails, matriculation numbers); confidentiality markers in English and German ("confidential", "internal use only", "do not distribute", "NDA", "vertraulich", "nur für den internen Gebrauch"), because theses get published; and author-in-text citations of references that declare neither an author nor an editor, because those render as a quoted title inside the sentence.

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
An agent pass SHALL cover typos/grammar and content-level forbidden material that regexes cannot catch (e.g. expected results embedded in prose).

#### Scenario: Hidden expected-results paragraph
- **WHEN** a methodology paragraph asserts concrete expected outcomes
- **THEN** the agent pass flags it as forbidden content

