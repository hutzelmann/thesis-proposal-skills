## ADDED Requirements

### Requirement: Cross-skill identical blocks materialized from one source

A block of `SKILL.md` prose that the specification requires to be identical across skills
SHALL exist once as a dev-side source and be materialized into each skill's `SKILL.md` by the
same automation that materializes synchronized file copies. The workflow line, the voice
block, and the failure-path report offer SHALL be materialized this way.

Materialization SHALL be byte-preserving on adoption: converting a hand-maintained block into
a materialized one SHALL leave every shipped `SKILL.md` unchanged, so that the change is
provably a change of authorship and not of content.

Per-skill wording SHALL NOT be materialized, even where a committed copy of it exists. A
mandate, a mandate's successor block, and a load-bearing pinned sentence are pinned precisely
so that revising them requires a deliberate paired edit; generating them from the prose would
make the pin restate whatever the prose says and confirm any reword, including an unintended
one.

#### Scenario: Shared block reworded

- **WHEN** the voice block's source is reworded and the sync is run
- **THEN** every skill's voice block is rewritten from it, and the reword is reviewable as a
  single source diff

#### Scenario: Skill joins the set

- **WHEN** a new skill is added to the package
- **THEN** the set named in the workflow line is edited in one source, and every skill's
  workflow line is materialized from it

#### Scenario: Adoption leaves content unchanged

- **WHEN** a previously hand-maintained identical block is first materialized
- **THEN** no shipped `SKILL.md` changes content

#### Scenario: Per-skill wording proposed for materialization

- **WHEN** a mandate, mandate successor, or pinned sentence is proposed to be generated from
  the skill's prose
- **THEN** it remains hand-maintained, because a pin derived from what it guards guards
  nothing

## MODIFIED Requirements

### Requirement: Functional self-containment
Each skill SHALL be functional standalone: installed alone, it fulfills its purpose without requiring any sibling skill. Shared guidance, structured data, and cross-skill scripts are provided through one of two declared paths:

1. **Synchronized copy** — the asset is materialized as a committed copy inside the consuming skill from a single dev-side source. A synchronized copy is either a whole file or a delimited region of a file. Whole-file copies carry a generated-file marker. A materialized region SHALL NOT carry one: the file it sits in is a rendered page, and a marker would appear to readers of that page. A region is instead located by a position this specification already fixes, so that its boundaries do not depend on an annotation a contributor can move or delete. Automated verification SHALL fail when a copy or a region drifts from its source.
2. **Sibling fallback** — the skill uses a sibling skill's files when that sibling is installed, and its SKILL.md SHALL document the degraded behavior used when the sibling is absent. This path is only permitted where the degraded mode still fulfills the skill's purpose; assets required for a skill's core function SHALL be synchronized copies.

#### Scenario: Shared guidance edited
- **WHEN** the shared source changes without re-materializing copies
- **THEN** the sync verification fails

#### Scenario: Sibling absent
- **WHEN** a skill with a declared sibling fallback runs in a workspace where the sibling skill is not installed
- **THEN** the skill performs its documented degraded behavior instead of failing opaquely

#### Scenario: Asset needed for core function
- **WHEN** a shared asset is required for a skill's core purpose rather than for enrichment
- **THEN** the skill ships it as a synchronized copy, not as a sibling fallback

#### Scenario: Materialized region in a rendered page
- **WHEN** a region of a `SKILL.md` is materialized from a shared source
- **THEN** the rendered page shows no generated-file marker, comment, or banner around it

#### Scenario: Region moved out of its fixed position
- **WHEN** a materialized region no longer sits at the position this specification fixes for it
- **THEN** the offline suite fails naming the skill, rather than materializing the block into the wrong place

### Requirement: Uniform skill opening structure

Every shipped `SKILL.md` body SHALL open with exactly four blocks, in this order, before its first section heading:

1. **Purpose** — one or two sentences in the vocabulary of a person who has never read the repository, stating what the skill produces and for whom. It SHALL NOT restate, soften, or paraphrase any rule stated below it, because the first statement of a rule fixes that rule's scope.
2. **Workflow line** — a single line naming every skill in the set and the order of the main chain, with the containing skill's own name marked. The line SHALL be identical across all skills except for which name is marked, and SHALL mark exactly one name, which SHALL be the name of the skill whose file it appears in. It SHALL be materialized from a single source, which carries the set and leaves the marked name to be filled per skill.
3. **Voice block** — a short block, byte-identical across all skills, fixing the agent's tone: neutral and constructive, never praising the user or their artifacts, never complimenting its own output, chat messages short and precise with findings stated plainly. The block constrains chat conduct only; it SHALL NOT alter what any skill checks, writes, or judges. It SHALL be materialized from a single source.
4. **Mandate** — the skill's agent-facing opening paragraph. It SHALL remain immediately followed by the paragraph that already followed it, so that a paragraph which elaborates or enforces a mandate is never separated from it. It is per-skill wording and SHALL NOT be materialized.

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
- **THEN** it opens with the same four blocks, and the set named on every page stays complete because each page's workflow line is materialized from the one source that was edited

#### Scenario: Skill installed without its siblings

- **WHEN** a skill is installed alone in a workspace
- **THEN** it performs its purpose, treating the sibling names in its workflow line as orientation rather than as available tools

#### Scenario: Voice block governs praise

- **WHEN** any skill reports a result in chat
- **THEN** the message contains no praise of the user or their material and no self-congratulation, per the voice block every skill carries

### Requirement: Opening structure and mandate wording enforced offline

The opening structure SHALL be enforced by the offline test suite rather than by convention. The suite SHALL fail when the workflow line differs from its source or marks a name other than the skill it appears in, when the voice block is missing from any skill or differs from its source, when the block order or the bounded length of the purpose block is violated, when a mandate is separated from the paragraph beneath it, or when a mandate's wording differs from a committed pinned copy of that mandate.

For the materialized blocks, identity across skills SHALL be established by materialization from a single source and verified against that source, not by comparison against a copy embedded in a test. The source is the one place the wording is stated, so a change to it is reviewable as one diff.

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

### Requirement: Uniform failure-path report offer

Every shipped skill except the one that assembles reports SHALL end a run that failed in a way it cannot resolve with a single offer to assemble a bug report. The offer SHALL be worded identically across those skills, SHALL be materialized from a single source, SHALL appear at most once in a session, and SHALL be an offer: no skill SHALL collect, assemble, or write report material without the user accepting.

The assembling skill SHALL NOT carry the offer at all. It is where the offer leads, so referring itself would be a loop rather than an offer, and its own unresolvable failure — a collector it cannot locate — is covered by the script-location rules that already bind every skill. Materialization SHALL therefore skip that skill rather than treat its absent offer as drift.

The offer SHALL fire on a script exiting non-zero, on a read-only skill detecting that the file it examined changed during its run, on a diagnostic failing repeatedly with no intervening user edit, and on a state the skill cannot proceed from. It SHALL NOT fire on ordinary findings: a proposal with errors is the diagnostic working, not a defect in it, and a skill that treats its own correct output as a bug trains users to ignore the offer.

#### Scenario: Shipped script exits non-zero

- **WHEN** a skill's script fails with a non-zero exit
- **THEN** the skill's report closes with the single offer to assemble a bug report

#### Scenario: Diagnostic reports findings

- **WHEN** a diagnostic skill completes normally and reports findings in the user's proposal
- **THEN** no report offer appears

#### Scenario: Offer declined

- **WHEN** the user does not take up the offer
- **THEN** the skill does not repeat it later in the session and collects nothing

#### Scenario: Offer wording drifts

- **WHEN** one skill's offer wording differs from the source it is materialized from
- **THEN** the offline test suite fails naming that skill

#### Scenario: The assembling skill carries the offer

- **WHEN** the skill that assembles reports contains the offer wording
- **THEN** the offline test suite fails, because that skill is the offer's destination

#### Scenario: Skill-specific sentence added after the offer

- **WHEN** a skill adds its own sentence about a defect particular to it in the closing section
- **THEN** the materialized offer remains byte-identical and the added sentence sits outside it
