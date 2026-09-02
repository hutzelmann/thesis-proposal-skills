# Thesis Proposal Skills

[![CI](https://img.shields.io/github/actions/workflow/status/hutzelmann/thesis-proposal-skills/ci.yml?branch=main&label=CI)](https://github.com/hutzelmann/thesis-proposal-skills/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/hutzelmann/thesis-proposal-skills)](LICENSE.txt)
[![skills.sh](https://img.shields.io/badge/skills.sh-install-2ea44f)](https://www.skills.sh/hutzelmann/thesis-proposal-skills)

Write a convincing Bachelor's or Master's thesis proposal with the help of an AI agent, in English or German.

**The idea stays yours.** The agent does not invent your topic, and it does not steer you toward one it happens to like. It works on the idea you bring: it asks the questions your supervisor would ask, checks whether the field has already answered them, and condenses your own answers into a clean, professional proposal. Keeping you focused and on track is its job; every decision that shapes the thesis stays yours.

The following shows three steps from a real session, condensed, in which a student turns a work anecdote into a finished proposal.

<details>
<summary><b>1 · A vague anecdote becomes a research question</b></summary>

> **Student**: For my Master's thesis I want to do something about ML monitoring. At my student job our churn model quietly got worse for months before anyone noticed. Is there a thesis in that?
>
> **`proposal-ideate`**: There's likely a thesis in this, but the interesting part isn't "the model got worse", it's *why nobody noticed*. That's two different failure modes wearing the same costume. Did the *predictions* silently drift, or could nobody even *check* accuracy, because you only find out if someone actually churned weeks or months later?
>
> **Student**: Both, but mostly the second: churn labels only arrive weeks later. Our dashboard alerted so often that everyone ignored it, and nobody could say whether a high score actually meant the model was worse.
>
> **`proposal-ideate`**: So "detect drift without labels" and "stop crying wolf" are both already being worked on, separately. What none of them do is close the loop back to what actually happened weeks later: whether the drift alerts *would have* predicted the real accuracy drop once the labels finally arrived.

</details>

<details>
<summary><b>2 · Verified literature, not invented literature</b></summary>

> **Student**: The idea file only has five grounding references so far. Build that out into a proper literature base before we draft anything.
>
> **`proposal-lit-search`**: Literature base is now 15 references, each individually verified against Crossref or arXiv rather than taken from search-tool output, with DOIs resolved and titles cross-checked:
>
> - **Sethi & Kantardzic (2015, 2017)**: MD3, an unsupervised drift detector built explicitly to cut false alarms, which is your alert-fatigue problem
> - **Zhang, Bui & Apley (2023, *Technometrics*)**: score-vector monitoring, an alternative signal to compare against distance-based drift metrics
> - **Cerqueira et al. (2026, arXiv)**: benchmarking framework for drift detectors with timing-aware metrics; flagged as a preprint, not yet peer-reviewed
> - **Krempl et al. (2014), Webb et al. (2018), Gonçalves et al. (2014)** and further background on how the field defines and compares drift, and where it names this gap
>
> Keyword searches that mostly returned noise (IoT intrusion detection, materials-science "fatigue" papers) were rejected rather than force-fit, and the file records that the net was cast that wide.

</details>

<details>
<summary><b>3 · Drafted, checked, published</b></summary>

> **Student**: Write the full proposal draft now. Keep my framing and just mark whatever is still open as a TODO.
>
> **`proposal-write`**: The full draft is written to `drift-alert-validity.md`: Introduction · Contribution to the State-of-the-Art · Research Focus and Research Questions · Methodology · Timeline. TODOs are left open exactly where things are undecided, namely the dataset choice and the drift-detector sample. Nothing was invented to fill them.
>
> **Student**: Run the check.
>
> **`proposal-check`**: One error: the `Timeline` section is missing. It needs a real start and end (a month, a semester, or "as soon as possible") and stays at most three lines, no table. That one is yours to answer, not mine to invent. Otherwise clean: no work plans, no personal data, no results asserted as fact.
>
> **Student**: No registered dates yet. I start as soon as my supervisor signs off.
>
> **`proposal-check`**: Timeline added and the check is clean. The submission month stayed an open TODO, since you have not been given one.
>
> **Student**: Good enough for a first hand-in. Build the PDF please.
>
> **`proposal-publish`**: PDF built successfully via typst: `drift-alert-validity.pdf`

</details>

---

This repository holds a set of **agent skills**: instruction packages that teach an AI coding agent (Claude Code, Cursor, Codex and many others) how to guide you from a vague idea to a polished, literature-grounded proposal. You install them once; after that you only ever work on your own files, in your own folder. You never need to touch this repository again.

**Never used an AI agent before?** Start with [docs/getting-started.md](docs/getting-started.md), which walks you through installing an agent from zero.

## What the skills hold themselves to

Whichever skill is running, six rules apply:

- **You take every key decision**: topic, research question, scope, methodology, timeline. Where something is still open, the agent leaves a visible TODO instead of filling the gap with something plausible.
- **Nothing is edited behind your back**: checking and reviewing are read-only, so they diagnose and report without touching a line. Your text changes when you ask for a change.
- **Everything stays advisory**: findings are reported, ordered by severity, and that is where the agent stops. Nothing overrules you and nothing blocks a hand-in.
- **Pushback comes early**: a vague, generic, or already-solved idea is named as such while changing course is still cheap, not after you have written ten pages.
- **Nothing is invented**: no fabricated references, no results claimed before you have them. Every literature entry is verified against Crossref, arXiv, or DBLP before it enters your file.
- **Your supervisor's rules win**: a `guidelines.md` in your folder overrides any default here, from bringing back a section these rules forbid to turning the one-sentence timeline into a full work plan. `proposal-customize` writes that file with you.

## What the skills do

| Skill | What it does for you |
|---|---|
| `proposal-ideate` | Sharpens the idea you bring through Socratic questions and early literature checks (is this already solved?), then captures the result in a proposal file. It never picks a topic for you. |
| `proposal-lit-search` | Finds real, relevant literature (DBLP, Crossref, arXiv, OpenCitations, Semantic Scholar, OpenAlex), by topic or by snowballing from papers you already have, and verifies every entry before adding it. |
| `proposal-write` | Turns your material into proposal prose following proven structure and writing rules. Thin material becomes a TODO, never invented filler. |
| `proposal-import` | Converts an existing proposal (usually a PDF) into the workable format and strips personal data. |
| `proposal-reverse` | Derives the proposal a finished thesis should have had — for a thesis whose proposal was never filed, or for a supervisor turning a thesis they supervised into an exemplar. Writes the plan the thesis started from, without the results it ended with. |
| `proposal-check` | Fast mechanical check: required sections, citation consistency, forbidden content, leftover TODOs, estimated length. |
| `proposal-review` | Supervisor-style content review: a verdict on whether there is a thesis here (ready / needs revision / no viable thesis core), then every weak point with a concrete suggestion. |
| `proposal-publish` | Optional: builds a compact PDF via pandoc with typst or an existing LaTeX installation. Where your program prescribes its own document, a build script in your folder takes over instead. A plain markdown hand-in is fine too. |
| `proposal-customize` | Adapts everything to your supervisor's requirements ("detailed work plan required", "max 3 pages", a methodology the defaults do not carry). |
| `proposal-supervise` | For supervisors: turns a raw student submission into curated, paste-ready draft feedback. Drafts only, never sends. |
| `proposal-troubleshoot` | Diagnoses a skill that misbehaved, and assembles a bug report if it really is a defect. Most problems turn out not to be. |

Your proposal itself lives in **one self-contained file**: readable text on top, literature entries at the bottom. A companion `<slug>.notes.md` beside it keeps the working knowledge the hand-in cannot carry, such as decisions, open points and rejected literature. Many proposals can sit side by side in one folder.

**The bar matches your degree.** The skills read Bachelor's or Master's from your proposal's subtitle and never guess it; if you leave it open, `proposal-write` asks once. Structure and check are the same at both levels, only the expectations move: a Bachelor's proposal is not asked for a novelty claim, though one is welcome; a Master's proposal is asked what will be new and for whom; research questions, literature base and scope are judged at that level too.

## Quick start

1. Get an AI agent (see [docs/getting-started.md](docs/getting-started.md) if you don't have one).
2. Create a folder for your proposals and open your agent in it.
3. Install the skills:
   ```sh
   npx skills add hutzelmann/thesis-proposal-skills
   ```
4. Tell your agent: *"Help me develop a thesis idea"*, or *"Import my existing proposal from proposal.pdf"*.

The typical flow is ideate, then literature search, then write, check, review, and finally publish. Every skill also works on its own, in any order, on a proposal that already exists. PDF building is optional; install `pandoc` and `typst` only when you want it (the publish skill tells you how). If your program hands you its own template, you do not need either: a `proposal-build` script in your folder takes over the build entirely.

## When something goes wrong

If a skill misbehaves — a script fails, a rule is applied that should not be, output contradicts what the skill says about itself — tell your agent: *"something went wrong with the proposal skills"*. `proposal-troubleshoot` takes it from there.

**Update first.** Re-run the install and try again before anything else:

```sh
npx skills add hutzelmann/thesis-proposal-skills
```

The installed skills carry no version number, so there is no way to tell from inside your folder whether yours are current. Updating is cheaper than finding out, and it resolves more problems than every other cause combined.

If the problem survives that, the skill works through the likely causes in order — your model not being able to do that particular task, a `guidelines.md` rule doing exactly what it says, a missing `pandoc` or `typst` — and most sessions end there, with an answer and no report. A run that cost ten times the usual while producing correct output is the same kind of cause: a host effort or workflow mode (Claude Code's ultracode, for instance) fanned one skill's task out into many agents. The skills state the shape they expect to run in; the host's own budget controls are the remedy, not a report.

**If it really is a defect**, the skill writes a `bug-report/` folder in your own directory and stops. Nothing is transmitted, and there is no "submit" button anywhere in these skills. You then choose what happens to it: paste it into an [issue](https://github.com/hutzelmann/thesis-proposal-skills/issues), email it, or show it to your supervisor.

**Your proposal text is not included by default.** The report carries the environment, which skill versions you have, and what the failing script printed — but of your proposal only counts and hashes, unless you ask for more. Your idea is unpublished; the report is built on that assumption. You will be shown exactly what the report contains before it is written, and you can delete the folder once you have sent it.

## Model support

<!-- model-support:start -->
Model support, measured by the metered eval matrix on **2026-08-10** (3 epochs per cell unless noted; details in docs/model-support.md):

| Model (pinned version) | Verdict | Notes |
|---|---|---|
| `anthropic/claude-haiku-4.5` | ❌ not recommended | fails: proposal-customize, proposal-review, proposal-write |
| `anthropic/claude-sonnet-5` | ❔ untested |  |
| `anthropic/claude-opus-5` | ❔ untested |  |
| `openai/gpt-5.6-luna` | ❔ untested | the eval harness cannot drive this model (Azure strict tool schemas reject Inspect's tools) — untested is a harness limitation, not a quality signal |
| `openai/gpt-5.6-terra` | ❔ untested |  |
| `openai/gpt-5.6-sol` | ❔ untested |  |
| `deepseek/deepseek-v4-pro` | 🟡 partial | untested on 9 task(s); tested cells solid |
| `qwen/qwen3.8-max` | ❔ untested |  |
| `moonshotai/kimi-k3` | 🟡 partial | untested on 9 task(s); tested cells solid |
<!-- model-support:end -->

## For supervisors

**These skills are built to work at any university, with any supervisor's rules.** What ships is a portable default, not a house style: every institution-specific decision — required sections, reference minimum, accepted methodologies, the document your students hand in — is something you set in their workspace, in files they copy into their own folder. Nothing below asks you to adopt this repository's conventions, and none of it requires a fork.

The skills encode conservative academic guidance: analytical research questions (not implementation goals), a single methodology, an explicit contribution to the state of the art (its bar set by the degree level), no fabricated references, and visible TODO markers for every gap. The proposal closes with a one-sentence timeline (the start month and the submission month, or "as soon as possible") and nothing more: work plans, phase tables and Gantt charts are forbidden, as are personal data and expected-results sections. The default methodology branches and their subsections are grounded in the research-methods literature; [docs/methodology-sources.md](docs/methodology-sources.md) records the citation behind every branch.

Bachelor's and Master's proposals are held to different bars, not different documents. Structure, section list and check are identical at both levels; the level — read from the subtitle, never guessed — changes only what the skills ask for. A Bachelor's proposal may close its contribution with a competent application or evaluation in a named setting, a novelty claim welcome but not required; a Master's proposal has to name what will be new and for whom; demanding a novelty claim from the one is the same error as accepting its absence from the other. Where the research questions come from, the weight established literature may carry and the scope the available months allow grade the same way. A subtitle that leaves the level open gets a level-neutral review with one line saying so. Anything stricter per level — a Master-only reference floor, a different page limit — is a rule you write into the `guidelines.md` described below, because programs weight the difference differently and the defaults stay portable. [docs/degree-level-sources.md](docs/degree-level-sources.md) records the qualification frameworks, curricula and assessment literature behind the grading.

Substance is judged, not assumed. The review skill applies five named tests (delta, falsifiability, anti-generic, method-fit, executability) and says plainly when a draft has no viable thesis core, rather than polishing hollow material into something that merely reads well. The student decides what to do about it; the tools advise and never block.

Feedback on incoming submissions has a skill of its own. `proposal-supervise` takes whatever a student sent — PDF, Word export, pasted email — normalizes it with personal data stripped, judges it against the same check and review rules your students' tools use, and drafts the feedback: a verdict, the three to five most pressing points, what to keep, and a plain-language note that an AI assistant prepared it. The feedback never commits you to anything and is never sent — you edit it and paste it as text into your own reply or your learning platform's feedback field, with nothing to attach.

Your rules replace these defaults, and you do not have to relay them student by student. Run `proposal-customize` yourself, and it produces a single `guidelines.md` holding your requirements: a page limit, a minimum number of references, a different section list, a full work plan in place of the one-sentence timeline, plus freeform notes such as a required focus or a house style. Hand that file to your students. Once it sits in their proposal folder, every skill follows it, and checks and reviews report against your requirements instead of the defaults. A student who receives your rules as prose can produce the same file with the same skill.

Your rules are a `guidelines.md`; your **document layout** is a build script. If your program prescribes a title page, a cover sheet or a house style, put a `proposal-build` file next to the proposal — any language, any toolchain — or add a `proposal-build` target to a `Makefile` or `justfile` you already have. `proposal-publish` finds it, builds nothing itself, and hands over: your script gets the proposal's path in `PROPOSAL_PATH` and produces whatever your faculty requires. There is deliberately no fallback — while your script is there, the built-in layout cannot be produced by accident, so a student never emails a document in the wrong template because a build failed quietly. [The publish skill](skills/proposal-publish/SKILL.md#workspace-build-script) has a worked example, and [tests/fixtures/w05-workspace-build/](tests/fixtures/w05-workspace-build/) is a complete working one. Neither this nor the rules file needs a fork.

Folder layout is a knob in the same file. `[paths] proposals = "proposals/"` in the `guidelines.md` TOML block keeps every proposal and its companion files — notes, reviews, feedback, built documents — in that subfolder, with the `guidelines.md` itself staying at the workspace root as the anchor. Unset, everything lives flat in the folder as before. Skills look only where the workspace points them, and the check reports a proposal left in the old place instead of anything silently guessing. [tests/fixtures/w07-paths-workspace/](tests/fixtures/w07-paths-workspace/) is a complete working example.

The methodology set itself is one of those knobs. If your accepted method is missing from the defaults, adding it is a few lines in that same `guidelines.md`, not a fork: a declared branch adds to the shipped set, a declaration with a shipped branch's id replaces it, and `enabled = false` removes one your program does not accept. [docs/methodology-catalog.md](docs/methodology-catalog.md) carries ready-to-paste declarations for common non-default methods — action research, simulation, mapping studies, repository mining, replications, and mixed methods with its scope warning — and [tests/fixtures/w04-methodology-branch/guidelines.md](tests/fixtures/w04-methodology-branch/guidelines.md) is a complete working example.

## For contributors (this repository)

This repo is **only** for developing and testing the skills. User proposals never live here.

**Defaults stay portable; institution-specific settings belong in the workspace.** These skills have to work at any university, so a change that makes one program's convention the shipped default is the wrong shape even when the underlying need is real — required sections, reference minimums, accepted methodologies and document layouts are all configurable per workspace, and that is where such a change belongs. If your program needs something the customization surface cannot express, that gap is the bug worth reporting, and it is a much better contribution than a fork. [For supervisors](#for-supervisors) describes the surface from the using side.

- Specs are the source of truth: `openspec/specs/`, managed with [OpenSpec](https://github.com/Fission-AI/OpenSpec). Every change runs propose, review, apply, archive. Agent integration files are not committed; run `openspec init --tools <your-agent>` once locally (and `openspec update` after CLI upgrades).
- `shared/` holds the single-source guidance; `scripts/sync_shared.py` materializes it, together with the cross-skill script copies, into the skills. Activate the pre-commit hook once per clone with `git config core.hooksPath .githooks`; it re-materializes and stages the copies on every commit, and CI's `--check` catches bypassed hooks.
- Tests: `uv run pytest` runs L0 without model calls; `harness/` holds the L1/L2 model evals (see `harness/README.md`).
- Fixtures in `tests/fixtures/` are synthetic: no real proposals, no personal data.

### The Agent Skills standard

The skills follow the [Agent Skills](https://agentskills.io) standard. Conformance is validated twice: `uv run poe conform` runs the standard's own reference validator (`skills-ref`, version-pinned in `scripts/conform.py`) over every skill as part of `poe test` and CI, and the repository's stricter checks in `tests/unit/test_skill_frontmatter.py` annotate each limit they mirror with its source in the specification. Each skill also ships its eval definitions in the standard's format at `evals/evals.json` — generated projections of the harness truth, never edited by hand.

Deliberate divergences, each with its reason; a divergence not on this list is a defect:

| Divergence | Reason |
| --- | --- |
| `proposal-troubleshoot` addresses the sibling check script by the standard install path (`.claude/skills/proposal-check/…`), not `${CLAUDE_SKILL_DIR}/../…` | The variable covers only the skill's own directory, and `../<sibling>/scripts/` is a cross-skill execution shape flagged by the security audits (remediated 2026-08-02) |
| `proposal-publish` keeps its build templates in `templates/`, not `assets/` | The directory predates the convention and is referenced by the build pipeline; renaming buys no behavior |
| `evals/evals.json` references input files by workspace name instead of copying them into `evals/files/` | The inputs are the repository's synthetic fixtures, maintained beside their `expected.json` oracles; copying them into every skill would fork the corpus and bloat installs |
| No per-skill lockfile or dependency manifest | User-side scripts are Python-stdlib-only by policy, so there is nothing to lock |

MIT licensed. Issues and PRs welcome; please open an issue first. If you hit a problem while writing a proposal, [When something goes wrong](#when-something-goes-wrong) is the path — it produces a report a maintainer can act on, and `uv run poe identify <bug-report/>` resolves a submitted one to the revision it ran against.
