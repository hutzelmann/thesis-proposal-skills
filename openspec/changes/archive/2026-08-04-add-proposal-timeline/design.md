## Context

See `proposal.md` — Why. What shapes the approach is the machinery already in place.

`shared/structure.json` holds the mechanically checkable skeleton and is materialized into six skills by `scripts/sync_shared.py`; `check.py` lives once under `proposal-check/scripts/` and is vendored into `proposal-write` and `proposal-import`. Three properties of the existing check decide most of this design:

- Forbidden headings are matched by **substring**, case-folded (`check.py:220`). `timeline` therefore matches a heading named `Timeline`, so a canonical title and a forbidden pattern of the same word cannot coexist.
- `headings()` returns `(level, text)` pairs in **document order** (`check.py:137-141`), so order verification needs no new parsing.
- `section_text()` stops at the next heading of the **same or shallower** level (`check.py:353-362`), so a `##` subsection nested under `# Timeline` is part of the timeline's own text and is visible to a body guard.

The repo also carries a rule that the machine-readable data stays mechanical: semantic judgements are prose for agents, never encoded as check data (`guidance-model` — Formalization boundary). That rule decides where the timeline's *content* check lives.

## Goals / Non-Goals

**Goals:**

- One coarse timeline sentence becomes part of the canonical structure, enforced like the other sections.
- The Gantt chart stays excluded — with at least as much mechanical force as the forbidden pattern that is being deleted.
- A program that genuinely mandates a phase table keeps a supported path.
- Every artifact that describes the structure agrees with the check, at every commit boundary.

**Non-Goals:**

- No template sentence. Phrasing stays the writer's, in both languages.
- No date parsing, no month vocabulary, no semester-label table in `structure.json`.
- `proposal-review` and `proposal-publish` are untouched: review refuses structural findings by charter, and a fifth heading renders with no template change.

## Decisions

### A section, not a metadata key or a bare sentence

Alternatives were a `start:`/`submission:` pair in the trailing metadata block, and one unheaded sentence at the end of the methodology. The metadata pair is the most machine-checkable option and *cannot* grow into a Gantt chart, which is a real advantage; the unheaded sentence needs no change to the forbidden list at all. Both were rejected because the timeline has to be visible to a supervisor skimming the document and describable as part of the structure in every README and skill page — which is the deliverable here. An unheaded sentence in particular can only be checked by prose regex, which is weaker than a heading check, not stronger.

Consequence accepted: `timeline` and `zeitplan` leave `forbidden_heading_patterns`, and the barrier they provided must be rebuilt (below).

### The guard is split: structure is mechanical, meaning is not

The deleted patterns blocked Gantt charts by blocking the heading. With the heading now canonical, the barrier moves into the section body, and splits in two.

**Mechanical, in `check.py`, error severity:** within the timeline section, no table row, no list item, no subsection, at most three non-empty lines. All four are language-agnostic and cannot false-fire on a legitimate coarse timeline. The three-line limit leans on an existing convention rather than inventing a metric — `guidelines.md` already mandates one sentence per line in the source file, so a non-empty-line count is a sentence count.

**Semantic, in the `proposal-check` agent pass:** whether the section actually names a timeframe, and whether a work plan arrived in a form the script cannot see. A positive format check in `check.py` was considered and rejected: matching real student phrasing (`SoSe 2027`, `WS 2026/27`, `Q3 2027`, "winter semester", month names in two languages) means enumerating a date vocabulary in `structure.json`, which is precisely the semantic encoding the formalization boundary forbids — and it would false-error on every phrasing not enumerated. The agent pass has no such limit, and it is the only layer that can see a Gantt chart **pasted as an image**, which no regex reaches.

The two layers are complementary, not redundant: the script catches the common case cheaply and deterministically; the agent catches what the script structurally cannot.

### Order enforcement piggybacks on the existing heading list

Order has never been checked. It becomes an error now because a five-section structure with a designated final section is meaningless if any permutation passes, and because `sections.order` should mean what its name says.

Implementation is an index comparison over `headings()` output — the canonical titles found in the document, in document order, compared against the expected sequence. Methodology is matched by its title **prefix**, since its heading is a template (`Methodology for Research: {methodology}`).

Expected order comes from `sections.order` by default. Under a workspace `required_sections` override it comes from **that list's own order** — the list is already ordered, so no third key is introduced. This matters because `check.py:198` already disables the methodology checks entirely when `required_sections` is overridden; order under an override therefore concerns only the override's own list, which keeps the two behaviours consistent.

A separate `section_order` key was rejected: two lists that must agree is a bug source, and nothing would stop them contradicting each other.

### `timeline_detail` is an explicit key, not an inference

Un-forbidding a heading used to be the escape hatch for a supervisor who wanted a work plan. A body guard living in code has no such hatch, so one is added: `timeline_detail = "simple" | "detailed"`, default `simple`. Under `detailed` the body guard is off and `milestones`, `work plan`, `workplan`, `arbeitsplan`, `meilensteine`, `gantt`, `workpackage`, `arbeitspaket` drop out of the forbidden list.

The alternative — relax the guard automatically when the workspace un-forbids `milestones` — was rejected as action-at-a-distance: nothing in that TOML block would say "tables are now allowed under Timeline", and un-forbidding a heading to change an unrelated body check is not discoverable. `tomllib` reads a string key with no new parsing, so the cost is one lookup.

### Forbidden-list surgery, and why it is safe

Remove `timeline`, `zeitplan`. Add `gantt`, `workpackage`, `arbeitspaket`. Keep `schedule`, `time plan`, `work plan`, `workplan`, `milestones`, `arbeitsplan`, `meilensteine`.

Because matching is substring, the canonical titles must not contain any surviving pattern. They do not: neither `Timeline` nor `Zeitplan` contains any of the ten kept-or-added patterns (`time plan` carries a space; `arbeitsplan` and `zeitplan` differ in their stems). Keeping `schedule` and `time plan` is deliberate — a student who writes `# Schedule` gets a forbidden-heading error that points them at the canonical title, which is better than silently accepting a rival heading.

### Import distills rather than strips

Import currently deletes timelines. It now reads the first and last month out of a source Gantt or phase table, writes them as the coarse sentence, drops the phase detail, and reports both facts in the removal note. This follows the skill's existing philosophy — map source content onto canonical sections, mark what is missing, never invent — and avoids discarding information the source actually contained. When nothing is recoverable the section gets a TODO marker, never an as-soon-as-possible statement: that is a claim only the writer can make, and a writer with a registered deadline would be misrepresented by it.

Import also gains an explicit reorder step, because order is now an error and free-form sources rarely arrive in canonical order.

### One change, demo re-run last

The change is large, and splitting it is tempting. It is not split, for one reason: between two commits, `main` would ship a README stating "the defaults forbid timelines" while the defaults require one. The repository would document the opposite of what it enforces.

The demo re-run is the final task rather than an omitted one. `docs/demo/README.md` binds the README excerpts to real session output with `harvest.log` as the audit trail, and block 3 quotes `proposal-check` reporting "no timelines" — a quote this change falsifies. Hand-editing it would put invented agent output in the repository's most public file. So the session is re-run on the same synthetic drift topic **after** the implementation lands, and block 3 is re-condensed from the genuine output.

### Fixture strategy: clean fixtures adapt, broken fixtures do not

`f00-clean-en`, `f12-clean-de`, and `f19-drift-alert-validity` gain a real timeline section — they must, or they stop being clean. The roughly seventeen broken fixtures keep their current bodies and each oracle gains one missing-section error. That is the realistic outcome: a proposal written elsewhere would not carry our canonical heading, and these fixtures exist to look like proposals found in the wild.

One new fixture covers the body guard — a phase table under a legitimate `# Timeline` heading — because the guard is the mechanism replacing the deleted patterns and would otherwise ship with no test at all.

`w02-override-workspace` is repurposed rather than deleted. Its premise ("my supervisor requires a timeline section") is now the default, but its *role* — the oracle for override precedence — is still needed, and `timeline_detail = "detailed"` is the natural successor: it exercises the new key and the guard's off-switch in one fixture.

## Risks / Trade-offs

- **A worked example used in roughly eight places disappears.** "Supervisor wants a timeline" is the canonical override demonstration in `proposal-customize/SKILL.md` (three sites, one of them the user-facing skills.sh description), `README.md`, `docs/getting-started.md`, and three spec scenarios. → Replaced everywhere by "supervisor wants a detailed work plan", which keeps the sentences timeline-shaped, flips only the adjective, and documents `timeline_detail` in the same breath.
- **A metered eval task asserts the old default.** `harness/skill_evals.py:421-434` scores `"timeline still forbidden"` as a failure. Left alone it would fail permanently and silently misreport the customize skill. → Rewritten to the detailed-work-plan premise, and run once to confirm; `harness/sources.py:22` carries a matching synthetic heading.
- **Order enforcement is scope beyond the timeline itself** and will newly fail proposals that passed yesterday. → It is confined to canonical titles, so a document with extra or unrecognised headings is unaffected; imports get the reorder step; and check is advisory by charter, so nothing is blocked.
- **The three-line limit is mechanically weak against a comma-spliced single line.** A student can cram a phase narrative onto one line and pass the script. → Accepted: the agent pass reads the content, and tightening to one line would push writers toward exactly that comma-splicing.
- **Every broken fixture oracle gains an identical error line**, slightly diluting what each fixture discriminates. → Accepted as the honest outcome; the alternative is editing twenty fixtures to carry a heading their real-world counterparts would not have.
- **`sync_shared.py` drift.** Seven generated copies plus two vendored `check.py` copies must be regenerated. → The pre-commit hook re-materializes and stages them, and CI's `--check` catches a bypassed hook.

## Migration Plan

No data migration: proposals are user-side files this repository never touches. Existing proposals in a user's workspace will report one new error (missing timeline) and possibly an ordering error on their next check. That is the intended signal, and check is advisory — nothing breaks, nothing is rewritten without the user asking.

Task ordering is the deployment plan: spec deltas → guidance data and sync → check script → skills → fixtures → harness → docs → demo re-run → verification. Rollback is a single revert, since it is one commit.
