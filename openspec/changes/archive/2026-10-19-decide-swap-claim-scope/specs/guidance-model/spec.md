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

A comparison of named tools passes by design, because the tools are what it studies. The guidance SHALL state the check as a replacement that compares claims, not nouns: when replacing the name with a comparable alternative, or dropping it, leaves the same claim standing — the research questions, the method and the data unchanged apart from the noun, and the expected contribution still claiming its result for the name's class — the name is decorative and the swap test fails. A contribution that claims its result for this instance SHALL pass unless its claim scope is undecided. The guidance SHALL reconcile the check with degree-level grading: a Bachelor's contribution close that promises to apply or evaluate something in a named setting passes when the thesis's own claims, the gap and the close among them, are all scoped to that setting. The guidance SHALL name the two repairs: state the dependence, or generalize the claim to the name's class. Names of prior work, and tools and domains named only in the method or only to motivate the topic, SHALL NOT be judged by this check; whether they belong is the necessity test's question. The check SHALL stay judgement: no mechanical rule SHALL try to tell a decorative name from an anchored one.

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
- **WHEN** a Bachelor's proposal's contribution close promises to evaluate a technique in one named project and claims its result for that project, and its gap and research questions are scoped to that project too
- **THEN** the swap test passes for the project's name, and the degree-level grading and the swap test agree that the close is complete

#### Scenario: Bachelor's close beside class-scoped claims
- **WHEN** a Bachelor's proposal names a platform in its title, purpose, research focus and one research question, its contribution section opens by claiming the gap for the general problem class, its close is scoped to the platform, and the proposal states nothing about why the result is about the platform
- **THEN** substance-judging tooling reports a swap-test failure for the platform by name, on the claim scope the proposal leaves undecided, rather than passing it under the degree-level clause

#### Scenario: Platform a prototype runs on, named in the title
- **WHEN** a title and a research question name the platform a prototype is built on, and the research questions, requirements and measures would read the same on any comparable platform
- **THEN** the swap test judges the name, because it stands in the thesis's own claims and not only in the method, and reports it as decorative

#### Scenario: Name outside the thesis's own claims
- **WHEN** a library appears only in the methodology as what the prototype is built with, or a domain appears only in the introduction's motivation
- **THEN** the swap test does not judge that name

## ADDED Requirements

### Requirement: Named-choice dependence rests on the proposal's text
A dependence SHALL count toward a swap-test pass only where the proposal's text states it. For the object of study, the listed claims state it when they put the gap and the result on the name; another anchor needs a sentence saying what the name constrains, supplies or represents, and being at hand is none. A reason given only in conversation or the student's messages, an unstated setting fact, an earlier round's remark and an argument the judge supplies SHALL NOT count.

#### Scenario: Host organisation runs the platform
- **WHEN** a proposal says the student's host organisation runs the named platform, and nowhere says what the research needs from that platform that a comparable one could not supply
- **THEN** no data-or-access anchor passes the name, and the swap test judges it by the replacement

#### Scenario: Access the judge infers
- **WHEN** a judging agent reasons that the host organisation's setup gives the student access no alternative offers, and the proposal does not state that
- **THEN** the argument passes nothing, and the judge may put it to the student as the dependence the proposal could state

#### Scenario: Use is not dependence
- **WHEN** the only sentences naming the platform outside the title, purpose and focus say that the evaluation runs in its test environment and compares against its native logs
- **THEN** no anchor passes the name on those sentences, because they state use, not what the research needs from that platform

#### Scenario: Earlier review's remark
- **WHEN** an earlier round's review called the platform the object of study or credited the student's access to it, and the current text states no such dependence
- **THEN** the remark is not evidence for a pass, and the name is judged on the current text

#### Scenario: Reason recorded only in the student's messages
- **WHEN** the student's messages, as recorded in the workspace, say that the team runs the framework and has access to it, and the proposal says neither
- **THEN** the recorded reason passes nothing until the proposal carries it

#### Scenario: Object of study by its scope
- **WHEN** every claim the swap test covers, the gap included, is scoped to the named framework, and no sentence argues why the research needs it
- **THEN** that scope states the dependence, and the name passes as the object of study

#### Scenario: Behaviour the instance's users rely on
- **WHEN** a proposal states that the framework ships a default configuration the teams that adopt it keep unless evidence tells them otherwise
- **THEN** that is something about the framework itself that makes its own result the question, and it counts, while the student's own team running the framework does not

#### Scenario: Reason written into the proposal
- **WHEN** the student explains in conversation why the platform matters and the revised proposal states that reason in its contribution
- **THEN** the stated reason counts as the dependence it describes

### Requirement: Claim scope decided before a name passes
Before the replacement, the guidance SHALL have the judge list the thesis's own claims the swap test covers, whether or not they name it, each with its scope: the named instance or setting, or its class. Where some claim the gap or the result for the class and others for the instance, the instance SHALL be the claim's object only when the proposal states why the result is about it; without that or another anchor the proposal states, the claim scope is undecided and the swap test fails.

#### Scenario: Class-scoped sentence that does not carry the name
- **WHEN** the contribution section's opening claims the gap for the general problem class without naming the platform, and the close names the platform
- **THEN** the list holds both sentences with their scopes, so the opening is not left out because the name is absent from it

#### Scenario: Gap attributed to cited work
- **WHEN** the contribution section states a limitation that the cited studies share, for the general class, before a close scoped to the named framework
- **THEN** the limitation is listed as a class-scoped gap, while sentences reporting what particular cited studies did are not listed

#### Scenario: Motivation and reports of cited work are not listed
- **WHEN** the introduction motivates the topic with a class-level problem before its closing purpose, and the contribution reports what particular cited studies did, while every gap, the significance and the close are scoped to the named framework
- **THEN** neither the motivation nor the report is on the list, the scope is decided, and the name passes as the object of study

#### Scenario: Undecided scope
- **WHEN** the listed claims put the gap on the class and the result on the platform, and the proposal states no reason why the result is about the platform and no other anchor
- **THEN** the swap test fails for the platform, and the finding quotes a class-scoped and an instance-scoped claim and names the repairs that decide the scope: scope every gap to the instance, state why the result is about the instance, or generalize the claim to the class

#### Scenario: Being run by the student's team is no reason
- **WHEN** the mixed-scope proposal says that the student's team runs the framework, and nothing more about why the result is about it
- **THEN** the scope stays undecided and the swap test fails

#### Scenario: Class gap with an argued instance close
- **WHEN** the contribution claims the gap for the class and closes by evaluating the named framework itself, stating that the framework ships the default configuration the teams that adopt it run
- **THEN** the instance is the claim's object and the swap test passes for the framework

#### Scenario: Mixed scope with a stated constraint
- **WHEN** the title and research questions name a domain whose regulation the method is built around, as the proposal states, and the gap and the result are claimed for the class
- **THEN** the domain passes on the constraint anchor, and no undecided-scope finding is raised

#### Scenario: Every claim scoped to the setting
- **WHEN** every listed claim, the gap included, is scoped to the named setting
- **THEN** the scope is decided and the name passes as the object of study, at either degree level

#### Scenario: One finding per name
- **WHEN** a name fails the replacement and leaves the scope undecided
- **THEN** the judge reports one swap-test finding for it, with every repair that applies

#### Scenario: Listing stays judgement
- **WHEN** a skill applies the claim list
- **THEN** the list is the judge's reading of the text, and no script, pattern rule or structured data decides a claim's scope
