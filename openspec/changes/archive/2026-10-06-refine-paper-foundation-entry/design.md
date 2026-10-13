## Context

The paper-foundation path landed in `add-paper-foundation-entry` (archived 2026-10-06) as one bullet with three ordered steps in `skills/proposal-ideate/SKILL.md`, guarded by seven `proposal-ideate--paper-*` pins and checked by `verdict_paper_foundation` through the `ideate_paper_foundation` dev scenario. Thomas approved the review's findings as a fix-forward, so this change applies them without reopening the design of that change. The motivation is in proposal.md, and the contract is in the two spec deltas.

## Goals / Non-Goals

**Goals:**
- Apply each verified finding as a wording change at the place the review named, mirrored in the spec delta and in the pin that guards the sentence.
- Keep the body as short as before or shorter. The per-section fallback and the front-matter range add words, and the third step's merged re-run rule pays some of them back.

**Non-Goals:**
- No verdict change. The README and the spec are corrected to describe what `verdict()` already receives. `workspace_markdown` is not widened.
- No new fixture paragraphs or markers. The fixture's front matter and the introduction's closing paragraphs carry no marker, so the narrowed text-file range is invisible to the verdict, and a read of lines 1–22 still passes. Whether a run reads only the introduction's closing paragraphs is recorded by hand.
- No description or routing change.

## Decisions

### D1 — The fallback is a statement, so the turn keeps one question

The old fallback ("say so and ask for it as text") put a second request into the turn whose only question the next step reserves for the axis. It also could not tell a paper that has no Limitations section from a heading search that missed one. The new wording says that the section was not located and that the student may paste it if the paper has one. That is a statement the student can act on without being asked, so the axis question stays the turn's only one. The whole-paper ingestion fallback stays a request: when nothing could be read there is no slice to ground an axis question on, so the turn's question is the request for the slice.

### D2 — Name the sections read, never summarize them

"Tell the student which sections you read" was meant as a reading receipt. A summary of the sections would restate Future Work items before the student points at one, which is the menu the next step forbids. The receipt therefore names the sections and nothing more. Quoting the paper stays allowed where the untrusted-text rule needs it, for example to show an embedded instruction as content.

### D3 — Front matter is in range because seeding needs it

The seeding step checks that a fetched record's title and authors match the paper. A read that skips the title block leaves nothing to match against. The front matter is therefore in the text-file range. For the same reason the contributions are read from the introduction's closing paragraphs rather than from the whole introduction, which reaches into motivation the slice does not need.

### D4 — Grounding waits for the axis and never uses the paper's title

"Ground early" sat before any axis existed in the reading order of the step, and the search term it implied was the paper's own title. The finding's wording, "Only then … never on the paper's own title", follows the step's opening gate (the student has named the axis), and the spec delta states that gate explicitly. "Early" is dropped because the gate already fixes when.

### D5 — One sentence for the re-run rule

Step 3 stated the re-run rule twice: once as "a transfer whose answer stays nothing is a re-run" and once as "a focus that only redoes the paper … is a scope". These become one sentence, and the `paper-transfer` pin follows it, together with the method-only gloss.

### D6 — The axis question is asked once, with the kinds inside it (after the dev run)

The single sonnet run read exactly the narrowed range and named the sections without summarizing them. It then asked the axis question, listed the kinds of change, and re-asked the question as "Which of those is it, in your own words?". The verdict failed it for a second question mark, as its requirement says. The fix goes to the wording, not the verdict: loosening a frozen check to pass the run that motivated the change is exactly the post-hoc change the previous change's measurement warned against. Step 2 therefore says "ask that alone and once" and puts any named kinds "inside that one question". The delta says the same, and the observed shape became an L0 failure case. Details are in `measurement.md`.

## Risks / Trade-offs

- [The new fallback is never exercised by the fixture, whose headings all match] → Recorded as unmeasured, as before. The pin guards the wording.
- [Naming the sections without summarizing them could read as curt] → The chat still mirrors the student's words in the axis question, which is where engagement belongs on this turn.
- [One sonnet run cannot show stability] → Recorded as such. The verdict is unchanged, so this run is directly comparable with run 5 of the previous change.
- [The D6 fix is unmeasured, because the run cap is one] → Recorded in `measurement.md` as the first thing to measure next.
