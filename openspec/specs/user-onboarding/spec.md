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
All user activity happens in their own workspace; this repository is exclusively for developing and testing the skills, and its documentation SHALL say so. The install guide SHALL state that the proposals folder is a folder of the student's own, empty when they start, and never a clone or copy of this repository, and that the repository's contributor instruction file is meant for people developing the skills and is never copied into a proposals folder. Wherever the guide names the workspace root, it SHALL call it the proposals folder, and it SHALL state that each proposal gets a folder in it, naming when the proposal-location setting is the better choice without describing any layout the skills do not offer.

#### Scenario: User seeks their files
- **WHEN** a user wonders where their proposals live
- **THEN** the documentation directs them to their own workspace, never into this repository

#### Scenario: Student about to clone the repository as their workspace
- **WHEN** a student reads the install guide before creating a place for their proposals
- **THEN** the guide tells them to create an empty folder of their own, that a clone of this repository is not a proposals folder, and that the repository's contributor instructions do not belong in it

#### Scenario: Student wonders whether to use a subfolder
- **WHEN** a student reads what the proposals folder will contain
- **THEN** the guide says each proposal gets a folder of its own named after it, when collecting those folders in a subfolder is worth it, and that the workspace-level files stay at the top either way

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

### Requirement: Supervisors can discover methodology configurability
The supervisor-facing documentation SHALL state that the methodology set is configurable per workspace — a branch can be added, a shipped branch replaced, and a shipped branch disabled — and SHALL point at the skill that produces the workspace file, at a working example of a branch declaration, and at a catalog of ready-to-paste declarations for common non-default methodologies. The catalog SHALL provide, per entry, the declaration in the exact format the workspace file accepts, a statement of when the methodology fits, and the primary source it derives from. The Mixed Methods entry SHALL carry an explicit scope warning and a subsection that forces the integration point to be named at proposal time.

#### Scenario: Supervisor with a missing method
- **WHEN** a supervisor's accepted methodology is not in the shipped defaults
- **THEN** the README tells them the set is a workspace config rather than a fork, and the catalog gives them a declaration to paste and adapt

#### Scenario: Mixed methods requested
- **WHEN** a workspace enables the catalog's Mixed Methods branch
- **THEN** the pasted declaration itself carries the scope warning and an integration-plan subsection, so a proposal that cannot name its point of interface fails the branch's own contract

#### Scenario: Design science requested
- **WHEN** a supervisor looks for Design Science Research in the catalog
- **THEN** the catalog explains it as a rename of the shipped Prototype Implementation branch rather than providing a duplicate declaration

### Requirement: Setup tiers and readiness checks in the install guide

The install guide SHALL state, in one table near its top, what each kind of work needs: developing an idea, writing and reviewing a proposal need only an agent app with the skills installed; the checks, the literature search and the other script-backed steps need Python 3.11 or newer, and the literature search also needs network access; PDF export needs pandoc plus typst or a LaTeX engine; API keys are optional. PDF export and API keys SHALL be marked optional, so that a student who only writes is never told to install them.

The guide SHALL carry a readiness checklist of exactly four checks, each built on output the skills or their scripts already produce, and each SHALL state what it proves and what it does not prove, so that no single check is read as proof that every script works:

1. a new chat lists the eleven skills — proves the app discovers the installed skills, not that their scripts run;
2. the check script starts and prints its usage when asked for help — proves that a Python 3.11 or newer answers and that the skill's scripts are found, not that any check passes or that the network is reachable;
3. one literature search reports its source summary — proves that the services named there were reachable and their certificates trusted, and, when the keyed source appears among them, that its key was read; it does not prove that unnamed services are reachable or that results are relevant;
4. the first PDF build of a draft — proves that pandoc and an engine work and names the pipeline that built it; it does not prove anything about the other tiers.

The checklist SHALL name the installer's closing presence lines as a quick view of what is installed and SHALL state that presence is not a working check. Each check that can fail SHALL point to the guide section that resolves its failure. The readiness search SHALL ask for a search only, merging nothing into a proposal. An automated check SHALL fail when the output the checklist quotes — the installer's presence heading and the search's source-summary prefix — no longer matches what the installer and the search print.

#### Scenario: Student who only wants to write
- **WHEN** a student without pandoc, typst or an API key reads what they need
- **THEN** the guide tells them writing needs only the agent app with the skills, and marks PDF export and keys optional

#### Scenario: Student checks a fresh setup
- **WHEN** a student who has just installed the skills works through the checklist
- **THEN** each check names the output to look for, what it proves, what it leaves unproven, and where to go if it fails

#### Scenario: Search reaches no source
- **WHEN** the readiness search reports no contributing source
- **THEN** the checklist points the student to the guide's section on a literature search that cannot reach its sources

#### Scenario: Presence mistaken for readiness
- **WHEN** the installer's presence lines report pandoc and typst as found
- **THEN** the guide still presents the first PDF build, not those lines, as the check that PDF export works

#### Scenario: Quoted output drifts
- **WHEN** the installer's presence heading or the search's source-summary prefix changes without the checklist
- **THEN** the offline suite fails

### Requirement: User-local PDF tools when no package manager works

The install guide SHALL carry a PDF-export section that names the package-manager route first, with commands the package manager accepts as written. For a machine with no package manager, or one that reports an error about its sources, the section SHALL describe a user-local route: the archive for the student's platform from each tool's latest official release, checked against the SHA-256 digest the release page shows beside that asset using the platform's own hash command, and placed in a folder the student owns that is on their PATH.

The section SHALL NOT pin a tool version or link a specific release, SHALL NOT tell the student or their agent to repair, reset or reconfigure a package manager, and SHALL NOT install anything for all users or with administrator rights. A download whose digest does not match SHALL be discarded rather than used. These download steps SHALL live in the install guide only: no skill instruction and no script message SHALL carry download, digest or extraction steps, and a skill MAY link the section.

#### Scenario: Package manager reports a source error
- **WHEN** a student's package manager fails with an error about its sources while installing typst
- **THEN** the guide's PDF-export section gives the release-archive route with its digest check, and nothing in it tells the student to repair the package manager

#### Scenario: Digest does not match
- **WHEN** the hash command's result differs from the digest the release page shows
- **THEN** the guide tells the student to delete the download and not use it

#### Scenario: New tool release
- **WHEN** typst or pandoc publishes a new release
- **THEN** the guide's instructions stay correct without an edit, because they name the latest release and no version

#### Scenario: Skill points at the fallback
- **WHEN** the publish skill or its script reports a missing tool
- **THEN** it links the guide's PDF-export section and carries no download steps of its own
