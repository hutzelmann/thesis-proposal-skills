# Introduction to the Topic

Continuous integration pipelines lose their value when tests fail for reasons unrelated to the change under test [@Brandt23Flaky].
Developers respond to such flaky failures by re-running builds or ignoring red pipelines, and both responses erode the signal the pipeline exists to give [@Silva24Trust].
How a team escapes that spiral while daily work continues is poorly understood, because published mitigations are evaluated offline, not inside a working team.
This thesis aims to reduce the flaky-test burden of one industrial CI pipeline through staged interventions, and to learn which intervention properties make the reduction stick.

# Contribution to the State-of-the-Art

Research on flaky tests clusters into detection and repair.
Detection work classifies failures as flaky with increasing accuracy, evaluated on mined build histories [@Brandt23Flaky].
Repair and mitigation work proposes quarantine lists and automatic re-runs, evaluated by their effect on build statistics rather than on the team that lives with them [@Silva24Trust].
Both clusters stop at the pipeline and share a limitation: none observes whether developers change their behavior when a mitigation arrives, and behavior is where the spiral starts.
The thesis fills that gap with evidence from inside a team: it improves the context by introducing a staged quarantine-and-triage process into one CI pipeline, such that flaky failures stop blocking unrelated changes, in order to restore the team's trust in a red build.
Answering the questions below matters because mitigations that work in build statistics but not in developer behavior keep being deployed and quietly abandoned.
The deliverable is a report of findings from the intervention cycles, together with the process description the host team keeps.

# Research Focus and Research Questions

The focus is the interaction between a flaky-test mitigation process and the team that operates it, studied while the mitigation is introduced.

1. To what degree does a staged quarantine-and-triage process reduce the share of builds that fail for reasons unrelated to the change under test?
2. Under which conditions do developers resume trusting a red build once quarantine is in place, and which properties of the process do they credit?

# Methodology for Research: Action Research

Action research fits these questions because the first asks for the effect of a change that only exists if the researcher introduces it, and the second for the team's response while it happens — neither is observable in an organisation left unchanged.

## Problem Diagnosis

The host is a single product team of about twenty engineers whose main pipeline fails flaky in a measurable share of runs, tracked by the team's own build dashboard.
Team members describe re-running builds as routine, and the backlog carries flaky-test tickets that have not moved for months — the problem is real to its members, not imported by the researcher.
The agreed scope is the main pipeline of one product; release pipelines and other teams stay out of scope.

## Intervention Cycles

The intervention introduces quarantine with mandatory triage in three plan-act-observe cycles of four weeks each, one escalation step per cycle (RQ1).
Each cycle records the flaky-failure share from build metadata, the quarantine list's size and age, and the re-run behavior of developers before and after the change.
Consent for observing build behavior is obtained from the team before the first cycle, and all recorded developer data is pseudonymised.

## Reflection and Learning

After each cycle, a retrospective with the team reviews the recorded measures against their experience, and the next cycle's plan is adjusted from it (RQ2).
Retrospective records are coded for the process properties developers credit, following established practice for coding reliability [@Weber24Coding].
The researcher's double role — process author and observer — is handled by keeping the measurement plan fixed before each cycle and by having the team lead validate the cycle notes.
What generalises is bounded and stated: the outcome is one team's tested process and the conditions it depended on, an expectation the final cycle can refute rather than confirm.

# Timeline

The thesis starts in March 2027 and is submitted in August 2027.

---
title: Restoring Trust in Continuous Integration under Flaky Tests
subtitle: Master's Thesis Proposal
lang: en
references:
- id: Brandt23Flaky
  type: paper-conference
  author:
  - family: Brandt
    given: J.
  issued:
    year: 2023
  title: Detecting Flaky Test Failures from Build Histories
  container-title: Proceedings of the Example Conference on Software Testing
  DOI: 10.xxxx/xxx30
- id: Silva24Trust
  type: article-journal
  author:
  - family: Silva
    given: R.
  issued:
    year: 2024
  title: Developer Trust in Continuous Integration Signals
  container-title: Journal of Example Software Practice
  DOI: 10.xxxx/xxx31
- id: Weber24Coding
  type: article-journal
  author:
  - family: Weber
    given: L.
  issued:
    year: 2024
  title: Coding Reliability in Qualitative Software Engineering Research
  container-title: Journal of Example Empirical Methods
  DOI: 10.xxxx/xxx32
---
