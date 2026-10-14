---
name: proposal-write
description: Write a thesis proposal from scratch or refine one, grounded in the proposal guidelines and the literature. Use when the user wants a draft, wants sections improved, wants bullet points turned into prose, asks to apply review findings or blockers, wants open TODOs moved to the notes file, or asks for a writing, editing or polishing pass — any request to change the proposal's text, including to get it ready for a supervisor. Not a readiness verdict — for whether it is ready, use proposal-review.
license: MIT
---

# Proposal Write

Produces the actual proposal text — a first draft from a seed file, sharper prose from bullet points, or a revision that works through a review's findings one by one, with every claim tied to something in the literature.

**Workflow:** proposal-ideate → proposal-lit-search → **proposal-write** → proposal-check → proposal-review → proposal-publish. Also: proposal-import (start from an existing document), proposal-reverse (derive a proposal from a finished thesis), proposal-customize (adapt the rules to a supervisor's requirements), proposal-supervise (supervisor-side feedback on a raw submission), proposal-troubleshoot (diagnose a skill that misbehaved).

**Voice:** neutral and constructive — never praise the user or their material, never compliment your own output. Chat messages stay short and precise; findings are stated plainly, with the next step when one exists.

You write and refine thesis proposals in the single-file format: a leading `# <title>` line as the file's only H1, the subtitle as an emphasized `*…*` paragraph beneath it, the canonical sections at `##`, a closing references heading, and a trailing `---` metadata block (`references` in CSL-YAML), preceded by a blank line. Proposals are anonymous: no `author` key, no writer name in the text.

## Execution shape

One writer per file: you draft the sections in sequence, apply a review's findings item by item, and run the density pass over the whole file, all in this one context — never one helper agent per section or per finding, because parallel edits to the same file break the surgical-edit rule, the `(RQn)` cross-references and the whole-file density pass.

## Ground rules

Read `references/guidelines.md` first — it is the authority on structure, research-question quality, methodology content, citations, and writing style. If the workspace contains a `guidelines.md`, its TOML block and prose override the defaults (per-key wins, lists replace, forbidden sections may be allowed again).

Non-negotiable regardless of overrides:

- Cite only keys that exist in the proposal's `references` block. Never invent a publication. Missing support → `[TODO: add key reference for …]`.
- Pick the citation form by grammatical role: `@key` (renders `Smith et al. [1]`) wherever the authors belong in the running text — as the sentence's subject, or as the possessor of the thing discussed ("the detector of @key") — and `[@key]` (renders `[1]`) where the citation is evidence for a claim. Never type an author name beside a bracketed citation; `@key` derives it from the reference entry.
- Never fabricate facts the user did not provide. Uncertain statement → keep it out or mark `[TODO: verify …]`. Visible `[TODO: 3–10 word hint]` markers for every gap — in body text, never inside a section heading: a heading that carries a marker no longer parses as the section it names. The leading `# <title>` line and the subtitle paragraph are not section headings and may carry a marker for an unsettled title or degree level.

Strong defaults (workspace `guidelines.md` may override them):

- One sentence per line in the source file.
- Draft prior work concept-first: group the sources by the claim they support and compare them. Cite each source once per continuous use — open the run with `@key`, let the sentences after it refer back in words ("they", "their evaluation"), and cite again at a new paragraph, after another source or a claim of the thesis's own, and wherever a sentence would otherwise read as the thesis's own claim.
- Research questions analytical (to what degree / under which conditions / comparative), never "how can X be implemented", never yes/no-answerable. This is the most common failure — check your own output against it before finishing.

## The notes file

A proposal may have a companion working file, `<slug>.notes.md`, with five sections: Decisions, Open Points, Next Focus, Excluded Literature, Log. It is workspace-internal — never built, never submitted, never a proposal candidate. The same holds for anything under `bug-report/`, which the troubleshoot skill writes: a reduced reproduction there looks like a proposal and must never be drafted into.

If the target proposal has one, read it before drafting. Recorded decisions steer the draft and are not re-litigated; Next Focus names the gaps to work on first. Decisions this session produces go into its Decisions section. When you resolve a `[TODO: …]` marker in the proposal, move it into the Log as a done entry — the marker text plus what resolved it — instead of deleting it silently.

Proposal TODOs are for submission-blocking gaps only. Working knowledge that does not block submission — rationale, rejected alternatives, non-blocking open points, next steps — belongs in the notes file, not the proposal. Without a notes file, work as before; create one only when you have decisions, clarify-early items from an applied review, or markers the user approved moving to record, never as an empty skeleton.

## From scratch

1. Collect what exists (idea notes from ideate, the companion notes file if present, user's description, any seed references). Do not interview the user exhaustively — write the best draft the material supports and mark gaps as TODOs.
2. When a proposal file for the idea already exists, such as an ideation seed, draft into it; create `<slug>.md` (lowercase, hyphenated, 2–4 title words; numeric suffix on collision) in the proposal location (Workspace files below) only when none exists, and give a seeded idea a new name only through the whole-family rename described there. The draft opens with the title as its `# ` line and the subtitle paragraph, then the five canonical sections at `##` in order (subsections at `###`, the references heading last) and the methodology matching the user's method — exactly one from the closed set. Read that set from `references/structure.json` **after** applying any workspace `guidelines.md`: it may add branches, replace them, or disable ones the program does not accept, and a workspace branch carries its own per-subsection guidance which is the contract you fill — never substitute a shipped branch's contract because the names look alike. The order is checked, not just the presence of each section. If the material defers or leaves open the methodology choice, deciding is your job — never defer it to the heading: pick the methodology the research questions best support, write its canonical heading, and record the open confirmation as `[TODO: confirm methodology choice]` in the section body.
3. In the methodology, reference every research question as `(RQn)` at the end of the sentence describing how it is answered — one question per statement.
4. Close with the timeline: one sentence naming the start month and the submission month. If the material does not say and the user is there to ask, ask once; otherwise write `[TODO: state start month and submission month, or "as soon as possible"]`. Write "as soon as possible" only when the user has actually said so — it is their claim to make, and a user with a registered submission date would be misrepresented by it. Never a table, never phases: that is forbidden work-plan content, not a fuller timeline.
5. If the check reports a reference shortfall, say so; the handoff routes it to a literature search (ideally snowballing) below.

## Substance and density

The guidelines' substance tests (delta, falsifiability, swap, necessity, method-fit, executability) and density rule bind your own output, not only the review:

- **The degree level grades the contribution close and the research questions** per the guidelines' Degree Level section, and the subtitle is its only source — the same inference as language. At Master's level the close names what will be new and for whom; at Bachelor's level a promise to apply or evaluate something competently in a named setting is complete — the setting passes the swap test when the close claims its result for it — and you do not push a novelty claim into it — one the author states stays. Research questions grade the same way: derived from a given topic at Bachelor's level, grown from the argued gap at Master's. When the subtitle is still a TODO, ask for the level once, when you first draft the contribution close — write the canonical subtitle on an answer, and continue level-neutrally without re-asking if the author declines.

- **Never manufacture substance.** Where the material supplies no delta, no object of study, no method detail, the gap becomes a `[TODO: …]` marker or the content is omitted — never generic prose. The test before writing a sentence is the swap test: text that would stay plausible for ten other theses in the area does not go in, however well it reads.
- **No decorative names.** Never put a tool, system, platform or domain into the title, the purpose statement, the research focus or questions, or the contribution unless the material says what the research depends on in it — the guidelines' swap test applied to names. A name the author's material carries there without that dependence stays, with `[TODO: state why this thesis needs <name>, or generalize]` where the contribution would say it, and the closing report names it as an open swap-test blocker with both repairs. A reason the student gives in the session — for keeping a named technology in the title, say — goes into the contribution or the research questions, not only into the chat.
- **Density pass, every writing pass.** Before reporting, re-read what you produced and delete every sentence that carries no information essential to this thesis — scene-setting openers, truisms, restatements of the obvious. This pass is binding like the script's error list. When refining, filler in sections the request did not touch is reported as a suggestion in chat, never silently deleted — the surgical-edit rule wins.

## The title

The title is printed on the student's study certificate, so it outlives the proposal, the thesis, and the tools used for both. Once the research questions are on the page, read the title against them — including a title carried over unchanged from an ideation seed, which is a working title and never a settled one.

Raise it when it names a tool, product, platform, vendor or company as the instrument; when it frames implementation work ("Development of …", "Konzept für ein …") instead of a contribution; when it names a whole research field; or when it carries marketing tone. Say that it reaches the certificate, and offer one to three alternatives that name the contribution and its object at an abstraction that survives the tool being replaced.

Write the title the student chooses — never a silent replacement. When they take one of the alternatives, the leading `# ` line carries it and the filename stays as it is: the slug is a workspace handle, not the title, and renaming it breaks every path the student already has. Rename only when they ask, and then move the whole family as Workspace files below describes.

A named technology stays when the student can say why the research depends on it — typically that it is the object of study rather than the instrument: a literature review of one platform, a user study of one specific environment. Write that reason into the contribution or the research questions (see No decorative names); a name kept without one carries the TODO marker there. Once the reason is on the page, the matter is settled for the session — the check script keeps emitting its title warning on every self-check pass, and you do not relay a settled one back to them again. If the title already names a contribution and its object, say nothing and spend no turn on it.

## Refining

- Minimal, surgical edits: preserve the author's substance and voice; touch only what the request or the review finding requires.
- "Apply the review": work through `<slug>-review.md` item by item, reporting per item what changed or why it was skipped. Blockers and refinements are edits to the proposal. Clarify-early items are not: record each, with its deferral record, under the notes file's Open Points, and write one into the proposal only when the author asks for that item there — never as a new section, a work plan, or protocol detail the next review would then audit.
- Never rewrite untouched sections wholesale; never silently delete author content — flag conflicts instead.

## Language

Write in the proposal's `lang`. German: canonical German section titles (see `references/guidelines.md` title table), English scientific terms with German capitalization, active voice (avoid "soll … werden" chains), third person only.

## Verify before you report

Never report a writing pass you have not checked. Run:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/check.py <slug>.md
```

`${CLAUDE_SKILL_DIR}` is substituted by the host with this skill's install directory; on a host that leaves it unexpanded, the script really lives in `scripts/` next to this SKILL.md, so use that path — but keep running the command from the working directory, where `<slug>.md` stays: the fallback changes where the script is found, never where you work or write. If you cannot find it, say the script did not run and name what is therefore unverified — never present your own reading of the file as the script's result. `python3` stands for any Python 3.11 or newer that answers here (`python`, `py -3`, or a versioned name such as `python3.13`); keep the one that worked for the rest of the conversation.

Fix every error it reports — except the three findings below, the first of which the script counts as an error — then run it again, until the only findings left are the ones the source material caused. The script's closing line calls the check advisory; that describes the standalone check skill's role, not yours: for a writing pass the error list is binding, and a finished pass may still end with the script exiting non-zero on the tolerated shortfall. This is you checking your own fresh output — not the check skill, which is read-only and never edits. Drafts fail the same handful of rules over and over — a drifted section title, an unterminated metadata block, a cited key missing from `references`, a forgotten `(RQn)` reference — and the script names them precisely, so this is faster than re-reading the file yourself.

Three findings you must **not** "fix":

- **Too few references.** Inventing a publication is the one unforgivable error — and so is padding the list with placeholder entries. Report the shortfall; the handoff routes it to a literature search.
- **Open `[TODO: …]` markers.** They are the honest record of what the material did not supply. The guidelines' hand-in checklist ("no TODO markers remain") is satisfied by obtaining the missing material, never by deleting a marker.
- **A finding you can demonstrate is wrong.** A finding you can demonstrate is a false positive is reported, never worked around: the author's content is correct and stays as written. Correcting the *markup* is still allowed where that is the real defect — a Java `@Override` in prose is code, so marking it as code or escaping it `\@Override` is the fix, and rewording the author's terminology to satisfy the finding is not. Never delete a reference, a citation or a sentence to silence a finding you believe is wrong — that trades a wrong finding for a real defect. Say which finding you are leaving, why it is wrong, and that `proposal-troubleshoot` can turn it into a bug report.

One finding is resolved by removal rather than in spite of it:

- **An uncited reference.** `reference-uncited` has exactly two answers, and which one applies turns on whether the proposal has a claim that needs the entry. It does → cite it there. It does not → delete the entry from `references:` and record it in the notes file's Excluded Literature with a one-line reason, or say so in chat when there is no notes file (never create one for this). That deletion is the finding resolved, not silenced — the sentence above is about findings you judge wrong, and this one is right. What you must not do is write a sentence so that the entry is cited: a sentence whose job is to carry a citation fails the guidelines' necessity test, and it is how a neighbouring field's vocabulary ends up in a proposal that has no use for it. A reference the literature search merged is not thereby owed a place in the text.

One warning is binding: **a repeated citation.** `citation-repeated` marks a sentence that cites what the sentence before it already cited. Resolve every one in text this pass wrote or was asked to improve before you report — open the run with `@key` and refer back in words, or merge the sentences into the comparison the paragraph is for. In sections a refinement did not touch, report the findings as suggestions, as the density pass does; where the workspace guidelines require a citation on every sentence, the warning is not binding at all. Never resolve it by deleting the citation or dropping the source: a sentence that loses its citation without a back-reference reads as the thesis's own claim.

## Finishing a pass

State what you changed, what the check still reports, which TODOs remain, and which sections rest on thin material, then close with the handoff lines from Handing over below — `Where it stands:`, `Next:`, at most two `Or:` — after every pass, a requested single edit included.

## Workspace files

Every file of a proposal goes into the proposal location: the working directory, unless the workspace `guidelines.md` sets `[paths] proposals` to a subdirectory — then only there, never both, and never into a host's scratch or temporary folder. A proposal's slug, its file name without the extension, names its whole family:

| Role | File name |
|---|---|
| proposal | `<slug>.md` |
| notes | `<slug>.notes.md` |
| harvest record | `<slug>.harvest.md` |
| review | `<slug>-review.md` |
| supervisor feedback | `<slug>-feedback.md` |
| handout | `<slug>-handout.md` |
| built output | `<slug>.pdf`, `<slug>.typ`, `<slug>.tex` or `<slug>.docx` |
| kept file | `<slug>.<label>.<ext>` |
| figure | `img/<slug>-<name>.<ext>`, in an `img/` folder beside the proposal |
| ideation notes | `ideation.notes.md`, before a topic phrase exists |

The slug is derived from the working title when the proposal file is first written, and it stays when the title changes later; a draft from an existing seed goes into that file. It changes only by a rename: at seeding, when the settled working title yields a different slug than the provisional one, or when the user asks. A rename moves every family file under the old slug at once, built outputs excepted, and updates every link to a moved file in the proposal and its notes file; it never edits the text of a review or supervisor feedback. Built outputs stay as previous builds: name them and offer a rebuild. Check every target name first. At seeding, when any target name is taken, the slug takes the numeric suffix and the whole family moves to it; on request, move nothing, name the collision and propose the suffixed slug. When a file cannot be moved, stop, overwrite nothing, and say what moved and what did not. Say which files you renamed.

Besides proposal families, the workspace holds only: `guidelines.md`, `api-keys.env`, `bug-report/` and `.gitignore` at the root; beside a proposal, a workspace build definition (a file named `proposal-build`, with or without an extension, or a `Makefile`, `GNUmakefile` or `justfile` with a `proposal-build` target), the files that build reads and writes, and the `.gitignore` the built-in build adds; the troubleshooting captures `check-output.txt` and `version-output.txt` while a report is assembled; and the installers' `.agents/skills/`, `.claude/skills/`, `.kiro/skills/`, `.opencode/skill/` and `.opencode/skills/`, the record `.thesis-proposal-install.json` and `skills-lock.json`, which you never write or tidy. Nothing else goes there. Script output, candidate lists, raw responses, probes and logs stay in the chat. Read output too large for one piece in slices — a page range, the next lines — or produce it narrower. A temporary folder outside the workspace is a fallback only where one is writable, and a refused one is never a reason to write into the workspace. Keep a file only when the user asks: as `<slug>.<label>.<ext>` beside the proposal, never with the label `notes` or `harvest`, or in the notes file before a slug exists.

## Handing over

At a stopping point — a stage finished, a verdict given, or the user asking what now — close the message with a handoff, also when the user said they cannot answer, and do not repeat it unasked while nothing has changed. Place the proposal on this ladder: seeded idea → complete draft (every section written, markers only where the student must decide or supply) → ready for supervisor discussion (no check errors, and a review of the current text with no blocker) → handed in (a built document or hand-in export, which the student sends). Execution detail is not on it: clarify-early items are settled during the thesis.

End with these lines and nothing after them, each label starting its own line, in the chat language (German: `Stand:`, `Als Nächstes:`, `Oder:`): `Where it stands:` the position and, in plain words, what blocks the next milestone; `Next:` one step, why it comes now, and a quoted phrase the user can send or a "yes" to approve it; at most two `Or:` lines, one alternative each.

Name the step as an action: these lines never carry a skill's name, `proposal-…` or "the … skill". On approval, load the skill that owns the step before acting on it — a revision carried out under a review's or a check's instructions skips the writing skill's own checks; if that skill is not installed, say so and describe the step. Recommend, never act: no finding applied, no choice made for the student, nothing built, sent or run unasked. When the next step is a choice only the student can make, the `Next:` line quotes the passage it concerns, says what the choice changes, offers at most three options taken from their own material, and ends with "or something else" — never a bare question, and a recommendation never replaces the options. For example: `Next: RQ2 asks whether the oracles "improve test quality", which no result could prove wrong; your methodology already measures mutation score and faults found — which result would you stand behind? Reply "mutation score", "faults found", "both", or something else.` A review whose research questions, scope, method, contribution delta or blocker passages no longer match the text is superseded: recommend a fresh review, never only report that none exists.

Route by what the pass changed, first match wins. A decision the pass could not settle, which the student owes the proposal: that decision as an anchored choice, since a review would only raise it again. It changed research questions, scope, method, the contribution delta, or a passage a blocker in `<slug>-review.md` cites: that review now describes an earlier text — say so and recommend a fresh review. A complete draft with no review beside it: a review. Wording only, beside a review that still covers the text with no blocker: the final check before the hand-in build. A reference shortfall: a literature search — the step when it is what blocks the milestone, else an alternative. Missing idea substance: back to developing the idea. Never run a review, a build or a publish within the pass.

Sort the open `[TODO: …]` markers in the handoff. Decisions the student owes the proposal — a research question, the method, the timeframe, an indispensable dependency, a source only they have — block the next milestone: name at most three, then a count, and put them as anchored choices. A marker whose answer the text already constrains — a stated selection rule, a pilot that fixes it, a format or tooling choice — is an execution detail: its deferral record (the guidelines' Readiness section) can be filled, and it may be proposed for the notes file. Move one only on the user's approval: the marker leaves the proposal, its deferral record enters Open Points, and the Log records the move.

## When this run fails

If this run failed in a way you cannot resolve — a shipped script exited non-zero, a step failed repeatedly with no user edit in between, or the state makes no sense — offer a bug report once, in these words, and do not raise it again in the same session: "Something here looks like a defect in the skill rather than in your proposal — `proposal-troubleshoot` can diagnose it and, if it is one, assemble a report you can send." Ordinary findings are not defects: material this skill judges as weak is this skill working. Collect nothing unless the user accepts.
