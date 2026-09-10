## MODIFIED Requirements

### Requirement: Supervise feedback coverage

The harness SHALL carry an L1 task that runs the supervise skill against a synthetic raw submission fixture and asserts the feedback contract with dedicated verdict functions: the feedback exists as the slug-named feedback file, it carries at most five curated points, it opens with one of the student-facing verdict tiers — including the idea-stage rendering in English and German — the feedback contains no personal data from the fixture, every skill pointer in the feedback names a skill that exists in the set, the feedback carries the shared closing note verbatim in the language it was written in, and any literature the feedback cites is woven rather than listed: every DOI it carries sits inside a numbered point or a prose block rather than a bulleted or bare citation list, is recorded in the companion notes file, and at most three distinct papers are cited — a feedback that cites no literature passes that verdict. The closing-note verdict SHALL fail on a paraphrase, on the wrong language's snippet, and on a closing note that arrives with markup the shared snippet does not carry. The synthetic fixtures SHALL include at least one non-standard-format submission (pasted-text fragment or PDF-shaped input) so normalization is exercised, not bypassed. Non-interactive runs (the Inspect task and the dev runner) SHALL pre-answer the borderline deferral and the literature approval in the request so a single-turn run cannot stall waiting for the professor.

#### Scenario: Feedback contract asserted
- **WHEN** the supervise L1 task runs against a messy synthetic submission
- **THEN** the scorers report feedback presence, point count, verdict tier, personal-data absence, skill-pointer validity, closing-note fidelity, and literature placement as separate verdicts

#### Scenario: Personal data leak caught
- **WHEN** a run leaves the fixture's fake student name or matriculation number anywhere in the feedback
- **THEN** the personal-data verdict fails and names the leaking file

#### Scenario: Paraphrased closing note caught
- **WHEN** a run rewrites the closing note instead of quoting the shared snippet
- **THEN** the closing-note verdict fails and says the snippet was not carried verbatim

#### Scenario: Standalone literature list caught
- **WHEN** a produced feedback carries its papers as a bulleted list or as bare citation lines rather than inside the points
- **THEN** the literature verdict fails and names the offending DOI

#### Scenario: Unrecorded or excess literature caught
- **WHEN** a produced feedback cites a DOI absent from the notes file, or cites more than three distinct papers
- **THEN** the literature verdict fails and says which rule was broken

#### Scenario: Literature-free feedback passes the literature verdict
- **WHEN** a produced feedback cites no DOI
- **THEN** the literature verdict passes, because literature is conditional on approval and findings

#### Scenario: Offline verdict coverage
- **WHEN** the L0 suite runs
- **THEN** every supervise verdict function is exercised by unit tests without model calls

#### Scenario: Idea-stage feedback recognized
- **WHEN** the feedback opens with the idea-stage rendering instead of the blunt review vocabulary
- **THEN** the tier verdict passes in both English and German

#### Scenario: Headless run does not stall
- **WHEN** the L1 task or dev runner drives a borderline submission single-turn
- **THEN** the request's pre-answers resolve the deferral and the literature approval, and the run completes
