## ADDED Requirements

### Requirement: Baseline comparison arm
Both runners SHALL support a without-skill control for single-turn tasks: the same fixture staging, user request, and verdicts, with the skill neither installed nor injected. Baseline runs SHALL be on-demand and cost-gated like every metered run, never part of the default matrix. Where baseline results exist beside with-skill results, the report SHALL show per task what the skill buys (pass-rate delta) against what it costs (token delta), SHALL flag scorers that pass in both arms as dead-assertion candidates, and SHALL flag scorers that fail in both arms as too-hard candidates. Verdict logic SHALL be identical in both arms.

#### Scenario: Baseline run requested
- **WHEN** a baseline run is invoked on a single-turn task
- **THEN** the model receives the task's user request and files without any skill instructions, and the run is scored by the same verdicts as the with-skill run

#### Scenario: Delta reported
- **WHEN** the report finds baseline and with-skill results for the same task and model
- **THEN** it renders the pass-rate delta beside the token delta, so a skill that buys nothing at double the tokens is visible as such

#### Scenario: Assertion passes in both arms
- **WHEN** a scorer passes with and without the skill
- **THEN** the report names it as a dead-assertion candidate rather than counting it silently toward skill value

#### Scenario: Multi-turn task requested as baseline
- **WHEN** a baseline run is invoked on a persona-dialogue task
- **THEN** the invocation is rejected with the reason rather than producing a meaningless control

### Requirement: Duration reported beside token usage
The support report SHALL read wall-clock duration from the run logs and present it alongside token usage, so the cost of a skill is visible in both currencies.

#### Scenario: Report generated from logs
- **WHEN** the report is regenerated from eval logs
- **THEN** each run's duration appears beside its token usage and cost
