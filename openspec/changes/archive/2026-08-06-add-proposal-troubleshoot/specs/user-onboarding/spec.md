## ADDED Requirements

### Requirement: README names the path for a problem

The README SHALL tell a reader what to do when the skills misbehave, before it discusses model support. It SHALL name the diagnostic skill as the entry point, SHALL state that updating the installation is the first thing to try, and SHALL state that a report is assembled locally and delivered by the user, with the proposal's own text excluded unless the user chooses to include it.

An invitation to open an issue without any of that is what this replaces: it produces reports naming a symptom and nothing else, and it invites a student to paste an unpublished thesis idea into a public tracker.

#### Scenario: Reader hits a problem

- **WHEN** a reader looks for what to do about a misbehaving skill
- **THEN** the README names the diagnostic skill, the update-first step, and that reports stay local until the reader sends them

#### Scenario: Reader worries about confidentiality

- **WHEN** a reader wants to know whether reporting exposes their idea
- **THEN** the README states that proposal text is excluded by default and included only by the reader's choice

### Requirement: Issue template mirrors the generated report

The repository SHALL provide a structured issue template whose fields correspond one-to-one with the sections of a generated report, so a user delivering a report by issue transfers content rather than reinterpreting it. The template SHALL request the triage outcome, the measured environment, the install identification, and the account of the failing exchange, and SHALL state that proposal text is not required.

#### Scenario: User files a generated report as an issue

- **WHEN** a user opens an issue holding a generated report
- **THEN** every template field has a corresponding report section to fill it from

#### Scenario: User reports without having run the diagnostic skill

- **WHEN** a user files the template without a generated report
- **THEN** the template names the diagnostic skill as the way to produce the missing content
