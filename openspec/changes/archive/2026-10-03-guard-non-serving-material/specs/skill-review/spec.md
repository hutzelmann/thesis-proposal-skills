## MODIFIED Requirements

### Requirement: Content-level review scope
The skill SHALL review argument structure, soundness, missing literature or information, sharpness/focus, unnecessary content, redundancy, and inconsistencies — including the semantic guidance rules (analytical research questions, explicit contribution delta, single methodology). The review SHALL judge the proposal against the six substance tests named in the guidance, including concreteness and executability: whether the proposal names its objects of study, states a concrete evaluation, and gives the student actionable goals feasible in the stated months. The review SHALL apply the information-density rule at sentence level: sentences that carry no information essential to this thesis SHALL be named concretely as removable, quoting or locating each, not merely described as a general verbosity concern.

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

### Requirement: Three-tier substance verdict
The review SHALL open with an explicit verdict, one of exactly three tiers: **ready** (no substantial findings remain), **needs revision** (findings exist but are fixable in place), or **no viable thesis core** (one or more substance tests fail in a way no in-place edit can repair). The verdict SHALL be judged against the six substance tests named in the guidance — delta, falsifiability, swap, necessity, method-fit, executability — and where any test fails, the verdict statement SHALL cite the failed tests by name. The verdict SHALL appear at the top of the review file and in the chat summary. The skill SHALL NOT soften a no-viable-core verdict into needs-revision phrasing: when the substance is hollow, the review says so plainly and states what kind of work (re-ideation, a genuine delta, a concrete evaluation object) would change the verdict. The verdict is advisory like the rest of the review: it blocks nothing.

A necessity-test failure SHALL NOT by itself carry a no-viable-core verdict: material that serves no research question is removable in place, so it is a needs-revision finding unless the tests that decide viability also fail.

#### Scenario: Hollow but structurally clean proposal
- **WHEN** a proposal passes every mechanical check but its text would describe any thesis in the area, states no delta beyond the cited work, and names no object of study
- **THEN** the review's verdict is "no viable thesis core", citing at least the swap, delta, and executability tests, and states what would change the verdict

#### Scenario: Sound proposal with fixable findings
- **WHEN** the substance tests pass but individual findings remain (an overlapping RQ pair, a vague evaluation metric)
- **THEN** the verdict is "needs revision" and the findings are enumerated as before

#### Scenario: Otherwise sound proposal carrying non-serving material
- **WHEN** the only failing test is necessity — a sourced, specific passage that no research question, delta statement, or method step depends on
- **THEN** the verdict is "needs revision", the finding names the necessity test and locates the passage as removable, and the verdict is not lowered to no viable thesis core

#### Scenario: Verdict reaches the chat summary
- **WHEN** the review file is written
- **THEN** the chat summary opens with the same verdict tier the file carries

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
