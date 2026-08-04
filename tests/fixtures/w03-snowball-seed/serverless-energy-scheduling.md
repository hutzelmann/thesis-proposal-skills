# Introduction to the Topic

Serverless platforms execute application logic as short-lived functions and bill per invocation [@Farahani23Energy].
Providers keep large pools of pre-warmed workers idle so that cold starts stay rare, which wastes energy at scale.
Data centers already consume a notable share of global electricity, so idle capacity is both an environmental and an economic concern [@Okafor24Carbon].
This thesis investigates how placement decisions on serverless platforms can reduce energy consumption without violating latency expectations.

# Contribution to the State-of-the-Art

Current serverless schedulers optimize latency and utilization and treat energy as a byproduct [@Farahani23Energy].
Carbon-aware load shifting moves batch jobs across time and regions but ignores the millisecond scale of function invocations [@Okafor24Carbon].
@Weiss25Proportional propose energy-proportional container pools, yet evaluate them only under synthetic uniform load.
This work contributes a scheduler that co-locates invocations based on measured per-function power profiles.
It extends pool-based approaches with an admission policy that trades cold-start probability against idle energy.

# Research Focus and Research Questions

The research focus lies on the trade-off between idle energy, cold-start latency, and scheduling overhead in serverless worker pools.

1. To what degree does power-profile-based co-location reduce the idle energy of a serverless worker pool compared to utilization-based placement?
2. Under which load patterns does energy-aware admission push the cold-start rate beyond common latency budgets?
3. How does the placement overhead of the proposed scheduler scale with the number of concurrently registered functions?

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype extends an open-source serverless runtime through its pluggable scheduler interface.
Energy readings come from the hosts' exposed power counters, following the profiling approach of @Farahani23Energy.
Load generation replays publicly available invocation traces with an established workload replay tool.

## Requirements

The scheduler must reach each placement decision within a budget of a few milliseconds.
It must encapsulate the energy model as an exchangeable module so alternative power profiles can be compared.
Multi-tenant isolation and billing integration are explicitly neglectable for the prototype.

## Evaluation

A trace-driven experiment compares idle energy under co-location against a utilization-based baseline (RQ1).
Synthetic bursty and diurnal load patterns expose how energy-aware admission affects the cold-start rate (RQ2).
A scalability benchmark with a growing number of registered functions measures placement overhead (RQ3).

# Timeline

The thesis starts in October 2027 and is submitted in March 2028.

---
title: Energy-Aware Scheduling for Serverless Functions
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Farahani23Energy
  type: paper-conference
  author:
  - family: Farahani
    given: S.
  - family: Bergstrom
    given: T.
  issued:
    year: 2023
  title: Energy Profiling of Serverless Function Runtimes
  container-title: Proceedings of the ACM Symposium on Cloud Computing
  DOI: 10.1145/3620678.3624645
- id: Okafor24Carbon
  type: article-journal
  author:
  - family: Okafor
    given: C.
  - family: Lindqvist
    given: M.
  issued:
    year: 2024
  title: Carbon-Aware Load Shifting for Batch Workloads in Geo-Distributed Data Centers
  container-title: IEEE Transactions on Sustainable Computing
  DOI: 10.1109/TSUSC.2024.3371245
- id: Weiss25Proportional
  type: article-journal
  author:
  - family: Weiss
    given: A.
  - family: Lindgren
    given: P.
  issued:
    year: 2025
  title: Proportional Energy Management for Container Pools
  container-title: Journal of Cluster Computing
  DOI: 10.1007/s10586-025-04412-8
---
