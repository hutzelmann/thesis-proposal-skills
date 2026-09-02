# skill-review Specification

## Purpose
High-level content review of a proposal — arguments, literature grounding, sharpness — producing an enumerated, actionable review file.
## Requirements
### Requirement: Content-level review scope
The skill SHALL review argument structure, soundness, missing literature or information, sharpness/focus, unnecessary content, redundancy, and inconsistencies — including the semantic guidance rules (analytical research questions, explicit contribution delta, single methodology). The review SHALL judge the proposal against the five substance tests named in the guidance, including concreteness and executability: whether the proposal names its objects of study, states a concrete evaluation, and gives the student actionable goals feasible in the stated months. The review SHALL apply the information-density rule at sentence level: sentences that carry no information essential to this thesis SHALL be named concretely as removable, quoting or locating each, not merely described as a general verbosity concern.

#### Scenario: Implementation-goal research questions
- **WHEN** research questions are phrased as "how can X be implemented"
- **THEN** the review flags them and suggests analytical reformulations

#### Scenario: Filler sentences named
- **WHEN** a proposal carries scene-setting sentences that would fit any thesis in the area
- **THEN** the review names those sentences and marks them as removable filler, rather than issuing a general brevity remark

#### Scenario: Methodology not executable
- **WHEN** the methodology promises an evaluation but names no dataset, benchmark, system, or population
- **THEN** the review flags the executability gap and asks for the missing concrete object

### Requirement: Three-tier substance verdict
The review SHALL open with an explicit verdict, one of exactly three tiers: **ready** (no substantial findings remain), **needs revision** (findings exist but are fixable in place), or **no viable thesis core** (one or more substance tests fail in a way no in-place edit can repair). The verdict SHALL be judged against the five substance tests named in the guidance — delta, falsifiability, swap, method-fit, executability — and where any test fails, the verdict statement SHALL cite the failed tests by name. The verdict SHALL appear at the top of the review file and in the chat summary. The skill SHALL NOT soften a no-viable-core verdict into needs-revision phrasing: when the substance is hollow, the review says so plainly and states what kind of work (re-ideation, a genuine delta, a concrete evaluation object) would change the verdict. The verdict is advisory like the rest of the review: it blocks nothing.

#### Scenario: Hollow but structurally clean proposal
- **WHEN** a proposal passes every mechanical check but its text would describe any thesis in the area, states no delta beyond the cited work, and names no object of study
- **THEN** the review's verdict is "no viable thesis core", citing at least the swap, delta, and executability tests, and states what would change the verdict

#### Scenario: Sound proposal with fixable findings
- **WHEN** the substance tests pass but individual findings remain (an overlapping RQ pair, a vague evaluation metric)
- **THEN** the verdict is "needs revision" and the findings are enumerated as before

#### Scenario: Verdict reaches the chat summary
- **WHEN** the review file is written
- **THEN** the chat summary opens with the same verdict tier the file carries

### Requirement: Title assessed as its own dimension
The review SHALL assess the proposal's thesis title as a dimension of its own, against the guidance: whether it names a contribution and its object, whether it carries a tool, product, or vendor name as the instrument, whether it frames implementation work rather than research, whether it names a field rather than a thesis, and whether it carries marketing tone. Where the review flags the title it SHALL say that the title is printed on the study certificate and SHALL suggest between one and three abstracted alternatives, as an enumerated item like any other finding. A title whose named technology is the object of the proposal's own research questions SHALL NOT be flagged.

#### Scenario: Tool-named title reviewed
- **WHEN** the proposal's title names the framework used to build its prototype
- **THEN** the review carries an enumerated title item naming the certificate consequence and suggesting abstracted alternatives

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
The review SHALL be written to `<slug>-review.md` next to the proposal (overwritten per run), in the proposal's declared language, as an enumerated list of issues each with an actionable suggestion. Where a finding concerns an exceeded limit or forbidden content, the suggestion SHALL state what suffices and where the surplus content goes — never only that the content does not belong.

#### Scenario: German proposal reviewed
- **WHEN** the proposal declares `lang: de`
- **THEN** the review file is written in German

#### Scenario: Work plan in the timeline section
- **WHEN** the proposal's timeline section carries a phase breakdown or Gantt-style work plan
- **THEN** the finding's suggestion states that one sentence naming start and submission month suffices and that the phase detail belongs in the writer's own working notes, rather than only declaring the plan forbidden

### Requirement: Grammar hint, never a list
If obvious grammar/spelling problems exist, the review SHALL end with a brief hint including at most one or two examples — never an exhaustive enumeration.

#### Scenario: Pervasive passive voice and typos
- **WHEN** the text shows widespread language issues
- **THEN** the review closes with a short hint and one or two examples, deferring the full pass to check

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

