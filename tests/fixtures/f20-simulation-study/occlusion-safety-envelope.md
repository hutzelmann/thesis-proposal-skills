# Introduction to the Topic

Automated driving functions must keep a safe distance to road users they cannot yet see.
Formal safety envelopes such as Responsibility-Sensitive Safety (RSS) derive that distance from worst-case assumptions about the behaviour of other traffic participants [@Halbach22Envelope].
Urban intersections violate the premise of these envelopes, because parked vehicles and buildings hide road users until they are close [@Ibarra24Occlusion].
Field testing cannot expose a function to enough occluded encounters to establish how often the envelope actually holds.
This thesis evaluates an occlusion-aware safety envelope across a systematically sampled scenario space in simulation.

# Contribution to the State-of-the-Art

Published evaluations of safety envelopes report violation rates over recorded drives, which cover only the situations the test fleet happened to encounter [@Halbach22Envelope].
Occlusion-aware extensions of the envelope exist, yet their evaluation is limited to a handful of hand-authored intersection layouts [@Ibarra24Occlusion].
@Sorensen25Coverage argue that scenario coverage, not scenario count, determines what a simulation campaign can support, but they do not apply the argument to safety envelopes.
This thesis contributes a coverage-driven simulation campaign that sweeps occlusion geometry, approach speed, and emergence timing, and reports envelope violation as a function of those parameters.
The result shows where the occlusion-aware envelope remains conservative and where it degrades to the unoccluded case.

# Research Focus and Research Questions

The research focus lies on how the guarantees of an occlusion-aware safety envelope depend on the geometry and dynamics of the occluded encounter.

1. To what degree does the occlusion-aware envelope reduce collision occurrence compared to the unoccluded envelope across the sampled scenario space?
2. Under which combinations of occlusion geometry and approach speed does the envelope fail to prevent a collision?
3. To what degree does the sampled scenario space cover the occlusion configurations documented in public urban intersection data?

# Methodology for Research: Simulation Study

## Scenario Design

The scenario space is spanned by four parameters: the lateral offset of the occluding object, the ego approach speed, the emergence speed of the hidden road user, and the time of emergence relative to the ego arrival.
Parameter ranges follow the distributions reported for urban intersections in public traffic observation data [@Ibarra24Occlusion].
Sampling combines a full factorial grid over the two geometric parameters with Latin hypercube sampling over the two dynamic parameters, which keeps the campaign tractable while avoiding a purely regular design.
Coverage of the sampled set against the documented configurations is quantified with a discrepancy measure (RQ3).

## Execution

Scenarios execute in an open-source driving simulator coupled to a reference planning stack through its standard interface.
Each sampled configuration runs twice, once with the occlusion-aware envelope active and once with the unoccluded envelope, so that the pair differs only in the envelope under test.
The simulation records ego and object trajectories, envelope activations, and collision events at a fixed time step.
Sensor noise and actuation delay are modelled as fixed nominal values rather than sampled, which bounds the campaign to the behaviour of the planning logic and is a deliberate limitation of the transfer to real vehicles.

## Analysis

Collision occurrence is compared between the paired runs across the whole sampled space (RQ1).
A regression of collision occurrence on the four scenario parameters, followed by an inspection of the parameter regions with the highest predicted risk, isolates the failing combinations (RQ2).
Because the evidence comes from a model of the intersection rather than from the intersection itself, all reported rates are interpreted as properties of the modelled scenario space, and the sensitivity of the conclusions to the fixed noise assumptions is reported alongside them.

---
title: Scenario-Based Evaluation of an Occlusion-Aware Safety Envelope
author: Jane Doe
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Halbach22Envelope
  type: article-journal
  author:
  - family: Halbach
    given: T.
  issued:
    year: 2022
  title: Envelope-Based Safety Guarantees for Automated Driving Functions
  container-title: Journal of Example Vehicle Safety
  DOI: 10.xxxx/xxx60
- id: Ibarra24Occlusion
  type: paper-conference
  author:
  - family: Ibarra
    given: L.
  issued:
    year: 2024
  title: Occlusion-Aware Motion Planning at Urban Intersections
  container-title: Proceedings of the Example Conference on Intelligent Vehicles
  DOI: 10.xxxx/xxx61
- id: Sorensen25Coverage
  type: article-journal
  author:
  - family: Sorensen
    given: M.
  issued:
    year: 2025
  title: Coverage Arguments for Scenario-Based Validation Campaigns
  container-title: Journal of Example Systems Validation
  DOI: 10.xxxx/xxx62
---
