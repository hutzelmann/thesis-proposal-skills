
# Introduction and Motivation

Conditionally automated vehicles drive without supervision until the system reaches the limits of its operating conditions and hands control back to the driver [@Du20Evaluating].
The interval between that request and the moment the driver must act determines whether the handover succeeds.
Manufacturers set this lead time to a fixed value, even though drivers differ widely in how quickly they disengage from a non-driving task [@Ou21Effects].
Too short an interval produces rushed and erratic manoeuvres, while too long an interval invites drivers to ignore the request altogether.
This thesis examines how lead time and request modality jointly shape takeover quality.

# Problem Statement and Research Questions

The research focus lies on the joint effect of takeover lead time and request modality on the criticality of the manoeuvre a driver performs after resuming control.

1. To what degree does takeover lead time affect the criticality of the resulting manoeuvre in a conditionally automated driving scenario?
2. Under which request modalities does a shortened lead time degrade manoeuvre criticality most strongly?
3. To what degree does reaction time predict manoeuvre criticality across the tested lead-time and modality combinations?

# Related Work

Existing studies vary lead time and report reaction times aggregated over all participants [@Du20Evaluating].
Modality comparisons between auditory, visual, and haptic requests exist, but they hold lead time constant [@Ou21Effects].
@Yang23Assessing combine both factors, yet evaluate takeover quality only through reaction time rather than through the resulting vehicle trajectory.
This thesis contributes a factorial evaluation in which lead time and modality vary together and takeover quality is measured through trajectory-based criticality rather than reaction time alone.
The resulting evidence indicates which combinations degrade manoeuvre quality even when reaction times look acceptable.

# Methodology: Controlled Experiment

The study follows a within-subjects design yielding nine conditions in counterbalanced order.
Its first hypothesis states that shorter lead times increase manoeuvre criticality; the second states that this increase differs across modalities.

## Use Case Definition

The object of study is a motorway roadworks approach in a fixed-base driving simulator, the situation in which series systems most often reach their operating limit.
This use case suits the research questions because it produces a genuine takeover need at a moment the experimenter controls, which on-road studies cannot arrange safely.
The simulator is available in the laboratory; motion cueing is absent, which is known to affect steering amplitude and bounds the transfer of the criticality values.

## Independent Variables

Takeover lead time is manipulated at three levels: four, seven, and ten seconds between the request and the point of no return.
Request modality is manipulated at three levels: auditory only, visual only, and combined auditory-visual.
The two factors are crossed fully, and condition order is counterbalanced across participants with a balanced Latin square.

## Dependent Variables

The primary dependent variable is a trajectory-based criticality measure computed over the ten seconds following the request, expressed as the minimum time-to-collision in seconds.
Reaction time, in milliseconds from request onset to first steering or pedal input, is recorded as a secondary measure.
Perceived urgency is captured after every condition on a seven-point Likert scale.

## Procedure

Each participant completes a familiarisation drive and then the nine experimental conditions in a fixed-base driving simulator.
During automated driving the participant works on a standardized visual non-driving task on a tablet, which is interrupted when the takeover request fires.
The simulator logs steering, pedal input, and vehicle trajectory continuously, and a short questionnaire after every condition records perceived urgency.

## Statistical Analysis

A repeated-measures analysis of variance over the criticality measure tests the main effect of lead time (RQ1).
The interaction term of the same model, followed by planned contrasts with Holm correction for multiple comparisons, identifies the modalities under which shortened lead time hurts most (RQ2).
A mixed-effects regression of criticality on reaction time, with participant as a random intercept, quantifies how well reaction time predicts manoeuvre quality (RQ3).
A power analysis for a medium within-subjects effect at the conventional significance level sets the target sample at 36 licence holders with at least two years of driving experience.
Participants give informed consent before the session, driving data is pseudonymized at recording time, and the study runs under an approved ethics protocol with the option to stop at any point.

# Objectives

The primary objective is to measure how takeover lead time and request modality jointly affect the criticality of the manoeuvre a driver performs after resuming control.

Supporting objectives:

- Implement a motorway roadworks scenario with a controllable takeover moment.
- Instrument the simulator to log trajectory, reaction time, and perceived urgency per condition.
- Analyse the factorial design with a pre-specified statistical plan.
- Compare trajectory-based criticality against reaction time as an outcome measure.

# Expected Contributions and Results

The scientific contribution is factorial evidence on lead time and modality measured through vehicle trajectory rather than reaction time alone, which existing studies do not provide.
The practical contribution is a recommendation on the minimum viable lead time per modality for series takeover requests.
It is expected that criticality rises sharply below seven seconds, that the combined modality mitigates part of that rise, and that reaction time predicts criticality only weakly.
Limitations are foreseeable: a fixed-base simulator without motion cueing, one traffic scenario, and a sample of experienced drivers that under-represents novices.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Literature and design specification | 1-4 |
| Ethics approval | 3-7 |
| Scenario and instrumentation build | 5-10 |
| Pilot sessions | 9-11 |
| Data collection | 11-17 |
| Statistical analysis | 16-20 |
| Writing and revision | 18-24 |

Data collection cannot begin before ethics approval, which sets the critical path.
The pilot deliberately precedes collection because the counterbalancing cannot change once the first participant has run.
Four weeks of overlap between analysis and writing absorb feedback rounds.

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
