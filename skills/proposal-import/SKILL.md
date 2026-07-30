---
name: proposal-import
description: Import an existing proposal (usually PDF) into the standard single-file format — extract text and references, strip personal data, mark gaps. Use when the user has a proposal from Word/LaTeX/another tool and wants to continue working on it here.
---

# Proposal Import

Convert an existing proposal document into one `<slug>.md` in the standard format: markdown body, trailing `---` metadata block (blank line before it) with `title`, `subtitle`, `lang`, `references` in CSL-YAML. Never carry an `author` key over from the source — proposals are anonymous.

## Reading the source

Read the PDF directly. If you cannot ingest PDFs in this environment, say so plainly and ask the user to paste the text (or export it as text); then proceed identically. Expect messy sources — Word exports, LaTeX output, LLM-generated PDFs with swallowed headings or missing title blocks. Reconstruct the intended structure; never import formatting noise.

## Mapping content

- Map existing content onto the four canonical sections — titles per the write skill's `../proposal-write/references/guidelines.md`, section "Canonical Section Titles (English / German)"; use the proposal's language. If that file is not installed, use the four canonical English titles named there (Introduction to the Topic; Contribution to the State-of-the-Art; Research Focus and Research Questions; Methodology for Research: <Methodology>). Free-form sources rarely map cleanly — place content where it belongs, and mark unfillable sections with `[TODO: …]`.
- Detect the language and set `lang` accordingly.
- Convert the bibliography to CSL-YAML entries (`AuthorYearFirstWord` keys, DOI when present, URL only without DOI). References that cannot be resolved to a real entry become `[TODO: recover reference …]` — never invent metadata.
- Convert in-text citations by the role they play in their sentence — full rule in the write skill's `../proposal-write/references/guidelines.md`, section "Literature and Citations". Where the source names the authors as the actor ("Smith et al. [1] propose …", "Smith et al. (2020) propose …"), delete the name and the year from the prose and write `@key` alone: the build renders the name back from the reference entry. Where the citation only backs a claim ("… is widely reported [1]."), write `[@key]`. Never leave a typed author name immediately before a bracketed citation (`Smith et al. [@key]`) — it renders correctly today but stops tracking the entry the moment that entry is corrected. If the write skill is not installed, apply that rule as stated here.

## Strip on import (always report what was removed)

- Personal data: the proposal author's own name (cover page, header, metadata block), matriculation numbers, postal addresses, emails, study program, supervisor names and contacts.
- Forbidden content: timelines/work plans, preliminary chapter outlines, expected-results sections, deliverables lists, confidentiality markers.

End the import with a removal note listing every stripped item class — the user may need some of it elsewhere, but it does not belong in the proposal.

## Figures

Do not silently drop figures. For each figure in the source, insert `[TODO: re-add figure from page N as img/<slug>-<name>.png]` at the right position. If `pdfimages` or `mutool` is available on the system, offer to extract images into `img/` directly (slug-prefixed names); otherwise tell the user how to export them manually.

## Validate and complement the references

After conversion, run (Windows: `py` instead of `python3`):

```
python3 scripts/validate_refs.py <slug>.md
```

For each reference it reports VERIFIED (DOI resolves and matches), ENRICHED (identified via confident title match — completed CSL-YAML is printed for you to apply, keeping the existing ids), UNVERIFIABLE, or OFFLINE. Apply the completed entries; for every UNVERIFIABLE entry keep it but add `[TODO: verify reference <id>]` next to its first citation — never silently trust or drop it. If everything reports OFFLINE (no network), proceed with the as-found references and say that validation was skipped.

## Wrap-up

Report: sections mapped, references verified/enriched/unverifiable (per reference), items stripped, figures marked. Recommend running check next — imports almost always carry violations worth seeing immediately.
