# Design

## Context

See proposal.md — Why. The letter machinery spans four components: the skill prose (`skills/proposal-supervise/SKILL.md`), the shared blurb snippet (`references/getting-started.md`), the troubleshoot companion inventory (`skills/proposal-troubleshoot/scripts/collect.py`), and the harness verdicts (`harness/l1_checks.py`, `harness/skill_evals.py`, `harness/claude_runner.py`). The Inspect scorer names (`supervise_l1_*`) are pinned by `tests/unit/test_eval_wiring.py` and read by the model-support classifier.

## Goals / Non-Goals

**Goals**: letter-only student artifact; honest disclosure; one-sentence blurb; every consumer of the package path migrated in the same change.

**Non-Goals**: no change to normalization, tiering, review-file content, or the starter-literature offer; no change to scorer names; no re-run of metered evals (L0 only); terminology enforcement (proposal vs. Exposé) is a separate change.

## Decisions

- **Letter path is `<slug>-letter.md`**, beside `<slug>.md` and `<slug>-review.md`. A flat suffix-named file mirrors the review file's convention and gives the troubleshoot collector a deterministic name to hash. Alternative — keeping a one-file `<slug>-package/` — preserves globs but ships ceremony without cargo.
- **Scorer names stay `supervise_l1_*`** (already letter-shaped); only the internal helper (`supervise_package()` → `supervise_letter_files()`), the runner's `package_files`, and the aggregate `verdict_supervise_package` → `verdict_supervise_letter_contract` are renamed. Keeps `test_eval_wiring.py` pins and the README model-support report stable.
- **`verdict_supervise_no_personal_data` keeps its `dict[str, str]` signature**, now fed only the letter file. The shape is the contract; narrowing to a single string would ripple through every caller for no behavioral gain, and the verdict still names the leaking file.
- **Blurb snippet file stays** at `references/getting-started.md` as the shared EN/DE verbatim source; only its content shrinks. The letter still quotes it verbatim, so the L2 surface is unchanged.
- **Disclosure and trust line merge into one sentence** authored per-letter by the agent (per SKILL.md), not a verbatim snippet — matching current behavior where only the blurb is verbatim.
- **Delivery wording is channel-neutral.** The professor "delivers the letter as text through their own channel — an email reply or a learning platform's feedback field". Naming the platform case keeps the Moodle-style workflow (student submits a PDF on the platform, supervisor answers in the feedback box) directly supported; email-specific phrasing like "quoted reply" is avoided everywhere.

## Risks / Trade-offs

- [Old runs/workspaces still hold `<slug>-package/` directories] → collect.py only reports what exists; a stale package directory simply stops being inventoried. Reports self-identify their revision via `hashes.txt`, so `poe identify` disambiguates.
- [Letter pasted as plain text — email reply or platform feedback field — loses markdown structure] → the letter already uses plain numbered lists and bold tier phrases that survive plain-text paste; no format change needed.
- [Eval fixtures/prompts that mention the attachment] → audited as part of tasks; the supervise eval request text is checked for package phrasing.

## Migration Plan

Single change, no deployment surface. Publish to skills.sh happens only on explicit request later; until then the repo is internally consistent after `uv run poe test`.
