# Introduction to the Topic

Driver monitoring cameras stream continuously [@on].
This proposal studies region-of-interest selection [@Ghost99Missing].
[TODO: sharpen motivation]

# Contribution to the State-of-the-Art

Prior work crops the face region manually [@Lee24Gaze].

# Research Focus and Research Questions

The thesis examines automated region-of-interest selection.

1. To what degree can saliency-driven heuristics match expert region choices?

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype builds on an open-source gaze estimator [@Lee24Gaze].

## Requirements

The prototype must propose region sets for a given recording (RQ1).
[TODO: name the driving dataset]

## Evaluation

Accuracy against expert-chosen regions is measured on public recordings (RQ1).
---
title: Automated Region-of-Interest Selection
author: Erika Musterfrau
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: on
  type: article-journal
  author:
  - family: Grid
    given: P.
  issued:
    year: 2022
  title: Online Region Advisors
  DOI: 10.xxxx/yyy1
- id: Lee24Gaze
  type: paper-conference
  author:
  - family: Lee
    given: S.
  issued:
    year: 2024
  title: Gaze Region Cropping Revisited
  DOI: 10.xxxx/yyy2
- id: Lee24Gaze
  type: paper-conference
  author:
  - family: Lee
    given: S.
  issued:
    year: 2024
  title: Gaze Region Cropping Revisited (duplicate)
  DOI: 10.xxxx/yyy2
---
