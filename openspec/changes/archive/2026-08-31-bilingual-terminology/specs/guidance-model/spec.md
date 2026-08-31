# guidance-model delta

## ADDED Requirements

### Requirement: Per-language document terminology

User-facing English text SHALL call the document a proposal and SHALL NOT call it an Exposé; user-facing German text SHALL call it an Exposé and SHALL NOT substitute an English or anglicized term for it. Identifiers are exempt in both directions: URLs, repository names, and skill names (`thesis-proposal-skills`, `proposal-*`) keep their spelling regardless of the surrounding language.

#### Scenario: English text names the document
- **WHEN** a skill or shared snippet renders English user-facing prose about the document
- **THEN** the document is called a proposal, never an Exposé

#### Scenario: German text names the document
- **WHEN** a skill or shared snippet renders German user-facing prose about the document
- **THEN** the document is called an Exposé, while skill and repository identifiers keep their English names
