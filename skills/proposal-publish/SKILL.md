---
name: proposal-publish
description: Build a PDF (or docx fallback) from a proposal file via pandoc — compact layout, typst-first, with install guidance when tools are missing. Also offers a stripped hand-in export. Use when the user wants a PDF, wants to hand something to their supervisor, or asks how to install the build tools.
---

# Proposal Publish

Builds a PDF from a proposal file — compact layout, typst first, pandoc as the fallback — and can also produce a stripped hand-in export.

**Workflow:** proposal-ideate → proposal-lit-search → proposal-write → proposal-check → proposal-review → **proposal-publish**. Also: proposal-import (start from an existing document), proposal-customize (adapt the rules to a supervisor's requirements).

Publishing is optional — a proposal markdown file is an acceptable hand-in on its own. Never pressure the user into installing anything; offer the paths and their costs.

## Build

Run the build script (stdlib-only, ≥3.11):

```
python3 .claude/skills/proposal-publish/scripts/publish.py <proposal.md>            # PDF via best available engine
python3 .claude/skills/proposal-publish/scripts/publish.py <proposal.md> --handout  # stripped markdown export instead
```

Paths are relative to the workspace root for a standard project install; the script really lives in `scripts/` next to this SKILL.md, so use that location if the skill is installed elsewhere. If you cannot find it, say the script did not run and name what is therefore unverified — never present your own reading of the file as the script's result.

The script resolves the best pipeline automatically: **typst** (preferred) → **LaTeX engine** → **docx** (last resort, no PDF), using the skill's `templates/` (compact layout, `RQ n:` styling, citeproc). Outputs land next to the proposal; the script also ensures the workspace `.gitignore` covers build artifacts (shared rule: whichever skill first creates an ignorable artifact adds the entry).

Citations render in two forms, both usable in one document: `[@key]` becomes `[1]`, and `@key` becomes `Smith et al. [1]` — the author name derived from the proposal's own reference entry, so it never has to be typed. The filter chain producing this is order-dependent (`author-intext.lua` → `cite-split.lua` → citeproc → `rq-filter.lua` → `todo-filter.lua`); don't reorder it.

`[TODO: …]` markers render as numbered annotations rather than prose — a marker alone on its line becomes a callout block, one inside a sentence becomes a highlight, and a marker carried by the title or subtitle is numbered ahead of the body. There is deliberately no option to render them quietly: the way to a marker-free PDF is to resolve the markers, which `proposal-check` already lists.

## When tools are missing

The script reports what is missing and what it would unlock. Guide concretely, best first:

- **pandoc + typst** (recommended, two single binaries): `winget install --id JohnMacFarlane.Pandoc Typst.Typst` / `brew install pandoc typst` / distro packages. Smallest install, fastest builds.
- Existing **TeX Live/MiKTeX** works as the LaTeX fallback — nothing extra needed besides pandoc.
- Nothing installable? → `--handout` produces a clean markdown for hand-in, or suggest the user's institution machines / a colleague's setup for the final PDF.

Relay the script's messages rather than re-diagnosing; on Windows use `py` if `python3` is absent.

## Hand-in guidance

- `--handout` strips abstracts from the references block (supervisor-facing file should not be half bibliography database) — citations and entries stay intact. The handout is a deliverable meant to be kept and sent, so it is deliberately **not** gitignored.
- docx output uses pandoc's default styling (acceptable last resort; the compact look exists for the typst and LaTeX tiers).
- Remind the user to rename the PDF to include their name before sending (supervisors receive many proposals).
- If check hasn't run recently, offer it first — but publishing proceeds on user confirmation regardless (check is advisory).
