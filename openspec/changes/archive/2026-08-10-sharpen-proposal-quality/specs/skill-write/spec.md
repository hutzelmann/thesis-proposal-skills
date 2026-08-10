# skill-write Delta

## ADDED Requirements

### Requirement: Substance gate
Where the collected material (seed, notes, user input, references) does not support a substantive statement, the skill SHALL NOT generate generic prose to fill the gap: the gap becomes a visible `[TODO: …]` marker or the affected content is omitted, and the closing report SHALL state plainly which sections rest on thin material and point to the ideation skill (for missing idea substance) or the review skill (for the substance verdict). Text the skill generates SHALL be traceable to the material; well-sounding filler that would survive the guidance's swap test in reverse — text equally true of any thesis in the area — SHALL NOT be written.

#### Scenario: Hollow seed drafted honestly
- **WHEN** the seed carries a topic phrase but no delta, no object of study, and no method substance
- **THEN** the drafted sections carry TODO markers for the missing substance, no generic filler prose is produced, and the closing report names the gaps

#### Scenario: Material supports the section
- **WHEN** the notes record a concrete evaluation design for the methodology section
- **THEN** the skill writes the section from that material without any substance TODO

### Requirement: Density pass binding per writing pass
After every writing pass, before reporting, the skill SHALL re-read the produced or edited text against the guidance's information-density rule and delete sentences that carry no information essential to this thesis — scene-setting openers, truisms, restatements. This pass is binding like the mechanical error list: a writing pass is not complete while removable filler the skill itself can identify remains. When refining author-written text, density findings in untouched sections are reported as suggestions, never silently deleted, consistent with the surgical-edit rule.

#### Scenario: Own draft carries a truism
- **WHEN** the skill's fresh draft opens a section with a general claim true of any project in the field
- **THEN** the sentence is deleted before the pass is reported complete

#### Scenario: Author's filler in an untouched section
- **WHEN** a refinement pass notices removable filler in a section the request did not touch
- **THEN** the skill reports the sentences as removable in chat and leaves the text unchanged
