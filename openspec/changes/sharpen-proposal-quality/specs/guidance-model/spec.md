# guidance-model Delta

## ADDED Requirements

### Requirement: Substance tests
The prose guidance SHALL name five substance tests that every proposal is judged against, each with a memorable name and a one-line operational question:

- **Delta test** — the proposal states precisely what the thesis adds beyond the work it cites; a contribution section that reads as a feature list or restates the field fails.
- **Falsifiability test** — the research questions can come out negative; a question whose every conceivable outcome counts as success fails.
- **Swap test** — the proposal's core statements could not equally describe ten other theses in the area; text that survives swapping the topic noun fails as generic.
- **Method-fit test** — the methodology concretely answers each research question; boilerplate method prose that never touches the questions fails.
- **Executability test** — the proposal gives the student concrete, actionable goals: it names the objects of study (dataset, system, population, corpus), states a concrete evaluation, is feasible in the stated months, and makes clear what the student would actually do first.

The tests SHALL be prose guidance for agents, never encoded as structured check data. Guidance-following skills that judge substance SHALL cite failed tests by these names.

#### Scenario: Generic proposal against the swap test
- **WHEN** a proposal's introduction, contribution, and research questions would remain plausible after replacing its topic with a neighboring one
- **THEN** substance-judging tooling reports a swap-test failure by name

#### Scenario: Unfalsifiable research question
- **WHEN** a research question is phrased so that any outcome demonstrates success
- **THEN** substance-judging tooling reports a falsifiability-test failure by name

#### Scenario: Proposal gives no actionable first step
- **WHEN** a proposal names no object of study and no concrete evaluation, so a student could not say what to do in the first week
- **THEN** substance-judging tooling reports an executability-test failure by name

### Requirement: Information density
The prose guidance SHALL require that every sentence carry information essential to this specific thesis. Scene-setting openers, truisms, restatements of the obvious, and sentences that would fit any proposal in the area SHALL be identified as removable filler. Shortness follows from density: the guidance SHALL frame deletion of low-information sentences as the primary length instrument, not compression of wording.

#### Scenario: Truism opener
- **WHEN** a section opens with a general claim true of any software project ("Software quality is important in modern systems")
- **THEN** guidance-following tooling identifies the sentence as removable filler

#### Scenario: Dense long section accepted
- **WHEN** a section is long but every sentence carries thesis-specific information
- **THEN** no length complaint is raised against it

### Requirement: Default page limit
The default guidance SHALL declare a page limit of five pages for the rendered proposal, deliberately generous, and SHALL treat it as a warning-level bound, never a hard failure. The workspace `page_limit` override SHALL replace the default. Because the source format is markdown, mechanical checks SHALL estimate pages from word count using a documented words-per-page constant and SHALL label the result an estimate.

#### Scenario: Default limit exceeded
- **WHEN** no override exists and the estimated length exceeds five pages
- **THEN** tooling reports a warning naming the estimate and the limit, and the run does not fail

#### Scenario: Workspace tightens the limit
- **WHEN** `guidelines.md` sets `page_limit = 3`
- **THEN** the estimate is judged against three pages

## MODIFIED Requirements

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, the timeline size constraint, research-question list conventions, the default page limit with its words-per-page estimation constant, and the mechanically matchable thesis-title tells (implementation-opener patterns, a closed buzzword list, and word-count bounds, each in English and German). All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy, the five substance tests, the information-density rule, whether the timeline actually names a timeframe, and whether a name in the title denotes a tool at all) SHALL remain prose guidance for agents.

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
