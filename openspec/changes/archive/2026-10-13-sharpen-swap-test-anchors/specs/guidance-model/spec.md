## MODIFIED Requirements

### Requirement: Substance tests
The prose guidance SHALL name six substance tests that every proposal is judged against, each with a memorable name and a one-line operational question:

- **Delta test** — the proposal states precisely what the thesis adds beyond the work it cites: what it confirms, refutes, or extends. A contribution section that reads as a feature list or restates the field fails; a contribution that confirms or refutes prior findings under new conditions passes, because extending is not the only admissible delta.
- **Falsifiability test** — the research questions can come out negative; a question whose every conceivable outcome counts as success fails.
- **Swap test** — the proposal's core statements could not equally describe ten other theses in the area; text that survives swapping the topic noun fails as generic, and so does a named tool, system, platform or application domain the research does not depend on.
- **Necessity test** — every sentence, citation and technical term in the proposal serves a research question, the delta, or the method. Material that is true, specific and well-sourced still fails if removing it would not weaken the argument. This is the swap test's mirror: the swap test catches text that could belong to any thesis in the area, the necessity test catches text that belongs to a different one.
- **Method-fit test** — the methodology concretely answers each research question; boilerplate method prose that never touches the questions fails.
- **Executability test** — the proposal gives the student concrete, actionable goals: it names the objects of study (dataset, system, population, corpus), states a concrete evaluation, is feasible in the stated months, and makes clear what the student would actually do first. The test asks for a plausible plan, not a finalized protocol: a choice the student can make during the thesis without changing a research question does not fail it.

The tests SHALL be prose guidance for agents, never encoded as structured check data. Guidance-following skills that judge substance SHALL cite failed tests by these names.

The necessity test SHALL NOT be satisfied by a source's quality, its correctness, or the fact that it is cited: a citation is evidence for a claim, and a claim that no research question, delta, or method step needs fails the test together with the sentence carrying it. Where guidance elsewhere bars technical detail irrelevant to the research questions or methodology, that bar SHALL be stated as this test rather than as an independent rule.

The swap test SHALL apply to named choices as well as to prose. Its scope is the thesis's own claims: the title, the purpose statement that closes the introduction, the research focus and research questions, and the contribution section's statements of what the thesis adds (its goals, the gap, the significance and the kind of deliverable). A tool, system, platform or application domain named there SHALL pass only when the research depends on it, in one of these ways:

- it is the object of study, so the expected contribution is a claim about it rather than about the class it belongs to;
- it imposes constraints that shape the method;
- it supplies data or access that no comparable alternative offers;
- it is the case the proposal argues suits its research questions — a typical, critical or revelatory case, selected as the shipped Case Study contract asks — rather than an instance that merely happened to be at hand.

A comparison of named tools passes by design, because the tools are what it studies. The guidance SHALL state the check as a replacement that compares claims, not nouns: when replacing the name with a comparable alternative, or dropping it, leaves the same claim standing — the research questions, the method and the data unchanged apart from the noun, and the expected contribution still claiming its result for the name's class — the name is decorative and the swap test fails. A contribution that claims its result for this instance SHALL pass. The guidance SHALL reconcile the check with degree-level grading: a Bachelor's contribution close that promises to apply or evaluate something in a named setting passes when it claims its result for that setting, and fails only when it claims a result for the class while the setting stays incidental. The guidance SHALL name the two repairs: state the dependence, or generalize the claim to the name's class. Names of prior work, tools chosen to carry out the method, and domains named only to motivate the topic SHALL NOT be judged by this check; whether they belong is the necessity test's question. The check SHALL stay judgement: no mechanical rule SHALL try to tell a decorative name from an anchored one.

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

#### Scenario: Decorative tool in the title and research questions
- **WHEN** a proposal names one agent framework in its title and research questions, its contribution claims a result about agent configurations in general, and any comparable framework would leave the research questions, the method and the expected contribution unchanged
- **THEN** substance-judging tooling reports a swap-test failure by name, locates the name, and states both repairs: state the dependence or generalize the claim

#### Scenario: Named tool as the object of study
- **WHEN** the same proposal's contribution states that the thesis evaluates that framework's own default configuration for the teams that run it
- **THEN** the swap test passes for the name, because a replacement would change the expected contribution

#### Scenario: Comparison of named tools
- **WHEN** the research questions compare three named static analysers on a common corpus
- **THEN** the swap test passes for those names

#### Scenario: Domain that shapes the method
- **WHEN** a thesis restricts its research questions to one application domain whose regulation constrains what the method may record, and the methodology is built around that constraint
- **THEN** the swap test passes for the domain

#### Scenario: Decorative domain
- **WHEN** a code-summarization thesis restricts its research questions to one industry, while its data, method and contribution would read the same for any other industry
- **THEN** substance-judging tooling reports a swap-test failure for the domain by name

#### Scenario: Argued typical case
- **WHEN** a case study names one company and argues, as the Case Study contract asks, why that company is a typical case for its research questions
- **THEN** the swap test passes for the company's name, although a comparable company could in principle have been chosen

#### Scenario: Bachelor's evaluation in a named setting
- **WHEN** a Bachelor's proposal's contribution close promises to evaluate a technique in one named project and claims its result for that project
- **THEN** the swap test passes for the project's name, and the degree-level grading and the swap test agree that the close is complete

#### Scenario: Name outside the thesis's own claims
- **WHEN** a library appears only in the methodology as what the prototype is built with, or a domain appears only in the introduction's motivation
- **THEN** the swap test does not judge that name

### Requirement: Readiness classification
The prose guidance SHALL define proposal readiness as supporting an informed decision to supervise the thesis, and SHALL state that this is distinct from a finalized execution protocol: a ready proposal may leave bounded execution decisions open. The guidance SHALL sort every finding a judging skill reports into exactly one of three classes:

- **Proposal blockers** — failures of a substance test other than the necessity test: no answerable research question, an unclear contribution — literature grounding included, when the cited work is too thin to show what the thesis adds — a named tool, system, platform or application domain the research does not depend on, a method that cannot answer a question, a scope that cannot fit the stated months at the declared level, or an indispensable resource whose availability is doubtful. No other finding SHALL be a blocker. Necessity, density, title and citation-practice findings SHALL NOT block on their own. A name in the title that fails the swap test SHALL be reported as a swap-test blocker, not as a title finding. Non-serving material that obscures what the thesis contributes or asks SHALL be reported as the delta or research-question blocker it causes.
- **Clarify early in the thesis** — decisions that matter for rigorous execution and can be settled by an initial pilot, a supervisor discussion or ordinary student judgement without changing a research question, the contribution or the methodology choice.
- **Optional refinements** — improvements to presentation or execution that are not conditions of acceptance.

A finding SHALL be classified as clarify-early only when its **deferral record** can be filled: what needs deciding, why it matters, when or under what condition it is settled, a reasonable way to resolve it during the thesis that leaves the research questions, the contribution and the methodology choice intact, and whether an adverse outcome would require revisiting the proposal — answered "no", or "yes" with a named fallback under which every research question stays answerable as asked. A fallback that narrows or drops a research question does not fill the record. A finding whose record cannot be filled SHALL be a blocker, and every blocker SHALL carry a sentence naming the failed test and stating why the issue must be resolved before approval rather than during the thesis. That an element is not specified SHALL NOT by itself be such a reason.

The guidance SHALL state the **optional-part test**: an element the proposal declares optional is struck from the plan; when every research question remains answerable without it, its arrangements — capacity, agreements, scheduling — SHALL NOT be blockers; when a research question falls with it, the element is not optional, and that inconsistency is the blocker.

The guidance SHALL keep a **dependency safeguard**: an indispensable permission, ethics approval or data access — one without which a research question cannot be answered — whose availability is doubtful SHALL remain a blocker and SHALL NOT be deferred. Routine organisational detail and arrangements for optional evidence SHALL NOT be treated as such dependencies.

A methodology contract element SHALL be satisfiable by a stated selection rule or candidate set; the instance — an exact model version, a sample size fixed by a pilot, a concrete capture convention — MAY be chosen during the thesis and documented there.

The guidance SHALL state a **stopping rule**: a proposal with no blocker is ready, whatever number of clarify-early items or refinements remain. That more detail could be added SHALL NOT lower a verdict, and no judging skill SHALL require anything beyond the applicable guidelines — the shipped defaults and the workspace `guidelines.md`, whose prose MAY raise an item to a blocker for its program.

The guidance SHALL state that **review rounds are monotone**: a finding about text that is unchanged since an earlier round SHALL NOT move to a higher class than that round gave it, and a blocker that is new in a later round SHALL either concern text the revision introduced or changed, or be labelled as missed in the earlier round with the flaw it exposes stated. A title name that an earlier round reported only as a title refinement, without holding it to the swap test, SHALL count as such a miss when it fails that test: it SHALL return as the swap-test blocker with that label and the dependence it lacks stated, and the title refinement SHALL NOT be repeated beside it.

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

#### Scenario: Decorative name blocks
- **WHEN** a proposal's research questions name a platform that nothing in its method, data or contribution depends on
- **THEN** the finding is a swap-test blocker whose reason says that either repair changes a research question or the contribution, so it cannot wait for the thesis

#### Scenario: Decorative name in the title alone
- **WHEN** a proposal's title names a platform that no research question, goal or contribution statement depends on
- **THEN** the finding is a swap-test blocker that carries the title's certificate consequence, its reason for not waiting is that the title is what the thesis is registered under and what the certificate prints, and the name is not reported as a second, non-blocking finding

#### Scenario: Decorative name missed in an earlier round
- **WHEN** an earlier round left a decorative name in unchanged text unreported
- **THEN** a later round reports it as a blocker only with the label missed in the earlier round and the flaw it exposes stated

#### Scenario: Title name an earlier round reported as a refinement
- **WHEN** an earlier round reported a platform name in the unchanged title only as a title refinement, without holding it to the swap test, and the name fails that test
- **THEN** a later round reports the swap-test blocker labelled missed in the earlier round with the dependence it lacks stated, and does not repeat the earlier title refinement beside it

### Requirement: Title alarm is raised and justified, never silently blocked
Where a title matches an alarm class, guidance SHALL require the agent to raise it explicitly, to state that the title reaches the certificate, and to offer between one and three abstracted alternatives. The agent SHALL NOT silently rewrite the title and SHALL NOT refuse to proceed. A title carrying a named technology SHALL be retained only against the student's stated justification that the technology is the object of study; absent that justification the agent SHALL keep recommending the abstracted alternative. The alarm itself SHALL never block. A named technology in the title that the research does not depend on is also a swap-test failure (requirement: Substance tests). That failure blocks readiness as the swap test's failure, and the agent SHALL raise the name once, as that blocker, with the certificate consequence and the alternatives. A justification stated only in conversation SHALL count for the swap test once the proposal's text carries it.

#### Scenario: Student justifies the named technology
- **WHEN** the student states why the named technology is the object of study
- **THEN** the title is retained, the alarm is not repeated for that reason, and the swap test judges the name by what the proposal's text says about it

#### Scenario: Student gives no justification
- **WHEN** the student neither justifies the name nor accepts an alternative
- **THEN** the agent records the recommendation and proceeds without overwriting the student's title

#### Scenario: Silent rewrite forbidden
- **WHEN** an agent judges a title problematic
- **THEN** it never replaces the title without saying so and never presents the replacement as the student's own choice

#### Scenario: Instrument that passes the swap test
- **WHEN** a title names a platform whose constraints the method is built around, though the platform is not what the thesis studies
- **THEN** the swap test passes, and the title alarm is raised as a non-blocking finding with the certificate consequence and alternatives
