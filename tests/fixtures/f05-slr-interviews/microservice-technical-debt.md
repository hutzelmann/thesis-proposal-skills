# Introduction to the Topic

Microservice architectures decompose software systems into small, independently deployable services.
Industrial adoption has grown rapidly, yet the architectural style introduces its own forms of technical debt [@Weber21Technical].
Accumulated debt slows down development, raises operational cost, and can erode the intended independence of services.
Primary studies on debt management in microservice systems have multiplied in recent years, but their findings remain scattered across venues and terminologies [@Okafor23Managing].
A consolidated view of this evidence would benefit practitioners and researchers alike.
This thesis provides such a consolidation through a systematic literature review.

# Contribution to the State-of-the-Art

Secondary studies to date either survey technical debt without regard for the architectural style or examine microservices without a debt perspective [@Lind24Empirical].
No systematic review consolidates which debt types are specific to microservice architectures and which management strategies address them.
This thesis closes that gap by mapping debt types, management strategies, and the empirical grounding of the reported evidence.
The resulting catalogue extends prior mapping work [@Weber21Technical] with an explicit assessment of study quality and industrial relevance.

# Research Focus and Research Questions

The thesis examines how the research literature characterizes and manages technical debt in microservice architectures.
Beyond cataloguing debt types, the review assesses under which conditions reported management strategies succeed and how strongly the evidence is grounded in industrial practice.

1. Which types of technical debt does the literature report as specific to microservice architectures, and to what degree do they differ from debt types known from monolithic systems?
2. Under which conditions do the reported management strategies reduce architecture-level technical debt effectively?
3. To what degree are the reported findings grounded in industrial systems rather than open-source or synthetic cases?

# Methodology for Research: Systematic Literature Review

## Search Strategy and Selection Criteria

The review follows established guidelines for systematic literature reviews in software engineering [@Sato25Guidelines].
Searches run over four digital libraries with a string that combines microservice terminology and technical debt terminology.
Included are peer-reviewed primary studies published since 2015 that report on technical debt in microservice systems; excluded are position papers, vendor whitepapers, and studies on generic service-oriented architectures.

## Quality Assessment and Extracted Information

Each included study is coded with the reported debt types, the management strategies applied, and the context factors of the studied systems.
A classification of the coded debt types against an established monolith-oriented taxonomy answers the first research question (RQ1).
Extraction further records the evidence type of every study, ranging from controlled experiment to anecdotal report.

## Synthesis

Thematic synthesis aggregates the coded strategies into a strategy catalogue and links each strategy to the conditions under which the primary studies report success (RQ2).
The recorded evidence types feed a maturity assessment of the field with respect to industrial grounding (RQ3).
To validate the synthesized catalogue, semi-structured interviews with practitioners from three industry partners complement the review, covering perceived completeness and practical relevance.
Interview findings are folded back into the final version of the strategy catalogue.

# Timeline

The thesis starts in September 2026 and is submitted in February 2027.

---
title: Managing Technical Debt in Microservice Architectures
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Weber21Technical
  type: paper-conference
  author:
  - family: Weber
    given: K.
  issued:
    year: 2021
  title: Technical Debt in Service-Oriented Systems — A Mapping Study
  container-title: Proceedings of the Example Conference on Software Architecture
  DOI: 10.xxxx/xxxx3
- id: Okafor23Managing
  type: article-journal
  author:
  - family: Okafor
    given: C.
  issued:
    year: 2023
  title: Managing Architectural Debt in Microservice Migrations
  container-title: Journal of Example Systems and Software
  DOI: 10.xxxx/xxxx4
- id: Lind24Empirical
  type: article-journal
  author:
  - family: Lind
    given: S.
  issued:
    year: 2024
  title: Empirical Studies of Architectural Technical Debt — State and Challenges
  container-title: Journal of Empirical Software Engineering Examples
  DOI: 10.xxxx/xxxx5
- id: Sato25Guidelines
  type: article-journal
  author:
  - family: Sato
    given: H.
  issued:
    year: 2025
  title: Guidelines for Systematic Reviews in Software Architecture Research
  container-title: Example Computing Surveys
  DOI: 10.xxxx/xxxx6
---
