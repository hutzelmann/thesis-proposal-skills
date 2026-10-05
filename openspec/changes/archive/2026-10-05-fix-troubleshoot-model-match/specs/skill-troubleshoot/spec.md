## MODIFIED Requirements

### Requirement: Support verdicts shipped as skill data

The model-support verdicts the ladder consults SHALL ship inside the skill as committed machine-readable data. The skill SHALL NOT depend on network access or on the development repository to reach them, because it runs in a user's workspace which contains neither. When the shipped data has no entry for the running model or the task, the skill SHALL say the rung is unevaluated rather than treat absence as a pass.

The running model SHALL be looked up by the exact identifier its host states. When that exact string is absent from the shipped data, the skill SHALL compare spellings instead. An entry belongs to the running model when both spellings are equal after the same normalisation is applied to each. That normalisation ignores:

- letter case and surrounding whitespace;
- routing and vendor prefixes, meaning everything up to the last `/`;
- a cloud provider's wrapping: a leading vendor segment with an optional region, and a trailing revision;
- a trailing date stamp;
- a trailing bracketed variant qualifier.

It also reads a dash between two digits as a dot. Hosts spell one model several ways. Claude Code, for one, puts dashes between version digits and appends a date stamp where the data keys the same model with a dotted version under a vendor prefix. A verdict missed for that reason reads to the user as "unevaluated" when the data records a failure.

Normalised spellings SHALL be compared for equality, never as prefixes. A different version number names a different model and SHALL NOT inherit another version's verdict. When more than one entry matches, the skill SHALL choose none and report the rung as unevaluated, because picking one would report a neighbouring model's verdict as the user's.

#### Scenario: Verdicts consulted offline

- **WHEN** the ladder reaches the model rung with no network available
- **THEN** the verdicts are read from the skill's shipped data

#### Scenario: Model absent from the shipped data

- **WHEN** the running model has no entry in the shipped verdicts
- **THEN** the skill reports the rung as unevaluated for that model and continues down the ladder

#### Scenario: Host spelling differs from the data's key

- **WHEN** the host states the running model as `example-4-5-20251001` and the shipped data keys that model as `lab/example-4.5`
- **THEN** the skill uses the verdicts recorded under `lab/example-4.5`

#### Scenario: Newer version than any recorded

- **WHEN** the host states the running model as `example-5-5` and the shipped data holds `lab/example-5` but no 5.5 entry
- **THEN** the skill reports the rung as unevaluated for that model rather than applying the `lab/example-5` verdict

#### Scenario: Two entries match the same spelling

- **WHEN** two entries in the shipped data normalise to the running model's spelling
- **THEN** the skill applies neither verdict and reports the rung as unevaluated

### Requirement: Measured facts distinguished from self-reported ones

Every fact in the report SHALL be marked as either measured or self-reported. Facts a script established — interpreter and tool versions, operating system, file hashes, script exit codes and digests — are measured. Facts the agent supplies about itself or about what happened — its model identity, its harness, its account of the failing exchange — are self-reported.

The distinction SHALL be visible in the report itself. The agent assembling the report is the subject of the report, so a maintainer must be able to see which half of it is testimony without inferring it.

The self-reported model identity SHALL be the exact identifier the agent's host states, not a display name or an alias such as `sonnet`. An alias names no version, so a maintainer cannot match it to a verdict or a measurement. An agent that does not know its exact identifier SHALL say so rather than supply a guess.

#### Scenario: Environment recorded

- **WHEN** interpreter and tool versions are collected by a script
- **THEN** they appear marked as measured

#### Scenario: Agent describes what it did

- **WHEN** the agent contributes its account of the failing exchange or its own model identity
- **THEN** that content appears marked as self-reported

#### Scenario: Model identity given as the host states it

- **WHEN** the agent fills in its model identity and its host states the identifier `example-5-5`
- **THEN** the report carries `example-5-5`, not a display name such as "Example 5.5" or an alias such as `example`
