# Simplify the supervise letter

## Why

The supervise feedback letter overreaches in two places and overdelivers in a third. Its disclosure claims the AI assistant "follows the program's proposal guidelines" — an overclaim, since the shipped defaults are portable and the program's actual guidelines may differ. Its getting-started blurb is a paragraph of setup steps that duplicates the repository README and prescribes a next step ("help me improve my proposal") the supervisor cannot know. And the send-package asks the professor to attach a normalized proposal file to their reply, which real use showed is a burden — and which does not fit feedback returned through a learning platform at all: the letter alone, pasted as text into an email reply or a platform's feedback field, is the deliverable.

## What Changes

- **BREAKING** The send-package is retired. The letter becomes the only student-facing artifact, written professor-side as `<slug>-letter.md`; the professor delivers it as pasted text through their own channel — an email reply or a learning platform's feedback field (e.g. a Moodle assignment comment). No attachment, no `<slug>-package/` directory. The normalized `<slug>.md` and `<slug>-review.md` remain professor-side working artifacts.
- The disclosure drops the guideline claim and absorbs the letter's trust line: the feedback was prepared with an AI assistant, and every decision about the thesis stays with the student.
- The getting-started blurb shrinks to one sentence per language — a pointer to the repository with a "guide starts from zero" nod — and stops naming assistants, install commands, or a prescribed first prompt. It remains a shared verbatim snippet in English and German.
- The troubleshoot companion inventory records the letter file instead of a send-package directory.
- The harness supervise task asserts the letter contract (existence, curated points, tier, personal-data absence, resolving pointers) against the letter file instead of a package directory.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-supervise`: the student-facing package requirement becomes a student-facing letter requirement (letter-only, paste-ready, no attachment); the disclosure scenario loses the guideline claim and gains the decisions-stay-yours clause; the blurb requirement stops mandating attachment placement and the writing-skill continuation; package-separation becomes letter separation.
- `skill-troubleshoot`: the companion-artifact inventory names the supervise letter file rather than the send-package directory.
- `testing-harness`: the supervise coverage requirement asserts the letter contract on the letter file, not on a package.

## Impact

- `skills/proposal-supervise/SKILL.md` — curate/package/wrap-up sections, disclosure item.
- `skills/proposal-supervise/references/getting-started.md` — both language blurbs replaced.
- `skills/proposal-troubleshoot/scripts/collect.py` — inventory glob `<slug>-package/` → `<slug>-letter.md`; troubleshoot SKILL.md wording if it names the package.
- `harness/l1_checks.py`, `harness/skill_evals.py` — package-shaped verdict inputs become letter-shaped; aggregate verdict renamed accordingly.
- `tests/unit/test_supervise_verdicts.py`, `tests/unit/test_troubleshoot_*` (whichever pins the inventory) — updated.
- `skills/*/evals/evals.json` — regenerated projections where scorer names shift.
