## Why

An external contributor's proposal rewrote the section skeleton to match their faculty's exposé template. The skeleton is rejected — this repository's five-section shape stays — but the judgement written into that rewrite is not template-specific, and four pieces of it fill real gaps in the current prose:

- The guidance says a research question must never be an implementation goal, but never says where an implementation goal *does* belong. A student told only what not to write moves the goal one section down and leaves it unphrased.
- The contribution section is described as a delta over prior work with no guidance on how to organise the prior work. Chronological reading lists are the predictable result.
- "Prefer peer-reviewed over vendor sources" reads as forbidding standards. For a normative definition — what a term means, what a system is required to do — an ISO or IEEE standard is not a weaker source than a paper, it is the correct one, and students currently cite a vendor's summary of the standard instead.
- The User Study branch says nothing about ethics, consent, or data protection, which is the first thing a supervisor asks about a study with participants.

A fifth item is a number the same proposal argued about: three references is a floor that catches an empty bibliography, not a target a submitted proposal should aim at. The floor stays where it is; the target belongs in prose where the write and review skills can act on it.

## What Changes

- **Where construction goals belong.** State the distinction — a goal says what the work will *do*, a research question asks what it will *find out* — and say that a construction goal belongs in the contribution section as the work's own description, not in the research questions.
- **Organising prior work.** The contribution section groups sources into thematic clusters rather than chronologically, synthesises rather than summarises, and closes by naming the gap the thesis fills, tied to the research questions.
- **Standards as sources.** Published standards and regulations are legitimate — and often the only correct — sources for normative definitions, required behavior, and terminology, cited by designation and year rather than through a vendor's summary. A standard establishes what is required; it never establishes that an approach works, so empirical claims still need peer-reviewed evidence.
- **Research with human participants.** Advisory guidance covering the ethics route, informed consent, personal-data handling, risk bounding, and compensation — two or three sentences inside Preparation or Procedure, explicitly not a new section and explicitly not mechanically checked.
- **Anticipated outcomes.** Where a proposal describes what the work will yield, that is stated as an expectation and never as a result already obtained, and the foreseeable limitations are named. This does not un-forbid an expected-results section; it governs the claims the proposal already makes.
- **Reference target.** `min_references` stays 3. The prose states that three is the mechanical floor and ten to fifteen the working range for a submitted proposal.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `guidance-model`: the prose guidance gains four content rules and states the difference between the reference floor and the reference target.

## Impact

- `shared/guidelines/guidelines.md` and its five generated copies.
- No structured data changes: every item here is a judgement, and the formalization boundary keeps judgements in prose. `min_references` is deliberately untouched.
- No fixture or oracle changes — nothing here is mechanically checked.
