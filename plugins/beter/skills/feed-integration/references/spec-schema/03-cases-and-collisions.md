# The mapping specification: cases, flatter targets and collisions

Part of `references/spec-schema.md`, which lists every part and when to read it.

### The `cases` block

Three of the named generator cases (`references/generation-contract/01-detect.md`, *Named generator
cases*) rest on what your integration does with the incident stream, which no row and no
catalog entry states: whether it re-orders incidents by index, whether it folds retractions
into state or records them as events, and whether it holds at match level a value the feed
carries per incident. An incidents file declares them once, at the top level:

```yaml
cases:
  emission_order: {applies: false, why: "the consumer sorts by index itself"}
  undo_chain:     {applies: true}
  level_shift:    {applies: true, rows: [{type: 1012}], field: set_score}
```

Each of the three is declared. `applies: false` carries a `why`. An applicable
`level_shift` names the rows it folds, by their keys, and the match-level field they fold
into. Generation reads the block and never infers it: a case the block does not carry is a
gap in the specification, reported as one, and generation stops there. The other two named
cases need no declaration — `sign_convention` is the `negate` rule on the row that carries
it, and `source_switch` follows from the source bands the catalog snapshot records.

### Targets flatter than the feed

Where the target carries fewer dimensions than the feed — a market and a choice, with
period and result kind implied — the forward direction drops information. The file
declares how those dimensions are recovered:

```yaml
inference:
  interval:
    from: target.id
    rule: prefix_table
    table: {S1_: 2, S2_: 3, M_: 1}
    default: 1
  resultType:
    from: target.id
    rule: constant
    value: 6
```

Rules are `prefix_table`, `suffix_table`, `regex_table` and `constant`. The inference
rule is tested against enumerated cases rather than against the row set, because it is
the part of the mapping that no row states.

### Collisions

Dropping dimensions means two distinct feed keys can reach the same target key. This
system then cannot represent the difference, which is a defect in the specification
rather than in the generated code. **Generation fails on an undeclared collision.**
Where a collision is intended, the file says so and says how the two merge:

```yaml
  - key: {marketType: 3, resultType: 6, interval: 1, subInterval: 0}
    target: {id: TOTAL, param: line}
    merge:
      with: [{marketType: 3, resultType: 6, interval: 1, subInterval: 1}]
      rule: first_wins
```

`rule` is `first_wins`, `last_wins` or `declared_order`. This check replaces the
round-trip assertion for flat targets, where a round trip cannot succeed by
construction.

A key listed under `merge.with` is an effective key. A message arriving under it has to
resolve, so the projection carries a row of its own for it — the declaring row's target,
the outcome map it resolves by and its `merge`, and the path `...merge.with[n]` as where it
came from — and it takes its place in precedence like any other row. A `with` key that
collides with another row's effective key is visible only because it is projected.

`merge` is declared on market rows only, where a target settles and the reverse lookup
has to name one feed key. Several stages reaching one target state is not a collision: a
stage row states scoreboard state, nothing settles on it, and a target vocabulary coarser
than the feed's is the ordinary case. Write one plain row per feed stage, without
`merge`; the schema rejects it on a stage row.

Two stage rows naming one `state` label name one `states` entry, so they agree field for
field by construction.

Outcomes collide only inside their market. Two codes in one market's map reaching one
selection fail generation, and there is no `merge` to declare it: an outcome is the
affirmative or negative of the market that carries it, and two of them settling on one
selection is a modelling error rather than a merge. The same selection under two
different markets is not a collision at all — the market key is part of the outcome's
identity.

### `comment`

A row carries an optional free-text `comment`. It is not a note to a future reader; it
instructs the agent doing the mapping, and generation must honour it or say why it did
not — a comment silently dropped is indistinguishable from one never read. A condition
attached to a mapping is written here as prose, `comment: "only when the discipline
plays a golden set"`, and never as an expression language: the schema does not define
one, and generation does not evaluate one.
