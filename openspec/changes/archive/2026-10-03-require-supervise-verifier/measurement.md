# Measurement

All runs used the dev runner, `--model sonnet --isolated --keep`, on the subscription. "Spawned" means a subagent call whose task was verifying the feedback. In the baseline no run could carry the brief, which did not exist yet, so the spawn is read from the saved stream, not from the scored verdict.

## Baseline — skill text as committed in eecd8db

| Arm | Run | Verifier spawned | Cost | Feedback words | The agent's own reason (from `.devrun-events.jsonl`) |
|---|---|---|---|---|---|
| s01 offline | 1 | no | $0.26 | 543 | "It cites no papers, standards or figures, so I made no network lookups … I did not run the separate verifier agent." |
| s01 offline | 2 | yes | $0.43 | 669 | the verifier's findings were applied, four of five |
| s01 offline | 3 | no | $0.25 | 453 | "I did not start a verifier agent, because I couldn't ask you anything" |
| s02 lookups | 1 | yes | $0.97 | 921 | the verifier's corrections were applied, including a recital number dropped as unconfirmable |
| s02 lookups | 2 | yes | $0.90 | 1,141 | "handing it to one independent verifier" |
| s02 lookups | 3 | no | $0.68 | 885 | "I also didn't start a separate verifier agent. I checked each claim myself against its fetched source." |

The verifier ran in **3 of 6 runs** (s01 1/3, s02 2/3).

The skips have two causes:
1. **The verifier read as being about external sources.** With no papers or norms to check, it seemed unnecessary.
2. **The headless request's "I cannot answer any further question" was read as ruling out a helper.**

Both causes now have their own sentence in the skill:
- "offline too: approval decides what the verifier may fetch, not whether it runs";
- "it asks the professor nothing, so a run that cannot ask still starts it".

## After — brief, offline sentence, declared fallback

| Arm | Run | Verifier spawned (with brief) | Declared | L1 | Cost | Feedback words |
|---|---|---|---|---|---|---|
| s01 offline | 1 | yes | "fresh verifier (offline …)" | PASS | $0.39 | 646 |
| s01 offline | 2 | yes | "fresh verifier" | PASS | $0.38 | 551 |
| s01 offline | 3 | yes | "fresh verifier (offline …)" | PASS | $0.42 | 546 |
| s02 lookups | 1 | yes | "fresh verifier" | PASS | $0.96 | 952 |
| s02 lookups | 2 | yes | "fresh verifier" | FAIL → PASS after verdict fix | $0.73 | 893 |
| s02 lookups | 3 | yes | "fresh verifier" | PASS | $0.85 | 884 |

The verifier ran in **6 of 6 runs**, against 3 of 6 at baseline and the target of at least 5 of 6. The offline arm went from 1 of 3 to 3 of 3. Every run started the verifier with the shipped brief and declared it in the review.

The verifier adds about $0.12–0.15 per offline run, compared with the two skipping baseline runs at $0.25–0.26.

The one failure was in the harness. s02 run 2 linked the paper the student already cites (Vigo et al., by its DOI) inside a point. The literature verdict demanded a notes record for every DOI, as if the paper were woven in. The verdict now leaves out DOIs that the normalized proposal carries, pinned by an L0 test, and the recorded artifacts pass on re-judging.

These are three epochs per arm on one model (sonnet), so the rate is a strong signal, not a guarantee. Other models' compliance belongs to the matrix.
