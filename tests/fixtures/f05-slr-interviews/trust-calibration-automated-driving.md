# Introduction to the Topic

Partially automated driving functions hand control back and forth between the vehicle and the driver.
Deployment has grown rapidly, yet the style of interaction introduces its own forms of miscalibrated trust [@Weber21Trust].
Overtrust leads drivers to disengage from supervision, while undertrust leads them to switch the function off entirely.
Primary studies on trust calibration in automated driving have multiplied in recent years, but their findings remain scattered across venues and terminologies [@Okafor23Calibrating].
A consolidated view of this evidence would benefit designers and researchers alike.
This thesis provides such a consolidation through a systematic literature review.

# Contribution to the State-of-the-Art

Secondary studies to date either survey trust in automation without regard for the driving context or examine driving interfaces without a trust perspective [@Lind24Empirical].
No systematic review consolidates which miscalibration patterns are specific to partially automated driving and which interface strategies address them.
This thesis closes that gap by mapping miscalibration patterns, interface strategies, and the empirical grounding of the reported evidence.
The resulting catalogue extends prior mapping work [@Weber21Trust] with an explicit assessment of study quality and on-road relevance.

# Research Focus and Research Questions

The thesis examines how the research literature characterizes and repairs miscalibrated trust in partially automated driving.
Beyond cataloguing miscalibration patterns, the review assesses under which conditions reported interface strategies succeed and how strongly the evidence is grounded in realistic driving contexts.

1. Which patterns of miscalibrated trust does the literature report as specific to partially automated driving, and to what degree do they differ from patterns known from other supervisory-control domains?
2. Under which conditions do the reported interface strategies bring driver trust closer to actual system reliability?
3. To what degree are the reported findings grounded in on-road or high-fidelity simulator studies rather than video-based or questionnaire-only designs?

# Methodology for Research: Systematic Literature Review

## Search Strategy and Selection Criteria

The review follows established guidelines for systematic literature reviews in human-computer interaction [@Sato25Guidelines].
Searches run over four digital libraries with a string that combines automated-driving terminology and trust-calibration terminology.
Included are peer-reviewed primary studies published since 2015 that report empirical trust measurements with human participants; excluded are position papers, vendor whitepapers, and studies on fully manual driving.

## Extracted Information

Each included study is coded with the reported miscalibration pattern, the interface strategy applied, and the context factors of the studied driving task.
A classification of the coded patterns against an established supervisory-control taxonomy answers the first research question (RQ1).
Extraction further records the evidence type of every study, ranging from controlled on-road experiment to anecdotal report.

## Synthesis

Thematic synthesis aggregates the coded strategies into a strategy catalogue and links each strategy to the conditions under which the primary studies report success (RQ2).
The recorded evidence types feed a maturity assessment of the field with respect to ecological validity (RQ3).
To validate the synthesized catalogue, semi-structured interviews with human-factors engineers from three industry partners complement the review, covering perceived completeness and practical relevance.
Interview findings are folded back into the final version of the strategy catalogue.

---
title: Trust Calibration in Partially Automated Driving
author: Erika Musterfrau
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Weber21Trust
  type: paper-conference
  author:
  - family: Weber
    given: K.
  issued:
    year: 2021
  title: Trust in Driving Automation — A Mapping Study
  container-title: Proceedings of the Example Conference on Automotive Interfaces
  DOI: 10.xxxx/xxxx3
- id: Okafor23Calibrating
  type: article-journal
  author:
  - family: Okafor
    given: C.
  issued:
    year: 2023
  title: Calibrating Driver Trust During Automation Handovers
  container-title: Journal of Example Human Factors and Systems
  DOI: 10.xxxx/xxxx4
- id: Lind24Empirical
  type: article-journal
  author:
  - family: Lind
    given: S.
  issued:
    year: 2024
  title: Empirical Studies of Trust in Automation — State and Challenges
  container-title: Journal of Empirical Interaction Research Examples
  DOI: 10.xxxx/xxxx5
- id: Sato25Guidelines
  type: article-journal
  author:
  - family: Sato
    given: H.
  issued:
    year: 2025
  title: Guidelines for Systematic Reviews in Human-Computer Interaction Research
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xxxx6
---
