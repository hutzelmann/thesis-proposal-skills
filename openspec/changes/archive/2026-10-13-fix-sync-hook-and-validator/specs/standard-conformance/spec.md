## MODIFIED Requirements

### Requirement: External conformance validator as a canary
The default test chain SHALL run the standard's reference validator over every skill directory, alongside the repository's own stricter checks.

The reference validator is the implementation that the standard's maintainers publish in the standard's own repository. A third-party port or re-implementation SHALL NOT stand in for it, whatever it is called or wherever it is published.

The validator SHALL be pinned by an identifier that cannot move, such as a full commit id, and never by a branch or tag name. The versions of the dependencies that decide what it accepts SHALL be pinned alongside it, so one pin always runs one validator. Updating the pin SHALL be a reviewed change, so movement in the standard arrives as a visible diff rather than silently.

#### Scenario: Skill violates the standard's format rules
- **WHEN** a skill's frontmatter or layout breaks a rule the reference validator checks
- **THEN** the conformance task fails even if the repository's own checks pass

#### Scenario: Standard evolves
- **WHEN** the pinned validator revision is bumped and the new revision rejects a previously accepted skill
- **THEN** the failure surfaces in the default chain and is resolved by a reviewed change, either conforming or recording a deliberate divergence

#### Scenario: Validator from another source
- **WHEN** the conformance task is configured to run a validator obtained from anywhere other than the standard's own repository, or a validator addressed by a name that can move
- **THEN** the offline suite fails and names the offending pin

#### Scenario: A validator dependency publishes a new release
- **WHEN** a library the pinned validator depends on publishes a new version
- **THEN** the conformance task keeps running the dependency versions recorded beside the pin until a reviewed change moves them
