# Energy-Optimal Model Partitioning at the Edge

*Master's Thesis Proposal*

## Introduction to the Topic

Inference workloads increasingly run on devices that cannot hold a full model in memory, so the model is split across a device and a nearby server.
Where that split is placed decides both the latency a user perceives and the energy the device spends.
Practitioners currently choose the split point by hand, guided by intuition rather than by a documented criterion [@Rivera23Survey].
This thesis examines how the choice of split point can be grounded in measurable device and network properties.

## Contribution to the State-of-the-Art

Existing partitioning work optimizes for a single objective, usually end-to-end latency, and assumes a stable network [@Vogel26Partiti].
Energy-aware variants exist but evaluate on simulated links rather than measured ones [@Nakamura25EnergyA].
Neither line reports how the optimal split moves when link quality degrades during inference, which is the common case on mobile networks.
This thesis contributes a measurement-grounded characterization of that movement, so a split decision can be justified against observed conditions rather than assumed ones.

## Research Focus and Research Questions

The focus is the relationship between measurable link and device properties and the split point that minimizes energy at a fixed latency budget.

1. To what degree do measured link-quality fluctuations shift the energy-optimal split point compared to a stable-link assumption?
2. Under which device and model characteristics does a static split remain within a defined margin of the dynamic optimum?
3. How does the latency budget change the sensitivity of the optimal split to link quality?

## Methodology for Research: Prototype Implementation

### Previous Work

The prototype builds on the partitioning runtime described by @Vogel26Partiti and on standard on-device inference tooling.
Link-quality traces are recorded with existing measurement utilities rather than newly implemented ones.

### Requirements

The prototype must partition a given model at an arbitrary layer boundary and execute both halves across a real link.
It must record per-inference energy and latency on the device side.
Automatic re-partitioning at runtime is out of scope: the study measures where the optimum lies, not how to reach it online.

### Evaluation

Replayed link traces at several quality levels locate the energy-optimal split for each trace and quantify how far it moves (RQ1).
A sweep across device classes and model architectures measures how often a single static split stays within the defined margin (RQ2).
Repeating both analyses under three latency budgets shows how the budget changes sensitivity to link quality (RQ3).

## Timeline

| Phase | Month 1 | Month 2 | Month 3 | Month 4 | Month 5 |
|---|---|---|---|---|---|
| Runtime setup | X | X | | | |
| Trace collection | | X | X | | |
| Measurement campaign | | | X | X | |
| Analysis | | | | X | X |
| Write-up | | | | | X |

## References

---
references:
- id: Rivera23Survey
  type: article-journal
  author:
  - family: Rivera
    given: L.
  title: A survey of split inference for constrained devices
  container-title: Example Computing Surveys
  issued:
    year: 2023
  DOI: 10.5555/example.rivera23
- id: Vogel26Partiti
  type: article-journal
  author:
  - family: Vogel
    given: M.
  - family: Haas
    given: T.
  title: Partitioning runtimes for on-device inference
  container-title: Example Transactions on Embedded Systems
  issued:
    year: 2026
  DOI: 10.5555/example.vogel26
- id: Nakamura25EnergyA
  type: paper-conference
  author:
  - family: Nakamura
    given: S.
  title: Energy-aware split points under simulated links
  container-title: Proceedings of the Example Conference on Mobile Systems
  issued:
    year: 2025
  DOI: 10.5555/example.nakamura25
---
