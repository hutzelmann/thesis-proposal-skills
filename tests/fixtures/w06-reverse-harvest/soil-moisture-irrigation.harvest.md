# Harvest record — soil-moisture irrigation scheduling

Synthetic — every sentence, name and reference below is invented. What is taken
from real theses is structure only, generalized from three of them across
computer science: an empirical software-engineering study, an artefact-building
thesis, and an evaluation study. Their common properties are what this record
reproduces — aim and objectives stated before the research questions, a
justification under each question, a research-gap statement closing the
related-work chapter, threats to validity stated per question inside the method
chapter rather than in a chapter of their own, scope appearing as exclusions
rather than under a heading called Delimitations, a deliverables list that a
proposal must not carry at all, and a redesign section recording a decision taken
mid-work.

## Source

- Title: Soil-Moisture-Driven Irrigation Scheduling for Smallholder Farms
- Degree level: Master's
- Language: en
- Author on the cover page: Erika Musterfrau, matriculation 00000000
- Supervisor on the cover page: Prof. Example (prof@example.org)
- Marked on every page: INTERNAL USE ONLY
- Registered: April 2026. Submitted: September 2026.

## Aim and objectives (thesis, section 1.2)

Aim: to determine whether irrigation scheduling driven by soil-moisture readings
uses less water than the fixed timetables smallholders currently follow, and
under which conditions the sensing it depends on stops being trustworthy.

Objectives, as the thesis lists them:

- Build a scheduling controller that reads soil moisture directly instead of following a fixed timetable.
- Compare its water use against the timetable practice the region currently uses, over a growing season.
- Characterise how sensor drift develops in the field and when it degrades scheduling quality.

## Research questions as stated (thesis, section 1.2)

1. To what degree does soil-moisture-driven scheduling reduce water use compared to fixed timetables?
   - Justification given: water is the binding constraint for smallholders in the region, and the timetable practice was set by convention rather than by measurement.
2. Under which soil conditions does sensor drift degrade scheduling quality?
   - Justification given: a controller is only as good as its input, and low-cost probes are known to drift.

## Research gap (thesis, section 3.4, closing the related-work chapter)

Moisture-driven control is established for large irrigation installations, and
low-cost sensing hardware is well characterised on the bench. What no work
covers is the two together at smallholder scale, where the probes are cheap
enough to drift and nobody recalibrates them.

## Methodology (thesis, chapter 4)

Prototype implementation, evaluated in a field trial. The thesis calls it
"prototype and field evaluation".

## Evaluation design (thesis, chapter 4, setup sentences only)

- Compared soil-moisture-driven scheduling against the fixed timetable currently used, over one growing season.
- The comparison ran on the Agrarmesse open sensor corpus, which was named in the registration document as the evaluation material.
- Sensor drift was measured by re-calibrating each probe monthly against a reference probe.

## Threats to validity, as the thesis states them per question (chapter 4)

- For RQ1: one region and one growing season, so the comparison may not transfer to other climates.
- For RQ1: farms self-selected into the panel, so it is not representative of the region.
- For RQ2: probe placement was not standardised across farms, so drift and placement are confounded.

## Scope, as the thesis states it (sections 1.4 and 4.2.6)

- "Irrigation hardware costs and procurement are outside the scope of this thesis."
- "The focus remains on maize; other crops are not considered."
- "Exclusion of other controller designs": model-predictive control was ruled out as needing forecast data the farms do not have.

## Deliverables, as the thesis lists them (section 1.5, "expected results")

- A working scheduling controller.
- A performance report comparing it against the timetable practice.
- A drift characterisation across the soil types in the panel.
- Recommendations for smallholders adopting moisture-driven scheduling.

## Execution outcomes (recorded here so they can be excluded, never carried over)

- The final panel comprised 41 farms, after nine of the fifty enrolled withdrew mid-season.
- The controller reduced water use by 18 % against the timetable baseline.
- Drift exceeded the tolerance on clay soils after eleven weeks.
- Section 4.3.2, "Justification for removing certain parameters": humidity was dropped from the controller inputs after the pilot showed the probes could not resolve it.
- Section 4.3.5, "Redesign": a Kalman filter replaced the moving-average smoother once the smoother proved too slow to react.

## Future work (thesis, chapter 7)

- Multi-crop scheduling.
- Predictive scheduling from weather forecasts.

## References, with where each was cited

- Rivera23Survey — introduction and related work. L. Rivera, "A survey of smart irrigation control", 2023, DOI 10.5555/example-rivera.
- Tanaka22Sensors — method chapter (the sensing approach the prototype builds on). H. Tanaka, "Low-cost soil moisture sensing", 2022, DOI 10.5555/example-tanaka.
- Okafor21Drift — introduction and related work (drift as a known problem), then again in the results discussion. C. Okafor, "Calibration drift in field sensor networks", 2021, DOI 10.5555/example-okafor.
- Lindqvist24Yield — results discussion only, to explain an unexpected yield figure. M. Lindqvist, "Yield variation under deficit irrigation", 2024, DOI 10.5555/example-lindqvist.
- Baumgartner20Timetables — results discussion only, comparing against reported timetable practice. S. Baumgartner, "Fixed irrigation timetables in practice", 2020, DOI 10.5555/example-baumgartner.
