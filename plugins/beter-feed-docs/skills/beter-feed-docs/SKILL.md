---
name: beter-feed-docs
description: Use when the task involves integrating, consuming, or debugging the BETER sports data feed — SignalR/WebSocket connection to the BETER feed, timetable/scoreboard/incident/trading channels, message contracts, offsets, connection snapshots, timers, match regulations, incident or market codes, rate limits, the BETER testing sandbox, the BETER feed HTTP API, or the BETER Client Console. Also use for any question naming BETER, docs.beter.co, or console.beter.co, and when a BETER feed payload needs interpreting.
---

# BETER feed documentation

Answers questions about the BETER feed from the official public documentation at
`https://docs.beter.co/public/` — the source of truth for BETER feed behaviour.

## The rule

Fetch the page before answering. The BETER feed is a private product: its channel
names, contracts, numeric codes, offset semantics, and limits are not in any model's
training data, and they change between releases. An answer produced without a
fetched page is a guess and will be wrong on specifics.

Every answer states which documentation page it came from, as a full URL.

Answer in the language the question was asked in.

## The documentation is the default ground truth

`docs.beter.co/public` is what an answer rests on unless the reader says otherwise.

The documentation is not indexed for search and is not discoverable by looking for
it. BETER gives integrating teams the link directly. So a failed search means the
skill's own page map is the way in, not that the documentation is missing — never
conclude from a search that no public documentation exists.

Do not silently derive feed behaviour from other material that happens to be
reachable: service source code, internal repositories or wikis, packaged assemblies,
a decompiled client, or the reader's own existing integration. That material is
implementation rather than contract, it is often ahead of or behind the published
version, and it is not something an external reader could have consulted.

### When local BETER source would answer the question

BETER's own engineers run this skill too, and for their work — reproducing a client
report, testing against unreleased behaviour, checking whether the documentation
matches what ships — the local code is the right source and the documentation is the
stale one.

So do not ignore it silently. Say what you found, and ask:

> The documentation does not cover this. A BETER service repository on this machine
> appears to, at `<path>`. Should I answer from the implementation instead?

Then follow the answer. Without a yes, the answer stays on the documentation.

When permitted to use local source, keep it visibly separate: label it as
implementation rather than contract, name the version or commit it came from, and
say that it may differ from what any given client's account receives. Finish with a
warning that the passage cannot go to a client as written.

### What an answer may cite

An answer written for a client cites public documentation URLs only. No file paths,
no internal hostnames, no repository names, no class or namespace names, no ticket
keys, no names of other BETER clients — those travel with the text when it is
forwarded.

An answer for a BETER engineer who authorised the implementation source may cite
that source, and should mark the whole passage as internal.

Default to the client-facing form. Ask which one is wanted when it is unclear and
the difference would change the answer.

## When the documentation does not cover it

Say that the documentation does not cover it, name the pages you searched, and point
the reader at their BETER integration manager or `support@beter.co`. Do not fill the
gap from general SignalR, WebSocket, or sports-betting knowledge, and do not infer an
answer from field names. Where local BETER source would answer it, ask first — see
above.

State the basis of a silence claim: which pages were fetched, and that a statement
may exist on a page not opened. The site's search index cannot be queried directly,
so a silence claim is only ever as wide as the sweep behind it. "I fetched these
seven pages and none of them states X" is honest; "the documentation does not
mention X" is a claim about all 43 pages.

Questions the documentation cannot answer, however they are phrased:

- Whether a field, market, or sport will be added, and when.
- What is enabled for this reader's account right now — booked matches, market
  templates, margins, whitelisted video domains, credentials.
- Why a specific match, event id, or payload behaved as it did in production.
- Commercial terms, pricing, coverage guarantees.

Repeat the reader's specifics — event id, payload, timestamps — so the message they
send to BETER is actionable.

**Mechanism and state are different questions.** The documentation describes what
the Client Console can do and how to do it, and much of it is self-serve. Describe
the mechanism, name the screen and the path, and distinguish options whose effects
differ. Refuse only on the state: what this account currently has set. "Escalate and
say nothing" is the wrong answer when the reader could do it themselves in two
clicks.

## Guarantees are quoted, never inferred

A guarantee is a promise the reader will build on and will not re-check. Stating one
the feed does not make produces a consumer that silently corrupts data under
conditions nobody tests.

State a guarantee only when the documentation states it, and carry the exact scope
the documentation gives — per match, per connection, per channel, per sport. Quote
the sentence. A guarantee whose scope you cannot quote is not a guarantee you can
pass on.

This covers ordering, delivery, de-duplication, exactly-once and at-least-once
semantics, retention, replay windows, latency, uptime, and completeness.

Ordering guarantees are stated per channel, on that channel's General Info page, and
they are usually about a sequencing field rather than about arrival. "Ordered by a
field within a match" is a different promise from "arrives in order", and neither
implies anything about a second connection. Quote which one the page makes.

When the documentation is silent, say so, then name what the reader should handle
defensively — reordering, duplicates, gaps — and recommend confirming with BETER
before relying on anything stronger.

| Reasoning that leads to a wrong answer | What is actually true |
|---|---|
| "The transport is TCP, so ordering follows" | Ordering at the transport says nothing about ordering across channels, connections, or matches. |
| "SignalR preserves order on a hub connection" | The library's behaviour is not the product's promise, and BETER's scoping may be narrower. |
| "A support message once said ordering is guaranteed per connection" | An answer written for one incident is not the specification, and its scope is usually narrower than remembered. |
| "Offsets exist, so replay must be complete" | The existence of a mechanism is not a statement of its window or its completeness. |
| "The reader needs a definite answer" | A wrong guarantee is worse than an open question. Escalate. |

## Numeric codes are never guessed

The feed identifies almost everything by number: `msgType`, `stage`, `interval`,
`result`, incident `type`, market and outcome ids, sport ids. A plausible-sounding
name for a code is worse than no answer, because it is silently wrong.

Resolve every code against the page that lists it, and carry two properties of the
numbering with you:

**Codes are namespaced per discipline.** The same integer means different things in
different sports, and a code that exists for one sport may not exist at all for
another. Establish the sport before resolving any code, and say so when the reader
has not stated it.

**Different code spaces overlap.** `stage` and `interval` are separate
enumerations with overlapping ranges on the same page; market type ids and outcome
type ids likewise. A mapping applied to the wrong field does not error — it silently
mislabels. Confirm which field the number came from before naming it.

If a code is absent from the documentation, say it is undocumented and quote it back.

## Fetching so that quotes are real

Fetch the raw page and read the text yourself. Do not quote from a fetch tool that
summarises — a summariser drops exactly the clauses that carry scope, and those
clauses are the answer. Observed losses include "within the same Match" dropped from
an ordering guarantee, and "the Regulation object remains the single source of
truth" dropped from a field description.

Pages are server-rendered; a plain HTTP GET returns the full content. Page content
sits inside `<main>`. Decode as UTF-8 — pages carry typographic quotes and Cyrillic
in name examples, and a lossy decode corrupts precisely the characters some
questions are about.

Use a summarising fetch only to locate a page. Quote from raw text.

## Two sources that disagree

**Two documentation pages contradict each other.** Quote both, say which page is
which, and raise it with BETER. Do not silently prefer one. Where one page names
itself the source of truth, follow that and quote the sentence that says so.

**The reader's own material contradicts the documentation.** Mapping spreadsheets,
integration notes, and answers from earlier support threads go stale and get
transcribed wrongly. The documentation wins. Say plainly which of the reader's
values are wrong, what the documented values are, and what breaks if the wrong
mapping is already in production — then suggest they raise the artefact with BETER
if it came from BETER.

## How to answer

1. Pick the pages from the routing table. Take the whole channel group when the
   question touches a channel — General Info, Data Contracts, and any topic page.
2. Fetch each page raw.
3. Answer from the fetched text. Quote field names, enum values, formulas, and
   limits exactly as written.
4. List the source URLs.

Reasoning built on top of quoted material is welcome and often the most useful part
of an answer — working out what a contradiction breaks downstream, or what a mapping
error corrupts. Keep it visibly separate from what the documentation states, and
label it as derived.

When the question carries a payload, walk the payload field by field against the
contract, resolve every numeric code, and state which fields the documentation does
not describe.

## Routing table

| Question is about | Fetch |
|---|---|
| Connecting, transport, protocol, client libraries | `feed/integration/signalr-websocket/signalr-websocket` |
| Go client | `feed/integration/signalr-websocket/go-client` |
| Reconnect, heartbeat, freshness, general integration advice | `feed/integration/general-recommendation` |
| Ordering, sequencing, duplicates, idempotency | the General Info page of the channel in question, plus `feed/general-feed-info/offset-logic` |
| Not blocking the update handler, consumer throughput | `feed/integration/message-processing` |
| Offsets, resuming after disconnect, recovery, connection snapshot | `feed/general-feed-info/offset-logic`, `feed/general-feed-info/types-of-messages` |
| `msgType`, message kinds, snapshots vs updates | `feed/general-feed-info/types-of-messages` |
| Running several consumers in parallel | `feed/general-feed-info/multiple-consumers` |
| Rate limits | `feed/integration/rate-limits` |
| Message size, update frequency, bandwidth planning | `feed/integration/message-sizes-and-frequency` |
| Logging, metrics, what to instrument | `feed/integration/logging-and-metrics` |
| Timetable channel, fixtures, schedule, league and tournament names, `extra` object | `feed/time-table-feed/general-info-tt`, `feed/time-table-feed/data-contracts-tt` |
| Match format, event duration, regulations, 2x4 / 2x6 / Volta | `feed/scoreboard-feed/data-contracts-sc` (the `regulations` object is the source of truth), then `feed/time-table-feed/data-contracts-tt` for the informational `extra` copy |
| Video streams, broadcast URLs, GRID widgets | `feed/time-table-feed/video-distribution`, `feed/time-table-feed/grid-widgets` |
| Scoreboard channel, scores, `stage`, `interval` — distinct per-sport enumerations with overlapping ranges | `feed/scoreboard-feed/general-info-sc`, `feed/scoreboard-feed/data-contracts-sc` |
| Match timer, game clock, `accelerationFactor`, `direction` | `feed/scoreboard-feed/timer`, plus the scoreboard group for field types and stage codes |
| Incident channel, incident types, sources, cancellation, undo/redo | `feed/incident-feed/general-info-in`, `feed/incident-feed/data-contracts-in`, `feed/incident-feed/incidents`, `feed/incident-feed/incident-sources`, `feed/incident-feed/incident-cancellation` |
| Trading channel, odds, market status, settlement | `feed/trading-feed/general-info-tr`, `feed/trading-feed/data-contracts-tr` |
| Which markets exist for a sport, market and outcome ids | `feed/trading-feed/meta-data`, `feed/trading-feed/general-market-list` |
| HTTP API, endpoints, schedule delivery | `feed/api/general-info-api`, `feed/api/endpoints`, `feed/api/schedule-delivery` |
| Sandbox, test environment, test data | `feed/testing-sandbox/general`, `feed/integration/testing-feed` |
| Terminology, entity names | `feed/general/terms` |
| Match states, lifecycle, when a match ends | `feed/general/matches-lifecycle` |
| Special events, technical matches | `feed/general-feed-info/special-events` |
| Bet settlement lifecycle | `feed/faq/bet-event-lifecycle` |
| Dropped messages, latency, network problems | `feed/troubleshooting/network-performance`, `feed/troubleshooting/packet-sniffing` |
| Booking matches, excluding markets, margins, auditing delivered data | `client-console/user-guide`, `client-console/admin-guide` |
| What changed, new fields, deprecations | `changelog` |

Prefix every path with `https://docs.beter.co/public/`.

The complete page list is in [references/doc-map.md](references/doc-map.md).

## Common mistakes

**Answering a contract question from one page.** Field lists live on the channel's
Data Contracts page; the General Info page describes the channel and carries its
guarantees. Fetch both.

**Quoting a summariser.** If the quote was not taken from raw page text, it is a
paraphrase, and the clause it dropped is probably the one that mattered.

**Naming a numeric code from memory, or across sports.** Establish the sport, then
the field, then look the code up.

**Assuming standard SignalR defaults.** BETER supports the WebSockets transport
only; Server-Sent Events and long polling are rejected. Check the page rather than
the SignalR default for anything transport-related.

**Answering "why is my feed behind" without the offset page.** Lag, replay, and
snapshot behaviour are defined by offset logic, not by the client library.

**Widening a guarantee's scope.** "Ordered by a field within a match" is not
"arrives in order", and neither is "ordered across connections". Carry the scope
through verbatim or do not carry the claim.

**Assuming a documented workaround is still current.** Parsing a value out of a name
because the documentation once said to is worth re-checking against the contracts and
the changelog; fields get added and the workaround becomes the bug.

**Refusing a Client Console question that the reader could act on.** Describe the
mechanism; withhold only the account's current state.

**Concluding from a failed search that the documentation does not exist.** The site
is not indexed. Start from the page map, not from a search engine.

**Using local BETER source without asking, or refusing it without asking.** Both are
wrong. Surface it and let the reader decide.
