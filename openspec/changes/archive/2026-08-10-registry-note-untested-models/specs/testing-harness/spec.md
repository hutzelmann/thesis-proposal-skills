# testing-harness delta: registry-note-untested-models

## MODIFIED Requirements

### Requirement: Pinned model registry
Matrix runs SHALL take their model roster exclusively from a tracked registry file pinning exact provider-qualified model IDs (the version visible in the ID), each with family, price tier, cached input/output pricing, and an enabled flag. A registry entry MAY carry a free-text note recording a caveat about the model's standing in the matrix — for example that the harness cannot drive it — which SHALL default to empty when absent. The roster SHALL cover at least three model families (Anthropic, OpenAI, open-weight) at cheap and frontier price points. Changing a model version SHALL require editing the registry, never a runtime "latest" resolution, so successive runs stay comparable.

#### Scenario: Roster comes from the registry
- **WHEN** a matrix run is started with a tier filter
- **THEN** exactly the enabled registry models of that tier are exercised, under their pinned IDs

#### Scenario: Disabled model skipped
- **WHEN** a registry entry sets enabled to false
- **THEN** matrix runs omit it without failing

#### Scenario: Note is optional
- **WHEN** a registry entry carries no note
- **THEN** the registry parses and the model's rendered notes are unchanged

### Requirement: Generated model-support report
A report generator SHALL derive, from the newest run logs only, (1) a summary table in the repository README between generated-section markers — one row per registry model with its pinned ID, verdict, warnings, and the run timestamp — and (2) a full model×task grid document with per-cell pass rates and per-model run cost. Regeneration SHALL be idempotent and SHALL replace only the marked README region. Models never exercised in the available logs SHALL appear as untested rather than silently omitted. A registry note SHALL appear in the model's summary-row notes, after any verdict-derived notes, so a model whose measurements were invalidated (for example, a harness incompatibility) is presented as untested with the reason visible rather than as bare untested or as failing.

#### Scenario: README region replaced in place
- **WHEN** the report generator runs twice on the same logs
- **THEN** the README outside the markers is byte-identical and the marked region is identical between runs

#### Scenario: Untested model visible
- **WHEN** a registry model has no cells in the available logs
- **THEN** the summary row shows it as untested instead of dropping it

#### Scenario: Registry note rendered
- **WHEN** a registry model carries a note and no measured cells
- **THEN** its summary row reads untested and its notes carry the registry note verbatim

#### Scenario: Note appended after verdict notes
- **WHEN** a registry model carries a note and its logs also produce verdict-derived notes
- **THEN** the row's notes carry the verdict-derived notes first and the registry note after them
