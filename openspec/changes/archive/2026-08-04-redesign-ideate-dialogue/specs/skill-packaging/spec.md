## ADDED Requirements

### Requirement: Load-bearing sentences pinned offline
Beyond mandates, sentences whose exact wording carries security or behavioral weight SHALL be pinned: each designated sentence has a committed pinned copy, and the offline test suite SHALL fail when the skill prose no longer contains it verbatim. The pinned set SHALL include at least: every untrusted-data framing sentence, the ideation hard rule against asking for or supplying idea content, the tell-boundary sentence, the proposal anonymity rules, and the always-present `references:` key rule. Changing such a sentence therefore requires editing its pinned copy in the same change, making the reword an explicit diff under review.

#### Scenario: Untrusted-data framing reworded silently
- **WHEN** a change rephrases a pinned untrusted-data sentence in a SKILL.md without touching the pinned copy
- **THEN** the offline suite fails naming the skill and the sentence

#### Scenario: Deliberate reword reviewed
- **WHEN** a change updates both the prose and the pinned copy
- **THEN** the suite passes and the reword is visible as a paired diff under review
