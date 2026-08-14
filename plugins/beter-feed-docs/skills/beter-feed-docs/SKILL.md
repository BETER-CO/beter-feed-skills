---
name: beter-feed-docs
description: Use when the task involves integrating, consuming, or debugging the BETER sports data feed — SignalR/WebSocket connection to the BETER feed, timetable/scoreboard/incident/trading channels, message contracts, offsets, connection snapshots, timers, incident or market codes, rate limits, the BETER testing sandbox, the BETER feed HTTP API, or the BETER Client Console. Also use for any question naming BETER, docs.beter.co, or console.beter.co, and when a BETER feed payload needs interpreting.
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

## When the documentation does not cover it

Say that the documentation does not cover it, name the nearest page, and point the
reader at their BETER integration manager or `support@beter.co`. Do not fill the gap
from general SignalR, WebSocket, or sports-betting knowledge, and do not infer an
answer from field names.

Questions the documentation cannot answer, however they are phrased:

- Whether a field, market, or sport will be added, and when.
- What is enabled for this client's account — booked matches, market templates,
  margins, whitelisted video domains, credentials.
- Why a specific match, event id, or payload behaved as it did in production.
- Commercial terms, pricing, coverage guarantees.

These go to BETER, not to the model. Repeat the reader's specifics — event id,
payload, timestamps — so the message they send is actionable.

## Numeric codes are never guessed

The feed identifies almost everything by number: `msgType`, `stage`, `interval`,
`result`, incident `type`, market and outcome ids, sport ids. A plausible-sounding
name for a code is worse than no answer, because it is silently wrong.

Resolve every code against the page that lists it — usually the channel's Data
Contracts page or `feed/general-feed-info/types-of-messages`. If the code is absent
from the documentation, say the code is undocumented and quote it back.

## How to answer

1. Pick the pages from the routing table. Take the whole group when the question
   spans a channel — general info plus data contracts.
2. Fetch each page. Pages are server-rendered HTML; a plain HTTP GET returns the
   full content.
3. Answer from the fetched text. Quote field names, enum values, formulas, and
   limits exactly as written.
4. List the source URLs.

When the question carries a payload, walk the payload field by field against the
contract, resolve every numeric code, and state which fields the documentation does
not describe.

## Routing table

| Question is about | Fetch |
|---|---|
| Connecting, transport, protocol, client libraries | `feed/integration/signalr-websocket/signalr-websocket` |
| Go client | `feed/integration/signalr-websocket/go-client` |
| Reconnect, heartbeat, freshness, general integration advice | `feed/integration/general-recommendation` |
| Processing messages, ordering, idempotency, duplicates | `feed/integration/message-processing`, `feed/general-feed-info/multiple-consumers` |
| Offsets, resuming after disconnect, connection snapshot | `feed/general-feed-info/offset-logic`, `feed/general-feed-info/types-of-messages` |
| `msgType`, message kinds | `feed/general-feed-info/types-of-messages` |
| Running several consumers in parallel | `feed/general-feed-info/multiple-consumers` |
| Rate limits | `feed/integration/rate-limits` |
| Message size, update frequency, bandwidth planning | `feed/integration/message-sizes-and-frequency` |
| Logging, metrics, what to instrument | `feed/integration/logging-and-metrics` |
| Timetable channel, fixtures, schedule, league and tournament fields | `feed/time-table-feed/general-info-tt`, `feed/time-table-feed/data-contracts-tt` |
| Video streams, broadcast URLs, GRID widgets | `feed/time-table-feed/video-distribution`, `feed/time-table-feed/grid-widgets` |
| Scoreboard channel, scores, `stage`, `interval` | `feed/scoreboard-feed/general-info-sc`, `feed/scoreboard-feed/data-contracts-sc` |
| Match timer, `accelerationFactor`, `direction`, game clock | `feed/scoreboard-feed/timer` |
| Incident channel, incident types, sources, cancellation | `feed/incident-feed/general-info-in`, `feed/incident-feed/data-contracts-in`, `feed/incident-feed/incidents`, `feed/incident-feed/incident-sources`, `feed/incident-feed/incident-cancellation` |
| Trading channel, odds, market status, settlement | `feed/trading-feed/general-info-tr`, `feed/trading-feed/data-contracts-tr` |
| Which markets exist for a sport, market ids | `feed/trading-feed/general-market-list`, `feed/trading-feed/meta-data` |
| HTTP API, endpoints, schedule delivery | `feed/api/general-info-api`, `feed/api/endpoints`, `feed/api/schedule-delivery` |
| Sandbox, test environment, test data | `feed/testing-sandbox/general`, `feed/integration/testing-feed` |
| Terminology, entity names | `feed/general/terms` |
| Match states, lifecycle, when a match ends | `feed/general/matches-lifecycle` |
| Special events, technical matches | `feed/general-feed-info/special-events` |
| Bet settlement lifecycle | `feed/faq/bet-event-lifecycle` |
| Dropped messages, latency, network problems | `feed/troubleshooting/network-performance`, `feed/troubleshooting/packet-sniffing` |
| Booking matches, market settings, margins, auditing delivered data | `client-console/user-guide`, `client-console/admin-guide` |
| What changed, new fields, deprecations | `changelog` |

Prefix every path with `https://docs.beter.co/public/`.

The complete page list is in [references/doc-map.md](references/doc-map.md).

## Common mistakes

**Answering a contract question from one page.** Field lists live on the channel's
Data Contracts page; the General Info page describes the channel. Fetch both.

**Naming a numeric code from memory.** `stage`, `interval`, and incident `type`
values are BETER-specific. Look them up.

**Assuming standard SignalR defaults.** BETER supports the WebSockets transport
only; Server-Sent Events and long polling are rejected. Check the page rather than
the SignalR default for anything transport-related.

**Answering "why is my feed behind" without the offset page.** Lag, replay, and
snapshot behaviour are defined by offset logic, not by the client library.

**Turning a client-console or account question into a feed answer.** Bookings,
market templates, and margins are configured per client; the documentation
describes the screens, not what a given account has set.
