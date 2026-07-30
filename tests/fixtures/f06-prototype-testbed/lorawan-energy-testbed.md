# Introduction to the Topic

Battery-powered sensor nodes form the backbone of environmental monitoring deployments.
Low-power wide-area networks such as Long Range Wide Area Network (LoRaWAN) promise node lifetimes of several years on a single battery charge.
In practice, the achieved lifetime depends heavily on radio configuration, payload size, and duty cycle [@Nowak23Energy].
Reliable energy figures are hard to obtain before deployment, because datasheet values and simulations diverge from real hardware behavior.
This thesis addresses the problem with a measurement testbed for LoRaWAN sensor nodes.

# Contribution to the State-of-the-Art

Existing energy studies of LoRaWAN either rely on analytical models [@Nowak23Energy] or measure single nodes in laboratory settings [@Petrov22Measuring].
Recent profiling frameworks target edge devices in general but do not cover the LoRaWAN media access behavior [@Vogel28Edge].
This thesis contributes a low-cost, reproducible testbed that measures the per-message energy consumption of off-the-shelf LoRaWAN nodes under controlled configurations.
The testbed enables a direct comparison between software-based estimation and measured hardware behavior.

# Research Focus and Research Questions

The thesis investigates how accurately the energy consumption of LoRaWAN sensor nodes can be predicted before deployment.
Its focus lies on quantifying the gap between model-based estimates and hardware measurements across realistic configurations.

1. To what degree do software-based energy estimates deviate from the measured energy consumption of LoRaWAN sensor nodes?
2. To what degree do spreading factor and payload size influence the per-message energy cost of a node?
3. Under which duty-cycle configurations does a node reach a battery lifetime of at least two years?

# Methodology for Research: Prototype Implementation

## Previous Work

The testbed builds on an open-source LoRaWAN protocol stack and a commodity network server for packet handling.
A shunt-based power monitor with an established driver library captures current draw at millisecond resolution [@Petrov22Measuring].
Energy estimation reuses a published analytical model of the LoRaWAN media access procedure [@Nowak23Energy].

## Requirements

The testbed must record per-message energy consumption for configurable spreading factors, payload sizes, and duty cycles.
It must support at least two different off-the-shelf node types to avoid vendor-specific artifacts.
Automation of complete measurement runs is required so that configurations can be repeated without manual intervention.
Portability of the testbed hardware is neglectable; the setup may assume a fixed laboratory bench.
Sub-millisecond timing precision is likewise not required, since per-message energies aggregate over longer windows.

## Evaluation

The estimation error is determined by comparing model-based predictions against the measured per-message energy across all configurations (RQ1).
Spreading factor and payload size are varied systematically, and their influence on energy cost is quantified through regression over the measurement data (RQ2).
Battery lifetimes are extrapolated from measured duty-cycle profiles and checked against the two-year target (RQ3).
Four measurement campaigns are planned, one for each combination of node type and antenna placement, before the results are aggregated.
Measurement uncertainty is estimated by repeating a reference configuration at the start of every campaign.

---
title: An Energy Measurement Testbed for LoRaWAN Sensor Nodes
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Nowak23Energy
  type: article-journal
  author:
  - family: Nowak
    given: P.
  issued:
    year: 2023
  title: Energy Models for LoRaWAN Class A Devices
  container-title: Journal of Example Networked Systems
  DOI: 10.xxxx/xxxx7
- id: Petrov22Measuring
  type: paper-conference
  author:
  - family: Petrov
    given: D.
  issued:
    year: 2022
  title: Measuring Power Draw of Constrained Wireless Nodes
  container-title: Proceedings of the Example Conference on Embedded Networked Sensing
  DOI: 10.xxxx/xxxx8
- id: Vogel28Edge
  type: article-journal
  author:
  - family: Vogel
    given: M.
  issued:
    year: 2028
  title: Edge Energy Profiling for Constrained IoT Devices
  container-title: Journal of Example Pervasive Computing
  DOI: 10.xxxx/xxxx9
---
