# Generation contract: what must exist

Part of `references/generation-contract.md`, which lists every part and when to read it.

The nine correctness classes named below are in `references/generation-contract/04-tests.md`.

## What must exist

| Must exist | Detail |
|---|---|
| **A normalised projection** | The specification flattened to one row per effective key, in resolved precedence order, each row naming its path in the specification file. Everything downstream reads this and not the file |
| **A resolver** | Takes a feed key, returns **exactly one decision**: a target, a set of targets, a declared absence, or unmapped. Where a binding names an existing resolver for the channel, that resolver satisfies this row and is not rewritten; the tests below are driven through it |
| **A sport resolver** | One shared generated unit keyed on `sportId`, one entry per in-scope sport, each entry derived from that sport's timetable file alone. The boundary calls it first for every message carrying a sport |
| **A failure value** | Unmapped is a value the caller receives, not an exception it must catch. It carries the key that failed. Where a binding names `failure`, that value is the one the caller receives |
| **Policy application** | The declared `policy.on_unmapped` applied at the boundary, affecting only the match the failure belongs to |
| **Parameter rules** | Handicap and total lines carried through their declared `value` rule |
| **A test per correctness class** | The nine classes below, all of them, not a subset |
| **A coverage check** | Runnable in this repository's own CI |
| **The bindings kept true** | Where `beter-feed/bindings.yaml` exists, every binding's `digest` equals the digest of its resolver file after generation. A generation that edited a bound file rewrites its digest in the same run |

### The projection

The specification file is the developer's. It is authoritative, and generation never
modifies it — not to flatten a nested row, not to reorder rows, not to fill in a field.
Re-entry means editing that file and running again, so a rewrite is not a one-time cost.

Generation does not read it directly either. It first builds a **normalised projection**:
one row per effective key, each row carrying the merge of its parent's key and its own,
in the order the generated code tries them. Everything downstream — the resolver's tables,
the correctness tests, the coverage report, the collision gate — reads the projection.

A key listed under a row's `merge.with` is an effective key as well: the projection carries
a row for it, with the declaring row's target, the outcome map it resolves by and its
`merge`, and `from` naming `...merge.with[n]`.

| Property | What it means |
|---|---|
| Derived | Rebuilt from the specification on every run. It carries the same full header as generated mapping code — the `generated. Do not edit.` marker, the fixed provenance mark `# plugin: beter-feed-integration` (see the example below), the specification path, the specification's SHA-256 and the catalog `snapshot_date` — because an edit made here instead of in the specification survives one run and is discarded by the next |
| Provenanced | Every projected row names the path of the row it came from — `markets[3].rules[1]`. Every error, coverage entry and precedence report cites that path, never a projection index. A developer asked to fix a row they cannot find in their own file will edit the projection instead |
| Ordered | Precedence resolved rather than implied: explicit priority first, then specificity, and a tie on both reported rather than resolved quietly. An effective key under a parent is computed, so its specificity is computed, and neither can be read off the nested source by eye |
| Deterministic | The same specification projects to the same rows in the same order. Emission is byte-stable, and a flattening whose order depended on anything else would break that with no row having changed |
| Identity on a flat file | A specification written flat projects to itself. The nested form is a convenience the format accepts, not a second model |

The projection is written to **`.beter/projection/sport-<id>-<channel>.yaml`, under the
root of the repository generation ran in**, one file per specification. That location is
fixed, and it is the one place in this contract where a path is. Generated *code* goes where the repository's conventions put it,
because it is code the repository owns and reviews. The projection is not code: it is the
generator's own record of what it resolved, it compiles into nothing, and it is read back
by the developer and by CI when a generated table disagrees with the file it came from. A
record nobody can find is a record nobody reads.

Each is one document, a `rows` list, in projected order:

```yaml
# BETER feed mapping — generated. Do not edit.
# plugin: beter-feed-integration
# specification: beter-feed/mapping/sport-6-trading.yaml
# specification-sha256: 9f2b6c1e7a4d3f805c9b2a6e1d4f7c803b5a9e2d6f1c4a7b0e3d6f9c2a5b8e17
# snapshot_date: 2026-08-19
version: 1
sport: 6
channel: trading
rows:
- key: {marketType: 8, resultType: 1, interval: 1, subInterval: 0}
  from: markets[0]
  target: {id: M_WINNER}
  outcomes: {1: HOME, 2: AWAY, 3: DRAW}
- key: {marketType: 2, resultType: 1, interval: 18, subInterval: 0}
  from: markets[3].rules[1]
  target: {id: H1_TOTAL, param: line}
  value: {from: "marketValue[0]", rule: passthrough}
  outcomes: {12: OVER, 13: UNDER}
```

The `# plugin: beter-feed-integration` line is a fixed provenance mark, not the name
the skill is installed under; write it exactly as shown.

The projection is a record, not code. Nothing compiles it, no test in the
repository imports it, and it is written under a dot directory for that reason.

`key` is the effective key, every dimension resolved, integer codes throughout. `from` is
the path of the row in the developer's file — a leaf's own path, or the parent path and
the rule's index for a row that came from a nested rule. A trading row also carries
`outcomes`, the effective map after inheritance and replacement, with integer codes.
Everything else on the row is what the specification said, merged. A row carrying no
`from` that resolves to nothing in the source file is a projection defect, not a
specification defect, and it is checked as one.

Nothing else may read the specification. A check that ran against the source rather than
the projection would be checking a different set of rows than the code was generated from,
and it would pass on exactly the nested files the projection exists for.

### Exactly one decision

The resolver is total over its input. For any feed key it is handed, it returns one of
four outcomes and never two, never none, and never a partially-filled result:

| Outcome | Produced by | Carries |
|---|---|---|
| A target | a row with `target: {id, param?}` | the target id, and the parameter value where the row has a `value` rule |
| A set of targets | a row with `target: {many: [...]}` | every declared target, as a set |
| A declared absence | a row with `target: {skip: true, reason}` | the reason |
| Unmapped | no row for that key | the key that failed |

**Outcomes are decided inside the market decision.** The outcome resolver takes the
market's decision — never a bare outcome type — and the outcome type code, and returns
one of three: the selection the market's map names for that code, a declared absence
where the market itself was skipped, or unmapped carrying the market key and the code.
There is no outcome resolver keyed on the code alone; the same code means different
things under different markets, and a resolver that answered it without the market would
answer it wrong for every market but one.

A decision is one value of one type, not a nullable target beside a boolean beside an
error. A caller that has to inspect three fields to learn which case it is in will get
one of them wrong, and the case it gets wrong is the rare one.

### Unmapped is a value

**Unmapped is a value the caller receives, not an exception it must catch. It carries the
key that failed.**

This holds whatever the repository's error style is. **The convention rule governs naming, layout and test style. It does not govern whether failure is a value** — that is
the contract, and it is the contract because an unmapped identifier is an ordinary
runtime event on a feed that adds markets, not a programmer error. A repository whose
error style is thrown exceptions gets a returned decision here, named and laid out the
way that repository names and lays out its types, with the departure stated in a comment
on the decision type.

Express it in the idiom the repository already has: a discriminated union where the
language has one, a sealed hierarchy where it has that, a struct with a kind field and a
sentinel where it has neither.

### Policy at the boundary

`policy.on_unmapped` in the specification header declares what happens when the resolver
returns unmapped. The resolver does not apply it — it returns the decision. The
**boundary** applies it: the one place where a feed message is turned into this
repository's own objects.

| Policy | Effect |
|---|---|
| `close_match` | The match is closed in this system; nothing further from it is trusted |
| `drop_market` | The affected market is dropped; the rest of the match continues |
| `alert_only` | The event is recorded and raised; nothing is suppressed |

All three are **affecting only the match the failure belongs to**. An unmapped market in
one match never closes, drops from or alerts on another. The boundary therefore keys its
state by match identifier, and the generated test for each policy asserts a second,
unrelated match kept flowing through the same call.

### The sport resolver

`beter-feed/mapping/sport-<id>-timetable.yaml` generates into a **sport resolver**: one
shared unit keyed on `sportId` — the sport identifier the feed carries on the message,
the same value the timetable file's header `sport` and its row key hold — with one entry
per in-scope sport, each entry derived from that sport's timetable file alone. One unit,
not a file per sport plus a dispatch file — it sits beside the decision, policy and
coverage files and is read the same way.
**Regenerating one discipline rewrites that discipline's entry and nothing else in it.**

It returns the ordinary decision, in the same four-outcome shape as every other resolver:
this system's discipline identifier, a declared absence carrying the skip reason, or
unmapped carrying the sport identifier. It never applies a policy.

**The boundary calls it first**, for every message that carries a sport:

| The sport resolver returns | The boundary does |
|---|---|
| A target | The message continues into that sport's market, stage or incident resolver |
| A declared absence | No output, no error. The match is not landed |
| Unmapped | The timetable file's `policy.on_unmapped` fires for that match — `close_match` or `alert_only` — and no resolver of that sport is entered |

**A sport with no timetable file fails generation for that discipline**, with a message
naming the missing file, the same way an undeclared collision fails it. Absence of the
file is the undecided state at mapping time and a generation failure at generation time,
because everything generated for that sport is reached through this resolver.

The projection is written like every other one, at
`.beter/projection/sport-<id>-timetable.yaml`.

Three of the nine correctness classes are generated for this channel:

| Class | The generated test asserts |
|---|---|
| `forward_totality` | The file's one row resolves to exactly one decision |
| `absence` | A skip row produces no output and no error, and carries its reason — and one assertion that the skipped sport never reaches a market resolver |
| `unmapped` | A sport identifier other than the file's resolves to unmapped, the declared policy fires, and it reaches no further than that match — and one assertion that the unmapped sport never reaches a market resolver |

The other six do not apply and are declared inapplicable with their reason, in the
`beter-generation` block, as every inapplicable class is: there is no expansion, no
inference, no carriage, no parameter, no arity to be injective over and no record to
assign.
