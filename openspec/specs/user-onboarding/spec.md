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

### Requirement: Visual workflow demo in README
The README SHALL show a visual, time-condensed impression of the workflow (idea → ideate → literature search → write → check → publish) near the top, before the textual skill explanation, as a storyboard of screenshots from a real condensed session that renders inline on the repository's GitHub page.

#### Scenario: Visitor grasps the tool in seconds
- **WHEN** a visitor opens the repository page without reading any text
- **THEN** they see a visual demo conveying that an agent guides a vague thesis idea into a checked, literature-grounded proposal

### Requirement: Users never work in this repository
All user activity happens in their own workspace; this repository is exclusively for developing and testing the skills, and its documentation SHALL say so.

#### Scenario: User seeks their files
- **WHEN** a user wonders where their proposals live
- **THEN** the documentation directs them to their own workspace, never into this repository

