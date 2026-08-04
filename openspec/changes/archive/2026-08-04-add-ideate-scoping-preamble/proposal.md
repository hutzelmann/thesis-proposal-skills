# Add Ideate Scoping Preamble

## Why

Ideation today starts blind: the skill knows nothing about the student's study program or the research group that might supervise the thesis, so it can develop ideas nobody in reach can supervise. Asking for that context up front — and, when possible, reading the group's webpage and recent publications — anchors every later Socratic turn in a field where the thesis can actually happen.

## What Changes

- **Administrative scoping preamble** at session start, mirroring the existing administrative ending (dates): one combined question asking for the study program and — if already known — the supervising professor or target research group, by name or webpage. Every part is optional; skipping everything means ideation proceeds unscoped with an explicit notice. The term used throughout is "research group" (never "chair").
- **Tiered context fetch**: a given URL is fetched with a read-only GET; a given name is looked up via the DBLP author API (recent publication titles) and, where search tools exist, a web search for the group's official page. Everything fetched is untrusted external data — quoted and judged, never treated as instructions — reusing the framing the skill already applies to literature grounding.
- **Scoping as filter and hint source, generously applied**: ideas in even loose proximity to the group's broader interests pass silently. Only a clearly-outside-field idea gets Socratic steering plus a chat-only warning; if the user insists, ideation continues and nothing about fit is written to the seed file. For a student with no idea at all, recent group publications may be offered as Socratic hints, never as a ready-made topic menu.
- **Optional persistence**: at the administrative ending the skill offers once to record a short scoping note in the workspace `guidelines.md` prose section (the customization surface all skills honor). Declining writes nothing. The seed file never carries supervisor names or the study program — the personal-data rule already forbids them in proposals.
- **Test coverage**: a synthetic research-group fixture (fake group page, fake DBLP author response) and a dev-runner scenario asserting the untrusted-data posture (an injection canary on the page must reach no produced file), a clean seed file, and a visible effect of the fetched page. The preamble exchange and the generous threshold are unobservable in a one-shot run and stay prose-reviewed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `skill-ideate`: the Socratic-interaction requirement gains an explicitly bounded administrative opening (today only the administrative ending is carved out); a new requirement covers research-group scoping — the optional preamble, the tiered fetch with untrusted-data framing, the generous fit filter with chat-only warnings, hint generation from group publications, and the once-offered scoping note in workspace `guidelines.md`.

## Impact

- `skills/proposal-ideate/SKILL.md` — prose changes only (the skill ships no scripts); mandate paragraph expected to stay unchanged, otherwise its pinned copy in `tests/unit/data/skill_mandates/` moves in the same change; frontmatter description gains a trigger hint.
- `tests/fixtures/` — new synthetic research-group fixture (obviously fake data, per fixture rules).
- `harness/` — one new claude_runner scenario; no inspect L1 task yet (deferred until prose stabilizes).
- No changes to `shared/` guidance content, generated `references/` copies, or other skills' behavior; the workspace `guidelines.md` prose section is already the documented customization surface.
- Security: the change adds outbound fetch targets (research-group pages, DBLP author API), so the pre-publish `scripts/audit_scan.py` gate runs after implementation.
