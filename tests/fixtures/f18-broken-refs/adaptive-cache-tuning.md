# Introduction to the Topic

Modern services depend on cache layers whose parameters are tuned by hand [@Bacchelli13Expect].
Static cache configurations waste memory under shifting workloads.
Adaptive tuning promises better hit rates without manual intervention [@Ghost21Vanished].

# Contribution to the State-of-the-Art

Prior work characterizes system behavior through microbenchmarking [@Wong10Demystifying].
This thesis extends adaptive tuning to multi-tier cache hierarchies under real workload traces [@Unknown22Mystery].

# Research Focus and Research Questions

The thesis investigates to what degree workload-aware parameter adaptation improves multi-tier cache performance.

1. To what extent does adaptive parameter tuning improve hit rates compared to static configurations across workload shifts?

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype builds on an open-source caching proxy and replays public workload traces [@Wong10Demystifying].

## Requirements

The prototype must adapt cache parameters at runtime from observed metrics (RQ1).
Production-grade fault tolerance is not required.

## Evaluation

Replayed traces measure hit-rate deltas between adaptive and static configurations (RQ1).

---
title: Adaptive Cache Tuning for Multi-Tier Services
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Bacchelli13Expect
  type: paper-conference
  author:
  - family: Bacchelli
    given: A.
  issued:
    year: 2013
  title: Expectations, outcomes, and challenges of modern code review
  DOI: 10.1109/icse.2013.6606617
- id: Wong10Demystifying
  type: paper-conference
  author:
  - family: Wong
    given: H.
  issued:
    year: 2010
  title: Demystifying GPU microarchitecture through microbenchmarking
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
