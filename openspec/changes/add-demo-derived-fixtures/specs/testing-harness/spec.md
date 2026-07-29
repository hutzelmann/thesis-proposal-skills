## ADDED Requirements

### Requirement: Publish filter regression coverage
The harness SHALL cover the publish skill's pandoc filters with regression tests, including at least one fixture whose research-question list contains an in-text citation; the filter output MUST contain the citation resolved rather than an unprocessed citation key. Tests requiring external converters SHALL be skipped cleanly when those tools are absent.

#### Scenario: Citation inside a research question
- **WHEN** the rq-filter regression test runs with pandoc available
- **THEN** the typst output wraps each research question and contains no unresolved citation keys

### Requirement: Session-derived fixtures
Fixtures MAY be curated from real skill-session output when the session used a synthetic topic. Such fixtures MUST be audited against the committed session log, MUST NOT contain personal data, and follow the same oracle rules as invented fixtures.

#### Scenario: Fixture curated from a demo session
- **WHEN** a session-derived fixture is added to the corpus
- **THEN** its content traces to a committed session log, contains no personal data, and ships with an `expected.json` oracle
