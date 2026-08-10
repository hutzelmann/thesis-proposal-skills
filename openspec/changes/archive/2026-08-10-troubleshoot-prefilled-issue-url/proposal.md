# Proposal: troubleshoot-prefilled-issue-url

## Why

A finished bug report currently ends with a bare pointer at the GitHub issues page: the user opens a blank skill-defect form and re-types by hand what `report.md` already holds. The repository's issue form has stable field ids and GitHub prefills them from URL query parameters, so the skill can hand the user a link that lands on the form with the short fields already filled — without touching the rule that the skill transmits nothing and files nothing.

## What Changes

- The "Delivering it" section of `skills/proposal-troubleshoot/SKILL.md` instructs the agent, once the `[self-reported]` fields in `report.md` are filled, to construct a prefilled issue URL — `https://github.com/hutzelmann/thesis-proposal-skills/issues/new?template=skill-defect.yml` plus URL-encoded parameters for the form's short fields (`skill`, `rung`, `what_happened`, `self_reported`) — and present it as the issue option.
- Long fields (`measured`, `script_output`, `repro`) stay paste-in: URL length limits make them unreliable as query parameters, and the instruction says so.
- Unchanged constraints, restated in place: the skill opens nothing, submits nothing, acquires no credentials; the user clicks, reviews, and decides. Content in the URL never exceeds what the chosen disclosure level put into `report.md`.
- No script changes; no change to the mandate paragraph or the report-offer block (pinned prose stays byte-identical).

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `skill-troubleshoot`: "Report stays local and is delivered by the user" — naming the issue option now includes handing over a prefilled form URL built from the report's own short fields; transmission, filing, and credentials stay forbidden.

## Impact

- `skills/proposal-troubleshoot/SKILL.md` — "Delivering it" section only
- `tests/unit/` — only if a pinned-prose test resolves the edited section (mandate pin and report-offer pin must remain untouched)
