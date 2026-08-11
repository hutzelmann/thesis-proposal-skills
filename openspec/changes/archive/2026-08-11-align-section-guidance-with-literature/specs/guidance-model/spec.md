## ADDED Requirements

### Requirement: Early purpose statement
The guidance SHALL require the introduction to close with an explicit statement of what the thesis tries to achieve — one or two sentences, at the level of ideas rather than technique. The existing rule that the introduction refers to the thesis itself only at its end SHALL be kept and sharpened: that closing reference is not optional color but the purpose statement the rest of the proposal unfolds.

#### Scenario: Introduction never states a purpose
- **WHEN** an introduction motivates a topic and ends without saying what this thesis tries to achieve
- **THEN** guidance-following tooling identifies the missing purpose statement at the section's close, rather than treating the section as complete because the topic was motivated

#### Scenario: Purpose stated mid-proposal only
- **WHEN** the first statement of what the work tries to achieve appears in the methodology section
- **THEN** the guidance directs it to the introduction's close, where a reader learns it before the prior-work discussion begins

### Requirement: Significance and result type at the contribution's close
The guidance SHALL require the contribution section's closing gap statement to carry two things beyond the gap itself: why answering the research questions matters once they are answered — significance is a distinct statement from the delta, which only names what is missing — and what kind of thing the thesis will deliver (a technique, a model, a tool or prototype, an evaluation of a specific instance, or a report of findings). Naming the kind is not an expected-results section: it types the deliverable without asserting its content.

#### Scenario: Gap named, significance absent
- **WHEN** a contribution section names the gap the thesis fills but never says why filling it matters to anyone
- **THEN** guidance-following tooling asks for the significance statement, distinct from the delta

#### Scenario: Result type never named
- **WHEN** a proposal's contribution section leaves open whether the thesis delivers a tool, a model, or an evaluation
- **THEN** the guidance asks the writer to name the kind of deliverable

#### Scenario: Result type is not an expected result
- **WHEN** a proposal states that the thesis will deliver a benchmark comparison of two approaches
- **THEN** naming that kind is compliant, while asserting which approach will win remains forbidden expected-results content

### Requirement: Deliberate stance on omitted conventions
The guidance SHALL state, in one place, that omitting work plans, expected-results sections, and the author's name is a deliberate stance of this guidance and not an oversight, because many university templates require exactly those elements and a student will encounter such templates. The statement SHALL point at the workspace override mechanism as the way a program's contrary requirements are honored.

#### Scenario: Student finds a contradicting template
- **WHEN** a student asks why this guidance forbids the milestone plan their faculty's template requires
- **THEN** the guidance names the divergence as deliberate and points at the workspace override as the mechanism for following the faculty's rule

## MODIFIED Requirements

### Requirement: Construction goals have a home
The guidance SHALL state where an implementation or construction goal belongs, not only that it is not a research question. A goal describes what the work will do; a research question asks what the work will find out. A goal phrased as "how can X be built" SHALL be directed to the contribution section, where the work describes itself, rather than merely rejected.

The guidance SHALL recommend stating a construction goal in a structured form that names the problem context, the artifact to be built, the requirements it must satisfy, and the stakeholder goal it serves, so that the goal carries its own so-what and its requirements are checkable. For a proposal whose contribution is an artifact, the guidance SHALL require the research questions to interrogate the stated goal — asking what effects the artifact has against its requirements, how it compares to alternatives, or under which conditions it holds — rather than standing unrelated beside it.

The guidance SHALL also carry the reviewer-facing nuance: a question of the form "how can X be done" is legitimate research when its answer is a method that generalizes beyond one instance. The test is whether the answer generalizes, not the interrogative surface; a student's one-off build target fails it, which is why the student-facing rule stands unchanged.

#### Scenario: Student writes a construction goal as a research question
- **WHEN** the guidance is consulted about "How can a dashboard for X be built?" appearing in the research-question list
- **THEN** it names the section that statement belongs in, rather than only reporting that it is not analytical

#### Scenario: Goal stated without structure
- **WHEN** a contribution section says only that a prototype will be developed
- **THEN** the guidance asks for the structured form: the context it improves, the requirements it must satisfy, and the stakeholder goal it serves

#### Scenario: Research questions unrelated to the stated goal
- **WHEN** a proposal states an artifact goal in the contribution section and lists research questions that never touch that artifact or its requirements
- **THEN** guidance-following tooling reports the missing derivation link between goal and questions

#### Scenario: Generalizing method question
- **WHEN** a reviewer judges "How can regression test selection be done under flaky tests?" where the intended answer is a technique applicable beyond one system
- **THEN** the guidance recognizes it as a legitimate research question rather than mechanically rejecting the phrasing

### Requirement: Substance tests
The prose guidance SHALL name five substance tests that every proposal is judged against, each with a memorable name and a one-line operational question:

- **Delta test** — the proposal states precisely what the thesis adds beyond the work it cites: what it confirms, refutes, or extends. A contribution section that reads as a feature list or restates the field fails; a contribution that confirms or refutes prior findings under new conditions passes, because extending is not the only admissible delta.
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

#### Scenario: Replication-flavored delta
- **WHEN** a proposal's contribution is to test whether a published finding holds in a different context, without extending the technique itself
- **THEN** the delta test accepts it as a confirm-or-refute delta rather than failing it for adding nothing new
