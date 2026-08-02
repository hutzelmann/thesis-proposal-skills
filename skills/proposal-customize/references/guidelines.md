<!-- GENERATED from shared/ — edit shared/, then run scripts/sync_shared.py -->

# Exposé Guidelines

Default guidance for writing a Bachelor's or Master's thesis exposé at the Faculty of Computer Science, in English (default) or German.
The structure follows the THI exposé template (<https://github.com/ignacioalvmar/thesis_expose_template>), which the publish skill fills to produce the submitted document — so the section set here is not a house style, it is the shape of the artifact the supervisor receives.
The defaults are tuned for research at the intersection of applied AI, intelligent systems engineering, and human-computer interaction — the empirical, human-subjects, and simulation-based work typical of the HCIS Lab — but nothing here is domain-specific: a purely theoretical or systems thesis follows the same rules.
A workspace `guidelines.md` may override or extend these defaults; its TOML block wins per key, its lists replace the defaults, and it may un-forbid sections listed as forbidden here.
The machine-checkable skeleton (canonical section titles in both languages, section order, methodology subsections, forbidden headings, minimum reference count, research-question conventions) is defined in `structure.json`; this document is the authority for everything semantic.

## Exposé Structure

An exposé consists of exactly the seven canonical sections, in order (titles per `structure.json`):

1. **Introduction and Motivation** — Introduce the topic to a reader who knows the field but not this problem. Cover why it matters now, the concrete deficiency the thesis addresses, and what the work will and will not cover. Stay on a high level: no deep background, no technical details. Target 1–2 pages. Write it last.
2. **Problem Statement and Research Questions** — State the core problem in a few sentences, explain precisely why existing solutions are insufficient, then list the research questions as an ordered list. Target 0.5–1 page.
3. **Objectives** — Translate the research questions into concrete goals: one primary objective mapping to the main question, then supporting objectives. Target 0.5 pages.
4. **Related Work** — Position the thesis against the literature: the search strategy in brief, then thematic clusters, then the gap. Target 1–2 pages.
5. **Methodology: \<Methodology\>** — One methodology from the closed set (Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study, Controlled Experiment, Simulation Study, Empirical Model Evaluation, Mixed Methods) with its required subsections per `structure.json`. Target 1–2 pages.
6. **Expected Contributions and Results** — The anticipated scientific and practical value, the expected findings stated as expectations, and the foreseeable limitations. Target 0.5–1 page.
7. **Work Plan and Schedule** — The phases, milestones, and dependencies that show the project fits the available time. Target 1 page.

The rendered exposé shows section 5 as plain "Methodology"; the methodology name stays in the working file so the check can verify the right subsections are present.

An exposé declares exactly one methodology heading.
Research combining a qualitative and a quantitative strand declares **Mixed Methods** and uses that branch's subsections — it does not stack two methodology sections.
Choosing Mixed Methods to avoid deciding what the thesis actually measures is the failure mode this branch invites; take it only when the two strands genuinely answer different research questions and the Integration subsection can say how their results are combined.

The following must NOT appear in an exposé: a preliminary thesis chapter structure; supervisor names in the body (they belong on the title page, i.e. in the metadata block); deliverables or code fragments; personal data in the body text (matriculation number, address, email, study program); confidentiality markers of any kind (theses get published).

### Canonical Section Titles (English / German)

| English | German |
|---|---|
| Introduction and Motivation | Einführung und Motivation |
| Problem Statement and Research Questions | Problemstellung und Forschungsfragen |
| Objectives | Zielsetzung |
| Related Work | Verwandte Arbeiten |
| Methodology: {methodology} | Methodik: {methodology} |
| Expected Contributions and Results | Erwartete Beiträge und Ergebnisse |
| Work Plan and Schedule | Arbeitsplan und Zeitplan |

Methodology names and their required subsections. Every branch opens with **Use Case Definition**, which is the template's first Methodology subsection; the rest are branch-specific.

| English | German |
|---|---|
| Use Case Definition | Definition des Anwendungsfalls |
| Prototype Implementation | Prototypimplementierung |
| Previous Work | Vorarbeiten |
| Requirements | Anforderungen |
| Evaluation | Evaluation |
| Theoretical Analysis | Theoretische Analyse |
| Formalization | Formalisierung |
| Example | Beispiel |
| Systematic Literature Review | Systematische Literaturrecherche |
| Search Strategy and Selection Criteria | Suchstrategie und Auswahlkriterien |
| Extracted Information | Extrahierte Informationen |
| Synthesis | Synthese |
| User Study | Nutzerstudie |
| Preparation | Vorbereitung |
| Procedure | Durchführung |
| Analysis | Analyse |
| Controlled Experiment | Kontrolliertes Experiment |
| Independent Variables | Unabhängige Variablen |
| Dependent Variables | Abhängige Variablen |
| Statistical Analysis | Statistische Auswertung |
| Simulation Study | Simulationsstudie |
| Scenario Design | Szenariendesign |
| Execution | Durchführung |
| Empirical Model Evaluation | Empirische Modellevaluation |
| Data and Baselines | Daten und Baselines |
| Experimental Setup | Versuchsaufbau |
| Mixed Methods | Mixed Methods |
| Qualitative Strand | Qualitativer Strang |
| Quantitative Strand | Quantitativer Strang |
| Integration | Integration |

## Title Page Metadata

The template's title page is filled from the trailing metadata block, never from body text. Supply `title`, `author`, `student_id`, `degree_program`, `supervisor`, `second_supervisor`, `submission_date`, `subtitle`, `lang`, and `references`. Unknown values get a `[TODO: …]` placeholder rather than an invention. These fields are the only place personal data belongs; the body stays free of it.

## Research Questions

One to three research questions — the template's table holds three rows and the third is optional. More than three is a sign the scope is not yet decided; fold them together or drop one.

Research questions must be:

- specific and focused — neither too broad nor too narrow, addressing one concept at a time.
- self-contained — understandable without reading the rest of the exposé.
- feasible — answerable within the thesis timeline, through the chosen methodology and the analyses described in the methodology section.
- analytical — they require analysis, comparison, or evaluation ("to what degree", "under which conditions"). Never phrase a research question as an implementation goal ("how can X be implemented/designed/built") and never so it can be answered with a simple yes or no.
- non-overlapping — no question may be a refinement or near-duplicate of another.

The methodology section must reference every research question explicitly with `(RQ1)`, `(RQ2)`, … at the end of the sentence describing how that question is answered — one question per statement, never a collective reference like "(RQ1, RQ2 and RQ3)".

## Objectives Versus Research Questions

These are different things and the section order depends on the distinction: an objective describes what the work will **do**; a research question asks what the work will **find out**.

- Objectives start with an action verb — design, implement, evaluate, analyse, compare, develop, validate.
- One primary objective maps to the main research question; secondary objectives support it.
- "How can X be built" belongs in Objectives, never in the research questions. A proposal whose research questions read as construction goals usually has its objectives in the wrong section.
- Objectives are not a work plan: they say what will exist at the end, not when.

## Related Work

- Open with the search strategy in two or three sentences: which databases, which keywords, which date range.
- Group sources into thematic clusters, one subsection per cluster, never chronologically. Three clusters is a workable default: existing approaches, methodological foundations, and remaining gaps.
- Synthesize rather than summarize. A paragraph that walks through one paper after another is a reading list; compare, contrast, and name the limitation the cluster shares.
- Close by naming the gap the thesis fills, referring to the research questions explicitly.

## Methodology Content

Every branch opens with **Use Case Definition**: the application domain, system, or dataset that serves as the object of study, why it suits the research questions, and the constraints that come with it (access, size, language, licensing).

- **Prototype Implementation** — Previous Work: key tools and libraries supporting the prototype and how they are used. Requirements: what the prototype must do, and explicitly which requirements are neglectable. Evaluation: not correctness verification, but how the prototype answers the research questions (dataset, benchmark, metrics).
- **Theoretical Analysis** — Formalization: the mathematical model, logic, or type system. Requirements: expressiveness/soundness expectations, and what is neglectable. Example: the case study or running example illustrating the formalization.
- **Systematic Literature Review** — Search Strategy and Selection Criteria: what literature is included and excluded. Extracted Information: what is extracted (taxonomy, classification) and how deeply sources are analyzed. Synthesis: how extracted information is synthesized into answers.
- **User Study** — Preparation: study design, recruitment, and (if prototype-based) the prototype's scope with explicitly excluded properties. Procedure: tasks performed and data collected. Analysis: how collected data is analyzed to answer the research questions.
- **Controlled Experiment** — this is the branch the template's variable subsections were written for. Independent Variables: what is deliberately manipulated, with the levels of each. Dependent Variables: what is measured, each with its instrument or metric and unit. Procedure: what each participant does, in what order, with what counterbalancing. Statistical Analysis: the tests chosen per hypothesis, the significance level, the handling of multiple comparisons, and the target sample size with its justification — decided before data collection, not after. State the falsifiable hypotheses in the section's opening paragraph.
- **Simulation Study** — Scenario Design: the scenario space, its parameters, and how coverage of that space is argued. Execution: the simulator or testbed, the fidelity level, the number of runs, and what is deliberately abstracted away. Analysis: the metrics computed over the runs and how they answer the research questions. State the validity limits of simulated evidence explicitly; a simulation answers a question about the model unless the transfer to reality is argued.
- **Empirical Model Evaluation** — Data and Baselines: the datasets with their provenance and splits, and the baselines the contribution is measured against. Experimental Setup: training or inference configuration, hyperparameters, hardware, and the seeds or repetitions behind reported numbers. Analysis: the metrics per research question, the ablations that isolate the contribution, and how variance is reported. A single number without a baseline and without variance answers nothing.
- **Mixed Methods** — Qualitative Strand: its design, participants or artifacts, and analysis procedure (e.g. thematic analysis, coding scheme, inter-rater agreement). Quantitative Strand: its design, measures, and analysis, following the Controlled Experiment or Empirical Model Evaluation rules as applicable. Integration: which research questions each strand answers, whether the strands run sequentially or in parallel, and how their results are combined into one answer — this subsection is what distinguishes mixed methods from two unrelated small studies.

Close the section by naming the threats to validity the design carries and what bounds them.

### Choosing between the branches

- The contribution is an artifact and the evaluation exists to show the artifact works → **Prototype Implementation**.
- The contribution is a measured comparison between models, configurations, or algorithms → **Empirical Model Evaluation**.
- The contribution is a hypothesis-driven measurement involving human participants → **Controlled Experiment**.
- The interest is in how people experience, interpret, or appropriate a system, without a hypothesis to falsify → **User Study**.
- The evidence comes from executing a model of the world rather than the world → **Simulation Study**.

### Research involving human participants

This applies to User Study, Controlled Experiment, and any Mixed Methods proposal with a human strand. It is guidance, not a structural requirement — no separate section is expected, and the mechanical check does not enforce it — but a proposal that stays silent on all of it invites the first question a supervisor will ask.

- Name the ethics route the study will follow and the approval that is required before data collection starts.
- Describe informed consent: what participants are told, when, and how consent is recorded.
- State what personal data is collected, how it is pseudonymized or anonymized, how long it is retained, and on what legal basis (GDPR).
- Where a study exposes participants to risk — driving simulators, safety-critical interfaces, sustained attention tasks — say how that risk is bounded and how participants can stop.
- Where participants are compensated, say how, since it affects recruitment bias.

Do not turn this into a compliance appendix. Two or three precise sentences inside Preparation or Procedure are enough.

## Expected Contributions and Results

- Separate the scientific contribution (new knowledge, a validated model, a benchmark, an empirically tested framework) from the practical one (a prototype, tool, guideline, or design recommendation).
- Expected findings are stated as expectations — "the thesis expects that", "it is hypothesised that" — never as results already obtained. An exposé that asserts its outcome has stopped being a plan.
- Name the foreseeable limitations: sample size, generalisation, access, time. Reviewers value intellectual honesty over grand claims, and an unacknowledged limitation reads as an unnoticed one.
- Do not restate the objectives here. Objectives are what the work does; contributions are what remains afterwards for someone else.

## Work Plan and Schedule

- Cover the full processing period in phases, with the milestones that mark their boundaries: registration, mid-point check-in, submission.
- Express the plan at week granularity in a table with one row per task and explicit start and end weeks. The publish skill renders that table as the template's Gantt chart, so a row that lacks a week range cannot be drawn.
- Add three to five sentences naming the critical-path dependencies — which task cannot start before another finishes.
- Leave buffer before submission. A plan with every week committed is a plan that has not accounted for feedback rounds or data-collection problems.

## Literature and Citations

- Cite with `[@key]`; use `@key` (author-in-text) when naming the authors in the sentence — never both for the same work in one sentence.
- Reference keys follow `AuthorYearFirstWordOfTitle` (e.g. `Smith26Deep`), shorter than 20 characters.
- Every entry carries a DOI when one exists; add a URL only when there is no DOI. Include the abstract when available. Do not add volume, series, address, or page fields.
- Cite only keys that exist in the exposé's `references` block. Never fabricate publications. When a supporting source is missing, write `[TODO: add key reference for …]`.
- Avoid citing the same publication in consecutive sentences; use author-in-text form first, then stop repeating the citation.
- At least ten relevant scientific publications must be cited, and ten to fifteen is the working range for an exposé. Especially the introduction and the related-work section must ground their claims in the literature.
- Prefer peer-reviewed publications over preprints and over vendor or commercial web sources; vendor pages must never carry definitional or scientific claims.
- Published standards and regulations (ISO, IEEE, ETSI, SAE, UNECE, EU regulations) are legitimate — and often the only correct — sources for normative definitions, required behavior, and terminology. Cite the standard by its designation and year, never a vendor's summary of it. A standard establishes what is required; it never establishes that an approach works. Empirical claims still need peer-reviewed evidence.
- Judge relevance by venue as well as by keyword. In this field the substantive work sits in venues such as CHI, CSCW, UIST, IUI, AutomotiveUI, and TOCHI on the human-computer interaction side; NeurIPS, ICML, ICLR, CVPR, ICCV, and ECCV on the machine-learning side; and IEEE T-ITS, IEEE IV, ITSC, ICRA, and IROS on the intelligent-systems side. A hit from outside these families is not disqualified, but it earns its place by content rather than by matching the search terms.

## Writing Rules

- Language: English or German per the exposé's `lang`. In German, use English scientific terms with German capitalization and the canonical German section titles.
- Tone: professional, specific, concise. No vague language, no generalizations, no marketing.
- Avoid technical details irrelevant to the research questions or methodology; stay on the level of ideas and concepts.
- Define abbreviations at first use, e.g. "System on a Chip (SoC)". Abbreviations used more than once also belong in the `abbreviations` metadata field, which fills the template's List of Abbreviations.
- Active voice; avoid passive constructions (especially German "soll … werden" chains).
- Third person only ("the thesis", "the study") — no I/we/my/our.
- Short sentences, short paragraphs, one idea per paragraph. One sentence per line in the source file.
- Never start three consecutive sentences with the same word.
- No redundancy: never repeat the same information across sections.
- Missing information gets a visible `[TODO: 3–10 word hint]` marker — never invented content, never an unmarked gap. If unsure whether a statement is correct, mark it: `[TODO: verify this claim]`.

## Quality Checklist Before Handover

- Structure and content comply with all rules above (or the workspace overrides).
- Text is fluent, non-repetitive, free of grammar and spelling errors.
- All citations resolve; the literature is relevant and scientific, and there are at least ten sources.
- No TODO markers remain, including in the title-page metadata.
- The file renders cleanly (valid trailing metadata block, blank line before it) and the publish skill produces the LaTeX project without warnings.
