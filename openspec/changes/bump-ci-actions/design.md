## Context

See proposal.md — Why. The design question is narrow but real: what to pin to, given that
the two actions now have incompatible tagging policies.

## Goals / Non-Goals

**Goals:**

- No job in this workflow depends on the Node 20 shim.
- A reader can tell why the two pins are written in different styles without leaving the
  file.

**Non-Goals:**

- Container image bumps. `pandoc/typst` is already current, and `pandoc/extra` is held
  deliberately (see proposal.md — What Changes).
- Adding uv caching. v9's breaking change is the `prune-cache` default, which this
  workflow never reaches because it enables no cache; turning caching on now would bundle
  an unrelated decision into a runtime bump.

## Decisions

**`actions/checkout@v7`, the floating major tag.** Matches the style the file already
uses, and picks up patch fixes without an edit. The three majors crossed carry nothing
this repository uses: v5 moved to Node 24, v6 changed where credentials are persisted, v7
blocks fork checkout for `pull_request_target` and `workflow_run` — and this workflow
triggers only on `push` to `main` and `pull_request`.

**`astral-sh/setup-uv@v9.0.0`, an exact version.** Forced by upstream: v8 stopped
publishing major and minor tags, citing the tj-actions supply-chain attack, so `@v9`
resolves to nothing. The tag is an immutable release, which gives the same guarantee a
commit SHA would with a version a reader can recognise. Alternative considered: pinning
the SHA, as setup-uv's own release notes suggest. Rejected — against an immutable tag it
buys no additional guarantee and costs the reader the version number.

**A comment carries the asymmetry.** Two pins in two styles reads as an oversight unless
the file says why, and the next person to bump them needs the reason more than the versions.

## Risks / Trade-offs

- **The bump cannot be verified locally** → it is verified by the CI run on the push that
  carries it, and the change is not archived before all four jobs are green.
- **A floating `@v7` can change under us** → that is the trade this file already accepted
  for checkout, and the annotation this change removes is what a stale pin costs.
