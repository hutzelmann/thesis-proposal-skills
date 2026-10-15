# Spec Delta

## MODIFIED Requirements

### Requirement: Users never work in this repository
All user activity happens in their own workspace; this repository is exclusively for developing and testing the skills, and its documentation SHALL say so. The install guide SHALL state that the proposals folder is a folder of the student's own, empty when they start, and never a clone or copy of this repository, and that the repository's contributor instruction file is meant for people developing the skills and is never copied into a proposals folder. Wherever the guide names the workspace root, it SHALL call it the proposals folder, and it SHALL state that each proposal gets a folder in it, naming when the proposal-location setting is the better choice without describing any layout the skills do not offer.

#### Scenario: User seeks their files
- **WHEN** a user wonders where their proposals live
- **THEN** the documentation directs them to their own workspace, never into this repository

#### Scenario: Student about to clone the repository as their workspace
- **WHEN** a student reads the install guide before creating a place for their proposals
- **THEN** the guide tells them to create an empty folder of their own, that a clone of this repository is not a proposals folder, and that the repository's contributor instructions do not belong in it

#### Scenario: Student wonders whether to use a subfolder
- **WHEN** a student reads what the proposals folder will contain
- **THEN** the guide says each proposal gets a folder of its own named after it, when collecting those folders in a subfolder is worth it, and that the workspace-level files stay at the top either way
