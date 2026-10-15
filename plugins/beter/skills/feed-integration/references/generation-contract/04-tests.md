# Generation contract: correctness classes, policies and the coverage check

Part of `references/generation-contract.md`, which lists every part and when to read it.

The collision gate and the `emission_order` named case, both named below, are in
`references/generation-contract/01-detect.md`.

## Correctness is defined per class

Not as one assertion. **A round trip is meaningful only where the mapping is injective, which is a minority of the mappings this skill produces**: incidents expand, declared absences have no
counterpart, and a target flatter than the feed discards dimensions by construction. A
generated suite built on one round-trip assertion would pass on the mappings that cannot
go wrong and be silently inapplicable on the ones that can.

Nine classes. Each is its own generated test.

| Class | Applies to | The generated test asserts |
|---|---|---|
| `forward_totality` | every row | Every key in the specification resolves to exactly one decision, and generation is deterministic across runs |
| `injectivity` | targets of equal or greater arity | No two feed keys reach one target key unless a `merge` rule declares it |
| `expansion` | `many` rows | The declared set is produced exactly, as a set |
| `inference` | flatter targets | The recovery rule holds over enumerated cases |
| `carriage` | incident `params` blocks | Every parameter of a mapped type reaches its named target field or is dropped with a reason; scores parse against the result type code the block names; an absent or empty parameter is tolerated where the feed documents one |
| `absence` | `skip` rows | No output and no error, and the reason is present |
| `unmapped` | keys absent from the specification | The declared failure policy fires |
| `parametric` | `value` rules | Properties hold over a generated range of lines |
| `assignment` | `stages` rows of a specification carrying `states` | Every mapped stage produces the assignment its state declares, over exactly the fields the `states` table carries; two stage keys naming one state are accepted and need no merge rule; one stage key reaching two states is a collision |

**All nine. A class with no test is not a class that did not apply** — it is a class
nobody looked at. Where a specification genuinely carries no row of a class, the class is
declared inapplicable **with the reason**, in the `beter-generation` block, as
`applicable: false` and a `why`. A silently absent class is a generation defect and it is
scored as one.

Every behavioural assertion drives production code through the resolver's public entry,
or through the boundary's where this contract drives the test through the boundary. The
table-order half of `forward_totality` reads the emitted table itself and is exempt. A test
that asserts only on its own fixture is not written: it passes whatever the resolver does.
Nor is a test that repeats another generated test's assertion and covers no additional
class.

### forward_totality

Enumerate every key the specification carries. Assert each resolves, and that the
decision is one of the four outcomes. Assert nothing about which one — that is the other
classes' work; this one asserts the resolver is total and single-valued over its own
input.

Determinism belongs to the same property and is asserted here. The generated test cannot
run the generator, so what it asserts instead is the invariant that makes determinism
observable: the emitted table is in ascending key order and holds no duplicate key. A
table out of order is a generator that has stopped sorting, and that is what a spurious
diff looks like before anybody sees the diff.

### injectivity

Asserted **only where the target carries equal or greater arity** than the feed key. A
target with a market dimension and a choice dimension, against a feed key with four, is
flatter by construction; asserting injectivity on it would fail on every correct mapping.

Where it applies: collect the target key of every row, and assert no two feed keys reach
one target key unless a `merge` block names them. Where it does not apply, the class is
declared inapplicable with the reason, and the collision gate below stands in its place.

Outcomes are asserted per market: within one market's map, no two codes reach one
selection. Across markets nothing is asserted — the market key is part of the target's
identity.

Incidents are never in this class. They expand, so the incident channel declares
`injectivity` inapplicable and carries `expansion` instead — which is why the
specification schema puts no `merge` on an incident row.

### expansion

For each `many` row, assert the declared set is **produced exactly, as a set** — every
declared target present, nothing else present, no duplicates. Compare as sets.

**Order is asserted only where the specification declares it.** The specification declares
order in exactly one place: a `merge` rule of `declared_order`. Nowhere else. So the
expansion test compares sets and asserts nothing about sequence, and a generated test that
asserts the order of a `many` list is over-specified — it fails the first time somebody
reorders two lines that mean the same thing.

The order in which the consumer *emits* incidents within a match is a different question,
and it is the `emission_order` named case below.

### inference

Where the target is flatter than the feed, the dropped dimensions are recovered by the
`inference` block:

```yaml
inference:
  interval:
    from: target.id
    rule: prefix_table
    table: {H1_: 18, H2_: 19, M_: 1}
    default: 1
```

The recovery rule is **asserted over enumerated cases, not over the row set**. That is the
point of the class. Asserting it over the rows proves only that the table agrees with the
rows it was derived from, which it does by construction. The generated test enumerates
cases the rows do not cover: each table entry; a target id matching no entry, taking the
`default` or resolving unmapped where there is none; a target id matching two prefixes,
where the longest wins; an empty target id; and a target id whose prefix appears in the
middle rather than at the start.

This is the part of the mapping that **no row states**, and therefore the part where a
wrong reading survives review.

### carriage

For each incident type the specification maps, every parameter the catalog declares for
it is **accounted for**: carried into the field named by `to`, or dropped with a reason.
The test enumerates the catalog's parameter keys for the type rather than the block's own
keys — reading the block to decide what the block should contain proves nothing, and an unaccounted parameter is the one failure this class exists to catch.

Three more assertions on top of the accounting. A `score_pair` parses `"P1:P2"` into the
two sides' counts and a `score_series` parses a run of them, both against the **integer
result-type code** the entry names; a test that hard-codes what is being counted would
pass on a discipline whose table says something else. A `clock` parses `"MM:SS"` into
elapsed time. And an absent `PeriodScore` and an empty `Winner` are tolerated and do not
fail the incident — the feed documents both, so treating either as a fault would close
matches in production on a message the feed says is normal.

### absence

For each `skip` row: **no output and no error, and the reason is present**. Three
assertions, all needed. No output, so a skipped market never reaches this system. No
error, so a skip is not the unmapped path wearing a different name. And the reason is
carried on the decision and asserted non-empty, because a skip whose reason was dropped in
generation is indistinguishable in production from an oversight.

On the timetable channel the same three assertions apply to the sport row, plus a fourth:
a skipped sport never reaches that sport's market resolver. A skip that stops the match
being landed and still runs the market path is a skip in the file and not in the code.

### unmapped

A key the specification does not contain resolves to the unmapped decision, carrying that
key, and the declared policy fires at the boundary. One test per policy — below.

On the timetable channel this carries one further assertion: an unmapped sport reaches no
resolver of that sport at all. The policy fires at the boundary and the message stops
there.

### parametric

Property tests over a generated range of lines, **including negative, zero and fractional**. The range is enumerated in the test from a fixed seed, because the generated
code takes no property-testing library, and seeded because a failure has to be
reproducible from the test file alone.

| Rule | Property asserted |
|---|---|
| `passthrough` | the parameter reaching the target equals the market or outcome value, for every line in the range |
| `negate` | the parameter equals the negated value; negating twice returns the original; zero maps to zero rather than to negative zero where the language distinguishes them |
| `scale` | the parameter equals the value times `factor`, compared exactly on values chosen to be representable rather than with a tolerance |
| `offset` | the parameter equals the value plus `by` |
| `lookup` | every table key maps to its value, and a value absent from the table is unmapped rather than defaulted |

The range covers at minimum `-4.5, -2.5, -1, -0.5, 0, 0.5, 1, 2.5, 4.5`. The catalog
carries no value range for a market, so the test adds no endpoint beyond that minimum and
invents none. Fractional lines are where a mapping that rounds silently is caught; negative
lines are where a sign convention running the other way is caught.

### assignment

The scoreboard channel's target is not an identifier. It is a **record** — a small set of
named fields the specification's `states` table declares, such as whether the match has
started, whether it has ended, whether a period is open, and which period number is
current — and a `stages` row answers with an assignment over those fields rather than with
a term the client already has a name for. Every other class in this list scores a mapping
onto a vocabulary; this one scores a mapping onto a shape.

Three assertions.

**The assignment covers exactly the fields the `states` table carries.** The record's
fields are the keys of the `states` entries, every entry carries the same set, and the
generated code assigns each of them by name for every mapped stage — the values the
stage's state declares, and no field outside the table. A partial assignment is the
failure this class exists to catch: a record with one field left at its zero value is a
state the consumer will read and act on, and nothing about it looks wrong. A table whose
entries disagree about the field set fails generation before anything is written.

**Two stage keys reaching one assignment are accepted.** This is the one place where the
collision gate does not apply, and the exception is deliberate. A stage key is
`{stage, interval?}`, so the same phase of a match is reachable by more than one key — a
stage qualified by an interval and the same stage unqualified — and a client record
coarser than the feed's stage list has fewer states than there are stages by construction.
Reporting that as a collision would fail every correct scoreboard mapping. What is
asserted instead is that the assignment is the same one: two keys naming the same state
name one `states` entry, so they agree field for field by construction, and two keys
reaching **different** assignments for the same stage are a collision and fail generation
as any other would.

**An unmapped stage is the unmapped decision, not a default assignment.** A stage the
specification does not carry resolves to unmapped and the declared policy fires. A
generator that fell back to the all-false record would publish "not started" over a match
in play, and the consumer has no way to tell that from the real thing.

Incidents and markets are never in this class. It applies exactly when the specification
carries a `states` table: a scoreboard specification whose stage rows name identifiers
(`target: {id: ...}`) is scored by the classes every identifier mapping is scored by, and
declares this one inapplicable with the reason, like any other class.

## Failure policies

`policy.on_unmapped` declares one of three. Each is proven by its own generated test, and
in every one **a second, unrelated match is asserted to keep flowing** through the same
boundary in the same test.

| Policy | The generated test asserts |
|---|---|
| `close_match` | The match carrying the unmapped key is closed and nothing further from it is accepted; a second match is unaffected and its later messages still resolve |
| `drop_market` | The affected market produces no output; other markets in the same match still produce theirs; the match is not closed |
| `alert_only` | The event is recorded and raised, and the record carries the key that failed; nothing is suppressed — the same match's other markets and the market itself continue |

A policy test that exercises one match proves the policy fired. It does not prove the
blast radius, and the blast radius is the whole reason the policy is declared per
specification rather than fixed. Two matches, always.

## The generated coverage check

A check runnable in **this repository's own CI**, alongside the generated tests and with
the same runner. It is generated code and it is committed, so CI runs it the way it runs
any other test — no agent, no network, no token cost, and nothing to invoke. **Never wire
this skill itself into a pipeline.** It runs when a developer invokes it; a pipeline that
called an agent after every code fix would spend a developer's attention and a model's
tokens on runs where nothing it reads has changed.

It emits the same `beter-coverage` block the skill emits, from constants written at
generation time: the three figures, the per-discipline breakdown, and the eight sections.
It fails when `status` is `fail` — that is, when `orphan_rows` or `out_of_scope_rows` is
non-zero. Undecided entries never fail it: they are work outstanding, and a build that
goes red because a mapping is unfinished is a build whose coverage check gets deleted.

The constants are a restatement of what generation computed, not a recomputation — the
generated code takes no YAML parser, so it cannot re-read the specification and the
snapshot. What makes the restatement trustworthy is the catalog digest test beside it. If
the snapshot moves, the digest test fails, and the restated figures are known to be stale
in the same CI run. The recomputing coverage report is the skill's, and it runs at step 5.
