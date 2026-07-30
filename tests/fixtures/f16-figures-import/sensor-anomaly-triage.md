# Introduction to the Topic

Industrial monitoring systems collect high-frequency data from thousands of sensors distributed across production lines [@Hoffmann23Visual].
Automated detectors flag anomalous readings, but operators still decide which alarms deserve intervention.
This triage step is a bottleneck: alarm floods overwhelm operators, and relevant faults drown in false positives [@Iyer25Anomaly].
The thesis addresses this bottleneck with an interactive visual analytics approach for anomaly triage.

# Contribution to the State-of-the-Art

Visual analytics research for time series concentrates on exploration and pattern search rather than on alarm handling [@Hoffmann23Visual].
Explanation methods attach feature attributions to individual anomalies but do not aggregate them into a ranked work queue [@Iyer25Anomaly].
@Duarte24Human show that human labeling of sensor faults improves detector precision, yet their interface presents alarms as an unordered list.
This work combines detector explanations with an interactive ranking view so operators can dismiss whole alarm groups instead of single alarms.
Figure 1 summarizes the proposed pipeline from raw sensor streams to the ranked queue.

![Figure 1: Overview of the proposed triage pipeline from raw sensor streams to the ranked alarm queue](img/sensor-anomaly-triage-a.png)

# Research Focus and Research Questions

The research focus lies on how explanation-based grouping and ranking of alarms changes triage efficiency in industrial monitoring.

1. To what degree does explanation-based grouping reduce the number of triage decisions per shift compared to chronological alarm lists?
2. Under which fault characteristics does the ranking place relevant alarms in the top positions of the queue?
3. How does triage accuracy change when operators act on grouped alarms instead of individual ones?

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype builds on an open-source dashboard framework and a published anomaly-detection library for streaming data.
Detector explanations reuse the attribution method introduced by @Iyer25Anomaly.
A labeled fault dataset from a public industrial benchmark provides ground truth for ranking quality.
Figure 2 sketches how the grouped queue view extends a standard alarm list.

![Figure 2: Interface sketch of the grouped alarm queue with explanation summaries](img/sensor-anomaly-triage-b.png)

## Requirements

The prototype must ingest recorded sensor streams and update the ranked queue within seconds.
It must group alarms by explanation similarity and expose the grouping threshold as a user-facing control.
Visual polish and multi-user support are explicitly neglectable.

## Evaluation

A replay experiment on the benchmark dataset counts triage decisions per simulated shift under grouped and chronological queues (RQ1).
The fraction of injected faults among the top queue positions measures ranking quality across fault types (RQ2).
Comparing triage outcomes against ground-truth labels quantifies accuracy for grouped versus individual handling (RQ3).

---
title: Interactive Visual Triage of Sensor Anomalies in Industrial Monitoring
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
  title: Visual Analytics for Industrial Time Series Monitoring
  container-title: Proceedings of the Example Conference on Visualization
  DOI: 10.1109/VISEX.2023.00184
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
  DOI: 10.1007/s41060-025-00712-3
- id: Duarte24Human
  type: paper-conference
  author:
  - family: Duarte
    given: M.
  issued:
    year: 2024
  title: Human-in-the-Loop Labeling of Industrial Sensor Faults
  container-title: Proceedings of the Example Conference on Human Factors in Computing
  DOI: 10.1145/3613904.3642178
---
