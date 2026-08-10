# skill-troubleshoot delta: troubleshoot-prefilled-issue-url

## MODIFIED Requirements

### Requirement: Report stays local and is delivered by the user

An assembled report SHALL be written only into the user's own workspace, as files the user can read. The skill SHALL NOT transmit it, open an issue, post to any service, or offer to. Delivery — a public issue, an email, a hand-off to a supervisor — SHALL remain the user's decision and the user's action. When naming the issue option, the skill SHALL present a prefilled form URL for the repository's skill-defect issue template, constructed from the report's own short fields (which skill, the triage rung, what happened, the self-reported agent identity), URL-encoded as query parameters; fields too long for a URL SHALL be named as paste-in steps instead. The URL SHALL carry nothing beyond what the chosen disclosure level already placed into the report.

#### Scenario: Report finished

- **WHEN** the skill finishes assembling a report
- **THEN** the report exists as local files and the skill names the delivery options without performing any of them

#### Scenario: User asks the skill to submit it

- **WHEN** the user asks the skill to file the report for them
- **THEN** the skill states that it does not transmit reports and tells them where the files are

#### Scenario: Issue option carries a prefilled URL

- **WHEN** the report's self-reported fields are filled and the skill names the issue option
- **THEN** the option is a URL to the skill-defect issue form with the short fields prefilled from the report, the long fields named for pasting, and the user left to open, review, and submit it themselves
