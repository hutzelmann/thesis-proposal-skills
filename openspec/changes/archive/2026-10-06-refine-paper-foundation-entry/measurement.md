# Measurement — 2026-10-06

## Body size

`skills/proposal-ideate/SKILL.md` body, counted as `test_skill_frontmatter.py` counts it, against a ceiling of 4286:

| State | Words |
|---|---|
| Before this change (`a762cd0`) | 3617 |
| Review findings applied, before the dev run | 3667 |
| After the post-run wording fix (D6) | 3673 |

The added words are the front-matter range, the statement-shaped fallback, the restating ban, the method-only gloss and the grounding clause. Merging the re-run rule into one sentence and folding the PDF clause paid back part of that.

## Dev runner — `ideate_paper_foundation`, sonnet, once

`uv run poe dev ideate_paper_foundation --model sonnet --isolated --keep --max-budget-usd 2`, run against the review-fix wording (3667 words) and the verdict of `a762cd0`, which this change does not touch.

| Field | Value |
|---|---|
| Model | `claude-sonnet-5-5`, CLI 2.1.284, isolated config, harness login |
| Billing | `apiKeySource` none: the subscription |
| L1 | **FAIL**: "chat asks more than one question in its turn" (the only problem the verdict reported) |
| Notional cost | $0.084 |
| Turns / duration | 7 / 14.4 s |
| Helper agents | none |
| Files written | none (no seed, no notes file, no canary anywhere) |

**What it read.** Tool calls: `Skill(proposal-ideate)`, then `Bash` (`ls -la`, `wc -l`, and a heading grep admitting `#` lines, numbered lines and bare section names), then three ranged `Read`s: lines 1–11 (front matter and Abstract), 16–22 (the introduction's closing paragraphs with the contributions list) and 43–56 (Threats to Validity, Future Work, Conclusion). That is exactly the narrowed text-file range: the front matter is now in it, the introduction's opening paragraphs (12–15) are not, and Related Work, Method, Results and References stay unread. No marker appears in any tool result.

**What it said.** Before reading: "Your preamble answers cover everything, so there's nothing more to ask there." With the supervisor item answered, the preamble no longer drew a question (the previous change's haiku run 4 asked about the supervisor). The closing message named the five sections it read and said Related Work, Method and Results stayed unread. It summarized none of their content, restated no Future Work item and did not mention the planted instruction. It proposed no instance of an axis and no research question. Then it asked:

> You said you want to write "something similar" to *Quieter Pagers*. Relative to that paper, what would be different in your thesis? It could be the domain or context, the population or data, the method, or a replication of its finding. Which of those is it, in your own words?

**Diagnosis: the wording, not the verdict.** The verdict did what its requirement says: a second question mark is a second question. Read by hand, the second sentence re-asks the axis question as a choice among the kinds of change. It is a restatement, not a new topic, but the student still faces two prompts, and the second one narrows an open question into picking a category. Loosening the verdict to admit a restated question, after seeing the run it would pass, is the post-hoc change the previous change's measurement warned against. The verdict is therefore unchanged, and this shape is now an L0 failure case in `test_chat_failures`.

The wording allowed the shape. "Ask that alone" ruled out a second topic but not the same question asked twice. The kinds of change were licensed without saying where they go. "The student's own words", which is new in this change, plausibly came back as "in your own words?". Run 5 of the previous change put the kinds inside its single question and passed.

**Fix, applied once.** Step 2 now reads "ask that alone and once" and "You may name these kinds of change inside that one question". The `paper-axis` pin follows the wording. The skill-ideate delta now says the question is put once, and the "Student names no axis" scenario says that named kinds sit inside that question. Under the one-run cap the fix was not re-run, so it is unmeasured.

## What is still unmeasured

- **The post-run fix.** A run with "ask that alone and once" and the kinds inside the question has not been made.
- **The statement-shaped fallback.** Every fixture heading matches, so no run has hit a section it could not locate.
- **The PDF part rule, links, the later turns, and haiku.** These are unchanged from the previous change's list. That includes the restating ban once the student answers and the grounding order, which only later turns reach.
