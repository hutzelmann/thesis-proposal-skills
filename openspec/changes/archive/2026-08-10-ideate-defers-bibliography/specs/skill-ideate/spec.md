## ADDED Requirements

### Requirement: Grounding is not bibliography-building
The skill SHALL NOT state a target or minimum number of references, and SHALL NOT run grounding searches in order to reach one. Grounding exists to test whether the idea is already solved and how it differs from prior work; assembling the literature base belongs to the literature-search skill, which the ideation skill SHALL name as the place that work happens.

The skill MAY still describe the shape the idea must eventually take — an analytical research focus, a research-question count within the configured bounds, one methodology from the closed set — since those are properties of the idea rather than of its bibliography.

#### Scenario: Reference count not raised during ideation
- **WHEN** the student asks how many sources the proposal needs
- **THEN** the skill answers by naming the literature-search skill as the next step rather than by setting a count to reach in this session

#### Scenario: Thin grounding is not padded
- **WHEN** grounding surfaces only one relevant work
- **THEN** the skill says the signal is thin and does not search further merely to raise the number of references in the seed
