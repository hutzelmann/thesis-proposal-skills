# Measurements for tighten-proposal-family

Recorded 2026-10-14 for tasks 1.1 and 4.3. No model call; $0. The runs used the shipped scripts in-process from a scratch directory, with stdout captured in memory and nothing written into the repository.

## Host output caps (task 1.1)

Read from pinned or installed sources only.

| Host | Cap | Unit | What happens beyond it | Source |
|---|---|---|---|---|
| Claude Code 2.1.296 | 30,000 | characters | output saved to a file; the model gets a short preview and the path | installed CLI: setting `bashOutputMaxChars`, "default 30000; values clamp to 4000-128000", falling back to `BASH_MAX_OUTPUT_LENGTH` |
| Codex, catalog models | 10,000 tokens ≈ 40,000 | bytes (4 bytes per token) | middle truncation, head and tail kept | openai/codex `90f00bd` (the commit `install.py` pins): `codex-rs/models-manager/models.json`, every bundled model `truncation_policy {"mode":"tokens","limit":10000}`; `codex-rs/utils/string/src/truncate.rs`, `APPROX_BYTES_PER_TOKEN = 4` |
| Codex, models without catalog metadata | 10,000 | bytes | middle truncation | same commit, `codex-rs/models-manager/src/model_info.rs`: the fallback metadata's `TruncationPolicyConfig::bytes(10_000)` |
| OpenCode | 2,000 lines or 51,200 bytes, whichever comes first | lines, bytes | full output saved to a file; a truncated preview is returned | anomalyco/opencode `c1615b1` (the commit `install.py` pins): `packages/core/src/tool-output.ts`, `MAX_LINES = 2_000`, `MAX_BYTES = 50 * 1024` |
| GitHub Copilot CLI 1.0.96 (harness pin 1.0.91) | not found | — | — | the installed binary embeds its application code in a form a string search does not reach; its documentation was not consulted |

The smallest cap of a supported host in its default configuration is Claude Code's 30,000 characters; the only cap counted in lines is OpenCode's 2,000. Codex's 10,000-byte fallback applies only to a model that is not in Codex's bundled catalog, such as a custom provider's, and is not counted here; the maintainer confirmed the exclusion on 2026-10-14 (see "Decided by the maintainer").

## Search output (task 1.1)

All runs keyless: no OpenAlex key resolves through the shipped lookup on this machine (`OPENALEX_API_KEY` unset, `$THESIS_PROPOSAL_KEYS` unset, no `~/.config/thesis-proposal/api-keys.env`), so OpenAlex degraded in every run and no keyed run was made. The repository's `.env` was not loaded.

Two of w03's three DOIs are synthetic and resolve nowhere: `10.1109/TSUSC.2024.3371245` and `10.1007/s10586-025-04412-8` return HTTP 404 from Semantic Scholar and Crossref and nothing from OpenCitations. A w03 "two-seed" run is therefore a one-seed run of `10.1145/3620678.3624645`. The two-seed measurement pairs that DOI with the resolvable DOI in the lit-search `SKILL.md` example, `10.1145/3292500.3330919`.

### Snowball (`snowball.py <seeds> --limit-per-seed N`, both directions)

| Seeds | N | Candidates | Lines | Characters | stderr |
|---|---|---|---|---|---|
| w03 pair (one resolves) | 5 | 24 | 425 | 23,735 | semantic_scholar 404, openalex no key, crossref 404 |
| w03 pair (one resolves) | 8 | 37 | 693 | 37,956 | same |
| w03 pair (one resolves) | 10 | 42 | 774 | 44,103 | same |
| w03 pair (one resolves) | 12 | 48 | 882 | 49,656 | same |
| w03 pair (one resolves) | 20 | 69 | 1,255 | 79,386 | same |
| w03 first + third (one resolves) | 5 | 24 | 425 | 23,735 | same |
| two resolvable seeds | 5 | 43 | 771 | 41,392 | openalex no key |
| two resolvable seeds | 8 | 65 | 1,203 | 63,742 | openalex no key |
| `10.1145/3292500.3330919` alone | 5 | 19 | 346 | 17,657 | semantic_scholar 404, openalex no key |
| `10.1145/3292500.3330919` alone | 8 | 28 | 510 | 25,786 | same |
| `10.1145/3292500.3330919` alone | 10 | 34 | 609 | 30,986 | same |

Average size over the two-seed N=5 run: 963 characters and 17.9 lines per candidate (the 2026-10-13 record: about 890 and 17).

Per seed and direction at N=5, deduplicated (what task 6.1's synthetic replay matches):

| Seed | Backward | Forward |
|---|---|---|
| `10.1145/3620678.3624645` | 9 | 15 |
| `10.1145/3292500.3330919` | 10 | 10 |

Raw per source at N=5 (each call capped at N): Semantic Scholar references 0 for both seeds, citations 5 each, recommendations 5 and 0; Crossref references 5 each; OpenCitations references 5 each and citations 5 each; OpenAlex degraded (no key).

### Keyword search (`search.py "energy-aware scheduling serverless functions"`)

| Limit | Candidates | Lines | Characters | `sources:` line | Degradation |
|---|---|---|---|---|---|
| 10 | 9 | 152 | 8,566 | `sources: dblp(0), crossref(10)` | arxiv 429, semantic_scholar 429, openalex no key |
| 10 (retry) | 9 | 152 | 8,566 | `sources: dblp(0), crossref(10)` | arxiv timed out, semantic_scholar 429, openalex no key |
| 6 | 11 | 190 | 12,755 | `sources: dblp(0), crossref(6), arxiv(6)` | semantic_scholar 429, openalex no key |

No run had all five sources answering; per candidate the runs carried 950 to 1,160 characters.

## Decision (Q1, answer (a) with threshold target (i))

- **Threshold:** 25,000 characters, below Claude Code's 30,000, plus 1,800 lines, below OpenCode's 2,000. The character bound decides for CSL-YAML (25,000 characters are about 470 lines); the line bound covers output of very short lines.
- **Default:** two resolvable seeds at N=5 emit 41,392 characters, above the threshold, so not even 5 fits two seeds. Under the rule the default is 5, and the `SKILL.md` example snowballs one seed per call. One seed at N=5 stays under the threshold (17,657 and 23,735 characters); one seed at N=8 does not (25,786 and 37,956).
- **Search example:** `--limit 10` stays: both measured runs stay under the threshold (8,566 characters). They were degraded, with only Crossref answering; a run with all five sources answering at 10 each was not observed, and could reach the threshold. The count line flags that case when it happens.

## Body sizes (tasks 4.3, 5.7, 9.3 and 10.2)

Whitespace-separated words of each `SKILL.md` body, as `test_no_skill_body_outgrows_its_siblings` counts them; the table's `|` separators count as words, so the block counts 469 words by this measure and about 430 in prose (481 after group 9).

| | Before (`2f1fa0d`) | After group 4 | After groups 5–6 | After group 9 | After group 10 | Design estimate ("Risks") |
|---|---|---|---|---|---|---|
| Median | 2,697 (troubleshoot) | 3,169 (troubleshoot) | 3,160 (reverse) | 3,172 (reverse) | 3,172 (reverse) | ≈ 3,090 |
| Ceiling (2 × median) | 5,394 | 6,338 | 6,320 | 6,344 | 6,344 | ≈ 6,180 |
| Largest body (supervise) | 4,743 (88 %) | 5,215 (82 %) | 5,203 (82 %) | 5,215 (82 %) | 5,215 (82 %) | ≈ 5,140 (83 %) |
| ideate | 4,253 (79 %) | 4,725 (75 %) | 4,774 (76 %) | 4,810 (76 %) | 4,819 (76 %) | ≈ 4,680 (76 %) |
| Longest body in lines (import) | 164 | 185 | 185 | 185 | 185 | far under 500 |

Group 10 adds 9 words to ideate only: the slug shape "(lowercase, hyphenated, 2–4 title words; numeric suffix on collision)" in its seeding sentence. Every other body is unchanged.

Group 9 adds 12 words to every body (the block's seeding clause now moves the whole family), 24 more to ideate (the location pointer at both notes-file creations and its own seeding clause) and 12 more to check (the conditional relay). Per-skill word counts after group 9: customize 2,054, publish 2,328, check 2,604, lit-search 2,714, import 3,067, reverse 3,172, troubleshoot 3,191, review 3,408, write 4,111, ideate 4,810, supervise 5,215.

The design estimated about 420 words per body; the uniform addition left every share of the ceiling lower than before. The per-skill prose of groups 5 and 6 nets out small: the pointers shorten seven sites (supervise −12 in all; troubleshoot +10 with its capture sentences), ideate gains 49 words for the whole-family rename at seeding and the resumed `ideation.notes.md`, and lit-search gains 100 for the sizing paragraph, which leaves it below the median. Per-skill word counts after groups 5–6: customize 2,042, publish 2,316, check 2,568, lit-search 2,702, import 3,055, reverse 3,160, troubleshoot 3,179, review 3,396, write 4,099, ideate 4,774, supervise 5,203.

## Subscription dev runs (task 8.3)

Run 2026-10-14, one at a time, on the Claude subscription through the harness login (`login: harness`, `config: isolated`, no billing signal in any stream; `cost_usd` is the host's notional figure, $0 billed), CLI 2.1.296, each with `--isolated --keep`. The sonnet runs were also isolated, so the six runs differ only in the model. `host-status` before the first run: logged in, access token expired 7 h earlier; the first run refreshed it through the linked login. Each run once; no re-run.

| Scenario | Requested | Served | L1 | Verdict reason | Files left (besides `.devrun-events.jsonl`) | `single_context` | `handoff` | Turns, s, notional $ | Kept workspace |
|---|---|---|---|---|---|---|---|---|---|
| `litsearch_snowball` | haiku | `claude-haiku-5-5` | PASS | 7 references, ids unique; no file added | `serverless-energy-scheduling.md` (3 → 7 references) | PASS | FAIL: 0 `Where it stands:` lines | 17, 142, 0.019 | `/tmp/devrun-litsearch_snowball-j3ivoo1u` |
| `write_rename_family` | haiku | `claude-haiku-5-5` | PASS | family renamed `ci-repair-agent-configurations` → `context-architecture-ci-repair-agents`; no `companion-orphaned`; 4 files added, each a family file | `context-architecture-ci-repair-agents.md`, `.notes.md`, `-review.md`, `img/context-architecture-ci-repair-agents-pipeline.png` | PASS | FAIL: no handoff lines | 13, 35, 0.010 | `/tmp/devrun-write_rename_family-pc1gogcu` |
| `ideate_seed_rename` | haiku | `claude-haiku-5-5` | PASS | family renamed `flaky-ci-triage` → `separating-flaky-failures-from-regressions-in-continuous-integration`; seed structurally complete; 4 files added, each a family file | `<new>.md`, `<new>.notes.md`, `<new>.reading-list.md`, `img/<new>-sketch.png` | PASS | PASS (65 words) | 12, 70, 0.010 | `/tmp/devrun-ideate_seed_rename-fkzpks35` |
| `litsearch_snowball` | sonnet | `claude-sonnet-5-5` | PASS | 4 references, ids unique; no file added | `serverless-energy-scheduling.md` (3 → 4 references) | PASS | PASS (54 words) | 11, 65, 0.186 | `/tmp/devrun-litsearch_snowball-ad0xso0v` |
| `write_rename_family` | sonnet | `claude-sonnet-5-5` | PASS | family renamed `ci-repair-agent-configurations` → `context-architecture-effects`; no `companion-orphaned`; 4 files added, each a family file | `context-architecture-effects.md`, `.notes.md`, `-review.md`, `img/context-architecture-effects-pipeline.png` | PASS | FAIL: no handoff lines | 6, 17, 0.086 | `/tmp/devrun-write_rename_family-qkb0p_ub` |
| `ideate_seed_rename` | sonnet | `claude-sonnet-5-5` | PASS | family renamed `flaky-ci-triage` → `separating-flaky-failures-from-regressions-in-continuous-integration`; seed structurally complete; 4 files added, each a family file | same four names as the haiku run | PASS | PASS (80 words) | 7, 23, 0.110 | `/tmp/devrun-ideate_seed_rename-fhhp0qky` |

The three scenarios carry family-only inside their verdict, so their summaries have no separate `family` field; the advisory fields are `single_context` and `handoff`. No FAIL, so nothing needed triage as a harness or fixture bug.

Read from the kept streams:

- **Count line (D7).** Haiku's first call looped all three w03 seeds through `snowball.py --limit 10`; the resolvable seed printed `candidates: 42 (774 lines, 44103 characters on stdout) — more than some hosts show from one command; run narrower` (matching 1.1's N=10 row), and haiku then re-ran one seed and one direction per call at `--limit 6`. Sonnet ran one seed per call at the default (N=5): `candidates: 24 (425 lines, 23735 characters on stdout)`, no clause, but piped the output through `head -150` and re-ran it filtered. The two synthetic seeds printed `semantic_scholar: HTTP 404` and `crossref: HTTP 404` degradations in both runs.
- **Skill loading.** Both `write_rename_family` runs made no `Skill` call: haiku read `.claude/skills/proposal-write/SKILL.md` with `cat`, sonnet grepped the skill folder for rename and slug rules. Both still moved the whole family and updated the figure link in the proposal and the notes file. The four other runs loaded their skill.
- **Slug length.** Both `ideate_seed_rename` runs derived an eight-word slug from the full working title. Ideate's seeding sentences (:104, :106) give no length; write's step 2 says "2–4 title words", which sonnet applied in its rename (three words) and haiku stretched to five ("CI" counted as one). Not asserted by any verdict. Fixed after the maintainer's answer ("Fix now: 2–4 words"): ideate's seeding sentence now carries write's shape (task 10.2), and the repeat run below checks it.
- **Handoff.** Neither `write_rename_family` run closed with the handoff lines, and haiku's lit-search run closed with a bold `**Next:**` but no `Where it stands:` line. Advisory only.

The skill-loading and handoff observations went to `docs/backlog.md` as two entries, by the maintainer's answer ("Backlog entries"); neither widens this change.

### Repeat after the slug fix (task 10.5)

Run 2026-10-14, once, after task 10.4's gates passed, as the maintainer approved ("then the ideate dev run is repeated on haiku"). Same conditions as above: `login: harness`, `config: isolated`, `billing: null`, CLI 2.1.296, `--isolated --keep`; $0 billed. `host-status` before it: logged in, access token valid for another 6 h.

| Scenario | Requested | Served | L1 | Verdict reason | Files left (besides `.devrun-events.jsonl`) | `single_context` | `handoff` | Turns, s, notional $ | Kept workspace |
|---|---|---|---|---|---|---|---|---|---|
| `ideate_seed_rename` | haiku | `claude-haiku-5-5` | PASS | family renamed `flaky-ci-triage` → `flaky-failures-regressions`; seed structurally complete; 4 files added, each a family file or an allowed one | `flaky-failures-regressions.md`, `.notes.md`, `.reading-list.md`, `img/flaky-failures-regressions-sketch.png` | PASS | PASS (85 words) | 13, 64, 0.017 | `/tmp/devrun-ideate_seed_rename-7elqbr8m` |

The slug `flaky-failures-regressions` has three words, within 2–4; the working title is again "Separating Flaky Failures from Regressions in Continuous Integration", whose eight words both earlier runs used whole. The chat named the slug as "three words drawn from the title". The run loaded `proposal-ideate` through a `Skill` call. The log is the kept stream, `/tmp/devrun-ideate_seed_rename-7elqbr8m/.devrun-events.jsonl`. One run shows that the shape can be followed, not how often it is; it was not repeated.

## Decided by the maintainer

- **Codex's fallback cap: excluded** (2026-10-14, "Exclude it"). A Codex model without bundled metadata gets 10,000 bytes. Counting it would put the threshold below 10,000 characters, which even one seed at N=5 exceeds, and the count line would flag nearly every snowball run on the other hosts. It is recorded, not counted, and the threshold stays 25,000 characters or 1,800 lines. The exclusion departed from the literal Q1 (i) answer, so it was put as a direct question in the approval request; the answer is in the design's decision log ("approval answers").

## Notes

- **The synthetic w03 seeds.** `w03-snowball-seed` has one resolvable DOI, so the `litsearch_snowball` scenario (task 7.3) expands from one real seed.
