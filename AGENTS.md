# AGENTS.md

Instructions for AI agents working **on this repository** (skill development and testing). User-facing proposal guidance lives in `shared/guidelines/guidelines.md` and is a product artifact, not agent instructions.

## What this repo is

`thesis-proposal-skills`: eight `proposal-*` agent skills (under `skills/`) that help students write thesis proposals, plus the machinery to test them. Users install the skills into their own workspace; their proposals never live here. Real proposals and credentials sit in the untracked `confidential/` directory — never commit, copy, or quote its contents.

## Spec-first workflow (mandatory)

`openspec/specs/` is the source of truth, managed with OpenSpec. Any behavior change runs the loop: propose (change folder with proposal, spec deltas, tasks) → human review → implement → archive. Pure refactors/tooling/docs set `skip_specs: true` in the change's `.openspec.yaml`. Validate with `openspec validate --all --strict`. Agent integration files under `.claude/` are regenerated with `openspec init --tools <agent>` and are not committed — except `.claude/settings.json`, which a `.gitignore` exception keeps tracked.

**Use the OpenSpec tooling; never hand-roll it.** Humans enter the loop through the `/opsx:*` slash commands (`/opsx:propose`, `/opsx:apply`, `/opsx:archive`). Agents invoke the matching skills instead — `openspec-propose`, `openspec-apply-change`, `openspec-archive-change`, `openspec-update-change`, `openspec-sync-specs`, `openspec-explore` — which carry their own `allowed-tools: Bash(openspec:*)` grant. Inside them, drive the CLI: `openspec new change`, `openspec instructions <artifact>`, `openspec status --change <id>`, `openspec archive`. Never create, move, or delete a change folder by hand (`mkdir -p openspec/changes/…`, `mv … openspec/changes/archive/…`, `rm -rf …/specs/…`), and never hand-write an artifact the CLI would scaffold.

## Hard rules

- **Skill scripts are user-side**: Python ≥ 3.11 standard library only, no pip installs, cross-platform. No general YAML parsing (narrow extraction only; TOML via `tomllib`, JSON via `json`). Dev-side tooling (tests, harness) may use the uv-managed environment freely.
- **Never edit generated copies.** Files marked GENERATED (skill `references/`, vendored scripts in `skills/proposal-import/scripts/` and `skills/proposal-write/scripts/`) come from `shared/` or sibling skills; edit the source, then run `python3 scripts/sync_shared.py`. CI fails on drift.
- **Fixtures are synthetic.** Nothing derived verbatim from real proposals; personal data obviously fake (`Erika Musterfrau`, matriculation `00000000`). Every fixture carries an `expected.json` oracle calibrated against `skills/proposal-check/scripts/check.py`.
- **Git**: work directly on `main`, no branches or worktrees; commit per completed OpenSpec change. Do not push and do not publish to skills.sh — both happen only on explicit request.
- **Credentials**: read from environment or `confidential/credentials.txt` locally; never hardcode, log, or commit them. User-side scripts resolve keys via environment, then `$THESIS_PROPOSAL_KEYS`, then `api-keys.env` in the working directory, then `~/.config/thesis-proposal/api-keys.env` — never by searching ancestor directories.

## Commands

```sh
uv run pytest                      # L0: all tests, no model calls — must stay green
uv run ruff check .                # lint — must stay clean
python3 scripts/sync_shared.py --check   # generated-copy drift check
openspec validate --all --strict   # spec validity
uv run inspect eval harness/skill_evals.py@<task> --model openrouter/...   # L1/L2, metered
uv run python harness/claude_runner.py <scenario> --model haiku            # dev loop, subscription
```

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

## History

Migrated from a LaTeX proposal template on 2026-07-29; the tag `legacy-latex-template` preserves the old state, and the archived OpenSpec changes under `openspec/changes/archive/` document every step including eval findings.
