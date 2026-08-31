# Rename the student-facing artifact from letter to feedback

## Why

"Letter" is the last channel-biased word left after the send-package retirement: pasted into a learning platform's feedback field, the artifact is not a letter — it is the feedback, which is also what both channels and both languages call it. A real run additionally showed the professor-side review being described in chat as "detailed feedback", so the naming must also fix which file may carry the word.

## What Changes

- **BREAKING** The student-facing artifact becomes `<slug>-feedback.md`; prose says "the feedback" / "the feedback draft". The professor-side files keep their names (`<slug>.md`, `<slug>-review.md`).
- The review file is presented under its own name — the review — and is never described as feedback, so the professor cannot paste the wrong file.
- Harness follows: verdict/aggregate function names, the letter-file readers, the dev-runner scenario key, and the presence scorer (`supervise_l1_letter` → `supervise_l1_feedback`; the other four scorer names carry no "letter" and stay). Supervise is not yet in the model-support report baseline and no eval logs exist locally, so the scorer rename has no report ripple.
- README's supervise paragraph loses the stale "attaching the normalized file" sentence left over from the send-package retirement, and all letter wording in docs follows the rename.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-supervise`: every requirement that names the letter now names the feedback; the two requirement titles carrying "letter" are renamed; delivery separation adds that the review file is never described as feedback.
- `skill-troubleshoot`: the companion inventory names the supervise feedback file.
- `testing-harness`: the supervise coverage requirement asserts the feedback contract on the slug-named feedback file.

## Impact

- `openspec/specs/skill-supervise/spec.md` (incl. its Purpose line, edited directly per the Purpose rule), `skill-troubleshoot`, `testing-harness`.
- `skills/proposal-supervise/SKILL.md` (incl. the pinned mandate — pin updated in the same change), `references/getting-started.md` heading.
- `skills/proposal-troubleshoot/scripts/collect.py` and its tests.
- `harness/l1_checks.py`, `harness/skill_evals.py`, `harness/claude_runner.py`, `harness/eval_export.py`; regenerated `evals.json`; `tests/unit/test_eval_wiring.py` pins; `tests/unit/test_supervise_verdicts.py`.
- `README.md` (table row, supervise paragraph incl. stale attach sentence), `harness/README.md`, `tests/fixtures/README.md`.
