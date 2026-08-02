Bachelor's Thesis Proposal

Submitted by: Erika Musterfrau
Matriculation number: 00000000
Address: Musterstraße 12, 12345 Musterstadt
Email: erika@example.org
Study programme: B.Sc. Computer Science

# 1 Introduction and Motivation

Automated driving functions are released with a declared Operational Design Domain that fixes the weather, road, and traffic conditions under which they may engage.
Test fleets record thousands of hours per week, and every drive can silently leave that domain without anyone noticing [@Weber24Policy].
Reviews of recorded drives in most organisations still happen at milestone boundaries and rely on manual spreadsheet inspection.
By the time a reviewer discovers that a function stayed active in dense fog, the evidence has already entered the safety argument [@Tanaka23Drift].
Automated domain auditing promises to close this gap by evaluating recorded drive logs against a machine-readable condition catalogue.
The proposed thesis develops and evaluates such an automated audit pipline for automated-driving log repositories.

# 2 Objectives and Work Packages

The overall objective is a working audit pipeline that flags out-of-domain engagements before the logs enter the release evidence.
The project is organised into the following work packages, which also serve as the guiding questions of the thesis:

1. How can the existing condition catalogue be translated into executable audit policies?
2. How can the audit engine be integrated into the continous integration pipeline?
3. How can audit findings be exported into a report that safety engineers can act on?

# 3 Approach

The audit engine builds on an open-source signal query language and evaluates recorded signal traces at ingest time [@Osei25Benchmarks].
A condition catalogue derived from a published operational-domain taxonomy serves as ground truth.
Detected violations are ranked by severity and written to a summary report.
The approach is validated on a set of deliberately out-of-domain example recordings.

# 4 Preliminary Chapter Structure

1. Introduction
2. Background and Related Work
3. Design of the Audit Pipeline
4. Implementation
5. Evaluation
6. Conclusion and Outlook

# 5 Timetable and Milestones

| Month | Milestone |
|---|---|
| Month 1 | Literature review complete |
| Month 2 | Condition catalogue translated into policies |
| Month 3 | Audit engine integrated into the pipeline |
| Month 4 | Evaluation finished, thesis submitted |

---
title: Automated Auditing of Operational Design Domain Compliance in Drive Logs
author: Erika Musterfrau
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Weber24Policy
  type: article-journal
  author:
  - family: Weber
    given: S.
  issued:
    year: 2024
  title: Policy-as-Code for Continuous Operational Domain Monitoring
  container-title: Journal of Example Vehicle Engineering
  DOI: 10.xxxx/xxxx3
- id: Tanaka23Drift
  type: paper-conference
  author:
  - family: Tanaka
    given: H.
  issued:
    year: 2023
  title: Drift Between Declared and Observed Operating Conditions in Test Fleets
  container-title: Proceedings of the Example Conference on Intelligent Vehicles
  DOI: 10.xxxx/xxxx4
- id: Osei25Benchmarks
  type: article-journal
  author:
  - family: Osei
    given: K.
  issued:
    year: 2025
  title: Benchmarks for Automated Drive Log Auditing
  container-title: Journal of Example Systems Validation
  DOI: 10.xxxx/xxxx5
---
