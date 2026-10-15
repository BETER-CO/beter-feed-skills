# The mapping specification: proposals, compositions, scaffolds and qualifiers

Part of `references/spec-schema.md`, which lists every part and when to read it.

*Composing through another feed's integration*, named below, is in
`references/mapping-mode/03-other-feed.md`.

## Proposal fields

A row the skill proposed rather than read carries three extra fields, and generation
stops while any of them is still marked:

```yaml
  - key: {marketType: 5, resultType: 6, interval: 1, subInterval: 0}
    status: proposed
    target: {id: TOTAL_GAMES}
    candidates:
      - {id: TOTAL_GAMES,  confidence: high, evidence: "result type is games, and the target's own description says games"}
      - {id: TOTAL_POINTS, confidence: low,  evidence: "shares the word total and nothing else"}
    chosen_because: "TOTAL_POINTS is scoped to points in the target's own description"
```

`status` carries two values, and a row may carry neither.

| State | Meaning |
|---|---|
| `status: proposed` | This skill proposed the row. Generation stops on it. |
| `status: confirmed` | A developer read the row and accepted it. Generation proceeds. |
| No `status` | The row was never proposed — read from a mapping you already had, in your own hand. |

A row this skill writes from your answer is not a row you wrote. A `skip` transcribed from
a dash in your sheet once you have said what the dash means, a `skip` written because you
ruled a market out in reply to a question, or a target you named when asked: each is
`status: proposed`, with your answer as its evidence. Transcribing is not reading, and the
row is put to you in the review like any other proposal, so that what was heard can be
checked against what was meant. A row discovery read from a literal in your code is the
exception: it carries no `status`, whatever the source of its target
(`references/discovery.md`), and no answer removes it: you take it out, or correct it, at
confirmation.
An answer of yours that disowns the target your literal gives adds nothing to the row: the
question stays in the `beter-questions` block and the row stays as your code has it.
Nor does this skill write a field your code does not give and it proposes itself, such as
an outcome map from the catalog or your vocabulary, on such a row: it asks you, and the
row stays as your code has it until you answer.

Absence and `confirmed` are not the same fact. Once a `proposed` line is deleted, a row a
developer reviewed is indistinguishable from a row nobody ever put to them, and a
specification is re-read by people who were not in the exchange. A `confirmed` row keeps the
`candidates` and `chosen_because` it was proposed on: the evidence is what makes the
acceptance reviewable later.

| Field | Rule |
|---|---|
| `candidates` | Required whenever `status` is present. Every candidate considered, each with `confidence` and `evidence` |
| `chosen_because` | Required whenever there are two or more candidates |

The schema enforces the last two.

A candidate may also name where it came from, which is what lets a reviewer check the
proposal rather than trust it:

| Candidate field | Rule |
|---|---|
| `source` | `target_catalog`, `beter_docs` or `other_integration` — this system's own enumeration and the code handling it, the feed's documented description, or a mapping this repository already holds from another provider's feed |
| `integration` | Required when `source` is `other_integration`, and refused otherwise. Names the integration the analogy was drawn from |

A proposal drawn from another provider's integration is the strongest of the three and
the easiest to get wrong: another provider's market can carry a scope that looks identical
and is not. Naming the integration is what makes that checkable.

**The proposal fields belong to a row that names a target**, so they appear on a leaf row
or on a rule inside a nested parent, never on the parent itself. A parent has no target of
its own; a candidate list on it would be a shortlist for a choice nobody is making, and
confirming it would confirm nothing. The schema refuses them there. A proposal accepted without being read is
indistinguishable from an inference, so accepting one is an edit rather than a silence.

An ambiguous row keeps its candidates after confirmation. The next person to read it
needs to know the decision was contested.

## Composed rows

Where a row was derived through another feed's integration rather than read directly, it
names both hops and stays marked. A row whose chosen target rests on a candidate with
`source: other_integration` is such a row, whether the other integration is a scaffold or
a mapping this repository holds. The schema leaves `composed` optional, so validation
never catches its absence:

```yaml
  - key: {marketType: 6, resultType: 6, interval: 1, subInterval: 0}
    status: proposed
    target: {id: CORRECT_SCORE}
    candidates:
      - {id: CORRECT_SCORE, confidence: medium, evidence: "other-feed maps this market to its own exact-score entry"}
    chosen_because: "derived through other-feed; the intermediate carries interval and result kind, so nothing was dropped"
    composed:
      through: other-feed
      hops:
        - {from: beter, to: other-feed, source: "documented on both sides"}
        - {from: other-feed, to: target, source: "beter-feed/scaffolds/other-feed.yaml, MarketMap.cs:41"}
```

Exactly two hops. The mark survives confirmation, because a reviewer six months later
needs to know the row was derived rather than read.

## The scaffold

`beter-feed/scaffolds/<feed-name>.yaml`, one file per other feed. Not a specification and
not a mapping this repository owns: it is what another feed's integration was found to map
onto this system's own names, and where each row was read.

```yaml
feed: other-feed
source:
  repository: "../client-otherfeed-integration"
  commit: 4f1c2ab
  read_from: code
  files: ["src/Integrations/OtherFeed/MarketMap.cs"]
key_shape: [market, interval, result_kind]
scope:
  - "pre-match only; live markets are not mapped"
  - "handicap markets are omitted"
rows:
  - key: {market: exact-score, interval: match, result_kind: goals}
    target: {id: CORRECT_SCORE}
    at: "MarketMap.cs:41"
unread:
  - "MarketMap.cs:88-120 builds targets at runtime from configuration; not resolved"
```

`rows` carry facts and nothing inferred: that feed's own key, the name this system uses for
it, and the place the pair was read. `key_shape` is that feed's own key dimensions, and it
is what the arity refusal under *Composing through another feed's integration* is decided
on. `scope` holds the limits the source states or plainly shows, because a row derived
through this file inherits them. `unread` holds what could not be resolved, with its
location — **nothing is guessed into `rows`**.

`commit` is written where the source is a checkout that has one and left out otherwise.
`read_from` is `mapping_file` where the developer had a mapping file and `code` where the
integration's code was read.

The file carries no BETER side and no proposal. The correspondence it supports becomes a
row under `beter-feed/mapping/`, marked `composed`, confirmed like any other row. A
scaffold that cannot be parsed is reported and skipped: composition through it does not
happen, and it is never silently rewritten.

Its schema is `schemas/beter-scaffold.schema.json`, carried inside the skill. No copy is
written into this repository: the file is written and read here and is not part of what
this repository's own pipeline validates.

## Qualifier classes

Some systems identify an outcome partly through a bag of qualifiers — key and value pairs
whose keys vary from market to market. Two classes of qualifier live in that bag and they
behave differently, so the file records them separately:

```yaml
qualifiers:
  identity:
    - key: setnr
      confirmed: true
      values: ["1", "2", "3", "4", "5"]
      note: "the market description lookup is keyed on it; two outcomes differ only in it; confirmed by the developer in q1"
    - key: variant
      confirmed: false
      note: "appears on three markets, never changes the outcome set; asked, not yet answered"
  context:
    - key: presenter
      note: "carries who is showing the market; two outcomes never differ only in it"
  entity_references:
    - market: 340
      resolves_to: competitor
      note: "the outcome identifier is a competitor reference, not a member of a fixed set"
    - market: 512
      resolves_to: player
    - resolves_to: player
      note: "this system's 'man of the match' term; no BETER market type corresponds to it"
```

An **identity** qualifier participates in identifying the outcome, so it belongs in the key
and travels into `target.qualifiers` on the rows that use it:

```yaml
  - key: {marketType: 1, resultType: 6, interval: 2, subInterval: 0}
    target: {id: SET_WINNER, qualifiers: {setnr: "1"}}
```

A **context** qualifier carries information about an outcome that is already identified.
Mapping one into the key **produces rows that never match**: the generated resolver builds a
key that includes it and the feed produces a key that does not, so every message for that
market falls through to the unmapped policy. That is why the two classes are recorded rather
than merged — the distinction is invisible in a bag and decisive in a key.

An **entity reference** is an outcome identifier that resolves against **a competitor or a
player rather than a member of an enumeration**. Those outcomes are not enumerable at
specification time, so they are recorded here and their rows map the *market* while the
outcome resolves at runtime against whichever entity the message names.

`market` holds BETER's market type, the integer a market row's `key.marketType` carries, and
never this system's own term identifier, even one that looks like a number. An entity
reference on a term that corresponds to no BETER market type is one entry per term, carrying
`resolves_to` and no `market`, with a `note` that names the term; where a market type
exists, in scope or not, `market` is written.

The block is recorded whole: every qualifier key and every entity reference found,
including one on a term that maps to nothing currently in scope.
`references/mapping-mode/04-conflicts-qualifiers.md`, *Record the two classes separately*, says why.

`confirmed` is required on every identity entry, and `confirmed: false` means the class is
still open. Every row using such a key stays `status: proposed`, and step 6 **generates
nothing** for it — a key nobody confirmed is a key nobody has agreed is part of an identity.

`confirmed: true` is the developer's word, never this skill's inference. The skill writes
every identity entry `confirmed: false` and asks; the developer confirms it in an answer,
or in their final review of the files, and only then is it written `true`. A key the lookup
code is plainly keyed on is a finding to report, and a question to put — not a confirmation.

The skill proposes the class from what the lookup code and the vocabulary show, and the
developer's answer is what moves it. A key the developer will not settle stays in the class
proposed for it: an identity key waits as `confirmed: false`, a context key keeps its
`context` entry, and its open state lives in the entry's `note` and in the still-open
question, since a context entry has no `confirmed`. While the developer has not spoken,
`identity` with `confirmed: false` is not the home of a key the evidence shows as context.
When the developer names the other class, write that class (identity with `confirmed: true`,
or a `context` entry) and record in the `note` the evidence that pointed the other way. A
key with no class evidence, or evidence for both classes, waits as `identity`,
`confirmed: false`, and is asked about.

**The schema checks** the block's shape, that `resolves_to` is `competitor` or `player`,
and that every key in a row's `target.qualifiers` appears in `qualifiers.identity`.
**Generation checks** the rest: that no `confirmed: false` key reaches emitted code, and
that no context key was smuggled in through a row.
