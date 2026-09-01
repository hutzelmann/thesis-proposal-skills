## Why

The supervisor pastes `<slug>-feedback.md` as plain text into an email reply or a learning
platform's feedback field, where no markdown is rendered. The feedback's last two blocks
defeat that: the disclosure is agent-authored prose whose scope is constrained only by a
rule nothing checks, and the getting-started blurb ships as a blockquote with a bold
run-in, so the student receives the literal characters `> **Continuing from here.**`. The
two blocks also say related things — this text was AI-prepared, and tools of the same kind
are available to you — while sitting in separate paragraphs that read as unrelated.

## What Changes

- The disclosure and the getting-started blurb merge into **one closing paragraph**, held
  verbatim in the skill's reference file and quoted whole. The disclosure is no longer
  written fresh per run, which removes the overclaim path the "no guideline-compliance
  claim" rule exists to block.
- The closing paragraph carries **no markdown syntax at all**: no blockquote, no bold, no
  heading. It opens with a plain run-in label — `Note:` in English, `Hinweis:` in German —
  and runs as a single paragraph, so it survives the plain-text channel the skill documents.
- The two halves are joined by an availability bridge ("tools of the same kind"), which
  states availability without prescribing the student's next step.
- The German text names the artifact **Rückmeldung**, pinning the German term for the
  feedback the way *Exposé* is pinned for the proposal document.
- `skills/proposal-supervise/references/getting-started.md` is renamed to
  `closing-note.md`, since the file now holds the whole closing paragraph rather than a
  getting-started blurb. This also removes the name collision with the unrelated
  `docs/getting-started.md` onboarding document.
- Two gates land with the change: an L0 guard on the reference file's shape (one paragraph
  per language, no markdown-syntax line starts, the required run-in labels and terms), and
  a `verdict_supervise_closing` L1 verdict asserting the produced feedback carries the
  closing paragraph verbatim for its language.

## Capabilities

### New Capabilities

<!-- none -->

### Modified Capabilities

- `skill-supervise`: the disclosure and getting-started blurb become one verbatim
  plain-text closing paragraph with a run-in label; the shared snippet is renamed and its
  minimality constraint is restated for the merged form.
- `testing-harness`: the bilingual-terminology guard points at the renamed file; a new L0
  guard covers the closing note's shape; a new supervise verdict scores the closing
  paragraph's verbatim survival into the feedback.

## Impact

- `skills/proposal-supervise/references/getting-started.md` → `closing-note.md`, rewritten.
- `skills/proposal-supervise/SKILL.md`: curated-feedback items 5 and 6 collapse into one.
- `openspec/specs/skill-supervise/spec.md`, `openspec/specs/testing-harness/spec.md`.
- `tests/unit/test_bilingual_terminology.py` (path constant), plus a new L0 test for the
  closing note's shape.
- `harness/l1_checks.py` (new verdict + aggregate), `harness/skill_evals.py` (scorer),
  `tests/unit/test_eval_wiring.py` (scorer-name pin),
  `tests/unit/test_supervise_verdicts.py` (L0 coverage for the new verdict).
- `skills/proposal-supervise/evals/evals.json` regenerated from the harness.
- Not affected: `docs/getting-started.md`, the curated points list (which keeps its
  markdown numbering), and the other nine skills.
