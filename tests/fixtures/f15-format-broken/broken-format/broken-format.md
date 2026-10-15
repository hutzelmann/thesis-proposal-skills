# Automated Index Selection

*Bachelor's Thesis Proposal*

## Introduction to the Topic

Databases power modern applications [@on].
This proposal studies index selection [@Ghost99Missing].
[TODO: sharpen motivation]

## Contribution to the State-of-the-Art

Prior work tunes indexes manually [@Lee24Index].

## Research Focus and Research Questions

The thesis examines automated index selection.

1. To what degree can workload-driven heuristics match expert index choices?

## Methodology for Research: Prototype Implementation

### Previous Work

The prototype builds on an open-source query planner [@Lee24Index].

### Requirements

The prototype must propose index sets for a given workload trace (RQ1).
[TODO: name the workload dataset]

### Evaluation

Accuracy against expert-chosen indexes is measured on public workloads (RQ1).

## References
---
author: Erika Musterfrau
references:
- id: on
  type: article-journal
  author:
  - family: Grid
    given: P.
  issued:
    year: 2022
  title: Online Index Advisors
  DOI: 10.xxxx/yyy1
- id: Lee24Index
  type: paper-conference
  author:
  - family: Lee
    given: S.
  issued:
    year: 2024
  title: Index Tuning Revisited
  DOI: 10.xxxx/yyy2
- id: Lee24Index
  type: paper-conference
  author:
  - family: Lee
    given: S.
  issued:
    year: 2024
  title: Index Tuning Revisited (duplicate)
  DOI: 10.xxxx/yyy2
---
