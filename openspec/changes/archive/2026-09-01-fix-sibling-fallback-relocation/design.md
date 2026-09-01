# Design

## Context

See proposal.md — Why. The repo already carries two safe fallback shapes: the reworded import paragraph (`skills/proposal-import/SKILL.md:122`, "so use that path — but keep running the command from the working directory…") and the omission shape in proposal-supervise/proposal-reverse, which states where the scripts live without any "use" imperative. `tests/unit/test_script_paths.py::test_fallback_prose_names_the_unexpanded_case` already parametrizes over all script-bearing skills and is the natural home for the guard. None of the five affected mandates or pinned sentences contains the hazard phrase, so no pin moves in this change.

Working-directory sensitivity per script, verified in source:

- `collect.py` (troubleshoot): `workspace = Path.cwd()`, bundle written to `workspace / BUNDLE_DIR` unless `--out` — CWD picks the output location.
- lit-search `common.py`: key resolution includes `Path.cwd() / "api-keys.env"` — CWD picks whether the user's keys are found; the failure is silent (providers skipped).
- `publish.py`: outputs, `.gitignore`, and `proposal-build` discovery all anchor to the resolved proposal path, but a relative `<proposal.md>` argument resolves against CWD, and a discovered workspace build is run by the agent from the working directory.
- `check.py` (check + write's vendored copy): takes the file path as argument, writes nothing; a relocated relative path fails loudly.

## Goals / Non-Goals

**Goals**

- No SKILL.md tells an agent to "use" the skill install directory as a place; every fallback resolves only a script path.
- Skills whose scripts read or write CWD-dependent locations name that stake in the same breath, so the sentence protects something concrete instead of stating policy.
- The hazard phrase cannot return by copy-paste: the known failure mode of this codebase is the next file being written from the last.

**Non-Goals**

- No materialization of the fallback paragraph as a `shared/blocks/` region. The three materialized blocks are byte-identical and position-located; the fallback paragraphs differ per skill (troubleshoot's sibling sentence, per-skill stake clauses) and sit at different body positions. Hand-maintained with an L0 negative guard matches the existing convention for per-skill wording.
- No new pinned sentences. The import change pinned a mandate sentence; these rewords touch only fallback paragraphs, and the negative test plus the spec scenario are the regression guard.
- No script changes, no harness changes — same reasoning as the import change: the eval sandbox's `ws/` framing already instructs "work there", so no eval can distinguish the wordings.
- proposal-import, proposal-supervise, proposal-reverse untouched: already in a safe shape.

## Decisions

- **Per-skill stake clause over one generic sentence.** The import wording earns its length by naming `<slug>.md`; a generic "never where you work or write" with nothing named would read as policy and invite trimming. Each skill names its own CWD stake (write: `<slug>.md`; troubleshoot: the report bundle; lit-search: `api-keys.env`; publish: outputs and the workspace build). Alternative — byte-identical generic paragraph everywhere — rejected: it loses the concrete referent that made the import fix stick, and would push toward materialization this design declines.
- **proposal-check gets the omission shape, not the import shape.** Check is read-only by mandate, its script writes nothing, and the misuse fails loudly (file not found). proposal-supervise wraps the same script with the omission shape already; adding a "keep running from the working directory" clause to check would give its strongest workspace statement to the skill with the weakest stake, diluting the clause where it matters. Alternative — import shape everywhere for uniformity — rejected for the same dilution reason.
- **Guard is a negative assertion in `test_script_paths.py`, not five pins.** Extend the existing parametrized fallback test to assert `"so use that location" not in text` for every SKILL.md. One assertion kills the copy-paste vector across all ten skills including future ones; five pin files would freeze wording this change deliberately keeps per-skill. The spec's new scenario carries the positive obligation.
- **Delta is MODIFIED on `skill-packaging`, not five per-skill ADDED deltas.** The obligation is a property of the fallback-prose convention, which "User-side script constraints" already owns; per-skill specs would repeat one rule five times and miss future skills. Cost: MODIFIED must carry the full requirement block — accepted, done in the delta.

### Replacement paragraphs (review surface)

- **proposal-write** (`SKILL.md:83`) — import wording verbatim: "…so use that path — but keep running the command from the working directory, where `<slug>.md` stays: the fallback changes where the script is found, never where you work or write. If you cannot find it…"
- **proposal-check** (`SKILL.md:33`) — omission shape: "…the script really lives in `scripts/` next to this SKILL.md. If you cannot find it…"
- **proposal-lit-search** (`SKILL.md:26`) — "…so use that path — but keep running the command from the working directory, where `api-keys.env` is looked up: the fallback changes where the script is found, never where you work. If you cannot find it…"
- **proposal-publish** (`SKILL.md:27`) — "…so use that path — but keep running the command from the working directory, where the proposal, its outputs, and any workspace build definition live: the fallback changes where the script is found, never where you work or write. If you cannot find it…"
- **proposal-troubleshoot** (`SKILL.md:88`) — "…so use that path — but keep running the command from the working directory, where the report bundle is written: the fallback changes where the script is found, never where you work or write. The check invocation above names the standard install path…" (sibling sentence and closing sentence unchanged).

## Risks / Trade-offs

- [Five hand-varied paragraphs drift apart over time] → the negative test blocks the known-bad phrase, and the spec scenario states the invariant any future wording must satisfy; full uniformity is deliberately not a goal.
- [The publish clause slightly overstates CWD sensitivity — outputs anchor to the proposal path, not CWD] → the clause is written around where things *live* (working directory) rather than claiming the script writes to CWD; the load-bearing part is running the discovered workspace build from the working directory, which is genuinely CWD-sensitive.
- [Omission shape on check reads as inconsistency with write, which runs the same script] → intentional and recorded above: the two skills have different stakes (write edits `<slug>.md`; check must not touch anything), and supervise already models the omission shape for a check wrapper.
