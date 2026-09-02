## 1. Execution-shape sections

- [x] 1.1 `skills/proposal-review/SKILL.md`: insert `## Execution shape` as the first `##` section (above "What to assess"): opening sentence naming single context, one pass, and the three-agent cap with fixed roles; the helper contract paragraph (main agent only writer, helper works from `<slug>.md` with the resolved override, per-test verdicts, at most five findings, merged duplicates, no reasoning/strengths/restated guidelines; title, density, limit findings stay with the main agent). Header region untouched.
- [x] 1.2 `skills/proposal-supervise/SKILL.md`: insert `## Execution shape` as the first `##` section (above "Normalize the submission"): same opening, supervise terms — helpers never see the submission, adversarial check informs the evidence bar but never decides the tier, per-test return carries decisive/uncertain plus irreparability reason and one quotable finding, strengths and all three artifacts stay with the main agent.
- [x] 1.3 `skills/proposal-check/SKILL.md`: insert `## Execution shape` as the first `##` section (above "Target"): two steps, one agent; script once, agent pass one reading; Python-missing fallback is the same single reading; nothing delegated per category.
- [x] 1.4 `skills/proposal-write/SKILL.md`: insert `## Execution shape` as the first `##` section (above "Ground rules"): one writer, one file; sections in sequence, review findings item by item, density pass whole-file; never one helper per section or per finding; sibling instructions in-context are not a helper.

## 2. Regression pins

- [x] 2.1 Add `tests/unit/data/pinned_sentences/proposal-review--execution-shape.txt`: the `## Execution shape` heading line, blank line, and the opening sentence up to and including the three-agent cap.
- [x] 2.2 Add `proposal-supervise--execution-shape.txt` the same way.
- [x] 2.3 Add `proposal-check--execution-shape.txt` (heading plus opening sentence).
- [x] 2.4 Add `proposal-write--execution-shape.txt` (heading plus opening sentence).

## 3. Cost case in docs and troubleshoot

- [x] 3.1 `skills/proposal-troubleshoot/SKILL.md` rung 5: one sentence — a run that cost many times the usual with correct output is the host's effort or workflow mode fanning the task out against the skill's stated execution shape; name the mode and its budget controls; no report. Mandate untouched.
- [x] 3.2 `README.md` "When something goes wrong", the non-defect-causes paragraph: one sentence pointing at a host effort or workflow mode as the cause of a ten-fold-cost run, with the host's budget controls as the remedy.
- [x] 3.3 `harness/README.md` "Known limitations": one bullet — no harness path observes a fan-out (Inspect: bash and text_editor only; dev runner: stdout only); the execution-shape sections are guarded by L0 pins alone and measured only on a real host run; the dev-runner cost probe (stream-json `total_cost_usd`, `num_turns`; `routing.py` already parses `tool_use`) is the follow-up.

## 4. Verify

- [x] 4.1 `python3 scripts/sync_shared.py --check` clean (no materialized region touched).
- [x] 4.2 `uv run poe test` green: header-pattern (mandates and successors unchanged), pinned sentences (four new pins found), report offer, frontmatter size caps, conformance.
- [x] 4.3 `openspec validate --all --strict` passes.
- [x] 4.4 Re-read the four sections in sequence for host-neutral wording (no host or tool names, "helper agent" not "delegate") and for no restatement of a rule the mandate already states.
