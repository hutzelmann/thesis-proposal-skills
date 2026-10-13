# Design

## Context

See proposal.md, "Why", for the two defects. This section covers only the mechanics the design depends on.

**The hook today.** `.githooks/pre-commit` is a 10-line `sh` script, activated by `poe setup` (`git config core.hooksPath .githooks`). It runs `python3 scripts/sync_shared.py` and pipes the output through `while read -r _ _ _ dst; do git add "$dst"`. Four passes in `sync_shared.py` call `_materialize`: attributes, skill blocks, prompt docs and copies. The prompt-docs pass passes `announce_unchanged=False`. The other three use the default `True`, so they print a `synced` line for every destination, changed or not: 36 lines on an in-sync tree. Git does not run `pre-commit` for a clean `git merge` (that is `pre-merge-commit`), for `rebase` or for `cherry-pick`. For `commit -a` and `commit <paths>` it runs it with `GIT_INDEX_FILE` pointing at a temporary index.

**`sync_shared.py --check`.** It compares each destination's current bytes with what the sources render to, relative to `REPO = Path(__file__).resolve().parent.parent`. A copy of the script inside an exported tree therefore checks that tree, with no flag needed. On drift it prints `OUT OF SYNC (run scripts/sync_shared.py):` and the drifted paths, then exits 1. A `SKILL.md` render re-reads the hand-written file and rewrites only its materialized regions.

**`conform.py` today.** It runs `npx -y skills-ref@0.1.5 validate <abs dir>` once per `skills/proposal-*` directory and aggregates the results. It is part of `poe test` (`test = ["_pytest", "_lint", "_drift", "conform"]`), and CI's `l0` job runs `poe test` on `ubuntu-latest` with `astral-sh/setup-uv@v9.0.0`. The `l0-windows` job runs `poe test-fast` (pytest only), so conform never runs on Windows in CI. No L0 test covers `conform.py`.

**The official validator.** `github.com/agentskills/agentskills`, subdirectory `skills-ref`:

- Python ≥ 3.11, Apache-2.0, author Keith Lazuka (Anthropic), `version = "0.1.0"`.
- Dependencies `click>=8.0` and `strictyaml>=1.7.3`, locked in `skills-ref/uv.lock` to click 8.3.1 and strictyaml 1.7.3.
- The repository has no tags and is not on PyPI.
- `main` = `69ef37e9424c0a7ea9dd2293b559e43ec8176379` (commit dated 2026-08-09). The last change under `skills-ref/` is `f130f34` (2026-08-03).
- Its README says the library is "intended for demonstration purposes only".

The npm port mirrors the same rule set: the same limits (64/1024/500), the same allowed fields and the same message texts. It parses YAML with `js-yaml`, where the reference uses `strictyaml`.

### Validator comparison (2026-10-13, read-only, `main` at 2188f45)

| Run | Command | Result |
|---|---|---|
| Port, all 11 skills | `python3 scripts/conform.py` (unchanged; `npx -y skills-ref@0.1.5 validate <abs dir>`) | `Valid skill: …` × 11, `all 11 skills conform (skills-ref@0.1.5)`, exit 0 |
| Official, all 11 skills | `uvx --from "git+https://github.com/agentskills/agentskills@69ef37e9424c0a7ea9dd2293b559e43ec8176379#subdirectory=skills-ref" skills-ref validate skills/<name>`, one call per skill | `Valid skill: skills/<name>` × 11, each exit 0 |

**On `main` the two validators agree: no finding either way.**

To check that agreement is not vacuous, both were also run on seeded copies of `proposal-check` in the scratchpad (repository untouched):

| Seed | Port 0.1.5 | Official @69ef37e |
|---|---|---|
| extra field `foo: bar` | exit 1: `Unexpected fields in frontmatter: foo. Only allowed-tools, compatibility, description, license, metadata, name are allowed.` | exit 1: `Unexpected fields in frontmatter: foo. Only ['allowed-tools', 'compatibility', 'description', 'license', 'metadata', 'name'] are allowed.` |
| publish stamp shape `metadata:\n  version: 0.10` | `Valid skill`, exit 0 | `Valid skill`, exit 0 |
| flow mapping `metadata: {version: "0.10.0"}` | `Valid skill`, exit 0 | exit 1: `Invalid YAML in frontmatter: While scanning … Found ugly disallowed JSONesque flow mapping (surround with ' and ' to make text appear literally)` |

The reference is stricter about YAML: strictyaml rejects flow style, which `js-yaml` accepts. No shipped skill uses flow style, and `stamp_version.py` writes the block form, so switching changes no verdict today. It closes a gap in which the port would have passed frontmatter that the reference rejects.

Side observation: run without a dependency pin, `uvx` resolved click 8.5.0. The upstream lock says 8.3.1, so `uvx --from git+…` does not honour the package's `uv.lock` (see D5).

## Goals / Non-Goals

**Goals:**
- A commit contains exactly what its author staged. The hook never writes the index or the working tree.
- Stale copies cannot be committed through an activated hook, including through partial staging and `commit -a`.
- The conformance canary is the standard's own validator, and one pin always runs the same code with the same parser.

**Non-Goals:**
- A `pre-merge-commit` hook. A clean merge that leaves stale copies (`merge=ours`) is caught at the next commit, because that commit's snapshot contains them. The `AGENTS.md` rule to re-sync after a merge stays.
- Interpreter discovery in the hook on Windows (`python3` versus `py -3`). It is unchanged from today, see Open Questions.
- Any change to what `--check` compares, to the CI workflow file, or to user-side scripts.

## Decisions

**D1: The hook checks the staged snapshot, not the working tree.**
The hook exports the index with `git checkout-index --all --prefix="$snap/"` into a `mktemp -d` directory, removed by `trap … EXIT`. It then runs `python3 "$snap/scripts/sync_shared.py" --check`. `checkout-index` honours `GIT_INDEX_FILE`, so `commit -a` and `commit <paths>` are judged by what they will actually commit. Running the snapshot's own copy of the script means the checker always matches the staged sources, and `sync_shared.py` needs no `--root` flag. Measured cost on the 1,344-file index: 0.05 s for the export and 0.05 s for the check.

A scratch prototype of this hook gave the following results:

| Case | Setup | Result |
|---|---|---|
| A | No drift. Unstaged hand edit in `skills/proposal-write/SKILL.md`. `notes.txt` staged | exit 0. The commit holds `notes.txt` only. `SKILL.md` stays ` M` |
| B | `shared/blocks/voice.md` edited and staged, no sync | Refused. All 11 `SKILL.md` listed. HEAD unchanged. Index unchanged (`M  shared/blocks/voice.md`) |
| C | As B, then sync run in the working tree, nothing re-staged | Refused (a working-tree check would have passed) |
| D | A peer's unsynced `voice.md` edit left unstaged. An unrelated file staged | exit 0. A working-tree `--check` exits 1 here |
| E | As D, with `commit -a` | Refused (temporary index judged) |

Alternatives considered:

- (a) Run `--check` on the working tree, the literal reading of Q-H1. Rejected for two failures the prototype reproduced.
  - It passes falsely in case C: stale copies get committed on `main`, which is the release channel and is committed to directly.
  - It fails falsely in case D: another session's work blocks an unrelated commit, which teaches `--no-verify`.
- (b) Use `git stash --keep-index` around the check. Rejected: it mutates the working tree and races other sessions, which is the hazard being removed.
- (c) Export only the sync's inputs (81 files). Rejected: the input list would be a hand-kept second copy of `SYNC_MAP`, and the full export costs 50 ms.

**D2: Refusal message and failure modes.**
On drift, the hook prints `--check`'s own output (the `OUT OF SYNC` header and the paths), then:

```
pre-commit: refused: the staged generated copies above do not match the staged sources.
  Run `python3 scripts/sync_shared.py`, review what it rewrote, stage the files it lists
  (git add -p where a file also holds edits you are not committing), and commit again.
  Nothing was staged or changed.
```

All of this goes to stderr, and the hook exits 1. The hook runs under `set -e`, so a crash of the check fails closed: a missing `python3`, an `AnchorError` traceback, or a failed `checkout-index`. The message never suggests `--no-verify`.

**D3: `announce_unchanged` is removed. Recommended: False everywhere.**
`_materialize` prints `synced <src> -> <dst>` only when it writes. `sync()` closes with `generated copies already in sync` when nothing was written, or `rewrote N generated file(s)` otherwise.

Reasons:
1. The only consumer of the announcement of unchanged files was the hook's `git add` loop, which this change deletes.
2. D2's message says "stage the files it lists". With today's output that would be 36 paths, including all 11 hand-written `SKILL.md` files, which would reproduce the sweep by hand.
3. Every `SKILL.md` is a hand-written document holding materialized regions. That is exactly the case `desktop-first-install` already fixed for `README.md` and `docs/install.md`.
4. For pure copies, an unchanged copy has no diff, so the line is noise.

The `synced` line format stays for humans, but it is no longer a parsing contract.

Alternative considered: keep the parameter and flip its default. Rejected: a parameter with only one value in use is dead code.

**D4: Run the official validator through `uvx`, pinned by a full commit SHA.**
`conform.py` runs:

```
uvx --from git+https://github.com/agentskills/agentskills@<SHA>#subdirectory=skills-ref --with strictyaml==1.7.3 --with click==8.3.1 skills-ref validate <dir>
```

It runs once per skill directory, because the CLI takes one `SKILL_PATH`. The constants live at the top of the script with a comment naming the bump procedure: new SHA from `git ls-remote …/agentskills main`, dependency versions from that revision's `skills-ref/uv.lock`, then `poe conform`. `uv` is already the repository's entry point (`uv run poe …`), and `uvx` caches the built tool environment. Measured: a first build of a few seconds (about 1 MB git database plus 5 wheels), then 0.22 s per call, `--offline` included. `uvx` is a real executable on Windows. `npx` is a `.cmd` shim there, which `subprocess.run([...])` without a shell cannot start (from reading the code; this was not run on Windows here).

Alternatives considered:
- A `skills-ref @ git+…` entry in the dev dependency group, so `uv.lock` pins everything. Rejected for now: the maintainer chose `uvx`, and it keeps `click` and `strictyaml` out of the resolver that also serves `inspect-ai`. If the `--with` pins prove awkward, this is the natural fallback.
- Vendoring the validator. Rejected: it creates a second copy of upstream code, and a bump would no longer be a visible one-line diff.

**D5: Pin the validator's direct dependencies.**
`uvx --from git+…` resolves the package's requirements afresh and ignores its `uv.lock` (observed: click 8.5.0 instead of 8.3.1). `strictyaml` decides which frontmatter is accepted, and `click` decides exit codes. Both are therefore pinned with `--with …==…` to the upstream lock's versions. Transitive dependencies (`python-dateutil`, `six`, `colorama` on Windows) float, because they do not decide acceptance.

Alternative considered: `--exclude-newer <date>`. Rejected: it pins indirectly and still does not reproduce the upstream lock.

**D6: The child runs in UTF-8 mode.**
The reference reads `SKILL.md` with `Path.read_text()` and no encoding argument, so on Windows it uses the locale codec (cp1252). Today's files would still decode: no cp1252-undefined bytes, and the longest description is 516 bytes against a limit of 1024. But each em dash would count as three characters, so a description near the limit would fail falsely on Windows only. `conform.py` therefore passes `env={**os.environ, "PYTHONUTF8": "1"}`.

**D7: An offline guard for the pin (`tests/unit/test_conform.py`).**
It asserts:
- the SHA matches `^[0-9a-f]{40}$`;
- the `--from` source is exactly `git+https://github.com/agentskills/agentskills@<SHA>#subdirectory=skills-ref`;
- every `--with` requirement is an `==` pin;
- no tracked file outside `openspec/changes/archive/` contains `npx -y skills-ref` or `skills-ref@`.

It also exercises `main()` with a monkeypatched `subprocess.run` and `shutil.which`:
- all pass → exit 0;
- one failure → exit 1, and the failing skill is named;
- `uvx` missing → exit 2, with uv install guidance.

The tests start no process, so they also run on the Windows job. This test enforces the spec scenario "Validator from another source".

**D8: Hook tests drive real `git commit` (`tests/unit/test_commit_hook.py`).**
A fixture copies the sync's inputs into `tmp_path`: `shared/`, `skills/` (without `__pycache__`), `scripts/sync_shared.py`, `README.md`, `docs/install.md`, `.gitattributes` and the real `.githooks/pre-commit`. It then runs `git init`, makes the initial commit, and sets `core.hooksPath=.githooks`. Every git call gets `GIT_CONFIG_GLOBAL=os.devnull`, `GIT_CONFIG_NOSYSTEM=1` and an identity through `-c`, so the developer's signing or aliases cannot interfere. The cases are prototype cases A–E, plus "the hook never writes": the working-tree bytes of every file are identical before and after a refused commit. The module is skipped off POSIX (as `test_push_guard.py` is), because the hook's `python3` is not guaranteed on Windows runners. It is not marked `slow` (about 1 s), and it touches only `tmp_path`, so it is xdist-safe.

## Risks / Trade-offs

- [Contributors used to auto-staging get a refused commit] → The message names the one command and what to stage. `AGENTS.md`, `README.md` and `CONTRIBUTING.md` describe the new behaviour.
- [Hook not activated or bypassed] → CI's `--check` is unchanged and still the backstop. `AGENTS.md` forbids `--no-verify` as a fix.
- [Clean merge leaves stale copies] → `pre-merge-commit` is not installed (non-goal). The next commit is refused until the sync runs, and the post-merge re-sync rule stays.
- [Upstream calls `skills-ref` "for demonstration purposes only"] → It is a canary beside the repository's stricter frontmatter tests, not the primary gate, and it never runs on a user's machine.
- [GitHub unavailable, or the SHA disappears upstream after a history rewrite] → `conform` fails loudly and never skips. Re-pinning is a reviewed change. setup-uv's cache shortens CI fetches.
- [A dependency release changes behaviour] → D5 pins the deciding dependencies.
- [The check itself crashes] → It fails closed (D2).

## Migration Plan

1. Land the change as one commit on `main` with `poe test`, `poe cov` and `poe specs` green. The hook is replaced in the same commit, so the commit itself passes through the new hook.
2. Nothing to do per clone: `core.hooksPath` already points at `.githooks`.
3. Rollback: revert the commit. The old hook and pin return together.

## Open Questions

- If `agentskills` starts tagging releases or publishes `skills-ref` to PyPI, should the pin move to that immutable version? The spec admits any identifier that cannot move, so this would be a pin bump, not a design change.
- Should the hook fall back to `py -3`/`python` when `python3` is absent (Windows contributors)? Today's hook has the same dependency, so nothing regresses. This can be decided when a Windows contributor appears.
- Is a `pre-merge-commit` hook wanted, to detect stale copies at merge time rather than at the next commit? It would be a single delegating file, and can be added later without changing this design.
