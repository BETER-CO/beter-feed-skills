# BETER public documentation — page map

Base: `https://docs.beter.co/public/`

Pages are server-rendered; a plain HTTP GET returns full content. There is no
`llms.txt` and no raw-markdown route — `.md` and `.txt` suffixes return 404.

Fetch raw and extract the text yourself. Page content sits inside `<main>`; the rest
of the payload is the sidebar and the framework's hydration data, which is why a
page can be several hundred kilobytes for a few screens of prose. Decode as UTF-8:
pages carry typographic quotes and Cyrillic name examples, and a lossy decode
corrupts them silently.

Trailing slashes redirect — `/public/` 308s to `/public`.

## Feed — General

| Path | Page |
|---|---|
| `feed/general/terms` | Terms |
| `feed/general/matches-lifecycle` | Matches Lifecycle |

## Feed — Integration

| Path | Page |
|---|---|
| `feed/integration/general-recommendation` | General Recommendations |
| `feed/integration/signalr-websocket/signalr-websocket` | SignalR and WebSocket |
| `feed/integration/signalr-websocket/go-client` | Go Client |
| `feed/integration/logging-and-metrics` | Logging and metrics |
| `feed/integration/message-processing` | Message Processing |
| `feed/integration/message-sizes-and-frequency` | Message sizes and frequency of updates |
| `feed/integration/rate-limits` | Rate Limits |
| `feed/integration/testing-feed` | Testing Feed |

## Feed — General feed info

| Path | Page |
|---|---|
| `feed/general-feed-info/types-of-messages` | Types of Messages |
| `feed/general-feed-info/special-events` | Special events |
| `feed/general-feed-info/offset-logic` | Offset Logic |
| `feed/general-feed-info/multiple-consumers` | Multiple Feed Consumer in parallel |

## Feed — Channels

| Path | Page |
|---|---|
| `feed/time-table-feed/general-info-tt` | Timetable Feed — General Info |
| `feed/time-table-feed/data-contracts-tt` | Timetable Feed — Data Contracts |
| `feed/time-table-feed/video-distribution` | Video Distribution |
| `feed/time-table-feed/grid-widgets` | GRID Widgets |
| `feed/scoreboard-feed/general-info-sc` | Scoreboard Feed — General Info |
| `feed/scoreboard-feed/data-contracts-sc` | Scoreboard Feed — Data Contracts |
| `feed/scoreboard-feed/timer` | Timer |
| `feed/incident-feed/general-info-in` | Incident Feed — General Info |
| `feed/incident-feed/data-contracts-in` | Incident Feed — Data Contracts |
| `feed/incident-feed/incidents` | Incidents |
| `feed/incident-feed/incident-sources` | Incident Sources |
| `feed/incident-feed/incident-cancellation` | Incident Cancellation |
| `feed/trading-feed/general-info-tr` | Trading Feed — General Info |
| `feed/trading-feed/data-contracts-tr` | Trading Feed — Data Contracts |
| `feed/trading-feed/general-market-list` | Markets structure |
| `feed/trading-feed/meta-data` | Meta Data |

## Feed — Sandbox, API, troubleshooting, FAQ

| Path | Page |
|---|---|
| `feed/testing-sandbox/general` | Testing Sandbox |
| `feed/api/general-info-api` | API Overview |
| `feed/api/endpoints` | API Endpoints |
| `feed/api/schedule-delivery` | Schedule delivery |
| `feed/troubleshooting/network-performance` | Network Performance |
| `feed/troubleshooting/packet-sniffing` | Packet Sniffing |
| `feed/faq/bet-event-lifecycle` | Bet Event Lifecycle |

## News and changelog

| Path | Page |
|---|---|
| `` (base) | News |
| `changelog` | Changelog — current |
| `changelog/archive/y2025` | Changelog archive 2025 |
| `changelog/archive/y2024` | Changelog archive 2024 |

Changelog entries are anchors on one page, keyed by date as `#DDMMYYYY` — for
example `changelog#17062026`.

## Client Console

The Client Console at `https://console.beter.co` is where matches are booked and
market settings are made; those settings determine what the feed delivers, so these
pages are in scope for integration questions.

| Path | Page |
|---|---|
| `client-console/admin-guide` | Administrator Guide |
| `client-console/user-guide` | User Guide |

## Site notes

The site runs on Nextra 4 with a Pagefind search index at
`_pagefind/pagefind-entry.json` (79 indexed pages). The index is binary and needs
the Pagefind WASM runtime, so it is not usable for direct lookups; navigate by the
paths above instead.
