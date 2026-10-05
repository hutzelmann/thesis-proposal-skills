# Predicting Flaky Tests from Continuous-Integration Histories

*Master's Thesis Proposal*

## Idea Notes

Working title: Predicting Flaky Tests from Continuous-Integration Histories.

### Problem Sketch

A flaky test passes and fails on the same code, so every red build forces a developer to decide whether the failure is real.
Projects answer with automatic reruns, which hide flakiness instead of locating it and multiply the CI time spent on it.
Static predictors flag likely-flaky tests before they fail, but they are trained and evaluated inside the project they come from.
The idea is to test whether the CI history a project already records — run outcomes, timings, retry counts — predicts flakiness better than test code alone, and whether that signal carries across projects.

### Candidate Research-Question Directions

These are candidate directions, not final research questions:

- To what degree do features mined from CI run histories improve flaky-test prediction over features from test code alone?
- How does prediction quality change when a model trained on one set of projects is applied to unseen projects?
- Under which retry budgets does history-based prediction find flaky tests that rerun-based detection misses?

### Methodology Notes

Empirical Model Evaluation fits: the thesis trains and compares predictors on recorded CI data rather than building a tool or running a user study.

### Literature Anchors

The central source is the large CI study [@Lindqvist25Flaky]. Its findings, as noted while reading:

- It analyses 1.2 million CI runs from 310 open-source projects over three years.
- 61 % of the flaky failures it classifies stem from timing and asynchronous waits.
- Rerun-based detection with a cap of three retries misses about a third of the flaky tests it identifies.
- Flaky tests cluster in test classes that touch the network or the file system.
- Flaky failures consume a median 4.2 % of a project's CI time.

Further sources, one note each:

- Rerun-based detection and its retry-budget trade-off [@Brandt24Rerun].
- Static prediction from test-code features, evaluated within single projects [@Okafor23Static].
- Identifier vocabulary of test code as a flakiness predictor [@Sanz23Vocabulary].
- Test-order dependence as a separate flakiness class [@Wexler22Order].
- Quarantining flaky tests in industrial pipelines [@Hagen24Quarantine].
- Developer survey on how flaky failures are triaged [@Moreau23Survey].
- Root-cause taxonomy of flaky tests [@Takeda24Root].
- Cost of CI time lost to reruns [@Ferreira25Cost].
- Cross-project transfer of defect predictors [@Novak24Transfer].
- A benchmark of labelled flaky tests for evaluating predictors [@Iqbal25Benchmark].

### Open Questions

[TODO: confirm access to CI histories beyond the public benchmark]

## References

---
references:
- id: Lindqvist25Flaky
  type: article-journal
  author:
  - family: Lindqvist
    given: E.
  - family: Moyo
    given: T.
  issued:
    year: 2025
  title: "Flaky Failures at Scale: An Analysis of 1.2 Million Continuous-Integration Runs"
  container-title: Journal of Example Software Engineering Studies
  DOI: 10.xxxx/w08-01
- id: Brandt24Rerun
  type: paper-conference
  author:
  - family: Brandt
    given: L.
  issued:
    year: 2024
  title: "Rerun Budgets and the Detection of Flaky Tests"
  container-title: Proceedings of the Example Conference on Software Testing
  DOI: 10.xxxx/w08-02
- id: Okafor23Static
  type: paper-conference
  author:
  - family: Okafor
    given: C.
  - family: Lindgren
    given: P.
  issued:
    year: 2023
  title: "Static Features for Predicting Flaky Tests"
  container-title: Proceedings of the Example Conference on Software Maintenance
  DOI: 10.xxxx/w08-03
- id: Sanz23Vocabulary
  type: paper-conference
  author:
  - family: Sanz
    given: R.
  issued:
    year: 2023
  title: "Vocabulary of Flaky Tests Revisited"
  container-title: Proceedings of the Example Workshop on Test Automation
  DOI: 10.xxxx/w08-04
- id: Wexler22Order
  type: paper-conference
  author:
  - family: Wexler
    given: J.
  - family: Aydin
    given: S.
  issued:
    year: 2022
  title: "Order-Dependent Tests in Large Test Suites"
  container-title: Proceedings of the Example Conference on Software Testing
  DOI: 10.xxxx/w08-05
- id: Hagen24Quarantine
  type: article-journal
  author:
  - family: Hagen
    given: M.
  issued:
    year: 2024
  title: "Quarantine Practices for Flaky Tests in Industrial Pipelines"
  container-title: Journal of Example Software Practice
  DOI: 10.xxxx/w08-06
- id: Moreau23Survey
  type: paper-conference
  author:
  - family: Moreau
    given: A.
  - family: Kaur
    given: N.
  issued:
    year: 2023
  title: "Survey of Developers on Triaging Flaky Failures"
  container-title: Proceedings of the Example Conference on Human Aspects of Software Engineering
  DOI: 10.xxxx/w08-07
- id: Takeda24Root
  type: article-journal
  author:
  - family: Takeda
    given: H.
  issued:
    year: 2024
  title: "Root Causes of Flaky Tests: A Taxonomy"
  container-title: Journal of Example Software Engineering Studies
  DOI: 10.xxxx/w08-08
- id: Ferreira25Cost
  type: paper-conference
  author:
  - family: Ferreira
    given: D.
  issued:
    year: 2025
  title: "Cost of Reruns in Continuous Integration"
  container-title: Proceedings of the Example Conference on Software Engineering in Practice
  DOI: 10.xxxx/w08-09
- id: Novak24Transfer
  type: article-journal
  author:
  - family: Novak
    given: I.
  - family: Petrov
    given: V.
  issued:
    year: 2024
  title: "Transfer of Defect Predictors Across Projects"
  container-title: Journal of Example Empirical Software Engineering
  DOI: 10.xxxx/w08-10
- id: Iqbal25Benchmark
  type: dataset
  author:
  - family: Iqbal
    given: S.
  issued:
    year: 2025
  title: "Benchmark of Labelled Flaky Tests"
  publisher: Example Research Data Repository
  DOI: 10.xxxx/w08-11
---
