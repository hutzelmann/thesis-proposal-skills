# Introduction to the Topic

Automated vehicles signal their yielding intention through external displays whose timing is set by hand [@Dey19Gaze].
Fixed signalling schedules ignore how differently pedestrians approach a crossing.
Adaptive timing promises clearer communication without manual tuning [@Ghost21Vanished].

# Contribution to the State-of-the-Art

Prior work characterizes crossing behaviour through simulator studies [@Lin23Pedestrian].
This thesis extends adaptive timing to mixed pedestrian and cyclist encounters under recorded approach traces [@Unknown22Mystery].

# Research Focus and Research Questions

The thesis investigates to what degree approach-aware signal timing improves crossing communication in shared spaces.

1. To what extent does adaptive signal timing improve crossing initiation compared to fixed schedules across approach speeds?

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype builds on an open-source pedestrian simulator and replays recorded approach traces [@Lin23Pedestrian].

## Requirements

The prototype must adapt display timing at runtime from observed approach metrics (RQ1).
Production-grade fault tolerance is not required.

## Evaluation

Replayed traces measure crossing-initiation deltas between adaptive and fixed schedules (RQ1).

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
