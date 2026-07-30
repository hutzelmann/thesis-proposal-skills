## ADDED Requirements

### Requirement: Citation form selection

The skill SHALL choose between the two citation syntaxes by grammatical role, consistently across a proposal: the author-in-text form only where the cited authors are the grammatical subject or agent of the sentence, and the bracketed form where the citation is evidence attached to a claim. The skill SHALL NOT type an author name next to a bracketed citation by hand, because the rendered author label is derived from the reference entry.

#### Scenario: Authors act in the sentence

- **WHEN** a sentence states what the cited researchers propose, show, or argue
- **THEN** the citation is written in the author-in-text form

#### Scenario: Citation supports a claim

- **WHEN** a sentence states a fact about the field and the cited work is evidence for it
- **THEN** the citation is written in the bracketed form and no author name appears in the prose

#### Scenario: Author name typed manually

- **WHEN** refining a proposal that contains a hand-typed author name immediately before a bracketed citation
- **THEN** the skill replaces the pair with the author-in-text form so the name stays derived from the reference entry
