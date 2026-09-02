## MODIFIED Requirements

### Requirement: Non-defect causes named as such

Four causes SHALL be reported as correct behavior rather than as defects: a model known to fail the task in question, a workspace `guidelines.md` override producing the behavior the user objects to, dissatisfaction with output that broke no stated rule, and a run that cost many times the usual while producing correct output because the host's effort or workflow mode fanned the task out into many agents — against the execution shape the skill states, where it states one. For each, the skill SHALL name the mechanism responsible and the user's available remedy — switch models, amend the overrides, use the review or customize skill, or use the host's own budget and effort controls.

An unsupported model SHALL remain reportable at the user's option, because a fresh failure on a known-weak model is evidence about that model rather than noise.

#### Scenario: Known-weak model on a task it fails

- **WHEN** the failing task is one the shipped support data records the running model as failing
- **THEN** the skill states that the model, not the skill, is the cause, names a remedy, and offers the report as optional model evidence

#### Scenario: Supervisor override is responsible

- **WHEN** a workspace `guidelines.md` override produces the behavior the user objects to
- **THEN** the skill names the override and states that it is winning as designed

#### Scenario: Output broke no rule

- **WHEN** the user's objection is to output quality and no stated rule was broken
- **THEN** the skill routes them to the review or customize skill and assembles no report

#### Scenario: Cost blowup under a fan-out host mode

- **WHEN** the user reports that a run cost many times the usual and its output was otherwise correct
- **THEN** the skill lands on the dissatisfaction rung, names the host's effort or workflow mode and its budget and effort controls as the mechanism and remedy, and assembles no report
