## ADDED Requirements

### Requirement: Hindsight leakage reported as a warning
The skill SHALL report as warnings (never hard failures, false positives acknowledged) prose that states the proposal's own work as already done: result verbs in the first person or with the work as subject — showed, found, demonstrated, outperformed, and their German equivalents — and quantitative outcomes stated as findings. A proposal describes work that has not happened, so such a sentence is either a draft written after the work began or a proposal derived from a finished thesis.

The check SHALL fire only on sentences carrying no citation. Reporting what prior work established is what the Contribution section is for, and a rule that cannot tell "@Rivera23 showed that scheduling reduces water use" from "we showed that scheduling reduces water use" would fire on every correctly written proposal. Each warning SHALL carry its line and quote the text it matched.

The skill SHALL NOT attempt to judge whether a research question is a settled claim in disguise. That reading requires knowing what the work found, which the document does not state; it belongs to the review skill's agent pass and to the reader.

#### Scenario: Result claim without a citation
- **WHEN** the body states that the work demonstrated an effect, in a sentence carrying no citation
- **THEN** the check emits a warning citing the line and quoting the matched text

#### Scenario: Result attributed to prior work
- **WHEN** the same claim is attributed to a cited reference
- **THEN** no warning is emitted

#### Scenario: Quantitative outcome stated as a finding
- **WHEN** the body reports a measured improvement as an achieved number, in a sentence carrying no citation
- **THEN** the check emits a warning

#### Scenario: Planned measurement
- **WHEN** the body states what will be measured and against which baseline
- **THEN** no warning is emitted, because the sentence describes a plan rather than an outcome

#### Scenario: Research question that reads like a conclusion
- **WHEN** a research question is phrased so that it presupposes its own answer
- **THEN** the mechanical check stays silent and the judgment is left to the review skill
