# Introduction to the Topic

Operations teams rely on anomaly detection over system logs to catch failures before users do [@Haas24Logs].
Published detectors report near-perfect scores on static benchmark datasets, yet production log formats change with every deployment.
Whether those scores survive such change is unclear, and a detector that silently degrades is worse than none.
This thesis aims to establish to what degree published log anomaly detectors keep their accuracy when the log data drifts away from their training distribution.

# Contribution to the State-of-the-Art

Work on log anomaly detection falls into two clusters.
Detection models — from classical clustering to sequence models — are trained and scored on fixed benchmark datasets, with evaluation protocols that shuffle events across time [@Haas24Logs; @Lindqvist25Deep].
Drift studies characterize how log formats and event distributions evolve in long-running systems, but stop at describing the drift rather than measuring its effect on detectors [@Okoro26Evolution].
Both clusters share a limitation: no published evaluation holds the detector fixed and moves the data, so reported scores conflate model quality with benchmark staleness.
The thesis fills that gap by re-evaluating published detectors under temporally realistic drift, tied to the research questions below.
Answering them matters because practitioners choose detectors from benchmark leaderboards, and a ranking that inverts under drift misleads exactly the people it is meant to guide.
The deliverable is an evaluation: a drift-aware comparison of published detectors, together with the temporally split benchmark protocol it introduces.

# Research Focus and Research Questions

The focus is the robustness of published log anomaly detectors under distribution drift, measured against the static-benchmark scores that made them known.

1. To what degree do the reported accuracies of published log anomaly detectors degrade when training and test data are split along time instead of shuffled?
2. Under which drift conditions does the accuracy ranking between detector families invert compared to the static benchmark ranking?

# Methodology for Research: Empirical Model Evaluation

An empirical model evaluation fits these questions because both ask how existing models behave under a changed evaluation protocol; nothing new is built, and no human participants are involved — the models and the data are the objects of study.

## Data and Baselines

The evaluation uses two public log datasets with multi-month time spans and documented collection contexts, both released for research use under permissive licenses [@Haas24Logs].
Baselines are the published detectors themselves: one clustering-based, one sequence-model-based, and one retrieval-based detector, each with a public reference implementation.
No new detector is introduced, so the published models serve as both subjects and baselines against their own reported scores.

## Experimental Setup

All detectors are re-run under two protocols: the original shuffled split reproducing the published numbers, and a temporal split where training strictly precedes test data (RQ1).
Leakage is prevented by splitting on timestamps before any preprocessing, so no template mined from test-period logs can inform training.
Drift intensity is varied by widening the gap between training and test windows, using the same hardware and hyperparameters as the reference implementations where published.

## Analysis

Precision, recall, and F1 against labeled anomalies answer whether reported accuracy survives the temporal split, because these are the metrics the original papers report and the comparison must stay commensurable (RQ1).
Rank correlation between detector orderings across drift intensities identifies where the leaderboard inverts (RQ2).
Every configuration runs with five seeds, and variance across seeds is reported alongside the means.
The thesis expects some degradation for all detector families; the size and the ranking effects are open, and small degradation would refute the staleness concern.
Foreseeable limitations are the two datasets and the three detector families, which bound generalization and are stated as such.

# Timeline

The thesis starts in May 2027 and is submitted in October 2027.

---
title: Robustness of Log Anomaly Detectors under Distribution Drift
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Haas24Logs
  type: paper-conference
  author:
  - family: Haas
    given: D.
  issued:
    year: 2024
  title: Benchmarking Log Anomaly Detection at Scale
  container-title: Proceedings of the Example Conference on Software Engineering
  DOI: 10.xxxx/xx24
- id: Lindqvist25Deep
  type: article-journal
  author:
  - family: Lindqvist
    given: A.
  issued:
    year: 2025
  title: Deep Sequence Models for System Log Analysis
  container-title: Journal of Empirical Software Engineering Examples
  DOI: 10.xxxx/xx25
- id: Okoro26Evolution
  type: paper-conference
  author:
  - family: Okoro
    given: C.
  issued:
    year: 2026
  title: How Production Log Formats Evolve
  container-title: Proceedings of the Example Conference on Systems Operations
  DOI: 10.xxxx/xx26
---
