## ADDED Requirements

### Requirement: Research-question count bounds
The structured guidance data SHALL bound the number of research questions from both sides. The lower bound SHALL be 1 and the upper bound SHALL default to 5. Both bounds SHALL be workspace-overridable. The prose guidance SHALL state the upper bound and the failure it detects — a scope that has not been decided — rather than the number alone.

The bound counts the ordered-list items under the research-questions section, which is the same list the `(RQn)` cross-reference rule already counts. Whether a set of questions is genuinely distinct, non-overlapping, and analytically phrased SHALL remain prose guidance, since it is a judgement rather than a count.

#### Scenario: Count within bounds
- **WHEN** a proposal declares three research questions
- **THEN** no count-related finding is reported

#### Scenario: Count above the default bound
- **WHEN** a proposal declares six research questions and the workspace sets no override
- **THEN** guidance-following tooling reports the count as a violation, naming both the count found and the bound

#### Scenario: Workspace raises the bound
- **WHEN** a workspace override sets the upper bound to 7 and a proposal declares six research questions
- **THEN** no count-related finding is reported

#### Scenario: Overlap judgement stays prose
- **WHEN** two of three research questions are near-duplicates of each other
- **THEN** no structured rule detects it, and the judgement stays with the agent
