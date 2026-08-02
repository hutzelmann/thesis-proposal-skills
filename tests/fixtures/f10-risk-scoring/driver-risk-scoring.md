# Context and Motivation

Logistics companies operate hundreds of vehicles, and a single fatigued driver can turn a routine shift into a serious collision.
Driver risk management at Example Logistics AG currently relies on annual self-assessment questionnaires, which capture risk levels months after the underlying situation has changed.
Recent work shows that telematics data such as harsh-braking frequency and lane-keeping variability can predict incident involvement earlier than questionnaire-based ratings.
This Master's thesis investigates a data-driven risk score that aggregates such operational signals into a single, continuously updated indicator.

# Problem Statement

Existing fleet dashboards at the company aggregate data manually and update quarterly at best.
Fleet safety officers therefore intervene with a driver only after an incident has already occurred.
A continuously computed risk score could support earlier intervention, but it is unclear which signals carry predictive value and how the score should be presented to safety officers.

# Objectives and Research Questions

The thesis aims to design, implement, and assess a risk-scoring prototype on top of the company's telematics warehouse.

1. How can the relevant behavioural signals be extracted from the existing telematics warehouse?
2. How can the risk score be implemented so that it updates daily without manual intervention?
3. To what degree do data-driven risk scores agree with the assessments of experienced fleet safety officers?
4. Under which conditions does the score fail to reflect actual driver risk?

# Planned Approach

The prototype extracts braking, steering, and duty-time signals, normalises them, and combines them into a weighted score.
Weights are calibrated on two years of historical fleet data.
The resulting scores are compared against past incident records and discussed in feedback sessions with the fleet safety department.
Success is assessed primarily through the feedback of the internal stakeholders.

# Work Plan and Phases

| Phase | Content |
|---|---|
| Phase 1 | Data exploration and signal selection |
| Phase 2 | Score implementation and calibration |
| Phase 3 | Comparison against historical incidents |
| Phase 4 | Stakeholder feedback and thesis writing |

# Supervisors

University supervisor: Prof. Dr. John Public (john.public@example.org)
Company supervisor: Max Mustermann (max.mustermann@example.org), Head of Fleet Safety Analytics

Confidential — internal use only. This document contains internal driver records of Example Logistics AG.

---
title: Data-Driven Risk Scoring for Commercial Fleet Drivers
author: Erika Musterfrau
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Silva24Early
  type: article-journal
  author:
  - family: Silva
    given: R.
  issued:
    year: 2024
  title: Early Warning Signals for Driver Risk Escalation
  container-title: Journal of Example Traffic Safety Research
  DOI: 10.xxxx/xxxx8
- id: Novak23Telematics
  type: article-journal
  author:
  - family: Novak
    given: P.
  issued:
    year: 2023
  title: "Telematics-Based Driver Risk Analytics: A Survey"
  container-title: Journal of Example Fleet Operations
  DOI: 10.xxxx/xxxx9
- id: Berg25Scoring
  type: paper-conference
  author:
  - family: Berg
    given: L.
  issued:
    year: 2025
  title: Scoring Operational Driver Risk from Telematics Data
  container-title: Proceedings of the Example Conference on Transport Informatics
  DOI: 10.xxxx/xxx10
---
