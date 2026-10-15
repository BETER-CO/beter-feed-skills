# Generation contract: parameters, conventions and emission

Part of `references/generation-contract.md`, which lists every part and when to read it.

The third failure named under *The catalog digest* is the third row of *When a
generated test fails*, in `references/generation-contract/05-failures-and-report.md`. *The boundary calls it first*,
named under *Adopting existing code*, is in `references/generation-contract/02-resolver.md`, *The sport resolver*.

### Parameter rules

Market value and outcome value are parameters, not key dimensions. They carry handicap
and total lines, so the space they range over is unbounded and no row enumerates it.
Each row that takes one declares how it travels:

| `value.rule` | Extra field | Generated behaviour |
|---|---|---|
| `passthrough` | — | The value unchanged |
| `negate` | — | The value with its sign flipped |
| `scale` | `factor` | The value multiplied by `factor` |
| `offset` | `by` | The value with `by` added |
| `lookup` | `table` | The value replaced from the table; a value absent from the table is unmapped, not a default |

The parameter reaches the target under the name in `target.param`. A row with a `value`
rule and no `target.param` does not validate, so this pairing is guaranteed by the time
generation runs.

A handicap or line that arrives as text is parsed independently of locale: the whole
string is read as a decimal number with `.` as the separator, or the parse fails. Never a
partial or prefix parse, and never a style that accepts digit grouping or currency; and a
non-finite result (NaN, infinity) is rejected. Examples of such a parse, not equivalent to
each other, are `NumberStyles.Float` with `CultureInfo.InvariantCulture` in C# and
`new BigDecimal(text)` in Java. A grouping style reads `"1,5"` as `15` and a prefix parse
reads it as `1`, and either way the market settles on a line nobody quoted.

`score_pair`, `score_series` and `clock` are also value rules and are described under
incident parameter carriage below, which is the only place they appear.

### Incident parameter carriage

An incident row carries a `params` block, a map keyed by the parameter name the feed
publishes, produced from the catalog rather than authored:

```yaml
incidents:
  - key: {type: 1029}
    target: {id: MATCH_START}
    params:
      PeriodScore:        {to: periodScore, rule: score_pair, result_type: 1}
      MatchScore:         {to: score,  rule: score_pair, result_type: 1}   # 1 is Goal
      ScoreHistory:       {to: history, rule: score_series, result_type: 1}
      MatchMinute:        {to: minute, rule: clock}
      VirtualMatchMinute: {to: null,   rule: drop, reason: "we display the real clock"}
      Winner:             {to: null,   rule: drop, reason: "not carried on our start event"}
```

| Entry field | Generated behaviour |
|---|---|
| `to` | The field of the target record the parameter is carried into. `null` exactly when `rule` is `drop` |
| `rule` | Any value rule above, plus `score_pair`, `score_series`, `clock` and `drop` |
| `result_type` | Required on `score_pair` and `score_series`, refused elsewhere, and always the **integer code**. It is what a score counts and the incident documentation never states it |
| `reason` | Required on `drop`, refused elsewhere |

| Score rule | Parses |
|---|---|
| `score_pair` | A `"P1:P2"` string into the two sides' counts of the result type named by the code |
| `score_series` | A space-separated run of `"P1:P2"` pairs, one per period |
| `clock` | An `"MM:SS"` string into elapsed time |

The map key is the source, so a carriage entry takes no `from`. That is the only shape
difference from a `value` block, and it is why carriage is not expressible as a row.

Three properties of the feed the generated carriage tolerates rather than treats as
faults: `PeriodScore` may be absent until a period starts, `Winner` may arrive empty, and
a key the catalog declares is not a key every message carries. **Every parameter the
catalog declares for a mapped type has an entry.** One with no entry fails generation:
silence is not a decision, for the same reason `skip` carries a reason.

## The two rules

### It follows the conventions already in the repository

Test runner, naming, error style, file layout, nullability, and the shape of the types
around it.

The reason is not tidiness. Generated code that does not look like the code around it
**is not reviewed, and unreviewed generated code is the failure mode this project exists to avoid.** A reviewer skims a file that reads like the rest of the repository and stops
on the line that is wrong. A reviewer opens a file written in a foreign idiom, sees that
it is machine-made, and approves it as a unit. The mapping is the repository owner's
declaration only for as long as somebody reads it.

Concretely: the generated tests use the runner already in the manifest and are named the
way the existing tests are named; the generated files sit where the existing files sit;
the generated types use the nullability and immutability settings the project already
enforces; and the generated code compiles under the warning level the project already
sets, including where warnings are errors.

### It takes no third-party dependency

Mapping is data and branching. **The generated code takes none either** — not a YAML
parser, not a property-testing library, not a code-generation runtime, not a mapping
framework. Some clients are barred by policy from adding libraries, and a generated file
that needs a package approval is a generated file that does not land.

Three consequences show up in the output and are worth naming, because each looks like an
omission until the reason is known:

- **Property tests are hand-rolled.** The parametric class generates its lines from a
  seeded, enumerated range written into the test, not from a generator library. Seeded,
  so a failure is reproducible from the test file alone.
- **The generated drift check hashes bytes.** It **hashes the file bytes rather than parsing them**, because every language's standard library has SHA-256 and not every
  one has a YAML parser.
- **The specification is not read at runtime.** Its rows are emitted as data in the
  generated language. Nothing in the generated code opens `beter-feed/mapping/`.

## Emission is deterministic

Re-entry is the frequent operation: someone adds rows and regenerates. That produces no
spurious diff only if emission is deterministic, and emission is deterministic only if it
is specified. It is not a property that falls out of generating carefully.

| Rule | Why |
|---|---|
| Rows are emitted **ascending by the key tuple**, never in file order — markets by `(marketType, resultType, interval, subInterval)`, each market's outcomes inside it, ascending by outcome type code, stages by `(stage, interval)` with an absent interval sorting first, incidents by `(type, params sorted by key then value)` | A row added in the middle of the file moves nothing else |
| Table and map literals are emitted in the same ascending order as their rows | A hash-ordered literal reorders itself between runs of the same generator |
| `many` targets are emitted in the order the specification lists them | It is the only order the specification states, and the expansion test asserts a set, so nothing depends on it — but it must not vary |
| The file header carries the fixed provenance mark `plugin: beter-feed-integration`, exactly that text in the language's comment syntax (`# plugin: beter-feed-integration` in 02-resolver.md), the specification path, the specification's SHA-256 and the catalog `snapshot_date`. **No timestamp, no tool version, no machine name, no absolute path** | Each of those changes on a run that changed nothing |
| Files end with a single newline, and use `\n` unless the repository's `.editorconfig` says otherwise | A line-ending flip is a whole-file diff |
| Files are written in **UTF-8 without a byte-order mark** (with one only where `.editorconfig` sets `charset = utf-8-bom`), whatever the host's default encoding | The marker line below is what makes a generated file findable, and a file it cannot be read from in UTF-8 is not found; a host default such as Windows-1252 writes the marker's dash as a byte UTF-8 rejects |
| Numbers are emitted in the **shortest round-trippable form in the invariant culture** | `0.5` written under a comma-decimal locale becomes `0,5`, which is a different literal and, in some languages, a compiling one |
| Identifiers derived from a target id use one stated transformation, applied the same way everywhere | Two files disagreeing about how `M_TOTAL` becomes a member name is a diff that appears when an unrelated row is added |

Every generated file opens with this line, in that language's comment syntax, as the
first line of the file:

```
BETER feed mapping — generated. Do not edit.
```

A generated test file is a generated file: it opens with the same line, wherever the
repository keeps its tests.

It is what makes a generated file findable without knowing where this repository puts
things, and it is what a reviewer needs on line one rather than line forty.

### The catalog digest

Generation writes the **digest of the catalog files it was generated against** into the
generated code: one constant per catalog file, holding the file's SHA-256 over its bytes.

One generated test re-reads those files, re-hashes them, and compares. A catalog snapshot
that changes under a generated mapping fails that test in this repository's own CI,
before anything reaches the boundary. This is the generated half of drift detection; the
coverage report is the other half, and the two are independent on purpose — a digest
mismatch says the catalog moved, and the coverage report says what moved and whether any
row now points at nothing.

Generation compares before it writes. Where a digest constant already stands in the
generated code and the catalog file it names no longer hashes to it, the catalog moved
under the mapping: leave the constant as it stands, write nothing, and report it as the
third failure below, naming the file, the recorded digest and the digest found. Do not
recompute the constant. A digest rewritten by the session that found the mismatch is a
drift signal deleted, and the figures restated beside it are trusted on a test that can no
longer fail. The block reports `status: blocked_by_catalog_drift`, and `blocked.catalog`
lists each file as `{file, recorded, found}`. Nothing was written.

### Adopting existing code

The contract states what must exist, not who wrote it. Where a binding names the resolver
for a channel, generation emits what is missing — the projection, a test per correctness
class driven through the bound resolver, the coverage check, the digest test, the unmapped
policy where none exists — and replaces nothing the tests prove. After confirmation the
specification is authoritative, and a generated test that fails against a bound resolver
is settled by the binding's `digest`, row by row:

| Generated test | Resolver digest | What generation does |
|---|---|---|
| Passes | Any | Nothing; the digest is rewritten if the file changed |
| Fails | Equals the recorded one | The code has not changed since this skill last reconciled it, so the difference came from the specification: the row wins. Edit the bound resolver for that row, following its conventions, rerun the tests, and list the edit under `adopted.edits` as `{file, row, at}` |
| Fails | Differs from the recorded one | The developer changed the code since. Write nothing for that channel; report `status: blocked_by_conflict` with the row under `blocked.conflicts` as `{row, file, recorded, found}`. The question is mapping mode's to put; the answer is an edit to the row or to the code |

The first generation after discovery lands in the second case: the digest was taken at
discovery and the developer confirmed in between, so a confirmed row the code contradicts
brings the code under the row. A row added later is generated into the bound resolver the
same way, under the same digest rule. A row deleted from the specification whose case
still sits in the bound resolver is removed under the same conditions and listed under
`adopted.removed`: "remove what the specification no longer holds" holds for adopted
code too. That rule reaches only a row that once stood: a row the confirmed specification
carried and lost later is a deleted row, and removal under the digest rule reaches it
whenever the deletion happened. A case the bound resolver handles for a catalog entry the
current catalog does not publish was never a row — nothing in the specification named it,
so nothing was deleted from one — and the removal rule does not reach it: the case stays
in the resolver as it stands and the binding's `digest` is not rewritten for it.
Discovery reported that entry under `unpublished` and the developer decided there;
generation has nothing to add. A binding that carries a `digest` and whose file or symbol
does not exist fails generation for that channel with the path named, as a
`blocked.conflicts` entry whose `found` is `absent`.

**A confirmed planned binding is a creation, not a conflict.** A planned binding is a row
with no `digest` whose resolver file does not exist. A row with no `digest` whose resolver
file exists is not one: generation writes nothing for it and reports a `blocked.conflicts`
entry `{binding: bindings/<sport>/<channel>, recorded: absent, found: <digest of the file as
read>}`. For a planned binding, generation creates the file
its `resolver` names, with the named symbol, as on a fresh repository; adds that
discipline's dispatch entry at the recorded `policy_site`, and nothing else in that file;
and writes the created file's digest into the row in `bindings.yaml`. Where the
`policy_site` is itself planned, on a channel no discipline was bound for, generation writes
that channel's boundary there as on a fresh repository.

**In a repository with bindings, a file a fresh repository would not get is not
created.** A planned binding names the channel's resolver file. For that channel generation
creates the files it creates on a fresh repository, plus the dispatch entry at the recorded
`policy_site`, and `files` in the block lists every file written. A file the repository
keeps beside another discipline's resolver, outside those, is not created for the new
discipline.

**A member the specification does not decide is never given a placeholder value**, on any
repository: not a `0`, an empty string, or a name copied from another discipline. Generation
withholds that discipline's whole channel and writes nothing for it, so no partial file
breaks the build. It reports a `blocked.conflicts` entry `{row, file, recorded: absent,
found: absent, member}`, where `row` is the specification row that must decide the member,
`file` is the unit that carries it and `member` names the member, and the block reports
`status: blocked_by_conflict`.

**On a repository with confirmed bindings, generation writes the bound resolver, the
generated files named above and what confirmed planned bindings name, and nothing else.**
The bound resolver changes only under the digest rule, and every change is listed under
`adopted.edits` or `adopted.removed`. Beyond what a confirmed planned binding names (its
dispatch entry, or a boundary at a planned `policy_site`), generation does not write the
boundary (the binding's `policy_site`), a call site or a hand-written test. A change one of those would need is left unwritten and reported as a
`blocked.conflicts` entry whose `file` names the file it would touch and whose `recorded`
is `absent`, since no binding records that file. An in-scope pair with no binding at all is
reported as `references/generation-contract/05-failures-and-report.md`, *What generation
reports*, says. The block reports `status: blocked_by_conflict`. *The boundary calls it
first* is a rule for a boundary this skill writes; a boundary that consumed the feed before
this skill arrived is this repository's own code, and it stays as it is. A gap in such a
boundary (it skips the sport resolver, the generated policy or both, or it hardcodes a
sport) is not a change the
conflict rule above reports: it is not a `blocked.conflicts` entry, it does not block
generation, and it is named in prose beside the block.
