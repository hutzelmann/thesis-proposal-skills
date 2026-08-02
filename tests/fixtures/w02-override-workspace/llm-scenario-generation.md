# Introduction and Motivation

Automated driving functions are released only after they have been exercised against large catalogues of traffic scenarios [@Miller23Scenario].
Assembling those catalogues by hand is time-consuming and biased toward the situations engineers already anticipate [@Novak24Coverage].
Regulators now expect scenario coverage to be argued rather than asserted, which raises the cost of a hand-curated catalogue further [@Halbach22Envelope].
Large language models can read unstructured crash narratives and emit structured descriptions, which makes automated scenario synthesis plausible [@Chen25Learning].
Whether the synthesized scenarios are diverse and physically plausible enough to enter a validation toolchain is an open question [@Ibarra24Occlusion].
This thesis covers the generation and filtering of scenario descriptions; it does not cover closed-loop testing of a driving function against them.

# Problem Statement and Research Questions

Scenario catalogues grow by hand, so they encode the imagination of their authors rather than the distribution of real traffic conflicts.
Existing generation tools sample parameters inside manually authored templates, which varies the numbers but never the structure of the situation [@Miller23Scenario].
The consequence is that rare actor constellations remain absent from the catalogue no matter how many samples are drawn.
A generator that derives structure from real crash narratives could close that gap, but nothing is known about how reliable such a generator is or which narratives it fails on.

1. To what degree do language-model-generated scenarios cover manoeuvre constellations that are absent from a manually authored baseline catalogue?
2. Which properties of a crash narrative most strongly predict whether the generated scenario passes a physical plausibility filter?
3. To what degree does generation quality differ between narratives from different reporting databases?

# Objectives

The primary objective is to develop and evaluate a generation pipeline that turns natural-language crash narratives into executable scenario descriptions.

Supporting objectives:

- Design a prompting scheme that extracts actors, manoeuvres, and road geometry from an unstructured narrative.
- Implement a rule-based plausibility filter that rejects physically inconsistent constellations before simulation.
- Compare the generated catalogue against a manually authored baseline on manoeuvre coverage.
- Analyse which narrative properties predict filter rejection.

# Related Work

The literature was searched in the ACM Digital Library, IEEE Xplore, and Scopus, combining scenario-generation terminology with language-model and crash-analysis terminology, restricted to publications from 2018 onward.

## Scenario Generation for Automated Driving

Parameter-sampling approaches vary speeds, distances, and timings inside a fixed scenario template [@Miller23Scenario].
Search-based methods steer that sampling toward criticality, which finds harder instances of the templates already present [@Sorensen25Coverage].
@Novak24Coverage show that coverage arguments built on such catalogues inherit the blind spots of the template set.
The shared limitation is structural: none of these approaches introduces an actor constellation the template author did not foresee.

## Language Models for Structured Extraction

Language models extract structured records from accident and incident reports with usable accuracy [@Chen25Learning].
Schema-constrained decoding raises the share of outputs that parse without repair [@Iyer25Prompting].
@Duarte24Human report that human review remains necessary where the narrative is ambiguous about who acted first.
These results concern extraction quality in isolation and stop short of executing the extracted records.

## Plausibility Filtering and Remaining Gaps

Physical plausibility checks for generated trajectories exist as post-hoc criticality metrics [@Halbach22Envelope] and as constraint solvers over kinematic feasibility [@Ibarra24Occlusion].
Neither line has been applied to filter the output of a generative pipeline before simulation.
The gap this thesis addresses is therefore the combination: structure-level generation from narratives, filtered for plausibility, and measured against a manual baseline on coverage rather than on extraction accuracy (RQ1).

# Timeline

The work spans six months from corpus access to submission.

# Methodology: Prototype Implementation

## Use Case Definition

The object of study is the publicly available crash-narrative corpus of a national road-safety authority, paired with an open-source scenario description format and an open-source driving simulator.
This corpus suits the research questions because its narratives are written by trained investigators, so the described constellations are real rather than imagined, and because its reports carry structured metadata that supports the database comparison in the third research question.
Access is unrestricted, but the narratives are English-only and skew toward severe collisions, which bounds the claims to that population.

## Previous Work

The prototype builds on an open-source scenario description format and an established open-source driving simulator [@Miller23Scenario].
Generation uses a hosted language-model API with schema-constrained decoding, following the prompting scheme of @Iyer25Prompting.
The plausibility filter reuses a published kinematic feasibility formulation [@Ibarra24Occlusion].

## Requirements

The prototype must convert a narrative into a parameterized scenario file that the simulator executes without manual repair.
It must support vehicle-to-vehicle and vehicle-to-pedestrian constellations.
It must record, for every rejected scenario, which filter constraint failed.
Generation latency is not critical; focus lies on output quality.
Closed-loop coupling to a driving function under test is not a requirement.

## Evaluation

A held-out set of narratives is used to measure how much manoeuvre diversity the generated catalogue adds over the manual baseline, using a coverage measure over an established manoeuvre taxonomy (RQ1).
A feature-importance analysis over narrative properties — length, actor count, explicitness of the sequence — identifies which of them predict filter rejection (RQ2).
Generation quality is compared across two reporting databases whose narrative conventions are known to differ [@Weber24Narrative], using execution success rate and filter pass rate (RQ3).
Reporting of the pipeline follows published guidance for generative components in safety engineering, so that the prompting scheme and filter constraints remain reproducible [@Sato25Guidelines].
The main threat to validity is that coverage is measured against one taxonomy; a second taxonomy is applied as a robustness check.

# Expected Contributions and Results

Scientifically, the thesis contributes empirical evidence on whether narrative-driven generation widens scenario coverage, together with a characterisation of the narratives on which it fails.
The practical contribution is the generation and filtering pipeline itself, released with the prompting scheme and the filter constraints.
It is expected that the generated catalogue adds constellations absent from the baseline, and that narratives with implicit action ordering dominate the rejected set.
Limitations are foreseeable: a single corpus in a single language, a filter that checks kinematic rather than behavioural plausibility, and coverage measured against taxonomies that are themselves incomplete.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Corpus access and tooling setup | 1-3 |
| Baseline catalogue reconstruction | 3-6 |
| Prompting scheme and generation pipeline | 5-11 |
| Plausibility filter implementation | 9-14 |
| Coverage and prediction analysis | 14-18 |
| Second-database comparison | 17-20 |
| Writing and revision | 18-24 |

The critical path runs through the generation pipeline: the plausibility filter cannot be calibrated before the pipeline emits scenarios, and neither analysis can start before the filter is stable.
Baseline reconstruction is independent and therefore scheduled in parallel with tooling setup.
The second-database comparison is the designated cut if earlier phases overrun, because it addresses the narrowest research question.
Four weeks of overlap between analysis and writing absorb feedback rounds without moving the submission date.

---
title: Language-Model-Based Scenario Generation for Automated Driving Validation
author: Jane Doe
student_id: "[TODO: add student ID]"
degree_program: Master of Science in Computer Science
supervisor: Prof. Dr. Ignacio Alvarez
second_supervisor: TBD
submission_date: "[TODO: add submission date]"
subtitle: "Master's Thesis Proposal"
lang: en
abbreviations:
  ADAS: Advanced Driver Assistance Systems
  LLM: Large Language Model
  ODD: Operational Design Domain
references:
- id: Miller23Scenario
  type: paper-conference
  author:
  - family: Miller
    given: J.
  issued:
    year: 2023
  title: Scenario Catalogues Meet Automated Driving Validation Practice
  container-title: Proceedings of the Example Conference on Intelligent Vehicles
  DOI: 10.xxxx/xxxx1
- id: Chen25Learning
  type: article-journal
  author:
  - family: Chen
    given: L.
  issued:
    year: 2025
  title: Learning Scenario Structure from Crash Report Narratives
  container-title: Journal of Empirical Intelligent Transportation Examples
  DOI: 10.xxxx/xxxx2
- id: Novak24Coverage
  type: article-journal
  author:
  - family: Novak
    given: T.
  issued:
    year: 2024
  title: Coverage Blind Spots in Template-Based Scenario Catalogues
  container-title: Journal of Example Systems Validation
  DOI: 10.xxxx/xxxx3
- id: Halbach22Envelope
  type: article-journal
  author:
  - family: Halbach
    given: T.
  issued:
    year: 2022
  title: Envelope-Based Safety Guarantees for Automated Driving Functions
  container-title: Journal of Example Vehicle Safety
  DOI: 10.xxxx/xxxx4
- id: Ibarra24Occlusion
  type: paper-conference
  author:
  - family: Ibarra
    given: L.
  issued:
    year: 2024
  title: Kinematic Feasibility Checking for Generated Traffic Scenarios
  container-title: Proceedings of the Example Conference on Intelligent Vehicles
  DOI: 10.xxxx/xxxx5
- id: Sorensen25Coverage
  type: article-journal
  author:
  - family: Sorensen
    given: M.
  issued:
    year: 2025
  title: Search-Based Criticality Sampling for Scenario Catalogues
  container-title: Journal of Example Systems Validation
  DOI: 10.xxxx/xxxx6
- id: Iyer25Prompting
  type: article-journal
  author:
  - family: Iyer
    given: R.
  issued:
    year: 2025
  title: Prompting Strategies for Schema-Constrained Information Extraction
  container-title: Journal of Example Dependable Systems
  DOI: 10.xxxx/xxxx7
- id: Duarte24Human
  type: paper-conference
  author:
  - family: Duarte
    given: M.
  issued:
    year: 2024
  title: Human-in-the-Loop Review of Automatically Extracted Incident Records
  container-title: Proceedings of the Example Conference on Human Factors in Computing
  DOI: 10.xxxx/xxxx8
- id: Weber24Narrative
  type: article-journal
  author:
  - family: Weber
    given: S.
  issued:
    year: 2024
  title: Narrative Quality in National Crash Reporting Databases
  container-title: Journal of Example Traffic Safety Research
  DOI: 10.xxxx/xxxx9
- id: Sato25Guidelines
  type: article-journal
  author:
  - family: Sato
    given: H.
  issued:
    year: 2025
  title: Guidelines for Reporting Generative Pipelines in Safety Engineering
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xx10
---
