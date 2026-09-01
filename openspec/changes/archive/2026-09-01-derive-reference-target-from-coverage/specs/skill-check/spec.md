# skill-check — delta

## ADDED Requirements

### Requirement: Reference-density advisory warning
The deterministic script SHALL judge the number of defined references against a length-scaled expectation: the body word count (the same count the length estimate uses) times the effective reference-density constant (default or workspace `[references] min_per_1000_words` override) per thousand words, rounded up. A proposal defining fewer references than the expectation SHALL receive a warning, never an error. The warning SHALL name the reference count, the word count, the effective density, and the resulting expectation, so the student sees why the number moved with the document's length.

The warning SHALL be suppressed while the reference-floor error fires, so one defect never produces two findings. A density of zero SHALL disable the advisory. An override value that is not a non-negative finite number SHALL be reported as a mechanical error and SHALL degrade to the default density, never crash the run or silently disable the rule. The effective density SHALL be capped at one reference per word (1000 per 1000 words), so an extreme but valid override cannot overflow the computation. Structured guidance data that predates the constant SHALL disable the advisory rather than fail the run.

#### Scenario: Full-length proposal with a thin bibliography
- **WHEN** a proposal's body is 2500 words and it defines 6 references at the default density of 4 per 1000 words
- **THEN** the check emits a warning naming 6 references against an expectation of 10, and the run does not fail

#### Scenario: Short draft is not nagged
- **WHEN** a proposal's body is short enough that the expectation is at or below the reference floor
- **THEN** no density warning is emitted

#### Scenario: Floor error suppresses the advisory
- **WHEN** a proposal defines fewer references than the floor
- **THEN** the floor error is the only reference-count finding

#### Scenario: Workspace override respected
- **WHEN** `guidelines.md` sets `[references] min_per_1000_words = 8` and the proposal's density sits between 4 and 8 per 1000 words
- **THEN** the density warning fires against the workspace value

#### Scenario: Zero disables the advisory
- **WHEN** `guidelines.md` sets `[references] min_per_1000_words = 0`
- **THEN** no density warning is emitted regardless of length

#### Scenario: Invalid override degrades to the default
- **WHEN** `guidelines.md` sets `[references] min_per_1000_words = "4"`, a negative value, or a non-finite value such as `inf`
- **THEN** the check reports a mechanical error naming the invalid value, judges the proposal against the default density, and the report still completes

#### Scenario: Extreme but valid override cannot crash the run
- **WHEN** `guidelines.md` sets the density to a finite but absurd value (a huge float or an arbitrary-precision TOML integer)
- **THEN** the run completes, with the effective density capped at one reference per word

#### Scenario: Older structured data disables the advisory
- **WHEN** the structured guidance data carries no reference-density constant and no workspace override sets one
- **THEN** no density finding is emitted and the run completes normally
