# Introduction to the Topic

Automated driving test fleets collect high-frequency data from dozens of sensors distributed across every vehicle [@Hoffmann23Visual].
Automated detectors flag perception failures such as dropped tracks and implausible object states, but engineers still decide which alarms deserve investigation.
This triage step is a bottleneck: alarm floods overwhelm engineers, and relevant failures drown in false positives [@Iyer25Anomaly].
The thesis addresses this bottleneck with an interactive visual analytics approach for perception-alarm triage.

# Contribution to the State-of-the-Art

Visual analytics research for driving data concentrates on scenario exploration and pattern search rather than on alarm handling [@Hoffmann23Visual].
Explanation methods attach feature attributions to individual perception failures but do not aggregate them into a ranked work queue [@Iyer25Anomaly].
@Duarte24Human show that engineer labeling of perception failures improves detector precision, yet their interface presents alarms as an unordered list.
This work combines detector explanations with an interactive ranking view so engineers can dismiss whole alarm groups instead of single alarms.
Figure 1 summarizes the proposed pipeline from raw sensor recordings to the ranked queue.

![Figure 1: Overview of the proposed triage pipeline from raw sensor recordings to the ranked alarm queue](img/perception-alarm-triage-a.png)

# Research Focus and Research Questions

The research focus lies on how explanation-based grouping and ranking of alarms changes triage efficiency in automated driving validation.

1. To what degree does explanation-based grouping reduce the number of triage decisions per test campaign compared to chronological alarm lists?
2. Under which failure characteristics does the ranking place relevant alarms in the top positions of the queue?
3. How does triage accuracy change when engineers act on grouped alarms instead of individual ones?

# Methodology for Research: Prototype Implementation

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
---
