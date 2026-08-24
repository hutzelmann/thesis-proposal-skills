# Design — eval-definition-isolation

## Context

See proposal.md. Both leaking call sites are `shutil.copytree(skill_dir, target)`; the Inspect path whitelists subdirectories and is already clean.

## Goals / Non-Goals

**Goals:** one-line fix per runner, L0-guarded so the next skill-shipped metadata file cannot silently join a measured environment.

**Non-Goals:** stripping `evals/` from user installs (the standard puts it there); hiding anything else from measured runs (scripts/references/templates are the skill).

## Decisions

**D1 — `shutil.ignore_patterns("evals")` at both copytree sites**, with a comment naming the contamination rationale. No shared constant: two sites, two modules with no common import today; a third site earns the extraction (repo convention: extract at the third repetition).

**D2 — L0 tests exercise the real staging functions.** The dev runner's `stage()` runs against a scenario into `tmp_path`; the routing rig's skill-install loop is extracted into a small `install_skills(target)` helper so the test calls exactly the code the rig runs. Assertion: no `evals` directory anywhere under the staged skill homes, while `SKILL.md` and `scripts/` are present.

## Risks / Trade-offs

- [A future runner copies whole folders again] → the spec scenario names the invariant; the L0 tests cover the two existing runners, and the pattern ("install for measurement = install without evals/") is documented at both sites.
