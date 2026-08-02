# Introduction to the Topic

Camera-based driver monitoring systems watch the driver continuously and must react before an inattentive moment turns into a hazard.
Automotive suppliers advertise Driver Monitoring System (DMS) pipelines that raise a warning within a few hundred milliseconds of a detected gaze deviation.
In practice, the achieved latency depends heavily on camera frame rate, model input resolution, and the scheduling of the inference runtime [@Nowak23Latency].
Reliable latency figures are hard to obtain before integration, because datasheet values and simulations diverge from real hardware behavior.
This thesis addresses the problem with a measurement testbed for driver-monitoring pipelines on embedded automotive hardware.

# Contribution to the State-of-the-Art

Existing latency studies of driver monitoring either rely on analytical scheduling models [@Nowak23Latency] or measure single inference stages in laboratory settings [@Petrov22Measuring].
Recent profiling frameworks target embedded accelerators in general but do not cover the camera-to-warning path of a monitoring pipeline [@Vogel28Edge].
This thesis contributes a low-cost, reproducible testbed that measures the end-to-end camera-to-warning latency of off-the-shelf driver-monitoring pipelines under controlled configurations.
The testbed enables a direct comparison between model-based estimation and measured hardware behavior.

# Research Focus and Research Questions

The thesis investigates how accurately the reaction latency of a driver-monitoring pipeline can be predicted before integration.
Its focus lies on quantifying the gap between model-based estimates and hardware measurements across realistic configurations.

1. To what degree do model-based latency estimates deviate from the measured camera-to-warning latency of driver-monitoring pipelines?
2. To what degree do camera frame rate and model input resolution influence the end-to-end latency of a pipeline?
3. Under which configurations does a pipeline stay below a warning latency of 300 milliseconds at the 95th percentile?

# Methodology for Research: Prototype Implementation

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
---
