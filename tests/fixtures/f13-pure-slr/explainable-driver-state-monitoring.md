# Introduction and Motivation

Modern driver state monitoring increasingly relies on machine learning classifiers to separate attentive from inattentive driving [@Rahman22Deep].
Such classifiers reach high detection rates but rarely explain why a particular moment was flagged as drowsy.
Human-factors engineers must therefore review alerts without insight into the model's reasoning, which slows validation and erodes trust [@Okafor24Trust].
Explainable artificial intelligence (XAI) promises to expose this reasoning, and a growing number of studies apply XAI techniques to driver state monitoring [@Silva23Survey].
This thesis consolidates that scattered body of work in a systematic literature review.

# Problem Statement and Research Questions

The research focus is the intersection of explainability techniques and machine-learning-based driver state monitoring, restricted to peer-reviewed studies that evaluate their explanations.
Beyond mapping the field, the review assesses how rigorously explanation quality is measured and how well the techniques match the constraints of in-vehicle deployment.

1. Which explanation techniques have been applied to machine-learning-based driver state monitoring, and to what degree do they cover local as well as global model behaviour?
2. Under which conditions do the published evaluations demonstrate that the generated explanations are faithful to the underlying classifier?
3. To what degree do the proposed techniques account for the operational constraints of in-vehicle deployment, such as latency budgets and limited display real estate?

# Related Work

Existing secondary studies cover either XAI methods in general [@Silva23Survey] or machine-learning-based driver monitoring without regard to explainability [@Rahman22Deep].
No systematic review currently maps which explanation techniques have been applied to driver state monitoring, how their explanations are evaluated, and which practitioner needs remain unmet.
The review closes this gap and follows established guidelines for evidence synthesis in empirical research [@Kummer21Guidelines].
Its outcome is a taxonomy of applied techniques together with an assessment of evaluation rigour, which gives future work a validated starting point.
Faithfulness metrics for post-hoc explanations remain contested, and different metrics rank the same explainer differently [@Ferreira24Faithful].
@Delgado22Saliency show that saliency explanations over video can look plausible while being insensitive to the model's actual decision.
Human-factors work on in-vehicle information load bounds how much explanation a driver-facing display can carry [@Kaur23Load], and validation engineers turn out to need different explanations than drivers do [@Lindqvist25Engineers].
Existing taxonomies of explanation scope predate the video-based models that dominate driver monitoring [@Aranda21Taxonomy].
The datasets these models are trained on rarely document how their drowsiness labels were produced, which limits what any explanation of them can mean [@Beck24Drowsiness].

# Methodology: Systematic Literature Review

## Use Case Definition

The object of study is the peer-reviewed literature that applies explanation techniques to machine-learning-based driver state models and evaluates the resulting explanations.
This body suits the research questions because explanation faithfulness can only be assessed where an evaluation was actually reported, which excludes purely demonstrative papers.
The corpus is bounded to English-language publications indexed in three databases from 2016 onward, which is the coverage claim the review can support.

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

# Objectives

The primary objective is a taxonomy of explanation techniques applied to driver state monitoring, annotated with the rigour of their evaluation.

Supporting objectives:

- Define inclusion criteria that separate evaluated explanations from demonstrated ones.
- Extract technique, scope, model family, dataset, and evaluation method for every included study.
- Assess each study's evaluation against documented faithfulness criteria.
- Map the extracted deployment attributes against in-vehicle constraints.

# Expected Contributions and Results

The scientific contribution is a consolidated map of an area currently scattered across human-factors and machine-learning venues, with an explicit judgement of evaluation quality.
The practical contribution is a selection aid naming which techniques have evidence of faithfulness under in-vehicle constraints.
It is expected that local post-hoc techniques dominate, that faithfulness is asserted more often than measured, and that latency budgets are rarely reported at all.
Limitations are foreseeable: three databases, English only, and an assessment that can judge what studies report rather than what they did.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Protocol and pilot search | 1-3 |
| Database search and screening | 3-9 |
| Snowballing | 8-11 |
| Full-text extraction and coding | 10-17 |
| Taxonomy construction and synthesis | 16-21 |
| Writing and revision | 18-24 |

Screening is the critical path: the extraction schedule depends on how many studies survive it, so the protocol fixes the criteria before the search runs.
Snowballing overlaps screening because it draws on studies already accepted.
The final six weeks hold both synthesis and writing, with three weeks of overlap as buffer.

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
- id: Ferreira24Faithful
  type: article-journal
  author:
  - family: Ferreira
    given: J.
  issued:
    year: 2024
  title: Disagreement Among Faithfulness Metrics for Post-Hoc Explanations
  container-title: Journal of Example Machine Learning Research Examples
  DOI: 10.xxxx/xx51
- id: Delgado22Saliency
  type: paper-conference
  author:
  - family: Delgado
    given: R.
  issued:
    year: 2022
  title: Saliency Explanations over Video Are Not Always Sensitive to the Model
  container-title: Proceedings of the Example Conference on Computer Vision
  DOI: 10.xxxx/xx52
- id: Kaur23Load
  type: article-journal
  author:
  - family: Kaur
    given: S.
  issued:
    year: 2023
  title: Information Load Limits for In-Vehicle Displays
  container-title: Journal of Example Human Factors and Systems
  DOI: 10.xxxx/xx53
- id: Lindqvist25Engineers
  type: paper-conference
  author:
  - family: Lindqvist
    given: M.
  issued:
    year: 2025
  title: What Validation Engineers Want from Model Explanations
  container-title: Proceedings of the Example Symposium on Human Factors
  DOI: 10.xxxx/xx54
- id: Aranda21Taxonomy
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2021
  title: A Taxonomy of Explanation Scope
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xx55
- id: Beck24Drowsiness
  type: article-journal
  author:
  - family: Beck
    given: A.
  issued:
    year: 2024
  title: Drowsiness Datasets and Their Label Provenance
  container-title: Journal of Example Vehicular Intelligence
  DOI: 10.xxxx/xx56
---
