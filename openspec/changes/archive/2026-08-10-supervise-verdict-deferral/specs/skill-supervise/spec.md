# skill-supervise Delta

## MODIFIED Requirements

### Requirement: Verdict expressed as proposal state

The letter SHALL open with a verdict expressed as the state of the proposal and never as a commitment on the professor's behalf. The student-facing tiers are: **ready**, phrased as requiring no substantial revisions; **needs revision**, directing the student to address the enumerated points and resubmit; and **idea stage** (German: Ideenphase), stating that the material is an idea that has not yet reached the proposal stage. The idea-stage tier SHALL couple the standard a proposal must meet with an assurance anchored in a named, true strength of the submission and a feed-forward to ideation as the designed next step — never framed as failure, never softened into revision advice. The professor-side review file SHALL keep the review skill's blunt three-tier vocabulary unchanged.

The idea-stage tier SHALL only be assigned automatically when the failure is evidence-clear: at least three of the five substance tests fail decisively, each with a stated reason why no single revision round can repair it. When the internal review reaches no-viable-core without meeting that bar, the verdict decision SHALL be deferred to the professor rather than taken by the skill. The skill SHALL NOT promise meetings, approvals, deadlines, or any other supervisor action.

#### Scenario: Ready without commitment
- **WHEN** the submission passes review with no substantial findings
- **THEN** the letter states that no substantial revisions are needed from the reviewer's side and leaves the next step to the professor

#### Scenario: Evidence-clear idea stage
- **WHEN** at least three substance tests fail decisively and no single revision round could repair them
- **THEN** the letter opens with the idea-stage verdict, names the proposal standard, anchors an assurance in a true strength, and directs the student to ideation — without asking the professor first

#### Scenario: Blunt vocabulary stays professor-side
- **WHEN** the internal review concludes no viable thesis core
- **THEN** the review file says so in those words while the letter renders the tier as idea stage

### Requirement: Student-facing package with disclosure and steering

The skill SHALL assemble a send-package containing the feedback letter and the normalized proposal file. The letter SHALL be written in the language of the submission, SHALL disclose in plain language that the feedback was prepared with an AI assistant, SHALL name for each curated point the skill that addresses it, and SHALL close with a getting-started blurb — maintained as a shared snippet in English and German — that links the skill installation source and tells the student to place the attached file in their workspace and continue with the writing skill.

For idea-stage and borderline outcomes, the skill SHALL offer the professor — never run unasked — a starter-literature step: finding two or three verified relevant papers via the literature-search sibling and naming them in the letter as where the conversation already is. The offer SHALL be declined silently when the sibling is not installed or the professor does not accept; entries SHALL only ever come from real, verified lookups.

#### Scenario: German submission
- **WHEN** the submission is written in German
- **THEN** the letter, its skill pointers, and the getting-started blurb are in German

#### Scenario: Point steers to a skill
- **WHEN** a curated point concerns thin literature grounding
- **THEN** the point names the literature-search skill as the way to address it

#### Scenario: Disclosure is plain-language
- **WHEN** the letter is assembled
- **THEN** it states that an AI assistant following the proposal guidelines prepared the feedback, in wording that assumes no prior AI exposure

#### Scenario: Starter literature offered, not imposed
- **WHEN** the outcome is idea-stage and the literature-search sibling is installed
- **THEN** the skill offers the starter-literature step and adds papers only after the professor accepts, from verified lookups only

## ADDED Requirements

### Requirement: Borderline verdict deferred to the supervisor

When the internal review reaches no-viable-core but the evidence bar is not met, the skill SHALL pause before writing the letter and put the decision to the professor as a guided choice: a needs-revision letter emphasizing re-grounding, an idea-stage letter, or reading the professor-side review file first and deciding after. The question SHALL summarize the split evidence — which substance tests failed, which are uncertain, with a finding excerpt each — so the professor can decide without leaving the chat. Evidence-clear cases (either direction) SHALL NOT trigger the question. When the professor cannot be asked (a non-interactive run, or the user declines to decide), the skill SHALL default to the needs-revision letter — in doubt, for the student.

#### Scenario: Borderline pauses for the professor
- **WHEN** the review concludes no-viable-core but only two substance tests fail decisively
- **THEN** the skill presents the split evidence and the three choices, and writes the letter only after the professor picks

#### Scenario: Clear case skips the question
- **WHEN** the evidence bar is met
- **THEN** the letter is written without a deferral question

#### Scenario: Undecidable defaults constructive
- **WHEN** the deferral cannot be answered
- **THEN** the letter takes the needs-revision path
