---
name: proposal-lit-search
description: Find relevant academic literature for a topic or proposal — keyword search across DBLP, Crossref, arXiv, Semantic Scholar, OpenAlex, plus citation snowballing from existing references. Writes CSL-YAML entries into the proposal. Use when the user needs sources, wants the literature base broadened, or asks whether their idea is already published.
---

# Literature Search

Academic literature only. You judge relevance — the scripts only gather candidates. Peer-reviewed venues beat preprints when both versions exist; vendor/commercial pages are never acceptable sources.

## Modes

**Keyword search** (topic or full proposal as context):

```
python3 .claude/skills/proposal-lit-search/scripts/search.py "distributed consensus energy efficiency" --limit 10
```

Paths are relative to the workspace root for a standard project install; the script really lives in `scripts/` next to this SKILL.md, so use that location if the skill is installed elsewhere. If you cannot find it, say the script did not run and name what is therefore unverified — never present your own reading of the file as the script's result.

**Snowballing** (expand from the proposal's existing references — the systematic way to deepen a literature base; prefer it over keywords once seeds exist):

```
python3 .claude/skills/proposal-lit-search/scripts/snowball.py 10.1145/3292500.3330919 10.1109/EX.2024.1 --direction both
```

Both emit CSL-YAML candidates on stdout; degradation notes (failed sources, missing keys) arrive on stderr — always relay them to the user in one line.

## Your job after the scripts

1. **Judge relevance** against the actual research focus — not keyword overlap. Drop papers that merely share terms. When both a preprint and a published version appear, keep the published one.
2. **Dedupe against the proposal**: never add an entry whose DOI or title already exists in `references:`.
3. **Merge**: append accepted entries to the proposal's `references:` block; keys follow `AuthorYearFirstWord` (script-generated ids are fine, ensure uniqueness within the file). Keep abstract/authors/year/DOI; URL only when no DOI.
4. **Report**: which sources contributed, what you accepted/rejected and why, in a few sentences.

## Keys (all optional — keyless mode always works)

- Storage: the scripts look up each credential in the environment first, then in the first key file that defines it — `$THESIS_PROPOSAL_KEYS`, then **`api-keys.env` in the working directory or any parent up to `$HOME`**, then `~/.config/thesis-proposal/api-keys.env` for keys shared across workspaces. One `KEY=VALUE` per line, `#` comments allowed. For students, the workspace file is the recommended path — no shell knowledge needed, and it is found from any subdirectory.
- `OPENALEX_API_KEY` missing → OpenAlex skipped. Offer guided setup when abstracts are sparse: free key at https://openalex.org/settings/api. Then **you create or update `api-keys.env` in the workspace root for the user** (`OPENALEX_API_KEY=...`), ensure `.gitignore` covers `api-keys.env` (add the entry if the workspace is a git repo — the file holds a secret), and verify with a single search.
- Semantic Scholar runs keyless by design (shared pool; the script backs off on 429 and degrades — no key setup is offered).
- `CONTACT_EMAIL` improves politeness standing with Crossref/arXiv — suggest setting it once in `api-keys.env`; it is not a secret.
- Quota errors (HTTP 409/429) → the affected source is skipped with a note; the search continues on the rest.

## If script networking is denied

Some agent sandboxes block outbound network for scripts. Fall back to your own fetch tools against the same APIs (`api.crossref.org/works?query=…`, `dblp.org/search/publ/api?q=…&format=json`, `export.arxiv.org/api/query?search_query=…`), apply the same relevance judgment, and construct the CSL-YAML entries yourself following the rules in step 3 above (AuthorYearFirstWord keys, DOI over URL, abstract when available).
