## ADDED Requirements

### Requirement: Title assessed as its own dimension
The review SHALL assess the proposal's thesis title as a dimension of its own, against the guidance: whether it names a contribution and its object, whether it carries a tool, product, or vendor name as the instrument, whether it frames implementation work rather than research, whether it names a field rather than a thesis, and whether it carries marketing tone. Where the review flags the title it SHALL say that the title is printed on the study certificate and SHALL suggest between one and three abstracted alternatives, as an enumerated item like any other finding. A title whose named technology is the object of the proposal's own research questions SHALL NOT be flagged.

#### Scenario: Tool-named title reviewed
- **WHEN** the proposal's title names the framework used to build its prototype
- **THEN** the review carries an enumerated title item naming the certificate consequence and suggesting abstracted alternatives

#### Scenario: Title drifted from the research questions
- **WHEN** the title promises something the research questions do not address
- **THEN** the review flags the mismatch as a title finding

#### Scenario: Named technology is the research object
- **WHEN** the research questions are about the named technology itself
- **THEN** the review does not flag the title for naming it

## MODIFIED Requirements

### Requirement: Format-agnostic
The review SHALL NOT complain about section layout, ordering, headings, or markup conventions — structure compliance belongs to check. The proposal's thesis title is content, not layout, and is therefore in scope for the review despite living in the metadata block.

#### Scenario: Non-canonical structure
- **WHEN** the proposal uses a free-form section structure
- **THEN** the review addresses only content and arguments, with no structural complaints

#### Scenario: Metadata title assessed anyway
- **WHEN** the review reaches the metadata block
- **THEN** it assesses the title as content and stays silent about the block's markup
