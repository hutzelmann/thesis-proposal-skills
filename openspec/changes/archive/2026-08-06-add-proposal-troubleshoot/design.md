## Context

See proposal.md — Why. Design-relevant constraints of the environment the skill runs in:

- The skill executes in the user's proposal folder. It cannot read this repository, has no network guarantee, and its scripts are limited to stock Python ≥ 3.11 standard library, cross-platform.
- The installed layout comes from the skills.sh CLI: skills at `.agents/skills/proposal-*/` with per-agent symlinks (`.claude/skills/…`), plus a `skills-lock.json` at the workspace root. That lock records `source`, `sourceType`, `skillPath` and a `computedHash` per skill. It carries no commit SHA, no ref, no timestamp, and `skillPath` points at `SKILL.md` only — shipped scripts and reference data are outside it. `computedHash` is produced by an algorithm we do not control and cannot reproduce, so it is corroboration, not identification.
- `proposal-check` and `proposal-review` diagnose read-only, and `proposal-check` proves it by comparing a content digest taken before and after its run. Any mechanism that writes during their runs breaks that proof.
- `proposal-check` auto-picks its target as "exactly one markdown file ending in a `---` metadata block", and notes files are already excluded from that selection.

## Goals / Non-Goals

**Goals:**

- A report a maintainer can act on without a round-trip: which revision, which environment, what happened, and where the agent's word is the only evidence.
- A funnel that answers the majority of problems without producing a report at all.
- Disclosure the user controls and sees before it is written.
- Identification that works on installs made before this change ships.

**Non-Goals:**

- Reading harness-native session transcripts. Per-harness locations and formats, large files, and unrelated conversation needing redaction — rejected in favour of the agent's own account plus measured artifacts.
- A continuous trace file written by the skills. It cannot exist for the read-only skills without breaking their digest proof.
- Any outbound path: no `gh issue create`, no HTTP POST, no mailto.
- Version data shipped inside the skills. See Decisions.
- Closing the gap between the published snapshot and `main`. That is the rewrite already in flight.

## Decisions

### Identify the install from git blob hashes, not a shipped manifest

Rejected first design: a generated `references/manifest.json` per skill holding sha256 of its own files, recomputed by the collector to detect drift. Fatal ordering flaw — it exists only in installs made *after* it ships, and the installs that will be reported are the ones already out there.

Chosen instead: the collector hashes every installed skill file and the maintainer resolves the hashes against git history. To make that resolution a lookup rather than a search, the collector emits **git blob hashes** — `sha1("blob " + len + "\0" + content)` — which is what `git ls-tree` already stores. Fourteen lines of stdlib, and then `git log --all --find-object=<sha>` names the commits containing that exact file. Alternative considered: sha256 plus a full-history content walk, which is correct but O(commits × files) and needs a cache.

Because git stores LF while a Windows checkout may hold CRLF, the collector emits the blob hash of the bytes as found **and** of the LF-normalized bytes, plus a sha256 as a provider-independent fallback. Three cheap hashes beat one ambiguous mismatch.

`skills-lock.json` is copied in verbatim regardless: it is small, holds no personal data, and proves source repository and install method — the two things hashes cannot show.

### Triage data ships as vendored JSON, generated from the harness

The model rung needs the support verdicts, and the skill cannot reach this repository. `harness/support.py` gains a JSON export; the result lands in `shared/model-support.json` and `scripts/sync_shared.py` materializes it into `skills/proposal-troubleshoot/references/model-support.json` under the existing generated-copy and drift-check machinery.

The export must distinguish untested from failing, because a skill reading a blank cell as a pass would clear a model nothing is known about. Model identity arrives self-reported by the agent as something like `claude-opus-5` while roster keys are `anthropic/claude-opus-5`, so matching is by suffix, and a non-match yields "unevaluated", never "supported".

### Bundle layout, and keeping it out of the skills' way

```
bug-report/
  report.md            # triage verdict, replay, expected vs actual, tagged env block
  skills-lock.json     # verbatim copy
  hashes.txt           # per-file: path, git blob (raw), git blob (LF), sha256
  artifacts/           # notes-file Log excerpt, guidelines.md, captured script output
  repro/               # conditional
    input.md
    command.txt
```

`repro/input.md` is a reduced *proposal* and therefore carries a `---` metadata block, which makes it a candidate for the same auto-pick logic that selects a proposal to check. It must be excluded from draft selection by the same mechanism that already excludes notes files. Without that, generating a report changes which file the next check runs against.

Writing is confined to `bug-report/`, which is what lets a read-only skill offer a report without breaching its mandate: the offer is made, the user accepts, and the collector touches nothing the read-only skill was examining. An existing `bug-report/` is never overwritten without asking.

### Report format: tag every field, two tags only

```
[measured]      python 3.12.4 · linux · typst 0.13 · pandoc absent
[measured]      proposal-check/scripts/check.py exit 0, digest 9b2c… → 9b2c… (unchanged)
[self-reported] model: claude-haiku-4.5 · harness: Claude Code CLI
[self-reported] replay: user asked for a draft; I wrote a Timeline table
```

Two tags, not a confidence scale. The distinction that matters is whether a script established the fact or the subject of the report asserted it; finer gradations invite the agent to grade its own testimony.

### Redaction implemented as levels over one collector

One collector with a `--level {minimal,structure,full}` flag, default `minimal`, and a `--dry-run` that prints what would be included without writing. The skill runs `--dry-run` first and shows the output — that is how "state what this level includes and what the next adds" is satisfied mechanically rather than by the agent's promise. `full` reuses the personal-data strip rules already applied to proposals.

### Offer line: one pinned sentence, position unconstrained

Failure paths differ per skill, so the enforceable invariant is that each `SKILL.md` contains the offer sentence verbatim exactly once. Candidate wording, to be pinned like the voice block:

> If this looks like a defect in the skill rather than in your proposal, the `proposal-troubleshoot` skill can diagnose it and, if it is one, assemble a report you can send.

A new offline test asserts presence-exactly-once across all nine files. Not folded into the header-pattern test, which governs the opening blocks and would have to grow a positional rule it should not own.

## Risks / Trade-offs

- **Agent misreports its own model, or does not know it** → the field is tagged `[self-reported]`; the model rung yields "unevaluated" rather than a verdict when the id matches no roster entry.
- **Offer line fires on ordinary findings, training users to ignore it** → the most damaging failure mode here. Negative eval coverage: a diagnostic run against a fixture whose oracle expects findings fails if an offer appears.
- **Nine offer sites is nine chances for drift** → presence-exactly-once test, and the sentence is pinned.
- **`repro/input.md` hijacks proposal auto-pick** → excluded from draft selection alongside notes files; covered by a test, since this is a silent failure that only shows up as a confusing later check.
- **User sends `full` level without understanding it** → default is `minimal`, `--dry-run` output is shown before any write, and the level's content is stated in the skill's own words rather than only in a flag name.
- **Bundle lingers in the proposal folder** → the report states that the directory can be deleted once sent; the skill does not delete it, because a user may still be composing the issue.
- **`computedHash` semantics could change upstream** → nothing depends on it; it is copied verbatim as corroboration only.
- **Ninth skill widens the surface each new skill must update** → already the accepted cost of the workflow-line invariant; the "Skill added to the set" scenario in `skill-packaging` covers it, so no delta collides with the change in flight.

## Migration Plan

The workflow line is byte-identical across the set and offline-enforced, so the ninth skill, the updated line in the eight existing files, the pinned mandate for the new skill, and the header-pattern test's expectation of nine skills all land in one commit. A partial landing fails the offline suite by design.

No user-side migration: the skill is additive, and identification deliberately requires nothing new in an install.
