## Context

See proposal.md — Why. Two measurements taken before writing this design shape it.

The widened rule set reports **151 findings** across the tree. They are not one population:
about two thirds are mechanical (ambiguous `l` names, composite asserts, `zip(x, x[1:])`,
stale `noqa`), and the rest are structural — the complexity findings on `check()`,
`collect.main()` and `matrix.main()`, and 33 `ARG001` hits that are all one cause, the
Inspect scorer signature `(state, target)` repeated fifteen times in
`harness/skill_evals.py`.

A coverage baseline over `harness/`, `scripts/` and `skills/` reports **60%** — but the
number is misleading in a way that matters here. `skills/proposal-check/scripts/check.py`
does not appear in the report at all, and `scripts/sync_shared.py` reports 0%, although both
are covered by passing tests. Both are only ever invoked as subprocesses, so
`coverage` never sees the executed lines. The distortion is itself a finding: it is the same
subprocess indirection the follow-up changes remove.

## Goals / Non-Goals

**Goals:**

- Every setting in `pyproject.toml` enforces something. No decorative configuration.
- New code is gated from the moment this change lands, before the two refactors that follow.
- The backlog this change does not fix is visible in the config, named, and attributed to
  the change that clears it.
- Every rule written into `AGENTS.md` is one a linter or an L0 test can check.

**Non-Goals:**

- Fixing the structural findings. `check()`, `collect.main()` and `matrix.main()` stay as
  they are; this change only makes them visible and bounded.
- Adopting a code formatter (see Decisions).
- Adding a type checker. It belongs with the refactors, which will move signatures around;
  running it against code about to be restructured buys a diff, not information.
- Raising coverage. This change measures and floors it; it writes no new tests.

## Decisions

**Park structural findings in `per-file-ignores`, annotated — rather than raising thresholds
or blanket-ignoring.** A `max-complexity` set to whatever passes today gates nothing, and a
bare ignore loses the reason. An annotated per-file entry (`# cleared by
structure-check-findings`) keeps the gate at its real value for every other file, records
why the exception exists, and makes its removal a visible line in a later diff. Alternative
considered: fix everything now — rejected, it merges three changes into one and the
complexity findings are exactly what the follow-up changes exist to fix.

**Enable `E501` at the existing `line-length = 100` and rewrap the 63 offending lines,
rather than adopting `ruff format`.** The repository's strings are prose — check findings,
skill guidance, judge criteria — and they are hand-wrapped at sentence boundaries, which
reads better than a formatter's column-filling and produces far better diffs when a sentence
changes. Reformatting ~11k lines would also bury the real edits of the next two changes.
Alternatives: raise the limit to 110 (20 violations) or 120 (10) — rejected as picking the
number that makes the problem disappear; leave `E501` ignored — rejected, that is the status
quo where `line-length` means nothing.

**`ARG001` on `harness/skill_evals.py` is parked, not suppressed at the call sites.** All 33
hits are one design fact: Inspect requires `async def score(state, target)` whether or not a
scorer reads both. Prefixing parameters with `_` would fight the framework's own naming, and
the scorer factory in the follow-up change collapses fifteen signatures into one adapter,
which removes the finding at its source.

**`ARG` in test files is fixed by `_`-prefixing stub parameters.** These are monkeypatched
fakes that must match a real signature (`def fake_search(query, limit)`). `_limit` states
"required by the contract, unused by this stub" — the same information the linter wants,
written where a reader sees it.

**`RUF001`/`RUF002` are ignored globally.** Em dashes, `×`, and typographic quotes appear
throughout user-facing output by deliberate choice. The rule is correct in general and wrong
for this codebase; a global ignore with a comment is honest, per-line `noqa` would be noise.

**Coverage omits the metered-only modules and floors at 70%.** `harness/skill_evals.py` and
`harness/claude_runner.py` only execute under `inspect eval` or a live model run, never at
L0, so counting them measures nothing and drags the number toward a floor no one can defend.
With them omitted the current figure is ~75%; the floor is set at 70% — below today's value,
so it fails on regression rather than on noise. It is deliberately not raised to match: this
change writes no tests, and a floor tuned to the current commit turns every unrelated change
into a coverage negotiation. The follow-up changes raise it as the subprocess blindness goes
away.

**`poe test` keeps running everything; the fast lane is a separate task.** The gate must stay
complete — a `-m "not slow"` default would silently stop running the pandoc and typst builds
that catch real export breakage. `poe test-fast` (xdist, `-m "not slow"`) is the inner loop;
`poe test` is the gate, unchanged in what it covers.

## Risks / Trade-offs

- **Large mechanical diff (~110 edits) obscures review.** → The edits are separated from the
  configuration in the task list, each class is one `ruff --fix` or one rename, and the L0
  suite must stay at 567 passing throughout. Nothing in the diff may change a string that
  reaches a user: the three `check.py` copies are regenerated by `sync_shared.py`, not
  hand-edited, and the drift check proves it.
- **`filterwarnings = ["error"]` can fail the suite on a dependency's deprecation, unrelated
  to any change here.** → Accepted deliberately: that is the point of the setting. If a
  third-party warning proves unfixable it gets one narrowly-scoped `ignore` entry naming the
  dependency, never a blanket relaxation.
- **A parked ignore can outlive the change that was supposed to clear it.** → Each entry
  names its follow-up change, and the follow-up's task list carries removing it as an
  explicit task rather than as a hoped-for side effect.
- **`pythonpath` in pytest config makes the L0 imports work while the shipped scripts still
  rely on their own resolution.** → No skill script changes here; `pythonpath` only affects
  test collection. The user-side stdlib-only, no-install constraint is untouched.
