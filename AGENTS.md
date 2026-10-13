# AGENTS.md

Instructions for AI agents working **on this repository** (skill development and testing). User-facing proposal guidance lives in `shared/guidelines/guidelines.md` and is a product artifact, not agent instructions.

## What this repo is

`thesis-proposal-skills`: eleven `proposal-*` agent skills (under `skills/`) that help students write thesis proposals — ten student-side, plus the supervisor-side `proposal-supervise` — and the machinery to test them. Users install the skills on their own machine, through the install prompt that runs the root `install.py`, the `.claude-plugin/` marketplace, or `npx skills add` (`docs/install.md`); their proposals never live here. Real proposals sit in a private local directory kept out of version control via `.git/info/exclude` — never commit, copy, quote, or name its contents. Developer credentials live in the gitignored `.env` (template: `.env.example`), never beside the real proposals.

## Spec-first workflow (mandatory)

`openspec/specs/` is the source of truth, managed with OpenSpec. Any behavior change runs the loop: propose (change folder with proposal, spec deltas, tasks) → human review → implement → archive. Pure refactors/tooling/docs set `skip_specs: true` in the change's `.openspec.yaml`. Validate with `openspec validate --all --strict`. Agent integration files under `.claude/` are regenerated with `openspec init --tools <agent>` and are not committed — except `.claude/settings.json`, which a `.gitignore` exception keeps tracked.

**Use the OpenSpec tooling; never hand-roll it.** Humans enter the loop through the `/opsx:*` slash commands (`/opsx:propose`, `/opsx:apply`, `/opsx:archive`). Agents invoke the matching skills instead — `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-update-change`, `openspec-sync-specs`, `openspec-explore` — which carry their own `allowed-tools: Bash(openspec:*)` grant. Inside them, drive the CLI: `openspec new change`, `openspec instructions <artifact>`, `openspec status --change <id>`, `openspec archive`. Never create, move, or delete a change folder by hand (`mkdir -p openspec/changes/…`, `mv … openspec/changes/archive/…`, `rm -rf …/specs/…`), and never hand-write an artifact the CLI would scaffold.

## Hard rules

- **Skill scripts are user-side**: Python ≥ 3.11 standard library only, no pip installs, cross-platform. No general YAML parsing (narrow extraction only; TOML via `tomllib`, JSON via `json`). The root `install.py` is user-side code under the same rules, plus one more: it must still parse on an older interpreter so it can say which version it needs. Dev-side tooling (tests, harness) may use the uv-managed environment freely.
- **Never edit generated copies.** Files marked GENERATED (skill `references/`, vendored scripts under `skills/*/scripts/`; the generated block in `.gitattributes` is the authoritative list), and the install prompt inside `README.md` and `docs/install.md`, come from `shared/` or sibling skills; edit the source, then run `python3 scripts/sync_shared.py` and stage the files it lists (it names only what it rewrote). The pre-commit hook refuses a commit whose staged copies do not match its staged sources, and never stages or rewrites anything itself. CI fails on drift.
- **Fixtures are synthetic.** Nothing derived verbatim from real proposals; personal data obviously fake (`Erika Musterfrau`, matriculation `00000000`). Every proposal fixture carries an `expected.json` oracle calibrated against `skills/proposal-check/scripts/check.py`; non-proposal web fixtures (`g` prefix) ship none.
- **Git**: `main` is the release channel — the installer, the plugin marketplace and `npx skills add` all deliver whatever is on it (plugin installs follow it without any action by the user), so what lands there is live and must be complete. Unfinished work therefore stays off `main`; where it lives instead (a branch, a worktree, a local sequence of commits) is deliberately unspecified. Commit per completed OpenSpec change. After merging work that touched `shared/`, re-run `python3 scripts/sync_shared.py` — the generated copies carry `merge=ours`, so a merge can leave them stale, and CI's drift check is the backstop. A commit the pre-commit hook refuses is fixed by running the sync and staging what it lists (`git add -p` where a file also holds edits that are not part of the commit), never by `--no-verify`. Do not push and do not publish to skills.sh — both happen only on explicit request, and the push itself is the maintainer's: `.githooks/pre-push` asks for confirmation at a terminal and refuses a shell without one, and `.claude/settings.json` denies the `git push` forms. Never route around either — no TTY wrapper such as `script`, no `--no-verify`, no other spelling of the command.
- **Credentials**: dev-side keys live in the gitignored `.env` at the repo root (`cp .env.example .env`, fill in) or in the environment; never hardcode, log, or commit them, and never store keys in the private proposals directory — it holds real proposals only. User-side scripts resolve keys via environment, then `$THESIS_PROPOSAL_KEYS`, then `api-keys.env` in the working directory, then `~/.config/thesis-proposal/api-keys.env` — never by searching ancestor directories.
- **Metered model calls**: an Anthropic model runs on the Claude subscription wherever the subscription can do the job — dev runs, routing, the audit preflight, and grading output that already exists. The dev runner strips every `ANTHROPIC_*` variable and `CLAUDE_CODE_USE_*` switch from its model runs, and its judge (`--judge`, `--rejudge`) starts from an allowlisted environment. The routing rig starts its children from an allowlisted environment that admits none of those variables. The audit preflight drops every `ANTHROPIC_*` variable and `CLAUDE_CODE_USE_*` switch before it starts `claude -p`, as the dev runner does, so an exported API key, gateway base URL or provider switch cannot bill its calls per token. Any metered call on an Anthropic model (billed per token through OpenRouter or any other API key) — `poe matrix` or another metered poe task, a bare `inspect eval`, a scratch script — goes through the matrix cost gate or an explicit user approval, and the request states the estimate with its basis and names the $0 subscription alternative, or says why there is none (a non-Anthropic row, a change that targets a shipped verdict). Re-grading recorded artifacts, an ad-hoc re-judge included, is never metered, approved or not. The matrix's pinned L2 judge is not re-grading: it runs only inside a gated `poe matrix` run, and a shipped cell whose judge call failed is re-scored by re-running that cell. Before proposing a metered run, run `uv run poe models`, since a stale pin pays to measure a model users no longer run. Why: by 2026-10-04 the OpenRouter key had billed $21.07 to traced runs, $20.61 of it on Anthropic models the subscription covers; $2.645 of that re-graded drafts the subscription had already produced, from a scratch script run with `--env-file .env` that no gate saw, after an approval of about $0.70. The gate enforces this only for the poe matrix tasks; a scratch script, an ad-hoc re-judge, an exported key or a bare `inspect eval` is invisible to every repo check, so this rule is the only guard there — which is why it names them.

## Python conventions

This code is largely AI-written, and the failure mode is always the same one: the next
file is written by copying the last, so a preamble nobody wanted appears twelve times and
one function grows to 250 lines. Every rule below is therefore paired with the linter rule
or L0 test that enforces it — a convention nothing checks is documentation, not a gate.

- **Scripts expose `main(argv: list[str] | None = None) -> int`** and parse `argv` rather
  than reading `sys.argv` implicitly, so tests call them in-process instead of spawning a
  subprocess. Subprocess-only scripts are invisible to `coverage`, which is why `check.py`
  reports no coverage at all despite being the most-asserted script in the repo.
- **Verdict functions return `(passed, explanation)` and live in `harness/l1_checks.py`.**
  Scorers in `harness/skill_evals.py` are adapters over them and hold no logic of their
  own; logic that sits in a scorer is logic no L0 test can reach.
- **Tests import through `conftest.py` and the configured `pythonpath`**, never through
  `sys.path.insert`. A test file that manipulates the import path is also telling every
  later test file to do the same.
- **Findings are dataclasses, not prefixed strings.** When two components exchange data,
  the data shape is the contract; a consumer that greps `- ERROR:` out of stdout is
  parsing a report meant for humans.
- **Extract at the third repetition**, and put the shared thing where the next writer will
  find it — a fixture in `conftest.py`, a helper beside its callers.
- **Complexity is capped** at `max-complexity = 12`. The exceptions live in
  `[tool.ruff.lint.per-file-ignores]`, and every entry names the change that removes it.
  Add to that list only with the same annotation; never raise the cap.

Enforcement: `uv run poe test` runs ruff with the full rule set and
`tests/unit/test_repo_conventions.py`, which fails on a `sys.path` line under `tests/`, on a
`main` without `argv`, and on a `verdict_*` function with no L0 test. `uv run poe cov` holds
the coverage floor. `tests/unit/test_eval_wiring.py` pins the scorer names the model-support
classifier reads, since the scorer factory made those names an argument rather than a
function name.

## Commands

Registered poe tasks (`[tool.poe.tasks]` in `pyproject.toml`) are the canonical entry points:

```sh
uv run poe setup                   # once per clone: dev env + core.hooksPath (pre-commit drift check) + merge.ours driver
uv run poe test                    # L0 chain: pytest + ruff + generated-copy drift check — must stay green
uv run poe test-fast               # inner loop: parallel, without the pandoc/typst builds (~3s)
uv run poe cov                     # coverage with the 78% floor
uv run poe specs                   # openspec validate --all --strict, CLI version pinned here for CI
uv run poe dev <scenario> --model haiku   # default for Anthropic models: real Claude Code on the subscription, $0 while the plan's extra usage stays off: billing variables are stripped from every model run (claude_runner passthrough); the alias runs the host's current haiku, not the matrix row
uv run poe smoke                   # subscription: the core scenarios on the dev runner, isolated and budget-capped, write_from_seed judged, closing summary
uv run poe smoke-inspect           # metered, cost-gated, only when the Inspect wiring changed: [roles].smoke × core tasks × 1 epoch via OpenRouter
uv run poe matrix [--estimate-only|--tier|--models|--tasks|--epochs|--yes]  # model-support matrix: metered OpenRouter, cost-gated — the source of record for shipped verdicts
uv run poe cache-probe [--estimate-only]   # metered prompt-caching check, cost-gated
uv run poe report                  # regenerate README model-support summary + docs/model-support.md from logs
uv run poe models                  # model currency vs the public OpenRouter catalog (networked, read-only)
uv run poe lit-live [--sources a,b]   # one live read-only request per lit-search source through the shipped modules (OpenAlex only with a key, else `skipped`), local only: exit 1 = the code needs to change (verification page not passed, unexpected answer, zero hits); `busy` (HTTP 429, any 5xx, network) exits 0
uv run poe audit                   # pre-publish gate: local Snyk Agent Scan (needs SNYK_TOKEN)
uv run poe audit-status            # post-publish: skills.sh verdicts vs audit-baseline.json
uv run poe install-check           # README npx command + install.py vs tracked tree (networked; own CI workflow + weekly)
uv run poe identify <bug-report/>  # resolve a submitted report's hashes.txt to the revision it ran
uv run poe host-login claude [--reset]  # the user only, interactive: the harness's own Claude login
uv run poe host-status             # harness login state; no model call, no account details (agents may run it)
uv run poe host-logout claude      # the user only: log the harness login out
uv run poe dev <scenario> --host codex --model <slug>   # subscription: the real Codex CLI on the ChatGPT plan quota, in the harness's own Codex home; never a matrix input
uv run poe host-login codex [--reset | --clear-stop] [--device-auth]   # the user only, interactive: the harness's own Codex (ChatGPT) login; --clear-stop lifts a recorded isolation stop
uv run poe host-status codex [--quota]  # Codex login, CLI version, feature allowlist, quota; no model call (agents may run it)
uv run poe host-logout codex       # the user only: log the harness's Codex login out
uv run poe dev <scenario> --host copilot --model <id> --max-ai-credits <N>   # the real Copilot CLI on the plan's included AI credits, in the harness's own Copilot home; never a matrix input
uv run poe dev canary --host copilot --model <id> --max-ai-credits 30   # the Copilot canary: the first model call after the user's go, the probe's commands as the prompt; no eval
uv run poe host-login copilot [--reset | --clear-stop]   # the user only, interactive: the harness's Copilot token file; --clear-stop lifts a recorded stop and gives the go (one canary, then one skill run)
uv run poe host-status copilot [--models | --no-token]   # Copilot token, CLI version, sandbox tools, raw quota snapshot, stop, go; no model call (agents may run it)
uv run poe host-logout copilot     # the user only: delete the harness's Copilot token file
```

The first Codex model call after any `host-login codex` needs the user's explicit go, like a metered run: it draws the plan quota the operator shares with their own ChatGPT use.

Every Copilot login records an approval stop, and only the user clears it, with `uv run poe host-login copilot --clear-stop` from a terminal outside any agent session, which is the explicit go: it covers the canary and, only once that canary passed, one skill run, the one the go request named (the runner enforces the order and records the approval stop again as that skill run starts); agents never read the Copilot token file (`<state>/hosts/copilot.token`), `/proc/<pid>/environ` of a Copilot child, or `ps e` output while one runs.

Agents never run `host-login` or `host-logout` — not through Bash, not through a terminal tool, and not through a TTY wrapper such as `script` — and relay a refusal that names either one to the user as a USER ACTION. The commands' own terminal and agent-session refusals are speed bumps; this rule is the guard.

A user's bug report is produced by `proposal-troubleshoot`, whose collector emits git blob
hashes for every installed skill file. `poe identify` compares them against the trees in this
repository and names the revision the report is about — always run it before reproducing, since
a report against an older published snapshot will not reproduce on `main`. A file it reports as
matching no revision was edited locally, which answers most "works for me" reports.

`poe test` is the gate and always runs everything; `poe test-fast` is the inner loop and is never the thing you check before claiming green.

The model-support matrix (`harness/models.toml` roster, cost gate, classification, report) is documented in `harness/README.md`. Metered matrix runs always show their estimate and wait for confirmation — never bypass the gate with `--yes` on a user's behalf without their explicit cost approval. `harness/README.md` opens with a "Which path to use" table that says which path each job takes. Every matrix run writes to `logs/evals`, and `poe report` builds the shipped verdicts from the newest log per cell there, so a check that is not meant for the record passes `--log-dir logs/scratch`.

Raw invocations behind them, plus commands without a poe task:

```sh
uv run pytest                      # L0: all tests, no model calls
uv run ruff check .                # lint
python3 scripts/sync_shared.py --check   # generated-copy drift check
openspec validate --all --strict   # spec validity
uv run inspect eval harness/skill_evals.py@<task> --model openrouter/...   # metered and ungated — prefer poe matrix --models/--tasks; see "Metered model calls"
```

Publish pipeline (publishing itself stays explicit-request only): L0 suite (includes the audit-invariant tests) → `scripts/audit_scan.py` gate → publish → `scripts/audit_status.py` confirmation, then `--update` the baseline once the new verdicts are reviewed. `harness/audit_llm_preflight.py` approximates the Gen Agent Trust Hub categories via headless `claude -p` and is advisory only.

Eval details, task list, and known limitations: `harness/README.md`. Model runs cost money (OpenRouter) or plan quota (subscription: no money while extra usage stays off, but the rolling limits are shared with the user's own Claude use) — run them deliberately, never in loops.

## Inspecting output

Reach for `jq` and the Edit/Write tools before inline Python. `jq` is allowlisted in `.claude/settings.json`, so it runs without a prompt, and an Edit prompt shows a reviewable diff. Inline `python3 -c` and `python3 - <<'PY'` heredocs prompt every time, show no diff, and can never be allowlisted, because allowing an interpreter means allowing arbitrary code execution. Reserve inline Python for genuinely novel analysis that `jq` cannot express.

- **Never rewrite a file with a Python heredoc** (`pathlib.write_text`, `open(..., 'w')`, regex substitution). Use the Edit or Write tool — that is what they are for, and the diff stays reviewable.
- **Read line ranges with the Read tool** (`offset`/`limit`), not `sed -n '10,40p'`. `sed` is deliberately not allowlisted — its `w` command can write files even under `-n` — so every `sed` call costs a prompt.
- **Never prefix a command with `timeout N`.** The Bash tool takes its own `timeout` parameter. The prefix only defeats the allowlist: `timeout 300 uv run pytest` does not match `Bash(uv run rtk pytest *)`, so it prompts.
- **No shell `for` loops for batch work.** A loop matches no allowlist entry, so it always prompts. Issue the calls separately or add a script. (`until` loops that poll background work are fine.)
- **Parse JSON with `jq -r`, not `json.load(sys.stdin)`:**

```sh
openspec status --change <id> --json | jq -r '.artifacts[] | "\(.id) \(.status) \(.requires)"'
openspec instructions design --change <id> --json | jq -r '.instruction, "---", .template'
```

- **Read eval logs with `jq`** (`inspect log dump` emits one JSON object; samples live under `.samples[]`):

```sh
uv run inspect log dump logs/evals/<run>.eval | jq -r '
.samples[0] as $s
| "SCORES: " + ($s.scores | to_entries | map("\(.key)=\(.value.value)") | join(", ")),
  "EXPL:   " + (($s.scores | to_entries[0].value.explanation // "") | .[0:180]),
  "MSGS:   " + ($s.messages | length | tostring)'
```

Message content is sometimes a string and sometimes a content-block array; normalize with `if type == "array" then map(.text // "") | join("") else . end`.

## Portability and the workspace boundary

These skills must stay usable at any university, by any supervisor. The shipped defaults are therefore the portable ones, and **anything institution-specific belongs in the user's workspace, never in the skills**: a program's required sections, its reference minimum, its accepted methodologies, its document layout. A request to make one faculty's convention the default is a request to configure a workspace — say so and point at the mechanism rather than editing `shared/`.

This is not a stylistic preference. A contributor retargeted the shipped defaults to their own lab and opened a 116-file pull request, which was the honest reading of the contributing guidance at the time; the work was real and the layer was wrong. The customization surface exists so that the answer to "our program needs X" is a file in a folder.

Two invariants carry that surface, and both are the kind a well-meaning change undoes by accident:

- **Override keys mirror their `structure.json` key path.** One rule, no aliases, no second spelling accepted beside the first, and a key resolving to no overridable leaf is reported as an error rather than ignored — a workspace whose overrides silently stopped applying is worse off than one that fails. Adding a convenience alias costs exactly the property `2026-08-11-nest-workspace-overrides` bought.
- **Publish hands over to a workspace build and never falls back.** When a `proposal-build` definition exists beside the proposal, the built-in document cannot be produced without `--builtin`. A fallback added while fixing something unrelated would silently reintroduce the failure the design prevents: a student emailing a document in the wrong template because a build failed quietly. See `2026-08-11-add-workspace-build-delegation`.

User-facing documentation of both lives in README "For supervisors", `skills/proposal-customize/SKILL.md`, and `skills/proposal-publish/SKILL.md`; the working examples are `tests/fixtures/w04-methodology-branch/` and `tests/fixtures/w05-workspace-build/`.

## The Agent Skills standard

The skills conform to the Agent Skills standard (agentskills.io; spec at `https://agentskills.io/specification`). Conformance is enforced, not aspirational: `poe conform` (part of `poe test` and CI) runs the standard's reference validator — the maintainers' Python `skills-ref` from `github.com/agentskills/agentskills`, never the unrelated npm package of that name — at the commit pinned in `scripts/conform.py`, with the dependency versions that decide what it accepts pinned beside it; bumping that pin is the reviewed step by which movement in the standard arrives here — and the constants in `tests/unit/test_skill_frontmatter.py` name the spec as their source. Each skill ships a generated `evals/evals.json` projection of its harness evals (`harness/eval_export.py`; drift-gated); edit the harness, never the projection.

**A divergence from the standard that is not on the README's deliberate-divergence list ("The Agent Skills standard" section) is a defect, not a choice.** Before "fixing" a listed divergence, read its reason. Script paths in SKILL.md bodies use `${CLAUDE_SKILL_DIR}` (host-substituted) with a prose fallback for non-substituting hosts — never bare `scripts/…`, which failed under the real host because commands run from the workspace, not the skill directory (dev-runner findings, 2026-07-31); the harness substitutes the variable to `skill` when injecting bodies. Frontmatter admits exactly `name`, `description`, `license`, `compatibility` (only on skills with genuine environment requirements), and the publish-stamped `metadata.version` — per-field rules in `test_skill_frontmatter.py`, still no general YAML parsing.

## Editing guidance content

`shared/structure.json` holds only the mechanically checkable skeleton (canonical titles en+de, methodology table, forbidden patterns); semantic rules stay prose in `shared/guidelines/guidelines.md`. Every structured title must appear verbatim in the prose (drift-guarded by an L0 test). The formalization boundary is deliberate — do not encode semantic quality rules as data.

Default methodology branches carry provenance: a citation for the taxonomy the branch derives from and for its subsection contract, recorded in `docs/methodology-sources.md`. A branch added to the defaults without one is a preference wearing a citation's clothes.

## Skill header pattern

Every `SKILL.md` is read twice: by the agent that loads it as instructions, and by anyone who lands on its page at skills.sh, which renders the frontmatter and the body and nothing else. Each body therefore opens with the same four blocks, in this order, before the first `##` heading:

1. **Purpose** — one or two sentences, impersonal, in the vocabulary of someone who has never read this repo. States the deliverable. It must never restate, soften, or paraphrase a rule stated below it: the first statement of a rule fixes that rule's scope. Where the mandate is already purpose-shaped, the purpose block adds the user-facing outcome the mandate omits rather than re-saying it.
2. **Workflow line** — byte-identical in all eleven files, with only the containing skill's own name wrapped in `**`. It is the only way a visitor who lands on one page learns the other ten exist. Materialized from `shared/blocks/workflow.md`.
3. **Voice block** — byte-identical in all eleven files: neutral constructive tone, no praise of the user or their material, no self-praise, short precise chat messages. Chat conduct only — it carries no operational rules. Materialized from `shared/blocks/voice.md`.
4. **Mandate** — the skill's agent-facing opening paragraph, verbatim, pinned in `tests/unit/data/skill_mandates/<skill>.txt`.

No file gets an exception, and nothing is inserted between a mandate and the paragraph beneath it. `tests/unit/test_skill_header_pattern.py` enforces all of it; rewording a mandate means editing its pinned copy in the same change, so the reword shows up as a diff under review.

Every skill except `proposal-troubleshoot` also carries the bug-report offer block verbatim once, in a closing `## When this run fails` section — `proposal-troubleshoot` is where the offer leads, so it does not refer itself. `tests/unit/test_report_offer.py` enforces both halves.

Every skill closes its work with a `## Handing over` section directly before that one (last in `proposal-troubleshoot`): the shared stage-handoff block — the milestone ladder, the `Where it stands:` / `Next:` / `Or:` lines, actions never skill names, recommend never act — followed by the skill's own exit condition and routes. `tests/unit/test_handoff_block.py` enforces position and identity; the routes stay per-skill prose.

**Four of those blocks are materialized, not retyped.** The workflow line, the voice block, the handoff block, and the report offer live once under `shared/blocks/` and are written into every `SKILL.md` by `scripts/sync_shared.py` — the same script that materializes the file copies, guarded by the same `--check` in `poe test`, CI and the pre-commit hook. Edit the block in `shared/blocks/`, run the sync; never edit one of those four regions in a `SKILL.md` directly, and never add a marker or banner around them (the file is a rendered page). Adding a skill therefore means editing `shared/blocks/workflow.md` once, not eleven files. The regions are located by the positions this section fixes, so a `SKILL.md` whose opening blocks are out of order fails the offline suite rather than getting a block written into the wrong place.

Per-skill wording stays hand-maintained on purpose: mandates, their pinned successors, and the load-bearing sentences in `tests/unit/data/pinned_sentences/`. A pin generated from the prose it guards would confirm any reword, including an unintended one.

Skills whose run has a per-item shape — a list of tests, dimensions, sections, references or candidates a host could hand to one helper agent each — open their body with an `## Execution shape` section as the first `##` heading: the run is one agent in one context, with the skill's own reason, and where a host may insist on a workflow, the cap and the helper contract. The section is pinned whole under `tests/unit/data/pinned_sentences/<skill>--execution-shape.txt`; `tests/unit/test_execution_shape.py` discovers covered skills from those filenames and enforces first position and pin-equals-section, so adding a pin file extends coverage. Skills that are sequential by construction — a dialogue, a ladder, a script — carry none. Origin: a real supervise run under a workflow-by-default host mode fanned out into 27 agents (2026-09-02); the sections are a mitigation, and the dev runner's probe (`harness/README.md`) is the only measurement.

## History

Migrated from a LaTeX proposal template on 2026-07-29; the tag `legacy-latex-template` preserves the old state, and the archived OpenSpec changes under `openspec/changes/archive/` document every step including eval findings.
