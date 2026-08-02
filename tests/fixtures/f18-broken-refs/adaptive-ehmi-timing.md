# Introduction and Motivation

Automated vehicles signal their yielding intention through external displays whose timing is set by hand [@Dey19Gaze].
Fixed signalling schedules ignore how differently pedestrians approach a crossing.
Adaptive timing promises clearer communication without manual tuning [@Ghost21Vanished].

# Problem Statement and Research Questions

The thesis investigates to what degree approach-aware signal timing improves crossing communication in shared spaces.

1. To what extent does adaptive signal timing improve crossing initiation compared to fixed schedules across approach speeds?

# Related Work

Prior work characterizes crossing behaviour through simulator studies [@Lin23Pedestrian].
This thesis extends adaptive timing to mixed pedestrian and cyclist encounters under recorded approach traces [@Unknown22Mystery].
Fixed signalling schedules dominate deployed external interfaces, and their timing is rarely justified from approach behaviour [@Ghost21Vanished].

# Methodology: Prototype Implementation

## Use Case Definition

The object of study is an unsignalised shared-space crossing, replayed in a pedestrian simulator from recorded approach traces of pedestrians and cyclists.
This use case suits the research question because signal timing only matters where the crossing decision is negotiated rather than regulated.
Recorded traces are reused under their original research licence; night-time and adverse-weather approaches are absent from them.

## Previous Work

The prototype builds on an open-source pedestrian simulator and replays recorded approach traces [@Lin23Pedestrian].

## Requirements

The prototype must adapt display timing at runtime from observed approach metrics (RQ1).
Production-grade fault tolerance is not required.

## Evaluation

Replayed traces measure crossing-initiation deltas between adaptive and fixed schedules (RQ1).

# Objectives

The primary objective is an adaptive signal-timing policy that adjusts display onset to the observed approach of a crossing road user.

Supporting objectives:

- Extract approach speed and trajectory features from recorded traces.
- Implement a timing policy that reacts to those features at runtime.
- Compare crossing initiation against a fixed-schedule baseline.

# Expected Contributions and Results

The scientific contribution is evidence on whether approach-aware timing improves crossing communication over the fixed schedules currently deployed.
The practical contribution is the timing policy and its feature extraction, released against the recorded trace set.
It is expected that adaptive timing helps most at low approach speeds, where fixed schedules signal too early to be associated with the crossing.
Limitations are foreseeable: recorded rather than live approaches, one crossing geometry, and no night-time or adverse-weather coverage.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Trace preparation and feature extraction | 1-5 |
| Timing policy implementation | 4-10 |
| Baseline replication | 8-12 |
| Replay comparison and analysis | 11-16 |
| Writing and revision | 14-20 |

The comparison depends on both the policy and the replicated baseline, which makes baseline replication the last blocking task.
Feature extraction runs first because the policy consumes its output directly.

---
title: Adaptive External Display Timing for Pedestrian Crossings
author: Erika Musterfrau
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Dey19Gaze
  type: paper-conference
  author:
  - family: Dey
    given: D.
  issued:
    year: 2019
  title: Gaze Patterns in Pedestrian Interaction with Vehicles
  DOI: 10.1145/3342197.3344523
- id: Lin23Pedestrian
  type: paper-conference
  author:
  - family: Lin
    given: Y.
  issued:
    year: 2023
  title: Pedestrian Crossing Decision-Making Model at Uncontrolled Mid-Block Locations Based on Pedestrian Simulator
- id: Ghost21Vanished
  type: article-journal
  author:
  - family: Ghost
    given: G.
  issued:
    year: 2021
  title: A Paper That Does Not Resolve
  DOI: 10.9999/does.not.exist
- id: Unknown22Mystery
  type: article-journal
  author:
  - family: Unknown
    given: U.
  issued:
    year: 2022
  title: Entirely Unidentifiable Invented Work of No Venue
---
