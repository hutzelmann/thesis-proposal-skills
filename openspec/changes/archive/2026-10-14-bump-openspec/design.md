# Design

## Context

See proposal.md, Why. The decisions below were taken with the maintainer before this change was written (approved as described, with "1.14.1 + ratchet" for the length rule), and are recorded here as decided.

Facts the design rests on, read from the 1.14.1 package (`dist/core/validation/validator.js`, `dist/core/parsers/*.js`) and its CLI on 2026-10-14:

- The limit is a constant (`MAX_REQUIREMENT_TEXT_LENGTH = 500`). No flag, config key or `openspec/config.yaml` rule turns the warning off, and `--strict` fails every item that carries a warning.
- Main specs report the warning by index: `{"level": "WARNING", "path": "requirements[61]", "message": "Requirement text is very long (>500 characters). …"}`. The index is into the requirement list of `MarkdownParser.parseSpec`, the same list `show <spec> --type spec --json` prints with `name` and `text`. The validator measures `req.text.length`, the same `text` that `show` prints.
- Open changes report it by name, for ADDED requirements only: `{"path": "installation/spec.md", "message": "ADDED \"<name>\": Requirement text is very long …"}`. MODIFIED text is deliberately not measured. The validator measures `extractRequirementBody` of the block, and `show <change> --type change --json --deltas-only` prints each delta's `requirement.text` through the same `extractRequirementBody`. Checked with the package's own modules over every ADDED block in the open and archived changes: 324 blocks, 0 differences in length or name.
- `show <change> --type change --json --deltas-only` prints MODIFIED deltas through the same reader, and an archive writes a MODIFIED block into the spec as it stands. Archiving a synthetic change with 1.14.1 gave spec lengths equal to the delta lengths `show` had printed for one ADDED and two MODIFIED requirements (541, 709, 529).
- `.length` counts UTF-16 code units, so a character outside the Basic Multilingual Plane counts two.
- On today's tree, 213 spec requirements and 12 open-change ADDED requirements are over the limit. 1.14.1 reports nothing else. The open changes also hold 10 MODIFIED requirements over the limit. OpenSpec does not report them while their changes are open, but the gate after their archive would.
- Bulk validation discovers specs as every `spec.md` below `openspec/specs/` (dot entries skipped) and changes as every directory in `openspec/changes/` except `archive` and dot directories. When it finds nothing, it prints `{"items": [], …}` and exits 0. Otherwise it exits 1 when an item is invalid and 0 when none is.
- A failed `show` prints `{"status": [{"severity": "error", "code": "show_error", "message": …}]}` and exits 1. `show --type change` refuses a change without `proposal.md`, and without its Why and What Changes sections, which `validate` accepts. A change without delta specs (`skip_specs: true`) validates and shows no deltas.
- Any CLI run may send telemetry, and may create an anonymous id in the user's global `~/.config/openspec/config.json`. A non-CI run also asks the registry for a newer version. `OPENSPEC_TELEMETRY=0` and `OPENSPEC_NO_UPDATE_CHECK=1` turn both off.

## Goals / Non-Goals

**Goals:**

- One pin, which both a person and the weekly job can change in one line.
- A gate that bites on every new or longer overlong requirement from today on, without a rewrite of 235 requirements. That includes MODIFIED text, which an archive writes into the specs: it is judged while its change is open, so archiving an approved change never turns the gate red.
- A gate that cannot pass on a report that validated less than the tree holds.
- Lengths that are OpenSpec's own, so an entry never disagrees with the CLI by a character.
- A currency check and a weekly bump that reuse `model-currency.yml`'s reviewed safety properties instead of inventing new ones.

**Non-Goals:**

- Shortening any existing requirement. The baseline makes that incremental, and `--update-baseline` records each shortening.
- Following RENAMED deltas. A rename gives a requirement a name that has no entry. That is the hand edit of D3, and the failure message says so.
- Regenerating `.claude/skills`. That is the orchestrator's landing step, and `openspec update` rewrites user-global configuration.
- Any change to what `ci.yml` runs. It keeps calling `uv run poe specs`; only its comments and the spec step's name change.

## Decisions

### D1. The pin is a constant in `scripts/validate_specs.py`

`OPENSPEC_VERSION = "1.14.1"` sits beside the code that runs it, the way `scripts/conform.py` holds the skills-ref pin. The `specs` poe task becomes `python3 scripts/validate_specs.py`. Its comment keeps the sentence "the one place the OpenSpec CLI version is pinned" and points at the constant. `openspec_currency.py` imports the constant to read the pin, and its write mode rewrites that one line.

*Alternatives:* keeping the version in the poe task string as an argument would mean TOML editing in the write mode, and a second default inside the script for direct runs. A separate version file adds a file whose only reader is the script beside it.

### D2. The gate parses `--json`; the CLI is the only measure

The script runs `npx -y @fission-ai/openspec@<pin> validate --all --strict --json --no-interactive` from the repository root. The JSON is the verdict, and output that does not parse is exit 2. Every issue fails the gate, except two. A WARNING whose message carries "Requirement text is very long" goes to the ratchet, and an INFO issue is printed and fails nothing. Every other level fails, whatever its spelling. An item marked invalid that names no failing issue and no length warning fails too. A changed wording in a future version therefore turns the length warnings into ordinary findings, which fail. The bump pull request shows that, and the gate never silently passes.

The report must also cover the tree. Its spec ids must be the `spec.md` files below `openspec/specs/`, and its change ids the change directories, both found the way 1.14.1 finds them (Context). A report that validated nothing, missed an item or named one that is not there is exit 2, and so is an exit status that disagrees with the items' `valid` flags (0 exactly when every item is valid). A future version that discovers or reports differently therefore stops the gate on the bump pull request, rather than passing on less than the tree.

Each length warning is resolved to `(where, capability, name, length)`:

- A spec warning (`requirements[i]`) is resolved through `show <spec> --type spec --json`: `requirements[i].name` and the UTF-16 length of `requirements[i].text`.
- A change warning (`<capability>/spec.md`, `ADDED "<name>"`) is resolved through `show <change> --type change --json --deltas-only`: the ADDED delta whose `spec` is the capability and whose `requirement.name` is the name.

MODIFIED text draws no warning, but an archive writes it into the specs. So every open change that holds a delta spec gets its `show --deltas-only`, with or without warnings, and each MODIFIED delta over the limit is measured from that output as `(change, capability, name, length)`. The limit is the one the report's length warnings name, or OpenSpec's 500 when the report carries none. A change without delta specs has nothing to measure and gets no `show`.

One `show` runs per spec that carries length warnings and per open change that holds delta specs, about 20 today, six at a time. The `validate` run comes first, so the npx cache is filled before the parallel runs start. A warning that does not resolve fails the gate and names the warning: an index out of range, a name that is not there, or a resolved text that is not over 500. A `show` that answers with a status error stops the gate (exit 2) with the CLI's own message. For a change, the gate adds that `show` reads proposal.md with its Why and What Changes sections, which `validate` does not require. A parser this repository would have to keep in step with OpenSpec's is never consulted.

*Alternatives:* a Python port of the parsers would save the `show` runs, but it is a second reader that can drift. That is the failure OpenSpec's own `requirement-text.js` header records about its two readers. Reading lengths through a `node` call into the npx cache would depend on the package's internal module layout, which is no interface.

Every CLI run gets `OPENSPEC_TELEMETRY=0` and `OPENSPEC_NO_UPDATE_CHECK=1` (Context).

### D3. Baseline shape and matching

`openspec/long-requirements.json`, written sorted and indented, UTF-8, so a diff reads as a list of names:

```json
{
  "about": "…",
  "changes": { "<change>": { "<capability>": { "<requirement name>": 612 } } },
  "specs": { "<capability>": { "<requirement name>": 734 } }
}
```

An open change's requirement that has an entry of its own answers to that entry alone. Every other measured requirement answers to the largest of these entries with its capability and name: its own, at its location, and any in the specs or under a change that is no longer open. On a tie its own entry wins. When the winner is not its own, the match is reported: as moved, or, for an open change's MODIFIED requirement answering to the spec's entry, as inherited. Every entry consulted counts as used, so none of them is reported as gone.

- An archive moves an ADDED or MODIFIED requirement from `changes/<id>` into `specs/<capability>` under the same name. Its change is no longer open, so the requirement keeps its change's entry, even where the specs held a shorter entry for the text the MODIFIED delta replaced, until `--update-baseline` relocates it.
- While the change is open, its entry does not loosen the spec requirement it will replace. The spec answers to its own entry.
- A MODIFIED delta with no entry of its own answers to the spec's entry. A delta that lengthens a baselined requirement therefore fails while it is written, and one that makes a short requirement long fails as new.

Verdicts:

| Measured against its entry | Result |
|---|---|
| no entry anywhere | **fail** (new) |
| longer | **fail** (grew; both lengths named, and both ways out: shorten it, or raise the entry by hand) |
| equal | pass |
| shorter | pass, reported (shorter) |
| matched by fallback | pass or fail as above, also reported (moved, or inherits for a MODIFIED requirement answering to the spec's entry) |
| an entry nothing matched | reported (gone) |

A requirement that is renamed, or split into two, therefore needs its entry edited by hand. The diff of that edit is the review.

### D4. `--update-baseline` only tightens

It writes the measured set, but each length is at most the matched entry's. It writes no entry for a new requirement, and a grown one leaves the entry it answered to where and as it was, so its failure stays. Entries nothing matched are dropped, moved ones are written at their new location, and an inherited match gets an entry of its own under its change, at its measured length. It refuses to write, exit 1, while the CLI reports any other finding: a spec that fails to parse yields no length warnings, and tightening then would drop every entry of that spec. A report that does not cover the tree stops it before anything is judged (exit 2, D2), so an empty report can never empty the baseline. An entry whose spec or change is gone from the tree is dropped, since the report covered everything that is there. When no baseline file exists it records everything measured. That is the bootstrap used once by this change, and it is only reachable by deleting the file, which a reviewer sees. With no file and no flag, the gate exits 2 and says how to record one. No workflow passes the flag, CI included; an L0 test pins that for every file under `.github/workflows/`.

*Alternative:* an update that accepts growth would turn the ratchet into a recording step that anyone runs when the gate goes red.

### D5. `scripts/openspec_currency.py`

Standard library only, and so is `scripts/validate_specs.py`, whose constants it imports: the weekly workflow runs the check with plain `python3`, without the uv environment. An L0 test parses both scripts' imports, as `test_model_currency.py` does for its checker. It has four sources, each replaceable in tests:

- **The pin:** the D1 constant.
- **npm latest:** `GET https://registry.npmjs.org/@fission-ai/openspec/latest`, the URL OpenSpec's own version check uses. The answer's `name` must be the package and its `version` a plain `X.Y.Z`; anything else is unknown.
- **The local CLI:** `openspec --version` when `openspec` is on `PATH`, with the same two environment variables as D2.
- **The skills stamp:** each `generatedBy:` line in `.claude/skills/openspec-*/SKILL.md`, read with a narrow regex, as AGENTS.md requires (no YAML parsing).

Status: `current` (exit 0); `behind` (exit 1; the write mode rewrites the D1 line and nothing else); `ahead` (exit 0 with a warning: npm's latest moved backwards, which a human should look at). A registry failure or an unusable answer is unknown (exit 2), and nothing is written. A write that cannot find exactly one pin line exits 3 and writes nothing, like `model_currency.py`. A local CLI or a stamp that differs from the pin adds a warning naming the action (update the openspec package; regenerate with `openspec update`), and never changes the exit status. An absent CLI or absent skills add a note. Output is text by default and JSON with `--json`, and `--pr-body` writes the pull-request description.

### D6. The weekly workflow copies `model-currency.yml`

`.github/workflows/openspec-currency.yml` keeps the same trigger set (schedule, at Mondays 07:17 UTC, after the model-currency slot, plus `workflow_dispatch`) and the same three write permissions. It reads `GITHUB_TOKEN` only. It keeps the same fail-closed reading of the report (exit 2 is an error, and only a 0 or 1 that ends in a JSON report with `status` and `warnings` is a verdict) and the same branch handling: lease on the inspected commit, never overwrite a branch carrying someone else's commit unless a merged pull request already carried that tip, comment instead. It closes an obsolete pull request when main is current, and dispatches `ci.yml` on the branch. What differs: the branch is `openspec-currency/bump`, the watched file is `scripts/validate_specs.py`, the one `git add` names only that file, and there is no alerts step. `tests/unit/test_currency_workflow.py` is generalized to pin both workflows with one property list. The new property is that each workflow stages only its watched file. A separate test checks that no workflow, `ci.yml` included, passes `--update-baseline`.

### D7. Tests use recorded shapes, synthetic content

`tests/unit/data/openspec_cli/` holds `validate`, `show <spec>` and `show <change> --deltas-only` output that the real 1.14.1 CLI produced over a small synthetic `openspec/` tree: one spec with a long requirement, one with a non-BMP character, and one open change with a long ADDED requirement and two MODIFIED ones (one lengthens the long requirement, one makes a short one long). `archived/` holds the `validate` and `show <spec>` output after 1.14.1 archived that change, and `show-change-no-proposal.json` the status error of a `show` refused for a missing proposal. The root path is trimmed out. The L0 tests replace the CLI runner and the registry fetch, and write the synthetic tree's layout (empty files) for the tree check. A suite-wide autouse fixture makes the CLI runner and the registry fetch raise, as `_model_catalog_offline` does for the model catalog. No test starts `npx` or touches the network.

## Risks / Trade-offs

- [The gate now needs about 20 CLI runs instead of 1] → They run six at a time, about 5 s. Only specs with length warnings and open changes with delta specs get a `show`. The count falls as requirements are shortened.
- [A future OpenSpec changes the warning text, path shape, discovery or `show` JSON] → Every such change makes the gate fail or stop, never pass (D2). The weekly pull request is where that shows, before the pin moves.
- [The tree check repeats OpenSpec's discovery rule] → A version that discovers differently stops the gate (exit 2) on its bump pull request, and the rule is updated there with the pin.
- [A change with delta specs but no proposal stops the gate] → Exit 2, with the CLI's message and the reason. `validate` alone would accept it, but this repository's schema writes the proposal first.
- [A renamed or split long requirement fails as new] → Intended: the baseline entry is edited by hand, and the failure message says so. A RENAMED delta is not followed, so a rename shows as new when its change is archived. That is the same hand edit, made by the archiving session.
- [The fallback match lets two requirements with the same capability and name share one entry] → Only an entry in the specs or under a change that is no longer open can stand in for another, so an open change's entry never loosens the spec it modifies. The largest entry is used, and the match is reported.
- [npm `latest` could point at a release that breaks the CLI's JSON] → The bump pull request is red, and nobody merges it.

## Migration Plan

1. Land the scripts, tests and workflow. The baseline is recorded from this tree with `python3 scripts/validate_specs.py --update-baseline` (bootstrap): 235 entries, the 213 spec requirements, the 12 ADDED and the 10 MODIFIED open-change requirements over the limit. Archiving either open change afterwards leaves the gate green, with its entries reported as moved until `--update-baseline` relocates them.
2. Landing step, not part of this change: install OpenSpec 1.14.1 locally and regenerate `.claude/skills` with it. `uv run poe openspec-currency` warns until both match the pin.
3. Rollback: revert the commit. The 1.7.0 task line comes back, and the baseline file becomes inert.
