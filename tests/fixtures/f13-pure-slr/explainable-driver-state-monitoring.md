# Introduction to the Topic

Modern driver state monitoring increasingly relies on machine learning classifiers to separate attentive from inattentive driving [@Rahman22Deep].
Such classifiers reach high detection rates but rarely explain why a particular moment was flagged as drowsy.
Human-factors engineers must therefore review alerts without insight into the model's reasoning, which slows validation and erodes trust [@Okafor24Trust].
Explainable artificial intelligence (XAI) promises to expose this reasoning, and a growing number of studies apply XAI techniques to driver state monitoring [@Silva23Survey].
This thesis consolidates that scattered body of work in a systematic literature review.

# Contribution to the State-of-the-Art

Existing secondary studies cover either XAI methods in general [@Silva23Survey] or machine-learning-based driver monitoring without regard to explainability [@Rahman22Deep].
No systematic review currently maps which explanation techniques have been applied to driver state monitoring, how their explanations are evaluated, and which practitioner needs remain unmet.
The review closes this gap and follows established guidelines for evidence synthesis in empirical research [@Kummer21Guidelines].
Its outcome is a taxonomy of applied techniques together with an assessment of evaluation rigour, which gives future work a validated starting point.

# Research Focus and Research Questions

The research focus is the intersection of explainability techniques and machine-learning-based driver state monitoring, restricted to peer-reviewed studies that evaluate their explanations.
Beyond mapping the field, the review assesses how rigorously explanation quality is measured and how well the techniques match the constraints of in-vehicle deployment.

1. Which explanation techniques have been applied to machine-learning-based driver state monitoring, and to what degree do they cover local as well as global model behaviour?
2. Under which conditions do the published evaluations demonstrate that the generated explanations are faithful to the underlying classifier?
3. To what degree do the proposed techniques account for the operational constraints of in-vehicle deployment, such as latency budgets and limited display real estate?

# Methodology for Research: Systematic Literature Review

## Search Strategy and Selection Criteria

The search combines title and abstract terms for explainability with terms for driver state monitoring across the ACM Digital Library, IEEE Xplore, and Scopus.
Backward and forward snowballing on the included studies complements the database search.
Included are peer-reviewed publications since 2016 that apply an explanation technique to a machine-learning-based driver state model and report an evaluation of the explanations.
Excluded are position papers, purely conceptual work, and studies outside the in-vehicle domain.

## Extracted Information

For every included study, a structured form records the explanation technique, its scope, the model family, the datasets, the evaluation method for explanation quality, and the intended audience.
Extraction covers the full text of each study, and a second pass validates a random sample of the extracted records.

## Synthesis

Clustering the extracted techniques by scope and mechanism yields a taxonomy of explanation approaches in driver state monitoring (RQ1).
A structured comparison of the reported evaluation methods identifies the conditions under which faithfulness to the classifier is actually demonstrated (RQ2).
Mapping the extracted audience and deployment attributes against documented in-vehicle constraints reveals to what degree operational needs are addressed (RQ3).

---
title: Explainability in Machine-Learning-Based Driver State Monitoring
author: Jane Doe
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Rahman22Deep
  type: article-journal
  author:
  - family: Rahman
    given: T.
  issued:
    year: 2022
  title: Deep Classifiers for Driver Drowsiness Detection at Scale
  container-title: Journal of Example Vehicular Intelligence
  DOI: 10.xxxx/xxx10
- id: Silva23Survey
  type: article-journal
  author:
  - family: Silva
    given: M.
  issued:
    year: 2023
  title: Survey of Explainable Artificial Intelligence Methods
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xxx11
- id: Okafor24Trust
  type: paper-conference
  author:
  - family: Okafor
    given: C.
  issued:
    year: 2024
  title: Trust and Alert Review in Driver Monitoring Validation
  container-title: Proceedings of the Example Symposium on Human Factors
  DOI: 10.xxxx/xxx12
- id: Kummer21Guidelines
  type: article-journal
  author:
  - family: Kummer
    given: S.
  issued:
    year: 2021
  title: Guidelines for Systematic Reviews in Empirical Research
  container-title: Journal of Example Empirical Methods
  DOI: 10.xxxx/xxx13
---
