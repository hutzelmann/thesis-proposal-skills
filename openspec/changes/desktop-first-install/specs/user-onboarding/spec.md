# Spec Delta

## MODIFIED Requirements

### Requirement: Newcomer-ready README
The repository README SHALL address users who have never used an AI agent: what the tool is, the workflow (ideate ⇄ literature search → write → check → review → publish), and how to install the skills — the install prompt to paste into their agent, the plugin button where their app has one, and where the per-app install guide lives — without assuming prior agent knowledge or a terminal.

#### Scenario: First contact
- **WHEN** an AI-newcomer reads the README top to bottom
- **THEN** they know what to install, in which order, and what their first prompt to the agent could be

#### Scenario: Reader without a terminal
- **WHEN** a reader who has never opened a terminal follows the README's install step
- **THEN** every step happens inside their agent app or its settings, and the terminal command appears only as an optional alternative

### Requirement: Zero-build quick start
The quick start SHALL require no build toolchain and no terminal: get an agent, open it in a workspace folder, install the skills by pasting the install prompt or using the app's plugin button, start ideating. Build tooling appears only in the optional publishing section.

#### Scenario: Quick start followed literally
- **WHEN** a user completes the quick start steps
- **THEN** they can ideate, write, and review proposals without any converter installed

### Requirement: Concrete agent walkthroughs
An install guide SHALL provide a short recipe for each featured app, marked as examples rather than endorsements, plus one entry covering every other local agent through the install prompt, keeping the skill set itself agent-agnostic. Each recipe SHALL state the date and the app version on which a maintainer last carried it out end to end; a recipe nobody has carried out SHALL NOT be published. Where an app offers both the plugin button and the install prompt, the recipe SHALL name one as the route to use and SHALL state that the two must not be combined.

#### Scenario: Student without any agent
- **WHEN** a student follows a recipe
- **THEN** they reach a working agent with the skills installed using only the documented steps

#### Scenario: Recipe not yet verified
- **WHEN** a recipe has not been carried out end to end on a real installation of its app
- **THEN** it is absent from the published guide rather than published on research confidence

#### Scenario: App with both routes
- **WHEN** a student's app supports the plugin button and the install prompt
- **THEN** the recipe names which one to use and warns that installing both loads every skill twice

### Requirement: README names the path for a problem

The README SHALL tell a reader what to do when the skills misbehave, before it discusses model support. It SHALL name the diagnostic skill as the entry point, SHALL state that updating the installation — the same way it was installed — is the first thing to try, and SHALL state that a report is assembled locally and delivered by the user, with the proposal's own text excluded unless the user chooses to include it.

An invitation to open an issue without any of that is what this replaces: it produces reports naming a symptom and nothing else, and it invites a student to paste an unpublished thesis idea into a public tracker.

#### Scenario: Reader hits a problem

- **WHEN** a reader looks for what to do about a misbehaving skill
- **THEN** the README names the diagnostic skill, the update-first step for each install route, and that reports stay local until the reader sends them

#### Scenario: Reader worries about confidentiality

- **WHEN** a reader wants to know whether reporting exposes their idea
- **THEN** the README states that proposal text is excluded by default and included only by the reader's choice

### Requirement: Issue template mirrors the generated report

The repository SHALL provide a structured issue template whose fields correspond one-to-one with the sections of a generated report, so a user delivering a report by issue transfers content rather than reinterpreting it. The template SHALL request the triage outcome, the measured environment, the install identification including the install route, and the account of the failing exchange, and SHALL state that proposal text is not required. Its update-first confirmation SHALL apply to every install route rather than naming one command.

#### Scenario: User files a generated report as an issue

- **WHEN** a user opens an issue holding a generated report
- **THEN** every template field has a corresponding report section to fill it from

#### Scenario: User reports without having run the diagnostic skill

- **WHEN** a user files the template without a generated report
- **THEN** the template names the diagnostic skill as the way to produce the missing content

#### Scenario: User installed through the plugin button

- **WHEN** a user who installed through the plugin button confirms they updated first
- **THEN** the template's confirmation fits their route without asking them to run a command they never used

## ADDED Requirements

### Requirement: Chat-only apps flagged honestly

The install guide SHALL carry a separate, flagged section for apps that run skills only in a chat sandbox without the user's own folder. It SHALL state which skills work there and which do not — literature search needs network access the sandbox may not grant, and a proposal file does not persist between conversations — and SHALL redirect to the plugin button where the app supports one, or to a free desktop agent that runs every skill. The section SHALL NOT present a chat-only app as equivalent to a desktop agent.

#### Scenario: Student only has a chat app

- **WHEN** a student whose only agent is a chat app reads the install guide
- **THEN** they learn what will and will not work there, and which free desktop agent runs everything

### Requirement: Literature-search network guidance

The install guide SHALL tell a student what to do when literature search cannot reach its sources, in the words the search actually reports. It SHALL name the public academic services the search reaches, and for each featured app the setting or approval that grants the agent network access. It SHALL also name the interpreter's own certificate setup where that is the cause. An automated check SHALL fail when the services the guide names differ from those the search scripts contact. The guidance SHALL sit outside the quick start, where it does not stand between a student and their first session.

#### Scenario: Search reports offline

- **WHEN** a student's literature search reports that the services are unreachable
- **THEN** the guide names the services and the network setting for the student's app

### Requirement: Supervisors can provision a cohort

The supervisor-facing documentation SHALL state that an organization's administrator can make the skills available to every member through the app's own organization plugin management. It SHALL name only apps that can load the repository's plugin definition, and SHALL say which organization plans cannot yet, so an administrator never provisions a cohort with a plugin that delivers nothing. It SHALL name this as a property of the organization's app setup rather than of the skills, and SHALL NOT turn any institution's setup into a shipped default.

#### Scenario: Supervisor with a cohort on an organization plan

- **WHEN** a supervisor wants the whole cohort to have the skills without each student installing them
- **THEN** the documentation points at the organization-level plugin management of the apps that can load the plugin

#### Scenario: Organization app that cannot load the plugin

- **WHEN** a supervisor's institution runs an app whose organization management cannot load the plugin
- **THEN** the documentation says so, and that the cohort installs with the prompt instead
