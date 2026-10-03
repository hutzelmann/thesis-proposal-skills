# Proposal

## Why

A proposal shown for illustration cited the same source on three to five consecutive sentences throughout its background and state of the art (`… [4]. … [4]. … [4]. … [5]. … [5]. … [5, 7].`). Scientific practice treats this as overcitation, not as an error. APA 7 §8.1 names repeating "the same citation in every sentence when the source and topic have not changed" as overcitation. German university guides call it "klobig" (FU Berlin), advise against it "nach jedem Satz" (TUM), or call it "unschön (aber nicht falsch)" (TH Nürnberg). The same sources reject the naive cure as well. Deleting the repeats so that one bracket closes a paragraph leaves the reach of the citation unclear, which is the "Bauernopfer" category of German plagiarism taxonomies (VroniPlag, PlagStop.NRW). The practice they converge on: open with a narrative citation, carry the attribution in words, and cite again at a new paragraph or when the source changes.

The guidance already says to avoid consecutive citations, but the rule (`guidelines.md` "Literature and Citations") lost its *how* when `@key` began rendering the number. It now reads "cite it once and then stop repeating the citation", which taken literally produces the ambiguous variant. One mechanical check actively works against it. `hindsight-leakage` judges each sentence alone, so "@Chen25 train a model." followed by "Their evaluation showed a 30 % reduction." fires the warning, and re-citing in the second sentence silences it, which rewards the repetition the guidance forbids.

A measurement over every agent-written proposal on disk found no same-key repetition (0 of 33 opportunity pairs). But no scenario gives the agent more than two references, so the pattern never had a chance to appear. The rule text and the check are defects in our own guidance whatever the models do. Whether more is needed is decided by measuring under conditions where the pattern can occur.

## What Changes

- Replace the consecutive-citation sentence in the guidance with an attribution-scope rule:
  - cite once per continuous use of a publication within a paragraph;
  - open such a run with the author-in-text form and carry the attribution in words ("they", "their evaluation");
  - cite again at a new paragraph, at a source switch, and after an intervening claim of the thesis's own;
  - never drop a citation without such a cue;
  - read a paragraph that needs one source in most of its sentences as a summary of that source, not a thematic cluster.
- Make `hindsight-leakage` attribution-aware across sentences. An uncited sentence counts as attributed when it continues an unbroken attributed run within its paragraph and opens with a back-reference cue (English and German). An uncued continuation keeps the warning, because a reader cannot tell it is borrowed either. The warning message names the cue as an admissible fix.
- Add measurement instruments for citation practice:
  - a synthetic rich idea seed (many references, one source central to a theme);
  - a synthetic draft that already carries the repetition pattern, both with oracles;
  - two dev-runner scenarios and two Inspect tasks over them;
  - L1 verdicts (identical citation-key set on adjacent sentences within a paragraph; for the repair task, no reference loses all its citations);
  - a model-graded rubric for citation practice (attribution scope clear at every sentence, no overcitation, no uncued continuation, synthesis rather than serial summary).
- Record a before/after measurement in the change. If it fails, escalate by failure type:
  - repetition → a `citation-repeated` check warning;
  - synthesis or attribution on the capable tier → a drafting clause in `proposal-write`.

  Each step lands only if the measurement shows it is needed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: a new requirement states the attribution-scope rule for citations, which today exists only as unspecified prose.
- `skill-check`: "Hindsight leakage reported as a warning" changes from a per-sentence citation anchor to a paragraph-scoped, cue-anchored attribution run.
- `testing-harness`: new requirement covering citation-practice instruments, which are the fixtures, scenarios, L1 verdicts, and the L2 rubric.

## Impact

- `shared/guidelines/guidelines.md` and its five generated `references/guidelines.md` copies (via `scripts/sync_shared.py`).
- `skills/proposal-check/scripts/check.py` and its four generated copies: `rule_hindsight_leakage`, plus a shared citation-key helper (the key regex reaches its third use).
- `harness/l1_checks.py` (new verdicts), `harness/claude_runner.py` (two scenarios), `harness/skill_evals.py` (two tasks, criteria), `harness/rubrics/` (one rubric), `harness/README.md`, the generated `evals/evals.json` projection of `proposal-write`.
- `tests/fixtures/` (two new synthetic fixtures with oracles), `tests/unit/` (rule and verdict tests).
- No change to import, review, supervise, publish, or the citation syntax. The ban on typed author names stays, and continuation uses pronouns and noun phrases.
- Conditional on the measurement: `check.py` gains `citation-repeated`, or `skills/proposal-write/SKILL.md` gains a pinned drafting clause.
