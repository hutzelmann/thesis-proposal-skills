# Introduction to the Topic

Software organisations decide when a release is ready using a mixture of automated signals and accumulated judgement [@Bauer22Release].
Dashboards report test results, defect counts, and coverage, yet practitioners routinely override what the numbers suggest [@Novak23Signals].
Which signals actually carry weight in that decision, and which are consulted only to justify one already taken, is poorly understood.
This thesis studies that decision inside one organisation over a full release cycle.

# Contribution to the State-of-the-Art

Existing work measures release-readiness models against historical defect data and reports predictive accuracy [@Bauer22Release].
That approach assumes the decision is a prediction problem, and it cannot observe the deliberation that surrounds the numbers.
Interview studies capture practitioner opinion but are detached from any specific release [@Novak23Signals].
This thesis contributes an account of the decision as it is actually made, grounded in one organisation's artefacts and deliberations, and names which signals were decisive rather than merely available.

# Research Focus and Research Questions

The focus is the release-readiness decision in a single industrial organisation, observed across one release cycle, using the artefacts the organisation already produces.
The interest is in the relationship between the signals available and the signals used.

1. Which release-readiness signals do practitioners refer to when a release decision is contested, and to what degree do those differ from the signals their dashboards emphasise?
2. Under which conditions is an automated readiness signal overridden, and what reasoning is recorded when that happens?

# Methodology for Research: Case Study

## Case and Context

The case is a single product team of roughly thirty engineers releasing a hosted service on a six-week cadence.
The team suits the research questions because its release decisions are made in recorded meetings and its readiness dashboard is version-controlled, so both the available signals and the deliberation are observable.
Access is granted for one full release cycle, which bounds the study to a single case and rules out cross-case comparison.

## Data Collection

Three sources are drawn on: the recorded release-decision meetings, the dashboard configuration history, and the defect tracker at each decision point (RQ1).
Meeting recordings are transcribed and pseudonymised before analysis, and consent is obtained from every participant before the first recording.
Dashboard and tracker states are captured as snapshots at each decision, so the signals available at the time can be reconstructed rather than recalled (RQ2).

## Analysis

Transcripts are coded for references to readiness signals, with a codebook derived from the dashboard's own metrics and extended as unanticipated signals appear.
Coding is performed twice with the second pass blind to the first, and disagreements are resolved against the recording, following established practice for coding reliability [@Weber24Coding].
Overrides are analysed separately: each is traced to the recorded reasoning and to the signal state at that moment (RQ2).
A single case bounds what this can show — the account explains one organisation's practice and is not evidence about release decisions in general.

# Timeline

The thesis starts in March and is submitted in August.

---
title: Release-Readiness Signals in an Industrial Release Decision
subtitle: Master's Thesis Proposal
lang: en
references:
- id: Bauer22Release
  type: article-journal
  author:
  - family: Bauer
    given: T.
  issued:
    year: 2022
  title: Predicting Release Readiness from Historical Defect Data
  container-title: Journal of Example Software Engineering
  DOI: 10.xxxx/xxx20
- id: Novak23Signals
  type: paper-conference
  author:
  - family: Novak
    given: P.
  issued:
    year: 2023
  title: What Practitioners Look at Before Shipping
  container-title: Proceedings of the Example Conference on Software Practice
  DOI: 10.xxxx/xxx21
- id: Weber24Coding
  type: article-journal
  author:
  - family: Weber
    given: L.
  issued:
    year: 2024
  title: Coding Reliability in Qualitative Software Engineering Research
  container-title: Journal of Example Empirical Methods
  DOI: 10.xxxx/xxx22
---
