<!-- GENERATED from shared/ — edit shared/, then run scripts/sync_shared.py -->

# Proposal Guidelines

Default guidance for writing Bachelor's and Master's thesis proposals in computer science, in English (default) or German.
A workspace `guidelines.md` may override or extend these defaults; its TOML block wins per key, its lists replace the defaults, and it may allow sections again that are forbidden here.
Set `timeline_detail = "detailed"` there when a program demands a full work plan: the timeline then accepts tables, lists and subsections, and work-plan headings stop being forbidden. The default is `"simple"`.
The machine-checkable skeleton (canonical section titles in both languages, section order, methodology subsections, forbidden headings, minimum reference count, the timeline size limit, research-question conventions) is defined in `structure.json`; this document is the authority for everything semantic.

## Proposal Structure

A proposal consists of exactly the five canonical sections, in this order (titles per `structure.json`). The order is checked, not only the presence of each section.

1. **Introduction to the Topic** — Introduce the topic and explain why it is important and relevant. Stay on a high level: no deep background, no technical details. Refer to the thesis itself only at the end of the section.
2. **Contribution to the State-of-the-Art** — Explain the relevant current approaches without repeating the introduction. State explicitly and precisely how the thesis extends previous work; this delta is the heart of the proposal.
3. **Research Focus and Research Questions** — State the high-level research focus in a single paragraph that adds precision beyond the introduction, then list each research question as an item of an ordered list.
4. **Methodology for Research: \<Methodology\>** — One methodology from the closed set (Prototype Implementation, Theoretical Analysis, Systematic Literature Review, User Study) with its required subsections per `structure.json`. Never combine methodologies — decide on one and stick to it.
5. **Timeline** — One short sentence naming the month the thesis starts and the month it is submitted, or stating that it begins as soon as possible. Nothing else belongs here.

The timeline stays coarse: no table, no list, no subsections, at most three lines. Anything richer — a phase breakdown, a milestone table, a Gantt chart, whether written as markup or pasted in as an image — is forbidden content, not a fuller timeline. Never invent a timeframe the writer has not given you: an unknown one gets `[TODO: state start month and submission month, or "as soon as possible"]`, and "as soon as possible" is written only when the writer has actually said so, because a writer with a registered submission date would be misrepresented by it.

The following must NOT appear in a proposal: work plans, phase breakdowns or milestone tables; supervisor names; the author's own name; expected results; deliverables or code fragments; personal data (matriculation number, address, email, study program); a preliminary thesis chapter structure; confidentiality markers of any kind (theses get published).

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
| Extracted Information | Extrahierte Informationen |
| Synthesis | Synthese |
| User Study | Nutzerstudie |
| Preparation | Vorbereitung |
| Procedure | Durchführung |
| Analysis | Analyse |

## Research Questions

Research questions must be:

- specific and focused — neither too broad nor too narrow.
- self-contained — understandable without reading the rest of the proposal.
- answerable through the chosen methodology and the analyses described in the methodology section.
- analytical — they require analysis, comparison, or evaluation ("to what degree", "under which conditions"). Never phrase a research question as an implementation goal ("how can X be implemented/designed/built") and never so it can be answered with a simple yes or no.
- non-overlapping — no question may be a refinement or near-duplicate of another.

The methodology section must reference every research question explicitly with `(RQ1)`, `(RQ2)`, … at the end of the sentence describing how that question is answered — one question per statement, never a collective reference like "(RQ1, RQ2 and RQ3)".

## Methodology Content

- **Prototype Implementation** — Previous Work: key tools and libraries supporting the prototype and how they are used. Requirements: what the prototype must do, and explicitly which requirements are out of scope. Evaluation: not correctness verification, but how the prototype answers the research questions (dataset, benchmark, metrics).
- **Theoretical Analysis** — Formalization: the mathematical model, logic, or type system. Requirements: expressiveness/soundness expectations, and what is out of scope. Example: the case study or running example illustrating the formalization.
- **Systematic Literature Review** — Search Strategy and Selection Criteria: what literature is included and excluded. Extracted Information: what is extracted (taxonomy, classification) and how deeply sources are analyzed. Synthesis: how extracted information is synthesized into answers.
- **User Study** — Preparation: study design, recruitment, and (if prototype-based) the prototype's scope with explicitly excluded properties. Procedure: tasks performed and data collected. Analysis: how collected data is analyzed to answer the research questions.

## Literature and Citations

- Two citation forms, both usable in one proposal. `[@key]` renders as `[1]`: use it when the citation is evidence attached to a claim. `@key` renders as `Smith et al. [1]`: use it whenever the authors belong in the running text — as the subject ("@Smith26Deep propose a detector that …"), or as the possessor of the thing under discussion ("the detector of @Smith26Deep"). Apply the rule consistently — never both forms for the same work in one sentence.
- Never type an author name next to a bracketed citation (`Smith et al. [@Smith26Deep]`). The name in `@key` is derived from the reference entry, so it stays correct when the entry changes; a typed name does not.
- Author-in-text names by author count: one author `Smith`, two `Smith and Klein` (German: `Smith und Klein`), three or more `Smith et al.` These are produced automatically — do not write them out.
- Reference keys follow `AuthorYearFirstWordOfTitle` (e.g. `Smith26Deep`), shorter than 20 characters.
- Every entry carries a DOI when one exists; add a URL only when there is no DOI. Include the abstract when available. Do not add volume, series, address, or page fields.
- Cite only keys that exist in the proposal's `references` block. Never fabricate publications. When a supporting source is missing, write `[TODO: add key reference for …]`.
- Avoid citing the same publication in consecutive sentences; cite it once and then stop repeating the citation.
- At least three relevant scientific publications must be cited (workspace overrides may raise this). The introduction and the contribution section in particular must ground their claims in the literature.
- Prefer peer-reviewed publications over preprints and over vendor or commercial web sources; vendor pages must never carry definitional or scientific claims.

## Writing Rules

- Language: English or German per the proposal's `lang`. In German, use English scientific terms with German capitalization and the canonical German section titles.
- Tone: professional, specific, concise. No vague language, no generalizations, no marketing.
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
- The file renders cleanly (valid trailing metadata block, blank line before it).
