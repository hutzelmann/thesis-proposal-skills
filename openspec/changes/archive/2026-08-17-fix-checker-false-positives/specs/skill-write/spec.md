## MODIFIED Requirements

### Requirement: Self-verification before reporting
The skill SHALL ship the mechanical check as a synchronized copy and SHALL run it over the produced or edited proposal before reporting a writing pass complete, fixing every error it reports and re-running until only tolerated findings remain. Three findings are explicitly not "fixed": a reference-count shortfall is reported to the user because inventing a publication is forbidden; open `[TODO: …]` markers stay because they are the honest record of what the material did not supply; and a finding the skill can demonstrate is a false positive is reported rather than worked around, because the author's content is correct as written.

Correcting markup remains permitted where markup is the actual defect — a code identifier in prose is marked as code. Rewording the author's terminology, and deleting a reference, a citation or a sentence, SHALL NOT be used to silence a finding: that trades a wrong finding for a real defect. The skill SHALL name the finding it is leaving, state why it is wrong, and name the troubleshoot skill as the route to a bug report.

#### Scenario: Check finds a structural error in fresh output
- **WHEN** the check reports an error on the file the skill just wrote (a drifted section title, an unterminated metadata block, a cited key missing from `references`, a missing `(RQn)` reference)
- **THEN** the skill corrects the file and re-runs the check before reporting, and the report states what the check still finds

#### Scenario: Check reports a reference shortfall
- **WHEN** the only remaining error is that the proposal cites fewer references than required
- **THEN** the skill reports the shortfall and suggests the literature-search skill instead of adding sources the material did not carry

#### Scenario: Open TODO markers remain
- **WHEN** the check warns about open `[TODO: …]` markers recording gaps the source material did not fill
- **THEN** the skill leaves the markers in place and lists them in its report

#### Scenario: Check reports a demonstrable false positive
- **WHEN** the check reports a code identifier written in prose as an undefined citation key
- **THEN** the skill marks the identifier as code, leaves the author's wording intact, and neither invents a reference nor deletes an existing one

#### Scenario: A finding cannot be resolved by markup
- **WHEN** a finding is wrong and no markup correction resolves it
- **THEN** the skill leaves the document as written, reports which finding it is leaving and why, and names the troubleshoot skill
