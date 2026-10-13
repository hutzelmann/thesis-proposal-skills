# Spec Delta

## MODIFIED Requirements

### Requirement: Stale install answered before anything else

The first rung SHALL be the possibility that the user's installed skills predate the fix for the problem they are reporting. The skill SHALL direct the user to update their installation the way it was installed and retry before any further diagnosis. Where an install record from the repository's installer is present, the skill SHALL name that route — running the install prompt again — and otherwise SHALL name each route's update action: the install prompt, the plugin page's update action, and the CLI's update command. It SHALL NOT attempt to establish whether the install is current by comparing revision identifiers, because offline it cannot know the newest revision; a recorded revision identifies the install, it does not date it.

#### Scenario: Problem reported on an unknown revision

- **WHEN** a user reports a problem and the currency of their install is unknown
- **THEN** the skill's first instruction is to update the installed skills and retry

#### Scenario: Problem survives an update

- **WHEN** the user confirms they updated and the problem persists
- **THEN** the skill proceeds to the next rung and records in any resulting report that the install was updated first

#### Scenario: Installed through the install prompt

- **WHEN** the user's skill directories hold the installer's record
- **THEN** the update instruction is to paste the install prompt again, not a command from another route

### Requirement: Install identified from workspace evidence

The report SHALL carry enough to identify which revision of the skills produced the problem, drawn only from what the workspace and the user's skill directories already hold: the repository installer's record where one exists, the CLI's lock record where one exists, and a content hash of every installed skill file found in the workspace's skill directories, the user-level skill directories, the plugin install locations of the featured apps, and the apps' own skill folders that the repository's installer lists but never fills. Hashes SHALL cover shipped scripts and reference data, not only instruction files, because a changed script is as capable of causing the problem as changed instructions. The report SHALL name the install route the evidence points to — installer, plugin, CLI, or unknown. It SHALL name each of the apps' own skill folders that holds a copy, relative to the home or the workspace, as one that may shadow the installed skills. Its list of those folders SHALL equal the installer's, enforced offline.

The repository SHALL provide a maintainer-side means of resolving a submitted hash set to the revision that produced it, and of naming any file that matches no known revision as locally modified. Identification SHALL NOT depend on data shipped inside the skills, because installs predating any such addition are exactly the ones most likely to be reported.

#### Scenario: Lock record present

- **WHEN** the workspace holds the installer's lock record
- **THEN** the report carries it unaltered alongside the recomputed hashes

#### Scenario: Install record present

- **WHEN** a skill directory holds the repository installer's record
- **THEN** the report carries the recorded revision, scope and source, names the route as the installer, and still carries the recomputed hashes

#### Scenario: Copy in an app's own skill folder

- **WHEN** a copy of a shipped skill sits in an app's own skill folder, such as OpenCode's in the user's configuration, beside an installer install
- **THEN** the report carries that copy's hashes and a line naming the folder home-relative as one that may shadow the installed skills, and no user name

#### Scenario: Collector run from the shadowing copy

- **WHEN** the app loaded the troubleshoot skill itself from its own skill folder, so the collector runs from the copy that shadows an installer install
- **THEN** the report still names that folder as one that may shadow the installed skills

#### Scenario: Lock record absent

- **WHEN** neither record exists, as with a hand-copied install
- **THEN** the report still carries the per-file hashes and records that the install method is unknown

#### Scenario: Submitted hashes resolved by a maintainer

- **WHEN** a maintainer resolves a submitted hash set against the repository's history
- **THEN** the matching revision is named, and any file matching no revision is reported as locally modified
