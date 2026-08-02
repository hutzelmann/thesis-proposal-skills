# Introduction and Motivation

Camera-based driver monitoring systems watch the driver continuously and must react before an inattentive moment turns into a hazard.
Automotive suppliers advertise Driver Monitoring System (DMS) pipelines that raise a warning within a few hundred milliseconds of a detected gaze deviation.
In practice, the achieved latency depends heavily on camera frame rate, model input resolution, and the scheduling of the inference runtime [@Nowak23Latency].
Reliable latency figures are hard to obtain before integration, because datasheet values and simulations diverge from real hardware behavior.
This thesis addresses the problem with a measurement testbed for driver-monitoring pipelines on embedded automotive hardware.

# Problem Statement and Research Questions

The thesis investigates how accurately the reaction latency of a driver-monitoring pipeline can be predicted before integration.
Its focus lies on quantifying the gap between model-based estimates and hardware measurements across realistic configurations.

1. To what degree do model-based latency estimates deviate from the measured camera-to-warning latency of driver-monitoring pipelines?
2. To what degree do camera frame rate and model input resolution influence the end-to-end latency of a pipeline?
3. Under which configurations does a pipeline stay below a warning latency of 300 milliseconds at the 95th percentile?

# Related Work

Existing latency studies of driver monitoring either rely on analytical scheduling models [@Nowak23Latency] or measure single inference stages in laboratory settings [@Petrov22Measuring].
Recent profiling frameworks target embedded accelerators in general but do not cover the camera-to-warning path of a monitoring pipeline [@Vogel28Edge].
This thesis contributes a low-cost, reproducible testbed that measures the end-to-end camera-to-warning latency of off-the-shelf driver-monitoring pipelines under controlled configurations.
The testbed enables a direct comparison between model-based estimation and measured hardware behavior.
Benchmarking practice for embedded inference has converged on standard reporting of percentile latency rather than means [@Ferreira23Percentile].
@Kaur24Pipelines show that stage-level measurements underestimate end-to-end delay whenever the stages contend for one accelerator.
Timestamping methodology for camera-to-actuation paths is documented for automotive networks [@Lindqvist22Timestamp], and the safety relevance of the resulting bound is argued from driver reaction data [@Osei24Reaction].
Comparable driver-monitoring products report latency without stating measurement conditions, which motivates a reproducible testbed [@Beck25Products].
Sustained inference also warms the accelerator enough to change its clock behaviour, so measurement runs need a documented thermal state [@Nowak24Thermal].
Reporting practice for hardware measurement studies gives the reproducibility checklist this testbed follows [@Sato25Reproduce].

# Methodology: Prototype Implementation

## Use Case Definition

The object of study is an off-the-shelf driver-monitoring pipeline running on a commodity embedded automotive board, exercised with recorded in-cabin video rather than a live driver.
Recorded input suits the research questions because latency must be measured against an identical stimulus across configurations, which a live driver cannot provide.
The board is available in the laboratory, and its accelerator is the mid-range part typical of current series projects, which bounds the results to that performance class.

## Previous Work

The testbed builds on an open-source gaze-estimation stack and a commodity embedded board for inference.
A hardware timestamping unit with an established driver library captures frame arrival and warning output at microsecond resolution [@Petrov22Measuring].
Latency estimation reuses a published analytical model of staged inference pipelines [@Nowak23Latency].

## Requirements

The testbed must record end-to-end latency for configurable frame rates, input resolutions, and accelerator settings.
It must support at least two different off-the-shelf camera modules to avoid vendor-specific artifacts.
Automation of complete measurement runs is required so that configurations can be repeated without manual intervention.
Portability of the testbed hardware is neglectable; the setup may assume a fixed laboratory bench.
Sub-microsecond timing precision is likewise not required, since warning latencies aggregate over longer windows.

## Evaluation

The estimation error is determined by comparing model-based predictions against the measured end-to-end latency across all configurations (RQ1).
Frame rate and input resolution are varied systematically, and their influence on latency is quantified through regression over the measurement data (RQ2).
Percentile latencies are extracted from the measured distributions and checked against the 300-millisecond target (RQ3).
Four measurement campaigns are planned, one for each combination of camera module and accelerator setting, before the results are aggregated.
Measurement uncertainty is estimated by repeating a reference configuration at the start of every campaign.

# Objectives

The primary objective is to build a reproducible testbed that measures end-to-end camera-to-warning latency of driver-monitoring pipelines.

Supporting objectives:

- Implement hardware timestamping of frame arrival and warning output.
- Automate measurement runs across frame rate, resolution, and accelerator settings.
- Compare measured latency against a model-based estimate.
- Publish the testbed design so that other groups can reproduce the measurements.

# Expected Contributions and Results

The scientific contribution is quantified evidence on how far model-based latency estimates diverge from measured behaviour in a staged perception pipeline.
The practical contribution is the testbed itself, released with its timestamping design and automation scripts.
It is expected that estimates are optimistic at high resolutions, where accelerator contention dominates, and that the 300-millisecond target holds only in the lower half of the configuration space.
Limitations are foreseeable: one board class, two camera modules, recorded rather than live input, and no claim about pipelines that fuse additional sensors.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Literature and instrumentation study | 1-3 |
| Testbed hardware assembly | 3-6 |
| Timestamping and automation software | 5-10 |
| Measurement campaigns | 10-16 |
| Analysis and model comparison | 15-19 |
| Writing and revision | 17-22 |

The campaigns cannot start before timestamping is validated against a known reference delay, which is the critical dependency.
Hardware assembly runs in parallel with the instrumentation study because the parts have a long delivery time.
Two weeks of slack before writing absorb a repeat campaign should the reference measurement drift.

---
title: A Latency Measurement Testbed for Camera-Based Driver Monitoring
author: Erika Musterfrau
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Nowak23Latency
  type: article-journal
  author:
  - family: Nowak
    given: P.
  issued:
    year: 2023
  title: Latency Models for Staged Perception Pipelines
  container-title: Journal of Example Embedded Systems
  DOI: 10.xxxx/xxxx7
- id: Petrov22Measuring
  type: paper-conference
  author:
  - family: Petrov
    given: D.
  issued:
    year: 2022
  title: Measuring End-to-End Delay of Constrained Vision Devices
  container-title: Proceedings of the Example Conference on Embedded Sensing
  DOI: 10.xxxx/xxxx8
- id: Vogel28Edge
  type: article-journal
  author:
  - family: Vogel
    given: M.
  issued:
    year: 2028
  title: Edge Inference Profiling for Constrained Automotive Devices
  container-title: Journal of Example Pervasive Computing
  DOI: 10.xxxx/xxxx9
- id: Ferreira23Percentile
  type: article-journal
  author:
  - family: Ferreira
    given: J.
  issued:
    year: 2023
  title: Percentile Latency Reporting for Embedded Inference
  container-title: Journal of Example Embedded Systems
  DOI: 10.xxxx/xx41
- id: Kaur24Pipelines
  type: paper-conference
  author:
  - family: Kaur
    given: S.
  issued:
    year: 2024
  title: Accelerator Contention in Staged Perception Pipelines
  container-title: Proceedings of the Example Conference on Embedded Sensing
  DOI: 10.xxxx/xx42
- id: Lindqvist22Timestamp
  type: article-journal
  author:
  - family: Lindqvist
    given: M.
  issued:
    year: 2022
  title: Timestamping Camera-to-Actuation Paths in Automotive Networks
  container-title: Example Journal of Vehicular Communication
  DOI: 10.xxxx/xx43
- id: Osei24Reaction
  type: article-journal
  author:
  - family: Osei
    given: K.
  issued:
    year: 2024
  title: Driver Reaction Time Bounds for Distraction Warnings
  container-title: Journal of Example Traffic Safety Research
  DOI: 10.xxxx/xx44
- id: Beck25Products
  type: article-journal
  author:
  - family: Beck
    given: A.
  issued:
    year: 2025
  title: Reported Performance of Commercial Driver Monitoring Systems
  container-title: Journal of Example Vehicle Engineering
  DOI: 10.xxxx/xx45
- id: Sato25Reproduce
  type: article-journal
  author:
  - family: Sato
    given: H.
  issued:
    year: 2025
  title: Reproducibility Guidelines for Hardware Measurement Studies
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xx46
- id: Nowak24Thermal
  type: paper-conference
  author:
  - family: Nowak
    given: P.
  issued:
    year: 2024
  title: Thermal Throttling Effects on Embedded Vision Latency
  container-title: Proceedings of the Example Conference on Edge Computing
  DOI: 10.xxxx/xx47
---
