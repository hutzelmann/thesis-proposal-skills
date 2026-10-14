# skill-review Specification

## Purpose
High-level content review of a proposal — arguments, literature grounding, sharpness — producing an enumerated, actionable review file.

## Requirements

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
The review SHALL assess the proposal's thesis title as a dimension of its own, against the guidance: whether it names a contribution and its object, whether it carries a tool, product, or vendor name as the instrument, whether it frames implementation work rather than research, whether it names a field rather than a thesis, and whether it carries marketing tone. Where the review flags the title it SHALL say that the title is printed on the study certificate and SHALL suggest between one and three abstracted alternatives, as an enumerated item among the optional refinements. Where a name the title carries fails the swap test, that finding SHALL be the swap-test blocker instead, carrying the certificate consequence and the alternatives. The name SHALL NOT be reported a second time among the refinements; the title's other tells, if any, SHALL stay one refinement that names them, points to the blocker's alternatives and does not repeat the name. A title whose named technology is the object of the proposal's own research questions SHALL NOT be flagged.

#### Scenario: Tool-named title reviewed
- **WHEN** the proposal's title names the framework used to build its prototype, and nothing in the research depends on that framework
- **THEN** the review carries one enumerated item for it, a swap-test blocker that names the certificate consequence and suggests abstracted alternatives

#### Scenario: Decorative title name beside other title tells
- **WHEN** the title carries a platform no research question, goal or contribution statement depends on, an employer name and an implementation opener
- **THEN** the review carries the swap-test blocker on the platform with the certificate consequence and one to three alternatives, and one title refinement for the employer name and the opener that does not repeat the platform name or offer a second set of alternatives

#### Scenario: Instrument that shapes the method
- **WHEN** the title names a platform whose constraints the method is built around, though the platform is not what the thesis studies
- **THEN** the review carries an enumerated title item among the optional refinements, naming the certificate consequence and suggesting abstracted alternatives, and raises no swap-test blocker for it

#### Scenario: Title drifted from the research questions
- **WHEN** the title promises something the research questions do not address
- **THEN** the review flags the mismatch as a title finding

#### Scenario: Named technology is the research object
- **WHEN** the research questions are about the named technology itself
- **THEN** the review does not flag the title for naming it

### Requirement: Format-agnostic
The review SHALL NOT complain about section layout, ordering, headings, or markup conventions — structure compliance belongs to check. The proposal's thesis title is content, not layout, and is therefore in scope for the review despite being carried by the leading `# ` line: the review judges the title's text and stays silent about its markup.

#### Scenario: Non-canonical structure
- **WHEN** the proposal uses a free-form section structure
- **THEN** the review addresses only content and arguments, with no structural complaints

#### Scenario: Title assessed anyway
- **WHEN** the review reaches the leading `# ` title line
- **THEN** it assesses the title as content and stays silent about the line's heading markup

#### Scenario: Metadata title assessed anyway
- **WHEN** an old-format proposal still carries its title in the metadata block
- **THEN** the review assesses that title as content and stays silent about the block's markup

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

### Requirement: Grammar hint, never a list
If obvious grammar/spelling problems exist, the review SHALL close its findings with a brief hint including at most one or two examples — never an exhaustive enumeration. The hint SHALL follow the three finding sections; only the research-questions record comes after it.

#### Scenario: Pervasive passive voice and typos
- **WHEN** the text shows widespread language issues
- **THEN** the review closes its findings with a short hint and one or two examples, deferring the full pass to check, and the research-questions record follows the hint

### Requirement: Degree-level review lenses
The review SHALL judge level fit through the graded dimensions when the subtitle states the level: whether the contribution close matches the level's bar (application promise sufficient at Bachelor's, statement of what is new required at Master's — in both directions, so demanding novelty of a Bachelor's proposal is flagged as a mis-set bar exactly like a Master's close missing one), whether the research questions' origin fits (derivation from a given topic acceptable at Bachelor's, gap-grounding expected at Master's), whether the literature stance fits (established anchors legitimate at Bachelor's, the gap produced by engaging current work at Master's), and whether the scope is deliverable in the stated months at that level. Methodology fit is reviewed as judgement — whether the chosen methodology follows from the research questions, and at Master's level whether the plan shows awareness of its limits — never as a demand for explicit justification prose. When the subtitle does not state a level, the review SHALL apply the level-independent core and include exactly one line naming the unset level; it SHALL NOT guess.

#### Scenario: Master proposal with application-only close
- **WHEN** the subtitle declares a Master's thesis and the contribution close promises only competent application
- **THEN** the review flags the missing statement of what will be new as a level mismatch

#### Scenario: Bachelor proposal not held to the Master bar
- **WHEN** the subtitle declares a Bachelor's thesis and the close promises a competent, well-bounded evaluation
- **THEN** the review raises no novelty finding for the close

#### Scenario: Unknown level reviewed neutrally
- **WHEN** the subtitle is a TODO marker or matches no canonical wording
- **THEN** the review applies the level-independent rules, adds one line that the level is unset so level-dependent lenses were not applied, and guesses no level

### Requirement: Single-context execution
The review SHALL be a single-context task: one agent holding the whole proposal judges the six substance tests and every review dimension in one pass, because the verdict cites the failing tests together, findings are ordered by severity across all of them, and a research question is judged non-overlapping only relative to the others. Helper agents (subagents, workflows) SHALL NOT be part of the skill's execution. When the host nevertheless runs the task as a workflow, the skill SHALL cap it at three agents counting the reviewing agent itself: that agent is the full review, and the helpers are at most one adversarial check of its fail verdicts and one optional reading of the proposal's own references block for citation consistency, without network access. The skill SHALL NOT assign one agent per substance test, per dimension, or per research question. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, so that it is read before a run is planned, and the whole section SHALL be pinned verbatim offline.

Whatever the host does, a helper SHALL write no file: the main agent is the only writer, and `<slug>-review.md` carries every finding regardless of how many a helper returned. A helper SHALL work from the proposal file — never a source document — with the resolved workspace `guidelines.md` override and only the guideline sections its task needs, and SHALL return a verdict per substance test it examined (decisive fail, uncertain, or pass, with one quotable finding per failed test), then at most five findings, each with severity, location, a one-sentence problem, a one-sentence suggestion and a quote of at most one sentence, location-only duplicates merged into one finding with a location list. The helper's return SHALL carry no reasoning prose, no strengths list and no restated guidelines, unless the user asks for full reasoning. Title findings, sentence-level density findings and exceeded-limit findings keep the fuller shape this specification requires and are written by the main agent.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the review as a multi-agent workflow
- **THEN** the run uses at most three agents counting the reviewer, never one per test, dimension, or research question, and the review file is written by the reviewer

#### Scenario: Helper returns more than the contract allows
- **WHEN** a helper returns reasoning prose, a strengths list, or a dozen findings differing only in location
- **THEN** the main agent keeps the per-test verdicts and the merged, capped findings, discards the rest, and the review file still enumerates every finding the review itself established

#### Scenario: Helper judges against the workspace bar
- **WHEN** the workspace carries a `guidelines.md` override
- **THEN** every helper receives the resolved override with its guideline sections, so no finding is judged against the shipped defaults alone

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section, drops its helper-contract paragraph, or moves the section below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

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

### Requirement: Review hands over a bounded revision path

The chat summary of a review SHALL close with the stage handoff (skill-packaging), its route set by the verdict:

- **needs revision**: the recommended step is a revision of the proposal blockers, named briefly, followed by a fresh review of the changed text; the optional refinements worth taking MAY be one alternative, by number, and are never part of the recommended step. Where a blocker can only be resolved by a choice of the student's, that choice is put as an anchored decision.
- **ready**: the proposal stands at ready for supervisor discussion; the recommended step is the final check of language, title and timeline before the hand-in build, and the hand-in export MAY be the alternative. The clarify-early agenda is named as the thesis's first weeks, never as a step before hand-in.
- **no viable thesis core**: the recommended step is reworking the idea, put as an anchored question about the object or contribution the draft lacks; a sentence-level revision is never recommended.

The review SHALL NOT apply a finding, start a revision or run any other step: on approval, the revision follows the writing skill's instructions. When the user asks what to do with the feedback, the answer SHALL state the remaining path to the next milestone in at most a few sentences — at most the revision and one fresh review, whose earlier-round rules keep the findings from growing — and close with the handoff.

#### Scenario: Needs revision
- **WHEN** the review finds two proposal blockers and four optional refinements
- **THEN** the handoff recommends revising the two blockers followed by a fresh review, lists refinements only as an alternative, and the proposal file is unchanged

#### Scenario: Asked what to do with the feedback
- **WHEN** after a needs-revision review the user asks "What do we do now with that feedback?"
- **THEN** the answer states that one revision of the blockers and one fresh review stand between the draft and supervisor discussion, closes with the handoff, and leaves the proposal unchanged

#### Scenario: Blocker needs the student's choice
- **WHEN** a blocker states that a research question cannot fail as phrased and the methodology already names two measures the student could commit to
- **THEN** the handoff quotes the research question, says that choosing the measure decides what the thesis must show, offers the two measures and a way out, and does not ask an unanchored question

#### Scenario: Ready
- **WHEN** the review is ready with three clarify-early items
- **THEN** the handoff places the proposal at ready for supervisor discussion, recommends the final check before the hand-in build, and does not recommend settling the clarify-early items first

#### Scenario: No viable thesis core
- **WHEN** the verdict is no viable thesis core
- **THEN** the handoff recommends reworking the idea and does not recommend revising sentences of the draft

### Requirement: Named choices held to the swap test
The review SHALL hold every tool, system, platform or application domain the thesis names in its own claims to the guidance's swap test. The thesis's own claims are the title, the purpose statement that closes the introduction, the research focus and research questions, and the contribution section's statements of what the thesis adds. The review SHALL ask the replacement question of each such name explicitly, rather than leaving the check implicit in a judgement of genericity. A name passes when the research depends on it as the guidance defines: it is the object of study (the expected contribution claims its result for this instance), it imposes constraints that shape the method, it supplies data or access no comparable alternative offers, or it is the case the proposal argues suits its research questions (typical, critical or revelatory, as the Case Study contract asks). A comparison of named tools passes by design. The review SHALL state the pass anchors before the replacement verdict, and the replacement SHALL compare claims, not nouns: a name is decorative when the same claim still stands with only the noun changed. A name that fails SHALL be a proposal blocker that does four things:

- it cites the swap test;
- it locates every place the name stands within that scope;
- it states what stays unchanged when a comparable alternative replaces the name;
- it suggests both repairs: state what the research depends on in it, or generalize the claim to its class.

Its reason for being settled before approval SHALL be that either repair changes a research question or the contribution, or, for a name only the title carries, that the title is what the thesis is registered under and what the certificate prints. Several places carrying the same name SHALL form one finding with a location list. A name that passes SHALL NOT be reported under the swap test. Names of prior work, tools chosen to carry out the method and domains named only to motivate the topic SHALL NOT be reported under this check.

#### Scenario: Decorative framework in title and research questions
- **WHEN** the title and two research questions name an agent framework, while the contribution claims a within-model estimate of configuration effects in general
- **THEN** the review opens with needs revision and carries one swap-test blocker naming the framework and its locations, saying that a comparable framework would leave the research questions, the method and the contribution unchanged, and suggesting that the student state the dependence or generalize the title and research questions

#### Scenario: Framework as the object of study
- **WHEN** the same text's contribution close states that the thesis evaluates the framework's own default configuration for the teams that run it
- **THEN** no blocker and no swap-test finding concerns the framework's name

#### Scenario: Library named only in the method
- **WHEN** only the methodology names the library a prototype is built with
- **THEN** the review raises no swap-test finding about that library

#### Scenario: Decorative domain
- **WHEN** the research questions restrict a code-summarization study to one industry, while nothing in the data, method or contribution depends on that industry
- **THEN** the review carries a swap-test blocker on the domain, with both repairs

### Requirement: Research questions recorded in the review
The review file SHALL close with a record of the research questions the review judged: a section titled `## Research questions reviewed` (German: `## Begutachtete Forschungsfragen`) holding an ordered list. Its items SHALL be the items of the numbered list in the proposal's research-questions section, and nothing else: each copied verbatim, in the proposal's order. An overarching question the section states in prose before or after that list SHALL NOT enter the record. A nested item SHALL stay inside its parent item, never becoming an item of its own. No item SHALL be added, shortened, merged, reworded or translated. The record SHALL be the last section of the file, after every finding and after the grammar hint where one exists, and SHALL be plain markdown: no hidden comment, no front matter, no machine syntax beyond the heading and the list. When the research-questions section holds no numbered list, the review SHALL write no record.

The record is provenance, not a finding: the review SHALL NOT count, classify or comment on it, and the chat summary SHALL NOT mention it. A review that overwrites an earlier one SHALL carry exactly one record, listing the questions this review judged.

#### Scenario: Record closes the review
- **WHEN** the review judges a proposal whose research-questions section numbers three questions
- **THEN** the review file's last section is `## Research questions reviewed`, listing those three questions in the proposal's order, each with the proposal's own wording

#### Scenario: German proposal with an overarching question
- **WHEN** a German proposal's research-questions section states an overarching question in a sentence and then numbers four sub-questions
- **THEN** the record is titled `## Begutachtete Forschungsfragen` and lists the four numbered sub-questions verbatim in German, in their order, and not the overarching question

#### Scenario: Record after the grammar hint
- **WHEN** the review ends its findings with a grammar hint
- **THEN** the record follows the hint and is the last section of the file

#### Scenario: Later round
- **WHEN** a review overwrites an earlier review whose record lists four questions, and the current proposal numbers three
- **THEN** the new file carries exactly one record section, the last one, listing the current three questions

#### Scenario: No numbered research questions
- **WHEN** a free-form draft numbers no research question in a research-questions section
- **THEN** the review writes no record section
