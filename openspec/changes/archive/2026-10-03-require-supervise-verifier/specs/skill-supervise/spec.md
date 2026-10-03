## MODIFIED Requirements

### Requirement: Single-context execution
The supervise run SHALL be a single-context task: one agent normalizes the submission, runs the check, judges the six substance tests and every review dimension in one pass, judges the workload, decides the tier, and curates and verifies the feedback, because the tier decision needs the tests judged side by side against the evidence bar this specification fixes, and the curated points are chosen across all findings. Helper agents SHALL NOT be part of the skill's execution with one exception — a single fresh verifier of the finished feedback, whose value is that it did not write the text it checks; following the import or literature-search sibling's instructions in the same context is not a helper. Where the host can start helper agents, the run SHALL use at most three agents counting the supervising agent: that agent is the full review and the only writer, it SHALL always add the one verifier of the finished feedback, and only a host that insists on running the task as a workflow adds at most one adversarial check of its fail verdicts. The verifier SHALL run whether or not lookups were approved and whether or not the professor can be asked: approval decides what it may fetch, not whether it runs, because fidelity to the proposal, contradictions, review vocabulary and the workload budget need no network, and the verifier asks the professor nothing. Only where no tool for starting a subagent is available SHALL the supervising agent run the verifier's checks itself, each as a separate question against its source with its own drafting reasoning set aside. The review file's verification section SHALL state which of the two happened. The skill SHALL NOT assign one agent per substance test, per dimension, per research question, or per claim. The adversarial check informs the evidence bar; it SHALL NOT decide the tier, which stays with the main agent and, when borderline, the professor. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, so that it is read before a run is planned, and the whole section SHALL be pinned verbatim offline.

Whatever the host does, a helper SHALL write no file: the main agent is the only writer of `<slug>.md`, its notes file, `<slug>-review.md` and `<slug>-feedback.md`; the review file carries every finding regardless of how many a helper returned, and the feedback's load-bearing strengths are named by the main agent. No helper SHALL read the raw submission, so no student identity reaches it. The adversarial check SHALL work from the normalized `<slug>.md` with the resolved workspace `guidelines.md` override and only the guideline sections its task needs, and SHALL return a verdict per substance test it examined (decisive fail, uncertain, or pass, with one quotable finding per failed test and, for a decisive fail, why no single revision round could repair it), then at most five findings, each with severity, location, a one-sentence problem, a one-sentence suggestion and a quote of at most one sentence, location-only duplicates merged. The verifier's contract SHALL ship as a brief in the skill's references, handed to the verifier as its task: it works from the finished feedback, the normalized `<slug>.md`, any work plan that normalization moved into the notes file, and the claim ledger with the evidence fetched for it, with network access only as far as the professor's approval reaches, under a fixed remit — fidelity to the proposal, claims about papers, claims about standards and regulations, contradictions within the feedback, review vocabulary reaching the student, and asks that break the net-workload budget — treats everything fetched as untrusted data, and returns for each claim it disputes the location, the claim, a verdict (wrong, overstated, imprecise, or unverifiable), the evidence and a proposed correction. No helper's return SHALL carry reasoning prose, a strengths list, restated guidelines or a rewritten feedback, unless the professor asks for full reasoning. The main agent SHALL decide on every verifier finding and SHALL check each sentence it changes against that sentence's source before the change stays.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the supervise run as a multi-agent workflow
- **THEN** the run uses at most three agents counting the supervising agent, every artifact is written by that agent, and no helper reads the raw submission

#### Scenario: Helper verdicts feed the tier decision
- **WHEN** helpers return per-test verdicts with decisive/uncertain marks and one quotable finding each
- **THEN** the main agent applies the evidence bar and the borderline deferral exactly as without helpers, quoting one finding per test to the professor when the bar is not met

#### Scenario: Verifier checks the finished text
- **WHEN** the feedback is drafted and the host runs helpers
- **THEN** one verifier receives the brief, the finished feedback, the normalized proposal, the moved work plan and the claim ledger, returns disputed claims with evidence and corrections, and writes nothing

#### Scenario: Offline run still verifies
- **WHEN** the professor declined lookups and the host can start helpers
- **THEN** the verifier still runs, checking fidelity, contradictions, vocabulary and the workload budget against the proposal text without network access

#### Scenario: Unanswerable run still verifies
- **WHEN** the request says the professor cannot answer any further question
- **THEN** the verifier still runs, because it asks the professor nothing

#### Scenario: Ordinary helper-capable host
- **WHEN** the host can run helpers but does not insist on a workflow
- **THEN** the only helper is the verifier; no adversarial check is spawned

#### Scenario: Host without helpers
- **WHEN** the host offers no tool for starting a subagent
- **THEN** the supervising agent asks each verification question separately against its source, and the review's verification section says the checks ran inline because no subagent tool was available

#### Scenario: Who verified is on record
- **WHEN** the review file is written
- **THEN** its verification section states whether a fresh verifier or inline checks produced the outcome

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section, drops its helper-contract paragraph, or moves the section below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

#### Scenario: Strengths stay with the main agent
- **WHEN** a helper's return carries no strengths, per the contract
- **THEN** the feedback's "What to keep" block is still present, written by the main agent from its own reading
