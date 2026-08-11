## Why

The 2026-08-11 literature survey found the shipped User Study branch structurally unable to carry hypothesis-testing research: its Preparation/Procedure/Analysis contract mirrors Wohlin et al.'s *operation* phase, so a student running a controlled experiment under it satisfies every heading while skipping hypotheses, variables, design, and validity — everything the experiment literature's planning phase exists to force. "User study" is also not a term of art; the empirical-methods literature partitions human research into experiment, survey, and observational study. The approved plan adds Controlled Experiment as a default branch and bounds User Study against it.

The subsection contract follows the literature rather than the externally proposed four-subsection split: Wohlin et al. treat variable selection as one planning step whose point is relating manipulated to measured variables in a hypothesis, and the proposed Independent Variables / Dependent Variables split spent two subsections on that one step while leaving hypotheses, design, participants, and validity homeless.

## What Changes

- New default methodology branch **Controlled Experiment** / **Kontrolliertes Experiment** with subsections Hypotheses and Variables / Design and Participants / Statistical Analysis (de: Hypothesen und Variablen / Versuchsdesign und Teilnehmende / Statistische Auswertung), with a content contract per subsection derived from Wohlin et al.'s planning steps and the SIGSOFT Experiments standard.
- The User Study contract gains its boundary: observational, usability, and survey-style research with human participants; hypothesis testing with manipulated treatments belongs in Controlled Experiment.
- New fixture `f23-controlled-experiment` with a calibrated oracle, exercising the new branch cleanly.

Not breaking: purely additive to the shipped set; existing proposals are unaffected.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the canonical-structure requirement's methodology enumeration gains Controlled Experiment; an added requirement pins the branch's subsection contract and the User Study boundary.

## Impact

- `shared/structure.json`, `shared/guidelines/guidelines.md` (enumeration, title tables, content contracts), generated copies via sync.
- `tests/fixtures/f23-controlled-experiment/` (new) and `tests/fixtures/README.md`.
- No check-script changes: the branch flows from the structured data.
