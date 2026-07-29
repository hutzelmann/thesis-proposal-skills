# AI-Boosted Thesis Proposal LaTeX Template

Help students write a convincing thesis proposal.

## File Structure

- `proposal.tex`: The main LaTeX file for the thesis proposal.
- `compactarticle.cls`: A custom LaTeX class file that defines the formatting and structure of the thesis proposal document. Do not touch this file unless explicitly requested.
- `literature.bib`: A BibTeX file containing the bibliography entries for the thesis proposal.

## Preface of `proposal.tex`

The preamble in `proposal.tex` should include the following:

- The document class declaration, which should be `\documentclass[usebib]{compactarticle}` and might include further options, e.g. `\documentclass[usebib,embedsources]{compactarticle}` to embed source files into the PDF.
- `\usepackage[english]{babel}` for English or `\usepackage[ngerman]{babel}` for German.
- The title and author declarations using `\title{}` and `\author{}` stating the title of the thesis and the name of the student working on the thesis.
- The title should be concise and informative, and should not include any technical terms or details that are not widely known in computer science.
- `\subtitle{Bachelor's Thesis Proposal}` or ` \subtitle{Master's Thesis Proposal}` depending on the level of the thesis.

## Literature in `literature.bib`

- Each entry should have a unique key.
- If possible, the key should be in the format `AuthorYearFirstWordOfTitle` (e.g. `Smith26Deep` for a paper by Smith published in 2026 with the title "Deep Learning for Computer Vision").
- Use short keys with less than 20 characters if possible.
- If the entry has a DOI, do not add a URL field.
- Check for every publication if it has a DOI and add it to the entry if possible. If the DOI is not available, add a URL field with a link to the publication if possible.
- Do not add volume, series, address or pages
- The given literature should be referenced in the document using `\cite{key}` where `key` is the unique key of the entry in the `literature.bib` file. Do not add references to keys that are not defined in the `literature.bib` file.
- If you want to refer the authors directly (e.g. `Author et al.`) use `\citeauthor{key}` where `key` is the unique key of the entry in the `literature.bib` file. Do not add another `\cite{key}` in the same sentence.
- Avoid citations to the same publication (with `\cite` or `\citeauthor`) in consecutive sentences. If you need to refer to the same publication in consecutive sentences, use `\citeauthor{key}` in the first sentence and avoid using `\cite{key}` in subsequent sentences.
- Do not add a bibliography section at the end of the document, as the bibliography will be automatically generated.
- Especially the introduction and the contribution to the state-of-the-art sections should reference the literature in `literature.bib` to support the statements made in these sections.
- The literature should contain at least three, relevant scientific publications that are related to the content of the proposal.

## Structure of a proposal

Any proposal written in `proposal.tex` must have the following sections in the following order:

- Introduction to the Topic
- Contribution to the State-of-the-Art
- Research Focus and Research Questions
- `Methodology for Research: <Methodolgy>` where `<Methodolgy>` is one of "Prototype Implementation", "Theoretical Analysis", "Systematic Literature Review", "User Study" depending on the chosen scientific method for the research.

The following sections must not be included in the proposal:

- Workplan, timeline or milestones
- Name of the supervisor(s)
- Expected results
- Deliverables or code fragments
- Personal data like Matriculation number, study program, email address, etc.
- Preliminary structure of the thesis (e.g. chapter structure, section structure, etc.)

## Section Content in Detail

### Introduction to the Topic

Introduce the topic of the thesis proposal, and explain why it is important and relevant.
The introduction should be on a higher level, and should not include too much background information or technical details.
The introduction should only refer to the thesis at the end of the section.

### Contribution to the State-of-the-Art

Explain the relevant, current approach to the topic from the introduction without repeating the information.
The contribution should clearly state how this thesis aims to extend the previous works in the field.
It is vital that this difference to previous work is stated explicitly and precisely.

### Research Focus and Research Questions

Clearly state the high level research focus in a single paragraph. Then state each research question as a separate `item` in a `\begin{RQs} ... \end{RQs}` environment.

The research questions should be
- specific and focused, and should not be too broad or too narrow.
- self-contained and understandable without referring to the rest of the proposal. Avoid research questions that require reading the rest of the proposal to understand them.
- answerable through the chosen scientific method and the analyses described in the methodology section.
- require analysis, comparison, or evaluation. Avoid research questions that can be answered with a simple yes or no.
- non overlapping, and should not be redundant or repetitive. Avoid research questions that are too similar to each other or research questions that are refinements of another research question.

### Methodology for Research: <Methodolgy>

The methodology section should have subsections in relation to the scientific method chosen for the research.
It shall refer explicitly to all research questions with (e.g. `(RQ1)`, `(RQ2)`, etc.) at the end of the sentence similar to a citation when describing how each of the research questions will be answered through the chosen scientific method.
Avoid generic references to research questions or a reference to all research questions in a single statement, e.g. "this step provides the structured evidence base (RQ1, RQ2 and RQ3)."
The following covers possible methodologies and lists the necessary subsections.

#### Prototype Implementation

The main focus of the work is the implementation of a prototype that will be used to answer the research questions.

- Previous Work. Describe which key tools and libraries will support the implementation of the prototype, and how they will be used.
- Requirements. Describe the requirements for the prototype, e.g. in terms of functionality, performance, etc. and also state requirements that are neglectable for the prototype.
- Evaluation. It shall not verify the correctness of the prototype, but describe how the prototype will be used to answer the research questions, e.g. naming a dataset or a benchmark, describing the evaluation metrics, etc.

#### Theoretical Analysis

This research does not implement any prototype, but is based on a theoretical analysis of a problem or a phenomenon.
The theoretical analysis is based on a formalization, e.g. in terms of a mathematical model, a logic, a type system, and deduces properties of the formalization.

- Formalization. e.g. a mathematical model, a logic, a type system, etc.
- Requirements. Describe the requirements for the formalization, e.g. in terms of expressiveness, soundness, etc. and also state requirements that are neglectable for the formalization.
- Example. Describe an example that will be used to illustrate the formalization, e.g. a case study, a running example, etc.

#### Systematic Literature Review

This research is based on a systematic literature review, which identifies, evaluates, and synthesizes the existing research on a specific topic around selected research question.

- Search strategy and selection criteria. Describe the literature to be included or excluded in the review
- Extracted information. What needs to be extracted from the included literature to answer the research questions, e.g. in terms of a taxonomy, a classification, etc. and how deep the included literature will be analyzed, e.g. in terms of a full text analysis, a meta-analysis, etc.
- Synthesis. Describe how the extracted information will be synthesized, e.g. in terms of a narrative synthesis, a thematic synthesis, etc. to potentially answer more research questions.

#### User Study

This research is based on a user study, which collects data from human participants using interaction with a prototype, a survey, an interview, etc. and analyzes the data to answer the research questions.

- Preparation. Describe the preparation for the user study, e.g. in terms of the design of the user study, the recruitment of participants, etc. If the user study is based on a prototype, the preparation should also include the implementation of the prototype, previous work and the key requirements for the prototype as defined in the prototype implementation scientific method above. As the prototype will not be fully functional, it is vital for the preparation to explicitly exclude properties not relevant for the user study, e.g. in terms of missing functionality, usage of mock-implementations, performance, etc.
- Procedure. Describe the procedure of the user study, e.g. in terms of the tasks to be performed, the data to be collected, etc. necessary to answer research questions.
- Analysis. Describe how the data collected in the user study will be analyzed, e.g. in terms of statistical analysis, qualitative analysis, etc. to elicit insights that will be used to answer research questions.

#### Mixtures of the above

Do not combine multiple scientific methods in the same thesis proposal. Decide for one scientific method and stick to it.

## Writing Rules (Important)

- Language: English or German.
- If you use German
    - use the English scientific terms with German capitalization.
    - Translate the section titles to German.
- Tone: professional, specific, and concise. Avoid vague language and generalizations.
- Avoid technical details that are not relevant to the research questions or the chosen scientific method. Focus on the high-level ideas and concepts.
- Do not use abbreviations or acronyms without defining them first. If you use an abbreviation or an acronym, define it in the text the first time you use it, e.g. "System on a Chip (SoC)".
- Avoid passive voice and use active voice instead.
- Avoid first-person pronouns (I, we, my, our, etc.) and use third-person pronouns (the thesis, the study, etc.) instead.
- Write short sentences and paragraphs. Avoid long and complex sentences.
- Avoid three or more consecutive sentences that start with the same word, e.g. "The thesis focuses", "The thesis will", "The thesis aims". Vary the sentence structure and the word choice to avoid monotony.
- Avoid redundancy and repetition. Do not repeat the same information in different sections.
- Keep every paragraph focused on a single idea or topic. Avoid mixing different ideas in the same paragraph.
- Do not fabricate publications or sources that do not exist
- If key information is missing, leave placeholders and flag clearly.
- Avoid grammar and spelling mistakes.


## Instructions for Agents

- Prefer minimal, surgical edits.
- Put one sentence per line.
- Minimize LaTeX code additional to the given structure of a proposal above.
- Do not edit `compactarticle.cls` unless explicitly requested.
- Do nut suggest the usage of `latexmk`, `pdflatex`, `biber` or similar for compiling the document, refer to the LaTeX workshop extension instead.
- The VScode extension LaTeX workshop automatically compiles the project after every file change.
- Do not add new tooling or dependencies unless explicitly requested.
- Use `\todo{text}` as a placeholder for missing information, and give a 3 to 10 word outline of what information is missing or how to fill the placeholder in the text, e.g. `\todo{Add a reference to a dataset}`.
- Avoid `\cite{\todo{Add key reference}}` constructions, instead just add `\todo{Add key reference}` as a placeholder for missing references to not cause invalid key errors.
- Stick close to the provided information and do not hallucinate additional facts. If you are not sure about the correctness of a statement, do not add it to the proposal. Instead, leave a placeholder or clear mark, e.g. `\todo{Check if this statement is correct}`.
- Do not add a `\maketitle` command, as the title and author information is already included in the preamble of `proposal.tex` and will be automatically rendered by the LaTeX class file.


## Quality Checklist Before Handover

- The document is compliant with all the above instructions and structure.
- Text is fluent, non-repetitive and does not contain redundant information.
- LaTeX syntax is valid (only existing commands, special chars escaped where needed).
- No grammar or spelling errors or other writing rule violations.
