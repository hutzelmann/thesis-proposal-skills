## Why

`proposal-publish` builds a PDF through a fixed pipeline: `publish.py` resolves an engine (typst → LaTeX → docx) and runs pandoc against templates that ship inside the skill. A workspace cannot change any of it. A program with its own required document layout — a faculty title block, a mandated cover sheet, a house citation style — therefore has no path except forking this repository, and one contributor already did exactly that.

Workspace *rules* are already configurable through `guidelines.md`. Workspace *layout* is not. This change closes that gap with the smallest mechanism that can close it, so a faculty template is a file beside the proposal rather than a fork.

## What Changes

- Publish gains a **discovery** step: before resolving an engine, it looks in the proposal's own directory for a workspace-supplied build definition — a `proposal-build.*` file, or a well-known recipe file (`Makefile`, `justfile`, …) that declares a `proposal-build` target.
- When one is found, publish **builds nothing and exits 3**, naming what it found and how to run it. Execution belongs to the agent, which knows the platform and can run any toolchain; the shipped script never executes user-authored code.
- **No fallback.** While a build definition exists, publish cannot produce the built-in document at all. Silently emitting the default-layout PDF after a workspace build failed is the worst available outcome: it succeeds loudly and is wrong quietly. `--builtin` is the single explicit escape.
- Exit 3 is a **handoff, not a failure** — it never triggers the skill's bug-report offer.
- `--handout` is unaffected: it is a markdown transform of the proposal, not a rendered document, and its branch runs before discovery.
- `proposal-troubleshoot`'s collector records that a workspace build definition exists, by name, size and hash, with **contents withheld at every disclosure level** — so a report from a workspace-built document stops reading as "works for me".
- Documentation: a `## Workspace build script` section in the publish SKILL.md with a worked example, and a paragraph in the README's "For supervisors" section, which is where someone holding a faculty template looks first.
- **No university-specific layout ships here.** What ships is the mechanism. The default build path is byte-identical to today.

## Capabilities

### New Capabilities

None. The mechanism extends an existing capability rather than introducing one.

### Modified Capabilities

- `skill-publish`: new requirement — a workspace-supplied build definition is discovered beside the proposal, publish refuses to build and hands over, with no fallback to the built-in pipeline; plus the discovery rule, the invocation contract, and the ambiguity refusal.
- `skill-troubleshoot`: the companion-artifact inventory requirement extends to a workspace build definition beside the proposal.
- `skill-packaging`: the audit-pattern requirement gains the narrowed subprocess invariant — a shipped script may invoke fixed tools by constant name, but SHALL NOT execute a path it discovered in the workspace.

## Impact

- `skills/proposal-publish/scripts/publish.py` — discovery, refusal, `--builtin`; `build()` and `pandoc_command()` untouched, so the export matrix keeps covering the default path unchanged.
- `skills/proposal-publish/SKILL.md` — new section; header blocks and mandate untouched.
- `skills/proposal-troubleshoot/scripts/collect.py` — one line in the companion-artifact inventory.
- `tests/unit/test_publish.py`, `tests/unit/test_audit_invariants.py`, `tests/unit/test_troubleshoot_collect.py` — new cases.
- `tests/fixtures/w05-workspace-build/` — new fixture with its `expected.json` oracle; `tests/fixtures/README.md` entry.
- `README.md` — "For supervisors" paragraph.
- No changes to other skills, no changes to `shared/`, no new dependencies, no template-shadowing layer, no build-configuration file, no plugin API.
