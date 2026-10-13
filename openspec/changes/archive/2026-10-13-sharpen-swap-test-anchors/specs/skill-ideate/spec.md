## ADDED Requirements

### Requirement: Named choices questioned Socratically
When the student's idea names a tool, system, platform or application domain in its working title, problem, research-question directions or goal, the skill SHALL ask once per name what about the thesis would change if a comparable one stood in its place. That is the guidance's swap test applied to the name, asked as a Socratic move anchored in the student's own words. The skill SHALL NOT name a particular alternative the student has not mentioned. The contrast belongs to the question; the alternative would be idea content. A name SHALL count as a concrete specific for the coverage aspects only once the student has said what the thesis depends on in it. When the student leaves the question open, the skill SHALL record it in the notes file as an open point and SHALL NOT supply the dependence itself. The open question SHALL NOT block seeding while the aspects hold other concrete specifics.

#### Scenario: Tool named as the vehicle
- **WHEN** the student's working title and a research-question direction name one agent framework, and nothing the student has said ties the idea to it
- **THEN** the skill asks once what about the thesis would change if a comparable framework stood in its place, naming no particular alternative

#### Scenario: Student anchors the name
- **WHEN** the student answers that the thesis evaluates that framework's own default configuration for the teams that run it
- **THEN** the name counts as a concrete specific and the question is not repeated

#### Scenario: Anchor left open
- **WHEN** the student cannot say what in the thesis depends on the name
- **THEN** the notes file records the open question, the name does not count toward an aspect having taken shape, and the skill generates no dependence of its own
