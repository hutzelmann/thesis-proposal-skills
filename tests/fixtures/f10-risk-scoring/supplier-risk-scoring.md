# Context and Motivation

Manufacturing companies depend on hundreds of suppliers, and a single delayed shipment can halt an entire production line.
Supplier risk management at Example Logistics AG currently relies on annual self-assessment questionnaires, which capture risk levels months after the underlying situation has changed.
Recent work shows that operational data such as delivery punctuality and quality-inspection outcomes can predict supplier failures earlier than questionnaire-based ratings.
This Master's thesis investigates a data-driven risk score that aggregates such operational signals into a single, continuously updated indicator.

# Problem Statement

Existing risk dashboards at the company aggregate data manually and update quarterly at best.
Purchasing teams therefore escalate supplier issues only after delays have already occurred.
A continuously computed risk score could support earlier escalation, but it is unclear which signals carry predictive value and how the score should be presented to purchasers.

# Objectives and Research Questions

The thesis aims to design, implement, and assess a risk-scoring prototype on top of the company's data warehouse.

1. How can the relevant operational signals be extracted from the existing data warehouse?
2. How can the risk score be implemented so that it updates daily without manual intervention?
3. To what degree do data-driven risk scores agree with the assessments of experienced purchasers?
4. Under which conditions does the score fail to reflect actual supplier risk?

# Planned Approach

The prototype extracts delivery, quality, and financial signals, normalises them, and combines them into a weighted score.
Weights are calibrated on two years of historical supplier data.
The resulting scores are compared against past supplier incidents and discussed in feedback sessions with the purchasing department.
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
Company supervisor: Max Mustermann (max.mustermann@example.org), Head of Procurement Analytics

Confidential — internal use only. This document contains internal supplier information of Example Logistics AG.

---
title: Data-Driven Risk Scoring for Supplier Management
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
  title: Early Warning Signals for Supplier Disruptions
  container-title: Journal of Example Supply Chain Research
  DOI: 10.xxxx/xxxx8
- id: Novak23Supply
  type: article-journal
  author:
  - family: Novak
    given: P.
  issued:
    year: 2023
  title: "Supply Chain Risk Analytics: A Survey"
  container-title: Journal of Example Operations Management
  DOI: 10.xxxx/xxxx9
- id: Berg25Scoring
  type: paper-conference
  author:
  - family: Berg
    given: L.
  issued:
    year: 2025
  title: Scoring Operational Supplier Risk from Transaction Data
  container-title: Proceedings of the Example Conference on Business Informatics
  DOI: 10.xxxx/xxx10
---
