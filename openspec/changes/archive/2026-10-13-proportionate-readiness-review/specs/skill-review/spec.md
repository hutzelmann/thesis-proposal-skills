## ADDED Requirements

### Requirement: Review rounds converge
Before overwriting an existing `<slug>-review.md`, the skill SHALL read it and carry its findings into the new review under an earlier-round section (German: `## Frühere Runde`): each earlier blocker marked resolved, partly resolved, or open, where resolved is judged against what that blocker asked for, not against a bar raised since. Classification across rounds SHALL be monotone as the guidance defines it: a finding about a passage the revision left unchanged SHALL keep its earlier class or move to a lower one, so an earlier clarify-early item or refinement about unchanged text SHALL NOT become a blocker. A blocker new in this round SHALL either concern text the revision introduced or changed, or be labelled as missed in the earlier round with the flaw it exposes stated; the chat summary SHALL count such missed-earlier blockers. Newly noticed execution details SHALL enter the clarify-early section. A partly resolved blocker whose residue passes the deferral record SHALL move to the clarify-early section. Without an earlier review the skill SHALL write no earlier-round section.

#### Scenario: Earlier blockers resolved
- **WHEN** an earlier review listed two blockers and the revised proposal addresses what each asked for
- **THEN** the new review marks both resolved in its earlier-round section and, with no new blocker, opens with the ready verdict

#### Scenario: Earlier deferred item stays deferred
- **WHEN** an earlier review listed the model-version choice as a clarify-early item and the revision left that passage unchanged
- **THEN** the new review does not list it as a blocker

#### Scenario: Missed flaw labelled
- **WHEN** a later round finds that a research question unchanged since the earlier round cannot come out negative
- **THEN** the review may report it as a blocker labelled missed in the earlier round, stating the flaw, and the chat summary counts it

#### Scenario: First review
- **WHEN** no earlier review file exists beside the proposal
- **THEN** the review carries no earlier-round section

## MODIFIED Requirements

### Requirement: Content-level review scope
The skill SHALL review argument structure, soundness, missing literature or information, sharpness/focus, unnecessary content, redundancy, and inconsistencies — including the semantic guidance rules (analytical research questions, explicit contribution delta, single methodology). The review SHALL judge the proposal against the six substance tests named in the guidance, including concreteness and executability: whether the proposal names its objects of study, states a concrete evaluation, and gives the student actionable goals feasible in the stated months. Missing information SHALL be judged by what the substance tests and the applicable guidelines need, never by what a supervisor might eventually ask: a plausible approach the student can settle during the thesis is not missing information. The review SHALL apply the information-density rule at sentence level: sentences that carry no information essential to this thesis SHALL be named concretely as removable, quoting or locating each, not merely described as a general verbosity concern.

Unnecessary content SHALL be judged by the necessity test rather than by tone: a passage fails it when no research question, delta statement, or method step depends on it, and being correct, specific, or carried by a citation SHALL NOT exempt it. The review SHALL locate such a passage as removable in the same way it locates filler.

#### Scenario: Implementation-goal research questions
- **WHEN** research questions are phrased as "how can X be implemented"
- **THEN** the review flags them and suggests analytical reformulations

#### Scenario: Filler sentences named
- **WHEN** a proposal carries scene-setting sentences that would fit any thesis in the area
- **THEN** the review names those sentences and marks them as removable filler, rather than issuing a general brevity remark

#### Scenario: Sourced passage about a neighbouring field
- **WHEN** a proposal carries a specific, correctly cited passage that no research question, delta statement, or method step depends on
- **THEN** the review names it as a necessity-test failure and locates it as removable, rather than counting its citation as literature grounding

#### Scenario: Methodology not executable
- **WHEN** the methodology promises an evaluation but names no dataset, benchmark, system, or population
- **THEN** the review flags the executability gap and asks for the missing concrete object

#### Scenario: Selection rule instead of an instance
- **WHEN** the methodology states how the compared models will be chosen but names no exact model version
- **THEN** the review does not report the missing version as missing information that blocks the verdict

### Requirement: Three-tier substance verdict
The review SHALL open with an explicit verdict, one of exactly three tiers, derived from the guidance's readiness classification: **ready** exactly when no proposal blocker stands — counting earlier-round blockers still open — whatever clarify-early items or refinements remain; **needs revision** when at least one blocker stands and every blocker is repairable in place; **no viable thesis core** when substance tests fail in a way no in-place edit can repair. The ready verdict SHALL state that the proposal supports a decision to supervise and that the clarify-early items are settled during the thesis, not before approval — it is not a finalized execution protocol. That more detail could be added SHALL NOT lower the verdict. The verdict SHALL be judged against the six substance tests named in the guidance — delta, falsifiability, swap, necessity, method-fit, executability — and where a blocking test fails, the verdict statement SHALL cite the failed tests by name. The verdict SHALL appear at the top of the review file and in the chat summary. The skill SHALL NOT soften a no-viable-core verdict into needs-revision phrasing: when the substance is hollow, the review says so plainly and states what kind of work (re-ideation, a genuine delta, a concrete evaluation object) would change the verdict. The verdict is advisory like the rest of the review: it blocks nothing.

A necessity-test failure SHALL NOT by itself lower the verdict: material that serves no research question is removable in place, so it is an optional refinement unless it obscures what the thesis contributes or asks, in which case the review reports the delta or research-question blocker it causes.

#### Scenario: Hollow but structurally clean proposal
- **WHEN** a proposal passes every mechanical check but its text would describe any thesis in the area, states no delta beyond the cited work, and names no object of study
- **THEN** the review's verdict is "no viable thesis core", citing at least the swap, delta, and executability tests, and states what would change the verdict

#### Scenario: Sound proposal with fixable findings
- **WHEN** the substance tests pass except for one repairable blocker (an overlapping RQ pair, an evaluation that names no measure)
- **THEN** the verdict is "needs revision" and the blocker carries its reason for being settled before approval

#### Scenario: Ready with open execution decisions
- **WHEN** no blocker stands and the review lists clarify-early items such as the exact model versions and the audit sample size
- **THEN** the verdict is "ready", stating that those items are settled during the thesis

#### Scenario: Otherwise sound proposal carrying non-serving material
- **WHEN** the only failing test is necessity — a sourced, specific passage that no research question, delta statement, or method step depends on, and that does not obscure the contribution
- **THEN** the verdict is "ready", and the finding is an optional refinement naming the necessity test and locating the passage as removable

#### Scenario: Verdict reaches the chat summary
- **WHEN** the review file is written
- **THEN** the chat summary opens with the same verdict tier the file carries

### Requirement: Title assessed as its own dimension
The review SHALL assess the proposal's thesis title as a dimension of its own, against the guidance: whether it names a contribution and its object, whether it carries a tool, product, or vendor name as the instrument, whether it frames implementation work rather than research, whether it names a field rather than a thesis, and whether it carries marketing tone. Where the review flags the title it SHALL say that the title is printed on the study certificate and SHALL suggest between one and three abstracted alternatives, as an enumerated item among the optional refinements. A title whose named technology is the object of the proposal's own research questions SHALL NOT be flagged.

#### Scenario: Tool-named title reviewed
- **WHEN** the proposal's title names the framework used to build its prototype
- **THEN** the review carries an enumerated title item naming the certificate consequence and suggesting abstracted alternatives

#### Scenario: Title drifted from the research questions
- **WHEN** the title promises something the research questions do not address
- **THEN** the review flags the mismatch as a title finding

#### Scenario: Named technology is the research object
- **WHEN** the research questions are about the named technology itself
- **THEN** the review does not flag the title for naming it

### Requirement: Persisted, actionable output
The review SHALL be written to `<slug>-review.md` next to the proposal (overwritten per run, after the earlier round has been carried over), in the proposal's declared language. After the verdict it SHALL carry the earlier-round section when an earlier review existed, then three sections in this order — proposal blockers, clarify early in the thesis, optional refinements (German: `## Vor der Annahme zu klären`, `## Früh in der Arbeit zu klären`, `## Optionale Verbesserungen`) — each an enumerated list ordered by severity, an empty one stating that it has no items. Every finding SHALL carry what is wrong, where, and an actionable suggestion. Every blocker SHALL name its failed test and state why it must be resolved before approval rather than during the thesis. Every clarify-early item SHALL carry its deferral record: what needs deciding, why it matters, when or under what condition it is settled, a reasonable way to resolve it, and whether an adverse outcome would require revisiting the proposal. The clarify-early section is the early-thesis clarification agenda: on a ready verdict the chat summary SHALL name it as the agenda for the thesis's first weeks; it stays outside the proposal, and the review SHALL NOT ask for a new proposal section or a work plan to carry it. Where a finding concerns an exceeded limit or forbidden content, the suggestion SHALL state what suffices and where the surplus content goes — never only that the content does not belong.

#### Scenario: German proposal reviewed
- **WHEN** the proposal declares `lang: de`
- **THEN** the review file is written in German, with the German section titles

#### Scenario: Work plan in the timeline section
- **WHEN** the proposal's timeline section carries a phase breakdown or Gantt-style work plan
- **THEN** the finding's suggestion states that one sentence naming start and submission month suffices and that the phase detail belongs in the writer's own working notes, rather than only declaring the plan forbidden

#### Scenario: Deferred item carries its record
- **WHEN** the review defers the choice of an audit sample size to a pilot
- **THEN** the clarify-early item states what is decided, why it matters, that it is settled after the pilot, a reasonable resolution, and that an adverse outcome does not reopen the proposal

#### Scenario: Agenda offered on a ready verdict
- **WHEN** the verdict is ready and the clarify-early section has items
- **THEN** the chat summary names that section as the agenda for the first weeks of the thesis, and no change to the proposal is asked for to carry it
