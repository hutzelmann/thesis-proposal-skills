## ADDED Requirements

### Requirement: Stage handoff at stopping points

Every shipped skill SHALL carry a closing section, `## Handing over`, placed directly before the failure-path report section — and last in the skill that carries no report offer — that opens with one shared handoff block and continues with the skill's own exit condition and routes. The shared block SHALL define:

- **The milestone ladder**: seeded idea → complete draft → ready for supervisor discussion → handed in. A draft is complete when every canonical section is written and its open markers stand only where the student must decide or supply something. A proposal is ready for supervisor discussion when the mechanical check reports no errors and a review of its current text names no proposal blocker. It is handed in when a built document or hand-in export exists and the student sends it. Execution readiness SHALL be named as outside the ladder: the clarify-early items are settled during the thesis, not before approval.
- **When to hand over**: at a stopping point — a stage finished, a verdict given, or the user asking what to do now — also when the user said they cannot answer, and not again unasked while nothing has changed. A turn inside a dialogue that continues is not a stopping point.
- **The shape**: the message SHALL close with these lines and nothing after them — exactly one `Where it stands:` line (the proposal's position on the ladder and, in plain words, what blocks the next milestone), exactly one `Next:` line (one recommended step, its reason, and — where the user can trigger it — a quoted phrase they can send or a one-word approval), and zero to two alternatives, each an `Or:` line; a list of at most two items under one `Or:` label is the same thing, and a list of an anchored choice's options under `Next:` continues that line. The labels follow the chat language (German: `Stand:`, `Als Nächstes:`, `Oder:`).
- **Actions, not skills**: the step SHALL be named as an action in the user's terms, never by a skill's name; on approval the instructions of the skill that owns the step govern it, and where that skill is not installed the skill SHALL say so and state the step in words. The fixed wording of the failure-path report offer is exempt.
- **User control**: a handoff recommends and SHALL NOT act — no review finding applied, no missing choice supplied, nothing built, published or sent, no other skill run, unless the user approves that step.
- **Anchored decisions**: when the next step needs a choice only the student can make, the handoff SHALL quote what the student's own text already says, state what the choice changes, and offer at most three options the student's material supports plus a way out — never a bare open question, never an option the material does not contain.
- **Superseded reviews**: a review covers the text it judged. When the research questions, scope, method or contribution delta differ from what a review judged, or a passage one of its blockers cites has changed, the review is superseded, and the recommended step SHALL be a fresh review — never only the statement that no current review exists.

The block SHALL stay short enough that no body crosses the size limits, and each skill's own routes SHALL follow it in a few sentences rather than restating it.

#### Scenario: Review finished with blockers
- **WHEN** a review ends with two proposal blockers
- **THEN** the message closes with a `Where it stands:` line naming the blockers as what stands between the draft and supervisor discussion, one `Next:` line recommending a revision of those blockers with a phrase the user can send, and at most two `Or:` lines

#### Scenario: Nothing changed since the last handoff
- **WHEN** the user asks a side question after a handoff and nothing about the proposal changed
- **THEN** the answer does not repeat the handoff lines

#### Scenario: No skill names in the handoff
- **WHEN** the recommended step is a fresh review
- **THEN** the `Next:` line names it as a review of the current draft and contains neither a skill identifier nor the phrase "review skill"

#### Scenario: Approval crosses skills
- **WHEN** the user approves a recommended revision at the end of a review
- **THEN** the revision follows the instructions of the skill that owns writing, not the review skill's

#### Scenario: Decision put to the student
- **WHEN** a blocker can only be resolved by a choice of the student's
- **THEN** the handoff quotes the passage concerned, says what the choice changes, offers at most three options drawn from the student's own material plus a way out, and asks no unanchored question

#### Scenario: Review judged an earlier scope
- **WHEN** the proposal now carries two research questions and one site while the review beside it judged four research questions and two sites
- **THEN** the handoff says that the review judged the earlier version and recommends a fresh review of the current draft

#### Scenario: Execution detail is not a milestone
- **WHEN** a ready proposal leaves model versions and an audit sample size to be fixed during the thesis
- **THEN** the handoff places the proposal at ready for supervisor discussion and does not recommend settling those items before hand-in

#### Scenario: Handing over section misplaced
- **WHEN** a skill's `## Handing over` section is missing, follows the report section, or its opening block differs from the shared source
- **THEN** the offline test suite fails naming that skill

## MODIFIED Requirements

### Requirement: Cross-skill identical blocks materialized from one source

A block of `SKILL.md` prose that this specification requires to be identical across skills SHALL exist once as a dev-side source and be materialized into each skill's `SKILL.md` by the same automation that materializes synchronized file copies. The workflow line, the voice block, the stage handoff block, and the failure-path report offer SHALL be materialized this way.

Materialization SHALL be byte-preserving on adoption: converting a hand-maintained block into a materialized one SHALL leave every shipped `SKILL.md` unchanged, so that the change is provably a change of authorship and not of content.

Per-skill wording SHALL NOT be materialized, even where a committed copy of it exists. A mandate, a mandate's successor block, and a load-bearing pinned sentence are pinned precisely so that revising them requires a deliberate paired edit; generating them from the prose would make the pin restate whatever the prose says and confirm any reword, including an unintended one.

#### Scenario: Shared block reworded

- **WHEN** the voice block's source is reworded and the sync is run
- **THEN** every skill's voice block is rewritten from it, and the reword is reviewable as a single source diff

#### Scenario: Skill joins the set

- **WHEN** a new skill is added to the package
- **THEN** the set named in the workflow line is edited in one source, and every skill's workflow line is materialized from it

#### Scenario: Adoption leaves content unchanged

- **WHEN** a previously hand-maintained identical block is first materialized
- **THEN** no shipped `SKILL.md` changes content

#### Scenario: Per-skill wording proposed for materialization

- **WHEN** a mandate, mandate successor, or pinned sentence is proposed to be generated from the skill's prose
- **THEN** it remains hand-maintained, because a pin derived from what it guards guards nothing

#### Scenario: Handoff block reworded

- **WHEN** the stage handoff block's source is reworded and the sync is run
- **THEN** every skill's `## Handing over` section opens with the new wording, and the skill's own route sentences after it are left unchanged
