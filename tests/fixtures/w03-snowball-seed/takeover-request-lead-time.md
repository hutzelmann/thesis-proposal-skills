# Introduction to the Topic

Conditionally automated vehicles drive without supervision until the system reaches the limits of its operating conditions and hands control back to the driver [@Du20Evaluating].
The interval between that request and the moment the driver must act determines whether the handover succeeds.
Manufacturers set this lead time to a fixed value, even though drivers differ widely in how quickly they disengage from a non-driving task [@Ou21Effects].
Too short an interval produces rushed and erratic manoeuvres, while too long an interval invites drivers to ignore the request altogether.
This thesis examines how lead time and request modality jointly shape takeover quality.

# Contribution to the State-of-the-Art

Existing studies vary lead time and report reaction times aggregated over all participants [@Du20Evaluating].
Modality comparisons between auditory, visual, and haptic requests exist, but they hold lead time constant [@Ou21Effects].
@Yang23Assessing combine both factors, yet evaluate takeover quality only through reaction time rather than through the resulting vehicle trajectory.
This thesis contributes a factorial evaluation in which lead time and modality vary together and takeover quality is measured through trajectory-based criticality rather than reaction time alone.
The resulting evidence indicates which combinations degrade manoeuvre quality even when reaction times look acceptable.

# Research Focus and Research Questions

The research focus lies on the joint effect of takeover lead time and request modality on the criticality of the manoeuvre a driver performs after resuming control.

1. To what degree does takeover lead time affect the criticality of the resulting manoeuvre in a conditionally automated driving scenario?
2. Under which request modalities does a shortened lead time degrade manoeuvre criticality most strongly?
3. To what degree does reaction time predict manoeuvre criticality across the tested lead-time and modality combinations?

# Methodology for Research: Controlled Experiment

## Design and Hypotheses

The study follows a within-subjects design with lead time at three levels and request modality at three levels, yielding nine conditions presented in a counterbalanced order.
The dependent variable is a trajectory-based criticality measure computed over the ten seconds following the request; reaction time is recorded as a secondary measure.
The first hypothesis states that shorter lead times increase manoeuvre criticality, and the second states that this increase differs across modalities.
A power analysis for a medium within-subjects effect at the conventional significance level indicates a target sample of 36 participants, recruited among licence holders with at least two years of driving experience.
Participants give informed consent before the session, driving data is pseudonymized at recording time, and the study runs under an approved ethics protocol with the option to stop at any point.

## Procedure

Each participant completes a familiarisation drive and then the nine experimental conditions in a fixed-base driving simulator.
During automated driving the participant works on a standardized visual non-driving task on a tablet, which is interrupted when the takeover request fires.
The simulator logs steering, pedal input, and vehicle trajectory continuously, and a short questionnaire after every condition records perceived urgency.

## Statistical Analysis

A repeated-measures analysis of variance over the criticality measure tests the main effect of lead time (RQ1).
The interaction term of the same model, followed by planned contrasts with Holm correction for multiple comparisons, identifies the modalities under which shortened lead time hurts most (RQ2).
A mixed-effects regression of criticality on reaction time, with participant as a random intercept, quantifies how well reaction time predicts manoeuvre quality (RQ3).

---
title: Lead Time and Modality of Takeover Requests in Conditionally Automated Driving
author: Erika Musterfrau
subtitle: "Bachelor's Thesis Proposal"
lang: en
references:
- id: Du20Evaluating
  type: paper-conference
  author:
  - family: Du
    given: N.
  issued:
    year: 2020
  title: "Evaluating Effects of Cognitive Load, Takeover Request Lead Time, and Traffic Density on Drivers' Takeover Performance in Conditionally Automated Driving"
  container-title: 12th International Conference on Automotive User Interfaces and Interactive Vehicular Applications
  DOI: 10.1145/3409120.3410666
- id: Ou21Effects
  type: article-journal
  author:
  - family: Ou
    given: Y.
  issued:
    year: 2021
  title: Effects of different takeover request interfaces on takeover behavior and performance during conditionally automated driving
  container-title: Accident Analysis & Prevention
  DOI: 10.1016/j.aap.2021.106425
- id: Yang23Assessing
  type: article-journal
  author:
  - family: Yang
    given: S.
  issued:
    year: 2023
  title: "Assessing the Effects of Modalities of Takeover Request, Lead Time of Takeover Request, and Traffic Conditions on Takeover Performance in Conditionally Automated Driving"
  container-title: Sustainability
  DOI: 10.3390/su15097270
---
