## RENAMED Requirements

- FROM: `### Requirement: Commit-time sync automation`
- TO: `### Requirement: Commit-time drift check`

## MODIFIED Requirements

### Requirement: Commit-time drift check
At commit time the development repository SHALL check that the generated copies the commit contains match the sources the commit contains. It SHALL refuse a commit whose copies have drifted. The refusal SHALL name the drifted files and the command that regenerates them.

The check SHALL judge the staged snapshot, which is exactly what the commit will contain, and not the working tree. It SHALL NOT stage, write, revert or otherwise modify any file: only the commit's author decides what a commit contains.

The regeneration command SHALL name exactly the files it rewrote, so the files to stage after a refusal are the files it names. Continuous integration SHALL keep an independent drift check as backstop for bypassed hooks.

#### Scenario: Shared source edited and committed
- **WHEN** a contributor stages an edit to a shared source and commits without running the sync script
- **THEN** the commit is refused, the message names the drifted copies and the regeneration command, and the index, the working tree and the branch are exactly as they were before the attempt

#### Scenario: Unstaged edits are never swept into a commit
- **WHEN** the working tree holds unstaged edits, the contributor's own or another session's in a shared checkout, to a `SKILL.md`, a generated copy or a shared source, and a commit is made from other staged changes
- **THEN** the commit contains exactly what was staged, and every unstaged edit remains unstaged and byte-for-byte unchanged

#### Scenario: Copies regenerated but not staged
- **WHEN** a contributor stages a shared-source edit, regenerates the copies in the working tree, and commits without staging the regenerated files
- **THEN** the commit is refused, because the staged copies still do not match the staged source

#### Scenario: Staged snapshot in sync
- **WHEN** the staged copies match the staged sources, whatever the working tree holds
- **THEN** the commit proceeds and nothing is added to it

#### Scenario: Regeneration on a tree already in sync
- **WHEN** the regeneration command runs on a tree whose copies already match their sources
- **THEN** it names no file as rewritten and says that the copies are in sync

#### Scenario: Hook bypassed
- **WHEN** stale copies reach the repository with the commit-time check bypassed
- **THEN** the continuous-integration drift check fails
