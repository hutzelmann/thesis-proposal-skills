# skill-lit-search Specification

## Purpose
Multi-source academic literature search producing CSL-YAML reference entries, with keyword and citation-snowballing modes, designed keyless-first for Computer Science.

## Requirements

### Requirement: Academic sources with judged relevance
The skill SHALL search academic literature only and SHALL judge actual relevance to the topic/proposal rather than returning keyword hits. Peer-reviewed venues SHALL be preferred over preprints when both versions exist.

Relevance SHALL be judged as a merge precondition, not as a presentation filter: an entry enters the proposal's `references:` block only when the claim it will support in this proposal can be named — a research question it grounds, a delta it evidences, or a method choice it supports. A candidate that is academic, correct, and topically adjacent but supports no such claim SHALL be rejected rather than merged, and rejected candidates are recorded as the Excluded Literature requirement specifies. The skill SHALL NOT merge an entry on the expectation that a use for it will be found later: after merging, an entry no claim needs leaves the proposal only through the writing skill's removal path, and the intervening state pulls the proposal's text toward the entry.

#### Scenario: Keyword-matching but irrelevant paper
- **WHEN** a source API returns a paper matching the query terms but unrelated to the research focus
- **THEN** the skill excludes it from the results

#### Scenario: Adjacent paper with no claim to support
- **WHEN** a returned paper is peer-reviewed and shares the proposal's domain but supports no research question, delta statement, or method choice the proposal makes
- **THEN** the skill rejects it, states that no claim in the proposal needs it, and does not merge it into `references:`

#### Scenario: Accepted entry names its claim
- **WHEN** the skill merges a candidate into `references:`
- **THEN** its report names the claim in the proposal that the entry supports

### Requirement: Keyword and snowballing modes
The skill SHALL support (a) keyword/topic search and (b) snowballing from seed papers in the proposal's `references`: backward via their reference lists and forward via citing papers and recommendations.

#### Scenario: Snowballing from three seeds
- **WHEN** the user requests expansion from a proposal with three references
- **THEN** the skill gathers referenced and citing works for those seeds, ranks by relevance, and proposes additions

### Requirement: Multi-source federation with graceful degradation
Results SHALL be merged and deduplicated across sources by DOI or normalized title. A failing or rate-limited source SHALL degrade the search to the remaining sources with a note — it MUST NOT block the search. A degraded source SHALL be named in its note together with the class of its failure, and SHALL NOT be reported as a source that answered with zero results. Candidates SHALL be the only content on standard output; notes and the source summary go to standard error. The search SHALL exit successfully when at least one candidate remains after merging, and with a failure status when none does, whatever the reason.

#### Scenario: One source down
- **WHEN** a literature API is unreachable
- **THEN** the search completes on remaining sources and reports the degradation

#### Scenario: One source answers with a verification page
- **WHEN** DBLP answers with a verification page the script cannot pass while another source returns candidates
- **THEN** standard output carries only the CSL-YAML candidates from the other sources, standard error names DBLP and the verification page as the cause, the source summary does not list DBLP as a contributor, and the search exits successfully

#### Scenario: Every source degraded
- **WHEN** every requested source fails
- **THEN** standard output stays empty, the notes name each source, and the search exits with a failure status as before

### Requirement: Keyless baseline, keys as guided upgrades
The default installation SHALL work fully without any API key. Optional keys only improve rate limits, abstracts, or coverage. The skill SHALL detect missing/exhausted keys (including quota errors) and degrade cleanly. When a free key would help, the skill SHALL offer agent-guided setup around one central key file at the workspace root, shared by every proposal in that workspace: state the concrete benefit, point to the signup location, create or update the key file with a named placeholder for the key, ensure version-control ignores cover the file, have the user paste the key value into the file themselves, and validate the result with a test call that reads the file mechanically. The secret value SHALL NOT pass through the agent: the agent never asks the user to provide the value in conversation and never reads, echoes, logs, or writes it. An error caused by a missing key SHALL name every location that was consulted.

#### Scenario: No keys configured
- **WHEN** the user runs a search with zero keys configured
- **THEN** the search succeeds on keyless sources and mentions what an optional key would add

#### Scenario: Quota exhausted
- **WHEN** a keyed source returns a quota-exhausted error
- **THEN** the skill continues with the other sources and reports the limitation

#### Scenario: Key is missing
- **WHEN** a keyed source is reached with no key available
- **THEN** the reported error names the environment variable and every key-file location that was searched

#### Scenario: Guided setup hand-off
- **WHEN** the user accepts guided key setup
- **THEN** the agent creates or updates the workspace-root key file with an empty placeholder entry, directs the user to paste the key into that file, and verifies afterwards by running a search — without the key value ever appearing in the conversation or in any agent-written content

#### Scenario: User offers the key in chat
- **WHEN** the user pastes an API key value into the conversation
- **THEN** the agent does not repeat or store the value, and asks the user to put it into the key file themselves

### Requirement: CSL-YAML output into the proposal
Accepted findings SHALL be written as CSL-YAML entries into the proposal's `references` block, deduplicated against existing entries. Each entry carries abstract, authors, year, and DOI when available; a URL is included only when no DOI exists.

#### Scenario: Entry with DOI
- **WHEN** a selected paper has a DOI
- **THEN** the stored entry contains the DOI and no URL field

### Requirement: Credential resolution without directory traversal
Credentials SHALL resolve per key, in this order: the process environment, the file named by `$THESIS_PROPOSAL_KEYS`, `api-keys.env` in the working directory, then a user-global `api-keys.env` under the user's config directory. Scripts SHALL NOT search ancestor directories or any other location for key files. Resolution SHALL proceed to the next location when a file exists but does not define the requested key, so that a workspace file and a global file compose rather than shadow one another. Key files SHALL remain one `KEY=VALUE` per line with `#` comments, and a missing or unreadable file SHALL NOT be an error. A key-related error message SHALL name every location that was consulted.

#### Scenario: Script run from the workspace root
- **WHEN** a script runs in a directory whose `api-keys.env` defines the requested key
- **THEN** the key resolves from that file

#### Scenario: Script run from a workspace subdirectory
- **WHEN** a script runs from a subdirectory while `api-keys.env` sits only at the workspace root and neither the environment nor `$THESIS_PROPOSAL_KEYS` supplies the key
- **THEN** the key does not resolve and the affected source degrades with the documented error naming the consulted locations

#### Scenario: Workspace and global files compose
- **WHEN** the workspace file defines only the API key and the global file defines only `CONTACT_EMAIL`
- **THEN** both values resolve

#### Scenario: Key file in an ancestor directory
- **WHEN** an `api-keys.env` exists in a parent of the working directory and nowhere else
- **THEN** it is not consulted

### Requirement: Static source registry
The orchestrator scripts SHALL resolve literature sources from a fixed registry compiled into the scripts. Source selection input SHALL be validated against that registry: a request naming an unknown source SHALL be rejected with an error listing the valid names, and SHALL NOT cause any module loading, code execution, or network access derived from the unknown name.

#### Scenario: Unknown source requested
- **WHEN** a search is invoked with `--sources dblp,evilmodule`
- **THEN** the run fails before any search with an error naming `evilmodule` as unknown and listing the valid sources

#### Scenario: Valid subset requested
- **WHEN** a search is invoked with `--sources dblp,crossref`
- **THEN** exactly those sources run

### Requirement: Excluded literature recorded in the notes file
When a companion `<slug>.notes.md` exists, the literature-search skill SHALL record rejected candidates in its Excluded Literature section — entry identifier (DOI or title) plus a one-line reason — and SHALL NOT re-propose an entry that section already lists in a later search. Acceptance bookkeeping is unchanged: accepted entries go into the proposal's `references:` block as before. When no notes file exists, rejections MAY go unrecorded; the skill SHALL NOT create the notes file for this purpose alone.

#### Scenario: Rejected candidate not proposed twice
- **WHEN** a search surfaces a paper the notes Excluded Literature section already lists
- **THEN** the skill skips it without presenting it to the user again

#### Scenario: Rejection recorded with reason
- **WHEN** the user rejects a candidate during result review and a notes file exists
- **THEN** the Excluded Literature section gains the entry's identifier and a one-line reason

### Requirement: Level-aware literature stance
When the proposal's subtitle states the degree level, the skill SHALL weight its relevance judgement accordingly: at Bachelor's level, established anchors — textbooks, surveys, canonical papers — are legitimate results alongside current work; at Master's level, recent primary literature capable of yielding the gap the proposal must argue is prioritized. The weighting is a single self-contained rule in the skill; it adds no reference wiring, changes no source registry or query behavior, and is silently skipped when the level is unknown.

#### Scenario: Master search prioritizes gap-bearing work
- **WHEN** the subtitle declares a Master's thesis and results include both a survey and recent primary studies adjacent to the research questions
- **THEN** the relevance judgement ranks the primary studies as the results the proposal's argument needs, without discarding the survey

#### Scenario: Bachelor search accepts established anchors
- **WHEN** the subtitle declares a Bachelor's thesis
- **THEN** textbook and survey anchors are judged legitimate results, not down-ranked for being established

#### Scenario: Unknown level changes nothing
- **WHEN** the working directory's proposal states no level or no proposal is present
- **THEN** search and relevance judgement behave exactly as without this requirement

### Requirement: Single-context execution

A literature search SHALL be performed by one agent in one context: the shipped scripts — or, when script networking is denied, the agent's own read-only requests — gather the candidates, and the same agent judges the whole candidate set together and merges the accepted entries. The skill SHALL NOT spawn one helper agent per candidate, per source, or per research question, because a preprint and its published version are recognised only side by side, key uniqueness is a property of the whole references block, and the proposal and the notes file have one writer. The SKILL.md SHALL state this shape in an `## Execution shape` section that is the first section of the body, and the whole section SHALL be pinned verbatim offline.

#### Scenario: Host runs tasks as workflows by default
- **WHEN** the host's mode would judge relevance through one helper per candidate, or fetch through one helper per source on the networking-denied fallback
- **THEN** the candidate set is gathered and judged together in one context and merged by that one agent

#### Scenario: Section survives a rewrite
- **WHEN** a change rewords any part of the execution-shape section or moves it below another section, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

### Requirement: Verification pages passed or explained
The literature-search scripts SHALL recognize a source's anti-bot verification page by its markup, not by HTTP status or declared media type alone, and SHALL NOT report it as malformed data. When the page offers a plain refresh to the verifier's own pass-challenge address, the scripts SHALL pass it at most once per request: wait the delay the page states when that delay is at most 10 seconds, follow the refresh only when it targets the request's own scheme, host and port, carries no userinfo, and names the verifier's exact pass-challenge path, follow no redirect that step returns, and then repeat the original request with the cookie received. A page that arrived through a redirect SHALL NOT be passed, and once a pass on a host has failed, the scripts SHALL NOT attempt another on that host for the rest of the process. Cookies SHALL be held in memory for the life of one process, accepted from and sent to only hosts that served a recognized verification page, and never written to disk. The scripts SHALL NOT solve proof-of-work challenges, run page scripts, change their user agent, or relax TLS certificate verification.

A response that is not usable JSON SHALL be classified as one of: a verification page that was not passed; other HTML or non-JSON content, including an empty or oversized body; or malformed JSON, including nesting too deep to parse — alongside the existing HTTP-error, rate-limit and network-failure classes. A verification page that was not passed and other unexpected content SHALL NOT be retried; malformed JSON, HTTP 429/500/502/503 and network failures keep their bounded retries with backoff. Valid JSON reporting no hits SHALL remain a successful zero-result answer.

A diagnostic SHALL name the source, the numeric HTTP status, and the response media type when it is one of a fixed set of common types, and SHALL NOT contain the request URL, the query, the refresh target, cookies, any part of the response body, the user agent or its contact address, or a client address the page echoes. A network failure SHALL be described by a fixed name for its class — timeout, refused or closed connection, unresolved host name, TLS failure, invalid HTTP response — never by the error's own text, which can carry what the server sent. When the search reports a verification page that was not passed, its note SHALL add that a normal browser may still pass it, that the script stays blocked either way, and that the run continues without that source's results.

#### Scenario: Refresh-tier page passed
- **WHEN** DBLP answers with a verification page whose refresh, after 2 seconds, points to DBLP's own pass-challenge address
- **THEN** the script waits 2 seconds, follows the refresh once, repeats the query, and returns DBLP's records — and a second DBLP query in the same run is answered without another verification

#### Scenario: Refresh carried in the page markup
- **WHEN** the verification page states its refresh in the page markup instead of a response header
- **THEN** the script passes it the same way

#### Scenario: Pass does not get through
- **WHEN** the source answers with a verification page again after the pass
- **THEN** the source degrades with a verification-page diagnostic, and later requests to that host in the same run degrade at once, without another wait

#### Scenario: Verification page reached through a redirect
- **WHEN** the request is redirected and the redirect target answers with a verification page
- **THEN** the script does not attempt a pass and the source degrades with a verification-page diagnostic

#### Scenario: Refresh target that cannot be parsed
- **WHEN** a verification page's refresh names a target the URL parser rejects, such as an unclosed bracket
- **THEN** the source degrades with a verification-page diagnostic and no other exception reaches the caller

#### Scenario: Refresh target outside the verifier
- **WHEN** a verification page's refresh points to another host, scheme or port, or to any path other than the exact pass-challenge path
- **THEN** no request is sent to that target and the source degrades as a verification page that was not passed

#### Scenario: Pass step redirects elsewhere
- **WHEN** the pass-challenge address answers with a redirect to another origin
- **THEN** the redirect is not followed; only the original request is repeated

#### Scenario: Delay too long
- **WHEN** a verification page asks for a delay longer than 10 seconds, or states one that is not a plain number
- **THEN** the script does not wait or follow it, and the source degrades with a verification-page diagnostic

#### Scenario: Verification page with a misleading media type
- **WHEN** a verification page arrives labelled `application/json`, or with no media type at all
- **THEN** it is recognized as a verification page, not reported as malformed JSON

#### Scenario: Unrelated HTML page
- **WHEN** a source answers with an HTML page that mentions the verifier by name in its text but carries none of its markup
- **THEN** the diagnostic reports an unexpected HTML page, not a verification page, and the request is not retried

#### Scenario: Malformed JSON
- **WHEN** a source answers with a body that starts as JSON but does not parse
- **THEN** the request is retried with backoff as before and the final diagnostic says the JSON was malformed

#### Scenario: Valid empty result
- **WHEN** DBLP answers with valid JSON reporting zero hits
- **THEN** the source contributes zero candidates without a degradation note

#### Scenario: Hostile body
- **WHEN** a source answers with a body larger than the read limit, or with JSON nested deeply enough to exhaust the parser
- **THEN** the source degrades with a classified diagnostic and no other exception escapes to the caller

#### Scenario: Diagnostics reveal nothing private
- **WHEN** a verification page echoes the request's user agent with a contact address, the client's IP address and a challenge token, and its refresh target carries the query
- **THEN** none of those values, the query, nor the request URL appears in any diagnostic or note

#### Scenario: Server text in a network failure
- **WHEN** a server answers with a malformed status line carrying its own text
- **THEN** the diagnostic names an invalid HTTP response and contains none of that text

#### Scenario: Cookies from other sources
- **WHEN** a source that never served a verification page sets a cookie
- **THEN** the cookie is not stored and not sent with later requests

#### Scenario: Parent-domain cookie from a challenged host
- **WHEN** a challenged host holds a cookie scoped to a parent domain it shares with a host that never challenged
- **THEN** the cookie is sent only to the challenged host

### Requirement: Browser fallback for a blocked source
The skill's instructions SHALL document an optional browser route for a source the script reported as blocked by a verification page it could not pass. The route applies only when lookup consent exists and the host provides a browser the agent can control; otherwise the skill SHALL state that the source remains unavailable, continue with the other sources' results, and MAY offer manual browser retrieval as an option, never as a precondition for the search. In the browser the skill SHALL open the source's official API address with only query terms already cleared for lookup — never proposal text, notes, or reports — let the site's ordinary verification complete, and continue only when the page shows the API's JSON; a loaded page or a success status alone SHALL NOT count. Records retrieved this way SHALL be judged, deduplicated and merged under the same rules as script results and built from the record's own fields only, with no abstract or publication detail the record lacks. The skill SHALL NOT write raw retrieved responses into the workspace and SHALL NOT claim a download that did not happen; its report SHALL state which entries came through the browser. The instructions SHALL state that browser success does not unblock the script, and SHALL forbid copying browser cookies into the scripts, installing challenge solvers, rotating proxies, changing the user agent, and disabling certificate checks. The route SHALL stay inside the single search-judge-merge context.

#### Scenario: Browser route yields JSON
- **WHEN** DBLP is reported blocked, lookup consent exists, the host offers a controllable browser, and the API page shows DBLP's JSON after verification
- **THEN** the records are judged and merged with the script's candidates under the usual rules, the report names them as retrieved through the browser, and nothing claims the script recovered

#### Scenario: No browser available
- **WHEN** DBLP is reported blocked and the host offers no browser the agent can control
- **THEN** the skill says DBLP stayed unavailable, continues with the other sources' candidates, and offers manual browser retrieval only as an option

#### Scenario: Browser still shows the verification page
- **WHEN** the browser page loads but shows a verification page or anything other than DBLP's JSON
- **THEN** the skill treats DBLP as unavailable and merges nothing from it

#### Scenario: Browser-versus-script sentence survives a rewrite
- **WHEN** a change rewords the sentence stating that browser success does not unblock the script, without updating its pinned copy
- **THEN** the offline suite fails naming the skill and the difference

### Requirement: Search converges and hands over

Broad searching SHALL end when the contribution delta and every research question — or, before a draft exists, every candidate direction — has at least one accepted source behind it, or when a search round, by keyword or by snowballing, adds no accepted entry. After that, the skill SHALL search only for a gap it names. The reference count SHALL NOT be a reason to continue: the minimum is the check's to report, and the claim-backed merge rule stays binding however far below it the block is.

The report SHALL close with the stage handoff (skill-packaging): without a draft, the recommended step is the full draft; with a draft and newly merged entries, a writing pass that cites them where a claim needs them; when a research question remains unbacked after saturation, the handoff names that gap and puts its resolution as an anchored decision — a narrower question, a targeted search, or the student's own sources.

#### Scenario: Claims covered
- **WHEN** a round leaves the delta and every research question backed by an accepted source and no draft exists
- **THEN** the skill stops broad searching and the handoff recommends a full draft from the seed and these sources

#### Scenario: Saturated round
- **WHEN** a snowballing round yields candidates of which none is accepted
- **THEN** the skill reports the round as saturated and does not start another broad round on its own

#### Scenario: Below the reference minimum but covered
- **WHEN** every claim is backed and the reference block is still below the check's minimum
- **THEN** the skill does not merge entries without a claim to reach the minimum, and the handoff names the shortfall as the check's finding rather than as a reason to keep searching

#### Scenario: Unbacked research question after saturation
- **WHEN** a research question still has no accepted source after a saturated round
- **THEN** the handoff names that gap and offers its resolution as an anchored choice rather than recommending another broad search
