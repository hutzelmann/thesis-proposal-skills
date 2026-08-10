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
The review SHALL NOT complain about section layout, ordering, headings, or markup conventions — structure compliance belongs to check. The proposal's thesis title is content, not layout, and is therefore in scope for the review despite living in the metadata block.

#### Scenario: Non-canonical structure
- **WHEN** the proposal uses a free-form section structure
- **THEN** the review addresses only content and arguments, with no structural complaints

#### Scenario: Metadata title assessed anyway
- **WHEN** the review reaches the metadata block
- **THEN** it assesses the title as content and stays silent about the block's markup

### Requirement: Persisted, actionable output
The review SHALL be written to `<slug>-review.md` next to the proposal (overwritten per run), in the proposal's declared language, as an enumerated list of issues each with an actionable suggestion.

#### Scenario: German proposal reviewed
- **WHEN** the proposal declares `lang: de`
- **THEN** the review file is written in German

### Requirement: Grammar hint, never a list
If obvious grammar/spelling problems exist, the review SHALL end with a brief hint including at most one or two examples — never an exhaustive enumeration.

#### Scenario: Pervasive passive voice and typos
- **WHEN** the text shows widespread language issues
- **THEN** the review closes with a short hint and one or two examples, deferring the full pass to check

