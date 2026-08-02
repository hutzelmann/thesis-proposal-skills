# Introduction and Motivation

Automated driving test fleets collect high-frequency data from dozens of sensors distributed across every vehicle [@Hoffmann23Visual].
Automated detectors flag perception failures such as dropped tracks and implausible object states, but engineers still decide which alarms deserve investigation.
This triage step is a bottleneck: alarm floods overwhelm engineers, and relevant failures drown in false positives [@Iyer25Anomaly].
The thesis addresses this bottleneck with an interactive visual analytics approach for perception-alarm triage.

# Problem Statement and Research Questions

The research focus lies on how explanation-based grouping and ranking of alarms changes triage efficiency in automated driving validation.

1. To what degree does explanation-based grouping reduce the number of triage decisions per test campaign compared to chronological alarm lists?
2. Under which failure characteristics does the ranking place relevant alarms in the top positions of the queue?
3. How does triage accuracy change when engineers act on grouped alarms instead of individual ones?

# Related Work

Visual analytics research for driving data concentrates on scenario exploration and pattern search rather than on alarm handling [@Hoffmann23Visual].
Explanation methods attach feature attributions to individual perception failures but do not aggregate them into a ranked work queue [@Iyer25Anomaly].
@Duarte24Human show that engineer labeling of perception failures improves detector precision, yet their interface presents alarms as an unordered list.
This work combines detector explanations with an interactive ranking view so engineers can dismiss whole alarm groups instead of single alarms.
Alarm-fatigue research outside driving documents the same dismissal behaviour under high false-positive rates [@Ferreira22Fatigue].
@Kaur24Grouping show that grouping by explanation similarity outperforms grouping by signal similarity when the detector is a learned model.
Ranking-quality metrics for work queues are established [@Delgado23Ranking], and the labelling conventions of public driving benchmarks determine what counts as a perception failure at all [@Lindqvist25Benchmark].
Surveys of validation practice put alarm triage among the larger recurring workloads in test-fleet operation [@Aranda23Triage].
Exposing a clustering threshold to the user is a documented interface pattern with known calibration pitfalls [@Beck24Threshold].
Replay experiments substitute for operator studies where the ground truth is known, at the cost of modelling rather than observing behaviour [@Novak25Replay].
Figure 1 summarizes the proposed pipeline from raw sensor recordings to the ranked queue.

![Figure 1: Overview of the proposed triage pipeline from raw sensor recordings to the ranked alarm queue](img/perception-alarm-triage-a.png)

# Methodology: Prototype Implementation

## Use Case Definition

The object of study is the alarm stream of an automated driving test fleet, replayed from a public driving benchmark whose perception failures are labelled.
This use case suits the research questions because triage effort can only be counted where the ground-truth failures are known, which live fleet data does not provide.
The benchmark is openly licensed; it covers highway and urban daytime driving only, which bounds the claims to that operating range.

## Previous Work

The prototype builds on an open-source dashboard framework and a published anomaly-detection library for streaming data.
Detector explanations reuse the attribution method introduced by @Iyer25Anomaly.
A labeled failure dataset from a public driving benchmark provides ground truth for ranking quality.
Figure 2 sketches how the grouped queue view extends a standard alarm list.

![Figure 2: Interface sketch of the grouped alarm queue with explanation summaries](img/perception-alarm-triage-b.png)

## Requirements

The prototype must ingest recorded sensor streams and update the ranked queue within seconds.
It must group alarms by explanation similarity and expose the grouping threshold as a user-facing control.
Visual polish and multi-user support are explicitly neglectable.

## Evaluation

A replay experiment on the benchmark dataset counts triage decisions per simulated campaign under grouped and chronological queues (RQ1).
The fraction of injected failures among the top queue positions measures ranking quality across failure types (RQ2).
Comparing triage outcomes against ground-truth labels quantifies accuracy for grouped versus individual handling (RQ3).

# Objectives

The primary objective is an interactive triage interface that groups and ranks perception alarms by explanation similarity.

Supporting objectives:

- Implement explanation-based grouping with a user-facing similarity threshold.
- Rank groups so that relevant failures surface in the top positions.
- Replay a labelled benchmark to count triage decisions under both queue designs.
- Measure triage accuracy against the benchmark's ground-truth labels.

# Expected Contributions and Results

The scientific contribution is evidence on whether explanation-based grouping reduces triage effort without costing accuracy, which the alarm-handling literature currently lacks.
The practical contribution is the triage interface itself, released against a public benchmark so the comparison can be reproduced.
It is expected that grouping cuts the number of decisions substantially while accuracy stays within a small margin of individual handling.
Limitations are foreseeable: one benchmark, daytime driving only, replay rather than live operation, and simulated rather than observed engineer behaviour.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Literature and benchmark selection | 1-4 |
| Detector and explanation integration | 3-9 |
| Grouping and ranking implementation | 8-14 |
| Interface implementation | 12-17 |
| Replay experiment and analysis | 16-21 |
| Writing and revision | 18-24 |

The replay experiment depends on both the ranking logic and the interface, which makes the interface the last blocking dependency.
Detector integration starts early because the explanation method must be validated before grouping can be built on it.
Three weeks of overlap between analysis and writing absorb a repeat replay.

---
title: Interactive Visual Triage of Perception Alarms in Automated Driving Test Fleets
author: Erika Musterfrau
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Hoffmann23Visual
  type: paper-conference
  author:
  - family: Hoffmann
    given: L.
  issued:
    year: 2023
  title: Visual Analytics for Automated Driving Test Data
  container-title: Proceedings of the Example Conference on Visualization
  DOI: 10.xxxx/xxx40
- id: Iyer25Anomaly
  type: article-journal
  author:
  - family: Iyer
    given: P.
  - family: Novak
    given: D.
  issued:
    year: 2025
  title: Anomaly Attribution for Multivariate Sensor Streams
  container-title: Journal of Data Science Examples
  DOI: 10.xxxx/xxx41
- id: Duarte24Human
  type: paper-conference
  author:
  - family: Duarte
    given: M.
  issued:
    year: 2024
  title: Human-in-the-Loop Labeling of Perception Failures
  container-title: Proceedings of the Example Conference on Human Factors in Computing
  DOI: 10.xxxx/xxx42
- id: Ferreira22Fatigue
  type: article-journal
  author:
  - family: Ferreira
    given: J.
  issued:
    year: 2022
  title: Alarm Fatigue in High False-Positive Monitoring Systems
  container-title: Example Journal of Human Factors and Systems
  DOI: 10.xxxx/xb11
- id: Kaur24Grouping
  type: paper-conference
  author:
  - family: Kaur
    given: S.
  issued:
    year: 2024
  title: Explanation Similarity Beats Signal Similarity for Alarm Grouping
  container-title: Proceedings of the Example Conference on Visualization
  DOI: 10.xxxx/xb12
- id: Delgado23Ranking
  type: article-journal
  author:
  - family: Delgado
    given: R.
  issued:
    year: 2023
  title: Ranking Quality Metrics for Operator Work Queues
  container-title: Journal of Data Science Examples
  DOI: 10.xxxx/xb13
- id: Lindqvist25Benchmark
  type: article-journal
  author:
  - family: Lindqvist
    given: M.
  issued:
    year: 2025
  title: Labelling Conventions in Public Driving Benchmarks
  container-title: Journal of Example Vehicular Intelligence
  DOI: 10.xxxx/xb14
- id: Aranda23Triage
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2023
  title: Triage Workload in Automated Driving Validation
  container-title: Journal of Example Systems Validation
  DOI: 10.xxxx/xb15
- id: Beck24Threshold
  type: paper-conference
  author:
  - family: Beck
    given: A.
  issued:
    year: 2024
  title: User-Facing Thresholds in Clustering Interfaces
  container-title: Proceedings of the Example Symposium on Interaction
  DOI: 10.xxxx/xb16
- id: Novak25Replay
  type: article-journal
  author:
  - family: Novak
    given: T.
  issued:
    year: 2025
  title: Replay Experiments as a Substitute for Operator Studies
  container-title: Example Journal of Research Methods
  DOI: 10.xxxx/xb17
---
