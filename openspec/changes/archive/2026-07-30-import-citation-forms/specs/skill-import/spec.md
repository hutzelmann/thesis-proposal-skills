## ADDED Requirements

### Requirement: Citation form conversion

When converting a source document, the skill SHALL choose the citation syntax by the role the citation plays in its sentence: where the source names the cited authors as the actor of the sentence, the name SHALL be removed from the prose and the citation written in the author-in-text form; where the citation stands as evidence for a claim, it SHALL be written in the bracketed form. The skill SHALL NOT leave an author name typed in the prose immediately before a bracketed citation, because such a name is a copy that stops tracking the reference entry.

#### Scenario: Source names the authors as the actor

- **WHEN** the source reads "Smith et al. [1] propose a drift detector"
- **THEN** the imported text carries the author-in-text citation alone and the typed name "Smith et al." is gone from the prose

#### Scenario: Source cites as evidence

- **WHEN** the source reads "Silent degradation is widely reported [1]."
- **THEN** the imported text carries the bracketed citation and no author name appears in the sentence

#### Scenario: Author-date source

- **WHEN** the source uses an author-date style, naming authors in the running text as "Smith et al. (2020) propose"
- **THEN** the imported text uses the author-in-text form, with neither the typed name nor the year left in the prose

#### Scenario: Reference cannot be resolved

- **WHEN** a source citation has no reference entry that can be recovered
- **THEN** the existing TODO marker behavior applies and no author name is invented to accompany it
