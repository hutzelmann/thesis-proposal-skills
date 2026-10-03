## Context

See `proposal.md` — Why for the two mechanisms and the debugging that surfaced them. Requirements are in the delta specs; this document covers how they land.

Three facts about the existing harness shape the approach:

- `tests/fixtures/g01-research-group/` already ships a synthetic supervisor profile — `group.html` with four research areas, `dblp.json` with five papers — served over localhost by the dev runner. No new fixture is needed for scoping, only a second and third scenario against it.
- `harness/l1_checks.py` already carries `SCOPING_LEAKS` (names and the injection canary) and `SCOPING_SIGNALS` (the research vocabulary). The vocabulary sits in the *signals* set, where its presence in chat proves the fetch happened. The containment rule needs the same vocabulary as a *leak*, and one tuple cannot serve both roles.
- `harness/routing.py:tool_calls` returns `(tool name, input dict)` across assistant messages, and `claude_runner.py` already consumes it for the helper-agent probe. Literature queries are therefore observable without new instrumentation: the query string is in the tool input. `claude_runner.py` also has a `--no-skill` baseline arm.

The existing `ideate_scoped` scenario hands the model the idea *"energy-efficient scheduling of containerized workloads on edge devices"* against a group whose first listed area is *"Energy-aware scheduling for containerized and edge workloads"*. It is a correct test of the fetch and a vacuous test of containment.

## Goals / Non-Goals

**Goals:**

- One rule, stated once, reachable from both entry points.
- Containment measured on the subscription, not the metered path.
- Every new test shown to fail before it is banked.

**Non-Goals:**

- No fix is validated by this change beyond the offline suite. Whether current models actually bleed profile vocabulary, and whether they actually write carrier sentences, is what the new scenarios exist to find out. This change ships the instrument and the rule; it does not claim a measurement.
- No metered eval task. Promoting a scenario to an Inspect L1 task with a model roster is a separate, cost-gated decision.
- No mechanical relevance detection in `check.py`.

## Decisions

### A sixth substance test, not a sixth review dimension

The alternative was a new dimension in `proposal-review`'s "What to assess" list. Rejected: dimensions are per-skill prose, and the same blindness exists in `proposal-write`'s self-audit, `proposal-ideate`'s convergence bar, and `proposal-supervise`'s tier decision. The substance tests are the one construct all four already cite **by name**, and the review verdict is required to cite failing tests by name. Adding the test to the guidance propagates to every judgment surface for the cost of one edit, and makes the failure sayable: "necessity test" is a thing a supervisor can write in a review.

Placement is deliberate: immediately after the swap test, because the two are mirrors and the pairing is the clearest way to explain either. The guidance sentence says so explicitly.

### A containment set beside `SCOPING_SIGNALS`, overlapping it

`SCOPING_SIGNALS` stays exactly as it is, and `SCOPING_VOCABULARY` is added beside it. The two deliberately overlap, because the roles are separated by **where** a term appears, not by which term it is: naming WebAssembly in chat is how a run proves it read the page, and writing WebAssembly into the seed file is the leak. What was missing was never a second list of words — it was the second reading of the same words.

Alternative considered: move the research vocabulary out of `SCOPING_SIGNALS` so each term has one role. Rejected on inspection — it would narrow the visibility check on the existing `ideate_scoped` scenario to three proper nouns, weakening a passing test to tidy up a taxonomy, and the taxonomy was wrong anyway.

Membership is distinctive-terms-only. A term that collides with ordinary proposal vocabulary (`runtime`, `edge`, `kernel`, bare `scheduling`) leaves the tuple rather than being special-cased in the matcher; multi-word terms are matched whole for the same reason, since a six-character stem of `power cap` is `power ` and would fire on "the power of the test".

### Containment is judged against student turns, not first utterance

Reusing `verdict_provenance`'s calibration rather than re-deriving it. That function deliberately does not require the student to say a term *first*, because good tutoring crispens phrasing and the assistant often voices the sharp term before the student adopts it — first-utterance scored a judge-confirmed student-led session 7/26 on the 2026-08-04 sonnet run. The same reasoning applies here and is the reason the spec's boundary is "whether a student turn voiced it, not who said it first". The no-idea hint path depends on this: a hint the skill is *required* to offer must not become a leak the moment the student picks it up.

Prefix-stemming at six characters, as `verdict_provenance` does, so morphology does not split a term.

### A new verdict function, not an extension of `verdict_ideate_scoped`

`verdict_ideate_scoped` asserts seed structure, name leaks, the canary, and chat visibility. Containment needs the transcript and the tool-call inputs, which that signature does not take. A separate `verdict_scoping_containment(transcript, files, queries)` composes with it rather than widening it, keeps each function's failure message attributable, and gets its own L0 test — which `tests/unit/test_repo_conventions.py` requires of every `verdict_*` anyway.

### Dev-runner scenarios, not Inspect tasks

`uv run poe dev <scenario> --model haiku` runs on the subscription and reports cost per run since `ea6a04c`. The metered path buys a model roster, which we do not need to answer "does this happen at all". The `--no-skill` arm gives the negative control for free.

### The ratchet exit narrows the prohibition rather than removing it

`skill-write`'s existing sentence — deleting a reference SHALL NOT be used to silence a finding — is correct and stays. What it lacked was a stated scope: it targets findings the skill judges *wrong*. An uncited-reference finding on an entry no claim needs is a finding that is *right*, and removal is its correct resolution. The delta adds "the skill believes is wrong" to the original sentence and states the two admissible resolutions explicitly, so the reader is never left inferring which case they are in.

Alternative considered: suppress `reference-uncited` in `check.py` when the entry looks incidental. Rejected — that is mechanical relevance judgment, and it would also hide the genuine case where the writer forgot to cite a source the argument rests on.

### The drift guard lands first

Adding a sixth test touches the guidance, four SKILL.md bodies, three spec files, and two verbatim pins. Landing the consistency test first means the additions fail loudly at every site that has not been updated, inside the same change. Landing it afterwards means the first run is already green and proves nothing. This is the repo's gate-before-refactor rule applied to a wording change.

## Risks / Trade-offs

- **The new scenarios may pass on the first run.** → That is a result, not a failure of the change, but it must not be reported as "the bug is fixed". Each scenario's task includes running its negative control — the `--no-skill` arm for containment, the pre-edit skill for the carrier sentence — and the task is not done until one arm has been observed failing. A scenario that cannot be made to fail gets said so plainly in the task notes rather than banked as green.
- **The containment set is fixture-specific and hand-maintained.** → Same trade-off `SCOPING_LEAKS` already accepts, and the fixture is synthetic and stable. The set lives beside the existing tuples with a comment pointing at the fixture file, so the two are edited together.
- **Necessity and delta overlap at the edges.** → A sentence that serves nothing often also fails to state a delta. The tests are diagnostic labels, not a partition; the guidance already expects a proposal to fail several at once. The scenarios pin the distinguishing case — a *sourced, specific* sentence — which delta does not catch.
- **Prefix-stem matching produces false positives on short shared roots.** → Six characters over a hand-maintained vocabulary set, on a synthetic fixture whose terms were chosen to be distinctive. If a term collides with ordinary proposal vocabulary, it leaves the containment set; the fix is the set, not the matcher.
- **Narrowing the deletion prohibition could be read as licence to delete.** → The delta states both resolutions and the choice rule between them, and the harness fails a run that removes an entry a claim does rest on via the existing uncited-with-reason path. The pinned sentence for this rule is updated in the same change so the reword is visible under review.

## Migration Plan

Nothing deployed, nothing to roll back: the skills are installed from `main` by users, and this change alters guidance prose, skill prose, and tests. The ordering constraint is internal — drift guard, then the sixth test, then the skill wording that cites it, then the harness work — and is encoded in the task order.

Workspaces that override guidance are unaffected: the necessity test is prose, not an overridable `structure.json` key, and no override key changes.
