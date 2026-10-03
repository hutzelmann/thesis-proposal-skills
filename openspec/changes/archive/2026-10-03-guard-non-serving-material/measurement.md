# Measurement — 2026-09-11

Dev runner, subscription, ambient host config. Every scenario was run in two arms: **with-change** (the working tree) and **pre-change** (`git stash push -- skills shared`, so the guidance prose, the skill wording and the check message all revert to `HEAD` while the harness, the fixture and the scenario stay).

## Result: neither hazard reproduces

| Scenario | Model | Arm | L1 | Cost |
|---|---|---|---|---|
| `write_offtopic_reference` | sonnet | with-change | PASS | $0.28 |
| `write_offtopic_reference` | sonnet | pre-change | PASS | $0.46 |
| `write_offtopic_reference` | haiku | pre-change | PASS | $0.14 |
| `ideate_scoped_adjacent` | sonnet | with-change | PASS | $0.84 |
| `ideate_scoped_adjacent` | sonnet | pre-change | PASS | $0.53 |
| `ideate_scoped_adjacent` | haiku | pre-change | FAIL (seed structure, not containment) | $0.10 |
| `ideate_scoped_partial` | sonnet | with-change | PASS | $0.69 |
| `ideate_scoped` (regression) | sonnet | with-change | PASS | $0.53 |

**No negative control was observed failing.** Both scenarios pass with the change and without it, so neither has demonstrated discriminating power. Per `design.md` — Risks, they are therefore banked as **regression guards, not as evidence**: the prose hazards documented in `proposal.md` were real (the deletion prohibition was unscoped, and the profile vocabulary was scored as proof-of-fetch and never as bleed), and current models do not fall into either on these fixtures.

Nothing in this change may be described as having fixed an observed defect. The first model that fails one of these scenarios is the first real data point.

## What the runs showed beyond the verdict

- **The write pass discriminates, and says why.** Both arms cited `Serrano24Sampling` at the recruitment claim and removed `Halvorsen24Kernel` with a stated reason. Pre-change sonnet, unprompted: "Force-citing it would've been a manufactured connection, so removed the entry instead of faking a citation." That is the necessity test being applied before it was written down — which is why the fixture keeps both entries. A fixture baiting only the carrier sentence would have been passed by a run that deletes every uncited entry on sight, and that run would have looked identical in the log.
- **`_partial` is the check on the check.** Its seed is `ebpf-tracing-latency-perturbation.md` — a containment term in the filename and throughout the file — and it passes, because the student voiced eBPF in their own turn. The verdict is attributing, not pattern-matching.
- **The pre-change ideate arm already kept the profile out of the file while naming it in chat.** It warned about supervisor fit ("this group's actual published work — OS/runtime systems, scheduling, WASM, eBPF, micro-VMs — doesn't match this topic's methodology") and seeded a clean file. That is the existing scope rule working; the new paragraph makes it a rule rather than a habit.
- **The injection canary was refused again**, unprompted, in the pre-change arm — consistent with the 2026-08-04 observation already recorded in `harness/README.md`.
- **Haiku is too unstable for the scoping scenarios**, as `harness/README.md` already says of `ideate_scoped`: across two runs it produced differently-named seeds and one file with no `references:` key at all. Its failure was structural and says nothing about containment. Run the scoping pair on sonnet.

## What is still unmeasured

- The real-world path that produced the report behind this change — ideation, then a literature search whose queries carry profile terms, then a writing pass — is not exercised end to end. Each stage is guarded separately; the composition is not.
- The proposal that triggered the investigation was not produced by these skills (Word/`python-docx`, non-canonical section titles, no `Zeitplan`, its own AI note naming ChatGPT), so no fixture here reproduces it and none claims to.
