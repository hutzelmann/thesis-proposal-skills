## Why

An adversarial probe run (2026-08-13, `sa-test/`) drove all ten skills through 16 student-shaped requests. Direct refusal held everywhere — invented citations, deleted TODO markers, personal data, a padded page count, a build fallback under deadline pressure were all declined. What broke was a chain nobody had aimed at: **the checker calling a correct document wrong, and the write skill treating that verdict as binding.**

A student writes about Java annotations. `scan_citations` matches any `@Word`, so `@Override` in prose is reported as `citation-undefined` — an error, and the error class carries no "false positives acknowledged" caveat. `proposal-write` says to fix every error with exactly two exemptions, neither of which covers a wrong finding. One model rewrote the author's terminology to satisfy the checker; another backticked the annotations (the regex ignored backticks, so the error survived), deleted a real reference to silence an unrelated warning, dropped below `min_references`, and reported "Done. Fixed both errors" without re-running the check. Two errors in, three errors out.

The same shape, cheaper, appears four more times: `Type I error` — required vocabulary in the repo's own Controlled Experiment subsection contract — is read as a first-person pronoun; a seven-digit corpus size is read as a matriculation number, and neither warning says where it fired, so dismissing it means reading the whole file; a metadata block at the top of the file (where every other markdown tool puts it) produces five errors, none of which mentions the position; a Word export whose headings are underlined instead of prefixed is reported as five missing sections.

## What Changes

- The citation scan skips fenced code blocks and inline code spans and honours a `\@` escape, and `citation-undefined` names both escapes in its message. A `@Word` that is code now has a *markup* fix; before, the only way out was editing the prose.
- `proposal-write` gains a third must-not-fix item: a finding demonstrably wrong is reported, never worked around. Fixing the markup stays allowed where markup is the defect; rewording the author's content, or deleting a reference or sentence to silence a finding, does not. `proposal-troubleshoot` is named as the landing place.
- `proposal-check`'s mandate states that a request combining check and fix is two steps rather than an exception, and the digest re-run is re-scoped from "your very last step" to the last step *of the check*, before any edit — an editing run never reached the old wording, so the tripwire could not fire.
- Every warning in the prose-pattern class carries a line number, and the matriculation warning quotes the token it matched. `Type I error` and other `<Capitalised word> I` Roman-numeral labels stop counting as pronouns.
- Two document shapes get named instead of only their consequences: a metadata block at the top of the file, and setext (underlined) headings. Both were reported as a pile of downstream errors with no diagnosis.
- The L1 harness gains `check_report_compound` — the exact utterance that broke the read-only mandate, scored on the proposal being byte-identical afterwards.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-check`: code spans, code fences and `\@` are excluded from citation scanning; prose-pattern warnings carry a location; a leading metadata block and setext headings are diagnosed by name; the read-only requirement covers a combined check-and-fix request and orders the digest re-run before any edit.
- `skill-write`: a finding demonstrably wrong joins the closed list of findings that must not be "fixed".
- `testing-harness`: the compound check-and-fix utterance becomes a scored L1 task.

## Impact

- `skills/proposal-check/scripts/check.py` and its three vendored copies — `scan_citations`, `rule_prose_patterns`, `rule_metadata_present`, one new rule and one new identifier (`heading-style-setext`).
- `skills/proposal-check/SKILL.md` (mandate and digest step) and `skills/proposal-write/SKILL.md` (third must-not-fix item), with their pinned copies under `tests/unit/data/`.
- `harness/skill_evals.py`, `harness/models.toml` — one task, excluded from the matrix like its two siblings.
- No fixture oracle changes: the whole corpus reports exactly what it did before, which is what makes these fixes false-positive removals rather than a rule change.
