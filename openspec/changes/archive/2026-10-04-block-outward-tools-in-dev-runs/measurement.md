# Measurement

## Model check (dev runner, `supervise_scope`, isolated, 3 runs per model)

| Model | Skill invoked | Verifier ran | Both planted errors caught | L1 | Cost (quota) | Feedback words |
|---|---|---|---|---|---|---|
| opus | 3/3 | 3/3 | 3/3 | 3/3 PASS | $1.87–2.39 | 1,163–1,236 |
| haiku | 0/3 | 0/3 | 0/3 | 0/3 | $0.06–0.24 | none written by the skill |

Sonnet, from `require-supervise-verifier`: 6 of 6 runs started the verifier, and every run passed after one verdict fix.

Haiku never loaded the skill. It answered on its own, called the over-scoped plan "ready to proceed", and missed both planted errors. In three of the runs it published its answer as a claude.ai artifact. The artifacts held synthetic fixture data only, were private, and were deleted on 2026-10-03. That publishing is the reason for this change.

## Publishing blocked (task 1.3)

A haiku run after the change shows no Artifact, SendMessage or scheduling tool in the host's tool list, and nothing was published. `CronDelete` and `ListAgents` were still offered, and were added to the list.

## Routing (routing rig, `--no-report`)

| Model | Cases | Correct | Notes |
|---|---|---|---|
| haiku | supervise ×4, 3 epochs | 0/12 | 11× no skill, 1× proposal-review |
| haiku | check, review, write, ideate, lit-search, customize, 2 epochs | 4/12 | check 2/2, write 1/2, ideate 1/2, the rest 0 |
| haiku | supervise ×4, 3 epochs, trigger-first description variant | 0/12 | all no skill; the variant was reverted |
| sonnet | the full set, recorded in `docs/skill-routing.md` | 119/120 | supervise 12/12 |

Haiku's skill routing is weak in general and absent for supervise. A description variant did not change it. The README therefore states the model requirement, and the skill text stays unchanged.
