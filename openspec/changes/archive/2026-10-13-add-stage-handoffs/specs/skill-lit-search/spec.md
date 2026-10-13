## ADDED Requirements

### Requirement: Search converges and hands over

Broad searching SHALL end when the contribution delta and every research question — or, before a draft exists, every candidate direction — has at least one accepted source behind it, or when a search round, by keyword or by snowballing, adds no accepted entry. After that, the skill SHALL search only for a gap it names. The reference count SHALL NOT be a reason to continue: the minimum is the check's to report, and the claim-backed merge rule stays binding however far below it the block is.

The report SHALL close with the stage handoff (skill-packaging): without a draft, the recommended step is the full draft; with a draft and newly merged entries, a writing pass that cites them where a claim needs them; when a research question remains unbacked after saturation, the handoff names that gap and puts its resolution as an anchored decision — a narrower question, a targeted search, or the student's own sources.

#### Scenario: Claims covered
- **WHEN** a round leaves the delta and every research question backed by an accepted source and no draft exists
- **THEN** the skill stops broad searching and the handoff recommends a full draft from the seed and these sources

#### Scenario: Saturated round
- **WHEN** a snowballing round yields candidates of which none is accepted
- **THEN** the skill reports the round as saturated and does not start another broad round on its own

#### Scenario: Below the reference minimum but covered
- **WHEN** every claim is backed and the reference block is still below the check's minimum
- **THEN** the skill does not merge entries without a claim to reach the minimum, and the handoff names the shortfall as the check's finding rather than as a reason to keep searching

#### Scenario: Unbacked research question after saturation
- **WHEN** a research question still has no accepted source after a saturated round
- **THEN** the handoff names that gap and offers its resolution as an anchored choice rather than recommending another broad search
