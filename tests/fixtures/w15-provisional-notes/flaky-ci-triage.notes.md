# flaky-ci-triage — notes

## Decisions

- Preamble: study program Computer Science (M.Sc.); target research group: the software engineering group of the department, no supervisor named yet; Master's thesis; proposal in English; about six working months; online lookups declined for this session.
- Problem: in the student's team, a failing CI job is retried by hand until it passes, and nobody records whether the failure was a flaky test, an infrastructure fault or a real regression. Triage takes the on-call engineer most of a morning per incident.
- Why it matters: real regressions hide among retried failures; the team merged two regressions last quarter that a retry had masked.
- Object of study: the team's own CI history, about 4,000 failed jobs over eighteen months with logs and retry outcomes, which the team lead has agreed to share in anonymised form.
- Candidate research-question directions: (1) which log and retry features separate flaky failures from regressions in this history; (2) how much of the triage time a ranking built on those features saves, measured against the on-call engineers' current order.
- Method: an empirical evaluation on the team's history — label a stratified sample of 300 failures by hand with a second rater on a subset, train an interpretable classifier, and replay the last three months in time order to measure ranking quality.
- Feasibility: labelling one failure takes about five minutes, so the sample fits the first six weeks; the replay runs on a laptop.

## Open Points

- Whether the second rater is a team colleague or the supervisor's doctoral student.

## Next Focus

- Seed the proposal once the working title is settled.

## Excluded Literature

## Log

- 2026-10-11: Sketched the triage flow from failed job to ranked queue: [sketch](img/flaky-ci-triage-sketch.png). Kept the reading list in `flaky-ci-triage.reading-list.md` at the student's request.
- 2026-10-12: All five aspects concrete; seeding offered for the next session.
