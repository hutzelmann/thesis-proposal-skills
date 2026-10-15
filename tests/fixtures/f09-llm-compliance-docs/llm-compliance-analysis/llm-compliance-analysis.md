## Introduction to the Topic

Regulatory frameworks such as the EU AI Act oblige providers of high-risk systems to maintain extensive technical documentation.
Producing and maintaining this documentation is laborious, and audits regularly reveal gaps between documented and actual system behavior.
Large language models can process both regulatory text and technical documentation, which makes automated support for compliance work plausible.
Whether such support is reliable enough for audit preparation remains an open question.
This thesis surveys the emerging research field at the intersection of language models and compliance documentation.

Contribution to the State-of-the-ArtPrior surveys either cover regulatory technology in general or focus on model documentation artifacts such as model cards.
A consolidated picture of how language models are applied to compliance documentation, which tasks they support, and how the resulting tools are evaluated is missing.
This thesis contributes that picture through a structured survey of the field and derives a research agenda from the identified gaps.

## Research Focus and Research Questions

The thesis maps how current research applies large language models to the creation and assessment of compliance documentation.
Special attention goes to the supported tasks, the documentation properties analyzed, and the evaluation practices of the field.

1. Which tasks in compliance documentation work does the literature support with large language models?
2. Which properties of technical documentation do the surveyed approaches analyze to detect compliance gaps?
3. Which criteria does the literature apply when evaluating language-model-based compliance tools?

## Methodology for Research: Systematic Literature Review

### Search Strategy and Selection Criteria

Four digital libraries are queried with a search string that combines language-model terminology with compliance and documentation terminology.
Included are peer-reviewed publications from 2020 onwards that apply a language model to a compliance-documentation task; excluded are purely legal analyses and vendor material.
Backward snowballing over the included studies compensates for the fast-moving terminology of the field.

### Extracted Information

Each included study is coded with the supported task, the model family used, the documentation properties analyzed, and the reported evaluation setup.
The coded tasks are aggregated into a task taxonomy of language-model support for compliance work (RQ1).
Analyzed documentation properties are consolidated into a property catalogue linked to the compliance gaps they reveal (RQ2).
In addition, a prototype extraction pipeline is implemented and run on public documentation samples to replicate the most frequently reported prompting strategies.

### Synthesis

The extracted evaluation setups are synthesized into a comparison of evaluation criteria, data sets, and reported limitations (RQ3).
Identified mismatches between supported tasks and evaluated criteria form the basis of the derived research agenda.

## Work Plan

| Phase | Weeks | Outcome |
|---|---|---|
| Pilot search and protocol | 1–4 | review protocol |
| Full search and selection | 5–10 | study pool |
| Extraction and coding | 11–18 | coded data set |
| Synthesis and writing | 19–26 | final thesis |

## References

---
references:
- id: Novak24Auditing
  type: paper-conference
  author:
  - family: Novak
    given: T.
  issued:
    year: 2024
  title: Auditing Machine Learning Documentation Against the EU AI Act
  container-title: Proceedings of the Example Conference on AI Governance
  DOI: 10.xxxx/xxx10
- id: Iyer25Prompting
  type: article-journal
  author:
  - family: Iyer
    given: R.
  issued:
    year: 2025
  title: Prompting Strategies for Regulatory Information Extraction
  container-title: Journal of Example Legal Informatics
  DOI: 10.xxxx/xxx11
- id: Beck23Compliance
  type: article-journal
  author:
  - family: Beck
    given: A.
  issued:
    year: 2023
  title: Compliance Checking of Technical Documentation — A Survey
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xxx12
---
