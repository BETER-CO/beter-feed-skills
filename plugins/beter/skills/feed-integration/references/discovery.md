# Discovery of an existing integration

Mapping mode Step 1 loads this file when the repository already consumes the feed and
holds no `beter-feed/` directory. The integration's truth is its code: which sports and
channels the consumer handles, how market keys resolve, what the default branch does.
Every mode presupposes the scope file, the snapshot and the specification, so the first
run derives them from the code, cites every row to the line it came from, has the
developer confirm, and only then brings the code under the specification. Nothing in the
code is edited here. Discovery is read-only.

## The precondition

Both facts, and only both: a consumer of this feed is in the repository, and
`beter-feed/` is not. A repository with `beter-feed/` re-enters mapping mode whatever its
code holds; a repository with no consumer starts at Step 1 as on a fresh repository.

A consumer is detected from files, not asked about, during Step 1's repository detection:

| Signal | Read |
|---|---|
| The feed's key on one type | A type, record or struct carrying `marketType`, `resultType`, `interval` and `subInterval` together, in the language's own casing, or `sportId` beside `marketType` |
| The feed's host | A string under `beter.co` |
| The feed's own names | A hub, channel, message or contract name as the `feed-docs` skill lists them, resolved through that skill rather than from memory |

One signal is enough to ask. None means no consumer, and Step 1 continues as written.

## Ask before reading

Detection reads only what Step 1 already reads. The integration itself is read after
the developer says so, in a `beter-questions` block, naming the files the signals were
found in:

```beter-questions
version: 1
questions:
  - id: q1
    about: "reading your existing feed integration"
    asked: "This repository already consumes the BETER feed (src/Feed/TradingConsumer.cs, src/Feed/MarketMap.cs) and holds no beter-feed/ directory. May I read the integration, read-only, and derive the scope, the specification and the bindings from it? Every row will cite the line it came from, and you confirm before anything is generated."
    blocking: true
```

A yes makes the next turn the discovery turn. The integration is read in that turn, the
turn stays discovery whichever mapping-mode steps it runs after the reading, and it ends
with the `beter-discovery` block described under *What discovery reports*.

A no ends discovery: say that scope and rows cannot be derived without reading, and
continue Step 1 as on a fresh repository, asking rather than reading.

## Reading is not inference

What the code states literally is the developer's declaration. What a reader has to
interpret is a proposal. Transcribing is not reading, and the table below draws the line
for code the way `references/mapping-mode/02-import-propose.md` draws it for a sheet.

| In the code | Written as |
|---|---|
| A literal: a dictionary entry, a `case` arm, an enum attribute, a constant table | A direct row: no `status`, cited by `at: "<path>:<line>"` |
| A key formed by interpreting logic: arithmetic over several dimensions, a condition combining channels, a target that depends on state | `status: proposed`, the code as `evidence`, reviewed like any proposal |
| A default or fall-through branch | A question: the unmapped policy, a declared `skip`, or an absence |
| A table loaded at runtime: a database, a configuration service, a file read at startup | `unread` in the discovery report, with its location, and a question |
| A mapping keyed on names rather than integer codes | Resolved to codes through the `feed-docs` skill and proposed, because a name may have moved |
| An intermediate enumeration the code defines: the feed into an internal enum, then into this system's vocabulary | Same-repository composition: two hops collapsed into one direct row, both hops cited in `at:` |
| A branch no test reaches | Reported, not read as a decision |
| An entry the code handles and the current catalog does not publish | Reported under `unpublished`; no row is written, because a row keys on a catalog entry; the developer decides |

A literal stays a direct row whatever the developer says about its target during
discovery: the doubt is about the code, not about the reading, and only a key formed by
interpreting logic is written `status: proposed`. The question the skill asked stays in
the `beter-questions` block; the answer to that doubt is written nowhere, because a wrong
literal is the developer's to correct, by editing the row or the code, at confirmation, and
generation then follows the digest rule of `references/generation-contract/03-emission.md`.
`status: proposed` on a literal is never the answer to a doubt. A field the code does not
give and the developer supplies in an answer, such as an outcome map or a target, is
written on the literal row with a `comment` naming the question, and the row stays direct
and in the specification: no answer removes it, because taking a literal out, like
correcting it, is the developer's edit at confirmation. A field the code does not give and
the developer has not supplied, such as an outcome map the skill could propose from the
catalog or the developer's vocabulary, is not written on a literal row: the skill asks for
it in the `beter-questions` block, the row stays as the code has it, and coverage lists
those outcomes as undecided until the answer comes
(`references/mapping-mode/05-validate-to-report.md`); the field it supplies is then written
as above.

The reading rules are the scaffold reader's (`references/spec-schema/04-proposals-and-evidence.md`, *The scaffold*):
the same `at:`, read-only, `unread` for what cannot be read. Only the output differs:
specification rows in this repository rather than a scaffold of another feed.

## Scope proposed from the code

Scope stays a declaration, and discovery proposes it. Each `in_scope` entry carries where
it was found and `status: proposed`; the developer confirms by edit, as for a row.
Absence in code is not a decision, so `deferred` is always asked and never read.

```yaml
version: 1
in_scope:
  - {sport: 6, name: "eFootball", channels: [trading],
     status: proposed, evidence: "src/Feed/TradingConsumer.cs:14 handles sportId 6"}
deferred: []
```

The timetable rows are proposed from where the code keys on sport. A sheet the developer
also keeps is asked about only for what the code leaves uncovered (Step 3), because a
sheet may hold decisions the code does not.

## Rows read from the code

A direct row is the row shape of `references/spec-schema/01-file-and-keys.md` with one more field:

```yaml
markets:
  - key: {marketType: 8, resultType: 1, interval: 1, subInterval: 0}
    target: {id: "Match Winner"}
    outcomes: {1: "1", 2: "X", 3: "2"}
    at: "src/Feed/MarketMap.cs:19"
```

`at:` is the file and the line the literal sits on, relative to the repository root, in
the scaffold's form. A row read from two literals (an intermediate enumeration) cites both:
`at: "src/Feed/MarketMap.cs:19, src/Feed/Vocabulary.cs:7"`. An interpreted row carries no
`at:`; its `evidence` names the code instead:

```yaml
  - key: {marketType: 2, resultType: 1, interval: 18, subInterval: 0}
    status: proposed
    target: {id: "Total. 1-st half x", param: line}
    value: {from: "marketValue[0]", rule: passthrough}
    candidates:
      - {id: "Total. 1-st half x", confidence: high,
         evidence: "src/Feed/MarketMap.cs:24-27 computes the half from interval - 17 and appends it to the total name"}
```

## Bindings

Bindings are the one new artefact: per discipline and channel, the existing entry point
that realises the mapping, the failure value, the policy site and a digest of the
resolver file as read. Discovery writes them `status: proposed`, the developer confirms
by edit, and generation mode reads them as one of its inputs. Discovery also proposes
planned bindings: for each in-scope discipline the code does not yet realise on a channel
the repository binds, and for each in-scope discipline on a channel no discipline is bound
for, with a planned `policy_site`. File and format: `references/catalog/01-scope.md`,
*Bindings*.

## The first run

The snapshot taken at discovery is the digest baseline: drift before adoption cannot be
measured. Entries the code handles that the current catalog does not publish are
reported under `unpublished`, not failed by the reverse-strict rule, on this run only
(`references/catalog/02-snapshot.md`, *The first run after discovery*).

## What discovery reports

A default branch or a runtime table is never held for a later turn. When the batching
rule in `references/mapping-mode/00-questions.md` (at most eight questions in a block) would hold
questions back, the default branch and runtime table questions fill the block first, past
eight if they alone need it, and the others wait.

Discovery ends its turn with this block, whatever it found, and puts every default branch
and every runtime table to the developer as `beter-questions` in the same turn, `about:`
anchored `default branch at <path>:<line>` and `runtime table at <path>:<line>`:

```beter-discovery
version: 1
consumer:
  files: [src/Feed/TradingConsumer.cs, src/Feed/MarketMap.cs]
  signals: ["src/Feed/FeedKey.cs:3 carries marketType, resultType, interval, subInterval"]
scope:
  - {sport: 6, channels: [trading], evidence: "src/Feed/TradingConsumer.cs:14"}
rows: {direct: 4, proposed: 1}
unread:
  - {at: "src/Feed/MarketMap.cs:30", what: "alternative markets loaded from config/alternative-markets.json at first use", question: q3}
defaults:
  - {at: "src/Feed/MarketMap.cs:33", question: q2}
unpublished:
  - {marketType: 99, at: "src/Feed/MarketMap.cs:22"}
bindings:
  - {sport: 6, channel: markets, resolver: "src/Feed/MarketMap.cs#Resolve"}
  # planned: no code resolves the sport id yet, so the row names the file to create
  - {sport: 6, channel: sports, resolver: "src/Feed/SportMap.cs#Resolve"}
status: proposed
```

The comment is a planned row's marker: discovery rows carry no digest, so nothing else in
the block tells a planned row from an existing one.

`status` is `proposed` until the developer has confirmed scope, rows and bindings, and
`declined` where the permission was refused. Mapping mode continues at Step 2 with the
scope this block names.
