# Proposal: implement-lit-search

## Why

Implements the skill-lit-search spec: multi-source academic search (keyword + snowballing) over stdlib-only clients, keyless-first, with CSL-YAML output. Also unblocks proposal-ideate (which vendors these scripts per the packaging spec).

## What Changes

- `skills/proposal-lit-search/scripts/`: `common.py` (HTTP, politeness, CSL normalization, dedupe, key generation), one client per source (`dblp.py`, `crossref.py`, `arxiv.py`, `opencitations.py`, `semantic_scholar.py`, `openalex.py`), `search.py` (keyword mode: federate, merge, dedupe) and `snowball.py` (backward/forward expansion from seed DOIs).
- `skills/proposal-lit-search/SKILL.md`: modes, relevance judgment by the agent, key-upgrade guidance, degradation rules, CSL-YAML merge into the proposal.
- Sync map extension: scripts vendored into `proposal-ideate/scripts/`.
- L0 tests on canned API responses (no network); live smoke tests behind a `live` marker, excluded by default.
- `skip_specs: true` — implements existing requirements.

## Capabilities

### New Capabilities

<!-- none — skip_specs: true -->

### Modified Capabilities

<!-- none -->

## Impact

- New scripts + SKILL.md + tests + sample-response data files; sync_shared.py map grows; ideate's scripts/ tree materializes.
- Keys: `OPENALEX_API_KEY` (present), optional `SEMANTIC_SCHOLAR_API_KEY`, optional `CONTACT_EMAIL` for politeness headers.
