## MODIFIED Requirements

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

## ADDED Requirements

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
