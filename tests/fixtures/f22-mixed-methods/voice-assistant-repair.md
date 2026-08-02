# Introduction to the Topic

In-vehicle voice assistants misrecognise commands often enough that recovery, not recognition, dominates the interaction [@Grant22Repair].
When a command fails, the driver must decide whether to repeat it, rephrase it, or abandon the voice channel and reach for the touchscreen.
That decision happens while the driver is steering, so a poor recovery path costs attention rather than merely convenience [@Nakagawa24Glance].
Assistant designers currently choose recovery prompts on intuition, because the literature reports failure rates but not what drivers do next.
This thesis examines both the strategies drivers use after a failed command and the attentional cost those strategies carry.

# Contribution to the State-of-the-Art

Conversational repair has been studied extensively for smart speakers, where visual attention is free and abandoning the interaction is cheap [@Grant22Repair].
Driving studies measure glance behaviour during voice interaction but treat a failed command as a single undifferentiated event [@Nakagawa24Glance].
@Oyelaran25Prompts compare recovery prompt wordings through preference ratings, without observing what drivers actually do or measuring the resulting glance load.
This thesis links the two levels: it describes the repair strategies drivers employ and measures the glance cost each strategy incurs, so that prompt design can be grounded in observed behaviour rather than stated preference.
Neither strand alone can produce that link, since the strategy space is not known in advance and the attentional cost is not observable through interviews.

# Research Focus and Research Questions

The research focus lies on how drivers recover from failed voice commands in a moving vehicle and what that recovery costs in visual attention.

1. Which repair strategies do drivers employ after an in-vehicle voice command fails, and how do those strategies relate to the type of failure?
2. To what degree does the choice of repair strategy affect total off-road glance time during the recovery episode?
3. To what degree do the strategies drivers report as preferable coincide with the strategies that minimise measured glance time?

# Methodology for Research: Mixed Methods

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
---
