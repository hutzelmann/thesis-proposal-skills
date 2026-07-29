# demo-recording Specification

## Purpose
Reproducible pipeline that renders the README demo images from committed, synthetic-content sources, so the demo can be regenerated and evolved without re-recording live sessions.
## Requirements
### Requirement: Reproducible demo content
The exact text content of every demo image SHALL be regenerable from committed source files (curated transcript plus render script) with one documented command per shot; capturing the terminal as an image is a documented manual screenshot step requiring no recording tooling.

#### Scenario: Contributor regenerates the demo
- **WHEN** a contributor edits the curated transcript and runs the documented render command in a terminal
- **THEN** the terminal shows the updated shot content, ready to screenshot, without recording a live agent session

### Requirement: Authentic, synthetic demo content
The demo transcript SHALL be curated from a real agent session run on a synthetic fixture topic. It MUST NOT contain personal data or fabricated literature references; any papers shown MUST come from a real literature-search result.

#### Scenario: Demo content audit
- **WHEN** the curated transcript is compared against the harvested session output
- **THEN** every shown paper reference and proposal excerpt traces back to real session output on the synthetic topic, with only ordering and length condensed

### Requirement: Agent-neutral presentation
The demo SHALL depict a generic agent-chat interaction and MUST NOT imitate the branded interface of a specific agent product.

#### Scenario: Rendered demo inspected
- **WHEN** the demo images are viewed
- **THEN** no specific agent product's interface chrome or branding is recognizable

### Requirement: Small plainly-committed images
The generated demo images SHALL be committed as ordinary git blobs (no LFS, no external hosting) and SHALL stay small in total (a few hundred KB) so README loads remain fast and checkouts need no extra tooling.

#### Scenario: Repository checkout without demo tooling
- **WHEN** anyone clones the repository with plain git
- **THEN** the demo images are present and the README renders them, with no other workflow affected
