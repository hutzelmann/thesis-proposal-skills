---
name: proposal-publish
description: Build the exposé deliverable — an Overleaf-ready LaTeX project from the THI exposé template (expose.tex + literature.bib + images/), optionally a quick local PDF or a stripped hand-in export. Use when the user wants to hand something to their supervisor, asks for a PDF, or asks how to submit.
---

# Proposal Publish

The deliverable is an **Overleaf-ready LaTeX project** built from the THI Faculty of Computer Science exposé template. The student uploads the folder to Overleaf and compiles it there; nothing has to be installed locally.

## Build

Run the build script (stdlib-only, ≥3.11; use `py` instead of `python3` on Windows if needed):

```
python3 scripts/publish.py <proposal.md>
```

That writes `<slug>-expose/` next to the proposal:

- `expose.tex` — the template with the title page filled from the metadata block, the seven sections rendered from the markdown body, and the work-plan table drawn as the template's Gantt chart.
- `literature.bib` — BibTeX converted from the proposal's CSL-YAML `references`.
- `images/` — the THI logo, plus anything from the workspace `img/` folder.

No pandoc, no typst, and no TeX are needed for this path. Relay the script's `note:` lines to the user; each names something the exposé is still missing (a title-page field, a work-plan table without week ranges, an empty bibliography).

Other modes:

```
python3 scripts/publish.py <proposal.md> --pdf       # quick local preview via pandoc
python3 scripts/publish.py <proposal.md> --handout   # stripped markdown export
```

`--pdf` keeps the older pandoc pipeline (typst → LaTeX engine → docx) for a fast look at the text. It does **not** use the exposé template, so never hand its output to a supervisor as the exposé.

## Getting it to Overleaf

Offer the shortest path that fits the user:

- **Upload** — zip the generated folder, then Overleaf → New Project → Upload Project, and set `expose.tex` as the main document if prompted. Overleaf runs `pdflatex → bibtex → pdflatex ×2` automatically.
- **Local compile** — only if TeX Live or MiKTeX is already installed: run that same four-step sequence inside the folder. Never suggest installing a TeX distribution just for this; Overleaf is free and needs nothing.

## Regenerating

The generated `expose.tex` carries a header saying it is generated, and re-running the script overwrites the whole folder. Before overwriting, check whether the folder already exists and say so — a student who has begun editing the `.tex` by hand must either keep working in the markdown or take ownership of the `.tex` and stop regenerating. Do not silently discard hand edits.

## Hand-in guidance

- The title page needs `student_id`, `degree_program`, `supervisor`, and `submission_date` in the metadata block. If the script reports them as placeholders, the exposé is not ready to send.
- `--handout` strips abstracts from the references block — citations and entries stay intact. The handout is meant to be kept and sent, so it is deliberately **not** gitignored.
- Remind the user to rename the final PDF to include their name before sending (supervisors receive many exposés).
- If check hasn't run recently, offer it first — but publishing proceeds on user confirmation regardless (check is advisory).
