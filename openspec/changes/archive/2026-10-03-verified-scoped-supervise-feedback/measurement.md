# Measurement

All runs used the dev runner on the subscription with `--model sonnet --isolated`, a fresh host configuration that carries none of the operator's plugins or hooks.

## Attempt 0 — host login expired

Both scenarios ended at the first turn, with no cost. The result event read: subtype `success`, `is_error` true, `terminal_reason` `api_error`, result "Failed to authenticate: OAuth session expired". The runner reported "success: no detail" because it read only `errors`. That was a harness defect, fixed here (task 3.4) and pinned by an L0 test. No skill behaviour was observed. The professor renewed the login.

## Round 1 — skill as reviewed

| Scenario | L1 as run | Cost | Turns | Helpers | Feedback words |
|---|---|---|---|---|---|
| `supervise_feedback` (s01, offline) | FAIL → PASS after verdict fix | $0.32 | 11 | 0 | 601 |
| `supervise_scope` (s02, lookups granted) | FAIL → PASS after verdict fix | $0.86 | 27 | 0 | 1,018 |

Both failures were in the harness, not in the skill. They were fixed, and the recorded artifacts were re-judged with the fixed verdicts:

- **s01, pointers.** Without code markup, the run wrote "Proposal-write helps with this." The pointer verdict matched only lowercase. It is now case-insensitive, and the skill asks for the lowercase name.
- **s02, locators.** The feedback named "WCAG 2.0" when describing the success criteria a cited paper measured. The proposal cites WCAG 2.2. WCAG versions now compare as one family, the way years of an ISO edition already did.

What the artifacts show, read by hand:

- **Planted regulation error caught.** The point names Directive (EU) 2016/2102 as the act for public-sector websites and says what 2019/882 covers. Both EUR-Lex texts were fetched, and both locators are in the feedback.
- **Planted citation misuse caught.** The point reports what the paper measured, against the student's reading. The ACM page returned 403. The run used a search-result rendering of the abstract and labelled it "partly supported" in the review. OpenAlex carries the abstract too; the run did not use it.
- **Workload.** Both reviews carry a work-package table, unknowns and a scope verdict; both runs judged their plans over-scoped. s01: 27–39 weeks against 24. Both feedbacks open the body with a scope paragraph offering A/B/C cuts and "the choice is yours". s02 asks for the catalogue size, the recruitment of screen-reader users, and what hinges on the pending registration.
- **No format lecture.** The s02 review parks the Gantt chart and chapter outline under its own "Format (not in feedback)" section.
- **Woven literature.** s02 wove one paper, Quispe et al. 2020, with its DOI, recorded in the notes and marked as an optional alternative, so the workload budget held.
- **Verification sections.** Both list exceptions first, with sources.
- **Verifier.** Neither run spawned it. s02 said so in its wrap-up: "I ran no separate verifier agent". The skill read "Where the host runs helpers … or ask its questions yourself", which left the choice open. The wording is now "can start helper agents … always add that verifier"; round 2 measures it.

## Round 2 — verifier wording tightened

| Scenario | L1 | Cost | Helpers | Feedback words |
|---|---|---|---|---|
| `supervise_feedback` (s01, offline) | PASS | $0.28 | 0 | 553 |
| `supervise_scope` (s02) | FAIL | $0.91 | 1 | 872 |

- **s01 still ran the verifier's checks inline:** "I did not launch a verifier agent. I ran its checks myself inline". The headless host does offer `Task` and `Workflow`. This is a compliance gap on a capable host. Its review records the inline checks; every verdict passes.
- **s02 spawned the verifier.** It flagged issues, and the main agent corrected them. EUR-Lex was blocked by a bot check this time. The run kept the regulation claim out of the feedback as fact and asked the student to re-source the legal basis from the primary texts. That is the offline rule working on a single unreachable source.
- **s02's L1 failure is genuine.** A woven preprint was not recorded in the notes file. Every round-1 paper had been recorded. The pre-existing literature verdict caught it. The final reread checklist now names "every woven paper recorded in the notes".

## Round 3 — final text

| Scenario | L1 | Cost | Helpers | Feedback words |
|---|---|---|---|---|
| `supervise_scope` (s02) | PASS | $1.00 | 1 | 1,112 |

Every verdict passes: four points, A/B/C cuts with the choice left to the student, no format remark, light markup, one paper woven and recorded, the new regulation located, the review's workload table with a scope verdict, and the verification section.

The verifier corrected five things before hand-over:
- an inexact research-question quote;
- a wrong option cross-reference;
- a second, missed occurrence of the regulation error;
- an objective located where normalization had moved it rather than where the student wrote it;
- asks that did not name what they replace.

One claim stayed unverified and out of the feedback: which WCAG version EN 301 549 V3.2.1 incorporates.

## Reading

- **Verification works when it runs.** Abstracts and primary texts were fetched, unverifiable claims were kept out or asked as questions, and the verifier caught rewrite-class errors. The added cost is about $0.6 per run over the offline s01 arm, against roughly 1.05M subagent tokens for the session's repair.
- **Verifier spawning is model behaviour.** It happened in 2 of 4 runs and 2 of 3 since the wording fix. s01 offline skipped it twice. A multi-epoch measurement belongs to the next matrix round.
- **Single runs per round.** These are single runs, not epochs; the pass rates are anecdotal.
