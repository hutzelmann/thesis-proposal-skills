## Context

See proposal.md — Why. The constraint that shapes every decision below: skill scripts are
user-side (`AGENTS.md` — Hard rules). They run from a student's workspace with Python ≥ 3.11
and the standard library, no installs, and no assumption about the working directory. Test
convenience may not leak into them.

`enforce-python-standards` already added `pythonpath` to the pytest configuration, so the
import roots exist and the `sys.path` preambles are pure redundancy today.

## Goals / Non-Goals

**Goals:**

- One place a test looks for shared setup, so the next test file copies four lines instead
  of forty.
- Script logic measurable by coverage, which means callable in-process.
- Verdict logic all in one module, with the scorer layer holding none of it.
- Every convention in the new `AGENTS.md` section backed by a test that fails when it is
  violated.

**Non-Goals:**

- Changing what any test asserts. The suite must stay at 567 passing tests with the same
  meanings; this change moves code, it does not re-specify behavior.
- Restructuring `check()`. That is `structure-check-findings`, and its parked ignores stay.
- Adding new test coverage for its own sake. Coverage rises here because subprocess calls
  become in-process, not because tests were added — except the two verdicts that move out
  of `skill_evals.py`, which get the tests they always should have had.

## Decisions

**`main(argv=None)` parses an explicit list; `sys.argv` is read only by the `__main__`
block.** `parser.parse_args(argv)` with `argv=None` falls back to `sys.argv[1:]`, so the CLI
behaviour is unchanged and the signature is the entire diff for most scripts. The two
scripts that already do this (`collect.py`, `identify_release.py`) are the model, and they
are also the two with the cleanest tests — that correlation is the argument.

**Keep one subprocess test per script.** In-process calls cannot catch a broken shebang, a
missing `sys.exit(main())`, or an import that only fails under a fresh interpreter. The
value of the subprocess test is the interpreter boundary, so one per script is enough and
the rest convert. `test_fixture_oracles.py` keeps its subprocess call deliberately: it
exists to check the shipped script as a user runs it.

**`conftest.py` provides fixtures, not a framework.** Concretely: `repo`/`fixtures` paths, a
`run_check` callable, and a `proposal` factory that copies a fixture into `tmp_path` and
applies a substitution. Anything used by one file stays in that file. The failure mode being
avoided is a conftest that grows into a second test framework nobody can read — the rule is
that a fixture earns its place at the third caller, the same rule the code follows.

**The scorer adapter takes an async callable returning `(passed, explanation)`.** Inspect
requires `async def score(state, target)`, so the adapter owns that signature once and the
verdict functions stay synchronous and pure where they can be. Scorers that need sandbox
reads stay async, but they read and delegate — they never decide.

**Verdicts moved out of `skill_evals.py` keep their exact semantics, including the awkward
parts.** `verdict_customize_override` still parses a fenced TOML block and checks
`min_references == 8` and `timeline_detail == "detailed"`; those constants belong to the
fixture scenario, so they become parameters with the current values as defaults rather than
being generalized on the way out. Rewriting a verdict while relocating it would make an
eval-result change indistinguishable from a refactor.

**The three invariant tests assert on source text, not on imports.** The `main(argv)` guard
reads each script with `ast` and checks the signature, rather than importing it — importing
every skill script into the test process would run their module-level side effects and
couple the guard to whatever a script does at import time. `ast` also lets the guard state
exactly which file and function failed.

**Coverage floor rises to 80%.** Measured after the conversion, not chosen first, and left
below the achieved figure so the floor fails on regression rather than on noise — the same
rule the 70% floor followed.

## Risks / Trade-offs

- **A behaviour change could hide inside a "pure" refactor**, especially in the scorer
  factories, where a mis-wired adapter would silently invert a verdict. → The L0 suite must
  stay at 567 passing with unchanged names, and the moved verdicts get tests written against
  their old inline behaviour *before* the move, so a semantic drift fails immediately rather
  than at the next metered run.
- **The scorer refactor touches metered-eval code the L0 suite cannot execute.** Coverage
  omits `skill_evals.py` for exactly that reason. → The factories are exercised indirectly by
  unit-testing the verdict functions they wrap, and the module must at minimum import
  cleanly and enumerate its tasks; a smoke check of task discovery is cheap and catches the
  wiring errors that matter. A metered run is not spent to validate a refactor.
- **Deleting `sys.path.insert` makes the tests depend on pytest's `pythonpath`.** Running a
  test file with a bare `python tests/unit/test_x.py` stops working. → That was never a
  supported entry point; `poe test` and `pytest` are. The invariant test names the
  replacement so the next author is not left guessing.
- **`conftest.py` centralizes what many files depend on**, so a mistake there fails
  everything at once. → That is the point: a broken shared fixture fails loudly and in one
  place, where today the same mistake would be copied into the next twelve files quietly.
