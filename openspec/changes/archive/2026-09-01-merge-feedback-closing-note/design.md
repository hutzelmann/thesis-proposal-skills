## Context

See proposal.md — Why. Two constraints shape everything below.

The delivery channel renders no markup. `skills/proposal-supervise/SKILL.md` already says
the professor pastes the feedback as text into an email reply or a learning platform's
feedback field, but the shipped snippet is a markdown blockquote with a bold run-in. Every
character of markup in that snippet reaches the student literally.

The disclosure is the one block in the feedback whose wording is constrained by a rule
about what it must *not* say — no claim that the assistant follows the program's
guidelines — and it is currently generated per run. Nothing in the repository checks the
produced wording, so the constraint lives only in the skill body.

Two files hold the moving parts: `skills/proposal-supervise/references/getting-started.md`
(the snippet, hand-maintained, not a `sync_shared.py` destination) and `SKILL.md` items 5
and 6 in the curated-feedback list. `docs/getting-started.md` is an unrelated onboarding
document and is not in scope.

## Goals / Non-Goals

**Goals:**

- One closing paragraph per language, verbatim in the reference file, quoted whole.
- Markup-free output for a markup-free channel.
- Gates that fail when either property regresses — in the shipped file (offline) and in a
  produced feedback (metered).

**Non-Goals:**

- Converting the rest of the feedback to plain text. The curated points keep their markdown
  numbering; `1.` degrades gracefully in a plain-text box, `>` and `**` do not.
- Adding headings anywhere in the feedback. The decision below is that the feedback carries
  none at all.
- Any change to the other nine skills, or to how `sync_shared.py` works — the snippet stays
  hand-maintained in the one skill that uses it.

## Decisions

**Merge into a single verbatim paragraph rather than a headline over two blocks.**
Alternative considered: keep the disclosure agent-authored under a shared headline. Rejected
because the overclaim path the "no guideline-compliance claim" rule exists to block *is*
free-text generation, and a headline would be the only heading in a document that has none.
Fixing the text removes the failure mode instead of testing for it. The cost is that the
disclosure can no longer flex per tier, which it should never have done: the disclosure says
who was involved, not how the proposal fared.

**Run-in label, not a headline.** A headline over a merged block is the natural shape, but
every markdown form of one — `##`, `**Bold**`, an underlined line — pastes as literal
characters into the target channel, which is the defect being fixed. A plain unmarked line
above a paragraph is structurally invisible. So the label runs into the paragraph: `Note:`
in English, `Hinweis:` in German. This is why the paragraph must not be split — a run-in
label reaches only the paragraph it opens, and a second paragraph would float unlabelled.
The spec states the single-paragraph rule for that reason, and the L0 guard enforces it.

**An availability bridge, not an invitation.** The two halves are joined by "tools of the
same kind are freely available", which states availability. The obvious alternative — "if
you want to work the same way, …" — prescribes the student's next step, which the closing
note is forbidden to do. Without a bridge the merge is only the deletion of a paragraph
break, and nothing stops a later editor splitting it back.

**German coins "Rückmeldung" for the artifact.** The repository has no German word for the
feedback today; the German snippet avoids naming it. The disclosure's whole job is to make
unambiguous *what* was AI-prepared, and "dieses Textes" does not. "Rückmeldung" is the
standard German university term and joins "Exposé" as a pinned per-language term, guarded by
the same L0 test file.

**Rename to `closing-note.md`.** The file no longer holds a getting-started blurb. The
rename is mechanical — one path constant in `tests/unit/test_bilingual_terminology.py`, one
path in `SKILL.md`, and the spec's noun for it, which had to change anyway once "SHALL close
with a getting-started blurb" stopped describing what closes the feedback. It also removes
the collision with `docs/getting-started.md`.

**Two gates, at different levels, because they catch different regressions.** The L0 guard
reads the shipped file: one paragraph per section, no `>`/`#`/`-`/`*` line starts, no
emphasis markers, the required run-in labels, and "Rückmeldung" in the German section. It is
offline, free, and catches the markup coming back. It cannot catch a model paraphrasing the
snippet instead of quoting it, which is the failure the verbatim decision was made to
prevent — so `verdict_supervise_closing` reads the produced feedback and asserts the
language-matching section survives verbatim. Following repo convention, the verdict function
lives in `harness/l1_checks.py`, the scorer in `harness/skill_evals.py` is a thin adapter,
and the verdict gets its own L0 test; the scorer name is pinned in
`tests/unit/test_eval_wiring.py` because the model-support classifier reads it.

**Verbatim comparison normalizes whitespace only.** The reference file wraps its paragraphs
for readability; a feedback file may wrap differently or not at all. The verdict collapses
runs of whitespace on both sides before comparing, so line wrapping is not a failure but a
changed word is.

## Risks / Trade-offs

- **The closing-note verdict only runs on metered eval runs** → the L0 guard covers the
  shipped file for free, and the verdict's own L0 test exercises the comparison logic
  offline against pass, paraphrase, and wrong-language inputs. The metered run adds
  evidence, not the first line of defence.
- **A stricter markup ban could false-positive** → the guard is scoped to the closing note's
  two sections only, never to the feedback as a whole, precisely because the curated points
  legitimately use markdown numbering.
- **`Rückmeldung` becomes a term every future German string must match** → it is pinned in
  the existing bilingual-terminology test file, next to the `Exposé` pins, so the next
  German surface inherits the guard rather than rediscovering the question.
- **Whitespace-normalized comparison hides a genuine formatting change** → acceptable: the
  formatting property is guarded at L0 on the source file, where the authoritative bytes
  live. The verdict's job is word-level fidelity.
- **The rename breaks any external reference to `getting-started.md` inside the skill**
  → the grep across `skills/`, `tests/`, `harness/`, `scripts/`, `docs/`, and
  `openspec/specs/` found four in-scope references and no others; all four are in the task
  list.
