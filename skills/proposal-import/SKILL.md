---
name: proposal-import
description: Import an existing proposal (usually PDF) into the standard single-file format — extract text and references, strip personal data, mark gaps. Use when the user has a proposal from Word/LaTeX/another tool and wants to continue working on it here.
---

# Proposal Import

Convert an existing proposal document into one `<slug>.md` in the standard format: markdown body, trailing `---` metadata block (blank line before it) with `title`, `author`, `subtitle`, `lang`, `references` in CSL-YAML.

## Reading the source

Read the PDF directly. If you cannot ingest PDFs in this environment, say so plainly and ask the user to paste the text (or export it as text); then proceed identically. Expect messy sources — Word exports, LaTeX output, LLM-generated PDFs with swallowed headings or missing title blocks. Reconstruct the intended structure; never import formatting noise.

## Mapping content

- Map existing content onto the four canonical sections — titles per the write skill's `../proposal-write/references/guidelines.md`, section "Canonical Section Titles (English / German)"; use the proposal's language. If that file is not installed, use the four canonical English titles named there (Introduction to the Topic; Contribution to the State-of-the-Art; Research Focus and Research Questions; Methodology for Research: <Methodology>). Free-form sources rarely map cleanly — place content where it belongs, and mark unfillable sections with `[TODO: …]`.
- Detect the language and set `lang` accordingly.
- Convert the bibliography to CSL-YAML entries (`AuthorYearFirstWord` keys, DOI when present, URL only without DOI); convert in-text citations to `[@key]`/`@key`. References that cannot be resolved to a real entry become `[TODO: recover reference …]` — never invent metadata.

## Strip on import (always report what was removed)

- Personal data: matriculation numbers, postal addresses, emails, study program, supervisor names and contacts.
- Forbidden content: timelines/work plans, preliminary chapter outlines, expected-results sections, deliverables lists, confidentiality markers.

End the import with a removal note listing every stripped item class — the user may need some of it elsewhere, but it does not belong in the proposal.

## Figures

Do not silently drop figures. For each figure in the source, insert `[TODO: re-add figure from page N as img/<slug>-<name>.png]` at the right position. If `pdfimages` or `mutool` is available on the system, offer to extract images into `img/` directly (slug-prefixed names); otherwise tell the user how to export them manually.

## Wrap-up

Report: sections mapped, references recovered vs. TODO-marked, items stripped, figures marked. Recommend running check next — imports almost always carry violations worth seeing immediately.
