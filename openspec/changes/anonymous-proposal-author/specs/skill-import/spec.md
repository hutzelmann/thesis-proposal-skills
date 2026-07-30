## MODIFIED Requirements

### Requirement: Personal data stripped on import
The skill SHALL remove personal data (the writer's own name, matriculation numbers, postal addresses, emails, supervisor names/contacts) and forbidden content (timelines, chapter outlines) from the imported result, and SHALL list what was removed. The imported file SHALL NOT carry the writer's name in the metadata block or in body text.

#### Scenario: Cover page with matriculation number
- **WHEN** the source PDF carries a matriculation number and supervisor emails
- **THEN** the output contains neither and the removal note names both

#### Scenario: Cover page with the student's name
- **WHEN** the source PDF names its author on the cover page
- **THEN** the imported file carries no `author` metadata key and no name in the body, and the removal note reports the dropped name
