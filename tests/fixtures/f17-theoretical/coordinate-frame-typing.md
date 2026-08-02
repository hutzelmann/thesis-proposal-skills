# Introduction and Motivation

Automated driving software combines geometric quantities such as positions, velocities, and bounding boxes that are each expressed in a particular reference frame.
A single mismatch between frames silently corrupts every downstream perception result, and empirical work documents such faults across robotics code bases [@Ortiz21Frame].
Static type systems can rule out frame mismatches before a program ever runs [@Brandt22Typing].
This thesis develops a type system that tracks reference frames in perception code while keeping the annotation burden low.

# Problem Statement and Research Questions

The research focus is the static enforcement of reference-frame consistency in perception code through a type system with inference, restricted to a core calculus rather than a full programming language.
The analysis centres on soundness, decidability, and the annotation effort the discipline demands in practice.

1. To what degree can a static type discipline with frame inference rule out reference-frame mismatches in perception code?
2. Under which conditions does frame inference remain sound and decidable when time-varying and sensor-local frames interact?
3. To what degree does boundary-only annotation reduce the annotation effort compared to fully annotated frame typing?

# Related Work

Runtime transform libraries resolve frames during execution and therefore cover only the paths a program actually takes.
Prior static approaches either fix the set of admissible frames in advance or demand frame annotations on nearly every declaration [@Brandt22Typing].
Unification over groupoids of rigid transforms makes inference of frame types feasible in principle [@Marek19Groupoid], but existing formulations stop short of time-varying and sensor-local frames.
This work contributes a type discipline that infers frames from a small set of boundary annotations and handles composed transforms soundly, which lowers the entry barrier for perception developers.
Empirical studies of robotics defects rank frame and unit confusion among the most frequently reported silent faults [@Ferreira22Defects].
@Kaur24Units show that dimension typing transfers to geometric types only when the underlying algebra is a groupoid rather than a group.
Gradual typing offers a migration path for codebases that cannot be annotated all at once [@Delgado23Gradual], and annotation burden is the documented reason such disciplines fail to be adopted [@Lindqvist21Burden].
Runtime transform libraries remain the state of practice and define the behaviour any static discipline must preserve [@Aranda25Transforms].
Unification over groupoids has been studied independently of typing, and the known complexity results bound what inference can achieve [@Beck24Groupoid].
Sensor-local frames multiply in multi-modal stacks, which is where the annotation burden becomes prohibitive [@Novak23Sensor].

# Methodology: Theoretical Analysis

## Use Case Definition

The object of study is a perception stack of the kind built on ROS-style message passing, where every geometric message carries a frame identifier that the compiler currently ignores.
This use case suits the research questions because frame mismatches there are both common and silent, and because the frame identifiers already present give the type discipline something to anchor on.
The analysis is bounded to a core calculus rather than the full language, so library-level and reflection-based frame handling stay out of scope.

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

# Objectives

The primary objective is a sound type discipline with inference that rules out reference-frame mismatches in perception code.

Supporting objectives:

- Define a core calculus with geometric types indexed by frame expressions.
- Formulate typing rules and a unification-based inference algorithm.
- Prove soundness and characterise the conditions under which inference terminates.
- Quantify the annotation burden against a fully annotated baseline.

# Expected Contributions and Results

The scientific contribution is a soundness result for frame typing that covers time-varying and sensor-local frames, together with the decidability boundary of its inference.
The practical contribution is a type discipline that needs annotations only at function boundaries, which is what makes retrofitting plausible.
It is expected that inference stays decidable while frame composition remains finite, and that boundary-only annotation cuts the annotation count substantially against full annotation.
Limitations are foreseeable: a core calculus rather than a real language, no implementation, and no claim about error-message quality or type-checking performance.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Literature and calculus selection | 1-4 |
| Core calculus definition | 3-8 |
| Typing rules and inference algorithm | 7-13 |
| Soundness and termination proofs | 12-18 |
| Running example and annotation count | 17-20 |
| Writing and revision | 18-24 |

The proofs depend entirely on the finished calculus, which puts the calculus definition on the critical path.
The running example is deliberately written after the proofs so that it illustrates their preconditions rather than anticipating them.
Four weeks of overlap between the example and writing absorb feedback.

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
- id: Ferreira22Defects
  type: article-journal
  author:
  - family: Ferreira
    given: J.
  issued:
    year: 2022
  title: A Study of Silent Defects in Robotics Middleware Code
  container-title: Journal of Example Software Engineering
  DOI: 10.xxxx/xx71
- id: Kaur24Units
  type: paper-conference
  author:
  - family: Kaur
    given: S.
  issued:
    year: 2024
  title: From Dimension Types to Geometric Types
  container-title: Proceedings of the Example Conference on Programming Languages
  DOI: 10.xxxx/xx72
- id: Delgado23Gradual
  type: article-journal
  author:
  - family: Delgado
    given: R.
  issued:
    year: 2023
  title: Gradual Typing as a Migration Path for Legacy Codebases
  container-title: Example Journal of Type Systems
  DOI: 10.xxxx/xx73
- id: Lindqvist21Burden
  type: article-journal
  author:
  - family: Lindqvist
    given: M.
  issued:
    year: 2021
  title: Annotation Burden and the Adoption of Static Disciplines
  container-title: Journal of Empirical Software Engineering Examples
  DOI: 10.xxxx/xx74
- id: Aranda25Transforms
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2025
  title: Runtime Transform Libraries and Their Failure Modes
  container-title: Example Journal of Robotics Software
  DOI: 10.xxxx/xx75
- id: Beck24Groupoid
  type: paper-conference
  author:
  - family: Beck
    given: A.
  issued:
    year: 2024
  title: Groupoid Unification Revisited
  container-title: Proceedings of the Example Symposium on Types
  DOI: 10.xxxx/xx76
- id: Novak23Sensor
  type: article-journal
  author:
  - family: Novak
    given: T.
  issued:
    year: 2023
  title: Sensor-Local Frames in Multi-Modal Perception Stacks
  container-title: Journal of Example Vehicular Intelligence
  DOI: 10.xxxx/xx77
---
