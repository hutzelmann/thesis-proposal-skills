
# Introduction and Motivation

Safety standards such as ISO 26262 and ISO 21448 oblige developers of automated driving functions to maintain extensive safety-argument documentation.
Producing and maintaining this documentation is laborious, and assessments regularly reveal gaps between the documented argument and the actual system behavior.
Large language models can process both standard text and technical documentation, which makes automated support for safety-argument work plausible.
Whether such support is reliable enough for assessment preparation remains an open question.
This thesis surveys the emerging research field at the intersection of language models and safety-case documentation.

Contribution to the State-of-the-ArtPrior surveys either cover assurance-case tooling in general or focus on machine-learning documentation artifacts such as model cards.
A consolidated picture of how language models are applied to safety-case documentation, which tasks they support, and how the resulting tools are evaluated is missing.
This thesis contributes that picture through a structured survey of the field and derives a research agenda from the identified gaps.

# Problem Statement and Research Questions

The thesis maps how current research applies large language models to the creation and assessment of safety-case documentation for automated driving.
Special attention goes to the supported tasks, the documentation properties analyzed, and the evaluation practices of the field.

1. Which tasks in safety-case documentation work does the literature support with large language models?
2. Which properties of technical documentation do the surveyed approaches analyze to detect argument gaps?
3. Which criteria does the literature apply when evaluating language-model-based safety-case tools?

# Methodology: Systematic Literature Review

## Use Case Definition

[[USE_CASE]]

## Search Strategy and Selection Criteria

Four digital libraries are queried with a search string that combines language-model terminology with safety-case and documentation terminology.
Included are peer-reviewed publications from 2020 onwards that apply a language model to a safety-documentation task; excluded are purely normative analyses and vendor material.
Backward snowballing over the included studies compensates for the fast-moving terminology of the field.

## Extracted Information

Each included study is coded with the supported task, the model family used, the documentation properties analyzed, and the reported evaluation setup.
The coded tasks are aggregated into a task taxonomy of language-model support for safety-argument work (RQ1).
Analyzed documentation properties are consolidated into a property catalogue linked to the argument gaps they reveal (RQ2).
In addition, a prototype extraction pipeline is implemented and run on public safety-case samples to replicate the most frequently reported prompting strategies.

## Synthesis

The extracted evaluation setups are synthesized into a comparison of evaluation criteria, data sets, and reported limitations (RQ3).
Identified mismatches between supported tasks and evaluated criteria form the basis of the derived research agenda.

# Work Plan

| Phase | Weeks | Outcome |
|---|---|---|
| Pilot search and protocol | 1–4 | review protocol |
| Full search and selection | 5–10 | study pool |
| Extraction and coding | 11–18 | coded data set |
| Synthesis and writing | 19–26 | final thesis |

---
lang: en
references:
- id: Novak24Auditing
  type: paper-conference
  author:
  - family: Novak
    given: T.
  issued:
    year: 2024
  title: Auditing Safety Arguments for Automated Driving Functions
  container-title: Proceedings of the Example Conference on System Safety
  DOI: 10.xxxx/xxx10
- id: Iyer25Prompting
  type: article-journal
  author:
  - family: Iyer
    given: R.
  issued:
    year: 2025
  title: Prompting Strategies for Safety Requirement Extraction
  container-title: Journal of Example Dependable Systems
  DOI: 10.xxxx/xxx11
- id: Beck23Compliance
  type: article-journal
  author:
  - family: Beck
    given: A.
  issued:
    year: 2023
  title: Compliance Checking of Safety Documentation — A Survey
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xxx12
---
