## MODIFIED Requirements

### Requirement: Methodology sections justify method fit
The guidance SHALL require every methodology section to open with one or two sentences stating confidently why the chosen methodology is the right one for the research questions: what answering them demands, and what this methodology does that meets the demand, in the questions' own terms. The opening SHALL NOT be a suitability verdict, the branch's definition restated as a property of the questions, a feasibility argument, or a list of methods not taken.

#### Scenario: Methodology opens without justification
- **WHEN** a methodology section starts directly with its first subsection and never says why this methodology is the right one for these questions
- **THEN** guidance-following tooling asks for the opening justification, as a refinement

#### Scenario: Suitability verdict instead of a justification
- **WHEN** a methodology section opens by saying the methodology fits the questions because they ask what the methodology does by definition, and that the study can be run this way
- **THEN** guidance-following tooling restates the opening as what the questions demand and what this methodology does that meets it, as a refinement, and leaves the methodology choice unchanged

#### Scenario: Justification present
- **WHEN** a methodology section opens by stating that both questions ask whether explanation style itself changes how developers act on a warning, and that only varying the style while the warnings, the code and the task stay fixed attributes a difference in behavior to it
- **THEN** the requirement is satisfied

#### Scenario: Justification that does not hold
- **WHEN** the opening names a demand the research questions do not make, or one the chosen methodology cannot meet
- **THEN** the defect is a method-fit failure, classified as the method-fit test classifies it, not a refinement of wording

### Requirement: Degree-level guidance
The guidelines SHALL carry a degree-level section stating where the level shows in a proposal, covering exactly four graded dimensions — contribution expectation, research-question origin, literature stance, and scope relative to the available months — in brief prose, and framing everything else as identical across levels by design, with `docs/degree-level-sources.md` named as provenance. The section SHALL state the both-directions bar: demanding a novelty claim from a Bachelor's proposal is the same error as accepting its absence from a Master's proposal. Bachelor-side statements SHALL be phrased as expectations not required, never as prohibitions — incipient novelty in a Bachelor's proposal remains welcome. The section SHALL state that the methodology section's opening justification is the same at both levels. The document skeleton, `structure.json`, and all mechanical checks SHALL remain level-blind.

#### Scenario: Four dimensions, nothing structural
- **WHEN** the guidelines' degree-level section is compared with `structure.json` and the check rules
- **THEN** the section names contribution expectation, research-question origin, literature stance, and scope-per-months as the graded dimensions, and no structured key or mechanical check varies by degree level

#### Scenario: Bachelor phrasing stays permissive
- **WHEN** the section describes the Bachelor's-level expectation on any dimension
- **THEN** the wording says what is not required at that level and never forbids exceeding it

#### Scenario: No justification requirement
- **WHEN** the section describes methodology at either level
- **THEN** it adds no level-specific justification requirement, states that the methodology section's opening justification is the same at both levels, and never says that no justification is required
