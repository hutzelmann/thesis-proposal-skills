## Context

See proposal.md — Why. Two constraints bound every option.

`check.py` is user-side (`AGENTS.md` — Hard rules): Python ≥ 3.11, standard library only, no
installs, cross-platform. `dataclasses` and `json` qualify; nothing else is needed.

It is also a sync source. The copies under `proposal-import/scripts` and
`proposal-write/scripts` are generated, and both skills run the check over the file they just
wrote before reporting. Any change to the script's output shape reaches three skills at once.

## Goals / Non-Goals

**Goals:**

- A finding is a value with an identity, not a sentence a consumer greps.
- Each rule is independently testable, so a rule's tests fail for that rule.
- The human report is byte-identical afterwards. This is the single most important
  constraint: it is what makes the change reviewable and what keeps the 25 oracles and 86
  check tests meaningful as a regression net.

**Non-Goals:**

- Changing any rule's behaviour, severity, or message. Not one finding is added, removed,
  re-levelled or reworded here. A message improvement is a later change, and the whole point
  of the identifiers is that it can then be a small one.
- Making the structured output a published interface for users. It exists for this
  repository's harness and for the two sibling skills; it is not documented in any SKILL.md
  as something a student runs.
- Restructuring `split_proposal` or the metadata extraction. The parse is not the problem.

## Decisions

**A frozen dataclass, not a dict or a tuple.** `Finding(level, rule, message)` gives the
three fields names at every use site and makes the value hashable and comparable, which the
tests want. A dict would reintroduce stringly-typed access one layer up; a tuple would leave
call sites indexing by position.

**Rule identifiers are kebab-case and derived from what the rule detects, not from where it
lives.** `duplicate-reference-id`, not `metadata-check-3`. The identifier is the part that
must survive refactoring, so it cannot encode structure. They are listed in one place in the
script so the closed set is reviewable.

**Rules are functions in an ordered registry.** Each takes the parsed proposal and the
effective configuration and returns `list[Finding]`. The registry's order is the report's
order, so keeping the current sequence is a matter of listing them in the current order
rather than of remembering to. The alternative — a decorator that registers on import —
hides the order in definition sequence, which is exactly the property under review here.

**Severity stays a property of the finding, not of the rule.** Several rules already emit
both: the title rules warn, the section rules error, and `guidelines.md` parse failure is an
error raised from inside an otherwise-warning area. A rule that could only produce one level
would force artificial splits.

**Oracles keep `errors_contain` and gain `rules`.** Dropping the text fragments would lose
the only guard on how a finding reads to a student, which is the thing the whole check exists
to communicate. Keeping both means the identifiers pin which checks fired and the fragments
pin the wording — the two failure modes are different and both are worth catching. The
`rules` lists are generated from the structured output rather than written by hand, then
reviewed as a diff.

**`--json` rather than a `--format` enum.** One extra mode is needed and one exists; an enum
with a single non-default value is a generalisation nothing has asked for.

## Risks / Trade-offs

- **A rule silently changes level or message during the move**, and the fixtures do not
  notice because a fragment still matches somewhere. → The human report must come out
  byte-identical: the 25 oracles, the 86 check tests, and a direct before/after comparison of
  the rendered report over every fixture. That comparison is the acceptance test for this
  change, and it is cheap because the report is deterministic.
- **The rendered order shifts**, which no oracle would catch since `errors_contain` is an
  unordered membership test. → The before/after report comparison is byte-exact, so an order
  change fails it.
- **Three skills consume this script**, so a defect ships to import and write as well as
  check. → The sync drift check keeps the copies identical, and `import`'s and `write`'s own
  eval scorers run the shipped copy over their output; those verdicts read the exit code and
  the error lines, both unchanged.
- **The identifier set becomes a de-facto public interface** that later changes cannot
  rename freely. → Accepted, and cheaper than the alternative: today the *message text* is
  the de-facto interface, which is far more expensive to keep stable.
