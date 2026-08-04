# Introduction to the Topic

Machine learning models deployed in production operate in non-stationary environments, where the statistical relationship between input features and the target variable changes over time, a phenomenon known as concept drift [@Krempl14Open].
This drift can manifest in different forms, ranging from abrupt to gradual shifts in the joint distribution of inputs and targets [@Webb18Analyzi].
Left undetected, concept drift silently degrades a model's predictive performance and erodes the value of the automated decisions built on it [@Hoens12Learnin].
In many practical settings, the true label needed to measure performance directly is not available immediately, but only after a substantial delay.
A customer churn prediction model is a representative example, since whether a customer actually churns only becomes observable weeks or months after the model produces a prediction.
During this delay, practitioners commonly rely on unsupervised drift-detection signals, statistical measures of how much the input or prediction distribution has shifted, as an early proxy for performance loss, since true performance cannot yet be computed [@Klaise20Monitor].
These signals are frequently decoupled from the actual severity of performance decay: they can fire on harmless distribution shifts as readily as on shifts that genuinely degrade the model, which produces frequent, low-value alerts and erodes practitioners' trust in the monitoring system.
This thesis studies whether unsupervised drift-detection signals, once evaluated against the delayed ground-truth labels that eventually arrive, actually predict the performance decay they are meant to warn about.

# Contribution to the State-of-the-Art

Existing work on concept-drift detection under delayed or absent labels falls into two largely separate strands.
The first strand designs unsupervised drift detectors that operate without any labels at prediction time, using signals such as margin density [@Sethi15Don; @Sethi17Reliabl], statistical process control on distributional statistics [@Tan25Flexibl], the gradient of the model's log-likelihood [@Zhang23Concept], or approaches that distinguish input-space from target-concept drift under scarcely labeled or fully unlabeled data [@Lughofer16Recogni].
Existing studies commonly evaluate these detectors against each other on synthetic or benchmark streams using detection-timing and accuracy metrics [@Goncalves14Compara; @Cerqueira26Framewo], and one specific line of work incorporates lagged labels directly into a drift-detection ensemble once they become available [@Xu21Concept].
The second strand estimates model accuracy without any labels at all, for instance by measuring agreement between multiple models on unlabeled data [@Woo25Classif].
Related work compares the accuracy-energy trade-off of several drift detectors under controlled conditions [@Omar24How], and discusses when accumulated monitoring evidence should trigger retraining [@Holt22When].
What this body of work has in common is that it evaluates drift detectors on their internal detection quality, how well they flag a change relative to a known ground-truth drift point, rather than on whether their alerts correspond to a real, measurable drop in downstream performance once labels eventually arrive.
This thesis closes that loop: it evaluates unsupervised drift-detection signals against the realized performance decay measured once delayed labels become available, and studies whether alert thresholds can be calibrated against this delayed ground truth to reduce false alarms without missing genuine degradation.

# Research Focus and Research Questions

The thesis focuses on the empirical validity of unsupervised drift-detection signals as an early-warning proxy for real performance decay under delayed ground-truth labels, using public streaming and tabular datasets with an artificially simulated label delay to approximate settings such as customer churn prediction where company data cannot be used.

1. To what degree do unsupervised drift-detection signals correlate with the performance decay measured once delayed ground-truth labels become available, across different families of signals and different types of concept drift?
2. To what extent can drift-alert thresholds calibrated against historical delayed-label outcomes reduce the false-positive alert rate without missing genuine performance degradation, compared to existing label-less drift detectors designed for false-positive control [@Tan25Flexibl]?
3. How does the length of the label delay affect the reliability of unsupervised drift-detection signals as an early-warning proxy for performance decay?

# Methodology for Research: Prototype Implementation

## Previous Work

The prototype builds on open-source streaming machine learning libraries that provide reference implementations of classifiers and unsupervised drift detectors, including margin-density-based [@Sethi17Reliabl] and statistical-process-control-based [@Tan25Flexibl] detectors.
It further draws on the drift-simulation and evaluation protocol of Cerqueira et al., which injects controlled distributional changes into real-world datasets and derives timing-aware detection metrics [@Cerqueira26Framewo].
[TODO: name the specific streaming ML library/libraries chosen, e.g. River]

## Requirements

The prototype must compute a representative set of unsupervised drift-detection signals at prediction time on a streaming dataset, without access to the true label.
It must simulate a configurable label delay, releasing the true label for each prediction only after a fixed or distributed number of subsequent time steps.
Once labels are released, the prototype must compute the realized performance decay of the underlying classifier, to serve as ground truth against which the drift signals are evaluated.
The prototype must also support threshold calibration against historical delayed-label outcomes, to compare a calibrated policy against an uncalibrated baseline and against existing label-less false-positive-controlled detectors [@Tan25Flexibl].
Real-time or production-grade deployment of the prototype is neglectable, since the goal is retrospective evaluation rather than a deployable monitoring system.
Exhaustive coverage of every published drift-detection method is neglectable as well; the prototype instead implements a representative sample spanning distributional-distance-based, margin-density-based, and score-based signal families.
[TODO: finalize which drift-detection methods form the representative sample]

## Evaluation

The evaluation runs the prototype on public datasets that admit a streaming replay with a simulated label delay.
[TODO: select specific dataset(s), e.g. streaming concept-drift benchmarks or a public churn-style tabular dataset replayed as a stream]
The first analysis measures the statistical correlation between each drift signal and the realized performance decay across drift types and signal families (RQ1).
A second analysis compares the false-positive alert rate and the missed-degradation rate of calibrated thresholds against an uncalibrated baseline and against the false-positive-controlled detector of @Tan25Flexibl (RQ2).
A third analysis varies the simulated label-delay length and measures how the correlation and calibration results change as the delay grows (RQ3).
[TODO: define the precise operationalization of "performance decay" — accuracy, calibration error, or a business-relevant metric]

# Timeline

The thesis starts as soon as the supervisor signs off on the proposal, with [TODO: state target submission month] as the submission month.

<!-- markdownlint-disable -->

---
title: "Closing the Loop: Evaluating the Validity of Unsupervised Drift Alerts Against Delayed-Label Performance Decay"
subtitle: "Master's Thesis Proposal"
lang: en
references:
  - id: Xu21Concept
    type: paper-conference
    author:
      - family: Xu
        given: Yiming
      - family: Klabjan
        given: Diego
    issued:
      year: 2021
    title: Concept Drift and Covariate Shift Detection Ensemble with Lagged Labels
    container-title: 2021 IEEE International Conference on Big Data (Big Data)
    DOI: 10.1109/bigdata52589.2021.9671279
  - id: Tan25Flexibl
    type: paper-conference
    author:
      - family: Tan
        given: Nelvin
      - family: Shih
        given: Yu-Ching
      - family: Yang
        given: Dong
      - family: Salunkhe
        given: Amol
    issued:
      year: 2025
    title: Flexible and Efficient Drift Detection Without Labels
    container-title: 2025 IEEE International Conference on Data Mining Workshops (ICDMW)
    DOI: 10.1109/icdmw69685.2025.00037
  - id: Woo25Classif
    type: article-journal
    author:
      - family: Woo
        given: Erin
      - family: Jun
        given: Hyungkook
      - family: Yeo
        given: Sangyeop
      - family: Eom
        given: YoungIk
      - family: Ma
        given: YuSeung
    issued:
      year: 2025
    title: Classification Accuracy Estimation Without Labels via Architecture-Agnostic Model Agreement
    DOI: 10.21203/rs.3.rs-7331038/v1
  - id: Omar24How
    type: paper-conference
    author:
      - family: Omar
        given: Rafiullah
      - family: Bogner
        given: Justus
      - family: Leest
        given: Joran
      - family: Stoico
        given: Vincenzo
      - family: Lago
        given: Patricia
      - family: Muccini
        given: Henry
    issued:
      year: 2024
    title: How to Sustainably Monitor ML-Enabled Systems? Accuracy and Energy Efficiency Tradeoffs in Concept Drift Detection
    container-title: 2024 10th International Conference on ICT for Sustainability (ICT4S)
    DOI: 10.1109/ict4s64576.2024.00026
  - id: Holt22When
    type: paper-conference
    author:
      - family: Holt
        given: James
    issued:
      year: 2022
    title: "When to retrain? assessing production ML model performance using uncertainty, out-of-distribution detection, and concept drift detection"
    container-title: Disruptive Technologies in Information Sciences VI
    DOI: 10.1117/12.2618321
  - id: Sethi17Reliabl
    type: article-journal
    author:
      - family: Sethi
        given: Tegjyot Singh
      - family: Kantardzic
        given: Mehmed
    issued:
      year: 2017
    title: On the reliable detection of concept drift from streaming unlabeled data
    container-title: Expert Systems with Applications
    DOI: 10.1016/j.eswa.2017.04.008
  - id: Sethi15Don
    type: article-journal
    author:
      - family: Sethi
        given: Tegjyot Singh
      - family: Kantardzic
        given: Mehmed
    issued:
      year: 2015
    title: "Don't Pay for Validation: Detecting Drifts from Unlabeled Data Using Margin Density"
    container-title: Procedia Computer Science
    DOI: 10.1016/j.procs.2015.07.284
  - id: Zhang23Concept
    type: article-journal
    author:
      - family: Zhang
        given: Kungang
      - family: Bui
        given: Alex
      - family: Apley
        given: Daniel
    issued:
      year: 2023
    title: Concept Drift Monitoring and Diagnostics of Supervised Learning Models via Score Vectors
    container-title: Technometrics
    DOI: 10.1080/00401706.2022.2124310
  - id: Cerqueira26Framewo
    type: article
    author:
      - family: Cerqueira
        given: Vitor
      - family: Gomes
        given: Heitor Murilo
      - family: Heyden
        given: Marco
      - family: Pfahringer
        given: Bernhard
      - family: Bifet
        given: Albert
    issued:
      year: 2026
    title: A Framework for Evaluating and Benchmarking Concept Drift Detection Methods
    URL: "http://arxiv.org/abs/2606.07789v1"
  - id: Goncalves14Compara
    type: article-journal
    author:
      - family: Gonçalves
        given: Paulo M.
      - family: Santos
        given: Silas G. T. C.
      - family: Barros
        given: Roberto S. M.
      - family: Vieira
        given: Davi C. L.
    issued:
      year: 2014
    title: A comparative study on concept drift detectors
    container-title: Expert Systems with Applications
    DOI: 10.1016/j.eswa.2014.07.019
  - id: Lughofer16Recogni
    type: article-journal
    author:
      - family: Lughofer
        given: Edwin
      - family: Weigl
        given: Eva
      - family: Heidl
        given: Wolfgang
      - family: Eitzinger
        given: Christian
      - family: Radauer
        given: Thomas
    issued:
      year: 2016
    title: Recognizing input space and target concept drifts in data streams with scarcely labeled and unlabelled instances
    container-title: Information Sciences
    DOI: 10.1016/j.ins.2016.03.034
  - id: Webb18Analyzi
    type: article-journal
    author:
      - family: Webb
        given: Geoffrey I.
      - family: Lee
        given: Loong Kuan
      - family: Goethals
        given: Bart
      - family: Petitjean
        given: François
    issued:
      year: 2018
    title: Analyzing concept drift and shift from sample data
    container-title: Data Mining and Knowledge Discovery
    DOI: 10.1007/s10618-018-0554-1
  - id: Krempl14Open
    type: article-journal
    author:
      - family: Krempl
        given: Georg
      - family: Žliobaitė
        given: Indrė
      - family: Brzeziński
        given: Dariusz
      - family: Hüllermeier
        given: Eyke
      - family: Last
        given: Mark
      - family: Lemaire
        given: Vincent
      - family: Noack
        given: Tino
      - family: Shaker
        given: Ammar
      - family: Sievi
        given: Sonja
      - family: Spiliopoulou
        given: Myra
      - family: Stefanowski
        given: Jerzy
    issued:
      year: 2014
    title: Open challenges for data stream mining research
    container-title: ACM SIGKDD Explorations Newsletter
    DOI: 10.1145/2674026.2674028
  - id: Hoens12Learnin
    type: article-journal
    author:
      - family: Hoens
        given: T. Ryan
      - family: Polikar
        given: Robi
      - family: Chawla
        given: Nitesh V.
    issued:
      year: 2012
    title: "Learning from streaming data with concept drift and imbalance: an overview"
    container-title: Progress in Artificial Intelligence
    DOI: 10.1007/s13748-011-0008-0
  - id: Klaise20Monitor
    type: article
    author:
      - family: Klaise
        given: Janis
      - family: Van Looveren
        given: Arnaud
      - family: Cox
        given: Clive
      - family: Vacanti
        given: Giovanni
      - family: Coca
        given: Alexandru
    issued:
      year: 2020
    title: Monitoring and explainability of models in production
    URL: "http://arxiv.org/abs/2007.06299v1"
---
