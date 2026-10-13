## MODIFIED Requirements

### Requirement: Seeds the proposal file
The skill SHALL seed the proposal file (per proposal-file-format) when the idea has converged — the coverage slots are filled — or when the user says "enough", whichever comes first; on convergence the skill SHALL offer seeding proactively rather than waiting for the user to end the session. The seed opens with the working title as the leading `# ` line and the subtitle paragraph beneath it, and carries: problem sketch, why it matters, candidate research-question directions as notes, open questions as `[TODO: …]` markers reserved for submission-blocking gaps, and a metadata block with any starter references found during grounding or fetched at seeding. A session that produced no idea content seeds no proposal file — its state lives in the notes file alone.

At the closing step the skill SHALL confirm the exact start and submission months, pre-filled from the preamble's months estimate, and record them as a note in the seeded body — never as a timeline section. The language and the degree level come from the preamble answers: the subtitle paragraph is `*Bachelor's Thesis Proposal*` / `*Master's Thesis Proposal*` for English and `*Exposé zur Bachelorarbeit*` / `*Exposé zur Masterarbeit*` for German, with a `*[TODO: …]*` subtitle only when the level was never given — the subtitle wording is what later tooling infers the language from, so it is written even in a seed. The skill SHALL read the captured state back in chat in a few lines before closing, say that the file exists, and close with the stage handoff (skill-packaging): the recommended next step is a full draft from the seed when grounding identified the closest prior work the contribution can be stated against, and a literature search on the idea's core terms first when it did not — the other step is the alternative. A session that ends at an impasse hands over to the offline steps it suggested, never to a draft. If the provisional notes-file slug diverged from the working title, the notes file is renamed to match the seed's slug at this step.

When the session started from another finished thesis, that thesis SHALL be recorded: as a starter entry in the seed's `references` when it is publicly accessible, and in the notes file alone when it is not. The skill SHALL NOT invent publication metadata for an unpublished thesis in order to cite it.

When the session started from a published paper, the paper SHALL always be recorded as a starter entry in the seed's `references`, built from a metadata record fetched in this session — the Crossref record of its DOI, its arXiv entry, or its DBLP entry. With lookup consent, the skill SHALL fetch that record before writing the seed when grounding has not already fetched it, SHALL check that the record's title and authors match the paper, and SHALL take every bibliographic field from that record — never from memory, and never a bibliographic field the record did not carry; the entry's `id` follows the guidelines' reference-key convention. Only when no matching record could be fetched in the session — lookups declined, or no matching record found — SHALL the paper be recorded as a line in the notes file instead, and no TODO marker in the seed SHALL stand for it. Either way, the notes file SHALL name the paper as the closest prior work.

#### Scenario: Convergence triggers a seeding offer
- **WHEN** problem, significance, candidate RQ directions, a plausible method, and feasibility within the stated months have all taken shape
- **THEN** the skill offers to seed the proposal file now, rather than continuing to provoke

#### Scenario: Session ends after ideation
- **WHEN** the ideation session concludes with idea content developed
- **THEN** a slug-named proposal file exists opening with the working title as its leading `# ` line, consumable by the write skill, and the notes file shares its slug

#### Scenario: Seeded with the closest prior work identified
- **WHEN** the session seeds the proposal and grounding identified the work the contribution is stated against
- **THEN** the closing handoff recommends a full draft from the seed, offers a literature search as an alternative, and names neither step by a skill name

#### Scenario: Seeded without prior work to argue against
- **WHEN** the session seeds the proposal but grounding found nothing close, or ran ungrounded
- **THEN** the closing handoff recommends a literature search on the idea's core terms before drafting

#### Scenario: Impasse hands over offline
- **WHEN** the session ends at an impasse without seeding
- **THEN** the handoff recommends the offline steps it suggested and recommends no draft

#### Scenario: Timeframe confirmed while seeding
- **WHEN** the preamble recorded roughly four months and the user confirms March to June at the seeding step
- **THEN** the seed file records the months as a note, carries no timeline section, and the writing skill does not ask again

#### Scenario: German proposal seeded
- **WHEN** the preamble answers were German and Master's level
- **THEN** the seed's subtitle paragraph reads `*Exposé zur Masterarbeit*` and the metadata block carries no `lang` key

#### Scenario: Nothing to seed
- **WHEN** the session ends with no topic developed
- **THEN** no proposal file is created and the notes file records where things stopped

#### Scenario: Published source thesis recorded as a reference
- **WHEN** the session started from a thesis that is publicly retrievable
- **THEN** the seed's `references` carries a starter entry for it

#### Scenario: Unpublished source thesis recorded in the notes file
- **WHEN** the session started from a thesis that is not publicly accessible
- **THEN** the notes file names it as the session's origin and the seed's `references` carries no invented entry for it

#### Scenario: Foundation paper seeded from a fetched record
- **WHEN** the session started from a published paper and its DOI record was fetched during the session
- **THEN** the seed's `references` carries a starter entry whose bibliographic fields all come from that record, and the notes file names the paper as the closest prior work

#### Scenario: Record fetched at seeding
- **WHEN** the session started from a published paper, lookups were allowed, and grounding never fetched the paper's own record
- **THEN** the skill fetches that record before writing the seed and builds the starter entry from it, rather than falling back to the notes file

#### Scenario: Fetched record does not match the paper
- **WHEN** the record a lookup returns carries a different title or different authors than the paper
- **THEN** the skill builds no entry from it, and when no matching record is found the paper is recorded in the notes file

#### Scenario: No record fetched for the foundation paper
- **WHEN** the session started from a published paper and no metadata record for it could be fetched in the session, because lookups were declined or no matching record was found
- **THEN** the seed's `references` carries no entry for the paper, no TODO marker stands for it, and the notes file records it in a line naming it the closest prior work
