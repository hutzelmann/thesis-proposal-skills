## MODIFIED Requirements

### Requirement: Hand-in export
Publish SHALL offer a stripped export for supervisor hand-ins without tooling: references reduced to citation-ready entries with abstracts removed.

The hand-in export is the one publish output that is not an ignorable build artifact — it is a deliverable meant to be kept and sent. Publish SHALL therefore NOT silently replace an existing hand-in export whose content differs from what it would write. It SHALL refuse, report the file and the way to proceed anyway, and exit non-zero. An explicit force option SHALL perform the replacement. Writing content identical to the existing file SHALL succeed silently, so an unchanged rebuild stays free. The skill SHALL relay the refusal to the user rather than resolving it on their behalf, because whether hand edits may be discarded is the user's decision.

#### Scenario: Markdown hand-in
- **WHEN** the user requests the hand-in export
- **THEN** a copy without abstract fields is produced, citations intact

#### Scenario: Hand-in export was edited by hand
- **WHEN** the hand-in export already exists with content differing from what would be written
- **THEN** publish refuses, names the file and the force option, and exits non-zero without writing

#### Scenario: Forced replacement
- **WHEN** the user requests the hand-in export with the force option and a differing file exists
- **THEN** the file is replaced

#### Scenario: Unchanged rebuild
- **WHEN** the hand-in export already exists and its content matches what would be written
- **THEN** the run succeeds without a refusal
