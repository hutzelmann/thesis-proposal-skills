## ADDED Requirements

### Requirement: Citation scope in writing passes
When drafting prior work, the skill SHALL group sources by the claim they support and compare them, and SHALL cite each source once per continuous use: the run opens with the author-in-text form, the following sentences refer back in words, and the source is cited again at a new paragraph, after another source or a claim of the thesis's own, and wherever a sentence would otherwise read as the thesis's own claim. These triggers are the guidance's. The skill SHALL NOT narrow them. Like the guidance's other writing rules, they are a default a workspace `guidelines.md` may override, for example where a program requires a citation on every sentence that draws on a source.

In a writing pass, the skill SHALL treat the check's repeated-citation warning as binding, the way it treats an error, unless the workspace guidance requires per-sentence citation. It SHALL resolve each warning by opening the run with the author-in-text form and referring back in words, or by merging the sentences into the comparison the paragraph is for. The skill SHALL NOT resolve the warning by deleting a citation or by dropping a source, because a sentence that loses its citation without a back-reference reads as the thesis's own claim. When refining, the surgical-edit rule governs this warning as it governs the density pass: findings in sections the request did not touch SHALL be reported as suggestions rather than rewritten.

#### Scenario: Several findings from one source
- **WHEN** the material supplies several findings from one publication
- **THEN** the draft cites it once at the start of the run and carries the following findings with back-references such as "they" or "their evaluation"

#### Scenario: Repeated-citation warning in a writing pass
- **WHEN** the check reports that a sentence in text the pass wrote or was asked to improve repeats the citation of the sentence before it
- **THEN** the skill rewrites the run before reporting the pass, and every source the paragraph cited is still cited

#### Scenario: Deletion is not a resolution
- **WHEN** removing the repeated citation would leave the sentence without a citation or a back-reference to its source
- **THEN** the skill adds the back-reference or keeps the citation instead of leaving the sentence unattributed

#### Scenario: Untouched section in a refinement
- **WHEN** a refinement asked for one section and the check reports repeated citations in another
- **THEN** the skill reports those findings as suggestions and leaves the untouched section as written

#### Scenario: Workspace requires per-sentence citation
- **WHEN** the workspace `guidelines.md` requires every sentence that draws on a source to carry its citation
- **THEN** the skill follows the workspace and does not treat the repeated-citation warning as binding
