## ADDED Requirements

### Requirement: Single-context execution

The review SHALL be a single-context task: one agent holding the whole proposal judges the five substance tests and every review dimension in one pass, because the verdict cites the failing tests together, findings are ordered by severity across all of them, and a research question is judged non-overlapping only relative to the others. Helper agents (subagents, workflows) SHALL NOT be part of the skill's execution. When the host nevertheless runs the task as a workflow, the skill SHALL cap it at three agents with fixed roles — one full review, one adversarial check of the review's fail verdicts, one optional reading of the proposal's own references block for citation consistency, without network access — and SHALL NOT assign one agent per substance test, per dimension, or per research question. Following a sibling skill's instructions in the same context is not a helper. The SKILL.md SHALL state this shape before the assessment list, so that it is read before a run is planned, and its opening sentence naming the shape and the cap SHALL be pinned offline.

Whatever the host does, the main agent SHALL be the only writer: a helper writes no file, and `<slug>-review.md` carries every finding regardless of how many a helper returned. A helper SHALL work from the proposal file — never a source document — with the resolved workspace `guidelines.md` override and only the guideline sections its task needs, and SHALL return a verdict per substance test (decisive fail, uncertain, or pass, with one quotable finding per failed test), then at most five findings, each with severity, location, a one-sentence problem, a one-sentence suggestion and a quote of at most one sentence, location-only duplicates merged into one finding with a location list — no reasoning prose, no strengths list, no restated guidelines, unless the user asks for full reasoning. Title findings, sentence-level density findings and exceeded-limit findings keep the fuller shape this specification requires and are written by the main agent.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the review as a multi-agent workflow
- **THEN** the run uses at most three agents in the fixed roles, never one per test, dimension, or research question, and the review file is written by the main agent

#### Scenario: Helper returns more than the contract allows
- **WHEN** a helper returns reasoning prose, a strengths list, or a dozen findings differing only in location
- **THEN** the main agent keeps the per-test verdicts and the merged, capped findings, discards the rest, and the review file still enumerates every finding the review itself established

#### Scenario: Helper judges against the workspace bar
- **WHEN** the workspace carries a `guidelines.md` override
- **THEN** every helper receives the resolved override with its guideline sections, so no finding is judged against the shipped defaults alone

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords the execution-shape section without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the sentence
