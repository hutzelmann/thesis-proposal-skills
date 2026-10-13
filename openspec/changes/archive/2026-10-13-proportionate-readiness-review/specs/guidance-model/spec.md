## ADDED Requirements

### Requirement: Readiness classification
The prose guidance SHALL define proposal readiness as supporting an informed decision to supervise the thesis, and SHALL state that this is distinct from a finalized execution protocol: a ready proposal may leave bounded execution decisions open. The guidance SHALL sort every finding a judging skill reports into exactly one of three classes:

- **Proposal blockers** — failures of a substance test other than the necessity test: no answerable research question, an unclear contribution — literature grounding included, when the cited work is too thin to show what the thesis adds — a method that cannot answer a question, a scope that cannot fit the stated months at the declared level, or an indispensable resource whose availability is doubtful. No other finding SHALL be a blocker. Necessity, density, title and citation-practice findings SHALL NOT block on their own; non-serving material that obscures what the thesis contributes or asks SHALL be reported as the delta or research-question blocker it causes.
- **Clarify early in the thesis** — decisions that matter for rigorous execution and can be settled by an initial pilot, a supervisor discussion or ordinary student judgement without changing a research question, the contribution or the methodology choice.
- **Optional refinements** — improvements to presentation or execution that are not conditions of acceptance.

A finding SHALL be classified as clarify-early only when its **deferral record** can be filled: what needs deciding, why it matters, when or under what condition it is settled, a reasonable way to resolve it during the thesis that leaves the research questions, the contribution and the methodology choice intact, and whether an adverse outcome would require revisiting the proposal — answered "no", or "yes" with a named fallback under which every research question stays answerable as asked. A fallback that narrows or drops a research question does not fill the record. A finding whose record cannot be filled SHALL be a blocker, and every blocker SHALL carry a sentence naming the failed test and stating why the issue must be resolved before approval rather than during the thesis. That an element is not specified SHALL NOT by itself be such a reason.

The guidance SHALL state the **optional-part test**: an element the proposal declares optional is struck from the plan; when every research question remains answerable without it, its arrangements — capacity, agreements, scheduling — SHALL NOT be blockers; when a research question falls with it, the element is not optional, and that inconsistency is the blocker.

The guidance SHALL keep a **dependency safeguard**: an indispensable permission, ethics approval or data access — one without which a research question cannot be answered — whose availability is doubtful SHALL remain a blocker and SHALL NOT be deferred. Routine organisational detail and arrangements for optional evidence SHALL NOT be treated as such dependencies.

A methodology contract element SHALL be satisfiable by a stated selection rule or candidate set; the instance — an exact model version, a sample size fixed by a pilot, a concrete capture convention — MAY be chosen during the thesis and documented there.

The guidance SHALL state a **stopping rule**: a proposal with no blocker is ready, whatever number of clarify-early items or refinements remain. That more detail could be added SHALL NOT lower a verdict, and no judging skill SHALL require anything beyond the applicable guidelines — the shipped defaults and the workspace `guidelines.md`, whose prose MAY raise an item to a blocker for its program.

The guidance SHALL state that **review rounds are monotone**: a finding about text that is unchanged since an earlier round SHALL NOT move to a higher class than that round gave it, and a blocker that is new in a later round SHALL either concern text the revision introduced or changed, or be labelled as missed in the earlier round with the flaw it exposes stated.

#### Scenario: Unspecified model versions
- **WHEN** a proposal comparing agent configurations states that the models are chosen at the start of the thesis by a stated rule and documented with their identifiers, and names none
- **THEN** the missing identifiers are a clarify-early item with a filled deferral record, not a blocker

#### Scenario: Optional expert feedback
- **WHEN** a proposal declares expert ratings optional and every research question is answered from data the student produces without them
- **THEN** reviewer capacity and company agreements for the ratings are not blockers

#### Scenario: Optional in name only
- **WHEN** a proposal calls an expert assessment optional but one research question can only be answered from that assessment
- **THEN** the inconsistency is a blocker under the method-fit or executability test

#### Scenario: Indispensable access in doubt
- **WHEN** the only data source for a research question is a partner company's internal records and access is still to be negotiated
- **THEN** the doubtful access is a blocker under the executability test, with a sentence saying why it must be settled before approval

#### Scenario: Blocker without a reason
- **WHEN** a judging skill would report "the audit sample size is not specified" as a blocker
- **THEN** the guidance rules it out: either the reviewer states why the question cannot be settled during the thesis, or the finding is a clarify-early item with its deferral record

#### Scenario: Ready with open decisions
- **WHEN** every substance test except possibly necessity passes and three clarify-early items remain
- **THEN** the proposal is ready

#### Scenario: Workspace raises the bar
- **WHEN** a workspace `guidelines.md` states that the ethics approval must be granted before a proposal is accepted
- **THEN** a missing approval is a blocker for proposals in that workspace

#### Scenario: Unchanged text does not climb
- **WHEN** an earlier round classified a passage's open decision as clarify-early and the revision left that passage unchanged
- **THEN** a later round does not report it as a blocker

## MODIFIED Requirements

### Requirement: Substance tests
The prose guidance SHALL name six substance tests that every proposal is judged against, each with a memorable name and a one-line operational question:

- **Delta test** — the proposal states precisely what the thesis adds beyond the work it cites: what it confirms, refutes, or extends. A contribution section that reads as a feature list or restates the field fails; a contribution that confirms or refutes prior findings under new conditions passes, because extending is not the only admissible delta.
- **Falsifiability test** — the research questions can come out negative; a question whose every conceivable outcome counts as success fails.
- **Swap test** — the proposal's core statements could not equally describe ten other theses in the area; text that survives swapping the topic noun fails as generic.
- **Necessity test** — every sentence, citation and technical term in the proposal serves a research question, the delta, or the method. Material that is true, specific and well-sourced still fails if removing it would not weaken the argument. This is the swap test's mirror: the swap test catches text that could belong to any thesis in the area, the necessity test catches text that belongs to a different one.
- **Method-fit test** — the methodology concretely answers each research question; boilerplate method prose that never touches the questions fails.
- **Executability test** — the proposal gives the student concrete, actionable goals: it names the objects of study (dataset, system, population, corpus), states a concrete evaluation, is feasible in the stated months, and makes clear what the student would actually do first. The test asks for a plausible plan, not a finalized protocol: a choice the student can make during the thesis without changing a research question does not fail it.

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

#### Scenario: Selection rule passes executability
- **WHEN** a proposal names the benchmark and the metrics and states that the compared models are chosen at the thesis start by a stated rule
- **THEN** the executability test passes, and the model choice is not reported as an executability failure
