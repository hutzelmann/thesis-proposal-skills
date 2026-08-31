# guidance-model Specification

## Purpose
Defines how proposal-writing guidance is stored, which parts are machine-readable, and how users customize it per workspace without touching installed skills.
## Requirements
### Requirement: Canonical proposal structure
The default guidance SHALL require exactly these sections in order: "Introduction to the Topic", "Contribution to the State-of-the-Art", "Research Focus and Research Questions", "Methodology for Research: <Methodology>" where <Methodology> is one of: Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Empirical Model Evaluation, Case Study, and "Timeline". Each methodology has a fixed set of required subsections. Exactly one methodology SHALL be used per proposal. Canonical German section titles SHALL be defined for all of the above.

The document SHALL be anchored by a single leading H1 carrying the thesis title; canonical sections sit at H2 and methodology subsections at H3. The title heading is not a section: it SHALL be exempt from required-section, forbidden-pattern, and methodology matching, so a title whose text collides with a section title or a forbidden pattern produces no section finding.

The declared order SHALL be enforced, not merely the presence of each section: a proposal whose canonical sections appear in a different order than the guidance declares SHALL be reported as a violation. Under a workspace override that declares its own required-section list, the order of that list SHALL be the enforced order.

#### Scenario: Mixed methodologies
- **WHEN** a proposal combines two methodologies
- **THEN** guidance-following tooling reports a violation of the single-methodology rule

#### Scenario: Canonical sections out of order
- **WHEN** a proposal carries all five canonical sections but places the timeline before the introduction
- **THEN** guidance-following tooling reports an ordering violation

#### Scenario: Override list defines the order
- **WHEN** a workspace declares its own required-section list in a different order than the default
- **THEN** the workspace's order is the one enforced, and the default order is not applied

#### Scenario: Title text collides with a forbidden pattern
- **WHEN** the leading H1 title contains a word from the forbidden-heading patterns
- **THEN** no forbidden-section violation is reported, because the title heading is not a section

### Requirement: Coarse timeline section
The default guidance SHALL require a final section, "Timeline" in English and "Zeitplan" in German, holding a short statement of when the thesis starts and when it is submitted, at month granularity, or a statement that the work begins as soon as possible.

The section SHALL stay coarse. Under default guidance its body SHALL contain no table, no list, and no subsection, and SHALL be limited to at most three non-empty lines. Anything richer — a phase breakdown, a milestone table, a Gantt chart, however it is rendered — SHALL be reported as a violation. A statement of a timeframe that the writer never supplied SHALL NOT be invented; an unknown timeframe SHALL be recorded as a visible TODO marker instead.

#### Scenario: Coarse timeline accepted
- **WHEN** the timeline section reads "The thesis starts in October 2026 and is submitted in March 2027."
- **THEN** the section passes

#### Scenario: As soon as possible
- **WHEN** the writer has no registered dates and states that the thesis begins as soon as possible
- **THEN** the section passes

#### Scenario: Gantt table under the timeline heading
- **WHEN** the timeline section body contains a table of phases and months
- **THEN** tooling reports it as a violation under default guidance

#### Scenario: Work packages as subsections
- **WHEN** the timeline section carries subsections, one per work package
- **THEN** tooling reports it as a violation under default guidance

#### Scenario: Gantt chart supplied as an image
- **WHEN** the timeline section embeds a Gantt chart as a figure rather than as markup
- **THEN** the agent pass reports it as a violation, since no mechanical check can inspect the image

#### Scenario: Timeframe unknown
- **WHEN** the writer's start and submission months are not known
- **THEN** the section carries a visible TODO marker and no timeframe is asserted

### Requirement: Forbidden content
The default guidance SHALL forbid: work plans, phase breakdowns and milestone tables, supervisor names, the author's own name, expected-results sections, deliverables/code fragments, personal data (matriculation number, address, email, study program), preliminary thesis chapter structures, and confidentiality markers. A coarse statement of when the thesis starts and when it is submitted is NOT forbidden content — it is the required timeline section. The guidance SHALL state that the writer is identified outside the document — hand-in channel, upload form, filename — so the absence of a name reads as a rule rather than an omission.

#### Scenario: Work plan present
- **WHEN** a proposal contains a work-plan or milestone heading
- **THEN** tooling reports it as forbidden content under default guidance

#### Scenario: Student asks where their name goes
- **WHEN** the guidance is consulted about naming the writer
- **THEN** it states that proposals stay anonymous and identification happens through the hand-in channel, not the document

### Requirement: Deliberate stance on omitted conventions
The guidance SHALL state, in one place, that omitting work plans, expected-results sections, and the author's name is a deliberate stance of this guidance and not an oversight, because many university templates require exactly those elements and a student will encounter such templates. The statement SHALL point at the workspace override mechanism as the way a program's contrary requirements are honored.

#### Scenario: Student finds a contradicting template
- **WHEN** a student asks why this guidance forbids the milestone plan their faculty's template requires
- **THEN** the guidance names the divergence as deliberate and points at the workspace override as the mechanism for following the faculty's rule

### Requirement: Workspace override file
A user-owned `guidelines.md` in the workspace SHALL override/extend defaults. It consists of a machine-readable fenced TOML block plus freeform prose. Absent file means pure defaults.

Every override key SHALL be the same key path the value occupies in the structured guidance data. There SHALL be exactly one naming rule: no hand-named aliases, and no flat spelling accepted alongside a nested one. The overridable set SHALL cover the reference minimum, the required-section list, the forbidden-heading list, the timeline detail mode, the page limit, and the research-question count bounds.

Merge semantics: a user key wins over the default per key; list values replace defaults entirely; a default-forbidden section may be allowed again by omitting it from the replacement list.

The timeline detail mode SHALL accept `simple` (the default) or `detailed`. Under `detailed` the timeline size constraint SHALL NOT apply and the work-plan heading patterns SHALL NOT be forbidden, so a program that mandates a phase table can have one without abandoning the rest of the defaults.

#### Scenario: Supervisor requires a detailed work plan
- **WHEN** `guidelines.md` sets the timeline detail mode to `detailed`
- **THEN** checks accept a timeline section containing a phase or milestone table, and work-plan headings are no longer reported as forbidden

#### Scenario: Raised reference minimum
- **WHEN** `guidelines.md` raises the reference minimum to 8
- **THEN** a proposal with 5 references fails the reference-count check

#### Scenario: Research-question bounds overridden
- **WHEN** `guidelines.md` sets the research-question upper bound to 3
- **THEN** a proposal declaring four research questions fails the count check

#### Scenario: Override key mirrors the structure path
- **WHEN** a value is nested in the structured guidance data
- **THEN** the override key for it is nested identically, and no alternative spelling is honoured

### Requirement: Thesis title quality
The guidance SHALL govern the proposal's own thesis title, stating that it is printed on the student's final study certificate and therefore outlives the document. A title SHALL name what is contributed and what it is contributed about, at a level of abstraction that stays true when the tool used to produce it is replaced. It SHALL stand on its own: the rendered title page carries title and subtitle, but the certificate carries the title alone, so the title SHALL NOT depend on the subtitle or on any surrounding context to be understood. It SHALL state its subject rather than pose a question, and SHALL stay within the documented word bounds, whose minimum is per language because German compounds into one noun what English spreads over several. A concrete technology, product, vendor, or company name MAY appear only as a scope qualifier, and only once the student has stated why that technology is the object of study rather than the instrument of it.

#### Scenario: Tool named as the instrument
- **WHEN** a title names the framework, library, product, or platform used to build the artefact
- **THEN** the guidance requires an abstracted formulation naming the contribution and its object instead

#### Scenario: Tool named as the object of study
- **WHEN** the research question is about that technology itself, as in a systematic literature review of one platform's operator patterns or a user study of one specific IDE
- **THEN** the guidance permits the name as a scope qualifier, on the record that the student stated the technology is the object of study

#### Scenario: Certificate standalone reading
- **WHEN** the title is read without the subtitle or the study program
- **THEN** it still states what was researched

### Requirement: Title alarm classes
The guidance SHALL name four classes of problematic title: a tool, product, vendor, or company name carried as the instrument; implementation framing that states building work rather than a contribution; vagueness or grandiosity that names a research field rather than a thesis; and marketing, buzzword, or clickbait tone borrowed from non-academic writing.

#### Scenario: Implementation framing
- **WHEN** a title reads as a work order, such as an opener declaring the development or implementation of a system
- **THEN** it falls under the implementation-framing class

#### Scenario: Field named instead of thesis
- **WHEN** a title names a whole research field with no stated object or contribution
- **THEN** it falls under the vagueness class

#### Scenario: Marketing tone
- **WHEN** a title carries promotional vocabulary
- **THEN** it falls under the marketing class

### Requirement: Title alarm is raised and justified, never silently blocked
Where a title matches an alarm class, guidance SHALL require the agent to raise it explicitly, to state that the title reaches the certificate, and to offer between one and three abstracted alternatives. The agent SHALL NOT silently rewrite the title and SHALL NOT refuse to proceed. A title carrying a named technology SHALL be retained only against the student's stated justification that the technology is the object of study; absent that justification the agent SHALL keep recommending the abstracted alternative.

#### Scenario: Student justifies the named technology
- **WHEN** the student states why the named technology is the object of study
- **THEN** the title is retained and the alarm is not repeated for that reason

#### Scenario: Student gives no justification
- **WHEN** the student neither justifies the name nor accepts an alternative
- **THEN** the agent records the recommendation and proceeds without overwriting the student's title

#### Scenario: Silent rewrite forbidden
- **WHEN** an agent judges a title problematic
- **THEN** it never replaces the title without saying so and never presents the replacement as the student's own choice

### Requirement: Substance tests
The prose guidance SHALL name five substance tests that every proposal is judged against, each with a memorable name and a one-line operational question:

- **Delta test** — the proposal states precisely what the thesis adds beyond the work it cites: what it confirms, refutes, or extends. A contribution section that reads as a feature list or restates the field fails; a contribution that confirms or refutes prior findings under new conditions passes, because extending is not the only admissible delta.
- **Falsifiability test** — the research questions can come out negative; a question whose every conceivable outcome counts as success fails.
- **Swap test** — the proposal's core statements could not equally describe ten other theses in the area; text that survives swapping the topic noun fails as generic.
- **Method-fit test** — the methodology concretely answers each research question; boilerplate method prose that never touches the questions fails.
- **Executability test** — the proposal gives the student concrete, actionable goals: it names the objects of study (dataset, system, population, corpus), states a concrete evaluation, is feasible in the stated months, and makes clear what the student would actually do first.

The tests SHALL be prose guidance for agents, never encoded as structured check data. Guidance-following skills that judge substance SHALL cite failed tests by these names.

#### Scenario: Generic proposal against the swap test
- **WHEN** a proposal's introduction, contribution, and research questions would remain plausible after replacing its topic with a neighboring one
- **THEN** substance-judging tooling reports a swap-test failure by name

#### Scenario: Unfalsifiable research question
- **WHEN** a research question is phrased so that any outcome demonstrates success
- **THEN** substance-judging tooling reports a falsifiability-test failure by name

#### Scenario: Proposal gives no actionable first step
- **WHEN** a proposal names no object of study and no concrete evaluation, so a student could not say what to do in the first week
- **THEN** substance-judging tooling reports an executability-test failure by name

#### Scenario: Replication-flavored delta
- **WHEN** a proposal's contribution is to test whether a published finding holds in a different context, without extending the technique itself
- **THEN** the delta test accepts it as a confirm-or-refute delta rather than failing it for adding nothing new

### Requirement: Information density
The prose guidance SHALL require that every sentence carry information essential to this specific thesis. Scene-setting openers, truisms, restatements of the obvious, and sentences that would fit any proposal in the area SHALL be identified as removable filler. Shortness follows from density: the guidance SHALL frame deletion of low-information sentences as the primary length instrument, not compression of wording.

#### Scenario: Truism opener
- **WHEN** a section opens with a general claim true of any software project ("Software quality is important in modern systems")
- **THEN** guidance-following tooling identifies the sentence as removable filler

#### Scenario: Dense long section accepted
- **WHEN** a section is long but every sentence carries thesis-specific information
- **THEN** no length complaint is raised against it

### Requirement: Default page limit
The default guidance SHALL declare a page limit of five pages for the rendered proposal, deliberately generous, and SHALL treat it as a warning-level bound, never a hard failure. The workspace `page_limit` override SHALL replace the default. Because the source format is markdown, mechanical checks SHALL estimate pages from word count using a documented words-per-page constant and SHALL label the result an estimate.

#### Scenario: Default limit exceeded
- **WHEN** no override exists and the estimated length exceeds five pages
- **THEN** tooling reports a warning naming the estimate and the limit, and the run does not fail

#### Scenario: Workspace tightens the limit
- **WHEN** `guidelines.md` sets `page_limit = 3`
- **THEN** the estimate is judged against three pages

### Requirement: Formalization boundary
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, the timeline size constraint, research-question list conventions, the default page limit with its words-per-page estimation constant, and the mechanically matchable thesis-title tells (implementation-opener patterns, a closed buzzword list, and word-count bounds, each in English and German). The mechanically checkable skeleton also covers the document frame: the leading H1 title's position and uniqueness, the emphasized subtitle paragraph with its canonical wordings, the closing references section, the retired metadata keys, and the deterministic language-inference rule. All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy, the five substance tests, the information-density rule, whether the timeline actually names a timeframe, and whether a name in the title denotes a tool at all) SHALL remain prose guidance for agents.

#### Scenario: Semantic rule stays prose
- **WHEN** a rule concerns argument quality rather than document skeleton
- **THEN** it appears only in prose guidance and is never encoded as structured check data

#### Scenario: Timeframe recognition stays prose
- **WHEN** the question is whether a timeline section states a real timeframe, given that students write `SoSe 2027`, `WS 2026/27`, `Q3`, or "winter semester"
- **THEN** no list of accepted date formats is encoded as structured data, and the judgement stays with the agent

#### Scenario: Tool recognition stays prose
- **WHEN** the question is whether a proper noun in the title names a tool, product, or vendor
- **THEN** no list of tool names is encoded as structured data, because the set is unbounded, and the judgement stays with the agent

#### Scenario: Substance tests stay prose
- **WHEN** the question is whether a proposal passes the delta, falsifiability, swap, method-fit, or executability test
- **THEN** no scoring rubric or keyword list for these judgments is encoded as structured data, and the judgement stays with the agent

#### Scenario: Document frame is mechanically checked
- **WHEN** the question is whether the title line is the file's first content line and only H1
- **THEN** the answer comes from deterministic tooling, not agent judgement

### Requirement: Structured data and prose must not drift
Every canonical title present in the structured guidance data SHALL appear verbatim in the prose guidance. Automated verification SHALL fail when they diverge.

#### Scenario: Title renamed in prose only
- **WHEN** a section title is changed in prose guidance but not in the structured data
- **THEN** the consistency verification fails

### Requirement: Research-question count bounds
The structured guidance data SHALL bound the number of research questions from both sides. The lower bound SHALL be 1 and the upper bound SHALL default to 5. Both bounds SHALL be workspace-overridable. The prose guidance SHALL state the upper bound and the failure it detects — a scope that has not been decided — rather than the number alone.

The bound counts the ordered-list items under the research-questions section, which is the same list the `(RQn)` cross-reference rule already counts. Whether a set of questions is genuinely distinct, non-overlapping, and analytically phrased SHALL remain prose guidance, since it is a judgement rather than a count.

#### Scenario: Count within bounds
- **WHEN** a proposal declares three research questions
- **THEN** no count-related finding is reported

#### Scenario: Count above the default bound
- **WHEN** a proposal declares six research questions and the workspace sets no override
- **THEN** guidance-following tooling reports the count as a violation, naming both the count found and the bound

#### Scenario: Workspace raises the bound
- **WHEN** a workspace override sets the upper bound to 7 and a proposal declares six research questions
- **THEN** no count-related finding is reported

#### Scenario: Overlap judgement stays prose
- **WHEN** two of three research questions are near-duplicates of each other
- **THEN** no structured rule detects it, and the judgement stays with the agent

### Requirement: Construction goals have a home
The guidance SHALL state where an implementation or construction goal belongs, not only that it is not a research question. A goal describes what the work will do; a research question asks what the work will find out. A goal phrased as "how can X be built" SHALL be directed to the contribution section, where the work describes itself, rather than merely rejected.

The guidance SHALL recommend stating a construction goal in a structured form that names the problem context, the artifact to be built, the requirements it must satisfy, and the stakeholder goal it serves, so that the goal carries its own so-what and its requirements are checkable. For a proposal whose contribution is an artifact, the guidance SHALL require the research questions to interrogate the stated goal — asking what effects the artifact has against its requirements, how it compares to alternatives, or under which conditions it holds — rather than standing unrelated beside it.

The guidance SHALL also carry the reviewer-facing nuance: a question of the form "how can X be done" is legitimate research when its answer is a method that generalizes beyond one instance. The test is whether the answer generalizes, not the interrogative surface; a student's one-off build target fails it, which is why the student-facing rule stands unchanged.

#### Scenario: Student writes a construction goal as a research question
- **WHEN** the guidance is consulted about "How can a dashboard for X be built?" appearing in the research-question list
- **THEN** it names the section that statement belongs in, rather than only reporting that it is not analytical

#### Scenario: Goal stated without structure
- **WHEN** a contribution section says only that a prototype will be developed
- **THEN** the guidance asks for the structured form: the context it improves, the requirements it must satisfy, and the stakeholder goal it serves

#### Scenario: Research questions unrelated to the stated goal
- **WHEN** a proposal states an artifact goal in the contribution section and lists research questions that never touch that artifact or its requirements
- **THEN** guidance-following tooling reports the missing derivation link between goal and questions

#### Scenario: Generalizing method question
- **WHEN** a reviewer judges "How can regression test selection be done under flaky tests?" where the intended answer is a technique applicable beyond one system
- **THEN** the guidance recognizes it as a legitimate research question rather than mechanically rejecting the phrasing

### Requirement: Prior work is organised thematically
The guidance SHALL require the contribution section to group prior work into thematic clusters rather than presenting it chronologically or one source at a time, to compare and contrast within a cluster rather than summarise each source in turn, and to close by naming the gap the thesis fills with explicit reference to the research questions.

#### Scenario: Reading-list contribution section
- **WHEN** a contribution section walks through one publication after another without comparing them
- **THEN** the guidance identifies it as a reading list rather than a synthesis, and asks for the shared limitation of each cluster

### Requirement: Early purpose statement
The guidance SHALL require the introduction to close with an explicit statement of what the thesis tries to achieve — one or two sentences, at the level of ideas rather than technique. The existing rule that the introduction refers to the thesis itself only at its end SHALL be kept and sharpened: that closing reference is not optional color but the purpose statement the rest of the proposal unfolds.

#### Scenario: Introduction never states a purpose
- **WHEN** an introduction motivates a topic and ends without saying what this thesis tries to achieve
- **THEN** guidance-following tooling identifies the missing purpose statement at the section's close, rather than treating the section as complete because the topic was motivated

#### Scenario: Purpose stated mid-proposal only
- **WHEN** the first statement of what the work tries to achieve appears in the methodology section
- **THEN** the guidance directs it to the introduction's close, where a reader learns it before the prior-work discussion begins

### Requirement: Significance and result type at the contribution's close
The guidance SHALL require the contribution section's closing gap statement to carry two things beyond the gap itself: why answering the research questions matters once they are answered — significance is a distinct statement from the delta, which only names what is missing — and what kind of thing the thesis will deliver (a technique, a model, a tool or prototype, an evaluation of a specific instance, or a report of findings). Naming the kind is not an expected-results section: it types the deliverable without asserting its content.

#### Scenario: Gap named, significance absent
- **WHEN** a contribution section names the gap the thesis fills but never says why filling it matters to anyone
- **THEN** guidance-following tooling asks for the significance statement, distinct from the delta

#### Scenario: Result type never named
- **WHEN** a proposal's contribution section leaves open whether the thesis delivers a tool, a model, or an evaluation
- **THEN** the guidance asks the writer to name the kind of deliverable

#### Scenario: Result type is not an expected result
- **WHEN** a proposal states that the thesis will deliver a benchmark comparison of two approaches
- **THEN** naming that kind is compliant, while asserting which approach will win remains forbidden expected-results content

### Requirement: Standards are legitimate sources
The guidance SHALL state that published standards and regulations are legitimate — and frequently the only correct — sources for normative definitions, required behavior, and terminology, and SHALL require citing the standard by its own designation and year rather than a vendor's or a blog's summary of it. The guidance SHALL also state the limit: a standard establishes what is required, never that an approach works, so empirical claims continue to require peer-reviewed evidence.

#### Scenario: Normative definition needed
- **WHEN** a proposal needs the defined meaning of a term fixed by an ISO, IEEE, ETSI, SAE, UNECE, or EU regulatory document
- **THEN** the guidance treats the standard itself as the correct source and rejects a vendor page restating it

#### Scenario: Standard cited as evidence of effectiveness
- **WHEN** a proposal cites a standard to support a claim that an approach performs well
- **THEN** the guidance requires peer-reviewed evidence for that claim, because the standard cannot supply it

### Requirement: Research involving human participants
The guidance SHALL cover, as advisory prose rather than as a required section or a mechanical check, what a proposal involving human participants is expected to address: the ethics route and the approval required before data collection begins, how informed consent is obtained and recorded, what personal data is collected and how it is pseudonymised, retained, and legally justified, how risk is bounded and how a participant can stop, and whether and how participants are compensated. The guidance SHALL bound its own scope, asking for a few precise sentences inside the existing methodology subsections rather than a compliance appendix.

#### Scenario: User study proposal silent on ethics
- **WHEN** a proposal declares a study with human participants and addresses none of these points
- **THEN** the guidance identifies the omission as the first question a supervisor will ask, while no mechanical check reports an error

#### Scenario: Guidance is not a new section
- **WHEN** a proposal addresses consent and data handling inside its Preparation subsection
- **THEN** that satisfies the guidance, and no separate ethics section is expected

### Requirement: Secondary-data ethics
The guidance SHALL cover, as advisory prose in the same style as the human-participants advisory and not as a required section or mechanical check, what a proposal working on mined, scraped, or third-party data is expected to address: where the data comes from and under what license or terms it may be used, whether it contains personal data and how that is handled, and whether redistribution or publication of derived data is permitted.

#### Scenario: Mining proposal silent on data provenance
- **WHEN** a proposal plans to mine public repositories and says nothing about licensing or personal data in commit metadata
- **THEN** the guidance identifies the omission as a question a supervisor will ask, while no mechanical check reports an error

#### Scenario: Advisory stays advisory
- **WHEN** a proposal addresses provenance and licensing in one sentence inside its methodology
- **THEN** that satisfies the guidance, and no separate data-ethics section is expected

### Requirement: Anticipated outcomes are stated as expectations
The guidance SHALL require that any statement about what the work will yield is phrased as an expectation rather than as a result already obtained, and that the foreseeable limitations — sample size, generalisation, access, time — are named rather than left implicit. This SHALL NOT be read as permitting an expected-results section, which remains forbidden content.

#### Scenario: Proposal asserts its outcome
- **WHEN** a proposal states that the approach improves a metric, as though the work were done
- **THEN** the guidance requires the claim be re-phrased as an expectation

### Requirement: Reference floor is not a reference target
The guidance SHALL distinguish the mechanically checked minimum number of references from the number a submitted proposal is expected to carry. The minimum SHALL be described as a floor that catches an empty or near-empty bibliography; the prose SHALL state the working range separately, so that meeting the floor is never read as meeting the bar.

#### Scenario: Proposal sits at the floor
- **WHEN** a proposal cites exactly the minimum number of references
- **THEN** the mechanical check passes and the guidance still identifies the bibliography as thin

### Requirement: The methodology set is closed per workspace
The methodology set SHALL remain closed — a proposal declares exactly one methodology from a fixed set, and that constraint is what forces a decision about the kind of evidence the thesis produces. The *contents* of that set SHALL be workspace-configurable, because which methodologies are acceptable is a property of a supervisor's field rather than of thesis writing.

A workspace declaration SHALL be able to add a branch, replace a shipped branch of the same identity, and disable a shipped branch. A workspace that declares no methodologies SHALL get the shipped defaults unchanged.

The guidance SHALL state that the shipped set is a default rather than a claim about which methodologies exist.

#### Scenario: Workspace adds a branch
- **WHEN** a workspace declares a methodology branch the shipped set does not contain
- **THEN** a proposal declaring that methodology is accepted, and its declared subsections are the ones required

#### Scenario: Workspace disables a shipped branch
- **WHEN** a workspace disables one of the shipped branches
- **THEN** a proposal declaring it is reported as an unknown methodology, and the branch is absent from the list of accepted ones

#### Scenario: Workspace declares nothing
- **WHEN** a workspace `guidelines.md` carries no methodology declaration
- **THEN** the shipped set applies unchanged

#### Scenario: Single-methodology rule is unaffected
- **WHEN** a proposal declares two methodology sections in a workspace with a widened set
- **THEN** the single-methodology rule still reports a violation

### Requirement: A workspace methodology branch declares its own content contract
A workspace-declared methodology branch SHALL supply, for every subsection, guidance describing what belongs in it. A branch declaring headings without that guidance SHALL be rejected as a configuration error rather than accepted with empty contracts.

The shipped branches carry their content contract as prose in the guidance document; a workspace branch has no such document, so the declaration is where that contract lives. This SHALL NOT be read as formalizing the shipped guidance: the requirement exists because a workspace cannot ship prose, not because content contracts belong in structured data.

#### Scenario: Branch without guidance
- **WHEN** a workspace declares a branch whose subsections carry no guidance
- **THEN** the declaration is reported as a configuration error naming the branch, and the branch is not applied

#### Scenario: Branch with guidance
- **WHEN** a workspace declares a branch with guidance for each subsection
- **THEN** the branch is applied, and writing tooling has a content contract for every heading it must fill

### Requirement: Systematic reviews assess primary-study quality
The SLR branch's second subsection SHALL be titled "Quality Assessment and Extracted Information" in English and "Qualitätsbewertung und extrahierte Informationen" in German, and its content contract SHALL cover both halves: how the quality of included primary studies is assessed and how that assessment is used (exclusion or weighting), alongside what is extracted and how deeply. The contract SHALL further require that the Synthesis subsection declares whether a formal meta-analysis is intended or the synthesis stays narrative, and that the review's type is declared: a mapping-style review, which legitimately omits per-study quality assessment, SHALL say so in the quality-assessment subsection and state why breadth replaces depth. The guidance SHALL recommend PICOC (population, intervention, comparison, outcome, context) as the shape for framing the review question and deriving search terms, scoped to this branch only.

#### Scenario: Review silent on study quality
- **WHEN** a proposal declares the SLR methodology and its quality-assessment subsection describes only what data is extracted
- **THEN** guidance-following tooling asks how primary-study quality is assessed and how the assessment is used

#### Scenario: Mapping-style review omits assessment with a reason
- **WHEN** the quality-assessment subsection states the review is a mapping-style survey of a field and quality assessment is omitted because classification, not evidence weighing, is the goal
- **THEN** the omission is compliant, because the branch requires the declaration rather than the assessment itself

#### Scenario: Old subsection title
- **WHEN** a proposal carries the former "Extracted Information" heading
- **THEN** the mechanical check reports the "Quality Assessment and Extracted Information" subsection as missing

#### Scenario: Synthesis type undeclared
- **WHEN** the Synthesis subsection describes combining findings without saying whether a formal meta-analysis is intended
- **THEN** the guidance asks for the declaration

### Requirement: Prototype evaluation names its empirical form
The Prototype Implementation contract SHALL require the Evaluation subsection to name the empirical form the evaluation takes — a benchmark against datasets or workloads, a controlled experiment, a case study, or a simulation — and to compare the prototype against state-of-the-art alternatives or state why such a comparison is impractical. Naming the form is a methodology-internal statement and SHALL NOT be read as declaring a second methodology.

#### Scenario: Evaluation names no form
- **WHEN** a Prototype Implementation proposal's Evaluation subsection promises that the prototype answers the research questions without saying by what kind of study
- **THEN** guidance-following tooling asks which empirical form the evaluation takes

#### Scenario: No alternatives addressed
- **WHEN** the Evaluation subsection measures only the prototype itself although comparable approaches exist in the cited literature
- **THEN** the guidance asks for a comparison or an explicit statement of why comparing is impractical

#### Scenario: Named form is not a second methodology
- **WHEN** a Prototype Implementation evaluation names a benchmark as its form
- **THEN** the single-methodology rule is not violated by that naming

### Requirement: Methodology sections justify method fit
The guidance SHALL require every methodology section to open with one or two sentences stating why the chosen methodology answers the research questions — the prose counterpart of the method-fit test, written by the student rather than judged only by a reviewer.

#### Scenario: Methodology opens without justification
- **WHEN** a methodology section starts directly with its first subsection and never says why this methodology fits these questions
- **THEN** guidance-following tooling asks for the opening justification

#### Scenario: Justification present
- **WHEN** a methodology section opens by stating that a user study is chosen because the research questions concern observed developer behavior rather than tool performance
- **THEN** the requirement is satisfied

### Requirement: Controlled experiments plan hypotheses, design, and analysis
The Controlled Experiment branch SHALL require the subsections "Hypotheses and Variables" / "Hypothesen und Variablen", "Design and Participants" / "Versuchsdesign und Teilnehmende", and "Statistical Analysis" / "Statistische Auswertung". The content contract SHALL require: in Hypotheses and Variables, the hypotheses being tested and, named separately, the independent variables with their treatments (what is manipulated) and the dependent variables with their measures (what is measured), plus the known confounding factors; in Design and Participants, the experiment design, how participants are recruited and assigned — random assignment, or a justified quasi-design — and the tasks or instruments used; in Statistical Analysis, the planned tests as a consequence of the chosen design, and the main threats to validity.

The guidance SHALL bound the User Study branch against this one: User Study covers observational, usability, and survey-style research with human participants; a study that manipulates a treatment to test a hypothesis belongs in Controlled Experiment.

#### Scenario: Variables named without hypotheses
- **WHEN** a Controlled Experiment proposal lists variables but states no hypothesis relating them
- **THEN** guidance-following tooling asks for the hypotheses the variables serve

#### Scenario: Manipulated and measured conflated
- **WHEN** the Hypotheses and Variables subsection lists variables without saying which are manipulated and which are measured
- **THEN** the guidance asks for the separation into independent variables with treatments and dependent variables with measures

#### Scenario: Tests unconnected to design
- **WHEN** the Statistical Analysis subsection names tests although no experiment design was stated
- **THEN** the guidance asks for the design the tests follow from

#### Scenario: Hypothesis-testing study declared as User Study
- **WHEN** a proposal declares the User Study methodology and its procedure manipulates a treatment to test a hypothesis
- **THEN** guidance-following tooling directs it to the Controlled Experiment branch

### Requirement: Model evaluations fix data, baselines, and analysis in advance
The Empirical Model Evaluation branch SHALL require the subsections "Data and Baselines" / "Daten und Baselines", "Experimental Setup" / "Versuchsaufbau", and "Analysis" / "Auswertung". The content contract SHALL require: in Data and Baselines, which datasets are used, where they come from and under what license, and which state-of-the-art baselines the models are compared against — or a justification why no baseline exists; in Experimental Setup, the train/validation/test protocol including how leakage between splits is prevented, and the models, features, and infrastructure involved; in Analysis, which metrics answer the research questions and why those metrics, plus how variance across runs is handled. The guidance SHALL state that benchmark-style comparisons of existing models or tools use this branch.

#### Scenario: No baselines named
- **WHEN** an Empirical Model Evaluation proposal evaluates only its own model configurations against each other
- **THEN** guidance-following tooling asks for state-of-the-art baselines or an explicit justification of their absence

#### Scenario: Split protocol silent on leakage
- **WHEN** the Experimental Setup subsection names a train/test split without saying how leakage is prevented
- **THEN** the guidance asks for the leakage discussion

#### Scenario: Metrics unjustified
- **WHEN** the Analysis subsection lists metrics without connecting them to the research questions
- **THEN** the guidance asks why these metrics answer these questions

#### Scenario: Benchmark study homed here
- **WHEN** a proposal compares existing published models on a public benchmark without training a new one
- **THEN** the guidance accepts Empirical Model Evaluation as the fitting branch

### Requirement: Case studies declare their case, sources, and limits
The Case Study branch SHALL require the subsections "Case and Units of Analysis" / "Fall und Analyseeinheiten", "Data Collection" / "Datenerhebung", and "Analysis" / "Auswertung". The content contract SHALL require: in Case and Units of Analysis, what the case is and its context, the units of analysis within it, why this case suits the research questions — case selection is intentional (a typical, critical, or revelatory case), never a sample — and what access exists; in Data Collection, which sources are drawn on and how each is recorded, with more than one source so findings can be triangulated, and with consent and confidentiality toward the host organisation addressed; in Analysis, how the material is coded and synthesised into answers, and what a single case can and cannot show.

#### Scenario: Case selection unexplained
- **WHEN** a Case Study proposal describes an organisation without saying why this case suits the research questions
- **THEN** guidance-following tooling asks for the selection rationale

#### Scenario: Single data source
- **WHEN** the Data Collection subsection names interviews as the only source
- **THEN** the guidance asks for a second source or an acknowledgment that findings cannot be triangulated

#### Scenario: Generalization unbounded
- **WHEN** the Analysis subsection promises conclusions about industry practice in general from one case
- **THEN** the guidance asks for the single-case limitation to be stated

#### Scenario: Observation versus intervention
- **WHEN** a proposal plans to change the studied organisation's process and evaluate the change
- **THEN** the guidance notes that intervening in the case is action research, which the shipped set does not contain, and points at the workspace mechanism

### Requirement: Default methodology branches record their provenance
Every methodology branch in the shipped default set SHALL record where it comes from: its content contract in the prose guidance SHALL close with a one-sentence citation of the branch's primary methodological source, and a maintained sources document SHALL state, per branch, the taxonomy or standard it derives from, the source of its subsection contract, and what the compression deliberately left out. A branch added to the defaults without provenance SHALL be treated as incomplete.

#### Scenario: Supervisor asks why a branch exists
- **WHEN** a supervisor asks why the default set contains a given branch and why it has these subsections
- **THEN** the guidance names a citable source in the branch's contract, and the sources document carries the fuller argument

#### Scenario: New default branch without provenance
- **WHEN** a future change adds a default branch with no citation and no sources-document entry
- **THEN** the change is incomplete against this requirement

#### Scenario: Provenance stays out of structured data
- **WHEN** provenance is recorded for a branch
- **THEN** it lives in prose and documentation, never as fields in the structured guidance data


### Requirement: Per-language document terminology

User-facing English text SHALL call the document a proposal and SHALL NOT call it an Exposé; user-facing German text SHALL call it an Exposé and SHALL NOT substitute an English or anglicized term for it. Identifiers are exempt in both directions: URLs, repository names, and skill names (`thesis-proposal-skills`, `proposal-*`) keep their spelling regardless of the surrounding language.

#### Scenario: English text names the document
- **WHEN** a skill or shared snippet renders English user-facing prose about the document
- **THEN** the document is called a proposal, never an Exposé

#### Scenario: German text names the document
- **WHEN** a skill or shared snippet renders German user-facing prose about the document
- **THEN** the document is called an Exposé, while skill and repository identifiers keep their English names
