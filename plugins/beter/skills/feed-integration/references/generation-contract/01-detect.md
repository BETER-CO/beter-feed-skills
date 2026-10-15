# Generation contract: detection, collisions and named cases

Part of `references/generation-contract.md`, which lists every part and when to read it.

## Detect first

The reader of this contract is the fresh context generation mode starts
(`references/generation-mode.md`), and it holds nothing of the mapping session: no
exchange, no catalog procedure, no vocabulary but what the specification, the scope file
and the catalog files the brief names carry. Every input below is a file, and every
decision below is taken from files.

One more input where it exists: `beter-feed/bindings.yaml` (`references/catalog/01-scope.md`,
*Bindings*), naming the code that realises, or will realise, a channel's mapping; a
planned binding names a file generation creates. Read it before
the repository. A binding still `status: proposed` stops generation as a proposed row
does: list it under `blocked.proposals` as `bindings/<sport>/<channel>` and write nothing.

Before emitting anything, read the repository:

| Detect | Read | Decides |
|---|---|---|
| Language | Build and manifest files first — `*.csproj`/`*.sln`, `package.json`, `pyproject.toml`/`setup.cfg`, `go.mod`, `pom.xml`, `build.gradle`, `Gemfile`, `composer.json` — then the source tree where they disagree | Which idiom everything below is written in |
| Test runner | The manifest's test dependency, and the existing test directory | Where the generated tests go and how they are run |
| Test naming | Two or three existing test names, read | What the generated test names look like |
| Error style | The existing integration code: thrown types, returned results, sentinel values | How a failure is expressed. Report the repository's own style first, by the type its code uses — the `error` interface, an exception class, a result type, a sentinel — and the departure *Unmapped is a value* makes after it. A line that describes only the generated code has detected nothing |
| File layout | Where existing source and tests sit relative to each other | Where the generated files go: beside the hand-written files of their kind, in the directory, package or namespace those files already use. A folder, package or namespace of its own for generated code is made only where the repository already keeps one |
| Nullability and typing | The manifest's strictness settings and the existing signatures | Whether an absent value is a null, an option, a zero value or a union member |

Where a repository holds more than one language, the language of the **component that
consumes the feed** is the one that decides, not the largest directory. A Python data
pipeline beside a C# consumer generates C#.

Where the repository is empty and has no conventions to follow, **state the conventions you chose rather than choosing silently**, in the session and in a comment at the top of
the first generated file. A client integration is normally an existing service, so an
empty repository is the exception — but a silent choice in the exception is a convention
nobody agreed to and nobody can find later.

A repository that has conventions has them for every detail. Where no existing file shows
the detail in hand — what a generated file is named, whether generated code sits in a
folder of its own, where a test for it goes — the nearest existing example decides it, and
the result is reported under the field it belongs to (`file_layout`, `test_naming`). That
is a reading, not a choice: `conventions_stated` stays empty, and it is filled only in the
empty repository above. A detail settled by example and written under `conventions_stated`
reports a convention as chosen in a repository that already had one, which is the one
report a reviewer cannot act on.

## Collisions fail generation

Dropping dimensions means two distinct feed keys can reach the same target key. This
system then cannot represent the difference, which is a defect in the specification rather
than in the generated code.

**Generation fails on an undeclared collision** rather than producing code. Emit
`status: blocked_by_collision`, list every colliding key group with the target it reaches,
and write no file. A partially generated tree is worse than none: it compiles, its tests
pass, and one of the two colliding markets settles against the other's result.

Where a collision is intended, the specification says so and how the two are merged:

```yaml
  - key: {marketType: 2, resultType: 1, interval: 1, subInterval: 0}
    target: {id: M_TOTAL, param: line}
    merge:
      with: [{marketType: 27, resultType: 1, interval: 1, subInterval: 0}]
      rule: first_wins
```

`rule` is `first_wins`, `last_wins` or `declared_order`. A declared collision generates,
and generates a test asserting the merge rule holds — that the key the rule names is the
one whose decision survives when both arrive.

An outcome collision — two codes in one market's map naming one selection — fails the
same way, `status: blocked_by_collision` with the market key and the codes, and has no
declared form: there is no `merge` on a map, by design (`references/spec-schema/03-cases-and-collisions.md`,
*Collisions*).

**This check replaces the round-trip assertion for flat targets, where a round trip cannot succeed by construction.** A flatter target discards dimensions; a round trip would have
to restore them; nothing can. The property that protects settlement there is not "the
mapping inverts" but "the mapping loses nothing this system needed", and an undeclared
collision is exactly the case where it did.

## Named generator cases

Some client-side semantics no mapping row can express. They live in the generated code and
its tests, and each is a **named case** with its own generated test. Generation never judges
whether a case applies. `sign_convention` applies where a row carries the `negate` rule,
`source_switch` where the catalog snapshot records both source bands for the discipline, and
the other three are read from the incidents file's `cases` block (`references/spec-schema/03-cases-and-collisions.md`,
*The `cases` block*). A case the block does not carry is a gap in the specification: report
it as one, generate nothing, and stop.

**This list is closed.** Five cases, not a licence to put arbitrary behaviour in generated
code. A semantic that fits none of them is raised with the developer and recorded as a
question; it is not quietly generated.

| Case | What it is | The generated test asserts |
|---|---|---|
| `sign_convention` | The target's handicap or line runs the opposite way from the feed's | The `negate` rule reaches the target's parameter over the parametric range, and a positive feed line arrives negative |
| `emission_order` | Incidents carry an index within a match and must reach this system in index order regardless of arrival order | A shuffled arrival of one match's incidents is emitted in ascending index order, and two matches' incidents do not interleave |
| `undo_chain` | The feed retracts by position and never by reference: no retraction names the incident it retracts. Undo retracts the latest unretracted incident, a `Cancel_*` type retracts the latest unretracted incident of its kind, and Redo restores what the latest Undo retracted. Each carries the scores as they stand after it | The state after a retraction equals the scores the retraction carries; only the retracted incident's effect is removed; and a retraction with nothing to retract — an Undo with no incident outstanding, a `Cancel_*` with none of its kind, a Redo with no Undo outstanding — is reported rather than applied |
| `source_switch` | Incident types **below 1000 come from one production mode and types from 1000 upward from another**, with the change **signalled mid-match by its own incident type**, so the same logical event arrives under two different type codes | Both codes of a paired event resolve to the same target; the switch incident itself resolves rather than falling to unmapped; and a match that switches mid-stream produces one continuous sequence of targets rather than two |
| `level_shift` | The target holds once at match level what the feed carries per incident, or the reverse. The rows folded and the match-level field are the ones the `cases` block names | The per-incident value is folded to one match-level value exactly once, and a second incident carrying the same value does not double it |

A named case is implemented where the mapped messages go, not beside them. The code that
carries it sits on the path a feed message takes through the generated mapping — the
ordering ahead of resolution, the retraction where an incident's effect is applied, the fold
where a row's parameter reaches the match-level field — so that a message of a mapped type
cannot get past it. A helper that nothing in the generated code calls is not the case: it
protects nothing, and its tests pass whether or not the integration ever uses it. Where the
repository has no confirmed bindings and no boundary of its own, generation writes the
boundary: the one unit that calls the sport resolver first, then the channel's resolver,
applies the policy, and takes each message through the named cases on its way. A case written
where a boundary *would* route a message, with no boundary written, is that uncalled helper.
Under confirmed bindings the boundary is the repository's own and stays as it is, below; a
confirmed planned binding's `policy_site` is where a new discipline's dispatch entry is
added, and a planned `policy_site` is where generation writes the boundary of a channel no
discipline was bound for (`references/generation-contract/03-emission.md`, *Adopting
existing code*).

The generated test drives the case the same way: through the feed boundary — the one
generation wrote, or the one a binding names — with messages of
the types the specification maps — the rows the `cases` block names for `level_shift`, the
retraction types the file maps for `undo_chain`, mapped incidents carrying an index for
`emission_order` — and it asserts on what comes out, by the targets those rows name. A test
that exercises a helper with values of its own proves the helper and nothing about the
mapping.

`source_switch` costs the most when it is missed, because both halves look correct in
isolation. A mapping covering only the band below 1000 passes every test it has and
produces nothing at all for the matches running on the other source. The catalog snapshot
records the band for each incident type and names the event each one carries, so the pairs
are emitted from the catalog's names — **the two bands share no numbering, and an offset
pairs the wrong events** — and the generated test enumerates them rather than being told
them.
