## MODIFIED Requirements

### Requirement: Route determined by the first skill invocation
A case's route SHALL be the first invocation of a `proposal-*` skill observed in the run, and the run SHALL be terminated as soon as that route is recorded. Preparatory non-skill tool calls SHALL be tolerated up to a bounded number, and a case that exceeds that bound SHALL be recorded as unrouted rather than retried. A case still running when its time limit is reached, with no route recorded, SHALL instead be recorded as an error naming the limit — whether or not it had exceeded the bound — and SHALL NOT be retried: a host that has not finished within the limit says nothing about the descriptions, and a negative case would pass on it. Skill invocations after the first SHALL NOT change the recorded route.

A case the host ends with an error result before any `proposal-*` invocation SHALL be recorded as an error carrying the host's reason — its subtype, its errors or result text, and the cost and turns so far — and SHALL NOT be recorded as unrouted. Unrouted is a finding about the descriptions; a host failure says nothing about them, and a negative case would pass on it.

#### Scenario: Route recorded and run stopped
- **WHEN** the agent invokes a `proposal-*` skill
- **THEN** that skill is the case's route and no further work is performed for that case

#### Scenario: Agent inspects before choosing
- **WHEN** the agent makes a small number of non-skill tool calls and then invokes a `proposal-*` skill
- **THEN** the invoked skill is still recorded as the route

#### Scenario: No skill chosen
- **WHEN** the bound on preparatory tool calls is exceeded with no `proposal-*` skill invoked, and the host ends the case before its time limit with a result that is not an error
- **THEN** the case is recorded as unrouted

#### Scenario: Skill chains into a sibling
- **WHEN** the selected skill invokes another `proposal-*` skill
- **THEN** the recorded route remains the first invocation

#### Scenario: Host ends the case with an error
- **WHEN** the host ends a case with an error result and no `proposal-*` skill was invoked
- **THEN** the case is recorded as an error naming the host's reason, it counts neither as unrouted nor toward any kind's total, and a negative case does not pass on it

#### Scenario: Unrouted answer is not an error
- **WHEN** the host ends a case with a result that is not an error and no `proposal-*` skill was invoked
- **THEN** the case is recorded as unrouted

#### Scenario: Case reaches its time limit
- **WHEN** a case is still running at its time limit and no route was recorded
- **THEN** the case is recorded as an error naming the limit, it counts neither as unrouted nor toward any kind's total, it is not retried, and a negative case does not pass on it
