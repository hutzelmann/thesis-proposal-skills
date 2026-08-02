---
name: proposal-import
description: Import an existing proposal (usually PDF) into the standard single-file format — extract text and references, strip personal data, mark gaps. Use when the user has a proposal from Word/LaTeX/another tool and wants to continue working on it here.
---

# Proposal Import

Convert an existing exposé document into one `<slug>.md` in the standard format: markdown body, trailing `---` metadata block (blank line before it) with `title`, `author`, `student_id`, `degree_program`, `supervisor`, `second_supervisor`, `submission_date`, `subtitle`, `lang`, the optional `abbreviations` mapping, and `references` in CSL-YAML.

## Reading the source

Read the PDF directly. If you cannot ingest PDFs in this environment, say so plainly and ask the user to paste the text (or export it as text); then proceed identically. Expect messy sources — Word exports, LaTeX output, LLM-generated PDFs with swallowed headings or missing title blocks. Reconstruct the intended structure; never import formatting noise.

## Mapping content

- Map existing content onto the seven canonical sections — titles per the write skill's `../proposal-write/references/guidelines.md`, section "Canonical Section Titles (English / German)"; use the proposal's language. If that file is not installed, use the seven canonical English titles named there (Introduction and Motivation; Problem Statement and Research Questions; Objectives; Related Work; Methodology: <Methodology>; Expected Contributions and Results; Work Plan and Schedule). Free-form sources rarely map cleanly — place content where it belongs, and mark unfillable sections with `[TODO: …]`.
- A source written against the older four-section shape maps predictably: "Introduction to the Topic" → Introduction and Motivation, "Contribution to the State-of-the-Art" → Related Work, "Research Focus and Research Questions" → Problem Statement and Research Questions. Objectives, Expected Contributions and Results, and Work Plan and Schedule will be absent and become TODO sections.
- Detect the language and set `lang` accordingly.
- Convert the bibliography to CSL-YAML entries (`AuthorYearFirstWord` keys, DOI when present, URL only without DOI); convert in-text citations to `[@key]`/`@key`. References that cannot be resolved to a real entry become `[TODO: recover reference …]` — never invent metadata.

## Title-page data: move, do not discard

The exposé template has a title page fed by the metadata block, so cover-page data is relocated rather than stripped. Move student name, student ID, degree program, supervisor names, and submission date out of the body and into the matching metadata fields. Drop the contact details that have no field — postal addresses, phone numbers, and email addresses are not part of the title page.

## Strip on import (always report what was removed)

- Personal data left in the **body**: matriculation numbers, postal addresses, emails, study program, supervisor mentions in prose.
- Forbidden content: preliminary chapter outlines, deliverables lists, confidentiality markers.

Work plans, timelines, and expected results are **not** stripped — they are required sections of the exposé. Map a Gantt chart or phase table onto Work Plan and Schedule as a table with a week range per row, and map an expected-results section onto Expected Contributions and Results.

End the import with a note listing every stripped item class and every field moved to the metadata block — the user may need some of it elsewhere, but it does not belong in the body.

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
