## ADDED Requirements

### Requirement: Title tells reported as warnings
The deterministic script SHALL inspect the metadata `title:` value and report as warnings, never as errors: an implementation-framing opener in English or German; a term from the closed buzzword list in English or German; a trailing question mark; and a word count outside the documented bounds. Each finding SHALL name the matched tell and state that the title reaches the study certificate. These findings SHALL be warnings because the patterns can fire on a legitimate title and because the script cannot judge whether a named technology is the object of study.

#### Scenario: Implementation opener
- **WHEN** the title opens with an implementation-framing phrase such as an English development opener or its German equivalent
- **THEN** the check emits a warning naming the opener and the certificate rationale, and the run does not fail on that finding

#### Scenario: Buzzword present
- **WHEN** the title carries a term from the documented buzzword list
- **THEN** the check emits a warning naming the term

#### Scenario: Question-form title
- **WHEN** the title ends in a question mark
- **THEN** the check emits a warning naming the certificate rationale

#### Scenario: Word count out of bounds
- **WHEN** the title falls below the documented minimum for the proposal's language or above the documented maximum word count
- **THEN** the check emits a warning naming the count, the bound it crossed, and the certificate rationale

#### Scenario: German title at the German minimum
- **WHEN** a `lang: de` proposal carries a compound title shorter than the English minimum but at or above the German one
- **THEN** no word-count warning is emitted

#### Scenario: Title written as a block scalar
- **WHEN** the metadata `title:` carries a YAML folded or literal block indicator and its text continues on the following lines
- **THEN** no title tell is applied, because the value the check can read is not the title

#### Scenario: Clean academic title
- **WHEN** the title names a contribution and its object within the bounds and matches no tell
- **THEN** no title warning is emitted

#### Scenario: Title findings never fail the run
- **WHEN** the only findings are title tells
- **THEN** the run reports them under warnings and exits successfully

### Requirement: Agent pass judges title quality
The agent pass SHALL judge the title against the guidance classes the patterns cannot reach — above all whether a proper noun in the title names a tool, product, vendor, or company carried as the instrument, and whether the title names a research field rather than a thesis. Where it flags the title, the skill SHALL offer between one and three abstracted alternatives and SHALL state that a named technology is acceptable only where the student can say it is the object of study. The skill SHALL report title judgement under the agent-pass bucket, never as mechanically verified.

#### Scenario: Tool name carried as instrument
- **WHEN** the title names a framework or product used to build the artefact and no pattern matched it
- **THEN** the agent pass flags it with abstracted alternatives, under the flagged-for-the-agent-pass bucket

#### Scenario: Named technology as object of study
- **WHEN** the proposal's research questions are about the named technology itself
- **THEN** the agent pass says so and does not flag the title
