## Why

When the skills misbehave, a student has no path to a useful report. The README's only guidance is "please open an issue first", which produces reports that name a symptom and nothing else: no environment, no idea which revision was installed, no trace of what the agent actually did. Reconstructing any of that after the fact is impossible, because the evidence lives in a chat session that is gone.

Two properties of this product make the generic answer wrong. First, the material is an unpublished thesis idea plus personal data, so a public issue template inviting the user to paste their proposal is the wrong default. Second, most failures are not defects: an unsupported model, a `guidelines.md` override doing exactly its job, or a stale install. Without triage, the reports that do arrive bury the real defects.

## What Changes

- **New ninth skill `proposal-troubleshoot`.** Runs a fixed triage ladder against a reported problem, resolves the non-defect cases itself, and only then assembles a report. The name avoids `proposal-report`, which reads as a near-twin of `proposal-review` in the workflow line.
- **Triage before collection.** A stale install is checked first and answered with `npx skills update`; then the vendored model-support verdicts, then a workspace `guidelines.md` override, then script failure, then a violated skill mandate, then "I do not like the output". Only the middle two categories produce a report.
- **Local bundle, user delivers.** The skill writes `bug-report/` into the user's proposal folder after showing what it contains. Nothing is transmitted, and no `gh` integration exists — the user chooses whether the report goes to a GitHub issue, an email, or their supervisor.
- **Redaction ladder with a paranoid default.** `minimal` carries no proposal prose at all; `structure` adds headings, TODO texts and DOIs; `full` adds the text with the personal-data strip applied. The user picks after seeing what each level adds.
- **Evidence separated from testimony.** Script-collected facts are tagged `[measured]`; anything the agent supplies about itself — model id, harness, replay of the failing exchange — is tagged `[self-reported]`. The agent writing the report is the subject of the report.
- **Revision identified without new shipped artifacts.** The bundle harvests the workspace `skills-lock.json` verbatim and dumps a raw SHA-256 per installed skill file; a new maintainer-side `scripts/identify_release.py` walks git history to name the commit and flag files matching no release as locally modified.
- **Conditional reproduction seed.** For mechanically reproducible defects the agent reduces the input to a minimal synthetic file and ships it as `repro/`, which drops into the existing fixture corpus. Judgment defects get prose only.
- **One offer line in every skill's failure path.** Uniform across all nine skills, offered once per session, never a nag, never collecting without consent.
- **Workflow line changes in all eight existing skills**, since each page names the whole set.

## Capabilities

### New Capabilities

- `skill-troubleshoot`: the ninth skill — triage ladder, redaction ladder, bundle contents and layout, evidence/testimony tagging, revision identification, conditional reproduction seed, and the discipline governing when a report is offered.

### Modified Capabilities

- `skill-packaging`: the skill set grows from eight members to nine, so the byte-identical workflow line, the uniform opening structure, the pinned mandate corpus and their offline enforcement all extend to the new member. Adds a uniform requirement that every skill's failure path carries the single bug-report offer, and a new synced artifact — the model-support verdicts exported as JSON and vendored into the troubleshoot skill, which cannot read this repository.
- `user-onboarding`: the README gains a "When something goes wrong" section, and the repository gains a structured issue template whose fields mirror the generated report so pasting is mechanical rather than interpretive.
- `testing-harness`: `harness/support.py` gains the JSON export the vendored verdicts are built from; the offer line needs negative coverage proving it does not fire on ordinary findings; and a shipped reproduction seed is recognized as a fixture candidate for the existing corpus.

## Impact

- **New**: `skills/proposal-troubleshoot/` (SKILL.md, `scripts/collect.py`, `references/model-support.json`), `scripts/identify_release.py`, `.github/ISSUE_TEMPLATE/skill-defect.yml`, `tests/unit/data/skill_mandates/proposal-troubleshoot.txt`.
- **Modified**: the workflow line in all eight existing `SKILL.md` files plus a failure-path offer line in each; `scripts/sync_shared.py` (new synced artifact); `harness/support.py` (JSON export); `harness/skill_evals.py` (offer-discipline coverage); `tests/unit/test_skill_header_pattern.py` (nine skills); `README.md`.
- **Constraints**: `scripts/collect.py` is user-side — Python ≥ 3.11 standard library only, no pip, cross-platform. It writes only inside the bundle directory it creates, so it does not collide with the read-only mandates of `proposal-check` and `proposal-review`.
- **Out of scope**: the published snapshot currently trailing `main`. That gap closes with the rewrite already in flight.
