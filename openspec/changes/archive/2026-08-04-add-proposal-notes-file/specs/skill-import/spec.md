## ADDED Requirements

### Requirement: Notes file seeded at import
The import skill SHALL create `<slug>.notes.md` beside the imported proposal and seed it with the knowledge the import produced but the proposal cannot carry: source content that did not map into the canonical sections (for example dropped work-plan phase detail beyond the kept boundary months), the gap list summarizing what the source did not supply, and an initial Next Focus naming the most important gaps to close first. Submission-blocking gaps continue to appear as `[TODO: …]` markers in the proposal; the notes file summarizes and prioritizes them, it does not replace them. Content copied into the notes file follows the same personal-data stripping rules as the proposal itself.

#### Scenario: Dropped work-plan detail preserved
- **WHEN** the source contains a phase-by-phase work plan whose boundary months go into the Timeline section
- **THEN** the dropped phase detail lands in the notes file instead of being reported only in chat

#### Scenario: Gap list becomes the initial focus
- **WHEN** the import leaves several TODO markers in the proposal
- **THEN** the notes Next Focus section names the gaps to close first, and the markers themselves remain in the proposal
