## MODIFIED Requirements

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
