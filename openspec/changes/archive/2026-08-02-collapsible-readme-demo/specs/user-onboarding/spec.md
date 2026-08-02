## ADDED Requirements

### Requirement: Condensed session demo in README
The README SHALL show a time-condensed impression of the workflow (idea → ideate → literature search → write → check → publish) near the top, before the textual skill explanation, as a sequence of short quoted exchanges attributing each answer to the skill that produced it. The demo SHALL be plain markdown with no images, and SHALL be collapsed by default so that its summary lines alone convey the workflow order.

#### Scenario: Visitor grasps the tool in seconds
- **WHEN** a visitor opens the repository page without expanding anything
- **THEN** the collapsed demo summaries alone convey that an agent guides a vague thesis idea through literature search into a checked, publishable proposal

#### Scenario: Visitor reads the session
- **WHEN** the visitor expands a demo section
- **THEN** they see quoted exchanges between the student and named skills, rendered by any markdown viewer without downloading images

### Requirement: Authentic, synthetic demo content
The README demo SHALL be curated from a real agent session run on a synthetic fixture topic. It MUST NOT contain personal data or fabricated literature references; any papers shown MUST come from a real literature-search result, and the harvested session output backing them SHALL stay committed as an audit trail.

#### Scenario: Demo content audit
- **WHEN** the README demo text is compared against the committed harvested session output
- **THEN** every shown paper reference and proposal excerpt traces back to real session output on the synthetic topic, with only ordering and length condensed

## REMOVED Requirements

### Requirement: Visual workflow demo in README
**Reason**: The screenshot storyboard dominated the top of the README (three 1000px images, ~500 KB) and reached no audience beyond GitHub — skills.sh renders each `SKILL.md`, never the repository README, and shows no images at all.
**Migration**: Replaced by "Condensed session demo in README", which keeps the same workflow story as collapsible plain-markdown quotes.
