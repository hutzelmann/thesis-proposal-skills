## MODIFIED Requirements

### Requirement: Decorative names reach the student as a question
The supervise run SHALL apply the guidance's swap-test check of named choices as its shipped guidelines state it. That check covers the tools, systems, platforms and application domains the thesis names in its title, the purpose statement closing the introduction, the research focus and research questions, and the contribution's statements of what the thesis adds. The professor-side review file SHALL name the swap test for each failure.

A failure is a proposal blocker and SHALL be curated like any other blocker: it reaches the numbered points when it is among the five that most block a viable thesis. When it reaches the feedback, the point SHALL do three things:

- locate the name;
- ask the student what in the thesis would change if a comparable alternative stood in its place;
- give the direction: make explicit what the research depends on in it, or state the claim for the class it belongs to.

The point SHALL be written in the student's words, and the test's name SHALL NOT appear in the feedback. A name that passes the check SHALL NOT become a point.

#### Scenario: Decorative framework in a submission
- **WHEN** a submission's title and research questions name an agent framework that nothing in its method, data or contribution depends on, and fewer than five blockers stand
- **THEN** the review file carries a swap-test blocker on the framework, and the feedback opens with needs revision and carries a numbered point that names the framework, asks what would change if a comparable framework replaced it, and gives both directions

#### Scenario: Test name kept professor-side
- **WHEN** the review file reports a decorative name under the swap test
- **THEN** the feedback carries the point without the words "swap test"

#### Scenario: Framework as the object of study
- **WHEN** the submission's contribution states that the thesis evaluates the framework's own default configuration for the teams that run it, and no other blocker stands
- **THEN** the feedback opens with the ready tier and carries no numbered point

#### Scenario: Bachelor's submission with undecided claim scope
- **WHEN** a Bachelor's submission names a framework in its title, purpose, research focus and one research question, its contribution opens by claiming the gap for the general problem class and closes scoped to the framework, and it states no reason why the result is about the framework
- **THEN** the review file carries a swap-test blocker on the undecided claim scope, quoting a class-scoped and a framework-scoped claim, and the feedback carries a numbered point that names the framework, asks what would change if a comparable framework stood in its place, and offers the three directions that decide the scope: scope every gap to the framework, say why the result is about it, or state the claim for the class

#### Scenario: Guidelines are the operative text
- **WHEN** the supervise skill is installed without the review skill beside it
- **THEN** the swap-test check runs from the guidelines the supervise skill ships, with the same claim list, replacement and dependence rule as in the review skill

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

#### Scenario: Term keeps its qualifier
- **WHEN** a point or a swap-test scope entry cites a term from the proposal as a claim about the general class, and the sentence carrying the term qualifies it with the named platform
- **THEN** the point or the entry quotes the term with its qualifier or does not rest on it, because a term cut from its sentence is an elision too

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

## ADDED Requirements

### Requirement: Swap-test passes verified as claims about the proposal
Every name the review passes on the swap test SHALL enter the claim ledger as a claim about the proposal: the scope of each claim the test covers and, for an anchor other than the object of study, the sentence stating it, quoted. The fidelity check SHALL cover these entries, and the verification section SHALL list each pass. A refuted entry SHALL send the name back to the swap test; a failure there makes it a blocker, and the points and the tier SHALL be decided again.

#### Scenario: Pass carried by a stated sentence
- **WHEN** the review passes a framework because the contribution states that the framework ships the default configuration the teams that adopt it run
- **THEN** the ledger holds that sentence, quoted, the scope of each claim the test covers, and the comparable alternative put in its place with the quoted claim that would not stand with it, and the review's verification section lists the pass with the sentence

#### Scenario: Pass by consistent scope
- **WHEN** the review passes a framework as the object of study because every claim the test covers, the gap included, is scoped to it
- **THEN** the ledger quotes those instance-scoped claims as the text that carries the pass, the verification section lists the pass with them quoted, and the verifier checks their scope against the proposal

#### Scenario: No quoted text, no pass
- **WHEN** the only support for passing a platform is that the student's host organisation runs it, or an earlier review's remark, no sentence of the proposal states what the research needs from it, and the listed claims do not all put the gap and the result on it
- **THEN** no ledger entry can quote what carries the pass, the name does not pass, and the review carries the swap-test blocker

#### Scenario: Verifier disputes a pass
- **WHEN** the verifier finds that a pass's quoted sentence is not in the proposal or states only use, or that the scope list leaves out a class-scoped claim the contribution makes
- **THEN** the supervising agent judges the name again on the corrected entry; only a failure makes it a blocker, the points and the tier are then decided again, and the changed text is verified before hand-over

#### Scenario: Disputed list, pass stands
- **WHEN** the verifier adds a class-scoped gap to the scope list of a pass whose proposal states why the result is about the framework
- **THEN** the pass stands with the corrected list, and the verification section records the dispute and the decision

#### Scenario: Ledger omits a class-scoped sentence
- **WHEN** the ledger's scope list for a passed platform leaves out a class-scoped gap sentence of the contribution section that does not carry the name
- **THEN** the verifier disputes the entry as incomplete, without deciding whether the pass holds

#### Scenario: Ready tier resting on a pass
- **WHEN** the review is ready and a named platform in the title passed the swap test
- **THEN** that pass is verified like any other ledger entry before the ready feedback is handed over

#### Scenario: Inline verification of a pass
- **WHEN** no tool for starting a subagent is available
- **THEN** the supervising agent asks the fidelity question for each pass separately against the proposal's text, with its drafting reasoning set aside

#### Scenario: Verifier remit unchanged
- **WHEN** the verifier brief is read after this change
- **THEN** it still names six checks, carries the pass entries under fidelity to the proposal, names the claims the swap test covers, and needs no network for them

### Requirement: Earlier-round judgements re-examined on the text
An earlier round's pass of a name, or its remark that a name is the object of study, SHALL NOT shield it: the name SHALL be judged on the current text and, when it fails, SHALL return as a point recorded as missed in the earlier round. An earlier swap-test point withdrawn or demoted on unchanged text SHALL be recorded under the earlier-round section with its reason and SHALL enter the claim ledger as a pass.

#### Scenario: Earlier remark on the title name
- **WHEN** the earlier review called the framework in the title the object of study inside a title refinement, and the earlier feedback credited the student's access to it among what to keep, and the resubmitted text states no dependence on it
- **THEN** the new review carries the swap-test blocker labelled as missed in the earlier round, and the feedback carries the point marked as new

#### Scenario: Earlier point on unchanged text
- **WHEN** the earlier feedback raised the framework as a numbered point, and the passages it concerned are unchanged
- **THEN** the point stays open unless this round shows why it no longer applies; a withdrawn or demoted point is recorded under the earlier-round section with its reason, enters the ledger as a swap-test pass with its quoted text and scope list, and the verifier checks it as one

#### Scenario: Monotone classes still hold
- **WHEN** the earlier round listed an execution detail as a clarify-early item and the text is unchanged
- **THEN** it does not return as a point, because classes never climb on unchanged text except for a title name reported only as a title refinement, and a name's earlier pass is no class at all

### Requirement: Requested re-run read as an earlier round
A re-run the professor asks for over an earlier run's review or feedback for the same idea SHALL be an earlier round for the review: its points SHALL be carried into the earlier-round section with their status, a dropped one with its reason, also when its files are replaced. Its feedback SHALL be written as for a first intake, with no sentence on what a revision addressed and no point marked new.

#### Scenario: Redo on unchanged text
- **WHEN** the professor asks to redo and replace the feedback for a submission whose earlier feedback raised the framework as a point, and the text is unchanged
- **THEN** the new review lists that point under the earlier-round section as open, or as withdrawn with its reason, and the new feedback carries no revision sentence and no point marked new

#### Scenario: Redo keeps the earlier points on record
- **WHEN** the earlier review and feedback files are overwritten by the redo
- **THEN** their points survive inside the new review's earlier-round section
