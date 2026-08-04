## ADDED Requirements

### Requirement: Excluded literature recorded in the notes file
When a companion `<slug>.notes.md` exists, the literature-search skill SHALL record rejected candidates in its Excluded Literature section — entry identifier (DOI or title) plus a one-line reason — and SHALL NOT re-propose an entry that section already lists in a later search. Acceptance bookkeeping is unchanged: accepted entries go into the proposal's `references:` block as before. When no notes file exists, rejections MAY go unrecorded; the skill SHALL NOT create the notes file for this purpose alone.

#### Scenario: Rejected candidate not proposed twice
- **WHEN** a search surfaces a paper the notes Excluded Literature section already lists
- **THEN** the skill skips it without presenting it to the user again

#### Scenario: Rejection recorded with reason
- **WHEN** the user rejects a candidate during result review and a notes file exists
- **THEN** the Excluded Literature section gains the entry's identifier and a one-line reason
