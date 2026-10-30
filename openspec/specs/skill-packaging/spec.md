# skill-packaging Specification

## Purpose
How the skills are packaged, named, kept self-contained, and distributed to user workspaces via the skills.sh ecosystem.

## Requirements

### Requirement: Registry installation from the repository
The skill set SHALL be installable from the public repository via the skills.sh CLI, both all-at-once and per-skill. What is committed on the default branch is what users receive.

#### Scenario: Selective install
- **WHEN** a user installs only the write skill
- **THEN** that skill arrives functional without requiring any sibling skill

### Requirement: Collision-safe naming
Every skill's frontmatter `name` SHALL carry the `proposal-` prefix (the installed directory name derives from the frontmatter name, and same-named skills from other packages silently overwrite each other).

#### Scenario: Installation directory
- **WHEN** any skill of this package is installed
- **THEN** its installed directory name starts with `proposal-`

### Requirement: Functional self-containment
Each skill SHALL be functional standalone: installed alone, it fulfills its purpose without requiring any sibling skill. Shared guidance, structured data, and cross-skill scripts are provided through one of two declared paths:

1. **Synchronized copy** — the asset is materialized as a committed copy inside the consuming skill from a single dev-side source. A synchronized copy is either a whole file or a delimited region of a file. Whole-file copies carry a generated-file marker. A materialized region SHALL NOT carry one: the file it sits in is a rendered page, and a marker would appear to readers of that page. A region is instead located by a position this specification already fixes, so that its boundaries do not depend on an annotation a contributor can move or delete. Automated verification SHALL fail when a copy or a region drifts from its source.
2. **Sibling fallback** — the skill uses a sibling skill's files when that sibling is installed, and its SKILL.md SHALL document the degraded behavior used when the sibling is absent. This path is only permitted where the degraded mode still fulfills the skill's purpose; assets required for a skill's core function SHALL be synchronized copies.

#### Scenario: Shared guidance edited
- **WHEN** the shared source changes without re-materializing copies
- **THEN** the sync verification fails

#### Scenario: Sibling absent
- **WHEN** a skill with a declared sibling fallback runs in a workspace where the sibling skill is not installed
- **THEN** the skill performs its documented degraded behavior instead of failing opaquely

#### Scenario: Asset needed for core function
- **WHEN** a shared asset is required for a skill's core purpose rather than for enrichment
- **THEN** the skill ships it as a synchronized copy, not as a sibling fallback

#### Scenario: Materialized region in a rendered page
- **WHEN** a region of a `SKILL.md` is materialized from a shared source
- **THEN** the rendered page shows no generated-file marker, comment, or banner around it

#### Scenario: Region moved out of its fixed position
- **WHEN** a materialized region no longer sits at the position this specification fixes for it
- **THEN** the offline suite fails naming the skill, rather than materializing the block into the wrong place

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

### Requirement: User-side script constraints

Scripts shipped inside skills SHALL run on stock Python ≥ 3.11 standard library only (no package installs), work on Windows/macOS/Linux, never general-parse YAML (narrow documented extraction only), detect missing interpreters/tools with install guidance, and document an agent-side fallback when script networking is denied.

A skill's instructions SHALL address each script it ships as `<skill-dir>/scripts/<name>`, and SHALL define `<skill-dir>` once in prose as the skill's own directory: the folder holding its `SKILL.md`, which the host names when it loads the skill. No skill SHALL rely on a host-specific substitution variable. The definition resolves a script path and nothing else: it SHALL NOT direct the agent to work from, or write into, the skill's install directory. The documented command still runs from the agent's working directory, where the user's material lives. A skill whose script reads from or writes to a working-directory-dependent location SHALL name that stake beside the definition. A script that another skill owns SHALL ship as a synchronized copy inside the skill that runs it, and SHALL be addressed through `<skill-dir>` like the skill's own scripts — never by an install path, which breaks under user-level and plugin installs, and never relative to the skill's own directory, because `../<sibling>/scripts/` is the cross-skill execution shape the audit remediation forbids.

A skill that cannot locate a script it ships SHALL say so, and SHALL say what consequently went unverified. It SHALL NOT silently substitute its own inspection for a deterministic script: the script exists because the agent's unaided judgement is not equivalent to it.

Every script-bearing skill SHALL state once, beside its `<skill-dir>` definition, that `python3` in its commands stands for any Python 3.11 or newer that answers on the machine — `python`, the `py` launcher, or a versioned name such as `python3.13` — and that the agent keeps the interpreter that worked for the rest of the conversation. The skill's instructions SHALL NOT scatter platform-specific interpreter hints across individual commands. Guidance for a missing Python SHALL point to the install guide rather than prescribe a package-manager command pinned to one Python version. No skill SHALL tell the agent to record the interpreter in a host's instruction file.

#### Scenario: Windows machine without python3 alias

- **WHEN** a script-bearing skill runs on Windows where `python3` is missing or opens only the Microsoft Store, and Python 3.11 or newer answers as `python`, through the `py` launcher, or under a versioned name such as `python3.14`
- **THEN** the agent runs the skill's commands with that interpreter and keeps it for the rest of the conversation, rather than failing opaquely or telling the user that Python is missing

#### Scenario: Only a versioned interpreter

- **WHEN** a script-bearing skill runs on any operating system where neither `python3` nor `python` answers with 3.11 or newer, but a versioned name such as `python3.13` does
- **THEN** the agent runs the skill's commands with that versioned name and keeps it for the rest of the conversation

#### Scenario: No Python at all

- **WHEN** proposal-check runs and no Python 3.11 or newer answers on the machine
- **THEN** it says so, points the user to the install guide's section on installing Python, and performs the script's checks itself with reduced determinism stated; no script-bearing skill names a version-pinned install command

#### Scenario: Interpreter statement present in every script-bearing skill

- **WHEN** the offline suite inspects the skills that ship scripts
- **THEN** each states what `python3` stands for exactly once, beside its `<skill-dir>` definition, and none carries a per-command platform interpreter hint

#### Scenario: Agent runs a documented script command

- **WHEN** an agent runs a script invocation as the skill's instructions give it, with `<skill-dir>` replaced by the directory the host named when it loaded the skill
- **THEN** the path resolves to the installed script, on any host, wherever the skill is installed and whatever the working directory

#### Scenario: Host does not substitute the variable

- **WHEN** the skill runs on a host that substitutes no variable into skill text — every host, since no skill relies on one
- **THEN** the `<skill-dir>` definition names the script's location next to the SKILL.md, and the agent can still find and run it

#### Scenario: No host-specific variable in any skill

- **WHEN** the offline suite inspects the shipped skills
- **THEN** no `SKILL.md` contains a host substitution variable such as `${CLAUDE_SKILL_DIR}`, every documented script invocation has the `<skill-dir>/scripts/` form, and each script-bearing skill defines `<skill-dir>` exactly once

#### Scenario: Fallback prose does not relocate the work

- **WHEN** an agent resolves `<skill-dir>` for a skill whose script depends on the working directory — one that writes its output there or resolves `api-keys.env` there
- **THEN** the definition names the script's location without instructing the agent to work from it, and the skill's outputs and key lookups still resolve against the agent's working directory

#### Scenario: Script cannot be found

- **WHEN** a skill's script is absent or cannot be located
- **THEN** the skill reports that the script did not run and names what was therefore not verified, instead of presenting its own inspection as the script's result

#### Scenario: A skill needs another skill's script

- **WHEN** a skill's instructions run a script that another skill owns
- **THEN** the script ships as a synchronized copy in that skill and is addressed through `<skill-dir>`, and the offline suite fails on any install-path reference to a skill's scripts

### Requirement: Rolling release policy
The default branch `main` SHALL stay the release channel and SHALL hold released versions only: installers receive what it holds, and it moves only by fast-forward to a release commit. Completed work SHALL integrate on the development branch `develop`, where releases are cut at maintainer-chosen milestones as a stamped version, an annotated tag and a dated changelog section. Pushing branches and tags and publishing releases SHALL remain the maintainer's own actions.

#### Scenario: Pre-adoption phase
- **WHEN** changes were pushed to the default branch before the first stamped release
- **THEN** they were live for installers without further release steps, and the changelog records that period as retroactive releases

#### Scenario: Change completed between releases
- **WHEN** a change is completed after the newest release
- **THEN** it lands on the development branch, is listed in the changelog's unreleased section there, and reaches installers only with the next release

#### Scenario: Release cut
- **WHEN** the maintainer cuts a release
- **THEN** the stamp commit on the development branch carries the new version in every skill and a dated changelog section, an annotated tag of that version points at it, and the default branch is fast-forwarded to it

### Requirement: Pre-publish local security gate
Before any publication of the skill set, a local security gate SHALL pass, in this order: the audit-invariant test suite, then a local run of the same skill scanner that audits the published registry entries, executed against the repository's skills staged in isolation from the developer's real agent configuration. The scanner gate SHALL fail on any finding at or above the calibrated risk threshold and SHALL report every finding with its skill, category, and reason. Publication with a failing gate requires an explicit, recorded decision.

#### Scenario: Scanner finds a high-risk pattern
- **WHEN** the local scanner reports a finding at or above the threshold for any skill
- **THEN** the gate exits non-zero, names the skill and the finding, and publication does not proceed by default

#### Scenario: Gate isolation
- **WHEN** the local scanner runs
- **THEN** it scans only the repository's skills, not the developer's installed agent configurations or MCP servers

### Requirement: Post-publish verdict confirmation
After publication, the published audit verdicts for every skill SHALL be fetched from the registry's audit API and compared against a committed baseline. A deviation SHALL be reported as a non-zero result with a per-skill, per-provider diff. The baseline SHALL be updatable only by an explicit command, so silent verdict drift — including provider-side re-scans without a new publication — is always surfaced.

#### Scenario: Provider verdict drifts
- **WHEN** a provider's verdict for any skill differs from the committed baseline
- **THEN** the comparison exits non-zero and names the skill, provider, and both verdicts

#### Scenario: Verdicts match baseline
- **WHEN** all fetched verdicts equal the baseline
- **THEN** the comparison exits zero

### Requirement: Audit-pattern regressions caught by tests
The risk patterns remediated in past audits SHALL be enforced by automated tests over the shipped skill content: no dynamic module loading from input-derived names, no credential lookup outside the documented locations, no instructions to mutate file permissions, no embedded execution of another skill's scripts, and no instructions that pass a secret value through the agent. The tests SHALL run in the default offline test suite.

A shipped script SHALL NOT execute a path it discovered in the user's workspace. Where a skill delegates work to a file the workspace supplies, the shipped script SHALL confine itself to discovering and reporting that file; running it belongs to the agent, which the user already directs. The single shipped script permitted to start a subprocess starts fixed document tools by constant name only, and this SHALL be enforced by the same offline test suite, so that widening it is a reviewed change rather than an incidental one.

#### Scenario: Remediated pattern reintroduced
- **WHEN** a change reintroduces one of the remediated patterns into a skill's shipped content
- **THEN** the offline test suite fails naming the file and the pattern

#### Scenario: Shipped script made to run a discovered file
- **WHEN** a change makes a shipped script execute a build definition it found in the workspace
- **THEN** the offline test suite fails, naming the script and the invariant

### Requirement: Uniform skill opening structure

Every shipped `SKILL.md` body SHALL open with exactly four blocks, in this order, before its first section heading:

1. **Purpose** — one or two sentences in the vocabulary of a person who has never read the repository, stating what the skill produces and for whom. It SHALL NOT restate, soften, or paraphrase any rule stated below it, because the first statement of a rule fixes that rule's scope.
2. **Workflow line** — a single line naming every skill in the set and the order of the main chain, with the containing skill's own name marked. The line SHALL be identical across all skills except for which name is marked, and SHALL mark exactly one name, which SHALL be the name of the skill whose file it appears in. It SHALL be materialized from a single source, which carries the set and leaves the marked name to be filled per skill.
3. **Voice block** — a short block, byte-identical across all skills, fixing the agent's tone: neutral and constructive, never praising the user or their artifacts, never complimenting its own output, chat messages short and precise with findings stated plainly. The block constrains chat conduct only; it SHALL NOT alter what any skill checks, writes, or judges. It SHALL be materialized from a single source.
4. **Mandate** — the skill's agent-facing opening paragraph. It SHALL remain immediately followed by the paragraph that already followed it, so that a paragraph which elaborates or enforces a mandate is never separated from it. It is per-skill wording and SHALL NOT be materialized.

The workflow line is orientation, not a dependency declaration: a skill SHALL remain functional when the siblings it names are not installed.

#### Scenario: Visitor lands on a single skill page

- **WHEN** a person opens one skill's rendered page without knowing the package
- **THEN** the first two blocks tell them what that skill does for them, that the other skills exist, and where the chain starts

#### Scenario: Purpose block would restate a rule

- **WHEN** a purpose block is written so that it also states a constraint the mandate below it states
- **THEN** the purpose block is rewritten to state the deliverable instead, leaving the constraint stated once, by the mandate

#### Scenario: Mandate has an enforcing paragraph

- **WHEN** a skill's mandate is followed by a paragraph that elaborates or mechanically verifies it
- **THEN** no header block is inserted between the two

#### Scenario: Skill added to the set

- **WHEN** a new skill joins the package
- **THEN** it opens with the same four blocks, and the set named on every page stays complete because each page's workflow line is materialized from the one source that was edited

#### Scenario: Skill installed without its siblings

- **WHEN** a skill is installed alone in a workspace
- **THEN** it performs its purpose, treating the sibling names in its workflow line as orientation rather than as available tools

#### Scenario: Voice block governs praise

- **WHEN** any skill reports a result in chat
- **THEN** the message contains no praise of the user or their material and no self-congratulation, per the voice block every skill carries

### Requirement: Opening structure and mandate wording enforced offline

The opening structure SHALL be enforced by the offline test suite rather than by convention. The suite SHALL fail when the workflow line differs from its source or marks a name other than the skill it appears in, when the voice block is missing from any skill or differs from its source, when the block order or the bounded length of the purpose block is violated, when a mandate is separated from the paragraph beneath it, or when a mandate's wording differs from a committed pinned copy of that mandate.

For the materialized blocks, identity across skills SHALL be established by materialization from a single source and verified against that source, not by comparison against a copy embedded in a test. The source is the one place the wording is stated, so a change to it is reviewable as one diff.

Changing a mandate SHALL therefore require editing its pinned copy, so the reword appears as an explicit diff under review instead of passing silently.

#### Scenario: Workflow line drifts on one skill

- **WHEN** one skill's workflow line is reworded, reordered, or left stale after the set changes
- **THEN** the offline suite fails naming that skill

#### Scenario: Sibling's line copied without re-marking

- **WHEN** a skill's workflow line marks a name other than its own
- **THEN** the offline suite fails naming that skill

#### Scenario: Voice block drifts on one skill

- **WHEN** one skill's voice block is reworded or removed
- **THEN** the offline suite fails naming that skill

#### Scenario: Mandate silently reworded

- **WHEN** a change alters the wording of a skill's mandate without updating that mandate's pinned copy
- **THEN** the offline suite fails naming the skill and the mandate

#### Scenario: Mandate deliberately revised

- **WHEN** a mandate is intentionally rewritten and its pinned copy is updated in the same change
- **THEN** the offline suite passes and the reword is visible as a diff in review

#### Scenario: Purpose block grows into a marketing section

- **WHEN** the material before the workflow line exceeds a single paragraph
- **THEN** the offline suite fails

### Requirement: Load-bearing sentences pinned offline
Beyond mandates, sentences whose exact wording carries security or behavioral weight SHALL be pinned: each designated sentence has a committed pinned copy, and the offline test suite SHALL fail when the skill prose no longer contains it verbatim. The pinned set SHALL include at least: every untrusted-data framing sentence, the ideation hard rule against asking for or supplying idea content, the tell-boundary sentence, the proposal anonymity rules, and the always-present `references:` key rule. Changing such a sentence therefore requires editing its pinned copy in the same change, making the reword an explicit diff under review.

#### Scenario: Untrusted-data framing reworded silently
- **WHEN** a change rephrases a pinned untrusted-data sentence in a SKILL.md without touching the pinned copy
- **THEN** the offline suite fails naming the skill and the sentence

#### Scenario: Deliberate reword reviewed
- **WHEN** a change updates both the prose and the pinned copy
- **THEN** the suite passes and the reword is visible as a paired diff under review

### Requirement: Uniform failure-path report offer

Every shipped skill except the one that assembles reports SHALL end a run that failed in a way it cannot resolve with a single offer to assemble a bug report. The offer SHALL be worded identically across those skills, SHALL be materialized from a single source, SHALL appear at most once in a session, and SHALL be an offer: no skill SHALL collect, assemble, or write report material without the user accepting.

The assembling skill SHALL NOT carry the offer at all. It is where the offer leads, so referring itself would be a loop rather than an offer, and its own unresolvable failure — a collector it cannot locate — is covered by the script-location rules that already bind every skill. Materialization SHALL therefore skip that skill rather than treat its absent offer as drift.

The offer SHALL fire on a script exiting non-zero, on a read-only skill detecting that the file it examined changed during its run, on a diagnostic failing repeatedly with no intervening user edit, and on a state the skill cannot proceed from. It SHALL NOT fire on ordinary findings: a proposal with errors is the diagnostic working, not a defect in it, and a skill that treats its own correct output as a bug trains users to ignore the offer.

#### Scenario: Shipped script exits non-zero

- **WHEN** a skill's script fails with a non-zero exit
- **THEN** the skill's report closes with the single offer to assemble a bug report

#### Scenario: Diagnostic reports findings

- **WHEN** a diagnostic skill completes normally and reports findings in the user's proposal
- **THEN** no report offer appears

#### Scenario: Offer declined

- **WHEN** the user does not take up the offer
- **THEN** the skill does not repeat it later in the session and collects nothing

#### Scenario: Offer wording drifts

- **WHEN** one skill's offer wording differs from the source it is materialized from
- **THEN** the offline test suite fails naming that skill

#### Scenario: The assembling skill carries the offer

- **WHEN** the skill that assembles reports contains the offer wording
- **THEN** the offline test suite fails, because that skill is the offer's destination

#### Scenario: Skill-specific sentence added after the offer

- **WHEN** a skill adds its own sentence about a defect particular to it in the closing section
- **THEN** the materialized offer remains byte-identical and the added sentence sits outside it

### Requirement: Cross-skill identical blocks materialized from one source

A block of `SKILL.md` prose that this specification requires to be identical across skills SHALL exist once as a dev-side source and be materialized into each skill's `SKILL.md` by the same automation that materializes synchronized file copies. The workflow line, the voice block, the stage handoff block, and the failure-path report offer SHALL be materialized this way.

Materialization SHALL be byte-preserving on adoption: converting a hand-maintained block into a materialized one SHALL leave every shipped `SKILL.md` unchanged, so that the change is provably a change of authorship and not of content.

Per-skill wording SHALL NOT be materialized, even where a committed copy of it exists. A mandate, a mandate's successor block, and a load-bearing pinned sentence are pinned precisely so that revising them requires a deliberate paired edit; generating them from the prose would make the pin restate whatever the prose says and confirm any reword, including an unintended one.

#### Scenario: Shared block reworded

- **WHEN** the voice block's source is reworded and the sync is run
- **THEN** every skill's voice block is rewritten from it, and the reword is reviewable as a single source diff

#### Scenario: Skill joins the set

- **WHEN** a new skill is added to the package
- **THEN** the set named in the workflow line is edited in one source, and every skill's workflow line is materialized from it

#### Scenario: Adoption leaves content unchanged

- **WHEN** a previously hand-maintained identical block is first materialized
- **THEN** no shipped `SKILL.md` changes content

#### Scenario: Per-skill wording proposed for materialization

- **WHEN** a mandate, mandate successor, or pinned sentence is proposed to be generated from the skill's prose
- **THEN** it remains hand-maintained, because a pin derived from what it guards guards nothing

#### Scenario: Handoff block reworded

- **WHEN** the stage handoff block's source is reworded and the sync is run
- **THEN** every skill's `## Handing over` section opens with the new wording, and the skill's own route sentences after it are left unchanged

### Requirement: Descriptions state what the skill does and when to use it
Every skill's frontmatter `description` SHALL be written in the third person and SHALL carry both what the skill produces and the situations that should trigger it. Trigger clauses SHALL name the situations in the vocabulary a user would use to describe their own position, not only the vocabulary this package uses for the task, and SHALL cover the languages the intended users write in. A description SHALL NOT be the only place a rule is stated, and SHALL NOT promise behaviour the skill does not implement.

#### Scenario: Description written in the second person
- **WHEN** a description addresses the reader as "you" or speaks as "I"
- **THEN** the packaging checks fail

#### Scenario: Trigger clause absent
- **WHEN** a description states only what the skill does, with no triggering situation
- **THEN** the packaging checks fail

### Requirement: One owner per contested trigger term
High-signal trigger terms SHALL be assigned to exactly one skill in a tracked table, and a skill SHALL NOT use a term its description does not own. Terms that are legitimately common across skills SHALL be listed explicitly as shared rather than left implicit. Moving a term between owners SHALL require editing the table, so a boundary change is visible in review rather than emerging from a reworded sentence.

#### Scenario: Second skill claims an owned term
- **WHEN** a skill's description uses a trigger term another skill owns
- **THEN** the packaging checks fail, naming both skills and the term

#### Scenario: Boundary deliberately moved
- **WHEN** the owned-trigger table assigns a term to a different skill and that skill's description uses it
- **THEN** the packaging checks pass

### Requirement: A skill that declines a contested situation names the one that owns it
Where two skills plausibly answer the same user situation, the skill that does not own that situation SHALL say so in its description and SHALL name the skill that does. Disambiguation SHALL be visible at selection time, since no skill body has been loaded when the choice is made.

#### Scenario: Adjacent skill named
- **WHEN** a description declines a neighbouring situation
- **THEN** it names the skill that handles it

### Requirement: Frontmatter contract
Every skill's frontmatter `name` SHALL equal its directory name and SHALL be within the length the skill format allows. The `description` SHALL be within both the format's limit and a tighter repository budget, and the combined metadata of all skills SHALL stay within a stated total, because every skill's metadata is loaded into context whether or not that skill is used. Beyond `name` and `description`, frontmatter MAY carry exactly three optional keys defined by the Agent Skills standard, each under a per-field rule; frontmatter SHALL carry no other keys.

- `license` SHALL be present on every skill and SHALL agree with the license the repository ships at its root, so the installed skill folder carries its terms.
- `compatibility` SHALL appear only on skills with genuine environment requirements beyond a standard agent setup — the publish skill (document toolchain) and the literature-search skill (network access) — and SHALL be rejected on any other skill, so the field keeps signal.
- `metadata` SHALL carry only a `version` entry — the suite's semantic version, shared by all skills and copied by the publish pipeline from its single hand-edited source; it SHALL NOT be hand-maintained in the skills, and one version SHALL never name two published snapshots.

#### Scenario: Name diverges from its directory
- **WHEN** a skill's frontmatter name does not match the directory it lives in
- **THEN** the packaging checks fail

#### Scenario: Metadata budget exceeded
- **WHEN** the combined frontmatter of all skills exceeds the stated total
- **THEN** the packaging checks fail

#### Scenario: Unknown frontmatter key
- **WHEN** frontmatter carries a key outside the admitted set
- **THEN** the packaging checks fail

#### Scenario: Optional field on the wrong skill
- **WHEN** `compatibility` appears on a skill without stated environment requirements
- **THEN** the packaging checks fail

#### Scenario: License field drifts from the shipped license
- **WHEN** a skill's `license` value no longer agrees with the repository's root license
- **THEN** the packaging checks fail

#### Scenario: Version stamped at publish
- **WHEN** the publish pipeline runs
- **THEN** every skill's `metadata.version` identifies the published snapshot, and a bug report against that snapshot resolves to it without searching revision history

### Requirement: Body size limits
A skill body SHALL stay within the line limit published in the skill-authoring guidance this package follows, and SHALL NOT exceed twice the median body size of the suite, so that one skill cannot grow disproportionate to its siblings without the growth being noticed. Content beyond those limits SHALL move to reference files rather than raising the limits.

#### Scenario: Body exceeds the published cap
- **WHEN** a SKILL.md body grows past the guidance's line limit
- **THEN** the packaging checks fail

#### Scenario: One skill outgrows its siblings
- **WHEN** a body exceeds twice the median body size across the suite
- **THEN** the packaging checks fail

### Requirement: Installation verified against the tracked tree
An on-demand check SHALL install the repository's tracked tree — exported as the registry would serve it, never the working directory — using the installation command documented in the README, into an isolated environment that cannot touch the operator's own agent configuration. It SHALL assert that exactly the shipped skills install, that installed skill files are byte-identical to the repository's, and that an installed skill's script runs correctly from its installed location. The check SHALL run in CI on the default branch and on a schedule, with the installer deliberately unpinned so a CLI-side regression that would break user installs surfaces here first. It SHALL NOT join the offline test gate.

#### Scenario: Untracked skill-shaped directory in a checkout
- **WHEN** a local checkout carries untracked skill directories (agent integration helpers)
- **THEN** the check, operating on the tracked tree, still counts exactly the shipped skills — and an accidentally committed extra skill directory fails the count

#### Scenario: README command drifts
- **WHEN** the README's documented install command is removed or reworded beyond recognition
- **THEN** the check fails at command extraction rather than silently testing a command nobody documents

#### Scenario: Installed script smoke
- **WHEN** the check runs the installed check script against a known-broken fixture
- **THEN** the script exits with findings, proving scripts and references travel and resolve from the installed location

#### Scenario: Installer regression upstream
- **WHEN** a new skills-CLI release breaks installation of this repository
- **THEN** the scheduled run fails without any commit here, naming the installer as the moving part

### Requirement: Stage handoff at stopping points

Every shipped skill SHALL carry a closing section, `## Handing over`, placed directly before the failure-path report section — and last in the skill that carries no report offer — that opens with one shared handoff block and continues with the skill's own exit condition and routes. The shared block SHALL define:

- **The milestone ladder**: seeded idea → complete draft → ready for supervisor discussion → handed in. A draft is complete when every canonical section is written and its open markers stand only where the student must decide or supply something. A proposal is ready for supervisor discussion when the mechanical check reports no errors and a review of its current text names no proposal blocker. It is handed in when a built document or hand-in export exists and the student sends it. Execution readiness SHALL be named as outside the ladder: the clarify-early items are settled during the thesis, not before approval.
- **When to hand over**: at a stopping point — a stage finished, a verdict given, or the user asking what to do now — also when the user said they cannot answer, and not again unasked while nothing has changed. A turn inside a dialogue that continues is not a stopping point.
- **The shape**: the message SHALL close with these lines and nothing after them — exactly one `Where it stands:` line (the proposal's position on the ladder and, in plain words, what blocks the next milestone), exactly one `Next:` line (one recommended step, its reason, and — where the user can trigger it — a quoted phrase they can send or a one-word approval), and zero to two alternatives, each an `Or:` line; a list of at most two items under one `Or:` label is the same thing, and a list of an anchored choice's options under `Next:` continues that line. The labels follow the chat language (German: `Stand:`, `Als Nächstes:`, `Oder:`).
- **Actions, not skills**: the step SHALL be named as an action in the user's terms, never by a skill's name; on approval the instructions of the skill that owns the step govern it, and where that skill is not installed the skill SHALL say so and state the step in words. The fixed wording of the failure-path report offer is exempt.
- **User control**: a handoff recommends and SHALL NOT act — no review finding applied, no missing choice supplied, nothing built, published or sent, no other skill run, unless the user approves that step.
- **Anchored decisions**: when the next step needs a choice only the student can make, the handoff SHALL quote what the student's own text already says, state what the choice changes, and offer at most three options the student's material supports plus a way out — never a bare open question, never an option the material does not contain.
- **Superseded reviews**: a review covers the text it judged. When the research questions, scope, method or contribution delta differ from what a review judged, or a passage one of its blockers cites has changed, the review is superseded, and the recommended step SHALL be a fresh review — never only the statement that no current review exists.

The block SHALL stay short enough that no body crosses the size limits, and each skill's own routes SHALL follow it in a few sentences rather than restating it.

#### Scenario: Review finished with blockers
- **WHEN** a review ends with two proposal blockers
- **THEN** the message closes with a `Where it stands:` line naming the blockers as what stands between the draft and supervisor discussion, one `Next:` line recommending a revision of those blockers with a phrase the user can send, and at most two `Or:` lines

#### Scenario: Nothing changed since the last handoff
- **WHEN** the user asks a side question after a handoff and nothing about the proposal changed
- **THEN** the answer does not repeat the handoff lines

#### Scenario: No skill names in the handoff
- **WHEN** the recommended step is a fresh review
- **THEN** the `Next:` line names it as a review of the current draft and contains neither a skill identifier nor the phrase "review skill"

#### Scenario: Approval crosses skills
- **WHEN** the user approves a recommended revision at the end of a review
- **THEN** the revision follows the instructions of the skill that owns writing, not the review skill's

#### Scenario: Decision put to the student
- **WHEN** a blocker can only be resolved by a choice of the student's
- **THEN** the handoff quotes the passage concerned, says what the choice changes, offers at most three options drawn from the student's own material plus a way out, and asks no unanchored question

#### Scenario: Review judged an earlier scope
- **WHEN** the proposal now carries two research questions and one site while the review beside it judged four research questions and two sites
- **THEN** the handoff says that the review judged the earlier version and recommends a fresh review of the current draft

#### Scenario: Execution detail is not a milestone
- **WHEN** a ready proposal leaves model versions and an audit sample size to be fixed during the thesis
- **THEN** the handoff places the proposal at ready for supervisor discussion and does not recommend settling those items before hand-in

#### Scenario: Handing over section misplaced
- **WHEN** a skill's `## Handing over` section is missing, follows the report section, or its opening block differs from the shared source
- **THEN** the offline test suite fails naming that skill

### Requirement: Script output encoding

Every user-side script with a command-line entry point, whether shipped inside a skill or the repository installer, SHALL write its standard output and standard error as UTF-8, whatever encoding the platform gives a pipe or console. The switch SHALL happen before the script writes anything. The installer is the one exception to that ordering: it makes the switch directly after its interpreter-version check, which stays its first statement. Switching SHALL keep each stream's existing error handler, so a diagnostic that was escaped before is still escaped and never raises. It SHALL NOT change line-ending translation or buffering. A stream that cannot be reconfigured, such as an in-memory buffer a caller substituted or an absent stream, SHALL be left exactly as it is. Messages a script captures as text from a program it starts SHALL be decoded as UTF-8, never in the platform's default encoding, and a byte that is not UTF-8 SHALL NOT abort the script. Files a script reads or writes keep their own explicit UTF-8 encoding; this requirement concerns only the two output streams and captured program messages.

#### Scenario: Output outside the pipe's code page

- **WHEN** a script runs with its output streams in a single-byte code page such as cp1252, as a Windows pipe gives them, and its output contains a character outside that code page, such as an author name with `Ł` or `ő`
- **THEN** the script writes that character as UTF-8 and exits with the code its documentation gives for that run, not with an encoding error

#### Scenario: Error handler and line endings preserved

- **WHEN** a script switches a stream whose error handler is not the default, such as `backslashreplace` (standard error) or `surrogateescape` (standard output under a POSIX C locale), or whose line endings are translated
- **THEN** the stream is UTF-8 afterwards and keeps that error handler and that line-ending translation

#### Scenario: Stream without reconfiguration

- **WHEN** a script's entry point is called with an output stream that cannot be reconfigured, such as an in-memory text buffer, or with no stream at all
- **THEN** the script runs as before and writes to that stream unchanged

#### Scenario: Captured program messages outside the code page

- **WHEN** a script captures the messages of a program it starts, such as the document converter or the typesetter, and they contain a UTF-8 character whose bytes the platform's code page cannot decode, such as `Ł`, or a byte that is not UTF-8 at all
- **THEN** the script decodes them without an error, whether the program succeeded or failed, and a failure report quotes the character intact

#### Scenario: Entry point without the switch

- **WHEN** a user-side script's entry point does not make the switch first (for the installer: directly after its version check), a script family's switch differs from the others, or a user-side script captures a program's messages as text without naming their encoding
- **THEN** the offline test suite fails and names the script

### Requirement: Workspace-files block in every skill
The workspace rules SHALL be stated once, as a shared block, and materialized into every shipped `SKILL.md` by the automation that materializes the other shared blocks. The block SHALL cover:

- the proposal location: the working directory, unless the workspace `guidelines.md` configures a subdirectory; a proposal's files never go into a host's scratch or temporary folder;
- the proposal family in its folder, listed once as a table from each role (proposal, notes, harvest record, review, supervisor feedback, handout, built output, kept file, figure) to its file name, and its slug, including that a rename moves the whole family (proposal-file-format);
- the workspace-level, build, troubleshooting-capture and installer-managed files that may also be present;
- the rule that working material stays out of the workspace, including what to do when no temporary location is writable.

The block SHALL be the whole content of a `## Workspace files` section placed directly before `## Handing over`. No per-skill sentence SHALL be added to that section. Outside the block, a skill's prose SHALL refer to the proposal location without restating its definition, except where a pinned mandate or a script-location fallback paragraph already states it; this requirement changes neither.

The offline suite SHALL fail in any of these cases:

- the section is missing, appears more than once, or stands anywhere but directly before `## Handing over`;
- its content differs from the block;
- it holds anything beyond the block.

The materialization SHALL locate the block's paragraphs without consuming a sentence added after them, so a skill-specific addition fails the suite instead of being silently deleted. The roles of the block's family table SHALL be the roles the mechanical check classifies family files into, and each row's file names SHALL classify as its role. The file names the block lists as allowed and the file names the mechanical check never reports SHALL agree, and the installer-managed folders the block names SHALL agree with the installer's own tables. The offline suite SHALL fail when one side names a role or a file the other does not.

#### Scenario: Block reworded
- **WHEN** the block's source is reworded and the sync runs
- **THEN** every skill's `## Workspace files` section carries the new wording and nothing else in any `SKILL.md` changes

#### Scenario: Skill-specific sentence appended to the section
- **WHEN** a contributor appends a sentence after the block in one skill's `## Workspace files` section
- **THEN** the offline suite fails naming that skill, and running the sync leaves the sentence in place

#### Scenario: Section misplaced
- **WHEN** one skill's `## Workspace files` section stands anywhere but directly before `## Handing over`
- **THEN** the offline suite fails naming that skill, and the sync refuses to write it

#### Scenario: Family table drifts from the check
- **WHEN** the block's family table gains a role the mechanical check does not classify, or the check gains a role the table lacks
- **THEN** the offline suite fails naming the role

#### Scenario: Role name drifts from the check
- **WHEN** the block's table names the review `review.md` and the mechanical check classifies a review under any other name
- **THEN** the offline suite fails naming the role and both names

#### Scenario: Allowed names drift from the check
- **WHEN** the block gains an allowed workspace file that the mechanical check would still report, or the reverse
- **THEN** the offline suite fails naming the file

#### Scenario: Installer gains a skill folder
- **WHEN** the installer's tables gain a workspace skill folder that the block does not name
- **THEN** the offline suite fails naming the folder

#### Scenario: Body size after the block lands
- **WHEN** the block is materialized into all eleven skills
- **THEN** every body stays within the published line limit and within twice the suite's median body size

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
