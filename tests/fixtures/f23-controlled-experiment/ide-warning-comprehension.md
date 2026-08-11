# Introduction to the Topic

Static analysis warnings are a standard part of modern development environments, yet developers routinely dismiss them without reading [@Vogel24Warning].
When a true positive is dismissed alongside the noise, the defect it pointed at survives into production.
How a warning is explained to the developer may decide whether it is read at all [@Sato25Explanations].
This thesis aims to determine to what degree the explanation style of static analysis warnings changes whether developers correctly act on them.

# Contribution to the State-of-the-Art

Research on warning usability falls into two clusters.
Studies of warning triage measure how many warnings developers resolve, but treat the warning text as fixed and vary only prioritization [@Vogel24Warning].
Studies of explanation generation produce richer warning texts, evaluated so far by author judgement or text metrics rather than by developer behavior [@Sato25Explanations; @Kim26Generating].
Both clusters share a limitation: neither measures whether a different explanation changes what a developer actually does with the same defect.
The thesis fills that gap with behavioral evidence: a controlled comparison of explanation styles on identical defects, measuring correct resolutions rather than stated preference.
Answering this matters beyond the gap because explanation style is one of the few warning properties a tool vendor can change without touching the analysis itself.
The deliverable is an evaluation of explanation styles, together with the annotated task set it is measured on.

# Research Focus and Research Questions

The focus is the causal effect of warning explanation style on developer comprehension and resolution behavior, isolated from the underlying analysis quality.

1. To what degree does the explanation style of a static analysis warning affect whether developers resolve the underlying defect correctly?
2. Under which conditions does a longer explanation reduce rather than improve resolution correctness?

# Methodology for Research: Controlled Experiment

A controlled experiment fits these questions because both ask for a causal effect of one manipulated property — explanation style — on measurable developer behavior, which observation alone cannot isolate.

## Hypotheses and Variables

The null hypothesis states that explanation style has no effect on resolution correctness; the alternative states that at least one style differs.
Explanation style is the single independent variable, manipulated across three treatments: the analyzer's original message, a rule-documentation excerpt, and a defect-specific explanation.
The dependent variables are resolution correctness against a predefined fix rubric and time to resolution.
Known confounding factors are programming experience and prior exposure to the analyzer; both are recorded in a pre-questionnaire.

## Design and Participants

The experiment uses a within-subjects design: every participant sees all three styles across nine seeded defects, with style-to-defect assignment counterbalanced by a Latin square (RQ1).
Participants are computer science students recruited from lab courses, assigned to sequence groups at random.
Each session uses the same instrumented editor, and task order is fixed so that only the explanation style varies.

## Statistical Analysis

Resolution correctness is compared across styles with a repeated-measures analysis matching the within-subjects design, at a significance level of 0.05 (RQ1).
The interaction between explanation length and resolution correctness is examined to identify conditions where longer explanations hurt (RQ2).
The main threats are the seeded defects not representing real warning diversity and student participants limiting generalization to professionals; both are stated as limitations.
It is expected that defect-specific explanations improve correctness; the experiment can refute this.

# Timeline

The thesis starts in April 2027 and is submitted in September 2027.

---
title: Effects of Warning Explanation Style on Defect Resolution
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Vogel24Warning
  type: paper-conference
  author:
  - family: Vogel
    given: T.
  issued:
    year: 2024
  title: Warning Triage Behavior in Continuous Integration
  container-title: Proceedings of the Example Conference on Software Engineering
  DOI: 10.xxxx/xxxx7
- id: Sato25Explanations
  type: article-journal
  author:
  - family: Sato
    given: M.
  issued:
    year: 2025
  title: Explanations for Static Analysis Findings
  container-title: Journal of Empirical Software Engineering Examples
  DOI: 10.xxxx/xxxx8
- id: Kim26Generating
  type: paper-conference
  author:
  - family: Kim
    given: H.
  issued:
    year: 2026
  title: Generating Contextual Warning Messages from Code Change History
  container-title: Proceedings of the Example Conference on Developer Tools
  DOI: 10.xxxx/xxxx9
---
