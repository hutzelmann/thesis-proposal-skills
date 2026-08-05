## ADDED Requirements

### Requirement: Thesis title quality
The guidance SHALL govern the proposal's own thesis title, stating that it is printed on the student's final study certificate and therefore outlives the document. A title SHALL name what is contributed and what it is contributed about, at a level of abstraction that stays true when the tool used to produce it is replaced. It SHALL stand on its own: the rendered title page carries title and subtitle, but the certificate carries the title alone, so the title SHALL NOT depend on the subtitle or on any surrounding context to be understood. It SHALL state its subject rather than pose a question, and SHALL stay within the documented word bounds, whose minimum is per language because German compounds into one noun what English spreads over several. A concrete technology, product, vendor, or company name MAY appear only as a scope qualifier, and only once the student has stated why that technology is the object of study rather than the instrument of it.

#### Scenario: Tool named as the instrument
- **WHEN** a title names the framework, library, product, or platform used to build the artefact
- **THEN** the guidance requires an abstracted formulation naming the contribution and its object instead

#### Scenario: Tool named as the object of study
- **WHEN** the research question is about that technology itself, as in a systematic literature review of one platform's operator patterns or a user study of one specific IDE
- **THEN** the guidance permits the name as a scope qualifier, on the record that the student stated the technology is the object of study

#### Scenario: Certificate standalone reading
- **WHEN** the title is read without the subtitle or the study program
- **THEN** it still states what was researched

### Requirement: Title alarm classes
The guidance SHALL name four classes of problematic title: a tool, product, vendor, or company name carried as the instrument; implementation framing that states building work rather than a contribution; vagueness or grandiosity that names a research field rather than a thesis; and marketing, buzzword, or clickbait tone borrowed from non-academic writing.

#### Scenario: Implementation framing
- **WHEN** a title reads as a work order, such as an opener declaring the development or implementation of a system
- **THEN** it falls under the implementation-framing class

#### Scenario: Field named instead of thesis
- **WHEN** a title names a whole research field with no stated object or contribution
- **THEN** it falls under the vagueness class

#### Scenario: Marketing tone
- **WHEN** a title carries promotional vocabulary
- **THEN** it falls under the marketing class

### Requirement: Title alarm is raised and justified, never silently blocked
Where a title matches an alarm class, guidance SHALL require the agent to raise it explicitly, to state that the title reaches the certificate, and to offer between one and three abstracted alternatives. The agent SHALL NOT silently rewrite the title and SHALL NOT refuse to proceed. A title carrying a named technology SHALL be retained only against the student's stated justification that the technology is the object of study; absent that justification the agent SHALL keep recommending the abstracted alternative.

#### Scenario: Student justifies the named technology
- **WHEN** the student states why the named technology is the object of study
- **THEN** the title is retained and the alarm is not repeated for that reason

#### Scenario: Student gives no justification
- **WHEN** the student neither justifies the name nor accepts an alternative
- **THEN** the agent records the recommendation and proceeds without overwriting the student's title

#### Scenario: Silent rewrite forbidden
- **WHEN** an agent judges a title problematic
- **THEN** it never replaces the title without saying so and never presents the replacement as the student's own choice

## MODIFIED Requirements

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, the timeline size constraint, research-question list conventions, and the mechanically matchable thesis-title tells (implementation-opener patterns, a closed buzzword list, and word-count bounds, each in English and German). All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy, whether the timeline actually names a timeframe, and whether a name in the title denotes a tool at all) SHALL remain prose guidance for agents.

#### Scenario: Semantic rule stays prose
- **WHEN** a rule concerns argument quality rather than document skeleton
- **THEN** it appears only in prose guidance and is never encoded as structured check data

#### Scenario: Timeframe recognition stays prose
- **WHEN** the question is whether a timeline section states a real timeframe, given that students write `SoSe 2027`, `WS 2026/27`, `Q3`, or "winter semester"
- **THEN** no list of accepted date formats is encoded as structured data, and the judgement stays with the agent

#### Scenario: Tool recognition stays prose
- **WHEN** the question is whether a proper noun in the title names a tool, product, or vendor
- **THEN** no list of tool names is encoded as structured data, because the set is unbounded, and the judgement stays with the agent
