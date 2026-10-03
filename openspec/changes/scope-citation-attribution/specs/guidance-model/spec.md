## ADDED Requirements

### Requirement: Citation scope
The guidance SHALL state how far a citation reaches and when a publication is cited again, so that every sentence's source stays recognisable without the same citation being repeated on consecutive sentences.

When consecutive sentences within a paragraph draw on the same publication, the guidance SHALL require citing it once: the run opens with the author-in-text form, and the sentences that follow carry the attribution in words — a pronoun or noun phrase referring back to the cited work or its authors — rather than with a repeated citation. The guidance SHALL require citing the publication again when a new paragraph starts, when another source or a claim of the thesis's own intervenes, and wherever a sentence would otherwise read as the thesis's own claim. Citing different subsets of sources on consecutive sentences is a change of source, not a repetition, and SHALL NOT be discouraged.

The guidance SHALL forbid removing a citation without leaving such a cue, and SHALL name the reason: a citation whose reach the reader cannot see makes borrowed content look like the thesis's own. The guidance SHALL identify a paragraph that needs one source in most of its sentences as a summary of that source rather than a thematic cluster, and SHALL direct its restructuring to the rule that prior work is organised thematically.

The existing prohibition on typing an author name in the prose SHALL stay. Continuation cues are pronouns and noun phrases, never a typed name. Whether a sentence still reads as attributed is a semantic judgement and SHALL remain prose guidance; no list of acceptable cues is encoded as structured guidance data.

#### Scenario: Same source on consecutive sentences
- **WHEN** three consecutive sentences in one paragraph each cite the same publication while the topic stays the same
- **THEN** the guidance identifies the repetition as overcitation and asks for one author-in-text citation that opens the run, followed by sentences that refer back in words

#### Scenario: Source switch is not repetition
- **WHEN** one sentence cites one publication and the next cites that publication together with another
- **THEN** both citations stay, because the set of sources changed

#### Scenario: The same source in a new paragraph
- **WHEN** a new paragraph continues to draw on the publication cited in the previous one
- **THEN** the guidance requires citing it again in the new paragraph

#### Scenario: Citation deleted without a cue
- **WHEN** repeated citations are removed so that the sentences after the remaining citation neither cite nor refer back to the source
- **THEN** the guidance identifies the unclear reach of the citation as the defect, not the earlier repetition, and asks for a cue or a citation

#### Scenario: One source carries the paragraph
- **WHEN** most sentences of a paragraph in the contribution section draw on a single publication
- **THEN** the guidance identifies the paragraph as a summary of that source and directs it to thematic restructuring
