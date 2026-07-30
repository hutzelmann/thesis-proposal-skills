# Design: Streamlined Key File Lookup

## Context

`get_key()` is the single credential entry point for every literature-search source client and for `user_agent()`. It is stdlib-only, runs on the user's machine, and is vendored into `proposal-import` via `scripts/sync_shared.py`. See proposal.md for the failure that motivated the change.

## Goals / Non-Goals

**Goals:**
- A key file placed once in the workspace is found regardless of which directory a script is launched from.
- A key can be shared across several proposal folders without copying it into each.
- A missing-key error tells the user where the code actually looked.

**Non-Goals:**
- Reading `.env` files with full shell semantics (quoting rules beyond stripping one surrounding quote pair, interpolation, `export` prefixes). The format stays deliberately trivial — it is written for students by hand or by the agent.
- Caching resolution across calls. `get_key()` is called a handful of times per run; a stale cache after the agent writes the file mid-session would cost more than the file reads save.

## Decisions

**Candidate list, resolved per key rather than per file.** The alternative — find the first existing key file, then read only that — is simpler but wrong for the common setup: a global file holding `CONTACT_EMAIL` and a workspace file holding `OPENALEX_API_KEY`. First-file-wins makes the workspace file shadow the global one, and the user loses politeness standing with Crossref/arXiv without any signal. Iterating candidates per key costs at most a few `read_text` calls on files that mostly do not exist.

**Ancestor walk stops at `$HOME`.** Walking to the filesystem root would let a file outside the user's own tree — `/api-keys.env`, or one in a shared parent on a multi-user machine — supply a credential. Bounding the walk at the home directory keeps discovery inside what the user owns. When the working directory is not under `$HOME` (a temp directory, a mounted volume) the loop simply exhausts at the root; nothing further is needed for the intended workflow.

**`$THESIS_PROPOSAL_KEYS` is a file path, not a directory.** A directory would need the filename convention appended, which reintroduces the guessing this change removes. A path names exactly one file and is testable as such.

**Order is most specific first.** Per-key environment variables win over any file — that keeps CI and shell-literate users in control. The explicit override then beats discovery, discovery beats the global default. Nothing else in the codebase depends on the previous ordering, so this is additive.

## Risks / Trade-offs

- *A key file in an unexpected ancestor is now read.* Real, but bounded by `$HOME` and by the fact that discovery only triggers when the environment does not already define the key. The alternative — the current cwd-only behavior — fails silently, which is worse.
- *`Path.home()` is evaluated at import for `GLOBAL_KEY_FILE`.* Acceptable: a process whose `$HOME` changes mid-run is not a scenario these scripts support, and tests that need to relocate the workspace use `$THESIS_PROPOSAL_KEYS` or the ancestor walk instead.

## Migration

None. An existing `api-keys.env` in the workspace root keeps resolving identically; every added path is a fallback consulted only when the previous ones yield nothing.
