## MODIFIED Requirements

### Requirement: Substance tests
The prose guidance SHALL name six substance tests that every proposal is judged against, each with a memorable name and a one-line operational question:

- **Delta test** — the proposal states precisely what the thesis adds beyond the work it cites: what it confirms, refutes, or extends. A contribution section that reads as a feature list or restates the field fails; a contribution that confirms or refutes prior findings under new conditions passes, because extending is not the only admissible delta.
- **Falsifiability test** — the research questions can come out negative; a question whose every conceivable outcome counts as success fails.
- **Swap test** — the proposal's core statements could not equally describe ten other theses in the area; text that survives swapping the topic noun fails as generic.
- **Necessity test** — every sentence, citation and technical term in the proposal serves a research question, the delta, or the method. Material that is true, specific and well-sourced still fails if removing it would not weaken the argument. This is the swap test's mirror: the swap test catches text that could belong to any thesis in the area, the necessity test catches text that belongs to a different one.
- **Method-fit test** — the methodology concretely answers each research question; boilerplate method prose that never touches the questions fails.
- **Executability test** — the proposal gives the student concrete, actionable goals: it names the objects of study (dataset, system, population, corpus), states a concrete evaluation, is feasible in the stated months, and makes clear what the student would actually do first.

The tests SHALL be prose guidance for agents, never encoded as structured check data. Guidance-following skills that judge substance SHALL cite failed tests by these names.

The necessity test SHALL NOT be satisfied by a source's quality, its correctness, or the fact that it is cited: a citation is evidence for a claim, and a claim that no research question, delta, or method step needs fails the test together with the sentence carrying it. Where guidance elsewhere bars technical detail irrelevant to the research questions or methodology, that bar SHALL be stated as this test rather than as an independent rule.

#### Scenario: Generic proposal against the swap test
- **WHEN** a proposal's introduction, contribution, and research questions would remain plausible after replacing its topic with a neighboring one
- **THEN** substance-judging tooling reports a swap-test failure by name

#### Scenario: Unfalsifiable research question
- **WHEN** a research question is phrased so that any outcome demonstrates success
- **THEN** substance-judging tooling reports a falsifiability-test failure by name

#### Scenario: Sourced sentence serving no research question
- **WHEN** a proposal carries a specific, correct, peer-reviewed-cited sentence about a neighboring technology that no research question, delta statement, or method step depends on
- **THEN** substance-judging tooling reports a necessity-test failure by name and identifies the sentence as removable, rather than crediting it as literature grounding

#### Scenario: Specific sentence that survives both mirrors
- **WHEN** a sentence is specific enough to fail no swap test and is depended on by a stated research question
- **THEN** neither the swap test nor the necessity test reports it

#### Scenario: Proposal gives no actionable first step
- **WHEN** a proposal names no object of study and no concrete evaluation, so a student could not say what to do in the first week
- **THEN** substance-judging tooling reports an executability-test failure by name

#### Scenario: Replication-flavored delta
- **WHEN** a proposal's contribution is to test whether a published finding holds in a different context, without extending the technique itself
- **THEN** the delta test accepts it as a confirm-or-refute delta rather than failing it for adding nothing new

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, the reference-density estimation constant, the timeline size constraint, research-question list conventions, the default page limit with its words-per-page estimation constant, and the mechanically matchable thesis-title tells (implementation-opener patterns, a closed buzzword list, and word-count bounds, each in English and German). The mechanically checkable skeleton also covers the document frame: the leading H1 title's position and uniqueness, the emphasized subtitle paragraph with its canonical wordings, the closing references section, the retired metadata keys, and the deterministic language-inference rule. All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy, the six substance tests, the information-density rule, whether the timeline actually names a timeframe, and whether a name in the title denotes a tool at all) SHALL remain prose guidance for agents.

Whether a sentence, a citation, or a technical term serves a research question is a semantic rule of exactly this kind. Mechanical checks MAY report that a reference is defined and never cited; they SHALL NOT judge whether the proposal needs it.

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
- **WHEN** the question is whether a proposal passes the delta, falsifiability, swap, necessity, method-fit, or executability test
- **THEN** no scoring rubric or keyword list for these judgments is encoded as structured data, and the judgement stays with the agent

#### Scenario: Document frame is mechanically checked
- **WHEN** the question is whether the title line is the file's first content line and only H1
- **THEN** the answer comes from deterministic tooling, not agent judgement

#### Scenario: Reference relevance stays prose
- **WHEN** the question is whether the cited works are relevant, peer-reviewed, or well chosen
- **THEN** only the count and the length-scaled density are checked mechanically, and every judgement about the sources themselves stays with the agent

#### Scenario: An uncited reference is reported, not judged
- **WHEN** a reference is defined in the metadata block and never cited in the body
- **THEN** the mechanical check reports it as uncited and states both admissible resolutions, and whether the proposal needs the entry stays with the agent
