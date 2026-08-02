# Idea Notes

Working title: Rater Disagreement in Camera-Based Drowsiness Detection.

## Problem Sketch

Camera-based drowsiness detectors are trained against drowsiness labels that expert raters assign by watching recorded video after the drive.
Two raters watching the same minute frequently disagree, and the disagreement is resolved by convention rather than by evidence.
Reported detection accuracies are therefore measured against a ground truth whose own reliability is rarely stated.
The idea is to quantify how much of the reported accuracy gap between detectors is attributable to label noise rather than to model quality.

## Candidate Research-Question Directions

These are candidate directions, not final research questions:

- To what degree does inter-rater agreement on drowsiness labels bound the achievable accuracy of a detector trained on them?
- Under which recording conditions do raters disagree most, and do detectors fail in the same conditions?
- How do reported accuracy rankings between detectors change when evaluated against consensus labels instead of single-rater labels?

## Literature Anchors

Nakamura et al. survey drowsiness detection benchmarks and note that label provenance is rarely reported [@Nakamura24Drowsy].
That gap — accuracy numbers everywhere, label reliability nowhere — is where the thesis could differentiate itself.

## Open Questions

[TODO: decide between prototype implementation and systematic literature review]
[TODO: find a second public dataset with per-rater labels]

---
title: Rater Disagreement in Camera-Based Drowsiness Detection
author: Erika Musterfrau
subtitle: "[TODO: confirm degree level]"
lang: en
references:
- id: Nakamura24Drowsy
  type: paper-conference
  author:
  - family: Nakamura
    given: K.
  - family: Silva
    given: R.
  issued:
    year: 2024
  title: "Drowsiness Detection Benchmarks: A Survey of Labelling Practice"
  container-title: Proceedings of the Example Conference on Driver State Monitoring
  DOI: 10.xxxx/xxx50
---
