# Design — local-audit-gates

## Context

See proposal.md — Why. Facts that shape the design, all verified 2026-08-02:

- Snyk Agent Scan (`uvx snyk-agent-scan@latest`) is the exact engine behind the skills.sh Snyk column; a local run on the current tree reproduced per-issue detail the registry API withholds and found the one remaining blocker (W007, risk 1.00, lit-search guided key setup).
- Calibration: risk ≤ 0.3 W011 findings exist locally on skills that skills.sh reports as "No issues" (publish, write) → gate threshold 0.5.
- The scanner discovers agent configs beyond `$HOME` (it found `~/.config/opencode` through XDG paths during the validation run) and connecting to MCP servers can execute their commands — isolation must cover HOME and XDG variables and pass no real configs.
- Headless `claude -p` bills the logged-in subscription when no `ANTHROPIC_API_KEY` is set; `harness/claude_runner.py` is the in-repo precedent.

## Goals / Non-Goals

**Goals**: publish pipeline = local gates → publish → registry confirmation; W007 eliminated without losing the student-friendly guided setup; every gate runnable in one command; no new Python dependencies.

**Non-Goals**: publishing itself (still explicit-request only); scheduling/cron for the poller (user can ask later); replicating ATH exactly (no local runner exists — the LLM pre-flight is an approximation and stays advisory); Windows support for dev-side gate scripts (dev machine is Linux; user-side scripts remain cross-platform).

## Decisions

### D1: Key hand-off — placeholder file + user paste + mechanical verification
The agent writes `OPENALEX_API_KEY=` (no value) into the workspace-root `api-keys.env`, ensures `.gitignore` covers it, tells the user to paste the key after the `=`, then verifies by running one search. The scripts read the file; the agent only ever sees "the search now returns abstracts". Alternatives rejected: env-var instructions (shell knowledge — exactly what students lack); agent writes the value (the W007 finding); a separate setup script (more shipped surface, no gain). The SKILL.md also gains the rule that a key pasted into chat is not repeated or stored — the user is redirected to the file.

### D2: Scanner wrapper stages skills into a synthetic HOME + XDG
`scripts/audit_scan.py` copies `skills/proposal-*` (minus `__pycache__`) into a temp dir as `.claude/skills/`, sets `HOME`, `XDG_CONFIG_HOME`, and `XDG_DATA_HOME` to that dir, and runs `uvx snyk-agent-scan@latest scan --skills --json` with no config argument (an explicit config path suppresses skill discovery — observed behavior). Findings map back to skills via the issue `reference` index into the `servers` array. Threshold: fail at risk ≥ 0.5, print everything. Token: `SNYK_TOKEN` env, else the `Snyk API Key:` line in `confidential/credentials.txt` (read narrowly, value never printed).

### D3: Poller keeps a committed baseline
`scripts/audit_status.py` normalizes the audit API response to `{skill: {provider: {status, riskLevel}}}` and diffs against `audit-baseline.json` (committed). `--update` rewrites it. Baseline starts from the *current published* (pre-fix) verdicts, so the first post-publish run shows exactly the expected improvements — updating the baseline then records the new state. Summaries/timestamps stay out of the baseline: they change without meaning (provider re-runs), verdict/risk are the signal.

### D4: LLM pre-flight is advisory and subscription-billed
`harness/audit_llm_preflight.py` bundles each skill's SKILL.md + scripts, asks one `claude -p --model <alias>` call per skill for verdicts on the ATH categories (COMMAND_EXECUTION, PROMPT_INJECTION, EXTERNAL_DOWNLOADS, REMOTE_CODE_EXECUTION, credential handling) as JSON, prints a table. Not chained into the default gate: it is the only layer with model variance, and ATH's real ruleset is unknown — advisory beats false confidence. Lives in `harness/` beside the other model-calling tooling.

### D5: No gate-runner wrapper script
The pipeline is four commands documented in AGENTS.md and `harness/README.md`. A wrapper would add a file to maintain and hide which layer failed; the repo's convention (no make, no boilerplate) says document the sequence instead.

## Risks / Trade-offs

- [Scanner CLI output is documented as experimental] → wrapper parses defensively, treats unparseable output as gate failure with the raw text shown; version pinned only by `@latest` intentionally — drift is what the gate exists to catch.
- [Threshold 0.5 calibrated on one snapshot] → post-publish poller cross-checks; threshold is a named constant with the calibration note.
- [W007 fix changes agent-visible behavior in lit-search] → key handling is not covered by an existing eval; verification is the local scanner re-run (W007 gone) plus L0 prose-drift checks. The `litsearch_expand` eval is network-flaky and tests search, not setup — not run for this change.
- [Scanner sends skill content to Snyk's API] → content is already published publicly on skills.sh; nothing confidential is staged (fixtures and `confidential/` never enter the staging dir).
- [Free-account API misuse limits] → gate runs are 8 skills, on-demand; no scheduled scanner runs.

## Migration Plan

Single commit on main. New scripts are additive; lit-search SKILL.md prose changes ship with the next publish (which this change unblocks by removing W007). Rollback: revert the commit.

## Open Questions

- Whether the registry re-audits on publish automatically — first post-publish poller run answers it (unchanged from the previous change; still only answerable empirically).
