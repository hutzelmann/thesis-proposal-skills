## Context

The thesis title is currently ungoverned. `shared/structure.json` and `shared/guidelines/guidelines.md` speak about titles only in the sense of *section headings*; `check.py` reads the metadata `title:` value and warns only when it is absent. See proposal.md — Why.

Three constraints shape the approach:

- `check.py` is user-side: Python ≥ 3.11 standard library only, deterministic, no model calls. It can match patterns; it cannot decide whether `Kubernetes` denotes a tool.
- AGENTS.md fixes a formalization boundary: `structure.json` holds the mechanically checkable skeleton, semantic quality rules stay prose in `guidelines.md`. The set of tool and vendor names is unbounded, so it can never be data.
- Both files are synced into skills as GENERATED copies by `scripts/sync_shared.py`, and `check.py` is vendored into `proposal-import` and `proposal-write`. Every edit lands in `shared/` or in `proposal-check`, then gets synced.

## Goals / Non-Goals

**Goals:**

- One authority (`guidelines.md`) that all four skills cite, so the alarm reads the same wherever it fires.
- Deterministic coverage of exactly the tells a pattern can carry, with no pretence of covering the rest.
- An alarm loud enough to change a title, quiet enough that a legitimate title survives it.

**Non-Goals:**

- No list of tool, product, or vendor names anywhere in the repo.
- No hard block, no silent rewrite, no refusal to proceed on a title the student defends.
- No title behavior in `proposal-import`, `proposal-publish`, `proposal-customize`, or `proposal-lit-search`.
- No numeric title norm stated as a rule in the guidance prose; the bounds live in `structure.json` and the prose points at them, exactly as the timeline size limit already does.

## Decisions

### Split by what each layer can actually decide

`guidelines.md` carries the positive criterion, the four alarm classes, and the raise-and-justify posture. `structure.json` gains a `title` block with three kinds of matchable tell. `check.py` matches them. Everything requiring world knowledge — is this proper noun a tool, is this field-naming or scope-setting — stays with the agent, in the check skill's agent pass and in the review skill.

*Alternative considered:* a curated tool-name list in `structure.json`. Rejected: the set is unbounded and dates instantly, and a stale list would give false confidence exactly where the rule matters most. The formalization boundary requirement is extended in the spec delta to say so explicitly.

### Openers anchored at the title start; buzzwords matched anywhere

An implementation opener is a *framing*, so it only means anything at position zero — "Ein Referenzmodell für die Entwicklung von …" is a fine title and must not warn. Buzzwords are tone markers and are matched anywhere in the string. Both lists are applied regardless of the proposal's `lang`: an English buzzword in a German title is still a buzzword.

Openers (prefix, case-insensitive), English: `implementing`, `implementation of`, `development of`, `developing`, `building a`, `building an`, `design and implementation of`. German: `entwicklung von`, `entwicklung einer`, `entwicklung eines`, `implementierung von`, `implementierung einer`, `umsetzung von`, `umsetzung einer`, `konzeption und umsetzung`, `konzept für`, `realisierung`, `erstellung von`, `erstellung einer`. Deliberately excluded: `towards a` / `towards an`, which is the standard hedge of a theory title ("Towards a Formal Semantics of …") and states no building work at all — the message would be factually wrong, and the same framing without the article would stay silent anyway.

Buzzwords (substring, case-insensitive, NFC-normalised so a decomposed umlaut still matches): `revolutioniz`, `next-gen`, `cutting-edge`, `ai-powered`, `game-chang`, `seamless`, `disruptive`, `bahnbrechend`, `revolutionär`, `zukunftsweisend`, `wegweisend`. Deliberately excluded: `smart`, which is a domain term in `Smart Home` and `Smart Grid`, and `intelligent`, which is a domain term in half of computer science.

A `title:` whose value is a YAML block-scalar indicator (`>-`, `|`) continues on lines the narrow one-line extraction never reads, so no tell is applied to it at all: judging the indicator would report a one-word title that does not exist.

### Warnings, not errors

Title findings join the warning bucket that already carries the anonymity `author:` finding — same reason: a heuristic on a semantic matter, false positives acknowledged, non-zero exit not warranted. This also keeps `proposal-write`'s self-check loop from being forced to mangle a title it cannot verify; the negotiation there runs with the student, not against the exit code.

*Alternative considered:* errors, matching "the title is very important". Rejected: an error is binding on the write loop, and the one case the rule most needs to survive — a named technology that genuinely is the object of study — is precisely the case the script cannot recognise.

### Word-count bounds as data, not as prose rule

`min_words: {en: 4, de: 3}`, `max_words: 20` in `structure.json`. The minimum is per language because German compounds into one noun what English spreads over three — "Anomalieerkennung in Produktionsnetzwerken" names a contribution and its object in three words, and a language-blind bound would warn on it while its five-word English equivalent passes. The maximum needs no such split. The guidance prose says the title must stand alone on a certificate and points at the bounds without repeating the numbers, mirroring how the timeline size limit is already handled. This keeps the drift-guard invariant intact and avoids stating a numeric norm that was not asked for.

### Ideate raises, write binds

At ideation time the research questions do not exist yet, so a title settled there is a title chosen before the work is understood — and, in practice, the one the student then defends. `proposal-ideate` therefore raises the alarm and offers alternatives but keeps the label *working title*; `proposal-write` runs the binding negotiation once the RQs are on the page, explicitly including a title inherited unchanged from a seed.

## Risks / Trade-offs

- **Buzzword and opener lists fire on a legitimate title** → warnings, never errors; each message names the matched tell so the student can dismiss it in one read.
- **Agents over-apply the alarm and spend turns arguing about good titles** → the guidance and each skill state the silent case explicitly: a title that names a contribution and its object gets no turn spent on it. The L2 eval scores the tool-shaped case; the fixture corpus keeps clean-title controls that must stay silent.
- **The raise-and-justify posture degenerates into a rubber stamp** ("the student said it's fine") → the justification is specific: the technology must be the *object of study*, and each skill spells out that formulation rather than accepting mere insistence.
- **Prefix matching misses openers behind an article or an adjective** ("A Development of …") → accepted; the residue is agent-judgment territory anyway, and loosening the anchor would start warning on legitimate titles.
- **Fixture oracle churn** → every proposal fixture is checked against the new tells during implementation and its `expected.json` recalibrated where it fires; f08 and f15 are the known hits.

## Migration Plan

Not applicable — no user data or persisted format changes. Users who already installed the skills get the new behavior on the next skill update; existing proposals are unaffected except that a check run may now emit title warnings.
