# The mapping specification: file, keys and rows

Part of `references/spec-schema.md`, which lists every part and when to read it.

*Qualifier classes*, named below, is in `references/spec-schema/04-proposals-and-evidence.md`.

## The schema, and the copy in this repository

The schema is carried inside the skill and validation runs in the agent, so a
specification is checked whether or not anything else is set up.

The skill also writes a copy to `beter-feed/schema/beter-mapping-spec.schema.json` and
refreshes that copy on every skill update. Specification files reference **that copy**:

```yaml
$schema: ../schema/beter-mapping-spec.schema.json
```

The copy is what gives the repository's own pipeline the same check the agent runs, and
what gives an editor completion while a specification is edited by hand. Derivatives —
a narrower schema, a lint rule, a type definition — are generated from it rather than
maintained beside it.

It is JSON Schema draft 2020-12. The draft matters: the row definitions compose a shared
block of proposal fields with per-channel key and target rules, and `unevaluatedProperties`
is what lets that composition still reject a misspelled key.

## Key model

| Channel group | Row key | Parameters |
|---|---|---|
| Trading — markets | sport, market type, result type, interval, sub-interval | market value |
| Trading — outcomes | the market's key, then outcome type | outcome value |
| Scoreboard | sport, stage, interval where the stage carries one | — |
| Incidents | sport, incident type, optional constraint on a side-valued parameter | parameter values, carried by generated rules |

The sport is stated once at the top of the file, not repeated per row.

**A market key that omits `subInterval` names the sub-interval `0` row.** The feed's
sub-interval is not nullable and `0` is its default, so `{marketType: 2, resultType: 1,
interval: 1}` and the same key with `subInterval: 0` are one row, not two. A reader accepts
either form. Wherever a row is named outside the file — a Step 6 stop, a confirmation —
name it in the form the file writes it, so the developer finds the row by searching for
what they were shown. A sub-interval other than `0` is always written out.

**An outcome is answered inside the market that gives it meaning.** BETER's outcome type
is one enumeration for the whole feed, and a market type lists which of its codes may
appear under it; what the same code means in *your* system depends on the market — under
one term `1` is the home side, under another it is the first player. So a market row
carries its outcomes as a map from outcome type code to your selection identifier, and
there is no outcome row: an outcome's identity is the market's key plus its own code.

**Every feed enumeration value is the integer code, never the name.** Market type, result
type, interval, sub-interval, outcome type, stage, incident type and the result type a
score parameter counts are all codes. A name can be corrected — a typo fixed, a wording
improved — without the entity it names changing, so a row keyed on the name stops matching
after an edit that was meant to change nothing, and it stops matching silently. Names
belong in a `comment`, in a log line and in a proposal's `evidence`, where a reader needs
them and nothing resolves against them. The exception is the parameter names on an
incident — `Participant`, `MatchScore` and the rest are keys the feed's parameter list
defines and there are no codes for them.

**Market value and outcome value are parameters, not key dimensions.** They carry
handicap and total lines, so the space they range over is unbounded. A specification
that enumerated one row per market identifier could not express totals or handicaps at
all. Rows key on the type dimensions; values travel by rule.

**Only one field per key is a mandatory anchor; the rest narrow it.** `marketType`
anchors a market row, `stage` anchors a scoreboard row, and `type` anchors an incident
row. A row keyed on the anchor alone is a **general rule** — it matches every value of
the fields it leaves out — and it is the first form put to a developer, widened with more
key fields only after they say the general shape is right:

```yaml
markets:
  - key: {marketType: 1}
    target: {id: MATCH_WINNER}
```

Duplicate rows and rows whose key ranges overlap without either being a strict
narrowing of the other are not a schema error. The coverage report is what surfaces
them, alongside catalog entries that carry no row at all — a key caught mid-way between
a general rule and a specific one is a real, reportable state, not a malformed file.

## File header

```yaml
$schema: ../schema/beter-mapping-spec.schema.json
version: 1
sport: 2
channel: trading                # trading | scoreboard | incidents | timetable
catalog:
  snapshot: ../catalog/meta.yaml
policy:
  on_unmapped: close_match      # close_match | drop_market | alert_only
```

A file for a target that identifies outcomes through a bag of qualifiers carries one more
top-level key beside these, `qualifiers`. See *Qualifier classes* below for the block;
`references/mapping-mode/04-conflicts-qualifiers.md` says when it is written.

`catalog.snapshot` names the catalog's `meta.yaml`, never a per-discipline enumeration
file. That file is the snapshot's identity — when it was taken and from which pages — so a
specification, and the code built from it, record which catalog they were written against.

`channel` decides which row lists the file may carry: `trading` takes `markets`, and
each market row carries its `outcomes`; `scoreboard` takes `stages`, `incidents` takes
`incidents`, `timetable` takes `sports`. A file carrying a list from another channel is
rejected — it means two channel groups have been merged into one file and the generated
resolvers would have to guess which key model applies.

On the `timetable` channel `policy.on_unmapped` is `close_match` or `alert_only` only.
`drop_market` is rejected by the schema for this channel: there is no market to drop at
sport level.

`policy.on_unmapped` is what the generated code does when the feed sends a key this file
does not contain:

| Policy | Effect |
|---|---|
| `close_match` | The match is closed in this system; nothing further from it is trusted |
| `drop_market` | The affected market is dropped; the rest of the match continues |
| `alert_only` | The event is recorded and raised; nothing is suppressed |

Failure is a value, not an exception. An unmapped identifier sets a flag on the affected
match; matches that are unaffected keep flowing. Each declared policy is proven by a
generated test.

## Row shape

Each row states its key and one of five targets.

```yaml
markets:
  # one — the plain case; the outcomes are answered on the row
  - key: {marketType: 1, resultType: 6, interval: 1, subInterval: 0}
    target: {id: MATCH_WINNER}
    outcomes: {1: HOME, 2: AWAY, 3: DRAW}

  # parametric: the line travels, the row does not enumerate it
  - key: {marketType: 3, resultType: 6, interval: 1, subInterval: 0}
    value: {from: "marketValue[0]", rule: passthrough}
    target: {id: TOTAL_POINTS, param: line}

  # parametric with a sign convention the target does not share
  - key: {marketType: 4, resultType: 6, interval: 2, subInterval: 0}
    value: {from: "marketValue[0]", rule: negate}
    target: {id: HANDICAP_SET, param: line}

  # skip — a declared absence
  - key: {marketType: 9, resultType: 6, interval: 1, subInterval: 0}
    target: {skip: true, reason: "not offered on our site"}

incidents:
  # conditional key — the same type resolves differently by parameter
  - key: {type: 1001, params: {Participant: "1"}}
    target: {id: HOME_POINT}
  - key: {type: 1001, params: {Participant: "2"}}
    target: {id: AWAY_POINT}

  # many — one-to-many expansion
  - key: {type: 4}
    target:
      many:
        - {id: SET_END}
        - {id: SCORE_SYNC}

# a scoreboard file whose target is a record, not an enumeration
states:
  P1-OPEN:   {started: true, ended: false, open_period: true,  period_number: 1}
  P1-CLOSED: {started: true, ended: false, open_period: false, period_number: 1}

stages:
  - key: {stage: 21, interval: 18}
    target: {state: P1-OPEN}
  - key: {stage: 9, interval: 18}
    target: {state: P1-CLOSED}
```

A row read from this repository's own integration code carries `at:`, the file and line
the literal sits on, relative to the repository root and in the form the scaffold uses,
`at: "src/Feed/MarketMap.cs:19"`. It is the row's citation, not its evidence: a row with
`at:` was read, carries no `status`, and is the developer's declaration exactly as a row
imported from their sheet is. A row this skill interpreted from code carries no `at:`;
its `candidates[].evidence` names the code instead (`references/discovery.md`).

## What the schema does not check

A specification can be schema-valid and wrong. These are checked elsewhere, and the
places are named so that nobody assumes validation covered them:

| Not checked by the schema | Checked by |
|---|---|
| A key that does not exist in the catalog snapshot — an orphan row | The coverage report, `references/catalog/03-coverage.md`. Fails |
| A row for a discipline that is not in scope | The coverage report. Fails |
| A catalog entry with no row and no skip — an absence | The coverage report, as undecided |
| Two rows reaching the same target without a `merge` | Generation, `references/generation-contract/01-detect.md`. Fails |
| Whether a target identifier exists in this system's own vocabulary | Generation, against the vocabulary declared in `scope.yaml` |
| A `states` entry whose field set differs from the other entries' | Validation, by reading (`references/mapping-mode/05-validate-to-report.md`, step 4), and again at generation. Fails |
| A `target.state` that is not a key of `states` | Validation, by reading, and again at generation. Fails |
| A scoreboard file mixing `state` and `id` on its stage rows, a file using `state` with no `states` table, or a `states` table in a file whose rows use `id` | Validation, by reading, and again at generation. Fails |
| An incidents file with no `cases` block, or a block that leaves out one of its three cases | Generation, `references/generation-contract/01-detect.md`: reported as a gap in the specification, and nothing is generated |
| Whether the mapping is *right* | A person, in review. That is the whole point of the format |
| A `timetable` row whose `key.sport` is not the file's own `sport` | Not expressible in draft 2020-12. The one-row rule and the file's own header are what the reader checks; nothing checks it automatically |
| That `at:` names a line that exists, or a literal that says what the row says | Discovery cites what it read; generation's tests prove it, and a failing test is settled by the binding's digest (`references/generation-contract/03-emission.md`, *Adopting existing code*) |
