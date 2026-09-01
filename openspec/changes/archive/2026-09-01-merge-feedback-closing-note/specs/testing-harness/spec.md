## MODIFIED Requirements

### Requirement: Supervise feedback coverage

The harness SHALL carry an L1 task that runs the supervise skill against a synthetic raw submission fixture and asserts the feedback contract with dedicated verdict functions: the feedback exists as the slug-named feedback file, it carries at most five curated points, it opens with one of the student-facing verdict tiers — including the idea-stage rendering in English and German — the feedback contains no personal data from the fixture, every skill pointer in the feedback names a skill that exists in the set, and the feedback carries the shared closing note verbatim in the language it was written in. The closing-note verdict SHALL fail on a paraphrase, on the wrong language's snippet, and on a closing note that arrives with markup the shared snippet does not carry. The synthetic fixtures SHALL include at least one non-standard-format submission (pasted-text fragment or PDF-shaped input) so normalization is exercised, not bypassed. Non-interactive runs (the Inspect task and the dev runner) SHALL pre-answer the borderline deferral in the request so a single-turn run cannot stall waiting for the professor.

#### Scenario: Feedback contract asserted
- **WHEN** the supervise L1 task runs against a messy synthetic submission
- **THEN** the scorers report feedback presence, point count, verdict tier, personal-data absence, skill-pointer validity, and closing-note fidelity as separate verdicts

#### Scenario: Personal data leak caught
- **WHEN** a run leaves the fixture's fake student name or matriculation number anywhere in the feedback
- **THEN** the personal-data verdict fails and names the leaking file

#### Scenario: Paraphrased closing note caught
- **WHEN** a run rewrites the closing note instead of quoting the shared snippet
- **THEN** the closing-note verdict fails and says the snippet was not carried verbatim

#### Scenario: Offline verdict coverage
- **WHEN** the L0 suite runs
- **THEN** every supervise verdict function is exercised by unit tests without model calls

#### Scenario: Idea-stage feedback recognized
- **WHEN** the feedback opens with the idea-stage rendering instead of the blunt review vocabulary
- **THEN** the tier verdict passes in both English and German

#### Scenario: Headless run does not stall
- **WHEN** the L1 task or dev runner drives a borderline submission single-turn
- **THEN** the request's pre-answer resolves the deferral and the run completes

### Requirement: Bilingual terminology guard

The L0 suite SHALL verify that the shipped bilingual surfaces use the per-language document term: the supervise closing note's English section names the document a proposal and never an Exposé; its German section names it an Exposé and contains "proposal" only inside identifiers or URLs; and the shipped German verdict-tier phrases and German subtitle strings use "Exposé". The guard SHALL name the offending file and term on failure.

#### Scenario: Crossed term caught
- **WHEN** "Exposé" enters the closing note's English section, or a bare "proposal" enters its German prose outside an identifier or URL
- **THEN** the L0 suite fails and names the file and the offending term

#### Scenario: Identifiers exempt
- **WHEN** the German section carries the repository URL or a `proposal-*` skill name
- **THEN** the guard does not flag it

## ADDED Requirements

### Requirement: Closing-note shape guard

The L0 suite SHALL verify the shape of the shipped supervise closing note, since its whole purpose is to survive a channel that renders no markup and nothing else checks that. For each of its English and German sections the guard SHALL require exactly one paragraph, no line beginning with a blockquote, heading, or list marker, and no emphasis markers anywhere in the section. It SHALL require the English section to open with "Note:" and the German section to open with "Hinweis:" and to name the artifact "Rückmeldung". The guard SHALL name the offending section and the offending construct on failure.

#### Scenario: Markup reintroduced
- **WHEN** a blockquote marker, heading marker, or bold run-in returns to either section of the shared snippet
- **THEN** the L0 suite fails and names the section and the construct

#### Scenario: Paragraph split
- **WHEN** a section is split into two paragraphs
- **THEN** the L0 suite fails, because a run-in label reaches only the paragraph it opens

#### Scenario: Run-in label missing
- **WHEN** a section no longer opens with its language's run-in label
- **THEN** the L0 suite fails and names the section
