## MODIFIED Requirements

### Requirement: Forbidden content
The default guidance SHALL forbid: work plans/timelines/milestones, supervisor names, the author's own name, expected-results sections, deliverables/code fragments, personal data (matriculation number, address, email, study program), preliminary thesis chapter structures, and confidentiality markers. The guidance SHALL state that the writer is identified outside the document — hand-in channel, upload form, filename — so the absence of a name reads as a rule rather than an omission.

#### Scenario: Timeline present
- **WHEN** a proposal contains a schedule heading
- **THEN** tooling reports it as forbidden content under default guidance

#### Scenario: Student asks where their name goes
- **WHEN** the guidance is consulted about naming the writer
- **THEN** it states that proposals stay anonymous and identification happens through the hand-in channel, not the document
