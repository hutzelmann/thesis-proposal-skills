# Introduction to the Topic

Continuous integration pipelines produce large volumes of build telemetry that teams rarely inspect systematically [@Nowak24Pipelines].
Failures are diagnosed reactively, often long after the change that caused them was merged.
Aggregating this telemetry into an operational view is therefore a recurring concern in industrial software delivery [@Ferreira23Telemetry].

# Contribution to the State-of-the-Art

Existing observability work reports pipeline health as raw metric time series [@Nowak24Pipelines].
Classification of build failures has been studied separately, on curated offline datasets [@Ibarra25Failures].
This thesis connects the two: it evaluates whether failure classification retains its reported accuracy when it runs over live pipeline telemetry, and under which telemetry conditions the accuracy degrades.

# Research Focus and Research Questions

The research focus is the accuracy of automated build-failure classification under operational conditions, as opposed to the curated conditions under which such classifiers are usually reported.

1. To what degree does classification accuracy measured on curated failure datasets carry over to live pipeline telemetry?
2. Under which telemetry conditions, such as truncated logs or missing stage metadata, does classification accuracy degrade measurably?
3. How does classification accuracy differ between infrastructure failures and test failures?

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype consumes pipeline telemetry through the platform's event stream and stores it in a time-series database.
Failure classification reuses the published model architecture described in the prior work [@Ibarra25Failures].
The visual layer builds on an existing charting component rather than a bespoke rendering stack.

## Requirements

The prototype must ingest build events continuously and classify each failed build into an operational category with a confidence score.
It must expose the classification alongside the raw telemetry that produced it, so that a disagreement can be traced.
Alerting, access control, and multi-tenant deployment are explicitly out of scope.
Response latency is not a requirement; classification runs after the build completes.

## Evaluation

A labelled sample of live builds is compared against the accuracy reported for curated datasets (RQ1).
Telemetry is degraded systematically, by truncating logs and withholding stage metadata, and accuracy is measured per degradation level (RQ2).
Classification results are stratified by failure category to compare infrastructure against test failures (RQ3).

# Timeline

The thesis starts in April 2027 and is submitted in September 2027.

---
title: Implementing an AI-Powered Kubernetes Dashboard at Musterfirma GmbH
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Nowak24Pipelines
  type: article-journal
  author:
  - family: Nowak
    given: P.
  issued:
    year: 2024
  title: Pipeline Telemetry in Industrial Continuous Integration
  container-title: Journal of Example Software Delivery
  DOI: 10.xxxx/xxxx7
- id: Ferreira23Telemetry
  type: paper-conference
  author:
  - family: Ferreira
    given: M.
  issued:
    year: 2023
  title: Telemetry Aggregation for Delivery Teams
  container-title: Proceedings of the Example Conference on Software Operations
  DOI: 10.xxxx/xxxx8
- id: Ibarra25Failures
  type: article-journal
  author:
  - family: Ibarra
    given: R.
  issued:
    year: 2025
  title: Classifying Build Failures from Log Evidence
  container-title: Journal of Example Empirical Software Engineering
  DOI: 10.xxxx/xxxx9
---
