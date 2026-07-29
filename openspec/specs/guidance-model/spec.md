# guidance-model Specification

## Purpose
Defines how proposal-writing guidance is stored, which parts are machine-readable, and how users customize it per workspace without touching installed skills.
## Requirements
### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order: "Introduction to the Topic", "Contribution to the State-of-the-Art", "Research Focus and Research Questions", and "Methodology for Research: <Methodology>" where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study. Each methodology has a fixed set of required subsections. Exactly one methodology SHALL be used per proposal. Canonical German section titles SHALL be defined for all of the above.

#### Scenario: Mixed methodologies
- **WHEN** a proposal combines two methodologies
- **THEN** guidance-following tooling reports a violation of the single-methodology rule

### Requirement: Forbidden content
The default guidance SHALL forbid: work plans/timelines/milestones, supervisor names, expected-results sections, deliverables/code fragments, personal data (matriculation number, address, email, study program), preliminary thesis chapter structures, and confidentiality markers.

#### Scenario: Timeline present
- **WHEN** a proposal contains a schedule heading
- **THEN** tooling reports it as forbidden content under default guidance

### Requirement: Workspace override file
A user-owned `guidelines.md` in the workspace SHALL override/extend defaults. It consists of a machine-readable fenced TOML block (keys include `required_sections`, `forbidden_sections`, `page_limit`, `min_references`) plus freeform prose. Merge semantics: a user key wins over the default per key; list values replace defaults entirely; un-forbidding a default-forbidden section is allowed. Absent file means pure defaults.

#### Scenario: Supervisor requires a timeline
- **WHEN** `guidelines.md` removes the timeline from `forbidden_sections` and adds it to `required_sections`
- **THEN** checks accept (and require) a timeline section for proposals in that workspace

#### Scenario: Raised reference minimum
- **WHEN** `guidelines.md` sets `min_references = 8`
- **THEN** a proposal with 5 references fails the reference-count check

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, and research-question list conventions. All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy) SHALL remain prose guidance for agents.

#### Scenario: Semantic rule stays prose
- **WHEN** a rule concerns argument quality rather than document skeleton
- **THEN** it appears only in prose guidance and is never encoded as structured check data

### Requirement: Structured data and prose must not drift
Every canonical title present in the structured guidance data SHALL appear verbatim in the prose guidance. Automated verification SHALL fail when they diverge.

#### Scenario: Title renamed in prose only
- **WHEN** a section title is changed in prose guidance but not in the structured data
- **THEN** the consistency verification fails

