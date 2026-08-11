## MODIFIED Requirements

### Requirement: Audit-pattern regressions caught by tests
The risk patterns remediated in past audits SHALL be enforced by automated tests over the shipped skill content: no dynamic module loading from input-derived names, no credential lookup outside the documented locations, no instructions to mutate file permissions, no embedded execution of another skill's scripts, and no instructions that pass a secret value through the agent. The tests SHALL run in the default offline test suite.

A shipped script SHALL NOT execute a path it discovered in the user's workspace. Where a skill delegates work to a file the workspace supplies, the shipped script SHALL confine itself to discovering and reporting that file; running it belongs to the agent, which the user already directs. The single shipped script permitted to start a subprocess starts fixed document tools by constant name only, and this SHALL be enforced by the same offline test suite, so that widening it is a reviewed change rather than an incidental one.

#### Scenario: Remediated pattern reintroduced
- **WHEN** a change reintroduces one of the remediated patterns into a skill's shipped content
- **THEN** the offline test suite fails naming the file and the pattern

#### Scenario: Shipped script made to run a discovered file
- **WHEN** a change makes a shipped script execute a build definition it found in the workspace
- **THEN** the offline test suite fails, naming the script and the invariant
