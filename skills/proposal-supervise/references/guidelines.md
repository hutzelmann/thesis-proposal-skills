<!-- GENERATED from shared/ — edit shared/, then run scripts/sync_shared.py -->

# Proposal Guidelines

Default guidance for writing Bachelor's and Master's thesis proposals in computer science, in English (default) or German.
A workspace `guidelines.md` may override or extend these defaults; its TOML block wins per key, its lists replace the defaults, and it may allow sections again that are forbidden here.
Set `[timeline] detail = "detailed"` there when a program demands a full work plan: the timeline then accepts tables, lists and subsections, and work-plan headings stop being forbidden. The default is `"simple"`. Every override key is the key path the value has in `structure.json`; a key that does not resolve to an overridable leaf is reported, never silently ignored.
The machine-checkable skeleton (canonical section titles in both languages, section order, methodology subsections, forbidden headings, minimum reference count, the timeline size limit, research-question conventions, the default page limit with its words-per-page estimation constant, the mechanically matchable title tells) is defined in `structure.json`; this document is the authority for everything semantic.

## The Thesis Title

The title is printed on your final study certificate. It outlives the proposal, the thesis, and the tools you used to write both, and it is read by people who will never see the document — so it carries more weight than any other line you write here.

A title names **what you contribute** and **what you contribute it about**, at a level of abstraction that stays true when the tool you happened to use is replaced by its successor. It stands on its own: the rendered title page shows title and subtitle, but the certificate shows the title alone, so a title that makes sense only next to the subtitle or your study program does not carry enough on its own. It states its subject rather than asking a question, and it stays inside the word bounds in `structure.json` — long enough to name a contribution, short enough to be read as one line.

Four kinds of title are problematic, and an agent working with you will raise every one of them:

- **A tool, product, vendor, or company name carried as the instrument.** The framework you build in, the platform you deploy to, the company you write the thesis at — none of them is your contribution. Name the problem class and the approach class instead.
- **Implementation framing.** "Development of …", "Implementierung einer …", "Konzept für ein …" reads as a work order, not as research. A thesis contributes an insight; state the insight.
- **Vagueness or grandiosity.** A whole research field ("Artificial Intelligence in Medicine") is not a thesis. On a certificate it reads as though nothing specific was done.
- **Marketing tone.** Promotional vocabulary borrowed from blog posts and vendor pages does not survive an academic reading.

A concrete technology may appear — but only as a scope qualifier, and only once you can say why that technology is the **object** of the study rather than the instrument of it. A systematic literature review of one platform's deployment patterns, or a user study of one specific development environment, genuinely is about that technology; a prototype that merely happens to be written in it is not.

The alarm is raised, never enforced: an agent tells you which class your title falls into, says that the title reaches your certificate, and offers one to three abstracted alternatives. It never rewrites your title silently and never refuses to continue. The decision stays yours — but if you keep a named technology, keep it because it is the object of study, not because changing the title is inconvenient.

## Proposal Structure

The file opens with the document itself, not with metadata: the first line is the thesis title as the file's only `# ` heading, followed by the subtitle as one emphasized paragraph — `*Bachelor's Thesis Proposal*` or `*Master's Thesis Proposal*` in English, `*Exposé zur Bachelorarbeit*` or `*Exposé zur Masterarbeit*` in German. The five canonical sections sit at `##` (methodology subsections at `###`), and the body closes with an empty references heading — `## References` in English, `## Literatur` in German — under which the built document renders the bibliography. The trailing metadata block carries only the `references` entries; the proposal's language is inferred from the canonical subtitle and section wordings, never declared.

A proposal consists of exactly the five canonical sections, in this order (titles per `structure.json`). The order is checked, not only the presence of each section.

1. **Introduction to the Topic** — Introduce the topic and explain why it is important and relevant. Stay on a high level: no deep background, no technical details. The section closes with one or two sentences stating what this thesis tries to achieve — the first and only place the introduction refers to the thesis itself, and the purpose the rest of the proposal unfolds. An introduction that motivates a topic but never states this purpose is unfinished.
2. **Contribution to the State-of-the-Art** — Explain the relevant current approaches without repeating the introduction. State explicitly and precisely how the thesis extends previous work; this delta is the heart of the proposal. Group the prior work into thematic clusters — never chronologically, never one publication per paragraph — and within a cluster compare and contrast rather than summarize, naming the limitation the cluster shares. A section that walks through one paper after another is a reading list, not a state of the art. Close by naming the gap the thesis fills and tying it to the research questions — and carry two more things in that close: why answering these questions will matter once they are answered, because significance is its own statement and the delta only names what is missing; and what kind of thing the thesis will deliver — a technique, a model, a tool or prototype, an evaluation of a specific instance, a report of findings. Naming the kind types the deliverable; asserting its content stays forbidden expected-results territory. This is also where the work describes what it will build or do; a construction goal belongs here, never among the research questions.
3. **Research Focus and Research Questions** — State the high-level research focus in a single paragraph that adds precision beyond the introduction, then list each research question as an item of an ordered list.
4. **Methodology for Research: \<Methodology\>** — One methodology from the closed set, with its required subsections per `structure.json`. Never combine methodologies — decide on one and stick to it. The set shipped here (Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Empirical Model Evaluation, Case Study) is a default, not a claim about which methodologies exist: a workspace `guidelines.md` may add branches, replace them, or disable ones its program does not accept, and the set that applies is always the one in `structure.json` after those overrides. What is not negotiable is the closure — whatever the set contains, a proposal declares exactly one member of it.
5. **Timeline** — One short sentence naming the month the thesis starts and the month it is submitted, or stating that it begins as soon as possible. Nothing else belongs here.

The timeline stays coarse: no table, no list, no subsections, at most three lines. Anything richer — a phase breakdown, a milestone table, a Gantt chart, whether written as markup or pasted in as an image — is forbidden content, not a fuller timeline. Never invent a timeframe the writer has not given you: an unknown one gets `[TODO: state start month and submission month, or "as soon as possible"]`, and "as soon as possible" is written only when the writer has actually said so, because a writer with a registered submission date would be misrepresented by it.

The following must NOT appear in a proposal: work plans, phase breakdowns or milestone tables; supervisor names; the author's own name; expected results; deliverables or code fragments; personal data (matriculation number, address, email, study program); a preliminary thesis chapter structure; confidentiality markers of any kind (theses get published).

Several of these prohibitions invert what many university templates require — milestone plans, expected-results sections, a named author. That is a deliberate stance of this guidance, not an oversight. Where a program requires such an element, the workspace `guidelines.md` honors it (a work plan via `[timeline] detail = "detailed"`, a named title page via the `author` key), so a contradicting template is a reason to configure the workspace, never to abandon the rest of the rules.

A proposal is anonymous: it carries no author name, neither in the text nor in the metadata block, and the rendered title page shows title and subtitle only. You are identified by the channel you submit it through — the email, the upload form, the filename — not by the document. If your program insists on a named title page, say so in your workspace `guidelines.md` and set `author` in the metadata block yourself; the check will still flag the key, which is expected in that case.

### Canonical Section Titles (English / German)

| English | German |
|---|---|
| Introduction to the Topic | Einführung in das Thema |
| Contribution to the State-of-the-Art | Beitrag zum Stand der Technik |
| Research Focus and Research Questions | Forschungsfokus und Forschungsfragen |
| Methodology for Research: {methodology} | Forschungsmethodik: {methodology} |
| Timeline | Zeitplan |

Methodology names and their required subsections:

| English | German |
|---|---|
| Prototype Implementation | Prototypimplementierung |
| Previous Work | Vorarbeiten |
| Requirements | Anforderungen |
| Evaluation | Evaluation |
| Theoretical Analysis | Theoretische Analyse |
| Formalization | Formalisierung |
| Example | Beispiel |
| Systematic Literature Review | Systematische Literaturrecherche |
| Search Strategy and Selection Criteria | Suchstrategie und Auswahlkriterien |
| Quality Assessment and Extracted Information | Qualitätsbewertung und extrahierte Informationen |
| Synthesis | Synthese |
| User Study | Nutzerstudie |
| Preparation | Vorbereitung |
| Procedure | Durchführung |
| Analysis | Analyse |
| Controlled Experiment | Kontrolliertes Experiment |
| Hypotheses and Variables | Hypothesen und Variablen |
| Design and Participants | Versuchsdesign und Teilnehmende |
| Statistical Analysis | Statistische Auswertung |
| Empirical Model Evaluation | Empirische Modellevaluation |
| Data and Baselines | Daten und Baselines |
| Experimental Setup | Versuchsaufbau |
| Analysis | Auswertung |
| Case Study | Fallstudie |
| Case and Units of Analysis | Fall und Analyseeinheiten |
| Data Collection | Datenerhebung |
| Analysis | Auswertung |

## Research Questions

One to five research questions. The upper bound is not a style preference: a proposal carrying more of them has usually not decided what it is measuring, and the extra questions turn out to be refinements of one another or work for a second thesis. Fold them together or drop one — a workspace may raise or lower both bounds.

Research questions must be:

- specific and focused — neither too broad nor too narrow.
- self-contained — understandable without reading the rest of the proposal.
- answerable through the chosen methodology and the analyses described in the methodology section.
- analytical — they require analysis, comparison, or evaluation ("to what degree", "under which conditions"). Never phrase a research question as an implementation goal ("how can X be implemented/designed/built") and never so it can be answered with a simple yes or no.

A goal and a question are different things, and confusing them is why the implementation phrasing keeps appearing: a goal says what the work will **do** and starts with a verb like design, implement, evaluate, compare; a question asks what the work will **find out**. Both belong in the proposal — the goal in the contribution section, where the work describes itself, and the question here. A research-question list that reads as a build plan usually means the goals were written in the wrong section, so move them rather than deleting them.

State a construction goal in its full shape: which context the work improves, by which artifact, satisfying which requirements, in order to serve whose goal. A goal carrying all four parts brings its own justification, and its requirements are what the methodology's evaluation can later be checked against. Where the contribution is an artifact, derive the research questions from that stated goal — what effects the artifact has measured against its requirements, how it compares to alternatives, under which conditions the results hold. A goal in the contribution section whose research questions never touch it is two unrelated proposals in one document.

One nuance for reviewing, not for writing: "how can X be done" is legitimate research when the answer is a method that generalizes beyond one instance. The test is whether the answer generalizes, never the question word — a one-off build target fails it, which is why the rule above stands unchanged.
- non-overlapping — no question may be a refinement or near-duplicate of another.

The methodology section must reference every research question explicitly with `(RQ1)`, `(RQ2)`, … at the end of the sentence describing how that question is answered — one question per statement, never a collective reference like "(RQ1, RQ2 and RQ3)".

## Substance Tests

A proposal that satisfies every structural rule can still be empty.
Five tests define the substance bar; agents judging a proposal cite them by these names, and a proposal that fails them is not ready no matter how cleanly it checks:

- **Delta test** — the proposal states precisely what the thesis adds beyond the work it cites: what it confirms, refutes, or extends. A contribution section that reads as a feature list or restates the field fails; confirming or refuting a published finding under new conditions passes, because extending is not the only admissible delta.
- **Falsifiability test** — the research questions can come out negative. A question whose every conceivable outcome counts as success fails.
- **Swap test** — the proposal's core statements could not equally describe ten other theses in the area. Text that stays plausible after swapping the topic noun fails as generic.
- **Method-fit test** — the methodology concretely answers each research question. Method prose that never touches the questions is boilerplate and fails.
- **Executability test** — the proposal gives concrete, actionable goals: it names the objects of study (dataset, system, population, corpus), states a concrete evaluation, is feasible in the stated months, and makes clear what the student would actually do first.

## Methodology Content

These are the content contracts for the shipped branches. A workspace that declares its own branch carries that branch's contract in the declaration itself — read it there, and never fill a workspace subsection from a shipped branch that happens to have a similar name.

Whatever the branch, the methodology section opens with one or two sentences stating why this methodology answers these research questions — the method-fit test written down by the student, not left for a reviewer to reconstruct. A section that starts at its first subsection has skipped its own justification.

- **Prototype Implementation** — Previous Work: key tools and libraries supporting the prototype and how they are used. Requirements: what the prototype must do, and explicitly which requirements are out of scope. Evaluation: not correctness verification, but how the prototype answers the research questions (dataset, benchmark, metrics) — name the empirical form the evaluation takes (a benchmark, a controlled measurement, a case study, a simulation) and compare against the state-of-the-art alternatives the contribution section cites, or state why comparing is impractical. Naming the form is part of this methodology, not a second one. The contract follows the design-science evaluation guidance of Hevner et al. (2004) and the ACM SIGSOFT Engineering Research standard.
- **Theoretical Analysis** — Formalization: the mathematical model, logic, or type system. Requirements: expressiveness/soundness expectations, and what is out of scope. Example: the case study or running example illustrating the formalization. The contract is house guidance: no community reporting standard exists for formal work, and the branch corresponds to the formal-theory strategy in Stol and Fitzgerald's (2018) framework.
- **Systematic Literature Review** — Search Strategy and Selection Criteria: what literature is included and excluded; frame the review question and derive the search terms along PICOC (population, intervention, comparison, outcome, context) — a shape that serves this branch and misleads elsewhere. Quality Assessment and Extracted Information: how the quality of included studies is assessed and whether the assessment excludes or merely weights them, plus what is extracted (taxonomy, classification) and how deeply sources are analyzed; a mapping-style review that legitimately skips per-study assessment says so here and states why breadth replaces depth. Synthesis: how extracted information is synthesized into answers, declaring whether a formal meta-analysis is intended or the synthesis stays narrative. The contract compresses the review protocol of Kitchenham and Charters (2007); mapping-style variants follow Petersen et al. (2008, 2015).
- **User Study** — observational, usability, and survey-style research with human participants; a study that manipulates a treatment to test a hypothesis is a Controlled Experiment, not a User Study. Preparation: study design, recruitment, and (if prototype-based) the prototype's scope with explicitly excluded properties. Procedure: tasks performed and data collected. Analysis: how collected data is analyzed to answer the research questions. The contract corresponds to the questionnaire-survey and interview-study guidance in the ACM SIGSOFT Empirical Standards.
- **Controlled Experiment** — hypothesis testing with manipulated treatments, with human participants or programmed subjects. Hypotheses and Variables: the hypotheses being tested and, named separately, the independent variables with their treatments (what is manipulated) and the dependent variables with their measures (what is measured), plus known confounding factors. Design and Participants: the experiment design (within- or between-subjects, factorial), how participants are recruited and assigned — random assignment, or a justified quasi-design — and the tasks or instruments used. Statistical Analysis: the planned tests as a consequence of the chosen design, the significance level, and the main threats to validity. The contract compresses the experiment-planning steps of Wohlin et al. (2012) and the ACM SIGSOFT Experiments standard.
- **Empirical Model Evaluation** — training or selecting models and evaluating them against baselines on datasets; benchmark-style comparisons of existing models or tools use this branch too. Data and Baselines: which datasets, where they come from and under what license, and the state-of-the-art baselines compared against — or why no baseline exists. Experimental Setup: the train/validation/test protocol including how leakage between splits is prevented, plus models, features, and infrastructure. Analysis: which metrics answer the research questions and why those, and how variance across runs is handled. The contract follows the ACM SIGSOFT Data Science standard and Raschka's (2018) model-evaluation guidance.
- **Case Study** — deep study of one real case in its natural setting, observed rather than manipulated; a thesis that changes the studied organisation's process and evaluates the change is action research, which the shipped set does not contain — a workspace may declare it. Case and Units of Analysis: what the case is and its context, the units of analysis within it, why this case suits the research questions — selection is intentional (a typical, critical, or revelatory case), never a sample — and what access exists. Data Collection: which sources are drawn on and how each is recorded, with more than one source so findings can be triangulated, and with consent and confidentiality toward the host organisation addressed. Analysis: how the material is coded and synthesised into answers, and what a single case can and cannot show. The contract compresses the case-study plan elements of Runeson and Höst (2009) and the ACM SIGSOFT Case Study standard.

Whatever the branch, say what the work will yield as an expectation — "the thesis expects", "it is hypothesized" — never as a result already obtained; a proposal that asserts its outcome has stopped being a plan. Name the foreseeable limitations too (sample size, generalization, access, time): a reviewer values an acknowledged limitation over a grand claim, and an unacknowledged one reads as an unnoticed one. None of this is an expected-results section, which stays forbidden — it is how the claims the proposal already makes are phrased.

### Research involving human participants

Guidance, not a required section, and nothing here is mechanically checked — but a proposal that stays silent on all of it invites the first question a supervisor will ask. Two or three precise sentences inside Preparation or Procedure are enough; this is not a compliance appendix.

- Name the ethics route the study follows and the approval needed before data collection starts.
- Describe informed consent: what participants are told, when, and how consent is recorded.
- State what personal data is collected, how it is pseudonymized or anonymized, how long it is kept, and on what legal basis.
- Where the study exposes participants to risk — driving simulators, safety-critical interfaces, sustained-attention tasks — say how that risk is bounded and how a participant can stop.
- Where participants are compensated, say how, because it affects who volunteers.

### Research on secondary data

The same advisory style applies to work on mined, scraped, or third-party data — repository histories, public datasets, crawled documents. One or two sentences inside the methodology are enough, and nothing here is mechanically checked:

- Name where the data comes from and under which license or terms it may be used for research.
- Say whether the data contains personal data — names and emails in commit metadata count — and how that is handled.
- Where derived data or the dataset itself is to be published, say whether the terms permit it.

## Literature and Citations

- Two citation forms, both usable in one proposal. `[@key]` renders as `[1]`: use it when the citation is evidence attached to a claim. `@key` renders as `Smith et al. [1]`: use it whenever the authors belong in the running text — as the subject ("@Smith26Deep propose a detector that …"), or as the possessor of the thing under discussion ("the detector of @Smith26Deep"). Apply the rule consistently — never both forms for the same work in one sentence.
- Never type an author name next to a bracketed citation (`Smith et al. [@Smith26Deep]`). The name in `@key` is derived from the reference entry, so it stays correct when the entry changes; a typed name does not.
- Author-in-text names by author count: one author `Smith`, two `Smith and Klein` (German: `Smith und Klein`), three or more `Smith et al.` These are produced automatically — do not write them out.
- Reference keys follow `AuthorYearFirstWordOfTitle` (e.g. `Smith26Deep`), shorter than 20 characters.
- Every entry carries a DOI when one exists; add a URL only when there is no DOI. Include the abstract when available. Do not add volume, series, address, or page fields.
- Cite only keys that exist in the proposal's `references` block. Never fabricate publications. When a supporting source is missing, write `[TODO: add key reference for …]`.
- Avoid citing the same publication in consecutive sentences; cite it once and then stop repeating the citation.
- Three relevant scientific publications is the mechanical floor, not the target: it catches an empty bibliography and nothing more, and a proposal sitting exactly at the floor has a thin literature base whatever the check says. The working range is not a quota — it follows from the coverage this document already demands: each thematic cluster in the contribution section needs at least two sources to show a theme rather than an anecdote, each research question's motivation needs grounding, and the introduction grounds its claims in the literature. For a five-page proposal that lands at ten to fifteen references — roughly four to six per thousand words — and the expectation scales with the document: mechanical checks warn below `[references] min_per_1000_words` (default 4) of the body's actual length, never fail. Workspace overrides may raise the floor or adjust the density. The introduction and the contribution section in particular must ground their claims in the literature.
- Prefer peer-reviewed publications over preprints and over vendor or commercial web sources; vendor pages must never carry definitional or scientific claims.
- Published standards and regulations (ISO, IEEE, ETSI, SAE, UNECE, EU regulations) are legitimate — and often the only correct — sources for normative definitions, required behavior, and terminology. Cite the standard by its own designation and year, never a vendor's or a blog's summary of it. The limit is exact: a standard establishes what is *required*, never that an approach *works*, so an empirical claim still needs peer-reviewed evidence.

## Writing Rules

- Language: English or German per the proposal's `lang`. In German, use English scientific terms with German capitalization and the canonical German section titles.
- Tone: professional, specific, concise. No vague language, no generalizations, no marketing.
- Every sentence carries information essential to this thesis. Scene-setting openers, truisms, and restatements of the obvious are filler: delete them. Shortness comes from deleting low-information sentences, not from compressing wording.
- The rendered proposal stays within five pages (workspace `[length] page_limit` overrides this). The bound is deliberately generous — a proposal that respects the density rule stays well under it. Mechanical checks estimate pages from word count and warn, never fail.
- Avoid technical details irrelevant to the research questions or methodology; stay on the level of ideas and concepts.
- Define abbreviations at first use, e.g. "System on a Chip (SoC)".
- Active voice; avoid passive constructions (especially German "soll … werden" chains).
- Third person only ("the thesis", "the study") — no I/we/my/our.
- Short sentences, short paragraphs, one idea per paragraph. One sentence per line in the source file.
- Never start three consecutive sentences with the same word.
- No redundancy: never repeat the same information across sections.
- Missing information gets a visible `[TODO: 3–10 word hint]` marker — never invented content, never an unmarked gap. If unsure whether a statement is correct, mark it: `[TODO: verify this claim]`.

## Quality Checklist Before Hand-In

- Structure and content comply with all rules above (or the workspace overrides).
- Text is fluent, non-repetitive, free of grammar and spelling errors.
- All citations resolve; the literature is relevant and scientific.
- No TODO markers remain.
- The file renders cleanly (leading `# ` title line, emphasized subtitle paragraph, closing references heading, valid trailing metadata block with a blank line before it).
