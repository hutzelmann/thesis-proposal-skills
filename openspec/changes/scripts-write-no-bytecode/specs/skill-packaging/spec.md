## ADDED Requirements

### Requirement: Scripts write nothing into the install directory

A script shipped inside a skill SHALL NOT write into the skill's install directory. A script that imports a sibling module from its own folder SHALL switch off the interpreter's bytecode cache before that import when it runs as the program, and SHALL leave the setting alone when another program imports it. An offline check SHALL run every shipped script that can run as a program from a copy of its skill's folder and fail on a bytecode cache appearing there.

#### Scenario: Script with sibling imports run as documented

- **WHEN** an agent runs a shipped script that imports a sibling module — the literature search, the snowball expansion, or the reference validation — from the workspace by its installed path
- **THEN** the skill's install directory holds exactly the files it held before the run, and no `__pycache__` folder appears beside the script

#### Scenario: Shipped module imported by another program

- **WHEN** the repository's test suite or harness imports a shipped script as a module
- **THEN** that program's own bytecode-cache setting is unchanged by the import

#### Scenario: New script imports a sibling without the switch

- **WHEN** a contributor adds a shipped script that runs as a program and imports a sibling module without switching off the bytecode cache
- **THEN** the offline suite fails, naming the script and the cache files its run left in the copy

#### Scenario: Cache already present in an installed skill folder

- **WHEN** an installed skill folder holds a `__pycache__` folder left by an earlier release or by the user's own interpreter
- **THEN** it does not count as an installed skill file: the troubleshoot report's file hashes leave it out, and the next install replaces the skill folder without it
