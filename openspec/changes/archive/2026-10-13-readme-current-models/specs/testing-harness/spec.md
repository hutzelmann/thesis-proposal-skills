## MODIFIED Requirements

### Requirement: Generated model-support report
A report generator SHALL derive, from the newest run logs only, (1) a summary table in the repository README between generated-section markers — one row per enabled registry model with its pinned ID, verdict, warnings, and the date of the newest log among those models — and (2) a full model×task grid document with per-cell pass rates and per-model run cost, covering every registry model and marking a disabled one as disabled. A disabled registry model SHALL have no README row: the README shows the models a reader can pick today, while the grid document and the exported verdict data keep the disabled model's verdict. Regeneration SHALL be idempotent and SHALL replace only the marked README region. Models never exercised in the available logs SHALL appear as untested rather than silently omitted. A registry note SHALL appear in the model's summary-row notes, after any verdict-derived notes, so a model whose measurements were invalidated (for example, a harness incompatibility) is presented as untested with the reason visible rather than as bare untested or as failing.

#### Scenario: README region replaced in place
- **WHEN** the report generator runs twice on the same logs
- **THEN** the README outside the markers is byte-identical and the marked region is identical between runs

#### Scenario: Untested model visible
- **WHEN** an enabled registry model has no cells in the available logs
- **THEN** the summary row shows it as untested instead of dropping it

#### Scenario: Registry note rendered
- **WHEN** an enabled registry model carries a note and no measured cells
- **THEN** its summary row reads untested and its notes carry the registry note verbatim

#### Scenario: Note appended after verdict notes
- **WHEN** an enabled registry model carries a note and its logs also produce verdict-derived notes
- **THEN** the row's notes carry the verdict-derived notes first and the registry note after them

#### Scenario: Disabled model kept out of the README
- **WHEN** a registry model is disabled and its logs carry a verdict
- **THEN** the README summary has no row for it and its date ignores that model's logs, while the grid document lists it marked `(disabled)` and the exported data keeps its verdict with `enabled` false

### Requirement: Shipped verdicts list exactly the registry roster
An L0 test SHALL fail when the generated verdict data lists a model set different from the registry roster, or when the README model-support summary lists a model set different from the roster's enabled entries. Outgoing IDs SHALL count as extra and incoming IDs as missing. A roster edit therefore cannot reach the default branch until the report has been regenerated from the run logs.

#### Scenario: Roster bumped without regeneration
- **WHEN** an enabled registry entry's ID is replaced and the report has not been regenerated
- **THEN** the L0 suite fails, naming the outgoing ID as extra and the incoming ID as missing

#### Scenario: Regenerated report
- **WHEN** the report has been regenerated after the bump
- **THEN** the test passes, with the new IDs shown as untested until a matrix run measures them

#### Scenario: Disabled row in the data only
- **WHEN** a registry entry is disabled and the report has been regenerated
- **THEN** the test passes with the entry present in the verdict data and absent from the README summary
