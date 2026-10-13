## MODIFIED Requirements

### Requirement: Multi-source federation with graceful degradation
Results SHALL be merged and deduplicated across sources by DOI or normalized title. A failing or rate-limited source SHALL degrade the search to the remaining sources with a note — it MUST NOT block the search. A degraded source SHALL be named in its note together with the class of its failure, and SHALL NOT be reported as a source that answered with zero results. A failure the scripts did not anticipate SHALL be noted with the source and the name of the error's type only, never with the error's own text. A note that several seeds or directions of one snowballing run would repeat word for word SHALL be printed once in that run. Candidates SHALL be the only content on standard output; notes and the source summary go to standard error, and the summary keeps its form `sources: name(n), …`, or `sources: none` when no source answered. The search SHALL exit successfully when at least one candidate remains after merging, and with a failure status when none does, whatever the reason.

#### Scenario: One source down
- **WHEN** a literature API is unreachable
- **THEN** the search completes on remaining sources and reports the degradation

#### Scenario: One source answers with a verification page
- **WHEN** DBLP answers with a verification page the script cannot pass while another source returns candidates
- **THEN** standard output carries only the CSL-YAML candidates from the other sources, standard error names DBLP and the verification page as the cause, the source summary does not list DBLP as a contributor, and the search exits successfully

#### Scenario: Every source degraded
- **WHEN** every requested source fails
- **THEN** standard output stays empty, the notes name each source, and the search exits with a failure status as before

#### Scenario: Unanticipated failure in a source
- **WHEN** a source fails with an error the scripts did not anticipate, whose text carries server-chosen content, an address and a line break, while another source returns candidates
- **THEN** a single note line names the source and the error's type and nothing of its text, the other source's candidates are emitted, and the source summary keeps its form without the failed source

#### Scenario: Same note from several seeds
- **WHEN** a snowballing run from two seeds in both directions reaches OpenAlex with no key configured
- **THEN** the missing-key note appears once, and every other distinct note of the run appears once as well

### Requirement: Verification pages passed or explained
The literature-search scripts SHALL request every source over HTTPS. They SHALL recognize a source's anti-bot verification page by its markup, not by HTTP status or declared media type alone, and SHALL NOT report it as malformed data. When the page offers a plain refresh to the verifier's own pass-challenge address, the scripts SHALL pass it at most once per request: wait the delay the page states when that delay is at most 10 seconds, follow the refresh only when it targets the request's own scheme, host and port, carries no userinfo, and names the verifier's exact pass-challenge path, follow no redirect that step returns, and then repeat the original request with the cookie received. A page that arrived through a redirect SHALL NOT be passed, and once a pass on a host has failed, the scripts SHALL NOT attempt another on that host for the rest of the process. Cookies SHALL be held in memory for the life of one process, accepted from and sent to only hosts that served a recognized verification page, and never written to disk. The scripts SHALL NOT solve proof-of-work challenges, run page scripts, change their user agent, or relax TLS certificate verification.

A response that is not usable JSON — or, for arXiv, not a usable Atom feed — SHALL be classified as one of: a verification page that was not passed; other HTML, other XML, or other content, including an empty or oversized body; or a malformed document, including JSON nested too deep to parse and a feed nested deeper than any feed needs, whose parse SHALL stop at that depth — alongside the existing HTTP-error, rate-limit and network-failure classes. A body SHALL be parsed as a feed only when its first markup, after an optional XML declaration, is the feed element, so that no document type declaration, and with it no entity definition, ever reaches the XML parser. A body that starts as the expected JSON or feed SHALL NOT be taken for a verification page, whatever text its records carry. A verification page that was not passed, other unexpected content, and any HTTP status other than 429, 500, 502 or 503 SHALL NOT be retried; a malformed document, HTTP 429/500/502/503 and network failures keep their bounded retries with backoff. Valid JSON reporting no hits, and a valid feed with no entries, SHALL remain a successful zero-result answer.

A diagnostic SHALL name the source, the numeric HTTP status, and the response media type when it is one of a fixed set of common types, and SHALL NOT contain the request URL, the query, the refresh target, cookies, API keys or access tokens the request carries, the server's reason phrase, any part of the response body, the user agent or its contact address, or a client address the page echoes. A network failure SHALL be described by a fixed name for its class — timeout, refused or closed connection, unresolved host name, TLS failure, invalid HTTP response — never by the error's own text, which can carry what the server sent. When the search reports a verification page that was not passed, its note SHALL add that a normal browser may still pass it, that the script stays blocked either way, and that the run continues without that source's results.

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
- **WHEN** a source answers with a body larger than the read limit, with JSON nested deeply enough to exhaust the parser, or with a feed nested deeper than any feed needs
- **THEN** the source degrades with a classified diagnostic, the feed's parse stops at the depth limit instead of reading on, and no other exception escapes to the caller

#### Scenario: Diagnostics reveal nothing private
- **WHEN** a verification page echoes the request's user agent with a contact address, the client's IP address and a challenge token, its refresh target carries the query, the verifier sets cookies with distinctive values, and the request carries an API key and an access token
- **THEN** none of those values, the query, nor the request URL appears in any diagnostic or note, for JSON and feed requests alike

#### Scenario: Server text in a network failure
- **WHEN** a server answers with a malformed status line carrying its own text
- **THEN** the diagnostic names an invalid HTTP response and contains none of that text

#### Scenario: Cookies from other sources
- **WHEN** a source that never served a verification page sets a cookie
- **THEN** the cookie is not stored and not sent with later requests

#### Scenario: Parent-domain cookie from a challenged host
- **WHEN** a challenged host holds a cookie scoped to a parent domain it shares with a host that never challenged
- **THEN** the cookie is sent only to the challenged host

#### Scenario: arXiv requested over HTTPS
- **WHEN** the search queries arXiv
- **THEN** the request goes to arXiv's HTTPS address directly, with no plain-HTTP request before it, and no shipped literature-search script names a plain-HTTP address to request

#### Scenario: arXiv answers with an HTML page
- **WHEN** arXiv answers with an HTML page instead of its feed
- **THEN** the diagnostic reports an HTML page, not malformed XML, and the request is not retried

#### Scenario: arXiv answers with other XML
- **WHEN** arXiv answers with well-formed XML that is not its Atom feed, such as an XHTML page or a feed element in another namespace
- **THEN** arXiv degrades with an unexpected-content diagnostic and is not listed as a source that answered with zero results

#### Scenario: Malformed feed
- **WHEN** arXiv answers with a body that starts as its feed but does not parse
- **THEN** the request is retried with backoff and the final diagnostic says the XML was malformed

#### Scenario: Entity definitions in an XML answer
- **WHEN** an XML answer declares a document type with entity definitions before its root element, also when it hides the declaration inside the XML declaration or behind a processing instruction
- **THEN** the body is not parsed, no entity is expanded, and the source degrades with an unexpected-content diagnostic without retrying

#### Scenario: Verifier markup inside a valid answer
- **WHEN** a valid JSON answer or a valid feed carries the verifier's markup in a record's text, such as an abstract quoting it
- **THEN** the answer's records are returned and no verification pass is attempted

#### Scenario: Not-found is not retried
- **WHEN** arXiv answers HTTP 404
- **THEN** the request is sent once, and the diagnostic names the source and the status number and none of the server's reason text

#### Scenario: arXiv rate limit or server error
- **WHEN** arXiv answers HTTP 503 twice and then its feed
- **THEN** the request is retried with backoff and the feed's records are returned

#### Scenario: Valid empty feed
- **WHEN** arXiv answers with a valid feed that holds no entries
- **THEN** arXiv contributes zero candidates without a degradation note
