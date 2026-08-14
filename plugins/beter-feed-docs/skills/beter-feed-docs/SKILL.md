---
name: beter-feed-docs
description: Use when the task involves integrating, consuming, or debugging the BETER sports data feed — SignalR/WebSocket connection to the BETER feed, timetable/scoreboard/incident/trading channels, message contracts, offsets, recovery snapshots, heartbeats, rate limits, the BETER testing sandbox, or the BETER feed HTTP API. Also use for questions naming BETER, docs.beter.co, or a BETER client console feed credential.
---

# BETER feed documentation

Answers questions about the BETER feed from the official public documentation at
`https://docs.beter.co/public/` — the only source of truth for BETER feed behaviour.

## The rule

Fetch the page before answering. The BETER feed is a private product: its channel
names, contracts, offset semantics, and limits are not in any model's training data,
and details change between releases. An answer produced without a fetched page is a
guess and will be wrong on specifics.

Every answer states which documentation page it came from, as a full URL.

If the documentation does not cover the question, say so and point at the nearest
page. Do not fill the gap from general SignalR, WebSocket, or sports-data knowledge.

## Scope

In scope: BETER feed integration, its channels, contracts, API, sandbox, and
troubleshooting. Changelog and news when the question is about what changed.

Out of scope: everything else, including general SignalR/WebSocket programming with
no BETER specifics, the client's own application code, and BETER commercial terms.
For those, answer normally without this skill.

## How to answer

1. Pick the pages from the routing table below. Take the whole group when the
   question spans a channel — general info plus data contracts.
2. Fetch each page. Pages are server-rendered HTML; a plain HTTP GET returns the
   full content.
3. Answer from the fetched text. Quote field names, enum values, and limits exactly
   as written.
4. List the source URLs.

## Routing table

| Question is about | Fetch |
|---|---|
| Connecting, transport, protocol, client libraries | `feed/integration/signalr-websocket/signalr-websocket` |
| Go client | `feed/integration/signalr-websocket/go-client` |
| Reconnect, heartbeat, freshness, general integration advice | `feed/integration/general-recommendation` |
| How to process messages, ordering, idempotency | `feed/integration/message-processing` |
| Offsets, resuming after disconnect, recovery snapshot | `feed/general-feed-info/offset-logic`, `feed/general-feed-info/types-of-messages` |
| Message types | `feed/general-feed-info/types-of-messages` |
| Running several consumers | `feed/general-feed-info/multiple-consumers` |
| Rate limits | `feed/integration/rate-limits` |
| Message size, update frequency, bandwidth planning | `feed/integration/message-sizes-and-frequency` |
| Logging, metrics, what to instrument | `feed/integration/logging-and-metrics` |
| Timetable channel, fixtures, schedule | `feed/time-table-feed/general-info-tt`, `feed/time-table-feed/data-contracts-tt` |
| Video streams, GRID widgets | `feed/time-table-feed/video-distribution`, `feed/time-table-feed/grid-widgets` |
| Scoreboard channel, live score, match timer | `feed/scoreboard-feed/general-info-sc`, `feed/scoreboard-feed/data-contracts-sc`, `feed/scoreboard-feed/timer` |
| Incident channel, incident types, sources, cancellation | `feed/incident-feed/general-info-in`, `feed/incident-feed/data-contracts-in`, `feed/incident-feed/incidents`, `feed/incident-feed/incident-sources`, `feed/incident-feed/incident-cancellation` |
| Trading channel, odds, markets, market metadata | `feed/trading-feed/general-info-tr`, `feed/trading-feed/data-contracts-tr`, `feed/trading-feed/general-market-list`, `feed/trading-feed/meta-data` |
| HTTP API, endpoints, schedule delivery | `feed/api/general-info-api`, `feed/api/endpoints`, `feed/api/schedule-delivery` |
| Sandbox, test environment, test data | `feed/testing-sandbox/general`, `feed/integration/testing-feed` |
| Terminology, entity names | `feed/general/terms` |
| Match states, lifecycle, when a match ends | `feed/general/matches-lifecycle` |
| Special events, technical matches | `feed/general-feed-info/special-events` |
| Bet settlement lifecycle | `feed/faq/bet-event-lifecycle` |
| Dropped messages, latency, network problems | `feed/troubleshooting/network-performance`, `feed/troubleshooting/packet-sniffing` |
| What changed, new fields, deprecations | `changelog` |

Prefix every path with `https://docs.beter.co/public/`.

The complete page list, including the Client Console pages, is in
[references/doc-map.md](references/doc-map.md).

## Common mistakes

**Answering a contract question from one page.** Field lists live on the channel's
Data Contracts page; the General Info page describes the channel. Fetch both.

**Treating a code sample as the specification.** Samples illustrate the connection
shape. Limits, retry rules, and required headers come from the integration pages.

**Assuming standard SignalR defaults.** BETER supports the WebSockets transport
only; Server-Sent Events and long polling are rejected. Check the page rather than
the SignalR default for anything transport-related.

**Answering "why is my feed behind" without the offset page.** Lag, replay, and
snapshot behaviour are defined by offset logic, not by the client library.
