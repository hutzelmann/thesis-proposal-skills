# user-onboarding Specification

## Purpose
Documentation that gets a student with zero AI-agent experience from nothing to a working proposal workspace.
## Requirements
### Requirement: Newcomer-ready README
The repository README SHALL address users who have never used an AI agent: what the tool is, the workflow (ideate ⇄ literature search → write → check → review → publish), and the install command — without assuming prior agent knowledge.

#### Scenario: First contact
- **WHEN** an AI-newcomer reads the README top to bottom
- **THEN** they know what to install, in which order, and what their first prompt to the agent could be

### Requirement: Zero-build quick start
The quick start SHALL require no build toolchain: get an agent, create a workspace folder, install the skills, start ideating. Build tooling appears only in the optional publishing section.

#### Scenario: Quick start followed literally
- **WHEN** a user completes the quick start steps
- **THEN** they can ideate, write, and review proposals without any converter installed

### Requirement: Concrete agent walkthroughs
A getting-started document SHALL provide copy-paste setup for one or two concrete agents (marked as examples, not endorsements), keeping the skill set itself agent-agnostic.

#### Scenario: Student without any agent
- **WHEN** a student follows a walkthrough
- **THEN** they reach a working agent with the skills installed using only the documented steps

### Requirement: Condensed session demo in README
The README SHALL show a time-condensed impression of the workflow (idea → ideate → literature search → write → check → publish) near the top, before the textual skill explanation, as a sequence of short quoted exchanges attributing each answer to the skill that produced it. The demo SHALL be plain markdown with no images, and SHALL be collapsed by default so that its summary lines alone convey the workflow order.

#### Scenario: Visitor grasps the tool in seconds
- **WHEN** a visitor opens the repository page without expanding anything
- **THEN** the collapsed demo summaries alone convey that an agent guides a vague thesis idea through literature search into a checked, publishable proposal

#### Scenario: Visitor reads the session
- **WHEN** the visitor expands a demo section
- **THEN** they see quoted exchanges between the student and named skills, rendered by any markdown viewer without downloading images

### Requirement: Authentic, synthetic demo content
The README demo SHALL be curated from a real agent session run on a synthetic fixture topic. It MUST NOT contain personal data or fabricated literature references; any papers shown MUST come from a real literature-search result, and the harvested session output backing them SHALL stay committed as an audit trail.

#### Scenario: Demo content audit
- **WHEN** the README demo text is compared against the committed harvested session output
- **THEN** every shown paper reference and proposal excerpt traces back to real session output on the synthetic topic, with only ordering and length condensed

### Requirement: Users never work in this repository
All user activity happens in their own workspace; this repository is exclusively for developing and testing the skills, and its documentation SHALL say so.

#### Scenario: User seeks their files
- **WHEN** a user wonders where their proposals live
- **THEN** the documentation directs them to their own workspace, never into this repository

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

