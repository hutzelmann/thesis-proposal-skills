## ADDED Requirements

### Requirement: Exposé template project as the default deliverable
Publish SHALL render the proposal into a self-contained LaTeX project directory containing `expose.tex` (the THI exposé template with the title page filled from the metadata block and the body rendered from the markdown), `literature.bib` (BibTeX converted from the CSL-YAML references), and `images/`. This path SHALL require no external converter — no pandoc, no typst, no TeX distribution — so that a student with nothing installed can produce it and upload it to Overleaf.

#### Scenario: Build on a machine with no toolchain
- **WHEN** publish runs on a workspace with no pandoc, typst, or TeX installed
- **THEN** the LaTeX project is written successfully and the user is told how to upload it to Overleaf

#### Scenario: Methodology heading in the rendered document
- **WHEN** the source declares `Methodology: Controlled Experiment`
- **THEN** the rendered document shows a plain `Methodology` section, the branch name having served only the check script

### Requirement: Work plan rendered as a Gantt chart
Publish SHALL render the work-plan section's table as the template's Gantt chart, deriving each bar from a task label and a week range and drawing single-week rows as milestones. Where no row yields a week range, publish SHALL fall back to a plain table and SHALL report that the chart could not be drawn.

#### Scenario: Schedule without week ranges
- **WHEN** the work-plan table gives phases at month granularity with no week numbers
- **THEN** a plain table is emitted and a note names the missing week ranges

### Requirement: Secondary build modes
Publish SHALL retain a pandoc-based PDF preview mode and a stripped markdown handout mode. The preview mode SHALL NOT be presented as the exposé deliverable, since it does not use the template.

#### Scenario: Preview requested without pandoc
- **WHEN** the preview mode is invoked and pandoc is absent
- **THEN** publish reports what is missing and points back at the template project as the deliverable

## REMOVED Requirements

### Requirement: Publishing is optional
**Reason**: The exposé is the submitted artifact, and the template project builds with no toolchain, so there is no longer a cost the student must opt into. The zero-dependency property is preserved by the replacement requirement rather than by making the step optional.

### Requirement: Engine resolution order
**Reason**: The default path uses no engine at all. Engine resolution survives only inside the `--pdf` preview mode, covered by "Secondary build modes".

### Requirement: Compact output and citation style
**Reason**: Layout and citation style are now fixed by the THI template (`natbib` numeric with the `dinat` style) rather than chosen by the skill.
