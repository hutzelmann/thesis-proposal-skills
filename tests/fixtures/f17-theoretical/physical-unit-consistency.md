# A Type System for Physical Unit Consistency in Numerical Code

*Bachelor's Thesis Proposal*

## Introduction to the Topic

Scientific software combines physical quantities such as lengths, masses, and durations in long chains of numerical operations.
A single mismatch between units silently corrupts every downstream result, and empirical work documents such faults across scientific code bases [@Ortiz21Unit].
Static type systems can rule out unit mismatches before a program ever runs [@Brandt22Typing].
This thesis develops a type system that tracks physical units in numerical code while keeping the annotation burden low.

## Contribution to the State-of-the-Art

Runtime unit libraries check quantities during execution and therefore cover only the paths a program actually takes.
Prior static approaches either fix the set of admissible dimensions in advance or demand unit annotations on nearly every declaration [@Brandt22Typing].
Unification over abelian groups makes inference of dimension types feasible in principle [@Marek19Abelian], but existing formulations stop short of derived and scaled units.
This work contributes a type discipline that infers units from a small set of boundary annotations and handles derived units soundly, which lowers the entry barrier for scientific programmers.

## Research Focus and Research Questions

The research focus is the static enforcement of physical unit consistency in numerical code through a type system with inference, restricted to a core calculus rather than a full programming language.
The analysis centres on soundness, decidability, and the annotation effort the discipline demands in practice.

1. To what degree can a static type discipline with unit inference rule out physical unit mismatches in numerical code?
2. Under which conditions does unit inference remain sound and decidable when derived and scaled units interact?
3. To what degree does boundary-only annotation reduce the annotation effort compared to fully annotated dimension typing?

## Methodology for Research: Theoretical Analysis

### Formalization

The formal core is a simply typed lambda calculus extended with numeric types indexed by unit expressions over an abelian group [@Marek19Abelian].
Typing rules constrain arithmetic so that addition requires equal units while multiplication composes them.
A unification-based inference algorithm derives unit indices from annotations placed only at function boundaries.

### Requirements

The type system must be sound: a well-typed program can never combine values of incompatible units.
Inference must terminate on every program of the core calculus.
Neglectable are type-checking performance, error-message quality, and coverage of language features beyond the core calculus, such as records and higher-kinded abstractions.

### Example

A numerical integration routine for satellite orbits serves as the running example, mixing base units with derived units such as velocity and acceleration.
Applying the type discipline to seeded unit faults in the example shows to what degree the discipline rules them out (RQ1).
A variant of the example that combines derived and scaled units probes the conditions under which inference stays sound and decidable (RQ2).
Counting the annotations the example needs under boundary-only inference against a fully annotated version quantifies the reduction in annotation effort (RQ3).

## Timeline

The thesis starts in May 2027 and is submitted in October 2027.

## References

---
references:
- id: Ortiz21Unit
  type: article-journal
  author:
  - family: Ortiz
    given: R.
  issued:
    year: 2021
  title: Unit Faults in Scientific Software — An Empirical Study
  container-title: Journal of Example Software Engineering
  DOI: 10.xxxx/xxx30
- id: Brandt22Typing
  type: paper-conference
  author:
  - family: Brandt
    given: K.
  issued:
    year: 2022
  title: Typing Physical Dimensions in Numerical Programs
  container-title: Proceedings of the Example Conference on Programming Languages
  DOI: 10.xxxx/xxx31
- id: Marek19Abelian
  type: article-journal
  author:
  - family: Marek
    given: J.
  issued:
    year: 2019
  title: Abelian Group Unification for Dimension Type Inference
  container-title: Journal of Example Type Systems
  DOI: 10.xxxx/xxx32
---
