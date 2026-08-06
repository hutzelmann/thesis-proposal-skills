# skill-review Delta

## ADDED Requirements

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

## MODIFIED Requirements

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
