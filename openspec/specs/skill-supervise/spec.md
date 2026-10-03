# skill-supervise Specification

## Purpose
Supervisor-side feedback on raw student submissions: normalize whatever arrives, curate the most pressing findings into paste-ready draft feedback, and steer the student into the proposal toolchain.

## Requirements

### Requirement: Raw submission intake and normalization

The skill SHALL accept a raw student submission in any form it is handed — PDF, Word export, pasted text, or an already-standard proposal file — and SHALL normalize non-standard input to the standard single-file proposal format with the same guarantees the import skill gives: personal data stripped, gaps marked, references carried over. The normalized file SHALL be named by an idea slug and placed in the professor's workspace beside their other proposals. The skill SHALL NOT build a student registry, SHALL NOT record student identity in any artifact it writes, and SHALL NOT manage artifact lifecycle beyond the single run — retention and deletion stay manual.

#### Scenario: Pasted email fragment
- **WHEN** the professor hands the skill half a page of pasted email text describing a thesis idea
- **THEN** the skill produces a slug-named standard-format proposal file with gaps marked, and proceeds to feedback

#### Scenario: PDF submission
- **WHEN** the professor points the skill at a submitted PDF
- **THEN** the skill runs the import pipeline, strips personal data, and continues from the resulting standard-format file

#### Scenario: No identity professor-side
- **WHEN** the submission carries the student's name, matriculation number, or contact data
- **THEN** no artifact the skill writes contains that data — the idea file is identified by slug only

### Requirement: Findings reused from check and review, curated to pressing points

The skill SHALL derive findings from the same sources the student-facing skills use — the mechanical check and the content-level review rubric, judged against the workspace guidelines override where one exists — and SHALL NOT introduce a separate quality rubric of its own; choosing which findings reach the student is curation, not a separate bar. For the feedback, the skill SHALL curate the combined findings to the three to five points that most block a viable thesis, each phrased as a direction rather than a prescribed fix.

Findings about format and the toolchain's document conventions — author, supervisor or company data, a work plan or Gantt chart, a chapter outline, the length of the timeline, page counts, section names, the style of reference links — SHALL stay in the professor-side review file and SHALL NOT reach the feedback, unless the workspace guidelines explicitly ask for them in the feedback. Language quality SHALL become a point only when it blocks understanding of the substance.

Each point SHALL locate what it addresses in the proposal, say why it matters for this thesis, and give the direction; a judgement SHALL NOT stand in the feedback without its reason. The feedback SHALL be written in the student's vocabulary rather than the review's: substance-test names and review shorthand are translated into what they mean for this proposal. The opening, the points and the strengths SHALL NOT contradict one another. The feedback SHALL name load-bearing strengths — parts that are sound and must be kept — SHALL NOT contain generic praise, and SHALL carry no action item inside the strengths block.

#### Scenario: Many findings, few points
- **WHEN** check and review together yield a dozen findings
- **THEN** the feedback carries at most five curated points, ranked by how much each blocks a viable thesis, and the remaining findings appear only in the professor-side review file

#### Scenario: Supervisor override respected
- **WHEN** the workspace carries a guidelines override with the professor's own requirements
- **THEN** findings are judged against the override, matching what the student-facing skills would report

#### Scenario: Strength named, flattery absent
- **WHEN** the submission contains a workable core design amid weak surroundings
- **THEN** the feedback states what is sound and should be kept, and contains no generic praise of the student or the material

#### Scenario: Format finding stays professor-side
- **WHEN** the submission carries the student's name, a chapter outline and a phase-by-phase Gantt chart, and the workspace guidelines say nothing about format in feedback
- **THEN** the review records those findings, and the feedback contains no remark asking the student to remove or shorten any of them

#### Scenario: Workspace asks for format remarks
- **WHEN** the workspace guidelines state that format findings belong in the feedback
- **THEN** format findings may reach the feedback under the usual curation

#### Scenario: Shorthand verdict explained
- **WHEN** the review judges a research question sound
- **THEN** the feedback says what makes it sound for this proposal — what it asks, why its answer is open, how the method answers it — rather than a bare "sound as it stands"

#### Scenario: Strength and point reconciled
- **WHEN** a draft's strengths block praises a part that one of its points calls imprecise
- **THEN** the contradiction is resolved before hand-over, so the student reads one judgement of that part

### Requirement: Verdict expressed as proposal state
The feedback SHALL open with a verdict expressed as the state of the proposal and never as a commitment on the professor's behalf. The student-facing tiers are: **ready**, phrased as requiring no substantial revisions; **needs revision**, directing the student to address the enumerated points and resubmit; and **idea stage** (German: Ideenphase), stating that the material is an idea that has not yet reached the proposal stage. The idea-stage tier SHALL couple the standard a proposal must meet with an assurance anchored in a named, true strength of the submission and a feed-forward to ideation as the designed next step — never framed as failure, never softened into revision advice. The statement that revision alone will not produce a proposal SHALL be composed in the feedback's own words and grounded in what the specific submission is missing; it SHALL NOT render the skill's instruction wording as feedback text and SHALL NOT refer to the proposal standard's elements by count or as an enumerated list. The professor-side review file SHALL keep the review skill's blunt three-tier vocabulary unchanged.

The idea-stage tier SHALL only be assigned automatically when the failure is evidence-clear: at least three of the six substance tests fail decisively, each with a stated reason why no single revision round can repair it. A necessity-test failure SHALL NOT count toward that bar: material that serves no research question is removable in place, so it never evidences a missing thesis core. When the internal review reaches no-viable-core without meeting that bar, the verdict decision SHALL be deferred to the professor rather than taken by the skill. The skill SHALL NOT promise meetings, approvals, deadlines, or any other supervisor action.

#### Scenario: Ready without commitment
- **WHEN** the submission passes review with no substantial findings
- **THEN** the feedback states that no substantial revisions are needed from the reviewer's side and leaves the next step to the professor

#### Scenario: Evidence-clear idea stage
- **WHEN** at least three substance tests fail decisively and no single revision round could repair them
- **THEN** the feedback opens with the idea-stage verdict, names the proposal standard, anchors an assurance in a true strength, and directs the student to ideation — without asking the professor first

#### Scenario: Necessity failure does not lower the tier
- **WHEN** only two substance tests fail decisively and the necessity test fails as well
- **THEN** the evidence bar is not met, the necessity failure is not counted toward it, and the tier decision follows the borderline path rather than becoming idea stage

#### Scenario: Blunt vocabulary stays professor-side
- **WHEN** the internal review concludes no viable thesis core
- **THEN** the review file says so in those words while the feedback renders the tier as idea stage

#### Scenario: Plainness statement in the feedback's own words
- **WHEN** an idea-stage feedback states that revision alone will not produce a proposal
- **THEN** the statement names what this submission is missing in the feedback's own words, rather than translating the skill's instruction sentence or pointing at the standard's elements by count

### Requirement: Student-facing feedback with disclosure and steering

The feedback SHALL be the only student-facing artifact: a paste-ready draft, written professor-side as a feedback file named after the proposal slug, that the professor delivers as text through their own channel — an email reply or a learning platform's feedback field. The skill SHALL NOT assemble a send-package and SHALL NOT ask the professor to attach any file. The feedback SHALL be written in the language of the submitted proposal; when the message that accompanied the submission is written in another language, the chat wrap-up SHALL offer a version in that language. The feedback SHALL name for each curated point the skill that addresses it, as a plain word.

The feedback SHALL carry light markup at most — bold runs and plain numbered or lettered lists — and SHALL carry no heading, no blockquote and no code markup, because the paste channel renders none of them reliably.

Every source the feedback names that the submitted proposal does not already cite SHALL carry a locator that resolved in this run: a `https://doi.org/` URL for a paper, and the issuing body's official page for a standard or a regulation. A source the proposal already cites needs no locator. Locators SHALL NOT count toward the feedback's length.

The feedback body SHALL aim at about 1,200 words, not counting locators and the closing note. Above that, detail SHALL move into the professor-side review before any blocking point is shortened, and the chat wrap-up SHALL report the length. The target is advisory: it SHALL NOT cut a blocking point.

The feedback SHALL close with a single closing note, maintained as a shared verbatim snippet in English and German and quoted whole into the feedback in the language of the submission. The closing note SHALL be one paragraph that both discloses in plain language that the feedback was prepared with an AI assistant and that every decision about the thesis stays with the student, and points at the skill installation source, noting that the guide there assumes no prior AI-assistant experience. The disclosure SHALL claim no more than that: in particular no claim that the assistant follows the program's guidelines. The closing note SHALL join the two through availability only — that tools of the same kind are freely available — and SHALL NOT name specific assistants, quote install commands, or prescribe the student's next step.

Because the professor delivers the feedback as plain text into a channel that renders no markup, the closing note SHALL carry no markup: no blockquote, no emphasis, no heading. It SHALL open with a plain run-in label — "Note:" in English, "Hinweis:" in German — and SHALL NOT be split across paragraphs. The German snippet SHALL name the artifact "Rückmeldung".

Literature in the feedback is governed by the requirement "Literature grounded by consent"; the feedback SHALL carry no separate starter-literature block.

#### Scenario: German submission
- **WHEN** the submission is written in German
- **THEN** the feedback, its skill pointers, and the closing note are in German, and the closing note names the artifact "Rückmeldung"

#### Scenario: Message in another language
- **WHEN** the proposal is written in English and the student's accompanying email in German
- **THEN** the feedback is in English and the wrap-up offers a German version in one line

#### Scenario: Point steers to a skill
- **WHEN** a curated point concerns thin literature grounding
- **THEN** the point names the literature-search skill as the way to address it, as a plain word without code markup

#### Scenario: Markup stays light
- **WHEN** the feedback is assembled
- **THEN** it carries no heading line, no blockquote line and no backtick, while bold tier words and point titles are allowed

#### Scenario: Standard named with its issuer page
- **WHEN** a point names a regulation the proposal does not cite
- **THEN** the regulation's official page follows its first mention, and the page resolved during the run

#### Scenario: Long draft trimmed into the review
- **WHEN** a draft body runs well past the length target
- **THEN** secondary detail — extra standards, citation-use observations, optional asks — moves into the review first, no blocking point is dropped, and the wrap-up states the final length

#### Scenario: Disclosure and pointer arrive as one paragraph
- **WHEN** the feedback is assembled
- **THEN** its final paragraph states that it was prepared with an AI assistant and that every decision about the thesis stays with the student, and points at the installation source in the same paragraph, in wording that assumes no prior AI exposure and makes no claim about guideline compliance

#### Scenario: Closing note survives a plain-text channel
- **WHEN** the professor pastes the feedback into an email reply or a learning platform's feedback field
- **THEN** the closing note reads as prose opening with "Note:" or "Hinweis:", with no blockquote marker, emphasis marker, or heading marker reaching the student

#### Scenario: Closing note stays minimal
- **WHEN** the feedback closes with the closing note
- **THEN** it is the shared snippet, linking the repository and stating availability, with no install command, no assistant names, and no prescribed next step

#### Scenario: Starter literature offered, not imposed
- **WHEN** the outcome is idea-stage and the literature-search sibling is installed
- **THEN** no end-of-run starter-literature offer is made and no list is appended: literature enters the feedback only under "Literature grounded by consent" — approval asked once at the start of the run, papers woven into the points from verified lookups

### Requirement: Draft-only delivery and feedback separation

The skill SHALL NOT send, publish, or transmit anything; the feedback SHALL be presented as a draft for the professor to edit and deliver as text through their own channel — an email reply or a learning platform's feedback field. The full review file and the normalized proposal file SHALL remain professor-side beside the feedback file and SHALL NOT be presented as student-facing; the review file SHALL be presented under its own name — the review — and never described as feedback; nothing beyond the feedback text reaches the student.

#### Scenario: Run completes
- **WHEN** the skill finishes a submission
- **THEN** nothing has left the machine, and the chat summary tells the professor to review and edit the feedback draft before delivering it as text through their own channel

#### Scenario: Learning-platform delivery
- **WHEN** the submission arrived through a learning platform and the professor returns feedback in that platform's feedback field
- **THEN** the feedback works as pasted text with nothing to attach, and no artifact assumes an email reply

#### Scenario: Review never wears the feedback name
- **WHEN** the chat summary or any artifact refers to the professor-side review file
- **THEN** it is called the review, never the feedback, so the professor cannot mistake it for the text to paste

#### Scenario: Professor-only content stays out
- **WHEN** the feedback is drafted
- **THEN** the blunt review vocabulary and the review file's contents are absent from it, and no send-package directory is produced

### Requirement: Borderline verdict deferred to the supervisor

When the internal review reaches no-viable-core but the evidence bar is not met, the skill SHALL pause before writing the feedback and put the decision to the professor as a guided choice: needs-revision feedback emphasizing re-grounding, idea-stage feedback, or reading the professor-side review file first and deciding after. The question SHALL summarize the split evidence — which substance tests failed, which are uncertain, with a finding excerpt each — so the professor can decide without leaving the chat. Evidence-clear cases (either direction) SHALL NOT trigger the question. When the professor cannot be asked (a non-interactive run, or the user declines to decide), the skill SHALL default to the needs-revision feedback — in doubt, for the student.

#### Scenario: Borderline pauses for the professor
- **WHEN** the review concludes no-viable-core but only two substance tests fail decisively
- **THEN** the skill presents the split evidence and the three choices, and writes the feedback only after the professor picks

#### Scenario: Clear case skips the question
- **WHEN** the evidence bar is met
- **THEN** the feedback is written without a deferral question

#### Scenario: Undecidable defaults constructive
- **WHEN** the deferral cannot be answered
- **THEN** the feedback takes the needs-revision path

### Requirement: Level-calibrated feedback bar
The drafted feedback SHALL be calibrated to the degree level the submission's subtitle states: a Master's proposal missing a statement of what will be new is always asked for one; a Bachelor's proposal is never asked for a novelty claim, and one it makes is engaged on its merits rather than removed. The same calibration applies to research-question origin, literature stance, and scope-for-the-months. When the submission does not state a level, the draft SHALL apply the level-independent bar and note the unset level once — as a point for the student, not a guess.

#### Scenario: Master submission missing the delta
- **WHEN** a submission subtitled as a Master's thesis promises only competent application in its contribution close
- **THEN** the drafted letter asks for the statement of what the thesis will add

#### Scenario: Bachelor submission held to its own bar
- **WHEN** a submission subtitled as a Bachelor's thesis has a bounded application promise and level-appropriate derived research questions
- **THEN** the drafted letter raises no novelty demand and no research-question-origin concern

#### Scenario: Level unset in the submission
- **WHEN** the submission's subtitle matches no canonical wording
- **THEN** the draft judges against the level-independent bar and includes one line asking the student to state the degree level in the subtitle

### Requirement: Single-context execution
The supervise run SHALL be a single-context task: one agent normalizes the submission, runs the check, judges the six substance tests and every review dimension in one pass, judges the workload, decides the tier, and curates and verifies the feedback, because the tier decision needs the tests judged side by side against the evidence bar this specification fixes, and the curated points are chosen across all findings. Helper agents SHALL NOT be part of the skill's execution with one exception — a single fresh verifier of the finished feedback, whose value is that it did not write the text it checks; following the import or literature-search sibling's instructions in the same context is not a helper. Where the host can start helper agents, the run SHALL use at most three agents counting the supervising agent: that agent is the full review and the only writer, it SHALL always add the one verifier of the finished feedback, and only a host that insists on running the task as a workflow adds at most one adversarial check of its fail verdicts. Where the host cannot start helpers, the supervising agent SHALL run the verifier's checks itself, each as a separate question against its fetched source with its own drafting reasoning set aside. The skill SHALL NOT assign one agent per substance test, per dimension, per research question, or per claim. The adversarial check informs the evidence bar; it SHALL NOT decide the tier, which stays with the main agent and, when borderline, the professor. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, so that it is read before a run is planned, and the whole section SHALL be pinned verbatim offline.

Whatever the host does, a helper SHALL write no file: the main agent is the only writer of `<slug>.md`, its notes file, `<slug>-review.md` and `<slug>-feedback.md`; the review file carries every finding regardless of how many a helper returned, and the feedback's load-bearing strengths are named by the main agent. No helper SHALL read the raw submission, so no student identity reaches it. The adversarial check SHALL work from the normalized `<slug>.md` with the resolved workspace `guidelines.md` override and only the guideline sections its task needs, and SHALL return a verdict per substance test it examined (decisive fail, uncertain, or pass, with one quotable finding per failed test and, for a decisive fail, why no single revision round could repair it), then at most five findings, each with severity, location, a one-sentence problem, a one-sentence suggestion and a quote of at most one sentence, location-only duplicates merged. The verifier SHALL work from the finished feedback, the normalized `<slug>.md`, any work plan that normalization moved into the notes file, and the claim ledger with the evidence fetched for it, with network access only as far as the professor's approval reaches, under a fixed remit — fidelity to the proposal, claims about papers, claims about standards and regulations, contradictions within the feedback, review vocabulary reaching the student, and asks that break the net-workload budget — and SHALL return for each claim it disputes the location, the claim, a verdict (wrong, overstated, imprecise, or unverifiable), the evidence and a proposed correction. No helper's return SHALL carry reasoning prose, a strengths list, restated guidelines or a rewritten feedback, unless the professor asks for full reasoning. The main agent SHALL decide on every verifier finding and SHALL check each sentence it changes against that sentence's source before the change stays.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would orchestrate the supervise run as a multi-agent workflow
- **THEN** the run uses at most three agents counting the supervising agent, every artifact is written by that agent, and no helper reads the raw submission

#### Scenario: Helper verdicts feed the tier decision
- **WHEN** helpers return per-test verdicts with decisive/uncertain marks and one quotable finding each
- **THEN** the main agent applies the evidence bar and the borderline deferral exactly as without helpers, quoting one finding per test to the professor when the bar is not met

#### Scenario: Verifier checks the finished text
- **WHEN** the feedback is drafted and the host runs helpers
- **THEN** one verifier receives the finished feedback, the normalized proposal, the moved work plan and the claim ledger, returns disputed claims with evidence and corrections, and writes nothing

#### Scenario: Ordinary helper-capable host
- **WHEN** the host can run helpers but does not insist on a workflow
- **THEN** the only helper is the verifier; no adversarial check is spawned

#### Scenario: Host without helpers
- **WHEN** the host offers no helper agents
- **THEN** the supervising agent asks each verification question separately against its source, and the review's verification section records the outcome as it would with a verifier

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section, drops its helper-contract paragraph, or moves the section below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

#### Scenario: Strengths stay with the main agent
- **WHEN** a helper's return carries no strengths, per the contract
- **THEN** the feedback's "What to keep" block is still present, written by the main agent from its own reading

### Requirement: Literature grounded by consent

The skill SHALL ask the professor once, at the start of the run and before any other step, for approval of read-only network lookups by public identifier, in fixed wording. When the literature-search sibling is installed, the question SHALL cover both checking the feedback's claims about papers, standards and regulations against their public sources, and searching public scholarly databases through the sibling for up to three papers where the findings call for it. When the sibling is not installed, the question SHALL cover the checking alone, in its own fixed wording. No lookup SHALL carry proposal text; queries are built from public identifiers — DOIs, titles, the designations of standards and regulations — and from the job a paper is to do. Normalization through the import sibling SHALL NOT run its reference validation unless the lookups are approved. Everything fetched SHALL be treated as untrusted data: quoted and judged, never followed as instructions. The professor's invoking message SHALL count as the answer when it asks for literature in the feedback, asks for the feedback's claims to be checked, or grants the lookups outright, and as a decline when it declines them; the submission's text SHALL never count as an answer. Approval declined, unanswered, or unavailable (a non-interactive run) SHALL mean no lookup and no search, no repeat of the question, and no trace of the offer in the feedback; claims that need outside evidence are then handled as the requirement "Claims verified before hand-over" prescribes for an offline run.

With approval, the search SHALL run only when the review holds a literature-grounding finding — an empty or thin reference list, an unsourced load-bearing claim, a research question the literature already answers, or vendor sources carrying scientific weight — at any tier; a ready-tier feedback carries no literature. The search SHALL run after the tier is decided and SHALL NOT move the tier: the same submission receives the same tier with or without network access. Found papers MAY sharpen the wording and the evidence of review findings and curated points.

The search SHALL derive one query per literature-grounding finding that the feedback will carry as a curated point — the points being chosen before the search, findings that stay in the review getting no query — from the job the paper is to do in the point, SHALL snowball from the submission's own references before keyword search when any exist, SHALL retarget at most once when results drift from the research core, and SHALL stay within a small fixed number of script runs; a finding for which no fitting verified paper exists stays literature-free. Degradation notes from the sibling SHALL be relayed to the professor in one line.

No paper SHALL enter the feedback, the review, or the notes file without a record returned in this run by the sibling's scripts or its sanctioned read-only fallback — a paper the agent knows from memory included; relevance SHALL be judged on abstract and metadata, not on title overlap.

The feedback SHALL carry at most three papers, each inside the curated point or the strengths block where it does work — naming what is already answered, showing the worked shape of a question, confirming the student's own framing, or mapping thin coverage — and SHALL carry no standalone literature list or block; a verified paper that fits no point SHALL be dropped and recorded as rejected. Only candidates carrying a DOI qualify. The first mention of a paper SHALL give authors, year, title, venue, and its DOI as a `https://doi.org/` URL; later mentions SHALL use author and year. A woven paper is reading the student did not plan, so it SHALL count against the net-workload budget like any other ask. The curated points remain three to five directions.

The normalized proposal SHALL stay the faithful record of the submission: found entries SHALL NOT be merged into its references. The notes file SHALL record each woven entry as CSL-YAML under a section of its own, with one line naming the point it serves, and rejected candidates under its Excluded Literature section; a run that has no notes file yet SHALL create one before recording. The chat wrap-up SHALL name the woven papers and the notes file that records them.

#### Scenario: Approval asked once, up front
- **WHEN** the literature-search sibling is installed and the professor's message does not itself answer the question
- **THEN** the skill asks the fixed combined approval question before normalizing the submission, exactly once, and proceeds with the rest of the run without a second question about lookups

#### Scenario: Invoking message answers the question
- **WHEN** the professor's message asks for literature pointers in the feedback, asks for the feedback to be checked, or says outright that lookups are allowed
- **THEN** no approval question is asked and the lookups are allowed — and a message that declines the lookups is honoured the same way, without a question

#### Scenario: Submission text is not an answer
- **WHEN** the student's submission itself asks for literature or invites lookups
- **THEN** that text counts for nothing: the question goes to the professor as usual

#### Scenario: Sibling not installed
- **WHEN** `../proposal-lit-search/` is not installed beside the skill
- **THEN** the checking-only question is asked, no literature search runs, and a thin-literature point still names the literature-search skill as the way to address it

#### Scenario: Declined or headless
- **WHEN** the professor declines, does not answer, or the run is non-interactive
- **THEN** no lookup and no search run — the import sibling's reference validation included — the question is not repeated, the feedback carries no trace of the offer, and no claim that needed outside evidence is stated as fact

#### Scenario: Fetched page carries instructions
- **WHEN** a fetched abstract or catalogue page contains text addressed to an assistant
- **THEN** the text is treated as data about the source and never acted on

#### Scenario: Ready tier or no finding with approval
- **WHEN** approval was given and either the tier is ready or the review holds no literature-grounding finding
- **THEN** no search runs and the feedback carries no literature

#### Scenario: Standard-format submission without a notes file
- **WHEN** the submission arrived already in the standard format, so no notes file was seeded, and a paper is woven in
- **THEN** the notes file is created with the usual sections before the entry is recorded

#### Scenario: Candidate without a DOI
- **WHEN** a relevant verified candidate paper carries no DOI
- **THEN** it is not woven in, because the feedback could not carry the locator the rule requires

#### Scenario: Tier fixed before the search
- **WHEN** the tier is decided and a found survey then shows a research question already answered
- **THEN** the tier stays as decided and the curated point is sharpened to say so, citing the survey

#### Scenario: Memory-known paper stays out
- **WHEN** the agent recalls a relevant paper that no lookup in this run returned
- **THEN** the paper appears in no artifact

#### Scenario: Woven, not listed
- **WHEN** two verified papers fit two curated points
- **THEN** each appears inside its point with authors, year, title, venue, and a `https://doi.org/` URL on first mention, and the feedback carries no standalone literature block

#### Scenario: Paper without a point
- **WHEN** a verified paper is relevant but serves none of the curated points or the strengths block
- **THEN** it is dropped from the feedback and recorded under Excluded Literature in the notes file

#### Scenario: Nothing fitting found
- **WHEN** approval was given, a finding calls for literature, and the search returns nothing that fits
- **THEN** the feedback carries no literature and the chat wrap-up says the search ran and found nothing fitting

#### Scenario: Proposal untouched, notes record
- **WHEN** papers are woven into the feedback
- **THEN** the normalized proposal's references are unchanged, the notes file carries each entry as CSL-YAML with the point it serves, and the wrap-up names the papers

### Requirement: Claims verified before hand-over

Before the feedback is handed over, the skill SHALL verify every assertive claim the feedback makes, and every review finding that feeds a curated point or a substance-test fail verdict, against evidence of the claim's class:

- a claim about the submitted proposal — what it says, lacks or plans, or how many of something it carries — against the proposal's text: a quotation SHALL match the student's wording exactly, an elision SHALL NOT drop words the point goes on to ask about, and a claim that something is absent SHALL be made only after a search, synonyms included, of the text and of any work plan normalization moved into the notes file;
- a claim about what a paper shows — a paper the student cites included — against that paper's abstract or text fetched in this run, never against its title, and no further than the fetched text supports;
- a claim about what a standard, regulation or framework requires, covers or defines against its primary text or its issuing body's own page fetched in this run, never a clause, scope or obligation from memory;
- a figure — a count, a duration, a sum — computed rather than estimated in prose.

Judgement and advice are not fact claims and SHALL be phrased as the reviewer's view. A claim that cannot be verified SHALL be removed or rephrased as a question for the student; it SHALL NOT be stated as fact. A correction adopted after verification is itself a claim and SHALL be checked against its source before it stays. The professor-side review file SHALL carry a short verification section listing contradicted, partly supported and unverifiable claims first, each with the source checked, and the chat wrap-up SHALL name every claim that stayed unverified. When verification refutes a claim that underpinned a substance-test fail verdict, the finding SHALL be removed and the tier decided again under the unchanged rules. A decisive fail SHALL rest on the proposal's own text and the reviewer's judgement, never on a claim about a paper, standard or regulation that only a lookup could settle, so that the tier never depends on whether lookups were approved.

#### Scenario: Absence claim searched first
- **WHEN** a draft point says the proposal plans no evaluation of its model
- **THEN** the proposal text is searched first, and when it does plan one the point engages what is planned rather than calling it missing

#### Scenario: Elision keeps the answer
- **WHEN** a point quotes the student with an ellipsis and then asks by whom a step is performed
- **THEN** the quotation does not elide the words that already name who performs it

#### Scenario: Cited paper judged by its abstract
- **WHEN** the feedback characterizes what a paper on the student's reference list does
- **THEN** the characterization rests on the paper's fetched abstract or text and claims nothing beyond it, and a judgement from the title alone does not appear

#### Scenario: Regulation claim from its primary text
- **WHEN** the feedback states what a regulation requires of an organisation in the student's sector
- **THEN** the statement rests on the regulation's official text fetched in this run, and the review's verification section names that source

#### Scenario: Unverifiable claim becomes a question
- **WHEN** a claim about a paywalled standard cannot be checked against its text or its issuer's public description
- **THEN** the feedback does not state it as fact — it drops it or asks the student to check it — and the wrap-up lists it as unverified

#### Scenario: Verifier correction re-checked
- **WHEN** the verifier proposes replacement wording for a disputed sentence
- **THEN** the replacement is checked against its source before it enters the feedback

#### Scenario: Offline run
- **WHEN** the professor declined the lookups or the run is non-interactive
- **THEN** claims about papers, standards or regulations that the proposal's own text does not support are absent from the feedback or phrased as questions, and the verification section marks them unverified

#### Scenario: Tier independent of lookups
- **WHEN** a method-fit failure could be argued from what a cited regulation requires
- **THEN** the decisive verdict rests on the proposal's own text, the regulation claim at most sharpens the point, and the same tier results with or without lookup approval

#### Scenario: Refuted premise removes its finding
- **WHEN** verification shows that a passage the review called missing is present in the proposal, and that finding was one of the decisive fails behind an idea-stage tier
- **THEN** the finding is removed and the tier is decided again by the evidence bar and the borderline rule

### Requirement: Workload volume check

Before the tier is decided, the skill SHALL judge whether the submitted plan fits the time available at the declared degree level, and SHALL record the judgement in the review file as a work-package table: each package that the method and any work plan describe, what it depends on, what drives its size, and a coarse estimate in weeks marked as an estimate. A work plan or Gantt chart moved out of the proposal during normalization SHALL be read as evidence for this table. A size the plan depends on but does not state — a number of items to process, of participants, of systems, a start date that hinges on a pending registration — SHALL be named as an unknown and become a question for the student, asked in the scope paragraph when there is one and otherwise inside the point it bears on. The total SHALL be set against the months the student's own plan states and the degree-level scope expectation of the guidelines, and SHALL yield one of three verdicts: fits, tight, or over-scoped. The skill SHALL NOT take workload figures from shipped constants: credits and durations belong to the program.

When the verdict is over-scoped and the tier is not idea stage, the feedback SHALL say so directly after the verdict and before the points, and SHALL offer two or three alternative cuts — each stating what it keeps, what it drops, and what it costs — labelled with letters rather than numbers, with the choice left explicitly to the student; a point whose demand depends on the cut SHALL say for which option it holds. When the verdict is tight, the feedback SHALL name the riskiest package and a fallback in one or two sentences. When the verdict is fits, the feedback carries no scope paragraph. Idea-stage feedback carries no scope paragraph and no cut options whatever the workload verdict, because there is no core to cut to; the table stays in the review. An over-scoped plan SHALL NOT receive the ready tier and SHALL NOT count toward the idea-stage evidence bar: scope is repairable in place.

The feedback's own asks SHALL respect a net-workload budget: every request that adds work to the student's plan — another evaluation, another standard to map, another body of literature to read — SHALL name what it replaces, be marked optional, or belong to one of the offered cuts. A request that restates an obligation the degree level already sets is not added work. Before hand-over the skill SHALL check that the plan, with every point followed, still fits the verdict it stated.

#### Scenario: Over-scoped plan gets lettered cuts
- **WHEN** a Bachelor's plan chains five dependent work packages into fourteen weeks
- **THEN** the review's work-package table records the verdict over-scoped, and the feedback names this after the verdict and offers lettered cut options, each with what it keeps and drops, leaving the choice to the student

#### Scenario: Unknown input size becomes a question
- **WHEN** the effort of a package scales with the number of items in an existing catalogue the proposal never counts
- **THEN** the table names that count as an unknown, and the feedback asks the student for it

#### Scenario: Gantt chart read as evidence
- **WHEN** normalization moved a phase-by-phase Gantt chart into the notes file
- **THEN** the work-package table uses its phases and durations, and the feedback carries no remark about the chart's format

#### Scenario: Ask paired with a cut
- **WHEN** a point asks for an independent expert validation the plan does not contain
- **THEN** the point names what that validation replaces, marks it optional, or ties it to one of the offered cuts

#### Scenario: Tight plan names a fallback
- **WHEN** the plan fits only if no package overruns
- **THEN** the feedback names the riskiest package and a fallback in one or two sentences, with no cut options

#### Scenario: Fitting plan stays quiet
- **WHEN** the table's verdict is fits
- **THEN** the feedback carries no scope paragraph, and any unknown the table names is asked inside the point it bears on

#### Scenario: Idea stage gets no cut options
- **WHEN** the tier is idea stage and the plan is also over-scoped
- **THEN** the feedback offers no lettered cuts and no scope paragraph, so the student is not invited to revise a text that has no core

#### Scenario: Over-scoped is never ready
- **WHEN** the substance tests pass but the plan is over-scoped
- **THEN** the tier is needs revision, and the over-scope does not count toward the idea-stage bar

### Requirement: Resubmission intake

When the professor says the submission is a revised version, or the professor-side locations already hold a review or feedback file for the same idea, the skill SHALL read the earlier review and feedback before judging the new version. Matching SHALL rest on the content — title, research questions, method — and never on student identity. The review file SHALL carry an earlier-round section stating for each earlier curated point whether it is resolved, partly resolved, or open, and the feedback SHALL add one sentence after the verdict naming what the revision addressed and what stays open. A point that is new in this round SHALL be marked as new; a point the earlier round settled SHALL NOT be raised again. Before an earlier review or feedback file is overwritten, its points SHALL be carried into the new review's earlier-round section, and an existing notes file for the same idea SHALL be extended rather than recreated, so its literature records survive. When the professor indicates an earlier round but none is found, the chat SHALL say so in one line and the run SHALL proceed as a first intake.

#### Scenario: Earlier round found
- **WHEN** the workspace holds a review and feedback for a proposal with the same research questions under the same slug
- **THEN** the new review carries the earlier points with their status, the feedback names what changed in one sentence after the verdict, and the earlier points survive the overwrite inside the new review

#### Scenario: Earlier literature records survive
- **WHEN** the earlier round recorded woven and rejected papers in the notes file
- **THEN** after the new run those entries are still present

#### Scenario: Earlier round indicated but absent
- **WHEN** the professor says a previous version may have been seen and no earlier artifact matches
- **THEN** the chat says so in one line and the run continues as a first intake

#### Scenario: Settled point not raised again
- **WHEN** the earlier feedback asked for a change the revision made
- **THEN** the new feedback does not ask for it again, and any new point is marked as new
