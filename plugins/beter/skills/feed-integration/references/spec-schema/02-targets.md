# The mapping specification: targets and values

Part of `references/spec-schema.md`, which lists every part and when to read it.

*Proposal fields*, named below, is in `references/spec-schema/04-proposals-and-evidence.md`.

### The five target forms

| Form | Written as | Means |
|---|---|---|
| **one** | `target: {id: X}` | Exactly one target, optionally carrying a parameter |
| **many** | `target: {many: [...]}` | The declared set is produced, exactly. Incidents only |
| **state** | `target: {state: <label>}` | The assignment the file's `states` table declares under that label. Stage rows only |
| **skip** | `target: {skip: true, reason: "..."}` | Deliberately not carried. The reason is mandatory |
| **absence** | no row for that key | **Not a target.** It triggers `policy.on_unmapped` |

`skip` requires a reason so that a deliberate omission is distinguishable, in review,
from an oversight. Absence is the fifth form and the schema cannot express it — there
is nothing on disk for a schema to look at. That is what the undecided section of the
coverage report is for, and it is why a skip counts as decided and an absence does not.

`many` is available on incident rows only. Markets and stages that fan out are
a modelling error rather than an expansion: scoreboard stages are one-to-one, and a
market reaching two targets is a collision, which is declared with `merge`.

`state` is for a target that carries no enumeration to pick from. Some systems do not name
their match states at all; they hold a record — started, ended, whether a period is open,
which period — and a state is one assignment over its fields. There is no identifier to
choose, so a top-level `states` table gives each state a label and its full assignment,
once, and a stage row names the label. The label belongs to the file; nothing in your
system has to carry it. The assignment does not: it is the vocabulary's own for that
stage, written out, not one the file invents. Generation reads the
specification and the repository, so the table is the one place the record reaches the
generated code.

Four rules hold the table together:

- The record's fields are the keys of the `states` entries. Every entry carries the same
  field set; an entry with a field missing, or a field of its own, is rejected.
- Every `target.state` on a stage row is a key of `states`. An entry no row names is
  allowed: a record can hold states this feed never reaches.
- A scoreboard file uses `state` or `id` on its stage rows, never both. A system that does
  name its match states keeps `target: {id: ...}` and carries no `states` table.
- `states` is required exactly when stage rows use `state`.

`outcomes` is optional on a market row: a skipped market has none to answer, and a market
whose outcomes are not yet settled is written without the map and listed by the coverage
report as undecided on its outcomes. A map, once written, names every outcome the market
carries in your system; a code the catalog lists under the market type and the map does
not name is undecided, and a code deliberately not carried is named in the row's
`comment`. The value is your selection identifier as a string; the code is the integer,
written bare. Where the outcome carries a value — a correct score arrives as the outcome
value — the entry is written the way a parametric market row is, `{id, param, value}`
with `value.from` naming `outcomeValue[0]`.

### The sport row

The `timetable` channel carries one list, `sports`, parallel to `markets`, `stages`
and `incidents`. Its key's anchor and only field is `sport`, and **the row's key
must equal the header's `sport`**, so a file carries exactly one row:

```yaml
sports:
  - key: {sport: 6}
    target: {id: e-football}
```

The row states which of this system's own disciplines the feed's sport lands in. It takes
the `one` and `skip` target forms and no others — `many` is an incidents-only expansion,
and a sport landing in two disciplines is a modelling error rather than a fan-out. A
system that keys nothing on sport opts out with the ordinary declared absence:

```yaml
sports:
  - key: {sport: 6}
    target: {skip: true, reason: "our system keys nothing on sport; matches land by league id"}
```

**Opting out is a row, not an absent file.** A file that is absent for an in-scope sport
is the undecided state the coverage report shows, exactly as an absent market row is; it
is not an error at mapping time and it is an error at generation time, because generation
for sport N reads this file first.

Leagues are not part of the row. They are matched at run time by id against this system's
own competition list, and where a rule about that belongs on paper it goes in `comment`.

### The nested form

A row may be a **leaf**, carrying `key` and `target` as shown so far, or a **parent**,
carrying `key` and `rules` instead of a `target`:

```yaml
markets:
  - key: {marketType: 1, resultType: 6}
    rules:
      - key: {interval: 1}
        target: {id: MATCH_WINNER}
      - key: {interval: 2}
        target: {id: S1_WINNER}
```

The parent's `key` is the part every rule underneath it shares. Each rule's own `key`
merges over the parent's: a field the rule states overrides the parent's value for that
field, and a field the rule leaves out is inherited from the parent. A rule's `key` is
therefore optional — a rule with no `key` at all uses exactly the parent's key.

`outcomes` follows the same direction with one difference. A parent's map is the default
for every rule beneath it, and a rule that writes its own `outcomes` **replaces the
parent's map whole** — it is never merged entry by entry, because a rule that changes one
selection and inherits the rest would hide which selections it answered for:

```yaml
markets:
  - key: {marketType: 2, resultType: 6}
    outcomes: {12: OVER, 13: UNDER}
    rules:
      - key: {interval: 1}
        target: {id: TOTAL_GOALS, param: line}
      - key: {interval: 2}
        target: {id: HALF_TOTAL, param: line}
        outcomes: {12: O, 13: U}
```

Nesting is one level deep. A rule inside `rules` carries no `rules` of its own; it is
always a leaf, naming a `target` directly. The schema accepts both the flat form and the
nested one, and does not prefer either: a skill that rewrote a client's file into the
shape it prefers, flattening what they nested or nesting what they kept flat, is a skill
they stop trusting with their file.

A parent carries what its rules share, and that is all it carries. `comment` is
accepted on it; the proposal fields are not — see *Proposal fields* for why.

#### The projection

This file is authoritative and is never modified. Generation and the coverage report do
not read it directly: both read a **normalised projection** of it, one row per effective
key, each row carrying the merge of its parent's key and its own, and the outcome map it
resolves by after inheritance and replacement, in the order the generated code tries
them, with precedence resolved rather than implied. A specification written flat and the
same specification written nested project to the same rows.

The projection matters because an effective key under a parent is computed, so its
specificity is computed too, and precedence — explicit priority first, then specificity,
with a tie on both reported rather than resolved quietly — cannot be read off the nested
source by eye.

Four things hold about it, and the first two are the ones to know:

- **It is generated output.** It is rebuilt from this file on every run and carries the
  same *generated, do not edit* header as the mapping code. An edit made to the projection
  instead of to the specification survives one run and is discarded by the next.
- **Every projected row names its origin here.** A row projected from a nested rule
  carries that rule's path in this file, so an error, a coverage entry or a precedence
  report cites a path you can find in your own file rather than a projection index.
- It is deterministic: the same specification projects to the same rows in the same order.
- Nothing else reads the specification. A check that ran against the source rather than
  the projection would be checking a different set of rows than the code was generated
  from.

### Value rules

`value` says how a market or outcome value is carried into the target's parameter. A row
with a `value` block must name the parameter it feeds, so `target` carries `param`.

| Rule | Extra field | Carries |
|---|---|---|
| `passthrough` | — | The value unchanged |
| `negate` | — | The value with its sign flipped — a handicap convention that runs the other way |
| `scale` | `factor` | The value multiplied |
| `offset` | `by` | The value shifted |
| `lookup` | `table` | The value replaced from a table, for enumerated rather than numeric parameters |
| `score_pair` | `result_type` | A `"P1:P2"` string split into the two sides' counts of the named result |
| `score_series` | `result_type` | A space-separated run of `"P1:P2"` pairs, one per period |
| `clock` | -- | An `"MM:SS"` string carried as elapsed time |

`from` names the source: `marketValue[0]` on a market row, `outcomeValue[0]` on an
outcome entry in a market row's `outcomes` map, `params.<Key>` on an incident row. The
index is there because a value field can carry more than one component.

#### Incident parameter carriage is generated, not authored

An incident row's `params` block is produced from the catalog's `params` for that
incident type, one entry per key, and written into the specification for the developer to
read and override. It is never a question put to them: the answer names a field of their
own incident record, and a target vocabulary enumerates market and incident terms, not
record fields. So the block arrives already filled in, and the developer's edit to it is a
correction rather than an answer.

The block is a map on the row, keyed by the parameter name the feed publishes:

```yaml
incidents:
  - key: {type: 1029}
    target: {id: MATCH_START}
    params:
      MatchScore:  {to: score,  rule: score_pair, result_type: 1}   # 1 is Goal
      MatchMinute: {to: minute, rule: clock}
      Winner:      {to: null,   rule: drop, reason: "not carried on our start event"}
```

| Entry field | Rule |
|---|---|
| `to` | The field of this system's incident record the parameter is carried into. `null` when the parameter is dropped |
| `rule` | Any value rule above, plus `drop` |
| `reason` | Required when `rule` is `drop`, and refused otherwise |
| `result_type` | Required on `score_pair` and `score_series`, refused otherwise, and always the integer code |

The map key is the source, so a carriage entry takes no `from` — that is the one
difference from a `value` block. Every parameter the catalog declares for a mapped type
gets an entry: carried, or dropped with a reason. A parameter with no entry fails
generation, because silence is not a decision.

The block appears on a leaf row or on a rule inside a nested parent — wherever the
`target` it carries into is named.

The score rules need a result type the incident documentation never states. It comes from a
per-sport table, keyed on (sport, parameter key) rather than on sport alone: eFootball
declares one result type, `Goal`, so every score parameter counts goals; table tennis
declares four, and `SetScore` counts Points while `MatchScore` counts Sets. The table lives
in `references/catalog/02-snapshot.md`, under *What a score parameter counts*, authored against the
`result_types` the snapshot carries for that discipline; a discipline whose result types
leave a parameter ambiguous gets a row with no value there, and generation stops on it
rather than counting the wrong thing.

Two feed properties the generated carriage must tolerate rather than treat as faults:
`PeriodScore` may be absent until a period starts, and `Winner` may arrive empty. A key the
catalog declares is not a key every message carries.

A discipline may declare no incident types at all, and generation produces no incident
carriage for it. That is a real product shape rather than a hole to fill: not every
discipline the feed carries publishes incidents, and a snapshot holding none for one is
the extraction reporting what the documentation gives rather than an extraction that came
up short. Declare the channel only where the discipline has one, in `scope.yaml`, and
nothing is extracted, asked or generated for the channels left out.

The four side-valued parameters -- `Participant`, `ActivePlayer`, `Winner`, `Losers` -- are
the exception, and are the only ones that also appear on the key side. Where the client's
own term carries the side, the row narrows on the parameter and fans out one row per value.
That is a mapping decision and is put to the developer.
