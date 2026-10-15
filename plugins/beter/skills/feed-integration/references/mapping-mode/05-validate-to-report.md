# Mapping mode: Steps 4 to 7

Part of `references/mapping-mode.md`, which lists every part and when to read it.

## Step 4 — Validate

Validate every specification file against the schema. `references/spec-schema.md` has
the format; the schema is in `schemas/beter-mapping-spec.schema.json`. Run the shipped
validation helper on each file rather than writing a check of your own; the skill's
*Checking a file against its schema* section says where it is and what to do when it
does not run.

Read and validate every specification file under `beter-feed/mapping/`, whether its
discipline is in scope or not. A file for a discipline that is not in scope is where out-of-scope rows come
from, and validating only the in-scope disciplines' files misses them.

Write the refreshed copy to `beter-feed/schema/beter-mapping-spec.schema.json` on every
run, so the copy the files reference and the copy validation ran against are the same
one. The write is a no-op unless the skill's schema has changed since the copy was
taken, so a run that changes nothing leaves the file and its diff untouched.

Report every violation with its file, its row key and what the schema expected. Do not
repair a file to make it validate: a row the schema rejects is a row somebody has to
look at, and a silent repair is the mapping deciding for them.

The schema cannot see two things, so check them by reading. The first: every row whose
chosen target rests on an `other_integration` candidate carries its `composed` block, with
both hops named. A row that lacks it is completed before the coverage report rather than
reported as a violation — the derivation is known, and only its record is missing. This is
the one exception to the rule above, and it is not a repair in that sense: nothing is
decided for anybody, because the target and the hops were chosen already and only their
record is written down. It is never silent. Say in one line which rows were completed.
The exception does not reach a row whose chosen candidate carries
`source: other_integration` and whose `integration` is a scaffold whose `key_shape`, or a
mapping held in this repository whose own key, is flatter than the row's key: composition
through it was refused (`references/mapping-mode/03-other-feed.md`
§ *Composing through another feed's integration*), the row composes through a source the
refusal closed, and its missing record is not what is wrong with it. Report it as a
violation of the refusal, with or without a `composed` block, with its file, its row key
and the intermediate's path, and never complete it.

The second is the `states` table of a scoreboard file. Every entry carries the same field
set; every `target.state` names a key of the table; the file's stage rows use `state` or
`id` and never both; and the table is present exactly when rows use `state`. Each failure is
a violation, reported like any other with its file and its row key or entry label, and never
repaired.

## Step 5 — Coverage

Report coverage per `references/catalog/03-coverage.md`: the three figures, then undecided entries,
proposed rows, ambiguous resolutions, collisions, orphan rows, out-of-scope rows,
deferred and undeclared disciplines. Emit the `beter-coverage` block.

**The coverage report is emitted, not announced.** Figures given in prose are not a coverage
report: they leave out the undecided entries and the ambiguous resolutions, which are what a
reviewer reads first. Step 5 ends by emitting the `beter-coverage` block in every session,
including one that Step 6 then stops. A turn that ran discovery (`references/discovery.md`)
emits its `beter-discovery` block in that turn as well, whatever it found.

A market row written without `outcomes`, or whose map omits a code the catalog lists
under its market type, is undecided on that outcome and is listed with the market's key
and the code.

Stop here if `status` is `fail`. Orphan rows and out-of-scope rows mean the
specification and the snapshot disagree about what exists, and generating from a
disagreement produces code that compiles.

Undecided entries do not stop anything. They are work outstanding, and the first useful
session usually ends with a large number here.

**Step 5 does not wait.** A coverage block is a report, not a stop, and a question asked
beside it with `blocking: false` holds nothing up. Go on to Step 6 in the same turn: a
session that ends on the coverage block, or on a note that the rows are the developer's to
confirm, has not stopped. Step 6 is where the stop is emitted, with every `proposed` row
listed.

**When a discipline is added, the others are counted from their own files.** Every
discipline in scope is still counted and reported in that run's `by_discipline` as its
`{decided, total}` pair, never as a marker that its entry was kept; the ones already in
scope are counted from their own snapshot and specification files, as
`references/catalog/03-coverage.md` § *Adding a discipline
changes one column* says. The catalog's changelog is read for a discipline only when it is
being added or an accepted refresh covers it, and the entry then follows the files that
refresh wrote; a refresh the developer declined changes nothing. An entry that moves for a
discipline whose files did not change was recounted from the wrong source, or something
regenerated that should not have.

## Step 6 — Generate

Check the specification for anything still proposed, and if nothing is, enter generation
mode: `references/generation-mode.md`. Generation runs in a context that holds nothing of
this session; that reference says how the handover works and carries the brief the fresh
context receives. This mode does not load the generation contract.

Where `beter-feed/bindings.yaml` exists, generation mode reads it as one of its inputs
and adopts the resolvers it names; a binding still `status: proposed` stops generation
the way a proposed row does, and is listed under `blocked.proposals` as
`bindings/<sport>/<channel>`.

**Stop and list every row still marked `status: proposed`.** Generate nothing while any
remains. What lifts a row is the developer saying so — for one row, or for the rest of the
file at once — and the edit that records it is `status: confirmed`, written in their own
repository and visible in their merge request. That is what makes the mapping their
declaration rather than this skill's guess. A confirmation that covered less than they
believed leaves rows `proposed`, and this step fails loudly rather than generating from an
unread row.

**Where a listed row is composed, the stop also names the intermediate provider and its
scope decisions**, in prose beside the block, in every turn that lists the rows: once per
provider, its name (the `feed` a placed scaffold records), then one line for each entry the
scaffold records under `scope`, in the scaffold's own words, or a line saying it records
none. `blocked.proposals` stays row ids. The rule and its reason:
`references/mapping-mode/03-other-feed.md` § *Composing through another feed's integration*.

**The stop is emitted, not announced.** A stop that exists only in prose has not stopped
anything a reader can check. Step 6 ends by emitting the `beter-generation` block whatever
happened (`references/generation-mode.md` § *The stop*), and on a stop
that block carries `status: blocked_by_proposals` with every `proposed` row under
`blocked.proposals`, one entry per row, written so the developer can find the row. The
usual form is the row's section and key —
`markets/<marketType>-<resultType>-<interval>-<subInterval>`, `stages/<stage>`,
`sports/<sport>`, `incidents/<type>`. Say which file each row is in beside the block. A stop
on one trading row and five scoreboard rows looks like this, with `files`, `classes` and
`named_cases` empty because nothing was written:

```beter-generation
version: 1
language: python
detected: {}
conventions_stated: []
files: {sources: [], tests: []}
classes: {}
named_cases: {}
blocked:
  proposals: [markets/2-1-1-0, stages/1, stages/21, stages/22, stages/9, stages/7]
  collisions: []
status: blocked_by_proposals
```

Ask for the confirmation in a `beter-questions` block in the same turn, as any other
question. The block is what a checker, a merge request and the next run read; the sentence
"Step 6 stops here" is not.

Confirming is scoped to the file the developer was reading. Several files, or all of them,
only when they ask for that specifically — a session that walked somebody through one
discipline's trading rows has not shown them another's scoreboard rows, and a confirmation
that spread there would confirm rows on the strength of a review of different ones. Rows
added by a later run arrive `proposed` and were not proposed when an earlier confirmation
was given, so no earlier confirmation reaches them.

## Step 7 — Run and report

Relay the `beter-generation` block generation mode returned, unchanged, as this step's
output. The fresh context ran, or tried to run, the repository's own tests and reported
per correctness class inside that block; this session adds nothing to it. Relay it in the turn the
generation agent returns, before any other work, summary or question: a status and a test
count given in prose relay nothing. When a sport is being added, the block comes first and
the list of what was not done follows it. Where generation mode could
not start a fresh context, this step's output is the brief the developer opens a new
session with, and the sentence that generation has not run.

A block carrying `status: blocked_by_conflict` names, under `blocked.conflicts`, every
row whose generated test fails against a bound resolver the developer changed since the
skill last reconciled it. Put each such entry to the developer as one blocking question in
a `beter-questions` block in this turn, `about:` the row's key, asking whether the row
stands or the code does; nothing in that channel is generated until they answer, and the
answer is an edit to the row or to the code, never both at once. An entry carrying `member`
is not one of these: its `row` is the specification row that must decide that member of the
generated unit named as `file`. Put it as one blocking question `about:` its `row`, asking
for the value or the row that decides the member; the developer adds that row or the value
on it, then runs generation again.

A failure here is a real one. Do not weaken a generated test to make it pass, and do not
regenerate until the failure is understood — the tests are the only thing standing
between a wrong row and a wrongly settled market.

**Report a failure as a decision, not as a stack trace.** The nine class names are this
skill's vocabulary and not the repository's, so a developer meeting them for the first time
cannot tell a wrong row from a defective generator from a moved catalog. Say which of the
three it is, cite the specification path of the row rather than a line in generated code,
and name the edits that would satisfy the class. The per-class table is in
the contract's *When a generated test fails* section, which generation mode's context
reads. Regenerate once after an edit the developer made; on a second failure of
the same class, stop and put the choice to them rather than iterating.

**A defect found in review after the tests pass is handled as a failing generated test
is.** A wrong name, a placeholder value or a missing case in the generated tree is one of
the three things the contract's *When a generated test fails* names: the specification says
something the developer did not mean, generation is defective, or the catalog moved. The
first is fixed by an edit to the specification and the third by a refresh, each followed by
a regeneration. The second is reported against this skill, and the generated tree is not
committed. A generated file no binding records is rewritten on the next run, and a hand edit
there is lost. A hand edit to a file a binding records is settled by the digest rule: one
the generated tests then fail on is reported as `blocked_by_conflict`, and one they pass is
adopted silently and its digest rewritten. In both cases that is why generated files are
never edited by hand. Behaviour the specification cannot express goes in a
hand-written file outside the generated tree, called from the dispatch, and that file is
named in the list of what was not done, and the report names every defect it found.

**An adopted edit to a discipline not being added changes production behaviour.** Every
`adopted.edits` entry on a discipline other than the one being added changes code that
already runs. Name each one as a production behaviour change beside the block, and
recommend that it gets its own review or merge request.

**A specification comment generation could not honour is named.** Generation honours a
row's `comment` or says why it did not (`references/spec-schema/03-cases-and-collisions.md`,
*`comment`*). Each comment it could not honour is named in the list of what was not done,
with the reason. Display names are the usual case: no row carries them, and generation
never invents them.
