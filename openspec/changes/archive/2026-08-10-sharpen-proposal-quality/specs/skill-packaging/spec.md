# skill-packaging Delta

## MODIFIED Requirements

### Requirement: Uniform skill opening structure

Every shipped `SKILL.md` body SHALL open with exactly four blocks, in this order, before its first section heading:

1. **Purpose** — one or two sentences in the vocabulary of a person who has never read the repository, stating what the skill produces and for whom. It SHALL NOT restate, soften, or paraphrase any rule stated below it, because the first statement of a rule fixes that rule's scope.
2. **Workflow line** — a single line naming every skill in the set and the order of the main chain, with the containing skill's own name marked. The line SHALL be identical across all skills except for which name is marked, and SHALL mark exactly one name, which SHALL be the name of the skill whose file it appears in.
3. **Voice block** — a short block, byte-identical across all skills, fixing the agent's tone: neutral and constructive, never praising the user or their artifacts, never complimenting its own output, chat messages short and precise with findings stated plainly. The block constrains chat conduct only; it SHALL NOT alter what any skill checks, writes, or judges.
4. **Mandate** — the skill's agent-facing opening paragraph. It SHALL remain immediately followed by the paragraph that already followed it, so that a paragraph which elaborates or enforces a mandate is never separated from it.

The workflow line is orientation, not a dependency declaration: a skill SHALL remain functional when the siblings it names are not installed.

#### Scenario: Visitor lands on a single skill page

- **WHEN** a person opens one skill's rendered page without knowing the package
- **THEN** the first two blocks tell them what that skill does for them, that the other skills exist, and where the chain starts

#### Scenario: Purpose block would restate a rule

- **WHEN** a purpose block is written so that it also states a constraint the mandate below it states
- **THEN** the purpose block is rewritten to state the deliverable instead, leaving the constraint stated once, by the mandate

#### Scenario: Mandate has an enforcing paragraph

- **WHEN** a skill's mandate is followed by a paragraph that elaborates or mechanically verifies it
- **THEN** no header block is inserted between the two

#### Scenario: Skill added to the set

- **WHEN** a new skill joins the package
- **THEN** it opens with the same four blocks, and every existing skill's workflow line is updated so the set named on each page stays complete

#### Scenario: Skill installed without its siblings

- **WHEN** a skill is installed alone in a workspace
- **THEN** it performs its purpose, treating the sibling names in its workflow line as orientation rather than as available tools

#### Scenario: Voice block governs praise

- **WHEN** any skill reports a result in chat
- **THEN** the message contains no praise of the user or their material and no self-congratulation, per the voice block every skill carries

### Requirement: Opening structure and mandate wording enforced offline

The opening structure SHALL be enforced by the offline test suite rather than by convention. The suite SHALL fail when the workflow line differs between skills, when the marked name does not match the skill it appears in, when the voice block is missing from any skill or differs between skills, when the block order or the bounded length of the purpose block is violated, when a mandate is separated from the paragraph beneath it, or when a mandate's wording differs from a committed pinned copy of that mandate.

Changing a mandate SHALL therefore require editing its pinned copy, so the reword appears as an explicit diff under review instead of passing silently.

#### Scenario: Workflow line drifts on one skill

- **WHEN** one skill's workflow line is reworded, reordered, or left stale after the set changes
- **THEN** the offline suite fails naming that skill

#### Scenario: Sibling's line copied without re-marking

- **WHEN** a skill's workflow line marks a name other than its own
- **THEN** the offline suite fails naming that skill

#### Scenario: Voice block drifts on one skill

- **WHEN** one skill's voice block is reworded or removed
- **THEN** the offline suite fails naming that skill

#### Scenario: Mandate silently reworded

- **WHEN** a change alters the wording of a skill's mandate without updating that mandate's pinned copy
- **THEN** the offline suite fails naming the skill and the mandate

#### Scenario: Mandate deliberately revised

- **WHEN** a mandate is intentionally rewritten and its pinned copy is updated in the same change
- **THEN** the offline suite passes and the reword is visible as a diff in review

#### Scenario: Purpose block grows into a marketing section

- **WHEN** the material before the workflow line exceeds a single paragraph
- **THEN** the offline suite fails
