# Introduction to the Topic

Automated driving functions are released only after they have been exercised against large catalogues of traffic scenarios [@Miller23Scenario].
Assembling those catalogues by hand is time-consuming and biased toward the situations engineers already anticipate.
Large language models offer potential to synthesize scenario descriptions from natural-language accident reports and thereby widen the covered space [@Chen25Learning].

# Contribution to the State-of-the-Art

Existing scenario-generation tools sample parameters within manually authored scenario templates [@Miller23Scenario].
This work extends generation to the structure of the scenario itself, deriving actor constellations and manoeuvre sequences from textual crash narratives.
The proposed approach combines a language model with a rule-based consistency filter that rejects physically implausible constellations before simulation.

# Research Focus and Research Questions

This thesis investigates how reliably a language-model pipeline can turn unstructured crash narratives into executable simulation scenarios.
The focus is on balancing the diversity of generated scenarios against their physical plausibility, so that the output is usable in an existing validation toolchain.

1. To what degree do language-model-generated scenarios cover manoeuvre constellations that are absent from a manually authored baseline catalogue?
2. Which properties of a crash narrative most strongly predict whether the generated scenario passes the plausibility filter?
3. How does generation quality vary between narratives from different reporting databases and road-user constellations?

# Timeline

The work spans six months from data collection to evaluation.

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype builds on an open-source scenario description format and an established open-source driving simulator [@Author24Generic].
Publicly available crash-report databases supply the natural-language input.
The implementation uses a hosted language-model API for generation and a constraint solver for the plausibility filter.

## Requirements

The prototype must convert a narrative into a parameterized scenario file that the simulator executes without manual repair.
It should support vehicle-to-vehicle and vehicle-to-pedestrian constellations.
Generation latency is not critical for the prototype; focus lies on output quality.
Closed-loop coupling to a driving function under test is not a requirement.

## Evaluation

Evaluation uses a held-out set of crash narratives to measure how much manoeuvre diversity the generated catalogue adds over the manual baseline (RQ1).
A feature-importance analysis over narrative properties identifies which of them predict filter rejection (RQ2).
Metrics include scenario execution success rate, plausibility-filter pass rate, and a coverage measure over the manoeuvre taxonomy.
A comparison across two reporting databases and both road-user constellations examines how generation quality varies (RQ3).

---
title: Language-Model-Based Scenario Generation for Automated Driving Validation
author: Jane Doe
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Author24Generic
  type: article-journal
  author:
  - family: Author
    given: A.
  issued:
    year: 2024
  title: Generic Title
  container-title: Journal Name
  DOI: 10.xxxx/xxxxx
- id: Miller23Scenario
  type: paper-conference
  author:
  - family: Miller
    given: J.
  issued:
    year: 2023
  title: Scenario Catalogues Meet Automated Driving Validation Practice
  container-title: Proceedings of the Example Conference on Intelligent Vehicles
  DOI: 10.xxxx/xxxx1
- id: Chen25Learning
  type: article-journal
  author:
  - family: Chen
    given: L.
  issued:
    year: 2025
  title: Learning Scenario Structure from Crash Report Narratives
  container-title: Journal of Empirical Intelligent Transportation Examples
  DOI: 10.xxxx/xxxx2
---
