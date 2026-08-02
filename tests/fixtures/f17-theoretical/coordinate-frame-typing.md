# Introduction to the Topic

Automated driving software combines geometric quantities such as positions, velocities, and bounding boxes that are each expressed in a particular reference frame.
A single mismatch between frames silently corrupts every downstream perception result, and empirical work documents such faults across robotics code bases [@Ortiz21Frame].
Static type systems can rule out frame mismatches before a program ever runs [@Brandt22Typing].
This thesis develops a type system that tracks reference frames in perception code while keeping the annotation burden low.

# Contribution to the State-of-the-Art

Runtime transform libraries resolve frames during execution and therefore cover only the paths a program actually takes.
Prior static approaches either fix the set of admissible frames in advance or demand frame annotations on nearly every declaration [@Brandt22Typing].
Unification over groupoids of rigid transforms makes inference of frame types feasible in principle [@Marek19Groupoid], but existing formulations stop short of time-varying and sensor-local frames.
This work contributes a type discipline that infers frames from a small set of boundary annotations and handles composed transforms soundly, which lowers the entry barrier for perception developers.

# Research Focus and Research Questions

The research focus is the static enforcement of reference-frame consistency in perception code through a type system with inference, restricted to a core calculus rather than a full programming language.
The analysis centres on soundness, decidability, and the annotation effort the discipline demands in practice.

1. To what degree can a static type discipline with frame inference rule out reference-frame mismatches in perception code?
2. Under which conditions does frame inference remain sound and decidable when time-varying and sensor-local frames interact?
3. To what degree does boundary-only annotation reduce the annotation effort compared to fully annotated frame typing?

# Methodology for Research: Theoretical Analysis

## Formalization

The formal core is a simply typed lambda calculus extended with geometric types indexed by frame expressions over a groupoid of rigid transforms [@Marek19Groupoid].
Typing rules constrain geometric operations so that addition requires equal frames while transform application composes them.
A unification-based inference algorithm derives frame indices from annotations placed only at function boundaries.

## Requirements

The type system must be sound: a well-typed program can never combine values expressed in incompatible frames.
Inference must terminate on every program of the core calculus.
Neglectable are type-checking performance, error-message quality, and coverage of language features beyond the core calculus, such as records and higher-kinded abstractions.

## Example

A sensor-fusion routine that merges lidar clusters with camera detections serves as the running example, mixing sensor-local frames with the vehicle frame and a global map frame.
Applying the type discipline to seeded frame faults in the example shows to what degree the discipline rules them out (RQ1).
A variant of the example that combines time-varying odometry frames with sensor-local frames probes the conditions under which inference stays sound and decidable (RQ2).
Counting the annotations the example needs under boundary-only inference against a fully annotated version quantifies the reduction in annotation effort (RQ3).

---
title: A Type System for Reference Frame Consistency in Perception Code
author: Max Mustermann
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Ortiz21Frame
  type: article-journal
  author:
  - family: Ortiz
    given: R.
  issued:
    year: 2021
  title: Frame Faults in Robotics Software — An Empirical Study
  container-title: Journal of Example Software Engineering
  DOI: 10.xxxx/xxx30
- id: Brandt22Typing
  type: paper-conference
  author:
  - family: Brandt
    given: K.
  issued:
    year: 2022
  title: Typing Reference Frames in Robotics Programs
  container-title: Proceedings of the Example Conference on Programming Languages
  DOI: 10.xxxx/xxx31
- id: Marek19Groupoid
  type: article-journal
  author:
  - family: Marek
    given: J.
  issued:
    year: 2019
  title: Groupoid Unification for Frame Type Inference
  container-title: Journal of Example Type Systems
  DOI: 10.xxxx/xxx32
---
