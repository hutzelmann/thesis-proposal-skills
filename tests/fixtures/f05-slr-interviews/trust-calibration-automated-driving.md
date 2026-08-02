# Introduction and Motivation

Partially automated driving functions hand control back and forth between the vehicle and the driver.
Deployment has grown rapidly, yet the style of interaction introduces its own forms of miscalibrated trust [@Weber21Trust].
Overtrust leads drivers to disengage from supervision, while undertrust leads them to switch the function off entirely.
Primary studies on trust calibration in automated driving have multiplied in recent years, but their findings remain scattered across venues and terminologies [@Okafor23Calibrating].
A consolidated view of this evidence would benefit designers and researchers alike.
This thesis provides such a consolidation through a systematic literature review.

# Problem Statement and Research Questions

The thesis examines how the research literature characterizes and repairs miscalibrated trust in partially automated driving.
Beyond cataloguing miscalibration patterns, the review assesses under which conditions reported interface strategies succeed and how strongly the evidence is grounded in realistic driving contexts.

1. Which patterns of miscalibrated trust does the literature report as specific to partially automated driving, and to what degree do they differ from patterns known from other supervisory-control domains?
2. Under which conditions do the reported interface strategies bring driver trust closer to actual system reliability?
3. To what degree are the reported findings grounded in on-road or high-fidelity simulator studies rather than video-based or questionnaire-only designs?

# Related Work

Secondary studies to date either survey trust in automation without regard for the driving context or examine driving interfaces without a trust perspective [@Lind24Empirical].
No systematic review consolidates which miscalibration patterns are specific to partially automated driving and which interface strategies address them.
This thesis closes that gap by mapping miscalibration patterns, interface strategies, and the empirical grounding of the reported evidence.
The resulting catalogue extends prior mapping work [@Weber21Trust] with an explicit assessment of study quality and on-road relevance.
Trust measurement instruments themselves vary widely across the field, from single-item confidence ratings to validated multi-factor scales [@Ostrom22Instruments].
@Delgado23Overtrust show that instruments disagree most precisely where automation is partially reliable, which is the regime this review targets.
Reviews of supervisory control outside driving report the same miscalibration patterns under different names [@Fischer21Supervisory], and guidance on synthesising heterogeneous measurement practice is available [@Kowalski24Synthesis].
Reporting standards for empirical driving studies remain uneven, which complicates any quality assessment built on published detail alone [@Aranda25Reporting].
Handover quality has been proposed as an observable proxy for calibrated trust, which would sidestep instrument disagreement altogether [@Novak24Handover].

# Methodology: Systematic Literature Review

## Use Case Definition

The object of study is the published empirical literature on trust in partially automated driving, restricted to studies that measure trust with human participants.
This body suits the research questions because miscalibration is only observable where trust and system reliability are measured together, which rules out purely conceptual work.
Access is unrestricted through the university's database subscriptions, and the corpus is bounded to English-language publications, which is a known limitation of the coverage claim.

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

# Objectives

The primary objective is to produce a validated catalogue of trust-miscalibration patterns and the interface strategies reported to repair them.

Supporting objectives:

- Develop a coding scheme covering miscalibration pattern, interface strategy, and study context.
- Classify the coded patterns against an established supervisory-control taxonomy.
- Assess the ecological validity of every included study on a documented scale.
- Derive a research agenda from the mismatches between strategies and evidence.

# Expected Contributions and Results

The scientific contribution is a consolidated catalogue of miscalibration patterns and repair strategies, each annotated with the conditions under which the evidence supports it.
The practical contribution is a short decision aid that points interface designers to the strategies with the strongest evidence for their situation.
It is expected that most published strategies address overtrust and that undertrust remains comparatively unstudied, and that video-based designs dominate the evidence base.
Limitations are foreseeable: English-language sources only, dependence on what primary studies chose to report, and a quality assessment that can judge reporting rather than conduct.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Protocol and pilot search | 1-3 |
| Full database search and screening | 3-8 |
| Full-text coding | 7-14 |
| Practitioner interviews | 12-16 |
| Synthesis and catalogue construction | 15-20 |
| Writing and revision | 18-24 |

Screening gates everything downstream, so a wider-than-expected result set is the main schedule risk; the protocol therefore fixes the inclusion criteria before the full search runs.
Coding and interview scheduling overlap deliberately, because recruiting practitioners takes longer than the coding of any single batch.
Four weeks of overlap between synthesis and writing absorb feedback rounds.

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
- id: Ostrom22Instruments
  type: article-journal
  author:
  - family: Ostrom
    given: L.
  issued:
    year: 2022
  title: Instruments for Measuring Trust in Automation — A Comparison
  container-title: Journal of Example Human Factors and Systems
  DOI: 10.xxxx/xx31
- id: Delgado23Overtrust
  type: paper-conference
  author:
  - family: Delgado
    given: R.
  issued:
    year: 2023
  title: Overtrust under Partial Reliability
  container-title: Proceedings of the Example Conference on Automotive Interfaces
  DOI: 10.xxxx/xx32
- id: Fischer21Supervisory
  type: article-journal
  author:
  - family: Fischer
    given: M.
  issued:
    year: 2021
  title: Supervisory Control and the Vigilance Decrement Revisited
  container-title: Example Journal of Cognitive Engineering
  DOI: 10.xxxx/xx33
- id: Kowalski24Synthesis
  type: article-journal
  author:
  - family: Kowalski
    given: A.
  issued:
    year: 2024
  title: Synthesising Heterogeneous Measurement Practice in Review Studies
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xx34
- id: Aranda25Reporting
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2025
  title: Reporting Completeness in Empirical Driving Studies
  container-title: Journal of Example Traffic Safety Research
  DOI: 10.xxxx/xx35
- id: Novak24Handover
  type: paper-conference
  author:
  - family: Novak
    given: T.
  issued:
    year: 2024
  title: Handover Quality as a Trust Signal
  container-title: Proceedings of the Example Symposium on Human Factors
  DOI: 10.xxxx/xx36
---
