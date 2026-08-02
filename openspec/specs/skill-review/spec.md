# skill-review Specification

## Purpose
High-level content review of a proposal — arguments, literature grounding, sharpness — producing an enumerated, actionable review file.
## Requirements
### Requirement: Content-level review scope
The skill SHALL review argument structure, soundness, missing literature or information, sharpness/focus, unnecessary content, redundancy, and inconsistencies — including the semantic guidance rules (analytical research questions, explicit contribution delta, one declared methodology, and — where Mixed Methods is declared — a substantive Integration subsection).

#### Scenario: Implementation-goal research questions
- **WHEN** research questions are phrased as "how can X be implemented"
- **THEN** the review flags them and suggests analytical reformulations

#### Scenario: Mixed Methods without integration
- **WHEN** a proposal declares Mixed Methods but its Integration subsection does not say which research questions each strand answers or how their results combine
- **THEN** the review flags it as two unrelated small studies and suggests dropping a strand

### Requirement: Format-agnostic
The review SHALL NOT complain about section layout, ordering, headings, or markup conventions — structure compliance belongs to check.

#### Scenario: Non-canonical structure
- **WHEN** the proposal uses a free-form section structure
- **THEN** the review addresses only content and arguments, with no structural complaints

### Requirement: Persisted, actionable output
The review SHALL be written to `<slug>-review.md` next to the proposal (overwritten per run), in the proposal's declared language, as an enumerated list of issues each with an actionable suggestion.

#### Scenario: German proposal reviewed
- **WHEN** the proposal declares `lang: de`
- **THEN** the review file is written in German

### Requirement: Grammar hint, never a list
If obvious grammar/spelling problems exist, the review SHALL end with a brief hint including at most one or two examples — never an exhaustive enumeration.

#### Scenario: Pervasive passive voice and typos
- **WHEN** the text shows widespread language issues
- **THEN** the review closes with a short hint and one or two examples, deferring the full pass to check

