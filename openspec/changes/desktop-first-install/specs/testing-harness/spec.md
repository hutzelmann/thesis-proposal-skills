# Spec Delta

## ADDED Requirements

### Requirement: Install prompt probed on the dev runner

The dev runner SHALL carry a probe that hands the shared install prompt, exactly as the documentation presents it, to the real host binary in an isolated home directory, with the repository's installer and the working tree's skills served from a local address in place of the default branch so the probe measures the working tree and reaches no public service. It SHALL run twice:

- **unanswered** — the request is the prompt alone. The verdict SHALL pass only when the agent asks the scope question and nothing has been installed into the isolated home.
- **pre-answered** — the request is the prompt followed by the student's answer choosing all projects. The verdict SHALL pass only when every shipped skill sits byte-identical in each user-level target directory, each holds an install record, and no skill file was written by any means other than the installer.

The verdicts SHALL be functions covered by offline tests against recorded outcomes, like every other dev-runner verdict. The probe SHALL NOT join the offline suite or CI, because it needs a host install and a subscription.

#### Scenario: Agent skips the scope question

- **WHEN** the unanswered run installs skills without having asked where
- **THEN** the probe fails, naming the skipped question

#### Scenario: Pre-answered run installs

- **WHEN** the pre-answered run completes
- **THEN** the probe checks the isolated home's user-level skill directories for the full shipped set, byte-identical, with an install record in each

#### Scenario: Agent copies files by hand

- **WHEN** skill files appear in a target directory without an install record, or with contents differing from the working tree
- **THEN** the probe fails, naming the directory
