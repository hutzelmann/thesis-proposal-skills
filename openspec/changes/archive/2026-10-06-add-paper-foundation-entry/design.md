## Context

`proposal-ideate` has three entry paths: the solid idea, a supervisor's topic list, and another thesis's future work (`2026-08-23-add-future-work-entry-path`). The thesis path is the closest model for this one. It bounds what the skill reads (the closing chapters only), gives the reason (a document read end to end makes the skill the party with the ideas), falls back to asking for the slice as text, and records the source at seeding. The paper path keeps that shape. What differs is the material. A paper is short, its contributions and limitations are stated explicitly, it is published by definition, and the student says "similar to", not "continue". That last difference brings a question the thesis path never had: in which respect should the new thesis be similar?

Constraints that shape the approach:

- The hard rule: idea content (topic, research questions, the method choice) comes from the student, and every move between the bookends anchors in something the student already said.
- Grounding: the skill names only works that appeared in a fetch result of this session; outbound requests need the preamble's lookup consent.
- Seeding: `[TODO: …]` markers are reserved for submission-blocking gaps; starter references are CSL-YAML entries in the metadata block.
- Body size: `test_no_skill_body_outgrows_its_siblings` caps every body at twice the median. Measured at the start of this change, ideate's body is about 3000 words against a ceiling of about 4400. The cap does not bind here, but the body is already the second-largest, so the new text reuses the thesis bullet's wording instead of repeating it.

## Goals / Non-Goals

**Goals:**
- A student who brings a paper gets a session in which the paper is their material and the thesis question is their own.
- The skill's reading of the paper is bounded, and the bound can be observed in a headless run.
- The paper reaches the seed as a starter reference built only from a fetched record, or reaches the notes file when no matching record can be fetched.

**Non-Goals:**
- No shipped script and no PDF reader. Reading the paper and fetching its record are the agent's own capabilities, as on the thesis path.
- No change to the literature-search skill. Building the bibliography beyond the foundation paper stays its job.
- No new preamble question. The path is recognized from what the student brings.
- No judgment of whether the paper is a good foundation (venue quality, age). That would be the skill evaluating the student's material before the student has said what they want from it. Grounding exposes staleness the same way it does for a future-work item.

## Decisions

### D1 — The framing slice: Abstract, contributions, Limitations/Threats, Future Work, Conclusion

The slice is what a paper says about itself: what it claims (abstract, contributions), where it admits it stops (limitations, threats to validity), where it thinks the next step lies (future work), and what it concludes. A transfer pushes against exactly those edges, and the delta is stated against the contributions. Method and Results are the paper's content. Read by the skill, they become the material it offers back ("you could keep their pruning scheme and…"), which is the no-content failure in its plainest form.

Alternatives considered:
- *Read the whole paper* (as `proposal-reverse` reads a thesis). Rejected for the thesis path's reason, and more sharply: a paper's method section is short enough to summarize in one chat turn, and a summary leads straight to a suggestion.
- *Abstract only.* Too thin. The limitations and future work are where the paper names its own open edges, and those are what a student's "similar, but…" usually pushes against.
- *The thesis path's slice (Future Work, Limitations, Conclusion).* A thesis's abstract is boilerplate and its contribution statement is spread over a chapter. A paper's abstract and contribution list are its most compact self-description and the anchor for the delta, so both join the slice.

A passage the student quotes from Method or Results enters the session as the student's own material. The skill does not then go and read the rest of the section, because the student chose what to bring. The bullet says both halves in one sentence ("a passage the student quotes from them is their material, and the rest of that section still stays unread"): an earlier "unless the student quotes a passage" read as permission to open the section once a quote arrived.

On a text source the bound means line ranges, not pages: find the heading lines first, then read only the ranges beneath the slice's headings. A heading line is one opening with `#` or a section number, or one holding a slice section's name alone, since text extracted from a PDF often carries "Abstract" or "Conclusion" as a bare line. For any slice section that cannot be located, the skill says so and asks for that section as text rather than reading the whole file or a neighbouring section. The fallback is per section because a file with numbered body headings and a bare "Abstract" yields some headings, and an all-or-nothing fallback would never fire while the Abstract went unread. "A neighbouring section" covers a paper whose closing section is called Discussion: Discussion interprets the Results, so it is not a substitute for a missing Conclusion. The heading-first rule and the no-whole-file rule were added after measurement (`measurement.md`, sonnet run 1). The first wording said only "in a text file only the lines under those headings". Sonnet tried exactly that, but its own heading regex missed `## Abstract`, so it fell back to reading the whole file and said so. A rule that names how to find headings and forbids the whole-file fallback is the smallest one that closes that path.

A PDF has no line ranges and a paper has no table of contents, and scanning a PDF's headings with a page reader renders every page, Method and Results included. The slice sits at the two ends of a paper, so the bullet names the pages instead: the opening page or two (Abstract, the introduction's closing contributions) and the pages just before the references (Limitations, Future Work, Conclusion). A page that turns out to hold Method or Results is named and not used. A link is bounded the same way: a fetch tool hands back a model-written answer to whatever prompt it gets, and the default prompt a weak model writes is "summarize this paper", so the bullet asks for the slice's sections by name and never for a summary. Both are untested (`measurement.md`).

The bullet is self-contained rather than pointing back to the thesis bullet ("located as in a thesis above", "for the thesis path's reason"). Those pointers also pulled in the thesis bullet's next sentence, "treat what you found like a supervisor's topic list", which on this path would turn the paper's Future Work into a list of axes to choose from (D2).

### D2 — The axis is the student's; the skill asks, anchored in the paper

"Similar to this paper" is the student's own statement, so asking "similar in which respect — what would be different in yours?" mirrors it back. That is the hard rule's "vague problem → mirror it back" move. It is not the forbidden out-of-nowhere question for missing content, since it operates on material the student brought. The skill may name the kinds of change (domain or context, population or data, method, replication of the finding) because they are the shape of the question, a convention like the closed methodology set. It may not name an instance, such as a particular domain, dataset, or method to move the paper to. That would be idea content, and it is exactly what a student pressing "just tell me what to change" asks for, so the existing extraction-pressure rule (decline and offer the next scaffolded step) covers it.

The axis question is asked alone, as the turn's only question, and the press on the transfer (D3) waits until the student has named the axis. The two were one sentence with no order between them, and every sonnet run joined them into one closing question, pressing on a setting the student had not named yet (`measurement.md`). The bullet therefore splits the path into three ordered steps (read, ask the axis, press once it is named), and the preamble keeps opening the session as on the solid-idea path, with the axis question never stacked onto the preamble block.

Alternatives considered:
- *Offer two or three concrete transfer directions.* Rejected: a menu of ready-made topics, which the no-idea path is explicitly bounded against, applied where the student has material of their own.
- *Derive the axis from the paper's own Future Work list.* Rejected as a choice the skill makes. Picking one item as the axis remains the student's move. Unlike a thesis's future work, the paper's Future Work is not a list to choose from: the path deliberately reads it, and the likeliest weak-model failure is "the authors suggest X or Y, either could be your thesis", which proposes the axis. So the skill never lays its items out as options and never recommends one. When the student's answer points at an item, the skill may quote it and judge it with them, because by then the student has made the choice and quoting is judging, not supplying.

### D3 — Every axis is legitimate; the pressure is on why the transfer matters

A method-only transfer (same method, new domain) and a replication are admissible. The guidelines' delta test already accepts "confirming or refuting a published finding under new conditions", and the degree-level steering names a bounded application of something established as the level-appropriate Bachelor move. The skill's work is the Socratic press on what about the new setting changes what is at stake: a transfer whose answer is "nothing" is the "redo this paper" scope, and the thesis path's leftover-task-list rule applies to it unchanged. The contract makes a method-only transfer legitimate "when the new setting changes what is at stake", so the condition is carried into both normative texts, not left here: the bullet says "once the student can say that; a transfer whose answer stays 'nothing' is a re-run of the paper", and the spec has a scenario for the failing branch. Replication gets the same treatment from the other side. A student who chooses it is in a sense redoing the paper, so the bullet says that confirming or refuting the finding under new conditions counts as a delta, and that only a redo with nothing at stake that the new setting changes is the scope.

Interaction with level steering: no new text is needed. At Bachelor level a bounded transfer of an established paper is exactly the move the level paragraph names. At Master level the existing push ("what would this add that is not already known?") lands on the transfer: what does it add beyond the paper's finding? The level concern stays out of the seed, as before.

Interaction with scoping: the paper is the student's material, not scoping material. The containment rule (lookup-only vocabulary stays out of the seed) does not apply to the paper's terms. The no-content rule still decides who originates the research question.

### D4 — Grounding the transfer early

The thesis path grounds the chosen item early because a two-year-old suggestion is often done. Here the question is whether someone has already made this transfer. Grounding runs once the student has named the axis, through the existing grounding route and its lookup consent, and searches with the student's terms for the new setting rather than for the paper's follow-ups. Both conditions are in the bullet, not only here. D3 counts the paper's terms as the student's material, so the scoping containment rule does not block a search on the paper's title or its Future Work items. Run on turn one, such a search returns ready-made transfers, and naming them in chat would hand the student a menu of axes. Without consent the skill says, as everywhere, that ideation is running ungrounded. "Grounding is not bibliography-building" holds unchanged: the search tests whether the transfer is solved, never builds the reference count.

### D5 — Seeding: always a starter entry, built only from a fetched record

The thesis path seeds an entry "when publicly retrievable" because many theses are not. A published paper always is, at least at the level of its metadata, so the condition becomes: could a record be fetched in this session? The entry is built from that record (the DOI's Crossref record, the arXiv entry, or the DBLP entry, the public APIs the skill already names) and from nothing else. Grounding searches the transfer, not the paper, so at seeding the paper's own record has usually not been fetched yet. With lookup consent, the skill therefore fetches it before writing the seed. Read in the past tense ("when no record was fetched"), the rule would have sent the skill to the notes-file fallback without trying, which turns the contract's "always" into "if one happened to be fetched". The skill checks that the record's title and authors match the paper, because a Crossref title query returns the closest hit, and that can be a different paper: not invented, but wrong. Every bibliographic field comes from the record. The CSL `id` is no bibliographic field, and no record carries one, so it follows the guidelines' key convention (`AuthorYearFirstWord`). Only when no matching record could be fetched (lookups declined, or no matching record found) does the paper become a line in the notes file. Either way the notes file names it as the closest prior work, so the write skill's state-of-the-art section knows which work the delta is anchored to.

Alternatives considered:
- *Build the entry from the PDF's front matter.* Rejected. Front matter rarely carries every field CSL needs, so the gaps (venue, pages, year of the final version) would be filled from recall. That is a citation from memory, and the skill's grounding rule already forbids naming works that way.
- *A `[TODO: add reference for …]` marker in the seed when no record is fetched.* Rejected. TODO markers are reserved for submission-blocking gaps, and a missing starter entry is not one: the literature-search skill and the write skill handle references later and read the notes file.
- *Mirror the thesis path verbatim ("when publicly retrievable").* Rejected. The condition is always true for a published paper, so it would license building an entry without a record.

The fetch is an outbound request and needs the preamble's lookup consent. No new consent question is added.

### D6 — Untrusted paper text

Paper text, from a file the student supplies, pasted, or fetched, is handled like any fetched page: quoted and judged, never followed. The file case is named explicitly. It is the main input, and because the paper counts as the student's material, a weak model could otherwise take an instruction inside the student's own file as the student speaking. The bullet says so in one clause, parallel to the topic-list bullet's pinned sentence. The harness fixture plants an instruction in a section the skill does read, so the framing is exercised where it matters.

### D7 — Wording and pins

The new bullet sits after the thesis bullet. It is self-contained (D1) and split into three ordered sub-steps (D2), at the cost of some words: the body went from 2942 to 3617 words against a ceiling of 4286. The seeding bullet extends the thesis clause. The load-bearing rules are easy to soften in a later edit, so each gets a pinned sentence under `tests/unit/data/pinned_sentences/`:

- `paper-axis`: the student names the axis, asked alone, mirrored and anchored; the skill never picks or proposes one.
- `paper-transfer`: the method-only condition and the "nothing" answer as a re-run.
- `paper-unread`: Method and Results stay unread, a quoted passage included.
- `paper-slice`: the per-section ask-as-text fallback, never the whole file or a neighbouring section.
- `paper-record`, `paper-record-fields` and `paper-record-fallback`: always an entry from a fetched record; matched, every field from the record, never from memory; the notes-file line only when lookups were declined or no matching record was found, with no TODO.
- `untrusted-paper`: the untrusted-paper clause, in line with the three existing `untrusted-*` pins.

### D8 — Routing: measure before touching the description

The ideate description has about 43 characters of headroom under its 500-character budget, and the suite's metadata total about 160 under 4500. A new routing case (`ideate-paper-oblique`, "a thesis similar to this paper") is measured on sonnet against the unchanged description first. It carries no link. A first version ended in a DOI with Crossref's test prefix, and haiku objected to the placeholder identifier and loaded no skill, so it measured the identifier, not the description (`measurement.md`). If it routes to `proposal-ideate` in all epochs, the description stays as it is. Spending always-loaded metadata on a phrase that already routes buys nothing (the README's own conclusion about `ideate-collision`). If it misroutes, the description gains the paper starting point within budget, without claiming lit-search's owned "already published", and the neighbouring cases (`litsearch-collision`, `negative-paper-summary`, the ideate and reverse cases) are re-measured. The run uses `--case` and `--no-report`, so `docs/skill-routing.md` stays the full sweep's report.

### D9 — Harness: one headless scenario, verdict over what the run read

A one-shot run fits this path, unlike a converging dialogue. The path's first turn is self-contained: with the preamble pre-answered, lookups declined, and no axis named, the correct turn reads the slice, says which sections it read, and asks what would change. The request therefore carries no "this is our whole session, seed now" cue, which `ideate_scoped` needs to reach a seed. Here the first turn is the thing measured, and a seed at that point is itself a failure: the session holds no idea content of the student's.

The verdict reads three inputs:

- **The text of every tool result the run received.** A marker phrase there means the Method or Results section was read, whether by `Read`, `Grep` context or a shell `cat`. A chat-only check would pass a run that read everything and happened not to repeat it. Every paragraph of both sections carries a marker. At first only two of the six did, and a ranged read overshooting the slice by one paragraph (lines 1–30, say) passed, while overshoot is the realistic failure of a ranged reader. The bound is Method and Results, the hazard the contract names. Related Work and References carry no marker, so the verdict measures "Method and Results unread", not "only the framing slice". Run 3's read into References is recorded by hand.
- **Every text block the run showed the student.** Sections named (at least three framing-section names), exactly one question asked, no marker, and no research questions or transfer axis of the skill's own, judged by deliberately narrow tripwire patterns. "Exactly one" is the hard rule's one question per turn. A headless run is one turn, so a second `?` fails, and so does a second question joined to the first behind a single `?` as ", and what …?". That was the closing shape of every sonnet run on the pre-review wording. The dev runner's other verdicts read only the final message the result event carries. This one reads every block, because naming the sections it is about to read, before the read calls, is a natural place for the path's announcement. Measured: sonnet run 3 named them there, and its final message only asked. Three names rather than two because two occur in passing. Sonnet run 2 cited "Threats to Validity and Future Work" as where the paper's limits come from, and recorded the sections it read only in its notes file.
- **The workspace files.** No proposal seeded, no marker, and no canary from the planted instruction.

To keep an unread paper from passing on the absence of markers, the verdict also requires that some tool result carries framing-slice text.

The fixture is a `.txt` file in a new `p` (paper) prefix directory. `.txt` follows the `s01` precedent: the corpus-wide "every proposal builds and has an oracle" invariants skip it, and the runner's `*.md` workspace scan never mistakes the staged paper for a produced proposal. Its contents are markdown-headed, so the headings are there to locate.

The tripwire patterns for an axis of the skill's own are narrow on purpose ("you could apply…", "how about transferring…", "one direction would be…"). A broad detector would fire on Socratic questions. The measurement notes record a hand reading of each run's chat for what the patterns cannot see.

## Risks / Trade-offs

- [A small text file is read whole by habit, whatever the skill says] → This is the measured hazard, not a side effect: the verdict fails it, and the bullet names line ranges for text sources (D1). If sonnet still reads whole files, the finding is recorded and the wording revisited in a follow-up, not hidden.
- [The axis tripwire misses a proposal phrased another way] → The patterns are a floor. The hand reading in the measurement notes is the real check for a one-off run, and an L2 criterion can follow if the path proves fragile.
- [Asking for the axis reads as the forbidden direct question] → D2 anchors it in the student's own "similar to" and in the paper they brought. The spec states the question is put "anchored in the paper they brought".
- [Concurrent edits to the harness on main] → Additions are appended (scenario at the end of `SCENARIOS`, verdict and helper at the end of `l1_checks.py`). The one dispatch line in `verdict()` sits in a region the other session does not touch, and the L0 tests live in a new file.
- [Haiku's one-shot adherence is known to be weak for ideate scenarios] → It is run once and recorded as data, not as the bar. Sonnet is the bar, as `harness/README.md` already says for `ideate_scoped`, and the README gives the sonnet invocation, because the runner defaults to haiku.
- [The one-question check fires on a legitimate message] → A second `?` in a first turn whose preamble is pre-answered is a second question. The joined pattern needs a comma, "and", and a question word, all inside a sentence that ends in `?`. A false FAIL would show in the hand reading every run gets.

## Review dispositions (2026-10-06)

Three lenses reviewed the implemented change: contract fidelity, the no-content rule, and tests and harness. Every finding was fixed except the parts listed as rejected below.

Contract fidelity:
- *Method-only condition dropped (major).* Fixed: the condition and the "nothing" branch are in the bullet, the spec, and a new scenario (D3).
- *Seeding fallback weaker than the contract (minor).* Fixed: the record is fetched at seeding with consent, and the fallback applies only when lookups were declined or no matching record was found (D5).
- *Replication read as a redo (minor).* Fixed: a replication counts as a delta, and the redo scope is qualified as "with nothing at stake that the new setting changes". There is a new scenario.
- *The no-ingest fallback lost its object (minor).* Fixed: "say why only that slice, and proceed identically", plus the per-section fallback.
- *The axis "ask" sat beside the hard rule unexplained (minor).* Fixed: the question is the mirror of the student's "similar to", anchored in the paper they brought.
- *Heading definition too narrow (minor).* Fixed: a bare slice-section name counts as a heading, and the fallback is per section (D1). Not fixed: a numbered list item ("1. We prune …") still matches as a heading line. Excluding it would need a rule about what follows the number, which costs words for a case the per-section fallback already makes harmless.

No-content rule:
- *A quoted passage read as permission to open the section (major).* Fixed (D1, `paper-unread` pin).
- *Two questions in one turn (major).* Fixed by ordering the steps and asking the axis alone (D2), and by the verdict's one-question check (D9).
- *Grounding before the axis, on the paper's terms (major).* Fixed (D4).
- *Future Work as a menu via the thesis bullet's back-reference (major).* Fixed: the bullet is self-contained, and Future Work is not a list to choose from (D1, D2).
- *No bound for the PDF and link cases (major).* Fixed in wording (D1), unmeasured.
- *Seeding readings: past tense, "always", and consent (major).* Fixed: fetch at seeding with consent, check the match, fields only from the record (D5).
- *"Never with a field the record lacks" excluded the `id` (minor).* Fixed: "never one the record lacks", which follows "every bibliographic field", plus "the `id` follows the guidelines' key convention".
- *File input missing from the untrusted clause (minor).* Fixed (D6).
- *Preamble order (minor).* Fixed: the preamble opens the session, the paper is read after it, and the axis question is never stacked onto the preamble block. There is a new scenario.
- *Unclear "if none turn up" (minor).* Fixed by the per-section fallback, which never reads a neighbouring section instead (D1).

Tests and harness:
- *Markers in two of six paragraphs (major).* Fixed: every Method and Results paragraph carries a marker, an L0 test checks that, and a parametrized test fails the overshooting reads. The four kept workspaces were re-graded (`measurement.md`).
- *Pins too short (minor).* Fixed: seven paper pins (D7).
- *Run 3's overshoot into References and the verdict's real bound (minor).* Fixed in `measurement.md`, the testing-harness delta and the README. Rejected: also planting a Related Work marker so the verdict measures the whole slice. The contract's no-content hazard is Method and Results; Related Work summarizes other work, not this paper's ideas, and References lists titles. A marker there would turn a harmless overshoot into a FAIL that says nothing about the hazard. The skill text still bounds the reading to the slice, and the hand reading records any overshoot.
- *Unverifiable evidence (minor).* Fixed. (a) `measurement.md` says the v1 routing stream was overwritten by the v2 run of the same case id. (b) It records run 3's notes file falsely claiming that the student was told. (c) A confirmatory sonnet run (run 5) was made under the frozen post-review verdict and wording, and run 3's earlier PASS is labelled a post-hoc re-grade.
- *Reviewer note: the runner's default model is haiku.* Fixed: the README gives the sonnet invocation.
