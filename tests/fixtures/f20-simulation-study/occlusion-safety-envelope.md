# Introduction and Motivation

Automated driving functions must keep a safe distance to road users they cannot yet see.
Formal safety envelopes such as Responsibility-Sensitive Safety (RSS) derive that distance from worst-case assumptions about the behaviour of other traffic participants [@Halbach22Envelope].
Urban intersections violate the premise of these envelopes, because parked vehicles and buildings hide road users until they are close [@Ibarra24Occlusion].
Field testing cannot expose a function to enough occluded encounters to establish how often the envelope actually holds.
This thesis evaluates an occlusion-aware safety envelope across a systematically sampled scenario space in simulation.

# Problem Statement and Research Questions

The research focus lies on how the guarantees of an occlusion-aware safety envelope depend on the geometry and dynamics of the occluded encounter.

1. To what degree does the occlusion-aware envelope reduce collision occurrence compared to the unoccluded envelope across the sampled scenario space?
2. Under which combinations of occlusion geometry and approach speed does the envelope fail to prevent a collision?
3. To what degree does the sampled scenario space cover the occlusion configurations documented in public urban intersection data?

# Related Work

Published evaluations of safety envelopes report violation rates over recorded drives, which cover only the situations the test fleet happened to encounter [@Halbach22Envelope].
Occlusion-aware extensions of the envelope exist, yet their evaluation is limited to a handful of hand-authored intersection layouts [@Ibarra24Occlusion].
@Sorensen25Coverage argue that scenario coverage, not scenario count, determines what a simulation campaign can support, but they do not apply the argument to safety envelopes.
This thesis contributes a coverage-driven simulation campaign that sweeps occlusion geometry, approach speed, and emergence timing, and reports envelope violation as a function of those parameters.
The result shows where the occlusion-aware envelope remains conservative and where it degrades to the unoccluded case.
Sampling strategies for scenario spaces trade regularity against coverage, and discrepancy measures make that trade explicit [@Ferreira24Sampling].
@Kaur23Fidelity show that planner behaviour in simulation diverges from vehicle behaviour mainly through actuation delay, which is why that parameter is held fixed here.
Reference planning stacks differ enough that envelope results do not transfer between them without restatement [@Delgado22Planners], and the sim-to-real gap for safety claims has been characterised for perception but not for planning [@Lindqvist25SimReal].
Urban intersection observation data provides the occlusion configurations against which coverage is judged [@Aranda23Intersections].
Paired-run designs isolate the component under test from run-to-run variation and are the standard construction for simulation campaigns [@Beck25Paired].
Encounters where the hidden road user emerges inside the braking distance are known to defeat envelope guarantees regardless of occlusion handling [@Novak24Braking].

# Methodology: Simulation Study

## Use Case Definition

The object of study is a four-way urban intersection with parked vehicles along the approach, modelled in an open-source driving simulator and driven by a reference planning stack.
This use case suits the research questions because it produces occluded encounters on demand, which a test fleet encounters too rarely to support a coverage argument.
The intersection geometry follows a published urban observation dataset; multi-lane arterials and signalised intersections stay out of scope.

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

# Objectives

The primary objective is a coverage-driven simulation campaign that quantifies where an occlusion-aware safety envelope prevents collisions and where it fails.

Supporting objectives:

- Define a four-parameter scenario space over occlusion geometry and encounter dynamics.
- Sample that space with a design whose coverage can be stated rather than assumed.
- Execute paired runs isolating the envelope under test.
- Quantify coverage of the sampled set against documented intersection configurations.

# Expected Contributions and Results

The scientific contribution is a parameter-resolved account of when an occlusion-aware envelope holds, replacing the aggregate violation rates that recorded-drive evaluations report.
The practical contribution is the reusable scenario-space definition and sampling design, released with the campaign configuration.
It is expected that the occlusion-aware envelope reduces collisions across most of the space and degrades toward the unoccluded case where emergence occurs inside the braking distance.
Limitations are foreseeable: fixed sensor-noise and actuation-delay assumptions, one planning stack, one intersection topology, and evidence that concerns the model rather than the road.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Literature and envelope formulation | 1-4 |
| Simulator and planner integration | 3-8 |
| Scenario space and sampling design | 6-10 |
| Campaign execution | 10-15 |
| Coverage and failure-region analysis | 14-19 |
| Writing and revision | 17-24 |

Campaign execution cannot begin before planner integration is stable, which makes integration the critical dependency.
The sampling design is finalised before execution because re-sampling invalidates the paired-run structure.
Five weeks of overlap between analysis and writing absorb a partial re-run should the integration change.

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
- id: Ferreira24Sampling
  type: article-journal
  author:
  - family: Ferreira
    given: J.
  issued:
    year: 2024
  title: Discrepancy Measures for Scenario Space Sampling
  container-title: Journal of Example Systems Validation
  DOI: 10.xxxx/xx81
- id: Kaur23Fidelity
  type: paper-conference
  author:
  - family: Kaur
    given: S.
  issued:
    year: 2023
  title: Actuation Delay Dominates the Simulation Fidelity Gap
  container-title: Proceedings of the Example Conference on Intelligent Vehicles
  DOI: 10.xxxx/xx82
- id: Delgado22Planners
  type: article-journal
  author:
  - family: Delgado
    given: R.
  issued:
    year: 2022
  title: Comparability of Reference Planning Stacks
  container-title: Example Journal of Robotics Software
  DOI: 10.xxxx/xx83
- id: Lindqvist25SimReal
  type: article-journal
  author:
  - family: Lindqvist
    given: M.
  issued:
    year: 2025
  title: Characterising the Sim-to-Real Gap for Safety Claims
  container-title: Journal of Example Vehicle Safety
  DOI: 10.xxxx/xx84
- id: Aranda23Intersections
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2023
  title: Observed Occlusion Configurations at Urban Intersections
  container-title: Journal of Example Traffic Safety Research
  DOI: 10.xxxx/xx85
- id: Beck25Paired
  type: article-journal
  author:
  - family: Beck
    given: A.
  issued:
    year: 2025
  title: Paired Run Designs for Simulation Campaigns
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xx86
- id: Novak24Braking
  type: paper-conference
  author:
  - family: Novak
    given: T.
  issued:
    year: 2024
  title: Emergence Timing Inside the Braking Distance
  container-title: Proceedings of the Example Symposium on Vehicle Dynamics
  DOI: 10.xxxx/xx87
---
