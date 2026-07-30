## Context

See proposal.md — Why. The relevant machinery today:

- `openspec/specs/proposal-file-format/spec.md` names five canonical keys, `author` among them, and `tests/unit/test_format_prose_drift.py` enforces that list across every format-describing SKILL.md (`CANONICAL_KEYS`, plus a discovery rule "names two or more of the five").
- `skills/proposal-ideate/SKILL.md` seeds `author` and writes `[TODO: add author]` when the name is unknown.
- `skills/proposal-publish/templates/proposal.typ:31` renders `$if(author)$…$endif$` in the title block — that is how the placeholder reached a PDF.
- `skills/proposal-check/scripts/check.py` parses only the fenced TOML block of a workspace `guidelines.md` (`load_overrides`); prose in that file is invisible to it.
- Eight fixtures declare `author:`; each fixture directory ships an `expected.json` oracle calibrated against `check.py`.

## Goals / Non-Goals

**Goals:**

- One place decides the metadata contract (the spec + the drift test), and `author` is not in it.
- The reported defect — a placeholder rendered on a title page — is impossible via the tool's own output path.
- A program that demands a named title page is still servable, without a second override mechanism.

**Non-Goals:**

- Detecting writer names in body prose. Left to the agent review pass.
- Any change to `skills/proposal-publish/`. The template's conditional author block is the override path; leaving it alone is the point.
- Retro-fixing proposals in user workspaces. The check warning tells them; nothing rewrites their files.

## Decisions

**Remove `author` from the contract rather than keep it and suppress rendering.** A key that exists is a key that gets filled in, exported, and shared — including into agent transcripts. Removing it from the contract, from ideate's seeding, and from every skill's format prose means the name never enters the file in the first place. Alternative considered: keep the key required and strip it at publish time — rejected, it leaves the name in the `.md` file, which is the artifact users actually pass around.

**Warn on the key, never fail.** `author:` becomes a warning in the existing personal-data warning class. Alternative considered: a hard mechanical error — rejected, every pre-existing and imported file would fail check until hand-edited, and the skill's own spec says checks are advisory and never blocking.

**The override is prose, so the warning always fires.** A workspace `guidelines.md` may state that the program requires a named title page; the user then sets `author` deliberately and publish renders it. Because `check.py` reads only the TOML block, it cannot know this, so the warning fires anyway — and its wording names the exception (`…remove it unless your program requires a named cover page`) so an override user reads it as expected noise rather than a defect. Alternatives considered: a new `author_allowed` TOML key — rejected, guidance-model draws a deliberate formalization boundary and this case has no user behind it yet; suppressing the warning whenever any `guidelines.md` exists — rejected, a workspace overriding only `page_limit` would silently lose the anonymity warning.

**Publish is not touched.** It renders whatever `author` holds. The defect dies upstream, because nothing writes the key anymore. Alternative considered: have publish drop `[TODO: …]`-shaped author values — rejected as a second, value-shaped rule in a place that otherwise has no opinion; the consequence, accepted deliberately, is that a hand-typed placeholder still prints and only the check warning catches it.

**No name regex in `check.py`.** Person names in prose are indistinguishable from cited researchers, institutions, and product names at regex precision. The rule stays on the metadata key; body-level names are a semantic concern for the review skill, listed under forbidden content.

**One fixture keeps its author on purpose.** `f15-format-broken` already exists to be broken and already carries `Erika Musterfrau`; it becomes the tripwire for the new warning. Every other fixture loses the key. This satisfies the testing-harness rule that each mechanical rule is tripped at least once and passed at least once, without inventing a fixture.

**Sequencing against `render-author-in-text-citations`.** That change is 10/28 tasks in and its delta MODIFIES the same `skill-check` requirement ("Warning-class pattern checks"). Implementation of this change starts only after it is archived; the `skill-check` delta here is then re-baselined onto the archived text (which will have gained the authorless-`@key` warning) before any code is edited. The two changes also use "author" in opposite senses — cited researcher vs. proposal writer — in the same files; running them concurrently invites exactly the wrong edit.

## Risks / Trade-offs

- **A hand-typed `[TODO: add author]` still reaches the title page** (publish untouched) → the check warning fires on the key regardless of its value, and ideate no longer produces the placeholder, so the only route left is a user typing it themselves.
- **Override users see a permanent benign warning** → wording names their case explicitly; checks never block.
- **`skill-check` delta goes stale while the citation change lands** → tasks.md gates implementation on the archive and makes re-baselining the first task, not a discovered surprise.
- **Existing user proposals silently lose their name from the next build** → they do not: nothing rewrites user files, and publish still renders an `author` a user already set. Only newly created proposals are anonymous by construction.
- **Drift test discovery rule is count-based** ("two or more of the five keys") → dropping to four keys narrows the discovery window; `test_discovery_finds_known_describers` already pins the three expected describers, so a skill falling out of discovery fails loudly.

## Migration Plan

No data migration. Existing proposals keep building; the check warning is the migration prompt. Rollback is reverting the change — the removed key stays valid YAML throughout, so no file written under either regime becomes unreadable under the other.
