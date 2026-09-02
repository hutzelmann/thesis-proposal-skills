## MODIFIED Requirements

### Requirement: Single-context execution

The supervise run SHALL be a single-context task: one agent normalizes the submission, runs the check, judges the five substance tests and every review dimension in one pass, decides the tier, and curates the feedback, because the tier decision needs the tests judged together — at least three failing decisively, each with a reason no single revision round could repair it — and the curated points are chosen across all findings. Helper agents SHALL NOT be part of the skill's execution; following the import or literature-search sibling's instructions in the same context is not a helper. When the host nevertheless runs the task as a workflow, the skill SHALL cap it at three agents with fixed roles — one full review, one adversarial check of the review's fail verdicts, one optional reading of the proposal's own references block for citation consistency, without network access — and SHALL NOT assign one agent per substance test, per dimension, or per research question. The adversarial check informs the evidence bar; it SHALL NOT decide the tier, which stays with the main agent and, when borderline, the professor. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, so that it is read before a run is planned, and the whole section SHALL be pinned verbatim offline.

Whatever the host does, the main agent SHALL be the only writer of `<slug>.md`, `<slug>-review.md` and `<slug>-feedback.md`; the review file carries every finding regardless of how many a helper returned, and the feedback's load-bearing strengths are named by the main agent. A helper SHALL work from the normalized `<slug>.md` — never the submission, so no student identity reaches it — with the resolved workspace `guidelines.md` override and only the guideline sections its task needs, and SHALL return a verdict per substance test (decisive fail, uncertain, or pass, with one quotable finding per failed test and, for a decisive fail, why no single revision round could repair it), then at most five findings, each with severity, location, a one-sentence problem, a one-sentence suggestion and a quote of at most one sentence, location-only duplicates merged — no reasoning prose, no strengths list, no restated guidelines, unless the professor asks for full reasoning.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the supervise run as a multi-agent workflow
- **THEN** the run uses at most three agents in the fixed roles, every artifact is written by the main agent, and no helper reads the raw submission

#### Scenario: Helper verdicts feed the tier decision
- **WHEN** helpers return per-test verdicts with decisive/uncertain marks and one quotable finding each
- **THEN** the main agent applies the evidence bar and the borderline deferral exactly as without helpers, quoting one finding per test to the professor when the bar is not met

#### Scenario: Strengths stay with the main agent
- **WHEN** a helper's return carries no strengths, per the contract
- **THEN** the feedback's "What to keep" block is still present, written by the main agent from its own reading

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section, drops its helper-contract paragraph, or moves the section below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference
