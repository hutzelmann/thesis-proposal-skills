## MODIFIED Requirements

### Requirement: Output bounded by its source, and reported as such
The skill SHALL report what the thesis could not supply rather than compensating for it: research questions the thesis never stated are recovered from its contribution claims and marked as candidates rather than presented as the thesis's own; a methodology outside the closed set is reported rather than force-fitted; a timeline is stated from the thesis's own start and submission months, or marked when the thesis states none. The skill SHALL verify its own output with the mechanical check before reporting, and SHALL NOT present its result as reviewed: quality judgment belongs to a review and to the reader. The report SHALL close with the stage handoff (skill-packaging), recommending a review of the derived proposal once the check reports no errors, and the step that resolves the leading gap otherwise.

#### Scenario: Thesis states no research questions
- **WHEN** the thesis contains no explicit research questions
- **THEN** candidates recovered from its contribution claims are marked as candidates

#### Scenario: Methodology outside the closed set
- **WHEN** the thesis's method does not match any methodology the guidance allows
- **THEN** the skill reports the mismatch and marks the section rather than choosing the nearest label silently

#### Scenario: No dates in the source
- **WHEN** the thesis states neither a start nor a submission month
- **THEN** the timeline section carries a marker and no month is written on the source's behalf

#### Scenario: Run completes
- **WHEN** the proposal has been written and the check reports no errors
- **THEN** the skill has run the mechanical check over it, reports what the check still finds, and hands over with a review of the derived proposal as the recommended step rather than certifying the result
