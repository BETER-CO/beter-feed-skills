# Catalog: detectors and coverage

Part of `references/catalog.md`, which lists every part and when to read it.

*Refresh* and *The first run after discovery*, both named below, are in
`references/catalog/02-snapshot.md`.

## What each detector catches

| Detector | Runs | Catches | Severity |
|---|---|---|---|
| Undecided catalog entries | This repository's CI, from generated code | An in-scope catalog entry that is neither mapped nor declared skipped | Needs a decision |
| Undeclared discipline | This repository's CI, from generated code | A discipline in the index that is neither in scope nor deferred | Needs a decision, once per discipline |
| Out-of-scope rows | This repository's CI, from generated code | A specification row for a discipline in the index that is not in scope | Fails |
| Orphan rows | This repository's CI, from generated code | A specification row whose sport or key the catalog does not carry | Fails |
| Snapshot staleness | This skill, on demand. **Never in CI** | The documentation changed since the snapshot was taken, within scope | Needs a decision |
| Unmapped identifier policy | The production consumer | The feed sent a key the specification does not contain | Fires the declared policy |

**The first five compare declarations against each other.** Scope against the index,
specification against the snapshot, snapshot against the documentation. They need no
feed connection and they run offline, and together they are the coverage report. Only the
first four of them reach CI; the fifth is why.

**Nothing this skill installs in your CI is an AI agent.** The first four detectors reach
CI as *generated code* — an ordinary test, in your language, run by your own test runner,
committed once and re-run for free on every build. The generated check is described in
`references/generation-contract/04-tests.md`. This skill runs when a developer invokes it, not on
every commit: a mapping session costs a developer's attention and an agent's tokens, and a
pipeline that spent both after every code fix would be turned off within a week.

The fifth detector is the exception and it is why the column above says what it says.
Snapshot staleness compares the snapshot against BETER's *published documentation*, which
is not in this repository — reading it needs the `feed-docs` skill and therefore an agent. It
runs when someone asks, on the cadence in *Refresh* (02-snapshot.md). Do not
wire it into a pipeline. What CI does hold for the same failure is cheaper and needs no
network: the generated catalog digest test fails the moment a snapshot file in this
repository changes under a generated mapping.

The sixth is the only one that observes the feed, and it is **a runtime policy rather than a report**. It lives in the generated code, at the boundary where a message is resolved, and it does what the specification's `policy.on_unmapped` header declares. It produces no section in any report, because there is no static input it could be computed from: the thing it catches is a message that arrived.

The two failing severities are the reverse direction, and the reverse direction is the
only strict one. A specification row whose catalog entry does not exist refers to
something the feed does not describe. A row for a discipline that is not in scope is a
specification and a scope declaration disagreeing about what the codebase carries.
Neither of those is a measurement. The one exception is the first run after discovery
(*The first run after discovery*), where an entry the code handles and the snapshot lacks
is reported rather than failed.

## Coverage is three measurements, not one failure

No leftover is a defect. The report presents all three figures as measurements.

**Share of the in-scope catalog decided.** Within the disciplines in scope, every feed
entry either mapped or declared skipped with a reason. At one hundred per cent, all the
content of the disciplines this codebase carries reaches this system. This is the figure
a developer works against during a mapping session, because it is the one their edits
move.

**Share of the client's vocabulary matched.** At one hundred per cent, everything this
system can display is being fed. A vocabulary fully matched while the feed carries more
is finished rather than deficient: there is nothing left to put the extra content in.

**Share of the feed's disciplines in scope.** Disciplines in scope over disciplines in
the index. This is the commercial figure. It moves only when a discipline is taken on,
and it is the one that says where the remaining revenue is.

The first two say how well the chosen disciplines are covered. The third says how many were chosen. They are **reported together and never combined** — there is no single coverage number, no average and no weighted score, because the three answer different questions and a client at 100 / 100 / 17 is in a completely different position from one at 17 / 17 / 100.

**A full figure is complete, not a fault.** Print `complete` beside it. Do not suggest
work to close a gap that is not there, and do not report a hundred per cent as though
something must have been missed.

### Denominators

| Figure | Numerator | Denominator |
|---|---|---|
| In-scope catalog decided | Distinct catalog entries in in-scope disciplines carrying a confirmed row or a `skip` | All catalog entries in in-scope disciplines, restricted to the channels declared for each, **plus one sport row (the timetable file's) per in-scope discipline** — the timetable channel is implied rather than declared, so it is counted for every discipline in scope and never read out of `channels` |
| Client vocabulary matched | Distinct target identifiers appearing as the target of at least one confirmed row | `vocabulary.entries` in `scope.yaml` |
| Feed disciplines in scope | Entries in `in_scope` | Entries in `discipline-index.yaml` |

A catalog entry is one row key as the schema defines it
(`references/spec-schema/01-file-and-keys.md` § *Key model*): a market key on the trading
channel, a stage on the scoreboard channel (with its interval where the stage carries
one), an incident type on the incidents channel, and the one sport row (the timetable
file's) per in-scope discipline on the timetable channel, counted above. A result type, an interval or a
sub-interval is a field of a key; a score or an incident parameter is a parameter of a
row; a code in an enumeration list is a code. None of them is an entry of its own, and an
incident type is one entry however many constrained rows it has.

A row still marked `status: proposed` is **not** decided. It is counted against the first
figure and listed in its own section. Nothing is generated from it, so treating it as
decided would report work as finished that has not been read.

Where `scope.yaml` carries no `vocabulary` block, the second figure is reported as not
measurable, in those words. Not zero — that reads as a failed mapping. Not complete —
that reads as a finished one.

### What is actionable

Within scope, the actionable set is the **undecided** one: entries absent from the
specification without anyone having said why.

**An entry declared skipped is closed**, and **an entry merely missing is a question nobody has answered.** The report keeps the two apart and never adds them together.

**A missing timetable file is undecided in exactly that sense.** An in-scope discipline
whose `beter-feed/mapping/sport-<id>-timetable.yaml` is absent contributes one undecided
entry on the `timetable` channel, keyed `{sport: <id>}`, the same as an absent market row.
Opting out is a skip row inside the file, not the file's absence
(`references/spec-schema/02-targets.md`, *The sport row*).

Catalog entries in out-of-scope disciplines are never undecided. They **contribute no undecided entries** and are not counted at all — the discipline itself carries the single
decision, which appears as one line in the deferred or undeclared section. A codebase
holding two of the disciplines `discipline-index.yaml` carries sees the rest of the catalog in the third figure and
in those two sections, and nowhere else; a row it holds for such a discipline is the failing
case below. This is what stops the undecided set from
being ten thousand entries nobody intends to map.

**Orphan rows and out-of-scope rows fail.** They are the reverse direction: a row whose
sport or key the catalog does not carry, and a row for a discipline that is not in scope, whether
the scope file defers it or leaves it undeclared. Both are declarations contradicting each
other rather than work outstanding, and the report exits non-zero on either. A row whose
sport is absent from `discipline-index.yaml` altogether is an orphan row: the feed describes
no such discipline, so no in-scope, deferred or undeclared line exists for it, and the row
is listed under orphan rows with its own `{sport, channel, key}` and nothing more. A discipline
that is not in scope still appears as its one line in the deferred or undeclared section,
and each of its rows is also an entry under out-of-scope rows: the line does not stand in
for the rows. Each entry has the form orphan rows use, `{sport, channel, key}` with the
row's own key, such as `{sport: 11, channel: incidents, key: {type: 88}}`. A discipline not
in scope that has no rows is that one line and nothing more.

Ambiguous resolutions and collisions each get their **own section** and neither fails.
An ambiguity that was resolved is a decision somebody made under a close call, and the
section exists so a reviewer sees the choices that were close rather than only the ones
that were wrong. A declared collision is a `merge` block someone wrote deliberately; an
*undeclared* collision fails at generation rather than here.

### The report

Printed in the session. It opens with the human-readable form:

```
BETER feed mapping coverage — 2026-08-19
Snapshot 2026-08-14, 7 pages

  In-scope catalog decided       412 / 480    85.8%
  Client vocabulary matched      126 / 126   100.0%   complete
  Feed disciplines in scope        2 / 12     16.7%

  by discipline    sport 2  210 / 240
                   sport 6  202 / 240

  Undecided             68
  Proposed               0
  Ambiguous              4
  Collisions             2   declared
  Orphan rows            1   FAILS
  Out-of-scope rows      0
  Deferred               1
  Undeclared             9
```

and ends with the same content as a block, so a pipeline can read it without parsing
prose:

```beter-coverage
version: 1
generated: 2026-08-19
snapshot: {date: 2026-08-14, pages: 7}
scope:
  in_scope: [2, 6]
  deferred: [11]
  undeclared: [1, 3, 4, 5, 7, 8, 9, 10, 12]
figures:
  in_scope_catalog:     {decided: 412, total: 480, complete: false}
  client_vocabulary:    {matched: 126, total: 126, complete: true}
  disciplines_in_scope: {in_scope: 2, total: 12, complete: false}
by_discipline:
  2: {decided: 210, total: 240}
  6: {decided: 202, total: 240}
sections:
  undecided:
    count: 68
    entries:
      - {sport: 6, channel: trading, key: {marketType: 11, resultType: 6, interval: 1, subInterval: 0}}
      - {sport: 6, channel: timetable, key: {sport: 6}}
  proposed:
    count: 0
    entries: []
  ambiguous:
    count: 4
    entries:
      - {sport: 2, channel: trading, key: {marketType: 5, resultType: 6, interval: 1, subInterval: 0}, chosen: TOTAL_GAMES, also: [TOTAL_POINTS]}
  collisions:
    count: 2
    entries:
      - {sport: 6, channel: trading, target: TOTAL, keys: 2, declared: true}
  orphan_rows:
    count: 1
    entries:
      - {sport: 2, channel: incidents, key: {type: 88}}
  out_of_scope_rows:
    count: 0
    entries: []
  deferred:
    count: 1
    entries:
      - {sport: 11, name: "Basketball", reason: "not traded on our site yet"}
  undeclared:
    count: 9
    entries:
      - {sport: 1, name: "..."}
status: fail
```

All eight sections are always present, with `count: 0` and an empty list where there is
nothing to report. A section that disappears when it is empty makes a reader check
whether the check ran.

`status` is `fail` when `orphan_rows` or `out_of_scope_rows` is non-zero, and `ok`
otherwise. Undecided entries never make it `fail`: they are work outstanding, and a
build that goes red because a mapping is not finished is a build that gets its coverage
check removed.

Where the second figure cannot be measured, that block reads
`client_vocabulary: {measurable: false}` and the human-readable line says
`not measurable — no vocabulary declared in scope.yaml`.

**The report is not committed.** A coverage file in the repository goes stale against the
files it describes within one merge request, and the stale copy is what people then read.
Nothing stores it; it is printed each time, and the block above is what gets printed.

Two things print it, and they are not the same thing. **This skill recomputes it** — from
the scope file, the snapshot and the specification — at step 5 of a mapping session, which
is when the figures can move. **The generated CI check restates it** from constants written
at generation time; generated code takes no YAML parser, so it cannot re-read those files
and does not try. What makes the restatement trustworthy is the generated catalog digest
test beside it: if an input moved, that test fails in the same CI run and the restated
figures are known to be stale. `references/generation-contract/04-tests.md` § *The generated
coverage check* is the detail.

### Adding a discipline changes one column

Bringing a discipline into scope adds a `by_discipline` row and moves the first and
third figures. It does not alter another discipline's `by_discipline` entry, because
each is computed from that discipline's own snapshot and specification files. The `decided`
and `total` pair computed for each discipline in scope is reported in every run, the
untouched ones included. A coverage run after adding a discipline that shows a different
figure for an untouched discipline means something regenerated that should not have.
