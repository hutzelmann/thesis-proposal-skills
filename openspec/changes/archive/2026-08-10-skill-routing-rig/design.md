## Context

See proposal.md — Why. Three facts from probe runs on 2026-08-10 shape everything below.

`claude_runner.py` already installs a skill into `<ws>/.claude/skills/` and drives headless `claude -p`, so real skill discovery is reachable from this repo today. `claude -p … --output-format stream-json` emits `tool_use` events including `{"name":"Skill","input":{"skill":"proposal-check",…}}`, which is the observable the rig needs. But two attempts at a clean environment both failed: `--safe-mode` disables *all* customizations including the skills under test (the probe made zero `Skill` calls and hand-rolled a `find`), and a fresh `CLAUDE_CONFIG_DIR` reports `Not logged in · Please run /login`, because subscription credentials live in the config directory.

The measurement is therefore Claude-only and machine-local by nature. It is an instrument, not a gate.

## Goals / Non-Goals

**Goals:**

- A routing number that describes a *student's* install: our ten skills, nothing else.
- A rig whose parsing and classification are testable with no model call, so a host output-format change fails loudly and specifically.
- A report that names which skill stole which utterance.

**Non-Goals:**

- Cross-model routing figures. Other hosts (Codex, Gemini) read the same `description` but select through their own prompts; measuring OpenRouter models against a listing format no host actually emits would produce a confident number about our own invention.
- Fixing the descriptions. That is `skill-trigger-contract`; this change must record the baseline while the collision still exists.
- Any CI participation for the measurement itself.

## Decisions

**Real selector over a metered proxy.** Alternative considered: an Inspect task listing the ten `name: description` pairs and asking a model to pick, which would run cross-model and join the matrix. Rejected because the fidelity of the whole exercise rests on the listing format, which we would be inventing. A wrong-but-confident answer about `check` vs `review` is worse than no answer.

**Isolation via a dedicated `CLAUDE_CONFIG_DIR` with credentials reachable by symlink.** Alternatives: (a) run against the ambient configuration — rejected, the developer machine carries personal skills and a session hook that commands skill invocation, so results would not reproduce anywhere else; (b) `--safe-mode` — rejected, it disables our skills too; (c) drive the binary with an API key, which isolates cleanly but converts a free run into ~$1.60 of metered spend per sweep. The symlink keeps the credential in exactly one place on disk and copies no secret. The rig SHALL refuse to run rather than degrade to the ambient config, because a silently contaminated measurement is the failure mode that wastes the most time.

**First `Skill` call is the verdict, and the process dies with it.** A run that continues past selection pays for work we discard; the probe runs went four and eight turns. Preparatory non-skill calls are tolerated because a real agent legitimately peeks at a named file before choosing — bounded at three calls or one per-case timeout, whichever comes first. Both numbers are judgment, not derivation, and are named constants carrying that admission in a comment.

**Tool restriction as a second belt.** The run allows only `Skill`, `Read`, `Glob`. The first probe passed `--allowed-tools Skill` and still saw `Bash` execute, which the ambient `settings.json` allowlist explains; under the isolated config that leak should be gone. Implementation verifies this once rather than assuming it — if a disallowed tool still runs, the early kill is what actually bounds the run.

**Pure functions over subprocess.** `route_from_events(events)` and `classify(cases, routes)` take data. The subprocess plumbing stays in a thin caller. This is what makes the rig L0-testable; the two probe captures from 2026-08-10 seed the stream fixtures.

**Dataset in TOML, alongside `models.toml`.** Cases carry utterance, expected skill, kind (`canonical` | `oblique` | `collision` | `negative`), and language. Composition: ten skills × three kinds = 30, plus four negatives, plus six German = 40.

**Default `sonnet`, one epoch, three epochs on the collision subset, parallelism four.** Haiku fails loudest — it mis-routed on the first probe — but tuning metadata until the weakest reader is satisfied over-fits it. Uniform epochs would buy repetition of cases that were never in doubt.

**Separate from `models.toml`.** The matrix maps one task to one skill under test (`[tasks.skills]`); a routing case exercises all ten at once and would corrupt that mapping.

**Report at `docs/skill-routing.md`, raw JSON under gitignored `logs/routing/`.** Mirrors `poe report` → `docs/model-support.md`, so the committed artifact is the reviewable one and the run output is not.

## Risks / Trade-offs

- **Symlinking the credentials file may be refused by an operator's permission policy** → the rig prints the exact `ln -s` it needs and exits; the operator can create it once by hand. No fallback to the ambient config.
- **Claude Code changes its stream event shape** → the parser's L0 fixtures fail with a named unparseable input rather than the sweep silently reporting everything unrouted.
- **Selection is stochastic; a single epoch can mislead** → the contested third runs three epochs, and the report records epochs per case so a 1-of-1 result is never read as settled.
- **The baseline is measured with the *current* descriptions and a later run uses rewritten ones** → the report records the git revision of `skills/` alongside the model, so before/after comparisons cannot silently mix.
- **Measuring only Claude leaves other hosts unmeasured** → accepted and stated in `harness/README.md`; the alternative measures nothing real.
- **Parallelism four against one subscription may hit rate limits** → per-case failures are recorded as errors distinct from `unrouted`, so a throttled run is visibly degraded rather than quietly red.

## Migration Plan

Additive. No existing task, fixture, or skill file changes. Removing the rig would mean deleting `harness/routing*.py`, its dataset, its tests, the poe task, and `docs/skill-routing.md`.
