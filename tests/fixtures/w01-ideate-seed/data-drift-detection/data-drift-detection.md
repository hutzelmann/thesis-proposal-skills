# Detecting Data Drift in Deployed Machine Learning Pipelines

*[TODO: confirm degree level]*

## Idea Notes

Working title: Detecting Data Drift in Deployed Machine Learning Pipelines.

### Problem Sketch

Production machine learning models degrade silently when the input distribution shifts away from the training data.
Teams typically notice the degradation only after downstream business metrics drop, which can take weeks.
Existing monitoring dashboards surface raw statistics but leave the decision when to retrain to intuition.
The idea is to ground that retraining decision in an explicit, evaluated drift-severity signal.

### Candidate Research-Question Directions

These are candidate directions, not final research questions:

- To what degree do statistical drift scores correlate with actual accuracy loss once delayed labels arrive?
- Under which conditions do lightweight detectors match the sensitivity of full shadow-retraining experiments?
- How do alerting thresholds trade off between false alarms and missed degradations in long-running pipelines?

### Literature Anchors

Nakamura et al. survey drift detectors for streaming settings and note that evaluations rarely use production traces [@Nakamura24Drift].
That gap — synthetic benchmarks everywhere, production evidence nowhere — is where the thesis could differentiate itself.

### Open Questions

[TODO: decide between prototype implementation and systematic literature review]
[TODO: find a second production-trace dataset for grounding]

## References

---
references:
- id: Nakamura24Drift
  type: paper-conference
  author:
  - family: Nakamura
    given: K.
  - family: Silva
    given: R.
  issued:
    year: 2024
  title: "Drift Detection for Streaming Machine Learning: A Survey of Evaluation Practice"
  container-title: Proceedings of the Example Conference on Data Stream Mining
  DOI: 10.1145/3611643.3616310
---
