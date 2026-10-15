# Spec Delta

## MODIFIED Requirements

### Requirement: Persisted, actionable output
The review SHALL be written to `review.md` in the proposal's folder (overwritten per run, after the earlier round has been carried over), in the proposal's declared language. After the verdict it SHALL carry the earlier-round section when an earlier review existed, then three sections in this order — proposal blockers, clarify early in the thesis, optional refinements (German: `## Vor der Annahme zu klären`, `## Früh in der Arbeit zu klären`, `## Optionale Verbesserungen`) — each an enumerated list ordered by severity, an empty one stating that it has no items. Every finding SHALL carry what is wrong, where, and an actionable suggestion. Every blocker SHALL name its failed test and state why it must be resolved before approval rather than during the thesis. Every clarify-early item SHALL carry its deferral record: what needs deciding, why it matters, when or under what condition it is settled, a reasonable way to resolve it, and whether an adverse outcome would require revisiting the proposal. The clarify-early section is the early-thesis clarification agenda: on a ready verdict the chat summary SHALL name it as the agenda for the thesis's first weeks; it stays outside the proposal, and the review SHALL NOT ask for a new proposal section or a work plan to carry it. Where a finding concerns an exceeded limit or forbidden content, the suggestion SHALL state what suffices and where the surplus content goes — never only that the content does not belong.

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

#### Scenario: Review lands in the proposal's folder
- **WHEN** the proposal is `<slug>/<slug>.md`
- **THEN** the review is written to `<slug>/review.md`, and no review file is written outside that folder

### Requirement: Single-context execution
The review SHALL be a single-context task: one agent holding the whole proposal judges the six substance tests and every review dimension in one pass, because the verdict cites the failing tests together, findings are ordered by severity across all of them, and a research question is judged non-overlapping only relative to the others. Helper agents (subagents, workflows) SHALL NOT be part of the skill's execution. When the host nevertheless runs the task as a workflow, the skill SHALL cap it at three agents counting the reviewing agent itself: that agent is the full review, and the helpers are at most one adversarial check of its fail verdicts and one optional reading of the proposal's own references block for citation consistency, without network access. The skill SHALL NOT assign one agent per substance test, per dimension, or per research question. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, so that it is read before a run is planned, and the whole section SHALL be pinned verbatim offline.

Whatever the host does, a helper SHALL write no file: the main agent is the only writer, and `review.md` carries every finding regardless of how many a helper returned. A helper SHALL work from the proposal file — never a source document — with the resolved workspace `guidelines.md` override and only the guideline sections its task needs, and SHALL return a verdict per substance test it examined (decisive fail, uncertain, or pass, with one quotable finding per failed test), then at most five findings, each with severity, location, a one-sentence problem, a one-sentence suggestion and a quote of at most one sentence, location-only duplicates merged into one finding with a location list. The helper's return SHALL carry no reasoning prose, no strengths list and no restated guidelines, unless the user asks for full reasoning. Title findings, sentence-level density findings and exceeded-limit findings keep the fuller shape this specification requires and are written by the main agent.

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
Before overwriting an existing `review.md`, the skill SHALL read it and carry its findings into the new review under an earlier-round section (German: `## Frühere Runde`): each earlier blocker marked resolved, partly resolved, or open, where resolved is judged against what that blocker asked for, not against a bar raised since. Classification across rounds SHALL be monotone as the guidance defines it: a finding about a passage the revision left unchanged SHALL keep its earlier class or move to a lower one, so an earlier clarify-early item or refinement about unchanged text SHALL NOT become a blocker. A blocker new in this round SHALL either concern text the revision introduced or changed, or be labelled as missed in the earlier round with the flaw it exposes stated; the chat summary SHALL count such missed-earlier blockers. Newly noticed execution details SHALL enter the clarify-early section. A partly resolved blocker whose residue passes the deferral record SHALL move to the clarify-early section. Without an earlier review the skill SHALL write no earlier-round section.

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
- **WHEN** no earlier review file exists in the proposal's folder
- **THEN** the review carries no earlier-round section
