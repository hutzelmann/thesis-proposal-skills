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

Every override key SHALL be the same key path the value occupies in the structured guidance data. There SHALL be exactly one naming rule: no hand-named aliases, and no flat spelling accepted alongside a nested one. The overridable set SHALL cover the reference minimum, the reference-density constant, the required-section list, the forbidden-heading list, the timeline detail mode, the page limit, the research-question count bounds, and the proposal-location path.

Merge semantics: a user key wins over the default per key; list values replace defaults entirely; a default-forbidden section may be allowed again by omitting it from the replacement list.

The timeline detail mode SHALL accept `simple` (the default) or `detailed`. Under `detailed` the timeline size constraint SHALL NOT apply and the work-plan heading patterns SHALL NOT be forbidden, so a program that mandates a phase table can have one without abandoning the rest of the defaults.

#### Scenario: Supervisor requires a detailed work plan
- **WHEN** `guidelines.md` sets the timeline detail mode to `detailed`
- **THEN** checks accept a timeline section containing a phase or milestone table, and work-plan headings are no longer reported as forbidden

#### Scenario: Raised reference minimum
- **WHEN** `guidelines.md` raises the reference minimum to 8
- **THEN** a proposal with 5 references fails the reference-count check

#### Scenario: Reference density adjusted
- **WHEN** `guidelines.md` sets the reference-density constant to a different value
- **THEN** the density advisory judges the proposal against the workspace value instead of the default

#### Scenario: Research-question bounds overridden
- **WHEN** `guidelines.md` sets the research-question upper bound to 3
- **THEN** a proposal declaring four research questions fails the count check

#### Scenario: Override key mirrors the structure path
- **WHEN** a value is nested in the structured guidance data
- **THEN** the override key for it is nested identically, and no alternative spelling is honoured

#### Scenario: Proposal location overridden at its structure path
- **WHEN** `guidelines.md` sets the proposal-location path at the key path it occupies in the structured guidance data
- **THEN** the workspace's proposal directory is the configured one, and no alternative spelling of the key is honoured

### Requirement: Workspace layout and the proposal location
The workspace root SHALL be the working directory the skills and their scripts operate from, which holds the workspace `guidelines.md`. The proposal-location path SHALL be resolved relative to that root and SHALL default to the root itself. Every proposal SHALL live in a folder of its own directly in that location (proposal-file-format: One folder per proposal); no other layout exists.

A configured proposal-location value SHALL be a relative directory inside the workspace: not absolute, not home-anchored, and not escaping the root through parent references.

The proposal's whole family SHALL sit in its folder (proposal-file-format: Proposal family under one handle). Workspace-level files SHALL stay at the root regardless of the configured proposal location: the `guidelines.md` itself, the workspace key file, and the bug-report bundle.

Skills that create or locate proposals SHALL honor only proposal folders in the configured location: a skill SHALL NOT fall back to the workspace root when the configured directory is empty, SHALL NOT treat a file outside a proposal folder as a proposal or a family member, and SHALL NOT write one outside it. A proposal outside its folder is a reportable condition, never a silently accepted alternative.

#### Scenario: Proposals collected in a subdirectory
- **WHEN** the workspace `guidelines.md` sets the proposal-location path to a subdirectory and a skill creates a proposal
- **THEN** the proposal's folder is created in that subdirectory, and `guidelines.md` stays at the workspace root

#### Scenario: Unset key preserves the flat layout
- **WHEN** the workspace sets no proposal-location path
- **THEN** the proposal location stays the workspace root, as before the key existed, and each proposal's folder sits directly in it

#### Scenario: Family follows the proposal
- **WHEN** a skill writes a proposal's review, feedback, notes, harvest record, or built output
- **THEN** the file lands in that proposal's folder, not in the location's root or the workspace root

#### Scenario: No fallback search
- **WHEN** the configured proposal directory holds no proposal folder but the workspace root does
- **THEN** a skill locating a proposal does not silently adopt the root copy; the mismatch surfaces as a reported condition

#### Scenario: Flat proposal not read
- **WHEN** a proposal file and its notes file sit directly in the proposal location, outside any folder
- **THEN** no skill offers the file as a candidate or reads the notes file, and the check reports the proposal as misplaced when it is named explicitly

#### Scenario: Submission handed over as a source
- **WHEN** a professor names a standard-format proposal file saved at the workspace root as the student's submission
- **THEN** the supervising skill reads it as a source document, writes the normalized copy into a new proposal folder, and leaves the original unchanged

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
Where a title matches an alarm class, guidance SHALL require the agent to raise it explicitly, to state that the title reaches the certificate, and to offer between one and three abstracted alternatives. The agent SHALL NOT silently rewrite the title and SHALL NOT refuse to proceed. A title carrying a named technology SHALL be retained only against the student's stated justification that the technology is the object of study; absent that justification the agent SHALL keep recommending the abstracted alternative. The alarm itself SHALL never block. A named technology in the title that the research does not depend on is also a swap-test failure (requirement: Substance tests). That failure blocks readiness as the swap test's failure, and the agent SHALL raise the name once, as that blocker, with the certificate consequence and the alternatives. A justification stated only in conversation SHALL count for the swap test once the proposal's text carries it.

#### Scenario: Student justifies the named technology
- **WHEN** the student states why the named technology is the object of study
- **THEN** the title is retained, the alarm is not repeated for that reason, and the swap test judges the name by what the proposal's text says about it

#### Scenario: Student gives no justification
- **WHEN** the student neither justifies the name nor accepts an alternative
- **THEN** the agent records the recommendation and proceeds without overwriting the student's title

#### Scenario: Silent rewrite forbidden
- **WHEN** an agent judges a title problematic
- **THEN** it never replaces the title without saying so and never presents the replacement as the student's own choice

#### Scenario: Instrument that passes the swap test
- **WHEN** a title names a platform whose constraints the method is built around, though the platform is not what the thesis studies
- **THEN** the swap test passes, and the title alarm is raised as a non-blocking finding with the certificate consequence and alternatives

### Requirement: Substance tests
The prose guidance SHALL name six substance tests that every proposal is judged against, each with a memorable name and a one-line operational question:

- **Delta test** — the proposal states precisely what the thesis adds beyond the work it cites: what it confirms, refutes, or extends. A contribution section that reads as a feature list or restates the field fails; a contribution that confirms or refutes prior findings under new conditions passes, because extending is not the only admissible delta.
- **Falsifiability test** — the research questions can come out negative; a question whose every conceivable outcome counts as success fails.
- **Swap test** — the proposal's core statements could not equally describe ten other theses in the area; text that survives swapping the topic noun fails as generic, and so does a named tool, system, platform or application domain the research does not depend on.
- **Necessity test** — every sentence, citation and technical term in the proposal serves a research question, the delta, or the method. Material that is true, specific and well-sourced still fails if removing it would not weaken the argument. This is the swap test's mirror: the swap test catches text that could belong to any thesis in the area, the necessity test catches text that belongs to a different one.
- **Method-fit test** — the methodology concretely answers each research question; boilerplate method prose that never touches the questions fails.
- **Executability test** — the proposal gives the student concrete, actionable goals: it names the objects of study (dataset, system, population, corpus), states a concrete evaluation, is feasible in the stated months, and makes clear what the student would actually do first. The test asks for a plausible plan, not a finalized protocol: a choice the student can make during the thesis without changing a research question does not fail it.

The tests SHALL be prose guidance for agents, never encoded as structured check data. Guidance-following skills that judge substance SHALL cite failed tests by these names.

The necessity test SHALL NOT be satisfied by a source's quality, its correctness, or the fact that it is cited: a citation is evidence for a claim, and a claim that no research question, delta, or method step needs fails the test together with the sentence carrying it. Where guidance elsewhere bars technical detail irrelevant to the research questions or methodology, that bar SHALL be stated as this test rather than as an independent rule.

The swap test SHALL apply to named choices as well as to prose. Its scope is the thesis's own claims: the title, the purpose statement that closes the introduction, the research focus and research questions, and the contribution section's statements of what the thesis adds (its goals, the gap, the significance and the kind of deliverable). A tool, system, platform or application domain named there SHALL pass only when the research depends on it, in one of these ways:

- it is the object of study, so the expected contribution is a claim about it rather than about the class it belongs to;
- it imposes constraints that shape the method;
- it supplies data or access that no comparable alternative offers;
- it is the case the proposal argues suits its research questions — a typical, critical or revelatory case, selected as the shipped Case Study contract asks — rather than an instance that merely happened to be at hand.

A comparison of named tools passes by design, because the tools are what it studies. The guidance SHALL state the check as a replacement that compares claims, not nouns: when replacing the name with a comparable alternative, or dropping it, leaves the same claim standing — the research questions, the method and the data unchanged apart from the noun, and the expected contribution still claiming its result for the name's class — the name is decorative and the swap test fails. A contribution that claims its result for this instance SHALL pass. The guidance SHALL reconcile the check with degree-level grading: a Bachelor's contribution close that promises to apply or evaluate something in a named setting passes when it claims its result for that setting, and fails only when it claims a result for the class while the setting stays incidental. The guidance SHALL name the two repairs: state the dependence, or generalize the claim to the name's class. Names of prior work, tools chosen to carry out the method, and domains named only to motivate the topic SHALL NOT be judged by this check; whether they belong is the necessity test's question. The check SHALL stay judgement: no mechanical rule SHALL try to tell a decorative name from an anchored one.

#### Scenario: Generic proposal against the swap test
- **WHEN** a proposal's introduction, contribution, and research questions would remain plausible after replacing its topic with a neighboring one
- **THEN** substance-judging tooling reports a swap-test failure by name

#### Scenario: Unfalsifiable research question
- **WHEN** a research question is phrased so that any outcome demonstrates success
- **THEN** substance-judging tooling reports a falsifiability-test failure by name

#### Scenario: Sourced sentence serving no research question
- **WHEN** a proposal carries a specific, correct, peer-reviewed-cited sentence about a neighboring technology that no research question, delta statement, or method step depends on
- **THEN** substance-judging tooling reports a necessity-test failure by name and identifies the sentence as removable, rather than crediting it as literature grounding

#### Scenario: Specific sentence that survives both mirrors
- **WHEN** a sentence is specific enough to fail no swap test and is depended on by a stated research question
- **THEN** neither the swap test nor the necessity test reports it

#### Scenario: Proposal gives no actionable first step
- **WHEN** a proposal names no object of study and no concrete evaluation, so a student could not say what to do in the first week
- **THEN** substance-judging tooling reports an executability-test failure by name

#### Scenario: Replication-flavored delta
- **WHEN** a proposal's contribution is to test whether a published finding holds in a different context, without extending the technique itself
- **THEN** the delta test accepts it as a confirm-or-refute delta rather than failing it for adding nothing new

#### Scenario: Selection rule passes executability
- **WHEN** a proposal names the benchmark and the metrics and states that the compared models are chosen at the thesis start by a stated rule
- **THEN** the executability test passes, and the model choice is not reported as an executability failure

#### Scenario: Decorative tool in the title and research questions
- **WHEN** a proposal names one agent framework in its title and research questions, its contribution claims a result about agent configurations in general, and any comparable framework would leave the research questions, the method and the expected contribution unchanged
- **THEN** substance-judging tooling reports a swap-test failure by name, locates the name, and states both repairs: state the dependence or generalize the claim

#### Scenario: Named tool as the object of study
- **WHEN** the same proposal's contribution states that the thesis evaluates that framework's own default configuration for the teams that run it
- **THEN** the swap test passes for the name, because a replacement would change the expected contribution

#### Scenario: Comparison of named tools
- **WHEN** the research questions compare three named static analysers on a common corpus
- **THEN** the swap test passes for those names

#### Scenario: Domain that shapes the method
- **WHEN** a thesis restricts its research questions to one application domain whose regulation constrains what the method may record, and the methodology is built around that constraint
- **THEN** the swap test passes for the domain

#### Scenario: Decorative domain
- **WHEN** a code-summarization thesis restricts its research questions to one industry, while its data, method and contribution would read the same for any other industry
- **THEN** substance-judging tooling reports a swap-test failure for the domain by name

#### Scenario: Argued typical case
- **WHEN** a case study names one company and argues, as the Case Study contract asks, why that company is a typical case for its research questions
- **THEN** the swap test passes for the company's name, although a comparable company could in principle have been chosen

#### Scenario: Bachelor's evaluation in a named setting
- **WHEN** a Bachelor's proposal's contribution close promises to evaluate a technique in one named project and claims its result for that project
- **THEN** the swap test passes for the project's name, and the degree-level grading and the swap test agree that the close is complete

#### Scenario: Name outside the thesis's own claims
- **WHEN** a library appears only in the methodology as what the prototype is built with, or a domain appears only in the introduction's motivation
- **THEN** the swap test does not judge that name

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
Machine-readable guidance data SHALL be limited to the mechanically checkable skeleton: canonical section titles (English and German), section order, the methodology-to-subsections table, forbidden-heading patterns, `min_references`, the reference-density estimation constant, the timeline size constraint, research-question list conventions, the default page limit with its words-per-page estimation constant, and the mechanically matchable thesis-title tells (implementation-opener patterns, a closed buzzword list, and word-count bounds, each in English and German). The mechanically checkable skeleton also covers the document frame: the leading H1 title's position and uniqueness, the emphasized subtitle paragraph with its canonical wordings, the closing references section, the retired metadata keys, and the deterministic language-inference rule. All semantic rules (analytical RQ phrasing, high-level introduction, explicit delta to prior work, tone, redundancy, the six substance tests, the information-density rule, whether the timeline actually names a timeframe, and whether a name in the title denotes a tool at all) SHALL remain prose guidance for agents.

Whether a sentence, a citation, or a technical term serves a research question is a semantic rule of exactly this kind. Mechanical checks MAY report that a reference is defined and never cited; they SHALL NOT judge whether the proposal needs it.

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
- **WHEN** the question is whether a proposal passes the delta, falsifiability, swap, necessity, method-fit, or executability test
- **THEN** no scoring rubric or keyword list for these judgments is encoded as structured data, and the judgement stays with the agent

#### Scenario: Document frame is mechanically checked
- **WHEN** the question is whether the title line is the file's first content line and only H1
- **THEN** the answer comes from deterministic tooling, not agent judgement

#### Scenario: Reference relevance stays prose
- **WHEN** the question is whether the cited works are relevant, peer-reviewed, or well chosen
- **THEN** only the count and the length-scaled density are checked mechanically, and every judgement about the sources themselves stays with the agent

#### Scenario: An uncited reference is reported, not judged
- **WHEN** a reference is defined in the metadata block and never cited in the body
- **THEN** the mechanical check reports it as uncited and states both admissible resolutions, and whether the proposal needs the entry stays with the agent

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

The working range SHALL be derived, not asserted: the prose SHALL ground it in coverage the guidance already requires — a thematic cluster in the contribution section needs at least two sources to show a theme rather than an anecdote, each research question's motivation needs grounding, and the introduction grounds its claims in the literature — and SHALL state the expectation as a density relative to the proposal's length, so the target scales with a workspace's page limit instead of assuming the default. The structured guidance data SHALL carry that density as an estimation constant, defaulting to four references per thousand body words, which reproduces the ten-to-fifteen range at the default length.

#### Scenario: Proposal sits at the floor
- **WHEN** a proposal cites exactly the minimum number of references
- **THEN** the mechanical check passes and the guidance still identifies the bibliography as thin

#### Scenario: Range justified by coverage, not quota
- **WHEN** the prose states the working range for references
- **THEN** it derives the range from the coverage rules (cluster grounding, research-question grounding) and a length-scaled density, and does not assert a fixed count as an observed norm

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

### Requirement: Degree-level guidance
The guidelines SHALL carry a degree-level section stating where the level shows in a proposal, covering exactly four graded dimensions — contribution expectation, research-question origin, literature stance, and scope relative to the available months — in brief prose, and framing everything else as identical across levels by design, with `docs/degree-level-sources.md` named as provenance. The section SHALL state the both-directions bar: demanding a novelty claim from a Bachelor's proposal is the same error as accepting its absence from a Master's proposal. Bachelor-side statements SHALL be phrased as expectations not required, never as prohibitions — incipient novelty in a Bachelor's proposal remains welcome. The section SHALL NOT require an explicit methodology-justification statement at either level: a proposal declares one methodology and the proposal as a whole is its support; methodology fit remains a review-side judgement. The document skeleton, `structure.json`, and all mechanical checks SHALL remain level-blind.

#### Scenario: Four dimensions, nothing structural
- **WHEN** the guidelines' degree-level section is compared with `structure.json` and the check rules
- **THEN** the section names contribution expectation, research-question origin, literature stance, and scope-per-months as the graded dimensions, and no structured key or mechanical check varies by degree level

#### Scenario: Bachelor phrasing stays permissive
- **WHEN** the section describes the Bachelor's-level expectation on any dimension
- **THEN** the wording says what is not required at that level and never forbids exceeding it

#### Scenario: No justification requirement
- **WHEN** the section describes methodology at either level
- **THEN** it requires no explicit justification prose and locates methodology fit in review judgement

### Requirement: Citation scope
The guidance SHALL state how far a citation reaches and when a publication is cited again, so that every sentence's source stays recognisable without the same citation being repeated on consecutive sentences.

When consecutive sentences within a paragraph draw on the same publication, the guidance SHALL require citing it once: the run opens with the author-in-text form, and the sentences that follow carry the attribution in words — a pronoun or noun phrase referring back to the cited work or its authors — rather than with a repeated citation. The guidance SHALL require citing the publication again when a new paragraph starts, when another source or a claim of the thesis's own intervenes, and wherever a sentence would otherwise read as the thesis's own claim. Citing different subsets of sources on consecutive sentences is a change of source, not a repetition, and SHALL NOT be discouraged.

The guidance SHALL forbid removing a citation without leaving such a cue, and SHALL name the reason: a citation whose reach the reader cannot see makes borrowed content look like the thesis's own. The guidance SHALL identify a paragraph that needs one source in most of its sentences as a summary of that source rather than a thematic cluster, and SHALL direct its restructuring to the rule that prior work is organised thematically.

The existing prohibition on typing an author name in the prose SHALL stay. Continuation cues are pronouns and noun phrases, never a typed name.

The surface pattern of the rule (the same set of references cited on adjacent sentences) MAY be reported mechanically as a warning. Whether a sentence still reads as attributed is a semantic judgement and SHALL remain prose guidance; no list of acceptable cues is encoded as structured guidance data.

#### Scenario: Same source on consecutive sentences
- **WHEN** three consecutive sentences in one paragraph each cite the same publication while the topic stays the same
- **THEN** the guidance identifies the repetition as overcitation and asks for one author-in-text citation that opens the run, followed by sentences that refer back in words

#### Scenario: Source switch is not repetition
- **WHEN** one sentence cites one publication and the next cites that publication together with another
- **THEN** both citations stay, because the set of sources changed

#### Scenario: The same source in a new paragraph
- **WHEN** a new paragraph continues to draw on the publication cited in the previous one
- **THEN** the guidance requires citing it again in the new paragraph

#### Scenario: Citation deleted without a cue
- **WHEN** repeated citations are removed so that the sentences after the remaining citation neither cite nor refer back to the source
- **THEN** the guidance identifies the unclear reach of the citation as the defect, not the earlier repetition, and asks for a cue or a citation

#### Scenario: One source carries the paragraph
- **WHEN** most sentences of a paragraph in the contribution section draw on a single publication
- **THEN** the guidance identifies the paragraph as a summary of that source and directs it to thematic restructuring

### Requirement: Readiness classification
The prose guidance SHALL define proposal readiness as supporting an informed decision to supervise the thesis, and SHALL state that this is distinct from a finalized execution protocol: a ready proposal may leave bounded execution decisions open. The guidance SHALL sort every finding a judging skill reports into exactly one of three classes:

- **Proposal blockers** — failures of a substance test other than the necessity test: no answerable research question, an unclear contribution — literature grounding included, when the cited work is too thin to show what the thesis adds — a named tool, system, platform or application domain the research does not depend on, a method that cannot answer a question, a scope that cannot fit the stated months at the declared level, or an indispensable resource whose availability is doubtful. No other finding SHALL be a blocker. Necessity, density, title and citation-practice findings SHALL NOT block on their own. A name in the title that fails the swap test SHALL be reported as a swap-test blocker, not as a title finding. Non-serving material that obscures what the thesis contributes or asks SHALL be reported as the delta or research-question blocker it causes.
- **Clarify early in the thesis** — decisions that matter for rigorous execution and can be settled by an initial pilot, a supervisor discussion or ordinary student judgement without changing a research question, the contribution or the methodology choice.
- **Optional refinements** — improvements to presentation or execution that are not conditions of acceptance.

A finding SHALL be classified as clarify-early only when its **deferral record** can be filled: what needs deciding, why it matters, when or under what condition it is settled, a reasonable way to resolve it during the thesis that leaves the research questions, the contribution and the methodology choice intact, and whether an adverse outcome would require revisiting the proposal — answered "no", or "yes" with a named fallback under which every research question stays answerable as asked. A fallback that narrows or drops a research question does not fill the record. A finding whose record cannot be filled SHALL be a blocker, and every blocker SHALL carry a sentence naming the failed test and stating why the issue must be resolved before approval rather than during the thesis. That an element is not specified SHALL NOT by itself be such a reason.

The guidance SHALL state the **optional-part test**: an element the proposal declares optional is struck from the plan; when every research question remains answerable without it, its arrangements — capacity, agreements, scheduling — SHALL NOT be blockers; when a research question falls with it, the element is not optional, and that inconsistency is the blocker.

The guidance SHALL keep a **dependency safeguard**: an indispensable permission, ethics approval or data access — one without which a research question cannot be answered — whose availability is doubtful SHALL remain a blocker and SHALL NOT be deferred. Routine organisational detail and arrangements for optional evidence SHALL NOT be treated as such dependencies.

A methodology contract element SHALL be satisfiable by a stated selection rule or candidate set; the instance — an exact model version, a sample size fixed by a pilot, a concrete capture convention — MAY be chosen during the thesis and documented there.

The guidance SHALL state a **stopping rule**: a proposal with no blocker is ready, whatever number of clarify-early items or refinements remain. That more detail could be added SHALL NOT lower a verdict, and no judging skill SHALL require anything beyond the applicable guidelines — the shipped defaults and the workspace `guidelines.md`, whose prose MAY raise an item to a blocker for its program.

The guidance SHALL state that **review rounds are monotone**: a finding about text that is unchanged since an earlier round SHALL NOT move to a higher class than that round gave it, and a blocker that is new in a later round SHALL either concern text the revision introduced or changed, or be labelled as missed in the earlier round with the flaw it exposes stated. A title name that an earlier round reported only as a title refinement, without holding it to the swap test, SHALL count as such a miss when it fails that test: it SHALL return as the swap-test blocker with that label and the dependence it lacks stated, and the title refinement SHALL NOT be repeated beside it.

#### Scenario: Unspecified model versions
- **WHEN** a proposal comparing agent configurations states that the models are chosen at the start of the thesis by a stated rule and documented with their identifiers, and names none
- **THEN** the missing identifiers are a clarify-early item with a filled deferral record, not a blocker

#### Scenario: Optional expert feedback
- **WHEN** a proposal declares expert ratings optional and every research question is answered from data the student produces without them
- **THEN** reviewer capacity and company agreements for the ratings are not blockers

#### Scenario: Optional in name only
- **WHEN** a proposal calls an expert assessment optional but one research question can only be answered from that assessment
- **THEN** the inconsistency is a blocker under the method-fit or executability test

#### Scenario: Indispensable access in doubt
- **WHEN** the only data source for a research question is a partner company's internal records and access is still to be negotiated
- **THEN** the doubtful access is a blocker under the executability test, with a sentence saying why it must be settled before approval

#### Scenario: Blocker without a reason
- **WHEN** a judging skill would report "the audit sample size is not specified" as a blocker
- **THEN** the guidance rules it out: either the reviewer states why the question cannot be settled during the thesis, or the finding is a clarify-early item with its deferral record

#### Scenario: Ready with open decisions
- **WHEN** every substance test except possibly necessity passes and three clarify-early items remain
- **THEN** the proposal is ready

#### Scenario: Workspace raises the bar
- **WHEN** a workspace `guidelines.md` states that the ethics approval must be granted before a proposal is accepted
- **THEN** a missing approval is a blocker for proposals in that workspace

#### Scenario: Unchanged text does not climb
- **WHEN** an earlier round classified a passage's open decision as clarify-early and the revision left that passage unchanged
- **THEN** a later round does not report it as a blocker

#### Scenario: Decorative name blocks
- **WHEN** a proposal's research questions name a platform that nothing in its method, data or contribution depends on
- **THEN** the finding is a swap-test blocker whose reason says that either repair changes a research question or the contribution, so it cannot wait for the thesis

#### Scenario: Decorative name in the title alone
- **WHEN** a proposal's title names a platform that no research question, goal or contribution statement depends on
- **THEN** the finding is a swap-test blocker that carries the title's certificate consequence, its reason for not waiting is that the title is what the thesis is registered under and what the certificate prints, and the name is not reported as a second, non-blocking finding

#### Scenario: Decorative name missed in an earlier round
- **WHEN** an earlier round left a decorative name in unchanged text unreported
- **THEN** a later round reports it as a blocker only with the label missed in the earlier round and the flaw it exposes stated

#### Scenario: Title name an earlier round reported as a refinement
- **WHEN** an earlier round reported a platform name in the unchanged title only as a title refinement, without holding it to the swap test, and the name fails that test
- **THEN** a later round reports the swap-test blocker labelled missed in the earlier round with the dependence it lacks stated, and does not repeat the earlier title refinement beside it
