# skill-ideate Delta

## MODIFIED Requirements

### Requirement: Seeds the proposal file
The skill SHALL seed the proposal file (per proposal-file-format) when the idea has converged — the coverage slots are filled — or when the user says "enough", whichever comes first; on convergence the skill SHALL offer seeding proactively rather than waiting for the user to end the session. The seed opens with the working title as the leading `# ` line and the subtitle paragraph beneath it, and carries: problem sketch, why it matters, candidate research-question directions as notes, open questions as `[TODO: …]` markers reserved for submission-blocking gaps, and a metadata block with any starter references found during grounding. A session that produced no idea content seeds no proposal file — its state lives in the notes file alone.

At the closing step the skill SHALL confirm the exact start and submission months, pre-filled from the preamble's months estimate, and record them as a note in the seeded body — never as a timeline section. The language and the degree level come from the preamble answers: the subtitle paragraph is `*Bachelor's Thesis Proposal*` / `*Master's Thesis Proposal*` for English and `*Exposé zur Bachelorarbeit*` / `*Exposé zur Masterarbeit*` for German, with a `*[TODO: …]*` subtitle only when the level was never given — the subtitle wording is what later tooling infers the language from, so it is written even in a seed. The skill SHALL read the captured state back in chat in a few lines before closing, and SHALL tell the user the file exists and what the write skill does next. If the provisional notes-file slug diverged from the working title, the notes file is renamed to match the seed's slug at this step.

When the session started from another finished thesis, that thesis SHALL be recorded: as a starter entry in the seed's `references` when it is publicly accessible, and in the notes file alone when it is not. The skill SHALL NOT invent publication metadata for an unpublished thesis in order to cite it.

#### Scenario: Convergence triggers a seeding offer
- **WHEN** problem, significance, candidate RQ directions, a plausible method, and feasibility within the stated months have all taken shape
- **THEN** the skill offers to seed the proposal file now, rather than continuing to provoke

#### Scenario: Session ends after ideation
- **WHEN** the ideation session concludes with idea content developed
- **THEN** a slug-named proposal file exists opening with the working title as its leading `# ` line, consumable by the write skill, and the notes file shares its slug

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
