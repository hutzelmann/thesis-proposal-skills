## Context

See `proposal.md` — Why. Constraints that shape the approach:

- `publish.py` is a user-side script: stdlib only, Python ≥ 3.11, cross-platform, no general YAML parsing.
- It is the one shipped script permitted to use `subprocess`, allowlisted in `tests/unit/test_audit_invariants.py` because it starts pandoc and typst by constant name. The published skill is audited by Snyk Agent Scan before every publish.
- `tests/unit/test_audit_invariants.py::test_no_ancestor_directory_traversal` bans `.parents` in user-side scripts. Discovery therefore uses `proposal.parent` and nothing above it — the same rule `check.py` already applies to `guidelines.md`.
- `tests/unit/test_export_matrix.py` builds every fixture on every resolvable tier in pinned CI containers by calling `publish.build()` directly.
- The agent is the caller: it runs `publish.py` through a shell and already executes commands the user directs it to.

## Goals / Non-Goals

**Goals**

- Delegation is discovered mechanically, so it is asserted at L0 rather than left to model behaviour.
- The rule that matters — never silently produce the default document instead of the workspace one — is enforced by code, not by prose in a SKILL.md.
- The shipped script never executes user-authored code, so the audit posture is unchanged and no invariant is widened.
- Arbitrary toolchains work: make, just, a shebang file, PowerShell, a full LaTeX rig.

**Non-Goals**

- Publish does not learn what the workspace build produced. There is no output-reporting protocol, and none is wanted: inventing one would turn a mechanism into a plugin API.
- Publish does not police the workspace's outputs, ignore rules, or overwrite behaviour.
- No layout, template, or faculty-specific asset ships here.

## Decisions

### Discovery and execution are split: publish discovers, the agent executes

Considered and rejected: **publish executes the definition itself**. It needs an interpreter table keyed on file extension, because a Windows workspace has no executable bit — and that table is both a maintenance burden and a hard ceiling on what a workspace may use (`make`, `just`, and PowerShell all fall outside it). It also turns publish's subprocess use from "fixed tools by constant name" into "a path found in the workspace", which is a materially different thing to hand an auditor.

Considered and rejected: **the SKILL.md instructs the agent to check for the file and run it, with publish not involved**. Discovery stops being mechanical, so the no-fallback rule becomes a sentence a model may route around — workspace build fails, agent "recovers" by running the built-in pipeline, user emails a document in the wrong template. That is the exact failure the mechanism exists to prevent, and it would be untestable at L0.

Chosen: publish discovers and **refuses**; the agent executes. The dangerous outcome becomes structurally impossible — publish cannot emit the default document while a definition exists, whatever the agent decides and however the workspace build failed — while the part that genuinely needs platform judgement goes to the component that has it.

### Two discovery forms, extension-agnostic

Form A: `proposal-build` with any suffix or none, matched by glob in `proposal.parent`. Presence is the signal. Extension-agnostic by design — the dispatch table died with the previous decision, so the suffix is now only a hint to the human reader and the agent.

Form B: a recipe file from a fixed name set (`Makefile`, `makefile`, `GNUmakefile`, `justfile`, `Justfile`, `.justfile`) that declares a `proposal-build` target, detected by the line-anchored pattern `^proposal-build\b[^\n]*:`. One regex covers make (`proposal-build:`) and just (`proposal-build proposal:`) alike. This is narrow extraction, not DSL parsing — the same posture as the `lang:` extraction and the TOML-block read.

The target requirement is what stops Form B being greedy: a workspace with a Makefile for unrelated reasons must keep publishing normally, and a workspace that suddenly cannot publish because it has a Makefile would be a worse bug than the one being fixed.

Candidates are deduplicated by resolved path — on a case-insensitive filesystem `Makefile` and `makefile` otherwise match as two, and the ambiguity refusal would fire on one file.

Form A does not win over Form B. Two definitions beside one proposal is a question only the user can answer.

### `PROPOSAL_PATH`, plus `argv[1]` for build files

Make and just share no positional-argument convention, so argv alone cannot serve both forms. An environment variable serves both identically. Form A additionally gets it as `argv[1]`, because that is the first place a script author looks. The redundancy is deliberate and costs one sentence of documentation; the alternative is a reader wondering which channel is authoritative.

### Exit 3

`0` success, `2` the existing failure status, `3` handover. A distinct code is what lets the SKILL.md say "this is not a failure" without the agent having to parse prose out of stderr — and the skill's bug-report offer is triggered by a shipped script exiting non-zero, so an undistinguished code would produce bug reports for successful handovers.

### `--builtin`

The only escape from the refusal. It earns its place under the no-fallback rule because it is user-requested and explicit, never automatic: a supervisor debugging a bad document needs to be able to ask "is this my template or my content?", and this is the only way to ask.

### Discovery runs after the `--handout` branch

`--handout` already returns before engine resolution. Placing discovery after it is what implements the spec's "hand-in export is never delegated" without a special case: the handout path simply never reaches the check.

### `ensure_gitignore` is not called on the handover path

Publish writes nothing at all when it hands over. This also satisfies the "must not silently overwrite a user's file" posture structurally rather than through a new guard — there is no file to overwrite. A separate test pins that no entry in `GITIGNORE_ENTRIES` matches any candidate name, so a build definition stays committable.

## Risks / Trade-offs

- **The agent could ignore the handover and pass `--builtin`.** → SKILL.md forbids it explicitly; this is the residual prose-enforced surface, and it is much smaller than the alternative designs' — the refusal already removed the tempting failure path.
- **Two steps instead of one** (publish reports, agent runs). → Accepted. The refusal message names the definition and, for Form B, the target and its runner, so the next command is obvious. Advisory text in a message, not a dispatch table in code.
- **A workspace build script that misbehaves is executed by the agent.** → It is the user's own file in a directory they opened an agent in, and the run announces what it is executing before it does. The shipped script's own audit posture is untouched, which is the part this repository is accountable for.
- **`proposal-build` could collide with a user's existing file.** → The `proposal-` prefix is the namespace; a bare `build.sh` is deliberately not recognized.
- **Delegation is invisible to the export matrix.** → By construction: no toolchain is involved. The matrix keeps covering the default path because `build()` and `pandoc_command()` are untouched, and the `w05` fixture's proposal is built through all three tiers there like any other, which incidentally proves a build definition beside a proposal does not disturb the shipped pipeline.
