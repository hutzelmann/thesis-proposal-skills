## ADDED Requirements

### Requirement: Citation scope in writing passes
When drafting prior work, the skill SHALL group sources by the claim they support and compare them, and SHALL cite each source once per continuous use: the run opens with the author-in-text form, the following sentences refer back in words, and the source is cited again only at a new paragraph or a change of source.

In a writing pass, the skill SHALL treat the check's repeated-citation warning as binding, the way it treats an error. It SHALL resolve each one by opening the run with the author-in-text form and referring back in words, or by merging the sentences into the comparison the paragraph is for. The skill SHALL NOT resolve the warning by deleting a citation or by dropping a source, because a sentence that loses its citation without a back-reference reads as the thesis's own claim.

#### Scenario: Several findings from one source
- **WHEN** the material supplies several findings from one publication
- **THEN** the draft cites it once at the start of the run and carries the following findings with back-references such as "they" or "their evaluation"

#### Scenario: Repeated-citation warning in a revision
- **WHEN** the check reports that a sentence repeats the citation of the sentence before it
- **THEN** the skill rewrites the run before reporting the pass, and every source the paragraph cited is still cited

#### Scenario: Deletion is not a resolution
- **WHEN** removing the repeated citation would leave the sentence without a citation or a back-reference to its source
- **THEN** the skill adds the back-reference or keeps the citation instead of leaving the sentence unattributed
