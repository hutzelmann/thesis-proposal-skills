## MODIFIED Requirements

### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order: "Introduction to the Topic", "Contribution to the State-of-the-Art", "Research Focus and Research Questions", "Methodology for Research: <Methodology>" where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, and "Timeline". Each methodology has a fixed set of required subsections. Exactly one methodology SHALL be used per proposal. Canonical German section titles SHALL be defined for all of the above.

The declared order SHALL be enforced, not merely the presence of each section: a proposal whose canonical sections appear in a different order than the guidance declares SHALL be reported as a violation. Under a workspace override that declares its own required-section list, the order of that list SHALL be the enforced order.

#### Scenario: Mixed methodologies
- **WHEN** a proposal combines two methodologies
- **THEN** guidance-following tooling reports a violation of the single-methodology rule

#### Scenario: Canonical sections out of order
- **WHEN** a proposal carries all five canonical sections but places the timeline before the introduction
- **THEN** guidance-following tooling reports an ordering violation

#### Scenario: Override list defines the order
- **WHEN** a workspace declares its own required-section list in a different order than the default
- **THEN** the workspace's order is the one enforced, and the default order is not applied

### Requirement: Forbidden content
The default guidance SHALL forbid: work plans, phase breakdowns and milestone tables, supervisor names, the author's own name, expected-results sections, deliverables/code fragments, personal data (matriculation number, address, email, study program), preliminary thesis chapter structures, and confidentiality markers. A coarse statement of when the thesis starts and when it is submitted is NOT forbidden content — it is the required timeline section. The guidance SHALL state that the writer is identified outside the document — hand-in channel, upload form, filename — so the absence of a name reads as a rule rather than an omission.

#### Scenario: Work plan present
- **WHEN** a proposal contains a work-plan or milestone heading
- **THEN** tooling reports it as forbidden content under default guidance

#### Scenario: Student asks where their name goes
- **WHEN** the guidance is consulted about naming the writer
- **THEN** it states that proposals stay anonymous and identification happens through the hand-in channel, not the document

### Requirement: Workspace override file
A user-owned `guidelines.md` in the workspace SHALL override/extend defaults. It consists of a machine-readable fenced TOML block (keys include `required_sections`, `forbidden_sections`, `page_limit`, `min_references`, `timeline_detail`) plus freeform prose. Merge semantics: a user key wins over the default per key; list values replace defaults entirely; un-forbidding a default-forbidden section is allowed. Absent file means pure defaults.

`timeline_detail` SHALL accept `simple` (the default) or `detailed`. Under `detailed` the timeline size constraint SHALL NOT apply and the work-plan heading patterns SHALL NOT be forbidden, so a program that mandates a phase table can have one without abandoning the rest of the defaults.

#### Scenario: Supervisor requires a detailed work plan
- **WHEN** `guidelines.md` sets `timeline_detail = "detailed"`
- **THEN** checks accept a timeline section containing a phase or milestone table, and work-plan headings are no longer reported as forbidden

#### Scenario: Raised reference minimum
- **WHEN** `guidelines.md` sets `min_references = 8`
- **THEN** a proposal with 5 references fails the reference-count check

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, the timeline size constraint, and research-question list conventions. All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy, and whether the timeline actually names a timeframe) SHALL remain prose guidance for agents.

#### Scenario: Semantic rule stays prose
- **WHEN** a rule concerns argument quality rather than document skeleton
- **THEN** it appears only in prose guidance and is never encoded as structured check data

#### Scenario: Timeframe recognition stays prose
- **WHEN** the question is whether a timeline section states a real timeframe, given that students write `SoSe 2027`, `WS 2026/27`, `Q3`, or "winter semester"
- **THEN** no list of accepted date formats is encoded as structured data, and the judgement stays with the agent

## ADDED Requirements

### Requirement: Coarse timeline section
The default guidance SHALL require a final section, "Timeline" in English and "Zeitplan" in German, holding a short statement of when the thesis starts and when it is submitted, at month granularity, or a statement that the work begins as soon as possible.

The section SHALL stay coarse. Under default guidance its body SHALL contain no table, no list, and no subsection, and SHALL be limited to at most three non-empty lines. Anything richer — a phase breakdown, a milestone table, a Gantt chart, however it is rendered — SHALL be reported as a violation. A statement of a timeframe that the writer never supplied SHALL NOT be invented; an unknown timeframe SHALL be recorded as a visible TODO marker instead.

#### Scenario: Coarse timeline accepted
- **WHEN** the timeline section reads "The thesis starts in October 2026 and is submitted in March 2027."
- **THEN** the section passes

#### Scenario: As soon as possible
- **WHEN** the writer has no registered dates and states that the thesis begins as soon as possible
- **THEN** the section passes

#### Scenario: Gantt table under the timeline heading
- **WHEN** the timeline section body contains a table of phases and months
- **THEN** tooling reports it as a violation under default guidance

#### Scenario: Work packages as subsections
- **WHEN** the timeline section carries subsections, one per work package
- **THEN** tooling reports it as a violation under default guidance

#### Scenario: Gantt chart supplied as an image
- **WHEN** the timeline section embeds a Gantt chart as a figure rather than as markup
- **THEN** the agent pass reports it as a violation, since no mechanical check can inspect the image

#### Scenario: Timeframe unknown
- **WHEN** the writer's start and submission months are not known
- **THEN** the section carries a visible TODO marker and no timeframe is asserted
