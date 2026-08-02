# Introduction and Motivation

In-vehicle voice assistants misrecognise commands often enough that recovery, not recognition, dominates the interaction [@Grant22Repair].
When a command fails, the driver must decide whether to repeat it, rephrase it, or abandon the voice channel and reach for the touchscreen.
That decision happens while the driver is steering, so a poor recovery path costs attention rather than merely convenience [@Nakagawa24Glance].
Assistant designers currently choose recovery prompts on intuition, because the literature reports failure rates but not what drivers do next.
This thesis examines both the strategies drivers use after a failed command and the attentional cost those strategies carry.

# Problem Statement and Research Questions

The research focus lies on how drivers recover from failed voice commands in a moving vehicle and what that recovery costs in visual attention.

1. Which repair strategies do drivers employ after an in-vehicle voice command fails, and how do those strategies relate to the type of failure?
2. To what degree does the choice of repair strategy affect total off-road glance time during the recovery episode?
3. To what degree do the strategies drivers report as preferable coincide with the strategies that minimise measured glance time?

# Related Work

Conversational repair has been studied extensively for smart speakers, where visual attention is free and abandoning the interaction is cheap [@Grant22Repair].
Driving studies measure glance behaviour during voice interaction but treat a failed command as a single undifferentiated event [@Nakagawa24Glance].
@Oyelaran25Prompts compare recovery prompt wordings through preference ratings, without observing what drivers actually do or measuring the resulting glance load.
This thesis links the two levels: it describes the repair strategies drivers employ and measures the glance cost each strategy incurs, so that prompt design can be grounded in observed behaviour rather than stated preference.
Neither strand alone can produce that link, since the strategy space is not known in advance and the attentional cost is not observable through interviews.
Repair taxonomies from conversation analysis transfer only partly to voice interfaces, where the machine cannot signal partial understanding [@Ferreira22Repair].
@Kaur25Glance report that glance duration during voice interaction is dominated by recovery rather than by the initial command.
Mixed-methods integration is itself a methodological literature with documented designs and failure modes [@Delgado23Integration], and reflexive thematic analysis provides the coding procedure used here [@Lindqvist21Coding].
Stated preference and measured behaviour diverge systematically in interface evaluation, which is the divergence the third research question targets [@Aranda24Preference].
Whether participants recognise scripted failures as artificial has been tested directly, with recognition rates low enough to keep the manipulation usable [@Novak25Scripted].
Established procedures cover consent and data handling for simulator studies that record video and gaze [@Beck23Ethics].

# Methodology: Mixed Methods

## Use Case Definition

The object of study is a commercially available in-vehicle voice assistant, exercised on a fixed simulator route with scripted recognition failures injected at controlled points.
This use case suits the research questions because scripted failures make the recovery episode observable at a known moment, which naturally occurring failures do not.
The simulator and eye tracker are available in the laboratory; the study covers German-language commands only and excludes hands-free phone calls.

## Qualitative Strand

Twenty-four participants drive a fixed-base simulator route during which scripted recognition failures are injected at controlled points, and each session closes with a retrospective interview over the recorded video.
Recordings are transcribed and analysed with reflexive thematic analysis to build an inductive taxonomy of repair strategies (RQ1).
Two researchers code a shared subset independently, disagreements are resolved through discussion, and inter-rater agreement is reported for the final coding scheme.
Participation is voluntary and consented, video is pseudonymized at ingest, and the study runs under an approved ethics protocol.

## Quantitative Strand

The same sessions supply eye-tracking data, from which total off-road glance time is computed for every recovery episode.
A within-subjects comparison across failure types, with episodes nested in participants, forms the quantitative design; the target sample follows a power analysis for a medium within-subjects effect.
A mixed-effects model regresses glance time on the repair strategy assigned by the qualitative coding, with participant as a random intercept (RQ2).
The post-session questionnaire additionally records which recovery path each participant would prefer in future, on a forced-choice scale.

## Integration

The strands run concurrently over one data collection and integrate at the analysis stage: the taxonomy from the qualitative strand supplies the categorical predictor that the quantitative model consumes, which is why neither strand can be dropped.
Comparing the preference ranking from the questionnaire against the glance-time ranking from the model answers the third research question and exposes where stated preference and measured cost diverge (RQ3).
Divergences are taken back to the interview transcripts to check whether participants articulated a reason, and the final account reports agreement and disagreement between the strands rather than privileging either.

# Objectives

The primary objective is to link the repair strategies drivers use after a failed voice command to the visual attention those strategies cost.

Supporting objectives:

- Build an inductive taxonomy of repair strategies from think-aloud and retrospective interview data.
- Measure off-road glance time for every recovery episode.
- Model glance time as a function of the coded repair strategy.
- Compare stated preference against measured glance cost.

# Expected Contributions and Results

The scientific contribution is an evidence-based link between an observed repair-strategy taxonomy and its attentional cost, which neither conversation-analytic nor glance-based work currently provides.
The practical contribution is a set of prompt-design recommendations grounded in what drivers do rather than in what they say they prefer.
It is expected that repeating a command verbatim is the most common strategy and among the most expensive, and that stated preference favours strategies that measure poorly.
Limitations are foreseeable: a simulator rather than the road, one assistant, one language, and scripted failures that may be recognised as artificial by some participants.

# Work Plan and Schedule

| Task | Weeks |
|---|---|
| Literature and study design | 1-5 |
| Ethics approval | 3-7 |
| Simulator and eye-tracker setup | 5-9 |
| Pilot sessions and refinement | 8-10 |
| Data collection | 10-16 |
| Qualitative coding | 13-20 |
| Quantitative modelling and integration | 18-22 |
| Writing and revision | 19-24 |

Data collection cannot start before ethics approval, which sets the critical path for the whole project.
Coding overlaps collection so that the taxonomy is stable before the quantitative model consumes it, since the model needs the coded strategy as its predictor.
Integration is scheduled last by design, because it is the step that requires both strands to be complete.

---
title: Repair Strategies After Failed In-Vehicle Voice Commands
author: Jane Doe
subtitle: "Master's Thesis Proposal"
lang: en
references:
- id: Grant22Repair
  type: paper-conference
  author:
  - family: Grant
    given: A.
  issued:
    year: 2022
  title: Repair Sequences in Conversational Agent Interaction
  container-title: Proceedings of the Example Conference on Conversational Interfaces
  DOI: 10.xxxx/xxx80
- id: Nakagawa24Glance
  type: article-journal
  author:
  - family: Nakagawa
    given: H.
  issued:
    year: 2024
  title: Glance Behaviour During In-Vehicle Voice Interaction
  container-title: Journal of Example Human Factors and Systems
  DOI: 10.xxxx/xxx81
- id: Oyelaran25Prompts
  type: paper-conference
  author:
  - family: Oyelaran
    given: F.
  issued:
    year: 2025
  title: Prompt Wording for Error Recovery in Voice Assistants
  container-title: Proceedings of the Example Conference on Automotive Interfaces
  DOI: 10.xxxx/xxx82
- id: Ferreira22Repair
  type: article-journal
  author:
  - family: Ferreira
    given: J.
  issued:
    year: 2022
  title: Repair Taxonomies Beyond Human Conversation
  container-title: Example Journal of Conversational Interaction
  DOI: 10.xxxx/xx91
- id: Kaur25Glance
  type: paper-conference
  author:
  - family: Kaur
    given: S.
  issued:
    year: 2025
  title: Recovery Dominates Glance Time in Voice Interaction
  container-title: Proceedings of the Example Conference on Automotive Interfaces
  DOI: 10.xxxx/xx92
- id: Delgado23Integration
  type: article-journal
  author:
  - family: Delgado
    given: R.
  issued:
    year: 2023
  title: Integration Designs and Failure Modes in Mixed Methods Research
  container-title: Example Journal of Research Methods
  DOI: 10.xxxx/xx93
- id: Lindqvist21Coding
  type: article-journal
  author:
  - family: Lindqvist
    given: M.
  issued:
    year: 2021
  title: Reflexive Thematic Analysis in Interaction Research
  container-title: Example Journal of Qualitative Methods
  DOI: 10.xxxx/xx94
- id: Aranda24Preference
  type: article-journal
  author:
  - family: Aranda
    given: P.
  issued:
    year: 2024
  title: Stated Preference Versus Measured Behaviour in Interface Evaluation
  container-title: Journal of Example Human Factors and Systems
  DOI: 10.xxxx/xx95
- id: Beck23Ethics
  type: article-journal
  author:
  - family: Beck
    given: A.
  issued:
    year: 2023
  title: Consent and Data Handling in Simulator Studies
  container-title: Example Journal of Research Ethics
  DOI: 10.xxxx/xx96
- id: Novak25Scripted
  type: paper-conference
  author:
  - family: Novak
    given: T.
  issued:
    year: 2025
  title: Do Participants Notice Scripted Recognition Failures?
  container-title: Proceedings of the Example Symposium on Human Factors
  DOI: 10.xxxx/xx97
---
