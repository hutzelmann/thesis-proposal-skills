# guidance-model Delta

## MODIFIED Requirements

### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order: "Introduction to the Topic", "Contribution to the State-of-the-Art", "Research Focus and Research Questions", "Methodology for Research: <Methodology>" where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Empirical Model Evaluation, Case Study, and "Timeline". Each methodology has a fixed set of required subsections. Exactly one methodology SHALL be used per proposal. Canonical German section titles SHALL be defined for all of the above.

The document SHALL be anchored by a single leading H1 carrying the thesis title; canonical sections sit at H2 and methodology subsections at H3. The title heading is not a section: it SHALL be exempt from required-section, forbidden-pattern, and methodology matching, so a title whose text collides with a section title or a forbidden pattern produces no section finding.

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

#### Scenario: Title text collides with a forbidden pattern
- **WHEN** the leading H1 title contains a word from the forbidden-heading patterns
- **THEN** no forbidden-section violation is reported, because the title heading is not a section

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, the timeline size constraint, research-question list conventions, the default page limit with its words-per-page estimation constant, and the mechanically matchable thesis-title tells (implementation-opener patterns, a closed buzzword list, and word-count bounds, each in English and German). The mechanically checkable skeleton also covers the document frame: the leading H1 title's position and uniqueness, the emphasized subtitle paragraph with its canonical wordings, the closing references section, the retired metadata keys, and the deterministic language-inference rule. All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy, the five substance tests, the information-density rule, whether the timeline actually names a timeframe, and whether a name in the title denotes a tool at all) SHALL remain prose guidance for agents.

#### Scenario: Semantic rule stays prose
- **WHEN** a rule concerns argument quality rather than document skeleton
- **THEN** it appears only in prose guidance and is never encoded as structured check data

#### Scenario: Timeframe recognition stays prose
- **WHEN** the question is whether a timeline section states a real timeframe, given that students write `SoSe 2027`, `WS 2026/27`, `Q3`, or "winter semester"
- **THEN** no list of accepted date formats is encoded as structured data, and the judgement stays with the agent

#### Scenario: Tool recognition stays prose
- **WHEN** the question is whether a proper noun in the title names a tool, product, or vendor
- **THEN** no list of tool names is encoded as structured data, because the set is unbounded, and the judgement stays with the agent

#### Scenario: Substance tests stay prose
- **WHEN** the question is whether a proposal passes the delta, falsifiability, swap, method-fit, or executability test
- **THEN** no scoring rubric or keyword list for these judgments is encoded as structured data, and the judgement stays with the agent

#### Scenario: Document frame is mechanically checked
- **WHEN** the question is whether the title line is the file's first content line and only H1
- **THEN** the answer comes from deterministic tooling, not agent judgement
