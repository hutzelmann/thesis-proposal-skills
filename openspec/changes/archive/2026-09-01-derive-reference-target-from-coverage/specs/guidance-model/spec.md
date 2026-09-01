# guidance-model — delta

## MODIFIED Requirements

### Requirement: Reference floor is not a reference target
The guidance SHALL distinguish the mechanically checked minimum number of references from the number a submitted proposal is expected to carry. The minimum SHALL be described as a floor that catches an empty or near-empty bibliography; the prose SHALL state the working range separately, so that meeting the floor is never read as meeting the bar.

The working range SHALL be derived, not asserted: the prose SHALL ground it in coverage the guidance already requires — a thematic cluster in the contribution section needs at least two sources to show a theme rather than an anecdote, each research question's motivation needs grounding, and the introduction grounds its claims in the literature — and SHALL state the expectation as a density relative to the proposal's length, so the target scales with a workspace's page limit instead of assuming the default. The structured guidance data SHALL carry that density as an estimation constant, defaulting to four references per thousand body words, which reproduces the ten-to-fifteen range at the default length.

#### Scenario: Proposal sits at the floor
- **WHEN** a proposal cites exactly the minimum number of references
- **THEN** the mechanical check passes and the guidance still identifies the bibliography as thin

#### Scenario: Range justified by coverage, not quota
- **WHEN** the prose states the working range for references
- **THEN** it derives the range from the coverage rules (cluster grounding, research-question grounding) and a length-scaled density, and does not assert a fixed count as an observed norm

### Requirement: Workspace override file
A user-owned `guidelines.md` in the workspace SHALL override/extend defaults. It consists of a machine-readable fenced TOML block plus freeform prose. Absent file means pure defaults.

Every override key SHALL be the same key path the value occupies in the structured guidance data. There SHALL be exactly one naming rule: no hand-named aliases, and no flat spelling accepted alongside a nested one. The overridable set SHALL cover the reference minimum, the reference-density constant, the required-section list, the forbidden-heading list, the timeline detail mode, the page limit, and the research-question count bounds.

Merge semantics: a user key wins over the default per key; list values replace defaults entirely; a default-forbidden section may be allowed again by omitting it from the replacement list.

The timeline detail mode SHALL accept `simple` (the default) or `detailed`. Under `detailed` the timeline size constraint SHALL NOT apply and the work-plan heading patterns SHALL NOT be forbidden, so a program that mandates a phase table can have one without abandoning the rest of the defaults.

#### Scenario: Supervisor requires a detailed work plan
- **WHEN** `guidelines.md` sets the timeline detail mode to `detailed`
- **THEN** checks accept a timeline section containing a phase or milestone table, and work-plan headings are no longer reported as forbidden

#### Scenario: Raised reference minimum
- **WHEN** `guidelines.md` raises the reference minimum to 8
- **THEN** a proposal with 5 references fails the reference-count check

#### Scenario: Reference density adjusted
- **WHEN** `guidelines.md` sets the reference-density constant to a different value
- **THEN** the density advisory judges the proposal against the workspace value instead of the default

#### Scenario: Research-question bounds overridden
- **WHEN** `guidelines.md` sets the research-question upper bound to 3
- **THEN** a proposal declaring four research questions fails the count check

#### Scenario: Override key mirrors the structure path
- **WHEN** a value is nested in the structured guidance data
- **THEN** the override key for it is nested identically, and no alternative spelling is honoured

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, the reference-density estimation constant, the timeline size constraint, research-question list conventions, the default page limit with its words-per-page estimation constant, and the mechanically matchable thesis-title tells (implementation-opener patterns, a closed buzzword list, and word-count bounds, each in English and German). The mechanically checkable skeleton also covers the document frame: the leading H1 title's position and uniqueness, the emphasized subtitle paragraph with its canonical wordings, the closing references section, the retired metadata keys, and the deterministic language-inference rule. All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy, the five substance tests, the information-density rule, whether the timeline actually names a timeframe, and whether a name in the title denotes a tool at all) SHALL remain prose guidance for agents.

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

#### Scenario: Reference relevance stays prose
- **WHEN** the question is whether the cited works are relevant, peer-reviewed, or well chosen
- **THEN** only the count and the length-scaled density are checked mechanically, and every judgement about the sources themselves stays with the agent
