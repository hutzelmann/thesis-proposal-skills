Bachelor's Thesis Proposal

Submitted by: Erika Musterfrau
Matriculation number: 00000000
Address: Musterstraße 12, 12345 Musterstadt
Email: erika@example.org
Study programme: B.Sc. Computer Science

# 1 Introduction and Motivation

Cloud deployments change daily, and every change can silently violate regulatory requirements.
Compliance audits in most organisations still happen quarterly and rely on manual spreadsheet reviews [@Weber24Policy].
By the time an auditor discovers a misconfigured storage bucket, the violation may have persisted for months.
Automated compliance auditing promises to close this gap by evaluating configuration snapshots against a machine-readable rule catalogue [@Tanaka23Drift].
The proposed thesis develops and evaluates such an automated audit pipline for infrastructure-as-code repositories.

# 2 Objectives and Work Packages

The overall objective is a working audit pipeline that flags non-compliant configurations before they reach production.
The project is organised into the following work packages, which also serve as the guiding questions of the thesis:

1. How can the existing rule catalogue be translated into executable audit policies?
2. How can the audit engine be integrated into the continous integration pipeline?
3. How can audit findings be exported into a report that compliance officers can act on?

# 3 Approach

The audit engine builds on an open-source policy language and evaluates configuration files at commit time [@Osei25Benchmarks].
A rule catalogue derived from a public cloud-security benchmark serves as ground truth.
Detected violations are ranked by severity and written to a summary report.
The approach is validated on a set of intentionally misconfigured example repositories.

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
| Month 2 | Rule catalogue translated into policies |
| Month 3 | Audit engine integrated into the pipeline |
| Month 4 | Evaluation finished, thesis submitted |

---
title: Automated Compliance Auditing of Cloud Configurations
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
  title: Policy-as-Code for Continuous Compliance Auditing
  container-title: Journal of Example Cloud Engineering
  DOI: 10.xxxx/xxxx3
- id: Tanaka23Drift
  type: paper-conference
  author:
  - family: Tanaka
    given: H.
  issued:
    year: 2023
  title: Drift Detection in Infrastructure-as-Code Repositories
  container-title: Proceedings of the Example Conference on Cloud Computing
  DOI: 10.xxxx/xxxx4
- id: Osei25Benchmarks
  type: article-journal
  author:
  - family: Osei
    given: K.
  issued:
    year: 2025
  title: Benchmarks for Automated Cloud Configuration Audits
  container-title: Journal of Example Systems Security
  DOI: 10.xxxx/xxxx5
---
