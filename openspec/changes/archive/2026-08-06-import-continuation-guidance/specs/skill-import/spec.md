## ADDED Requirements

### Requirement: Import names the continuation path
The import summary SHALL close by naming the next step, chosen by the class of gap the import left rather than by a fixed pointer: prose gaps that the source did not fill go to the write skill, a reference shortfall goes to the literature-search skill, and absent research questions or an absent method go to the ideation skill. The summary SHALL state that the `[TODO: …]` markers are the work queue and that the notes file's Next Focus ranks them. Import remains a single pass: naming the next skill SHALL NOT start it, and no gap is filled in the import run.

#### Scenario: Import leaves prose gaps

- **WHEN** the import completes with `[TODO: …]` markers for content the source did not supply
- **THEN** the summary names the write skill as the way to close them, and says the markers are the work queue with the notes file's Next Focus ranking them

#### Scenario: Import leaves a reference shortfall

- **WHEN** the mechanical check reports fewer references than the guidelines require
- **THEN** the summary names the literature-search skill for that gap, rather than pointing the shortfall at the write skill

#### Scenario: Source supplied no research questions

- **WHEN** the source carried no research questions or no method, so those sections hold only markers
- **THEN** the summary says the gap is idea substance and names the ideation skill for it

#### Scenario: Naming the next skill does not start it

- **WHEN** the summary names a continuation skill
- **THEN** the import run ends there and no gap is filled, no further skill runs, and the user decides what happens next
