# AGENTS.md

Instructions for AI agents working **on this repository** (skill development and testing). User-facing proposal guidance lives in `shared/guidelines/guidelines.md` and is a product artifact, not agent instructions.

## What this repo is

`thesis-proposal-skills`: nine `proposal-*` agent skills (under `skills/`) that help students write thesis proposals, plus the machinery to test them. Users install the skills into their own workspace; their proposals never live here. Real proposals sit in the untracked `confidential/` directory — never commit, copy, or quote its contents. Developer credentials live in the gitignored `.env` (template: `.env.example`), not in `confidential/`.

## Spec-first workflow (mandatory)

`openspec/specs/` is the source of truth, managed with OpenSpec. Any behavior change runs the loop: propose (change folder with proposal, spec deltas, tasks) → human review → implement → archive. Pure refactors/tooling/docs set `skip_specs: true` in the change's `.openspec.yaml`. Validate with `openspec validate --all --strict`. Agent integration files under `.claude/` are regenerated with `openspec init --tools <agent>` and are not committed — except `.claude/settings.json`, which a `.gitignore` exception keeps tracked.

**Use the OpenSpec tooling; never hand-roll it.** Humans enter the loop through the `/opsx:*` slash commands (`/opsx:propose`, `/opsx:apply`, `/opsx:archive`). Agents invoke the matching skills instead — `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-update-change`, `openspec-sync-specs`, `openspec-explore` — which carry their own `allowed-tools: Bash(openspec:*)` grant. Inside them, drive the CLI: `openspec new change`, `openspec instructions <artifact>`, `openspec status --change <id>`, `openspec archive`. Never create, move, or delete a change folder by hand (`mkdir -p openspec/changes/…`, `mv … openspec/changes/archive/…`, `rm -rf …/specs/…`), and never hand-write an artifact the CLI would scaffold.

## Hard rules

- **Skill scripts are user-side**: Python ≥ 3.11 standard library only, no pip installs, cross-platform. No general YAML parsing (narrow extraction only; TOML via `tomllib`, JSON via `json`). Dev-side tooling (tests, harness) may use the uv-managed environment freely.
- **Never edit generated copies.** Files marked GENERATED (skill `references/`, vendored scripts in `skills/proposal-import/scripts/` and `skills/proposal-write/scripts/`) come from `shared/` or sibling skills; edit the source, then run `python3 scripts/sync_shared.py`. CI fails on drift.
- **Fixtures are synthetic.** Nothing derived verbatim from real proposals; personal data obviously fake (`Erika Musterfrau`, matriculation `00000000`). Every proposal fixture carries an `expected.json` oracle calibrated against `skills/proposal-check/scripts/check.py`; non-proposal web fixtures (`g` prefix) ship none.
- **Git**: work directly on `main`, no branches or worktrees; commit per completed OpenSpec change. Do not push and do not publish to skills.sh — both happen only on explicit request.
- **Credentials**: dev-side keys live in the gitignored `.env` at the repo root (`cp .env.example .env`, fill in) or in the environment; never hardcode, log, or commit them, and never store keys in `confidential/` — that directory holds real proposals only. User-side scripts resolve keys via environment, then `$THESIS_PROPOSAL_KEYS`, then `api-keys.env` in the working directory, then `~/.config/thesis-proposal/api-keys.env` — never by searching ancestor directories.

## Commands

Registered poe tasks (`[tool.poe.tasks]` in `pyproject.toml`) are the canonical entry points:

```sh
uv run poe test                    # L0 chain: pytest + ruff + generated-copy drift check — must stay green
uv run poe dev <scenario> --model haiku   # dev loop, subscription (claude_runner passthrough)
uv run poe smoke                   # metered smoke: 1 cheap model × core tasks × 1 epoch (cost-gated)
uv run poe matrix [--estimate-only|--tier|--models|--tasks|--epochs|--yes]  # model-support matrix, cost-gated
uv run poe report                  # regenerate README model-support summary + docs/model-support.md from logs
uv run poe audit                   # pre-publish gate: local Snyk Agent Scan (needs SNYK_TOKEN)
uv run poe audit-status            # post-publish: skills.sh verdicts vs audit-baseline.json
uv run poe identify <bug-report/>  # resolve a submitted report's hashes.txt to the revision it ran
```

A user's bug report is produced by `proposal-troubleshoot`, whose collector emits git blob
hashes for every installed skill file. `poe identify` compares them against the trees in this
repository and names the revision the report is about — always run it before reproducing, since
a report against an older published snapshot will not reproduce on `main`. A file it reports as
matching no revision was edited locally, which answers most "works for me" reports.

The model-support matrix (`harness/models.toml` roster, cost gate, classification, report) is documented in `harness/README.md`. Metered matrix runs always show their estimate and wait for confirmation — never bypass the gate with `--yes` on a user's behalf without their explicit cost approval.

Raw invocations behind them, plus commands without a poe task:

```sh
uv run pytest                      # L0: all tests, no model calls
uv run ruff check .                # lint
python3 scripts/sync_shared.py --check   # generated-copy drift check
openspec validate --all --strict   # spec validity
uv run inspect eval harness/skill_evals.py@<task> --model openrouter/...   # L1/L2, metered
```

Publish pipeline (publishing itself stays explicit-request only): L0 suite (includes the audit-invariant tests) → `scripts/audit_scan.py` gate → publish → `scripts/audit_status.py` confirmation, then `--update` the baseline once the new verdicts are reviewed. `harness/audit_llm_preflight.py` approximates the Gen Agent Trust Hub categories via headless `claude -p` and is advisory only.

Eval details, task list, and known limitations: `harness/README.md`. Model runs cost money or quota — run them deliberately, never in loops.

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

## Editing guidance content

`shared/structure.json` holds only the mechanically checkable skeleton (canonical titles en+de, methodology table, forbidden patterns); semantic rules stay prose in `shared/guidelines/guidelines.md`. Every structured title must appear verbatim in the prose (drift-guarded by an L0 test). The formalization boundary is deliberate — do not encode semantic quality rules as data.

## Skill header pattern

Every `SKILL.md` is read twice: by the agent that loads it as instructions, and by anyone who lands on its page at skills.sh, which renders the frontmatter and the body and nothing else. Each body therefore opens with the same four blocks, in this order, before the first `##` heading:

1. **Purpose** — one or two sentences, impersonal, in the vocabulary of someone who has never read this repo. States the deliverable. It must never restate, soften, or paraphrase a rule stated below it: the first statement of a rule fixes that rule's scope. Where the mandate is already purpose-shaped, the purpose block adds the user-facing outcome the mandate omits rather than re-saying it.
2. **Workflow line** — byte-identical in all nine files, with only the containing skill's own name wrapped in `**`. It is the only way a visitor who lands on one page learns the other eight exist.
3. **Voice block** — byte-identical in all nine files (its bytes live as a constant in `tests/unit/test_skill_header_pattern.py`): neutral constructive tone, no praise of the user or their material, no self-praise, short precise chat messages. Chat conduct only — it carries no operational rules.
4. **Mandate** — the skill's agent-facing opening paragraph, verbatim, pinned in `tests/unit/data/skill_mandates/<skill>.txt`.

No file gets an exception, and nothing is inserted between a mandate and the paragraph beneath it. `tests/unit/test_skill_header_pattern.py` enforces all of it; rewording a mandate means editing its pinned copy in the same change, so the reword shows up as a diff under review.

Adding a tenth skill means updating the workflow line in every existing skill, since each page names the whole set. Every skill except `proposal-troubleshoot` also carries the bug-report offer block verbatim once, in a closing `## When this run fails` section — `proposal-troubleshoot` is where the offer leads, so it does not refer itself. `tests/unit/test_report_offer.py` enforces both halves.

## History

Migrated from a LaTeX proposal template on 2026-07-29; the tag `legacy-latex-template` preserves the old state, and the archived OpenSpec changes under `openspec/changes/archive/` document every step including eval findings.
