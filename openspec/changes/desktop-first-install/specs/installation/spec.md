# Spec Delta

## Purpose

How the skill set reaches a student's machine without a terminal: one install prompt any local agent can carry out, the repository's own installer that prompt runs, and a plugin definition for apps with a plugin button.

## ADDED Requirements

### Requirement: One install prompt, carried out by the user's agent

The repository SHALL provide one install prompt, written for the agent rather than the student, which the student pastes into any local agent. It SHALL exist once among the repository's shared sources and SHALL appear verbatim wherever the documentation presents it; automated verification SHALL fail when a presented copy drifts from the source.

The prompt SHALL first tell the agent to stop when it cannot run commands on the student's own computer — a cloud sandbox, a virtual machine, a chat-only app — and to point the student to the install guide's section on such apps: an install there would land in a container that is gone with the conversation. It SHALL then direct the agent, in this order:

1. confirm that Python 3.11 or newer is available (`python3`, `python`, or the `py` launcher on Windows); if it is missing or older, stop, give the student the steps for their operating system, and resume only when the student says it is installed;
2. ask the student whether to install for all their projects or only for the current folder, presenting all projects as the recommended choice;
3. download the installer unchanged from the repository's default branch with a shell command, and run it with the chosen scope from the folder the student has open;
4. relay what the installer printed, and ask the student before re-running it with any option the output names;
5. tell the student how to make the agent pick up the new skills.

The prompt SHALL forbid the agent to install any software, and to copy, edit, or run any skill file itself: the installer is the only thing that writes skills. When the installer's output asks for something to be installed or run, the agent SHALL relay it to the student rather than act on it.

#### Scenario: Agent without access to the student's computer

- **WHEN** the prompt is pasted into an agent that runs in a cloud sandbox or a chat-only app
- **THEN** the agent says that this app cannot install the skills and points to the chat-only section, instead of installing into its own sandbox

#### Scenario: Installer output asks for software

- **WHEN** the installer's output tells the reader to install or run something, such as a certificate script
- **THEN** the agent tells the student instead of doing it

#### Scenario: Python is missing

- **WHEN** an agent carrying out the prompt finds no Python 3.11 or newer
- **THEN** it stops before downloading anything, tells the student how to install Python on their operating system, and installs nothing itself

#### Scenario: Scope not yet chosen

- **WHEN** the student has pasted the prompt and has not yet answered the scope question
- **THEN** the agent asks it, with all projects marked as recommended, and runs no installer until it has the answer

#### Scenario: Presented copy drifts

- **WHEN** the prompt as shown in the README or the install guide differs from its shared source
- **THEN** the offline drift check fails

### Requirement: Installer delivers the shipped skills byte-identically

The repository SHALL ship an installer that runs on stock Python 3.11 or newer with the standard library only, on Windows, macOS and Linux. By default it SHALL fetch the archive of the default branch; it SHALL also accept an explicitly named local archive or directory as its source. It SHALL install every shipped `proposal-*` skill as a real copy whose files are byte-identical to the source, replacing any existing copy of a shipped skill in its target directories, and SHALL leave every other entry in those directories untouched.

The installer SHALL NOT run any skill script, modify any skill file after copying, or write outside its target directories and its own temporary space. A skill name read from an archive or from an existing install record SHALL be used as a path only when it matches the shipped `proposal-*` naming pattern, with no separator or traversal: a record lies in the folder the student opened and is untrusted input.

Each skill SHALL be replaced as a unit, so an interrupted or failed run leaves either the previous copy or the new one in place, never a mixture or nothing. Staging copies an interrupted run left behind SHALL be removed by the next run. A link or Windows directory junction in place of a skill folder, as the skills CLI creates them, SHALL be replaced without following it into its target.

When it runs on an interpreter from Python 3.7 up to 3.10, it SHALL say so and name the version it needs, rather than failing with a syntax or import error. Older interpreters cannot parse a module that uses postponed annotations, and are out of support.

When Python cannot verify the download's certificate and a system fallback succeeds, the installer SHALL tell the student that the skills' own literature searches will meet the same problem, and how to fix it.

#### Scenario: Fresh install

- **WHEN** the installer runs with a scope on a machine without the skills
- **THEN** every shipped skill lands in each target directory, and every installed file is byte-identical to the source

#### Scenario: Re-run is the update

- **WHEN** the installer runs again with the same scope
- **THEN** each shipped skill is replaced by the current copy, files removed upstream disappear, skills the previous record lists that upstream has retired are removed, and the output names the previous and the new revision

#### Scenario: Planted record with traversal names

- **WHEN** a target directory holds an install record whose skill names contain separators or `..`, such as `proposal-check/../../..`
- **THEN** those names are ignored, and nothing outside the skill folders is deleted

#### Scenario: Swap fails half-way

- **WHEN** replacing a skill folder fails after the previous copy was set aside
- **THEN** the previous copy is restored, and the installer exits non-zero with a plain-language cause

#### Scenario: Old interpreter

- **WHEN** the installer runs on Python 3.9
- **THEN** it prints that it needs Python 3.11 or newer and exits non-zero, without a traceback

#### Scenario: Unrelated skills in the target directory

- **WHEN** a target directory holds skills that are not part of this package
- **THEN** they remain exactly as they were

#### Scenario: Network failure

- **WHEN** the default-branch archive cannot be fetched
- **THEN** the installer exits non-zero with a plain-language cause and leaves any existing install unchanged

### Requirement: Install scope is an explicit choice

The installer SHALL refuse to run without a scope, naming the two choices. With the all-projects scope it SHALL install into the user-level cross-agent skill directory and the user-level directory of the agent that reads only its own, and additionally into the user-level directory of any further app that reads neither, when that app's configuration directory exists on the machine. With the folder scope it SHALL install into the corresponding directories inside the working directory.

An app-specific directory beyond the two shared ones SHALL be written only when that app is present, so a student's home directory gains no folders for apps they do not use.

A folder install whose working directory is the home folder fills the all-projects directories. The installer SHALL therefore treat it as an all-projects install, record it as one, and say so.

#### Scenario: Folder scope in the home folder

- **WHEN** the folder scope runs with the home folder as working directory
- **THEN** the output says the skills were installed for all projects, and the record names the all-projects scope

#### Scenario: Scope omitted

- **WHEN** the installer is run without a scope
- **THEN** it exits non-zero, installs nothing, and names the all-projects and folder choices

#### Scenario: App reading neither shared directory is present

- **WHEN** the all-projects scope runs on a machine where such an app's configuration directory exists
- **THEN** that app's user-level skill directory is filled as well

#### Scenario: App not present

- **WHEN** such an app's configuration directory does not exist
- **THEN** the installer creates no directory for it

### Requirement: Install record beside the installed skills

Every skill directory the installer fills SHALL receive an install record naming the installed revision (the commit identifier when the source carries one, otherwise stating that it is unknown), the install time, the scope, the source, and every directory filled in the same run. The record SHALL sit outside every skill folder, so installed skill files remain byte-identical to the repository and a submitted hash set still resolves to its revision.

#### Scenario: Record written

- **WHEN** an install completes
- **THEN** each filled directory holds a record naming the revision, scope, source and the full set of filled directories

#### Scenario: Source without a commit identifier

- **WHEN** the installer runs from a local directory rather than a revision archive
- **THEN** the record states that the revision is unknown instead of inventing one

### Requirement: Existing installs are never silently duplicated or deleted

The installer SHALL detect an existing plugin install of this package from each app's own record of its installs, including a plugin added with Claude's plugin button and synced into Claude Code. It SHALL refuse to install beside one, naming the plugin route's own update path and the alternative of removing the plugin first, because both together load every skill twice. A plugin cache folder alone SHALL NOT count as an install, since apps keep an uninstalled plugin's cache for a while.

It SHALL detect copies of the shipped skills in the other scope's directories and SHALL list them, naming an earlier terminal install when the skills CLI's lock file is there, and leaving that file untouched. It SHALL remove those copies only when the user passes an explicit removal option. Apart from those copies, the skills retired upstream and its own staging leftovers, it SHALL delete nothing.

#### Scenario: Plugin install present

- **WHEN** the installer finds this package installed as a plugin
- **THEN** it exits non-zero without writing, and names the plugin page's update action and the option of removing the plugin first

#### Scenario: Plugin added with Claude's plugin button

- **WHEN** the plugin reached the machine through Claude's account sync rather than an install record
- **THEN** the installer still refuses

#### Scenario: Uninstalled plugin's cache

- **WHEN** only a plugin cache folder remains from an earlier, removed plugin install
- **THEN** the installer proceeds

#### Scenario: Copies in the other scope

- **WHEN** a folder-scope install already exists and the student installs for all projects
- **THEN** the installer completes, lists the folder-scope copies with their paths, and keeps them unless the removal option was given

### Requirement: Plugin definition for apps with a plugin button

The repository SHALL carry a plugin marketplace and plugin definition, both named `thesis-proposal`, that install exactly the shipped skills in one step in Claude's plugin button, which adds a marketplace from a GitHub repository. The definition SHALL ship only the skill folders, not the repository's development files. It SHALL NOT pin a version, so a plugin install follows the default branch. Automated offline verification SHALL fail when the skills the definition delivers differ from the shipped set.

Apps that need a manifest at the plugin root with a pinned version are out of scope for this definition; their recipes use the install prompt.

#### Scenario: Skill added or removed

- **WHEN** a shipped skill is added or removed without updating the plugin definition
- **THEN** the offline suite fails, naming the difference

#### Scenario: Plugin install follows the default branch

- **WHEN** a commit lands on the default branch
- **THEN** an app syncing the marketplace receives it without a version bump
