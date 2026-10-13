## MODIFIED Requirements

### Requirement: Import names the continuation path
The import summary SHALL close with the stage handoff (skill-packaging), whose recommended step is chosen by the class of gap the import left rather than by a fixed pointer: prose gaps that the source did not fill lead to a writing pass, a reference shortfall leads to a literature search, and absent research questions or an absent method lead back to developing the idea. Where several classes apply, the one that blocks the most leads and one other may be an alternative. The summary SHALL state that the `[TODO: …]` markers are the work queue and that the notes file's Next Focus ranks them. Import remains a single pass: naming the next step SHALL NOT start it, and no gap is filled in the import run.

#### Scenario: Import leaves prose gaps
- **WHEN** the import completes with `[TODO: …]` markers for content the source did not supply
- **THEN** the handoff recommends a writing pass to close them, without naming a skill, and the summary says the markers are the work queue with the notes file's Next Focus ranking them

#### Scenario: Import leaves a reference shortfall
- **WHEN** the mechanical check reports fewer references than the guidelines require
- **THEN** the handoff names a literature search for that gap, rather than pointing the shortfall at a writing pass

#### Scenario: Source supplied no research questions
- **WHEN** the source carried no research questions or no method, so those sections hold only markers
- **THEN** the summary says the gap is idea substance and the handoff recommends developing the idea before any writing pass

#### Scenario: Naming the next skill does not start it
- **WHEN** the handoff recommends a continuation step
- **THEN** the import run ends there and no gap is filled, no further skill runs, and the user decides what happens next
