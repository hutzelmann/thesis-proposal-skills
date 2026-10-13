## MODIFIED Requirements

### Requirement: Substance gate
Where the collected material (seed, notes, user input, references) does not support a substantive statement, the skill SHALL NOT generate generic prose to fill the gap: the gap becomes a visible `[TODO: …]` marker or the affected content is omitted, and the closing report SHALL state plainly which sections rest on thin material and point to the ideation skill (for missing idea substance) or the review skill (for the substance verdict). Text the skill generates SHALL be traceable to the material; well-sounding filler that would survive the guidance's swap test in reverse — text equally true of any thesis in the area — SHALL NOT be written.

The gate SHALL cover named choices as the guidance's swap test defines them. The skill SHALL NOT introduce a tool, system, platform or application domain into the title, the purpose statement, the research focus, a research question or the contribution's statements of what the thesis adds, unless the material states what the research depends on in it. Where the author's material names one there without that dependence, the skill SHALL keep the name and SHALL place a visible `[TODO: …]` marker asking for the dependence where the contribution would state it. It SHALL NOT invent the dependence. The closing report SHALL name the open swap-test blocker with its two repairs: state the dependence, or generalize the claim. Where the student states the dependence in the session — for instance as the reason for keeping a named technology in the title — the skill SHALL write it into the contribution or the research questions, so that the proposal carries it.

#### Scenario: Hollow seed drafted honestly
- **WHEN** the seed carries a topic phrase but no delta, no object of study, and no method substance
- **THEN** the drafted sections carry TODO markers for the missing substance, no generic filler prose is produced, and the closing report names the gaps

#### Scenario: Material supports the section
- **WHEN** the notes record a concrete evaluation design for the methodology section
- **THEN** the skill writes the section from that material without any substance TODO

#### Scenario: Decorative name in the seed
- **WHEN** the seed's working title and research-question directions name an agent framework, and neither the seed nor the notes say what the research depends on in it
- **THEN** the draft keeps the name, carries a TODO marker in the contribution section asking for the dependence, and the closing report names the open swap-test blocker with both repairs

#### Scenario: Implementation choice stays in the method
- **WHEN** the notes record that the prototype is built with a particular library and nothing else ties the research to it
- **THEN** the skill names the library in the methodology only, and introduces it into no title, research question or contribution statement

#### Scenario: Reason given in the session
- **WHEN** the student says the named framework stays in the title because the thesis evaluates its default configuration for the teams that run it
- **THEN** the skill writes that dependence into the contribution section rather than leaving it in the chat

### Requirement: Title negotiated once research questions exist
The skill SHALL judge the proposal's title against the guidance once the research questions are written, including a title inherited unchanged from an ideation seed, and SHALL NOT treat an inherited title as settled. Where the title matches an alarm class, the skill SHALL raise it in chat, state that the title is printed on the study certificate, and offer between one and three abstracted alternatives naming the contribution and its object. The skill SHALL write the student's chosen title, never a silent replacement, and where a named technology is retained the skill SHALL have the student's stated reason why the research depends on it, typically that the technology is the object of study. The skill SHALL write that reason into the contribution or the research questions, as the substance gate requires for named choices, and SHALL treat the title as settled for the session only once the proposal carries it; a name kept without a reason SHALL carry the substance gate's `[TODO: …]` marker.

#### Scenario: Seed title inherited unchanged
- **WHEN** the draft is written from a seed whose working title names a product carried as the instrument
- **THEN** the skill raises the title, names the certificate consequence, and offers abstracted alternatives before reporting the draft finished

#### Scenario: Student picks an alternative
- **WHEN** the student chooses one of the offered titles
- **THEN** the leading `# ` line carries that title and the slug is left alone unless the student asks for a rename

#### Scenario: Student keeps a named technology
- **WHEN** the student states that the named technology is the object of study
- **THEN** the title is written as the student chose it, the reason is written into the contribution or the research questions, and the point is not raised again in that session

#### Scenario: Student keeps a named technology without a reason
- **WHEN** the student keeps a named technology in the title and gives no reason why the research depends on it
- **THEN** the title is written as the student chose it and the contribution carries the substance gate's TODO marker asking for the dependence

#### Scenario: Title already academic
- **WHEN** the title names a contribution and its object with no alarm class matched
- **THEN** the skill leaves it alone and spends no turn on it
