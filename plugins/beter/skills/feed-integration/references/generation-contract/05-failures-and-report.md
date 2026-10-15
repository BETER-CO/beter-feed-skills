# Generation contract: failures, re-entry and the report

Part of `references/generation-contract.md`, which lists every part and when to read it.

The emission rules named under *Re-entry, and adding a discipline* are in
`references/generation-contract/03-emission.md`, *Emission is deterministic*.

## When a generated test fails

Nine class names are this contract's vocabulary, not the repository's. A developer meeting
them for the first time reads `injectivity failed` and has no way to know whether that
means their specification is wrong, the generator is wrong, or the test is too strict — and
the wrong guess is expensive in both directions. So a failure is reported as a **decision
put to the developer**, never as a stack trace and never as something to iterate against.

**Every failure is exactly one of three things.** Say which one, in these words:

| It is | Looks like | Who fixes it |
|---|---|---|
| **The specification says something the developer did not mean** | The test asserts what the row declares, and the row is the wrong declaration | The developer, by editing their own specification file and re-entering |
| **Generation is defective** | The specification is right and the emitted code or table does not implement it | This skill. Report it, do not commit the generated tree |
| **The catalog moved under the mapping** | The digest test fails alongside, or the coverage report shows orphan rows | Refresh the snapshot (`references/catalog/02-snapshot.md` § *Refresh*), then re-enter |

There is no fourth. **Do not weaken a generated test, do not delete it, and do not declare
its class inapplicable to make a run go green.** A class declared inapplicable to silence a
failure is the one outcome none of the three above can be told apart from afterwards.

Cite the row, not the assertion. Every projected row names its path in the developer's own
file — `markets[3].rules[1]` — and that path, the feed key, and the target are what makes a
failure actionable. A developer sent to a line number in generated code will edit generated
code.

**What each class's failure actually means**, in the terms the developer already has:

| Class | A failure says | Usually decided by |
|---|---|---|
| `forward_totality` | A key in your own file resolves twice, or not at all, **or** the emitted table is out of key order | Generation, in both halves. If two rows genuinely both apply, the developer declares which wins; an unordered table is a generator that stopped sorting and is never the specification's fault |
| `injectivity` | Two different feed keys land on one of your terms, and nothing said they should | The developer: either the two really are one thing — declare a `merge` — or one of them is on the wrong target |
| `expansion` | A `many` row produced a different set than it declared | The developer, by correcting the declared set. The test compares as sets and asserts nothing about order |
| `inference` | The recovery rule breaks on a case your rows do not contain — an unmatched prefix, two prefixes matching, an empty id | The developer. This is the class with no row behind it, so this is the class where a wrong reading survives review |
| `carriage` | A parameter the catalog declares for a mapped incident type is neither carried nor dropped with a reason | The developer, by naming the field it goes to or the reason it does not |
| `absence` | A `skip` produced output, raised an error, or lost its reason | Generation, in all three. The schema will not accept a `skip` without a reason, so a reason missing at this point was dropped between the file and the decision |
| `unmapped` | The declared `policy.on_unmapped` did not fire, or took down more than the policy the developer declared allows | Generation. Which policy applies is the developer's declaration; that the declared one fires, and reaches no further than its own definition, is this contract's |
| `parametric` | A `value` rule breaks on a negative, zero or fractional line | The developer, by correcting the rule. A rule that is right only for positive integers is a rule that settles a handicap wrongly |
| `assignment` | A stage's generated assignment leaves a field of the `states` table unassigned, or one stage key reaches two states | The developer. A partially assigned record is a state the consumer acts on and nothing about it looks wrong |

**Stop rather than loop.** Regenerating against a failure that has not been understood
costs the developer's build time and this skill's tokens, and it changes nothing: the same
specification emits the same code. Regenerate once after an edit the developer made. On a
second failure of the same class, stop and put the choice to them — the row, what the class
asserts, and the two or three edits that would satisfy it — and wait. Their answer is a
decision about their own product, and this skill does not hold the facts to take it for
them.

Record the decision where it will be found again: the reason on a `skip`, the
`chosen_because` on a resolved ambiguity, the `merge` block on a declared collision. A
failure argued out in a chat session and fixed silently in the specification is a failure
the next person re-argues from nothing.

## Re-entry, and adding a discipline

Re-entry is the frequent operation. Somebody adds rows to a specification and regenerates.

The result is a diff containing the added rows and nothing else. That is a consequence of
the emission rules above rather than of care taken during the run: rows sorted ascending
by key, tables in the same order, no timestamp in the header, invariant number formatting.
A re-entry that touches a file nobody edited is a defect in the generator — report it
rather than committing it.

Adding a discipline regenerates **that discipline alone**. Each discipline's generated
files are keyed by its sport identifier and derive from that discipline's specification
and snapshot files only, so nothing in another discipline's generated tree has an input
that changed. After adding a discipline, the other disciplines' generated files are
byte-identical and their `by_discipline` entries are their `{decided, total}` pairs counted
from those same files. A run that regenerates an untouched discipline produces a diff
nobody can review, and an unreviewed diff on settlement code is what this design exists to
prevent. In a repository with bindings, the new discipline's files are created at the paths
its confirmed planned bindings name and its dispatch entries are added at the recorded
policy sites. A binding of any channel whose resolver file already exists, such as a
hand-written sport dispatch or a resolver the bound disciplines of that channel share,
carries a digest and is an existing binding: the new discipline's entries are added to that
file under the digest rule (`references/generation-contract/03-emission.md`,
*Adopting existing code*), and it is neither a conflict nor a creation. Every other
discipline's generated files stay byte-identical, and in bound files only the dispatch
entries and rows added under the digest rule change.

## What generation reports

Step 6 ends by emitting this block, whatever happened:

```beter-generation
version: 1
language: go
detected:
  test_command: go test ./...
  test_runner: go test
  test_naming: TestXxx with table-driven subtests
  error_style: explicit error values, no exceptions
  file_layout: internal/<package>/ with _test.go beside the source
conventions_stated: []
files:
  sources:
    - internal/mapping/generated/decision.go
    - internal/mapping/generated/incidents_sport6.go
    - internal/mapping/generated/policy.go
    - internal/mapping/generated/catalogdigest.go
    - internal/mapping/generated/coverage.go
  tests:
    - internal/mapping/generated/forward_totality_test.go
    - internal/mapping/generated/expansion_test.go
    - internal/mapping/generated/absence_test.go
    - internal/mapping/generated/unmapped_test.go
    - internal/mapping/generated/named_cases_test.go
    - internal/mapping/generated/catalogdigest_test.go
    - internal/mapping/generated/coverage_test.go
classes:
  forward_totality: {tests: 1, applicable: true}
  injectivity:      {tests: 0, applicable: false, why: "incident rows expand; this channel carries no injective target"}
  expansion:        {tests: 1, applicable: true}
  inference:        {tests: 0, applicable: false, why: "no inference block in this specification"}
  carriage:         {tests: 1, applicable: true}
  absence:          {tests: 1, applicable: true}
  unmapped:         {tests: 1, applicable: true}
  parametric:       {tests: 1, applicable: true}
  assignment:       {tests: 0, applicable: false, why: "no `states` table in this specification; assignment is the class of a scoreboard record"}
named_cases:
  sign_convention: {tests: 0, applicable: false, why: "no negate rule in this specification"}
  emission_order:  {tests: 1, applicable: true}
  undo_chain:      {tests: 1, applicable: true}
  source_switch:   {tests: 1, applicable: true}
  level_shift:     {tests: 1, applicable: true}
  # applicable mirrors the specification's cases block; a case it declares false carries that why
adopted:
  bindings: 0
  edits: []
  removed: []
blocked:
  proposals: []
  collisions: []
  catalog: []
  conflicts: []
  # an entry is {row, file, recorded, found, member?} or {binding, recorded, found?}, e.g.
  # conflicts: [{binding: bindings/3/markets, recorded: absent}]
status: ok
```

`status` is one of:

| Value | Meaning |
|---|---|
| `ok` | Files written |
| `blocked_by_proposals` | At least one row is still `status: proposed`. `blocked.proposals` lists every one so the developer can find it, usually as its section and key — `markets/2-1-1-0`, `stages/9`, `sports/6`, `incidents/12` — with the file named in prose beside the block. Nothing was written; `files`, `classes` and `named_cases` are empty. This block is the stop `references/mapping-mode/05-validate-to-report.md` Step 6 requires; a stop said in prose without it is not a stop |
| `blocked_by_collision` | At least one undeclared collision. `blocked.collisions` lists each as `{target, keys}`. Nothing was written |
| `blocked_by_catalog_drift` | A digest constant already in the generated code no longer matches the catalog file it names. `blocked.catalog` lists each as `{file, recorded, found}`. The constant stays as it stands. Nothing was written |
| `blocked_by_conflict` | A generated test fails against a bound resolver whose digest differs from the one `bindings.yaml` records, or a change generation may not make would touch a file no binding records (`recorded: absent`); a gap in a boundary the repository already had is not one: it is named in prose beside the block. In a repository with bindings, an in-scope discipline-and-channel pair with no binding, existing or planned, is one too, and so is a row with no digest whose resolver file exists. On any repository, a generated unit with a member the specification does not decide is one as well: its entry is `{row, file, recorded: absent, found: absent, member}`, where `row` is the specification row that must decide the member and `member` names it, and nothing is written for that discipline's channel. `blocked.conflicts` entries take one of two shapes: `{row, file, recorded, found, member?}` for a row or a file, where `member` is present only on an undecided-member entry, and `{binding, recorded, found?}` for a binding, where `binding` is `bindings/<sport>/<channel>`, `recorded` is `absent` and `found`, present only where the resolver file exists, is its digest as read. Nothing was written for that channel or pair; other channels report as usual under `files`. Beside a pair with no binding stands a one-line pointer to `references/mapping-mode/01-scope-snapshot.md`, Step 1, where its binding is proposed |
| `blocked_by_test_run` | No test command was found in the repository's build, test and configuration files, the command did not start, or the toolchain it needs (an SDK, a runtime version) is absent. `detected.test_command` carries the command, or `absent` where none was found, and the shortest decisive error line stands beside the block. `files` lists what was written, and nothing is reported as passing. The run is not made another way: no other toolchain, runtime version or project file is substituted, and no harness is built by hand |

`blocked_by_proposals` reports every row carrying `status: proposed`. A row carrying
`status: confirmed`, and a row carrying no `status` at all, both generate: the first was
read and accepted, the second was never proposed.

`conventions_stated` is empty in every repository that holds code of its own, whatever
detail its conventions left unshown; it is filled only in an empty repository, where it
lists each convention chosen and why. Step 7 runs the tests and reports per
class, using these same nine names.

`adopted` is present whenever `beter-feed/bindings.yaml` exists: `bindings` counts the
bindings read, `edits` lists every edit made to a bound file under the digest rule as
`{file, row, at}`, and `removed` every case taken out of one, as `{file, row}`, with no
`at`, since the line it stood on is gone — `removed: [{file: internal/mapping/markets.go,
row: markets/6-1-1-0}]`. `row` is
the row's section and key, the same spelling `blocked.proposals` uses — `markets/6-1-1-0`,
`stages/9` — and `at` is the file and line edited. A generation that adopted nothing
reports the three as `0`, `[]` and `[]`.
