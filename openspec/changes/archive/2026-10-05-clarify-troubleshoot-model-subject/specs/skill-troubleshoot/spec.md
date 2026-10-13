## MODIFIED Requirements

### Requirement: Support verdicts shipped as skill data

The model-support verdicts the ladder consults SHALL ship inside the skill as committed machine-readable data. The skill SHALL NOT depend on network access or on the development repository to reach them, because it runs in a user's workspace which contains neither. When the shipped data has no entry for the running model or the task, the skill SHALL say the rung is unevaluated rather than treat absence as a pass.

The running model is the model that produced the failure: the agent's own when the failure happened in the current session, otherwise the model the user names for the run that failed, which need not be the agent's. Looking up the agent's own model in that case would report the verdict of the model doing the troubleshooting as the cause of another model's failure.

The running model SHALL be looked up by its exact identifier, as the agent's host states it or as the user spells it. When that exact string is absent from the shipped data, the skill SHALL compare spellings instead. An entry belongs to the running model when both spellings are equal after the same normalisation is applied to each. That normalisation ignores:

- letter case and surrounding whitespace;
- routing and vendor prefixes, meaning everything up to the last `/`;
- a cloud provider's wrapping: a leading vendor segment with an optional region, and a trailing revision;
- a trailing date stamp carrying year, month and day, written compact or with dashes;
- a trailing bracketed variant qualifier.

It also reads a dash between two digits as a dot. A shorter trailing number, such as a year and month alone, is not a date stamp and SHALL be kept, because a vendor may number a version that way. Hosts spell one model several ways. Claude Code, for one, puts dashes between version digits and appends a date stamp where the data keys the same model with a dotted version under a vendor prefix. A verdict missed for that reason reads to the user as "unevaluated" when the data records a failure.

Normalised spellings SHALL be compared for equality, never as prefixes. A different version number names a different model and SHALL NOT inherit another version's verdict. When more than one entry matches, the skill SHALL choose none and report the rung as unevaluated, because picking one would report a neighbouring model's verdict as the user's.

#### Scenario: Verdicts consulted offline

- **WHEN** the ladder reaches the model rung with no network available
- **THEN** the verdicts are read from the skill's shipped data

#### Scenario: Model absent from the shipped data

- **WHEN** the running model has no entry in the shipped verdicts
- **THEN** the skill reports the rung as unevaluated for that model and continues down the ladder

#### Scenario: Failure from an earlier session on another model

- **WHEN** the agent runs as `example-5-5`, the user reports a failure from an earlier session they ran on `example-4-5-20251001`, and the shipped data holds both `lab/example-4.5` and `lab/example-5.5`
- **THEN** the skill uses the verdicts recorded under `lab/example-4.5`, not those under `lab/example-5.5`

#### Scenario: Host spelling differs from the data's key

- **WHEN** the host states the running model as `example-4-5-20251001` and the shipped data keys that model as `lab/example-4.5`
- **THEN** the skill uses the verdicts recorded under `lab/example-4.5`

#### Scenario: Short numeric suffix is not a date stamp

- **WHEN** the host states the running model as `example-large-2411` and the shipped data holds `lab/example-large` but no entry with that suffix
- **THEN** the skill keeps `-2411` as part of the name and reports the rung as unevaluated for that model rather than applying the `lab/example-large` verdict

#### Scenario: Newer version than any recorded

- **WHEN** the host states the running model as `example-5-5` and the shipped data holds `lab/example-5` but no 5.5 entry
- **THEN** the skill reports the rung as unevaluated for that model rather than applying the `lab/example-5` verdict

#### Scenario: Two entries match the same spelling

- **WHEN** two entries in the shipped data normalise to the running model's spelling
- **THEN** the skill applies neither verdict and reports the rung as unevaluated
