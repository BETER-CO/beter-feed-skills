# Catalog: snapshot, extraction and refresh

Part of `references/catalog.md`, which lists every part and when to read it.

The reverse-strict rule named under *The first run after discovery* is in
`references/catalog/03-coverage.md`, *What each detector catches*.

## Snapshot, not lookup

The snapshot lives in `beter-feed/catalog/` and is committed:

```
beter-feed/catalog/
  meta.yaml                    when it was taken, from which pages, and the hash of each
  discipline-index.yaml        every discipline the documentation carries — always complete
  shared-codes.yaml            the code lists that do not vary by discipline
  sport-2-table-tennis.yaml    one per in-scope discipline
  sport-6-efootball.yaml
```

Slugs are lowercase and hyphenated, derived from the documentation's own name for the
discipline: `sport-2-table-tennis.yaml`, `sport-6-efootball.yaml`,
`sport-11-basketball.yaml`.

The snapshot covers the disciplines in scope, plus the shared codes. **The discipline index is always extracted in full**, with names and identifiers but without enumerations, so a discipline the codebase does not hold is still visible as available. Three disciplines in scope therefore means three enumeration files and an index of the rest, rather than the whole feed's vocabulary sitting in a repository that maps a fraction of it.

**A catalog bundled inside the skill was considered and rejected.** Skill releases and
documentation changes happen on different cadences, so a bundled copy is stale between
releases and carries no signal that it has gone stale. It would also be a second source
of truth for feed semantics, against the rule that semantics resolve through
the `feed-docs` skill alone — and a mapping built against a stale bundled copy is wrong in
the way that is hardest to see, because the copy and the mapping agree with each other.

A snapshot in the repository is also what makes the mapping reviewable. A merge request
that changes the mapping shows, in the same diff, the catalog it was built against.

### meta.yaml

```yaml
version: 1
snapshot_date: 2026-08-19
changelog_seen: 2026-08-14
source:
  base: https://docs.beter.co/public/
  pages:
    - path: feed/trading-feed/meta-data
      fetched_at: 2026-08-19T08:41:07Z
      sha256: 9d1e4c7a2b6f0358ce41a7bd2f9e0c5183ab74d6e2905fb1cc4e7a3d80b6f215
      provides: [discipline-index, sport-2/trading, sport-6/trading]
    - path: feed/scoreboard-feed/data-contracts-sc
      fetched_at: 2026-08-19T08:41:22Z
      sha256: 4c8a03f5e17b9d62ca0f3e84b5d1927fa6c30e8b74d95f21083ac6e5b9f74d30
      provides: [sport-2/scoreboard, sport-6/scoreboard]
```

`sha256` is over the page's extracted text, **normalised before hashing**: the content
of `<main>` only, decoded as UTF-8, line endings converted to `\n`, trailing whitespace
stripped from each line, and a single trailing newline. Without that normalisation the
hash moves whenever the site's framework changes its hydration payload, and a staleness
detector that fires every week is a staleness detector nobody reads.

`changelog_seen` is the date of the newest changelog entry at the moment the snapshot
was taken. Refresh compares against this rather than against `snapshot_date`, because an
entry published on the snapshot date may have appeared after the extraction ran.

`provides` says which files each page fed. When one page changes, this is what says
which disciplines need re-extracting.

### The first run after discovery

The snapshot taken at discovery is the digest baseline. Drift before adoption cannot be
measured, and an entry the code handles that this snapshot does not publish is expected on
that run: it is reported under `unpublished` in the discovery report, no row is written
for it, and the reverse-strict rule in part 03 does not fire on it. From the next run on, the
rule holds as written.

### discipline-index.yaml

```yaml
version: 1
snapshot_date: 2026-08-19
disciplines:
  - {sport: 2,  name: "Table tennis", slug: table-tennis}
  - {sport: 6,  name: "eFootball",    slug: efootball}
  - {sport: 11, name: "Basketball",   slug: basketball}
```

### sport-&lt;id&gt;-&lt;slug&gt;.yaml

Only the channels declared for that discipline are present.

```yaml
version: 1
sport: 2
name: "Table tennis"
slug: table-tennis
snapshot_date: 2026-08-19

trading:
  market_types:  [{code: 1, name: "..."}, {code: 3, name: "..."}]
  result_types:  [{code: 6, name: "..."}]
  intervals:     [{code: 1, name: "..."}, {code: 2, name: "..."}]
  sub_intervals: [{code: 0, name: "..."}]
  outcome_types: [{code: 1, name: "..."}]
  documented_markets: {match: [{marketType: 2, resultType: 43, interval: 1, name: "..."}]}

scoreboard:
  stages:    [{code: 1, name: "..."}]
  intervals: [{code: 1, name: "..."}]

incidents:
  types:
    - code: 4
      name: "..."
      source: {band: below_1000, code: 1}
      params: [{key: Participant, values: ["1", "2"]}]

unresolved:
  - {field: incident.type, code: 77, looked_on: feed/incident-feed/incidents}
```

Incident types are scoped per discipline and are additionally split by source: types
below 1000 come from one production mode and types from 1000 upward from another, with a
switch between them signalled mid-match by its own incident type. Both bands are
extracted where the documentation lists both, and every entry carries the band it falls
in and the raw source code the documentation gives it. The same logical event reaches a
consumer under two different type codes depending on which source is active, so a
snapshot carrying one band and not the other produces a mapping that is silently half a
mapping.

**The mode names are not recorded.** The incidents page and the incident-sources page
state opposite mappings of the source values to their two mode names, so a name written
into the snapshot would be a coin toss that reads as decided. `band` is derived from the
code and is not in dispute; `code` is what the page states. The mode is description
either way — no specification row keys on it, and two type codes for one logical event
are two rows.

## What a score parameter counts

Incident messages carry scores as delimited strings, and no incident page says what is
being counted. The constant comes from the discipline, and it is per parameter key
rather than per discipline: a sport publishing one result type fixes every score
parameter it carries, and a sport publishing several does not.

| Sport | Parameter key | Counts | How it is known |
|---|---|---|---|
| 2 | `SetScore` | `Points` (5) | read from the parameter's own name against the four result types the discipline publishes |
| 2 | `MatchScore` | `Sets` (6) | read the same way; the two disagree, which is why the table is keyed per parameter |
| 2 | `ScoreHistory` | `Points` (5), one entry per completed set | the history is of the quantity the set score carries |
| 6 | `MatchScore` | `Goal` (1) | the discipline publishes one result type, so no reading is involved |
| 6 | `PeriodScore` | `Goal` (1) | the same |
| 6 | `ScoreHistory` | `Goal` (1) | the same |

A row whose *How it is known* column says *read* is a judgement and may be disagreed
with; a row that says the discipline publishes one result type is transcription. **A
discipline whose result types leave a parameter ambiguous gets a row with no value in
the *Counts* column**, and generation stops on it rather than counting the wrong thing
quietly. Those rows are questions for BETER's trading side, not defaults.

The same constant is what a proposal weighs a bracketed qualifier against. A target term
whose label ends in a parenthetical does not carry whatever the feed's term counted: the
qualifier is read against the whole term name and against what the discipline counts.

`unresolved` holds every code seen on a page whose meaning that page did not give. It is
never empty by omission: a code that could not be resolved is recorded here rather than
guessed, and the coverage report counts it as undecided. An entry leaves `unresolved` once
a staging file carries its code in the list its `field` names, and the merge reports it
under `resolved`. The merge snake-cases each segment of `field` and matches the segments,
singular or plural, against the trailing segments of the file's list paths; the entry
leaves only when exactly one list matches. The forms that resolve are `incident.type`,
`stage`, `trading.interval`, `scoreboard.interval`, `market_type` (or `marketType`),
`result_type`, `sub_interval` and `outcome_type`. The merge also accepts plural segments and bare
list names; write one of the forms above so the field reads the same way everywhere.

## Acquisition is one isolated step

**Extraction is the only step that touches the documentation.** The specification
format, the coverage report and the generators consume the snapshot and know nothing
about where it came from.

This is deliberate. The public feed pages are moving to generation from an internal
entity catalogue, and a machine-readable artifact for integrating teams has been raised
there and deferred rather than ruled out. If one appears it replaces this step and
nothing downstream changes.

### Extracting

Steps 2 to 7 write into a staging directory that starts empty and is not committed, such
as `.beter-fetch/catalog/` under the working directory, and never into `beter-feed/catalog/`.

1. Read `beter-feed/scope.yaml`. If it does not exist, mapping mode step 1 writes it
   first — do not infer scope from what is in the repository.
2. Through the `feed-docs` skill, fetch the pages that carry the discipline list. Write
   `discipline-index.yaml` **complete** — every discipline the documentation names,
   in scope or not.
3. For each in-scope discipline, and for each channel declared for it, fetch the pages
   carrying that channel's enumerations and write `sport-<id>-<slug>.yaml`.
4. Fetch the pages carrying the discipline-independent code lists and write
   `shared-codes.yaml`.
5. Record every page fetched in `meta.yaml` with its fetch time and its normalised hash,
   and set `provides` from which files it fed.
6. Read the changelog page and record the newest entry's date as `changelog_seen`.
7. Write nothing you could not resolve. A code whose meaning no fetched page gives goes
   into `unresolved` with the page you looked on.
8. Merge the staging directory into `beter-feed/catalog/` with the merge script
   (*Merging into the committed catalog*):
   `merge-catalog.py <staging dir> --into beter-feed/catalog`. The first extraction into
   an empty catalog is the same command.

On a first extraction, steps 2 to 7 can go to a fresh helper agent where the runtime you
are running in can start one. Give it `beter-feed/scope.yaml`, the disciplines to extract
when only some are wanted, the staging path, steps 2 to 7 and the file formats above, and
the documentation-access rule in `SKILL.md` § *Before anything else*; it returns the
staging directory. Where the runtime lets you choose its model, a smaller and faster model
class is enough. This session then runs the merge (step 8) and reads its report; the merge,
and anything that needs the developer, stays here. Refresh keeps its own page list in this
session.

Never write an enumeration entry from memory, from a field name, or from another
discipline's list. Codes are namespaced per discipline and the ranges overlap.

### Merging into the committed catalog

The merge script, `bin/merge-catalog.py` in this plugin, is the only writer of
`beter-feed/catalog/`; `SKILL.md` § *Merging a catalog extraction* says how to run it.
It merges each staging file into the committed file of the same name:

- Every list is a union keyed by the entry's identity: `sport` in
  `discipline-index.yaml`, `(field, code)` in `unresolved`, and `code` in every other list,
  except that `documented_markets` rows are keyed by `marketType`, `resultType`,
  `interval` and `subInterval` when present.
- An entry in both keeps its committed value, except that a changed `name` follows the
  documentation; any other field keeps its committed value and is reported under `changed`.
- An entry only in the staging file is appended to the end of its list. A staging file
  with no committed counterpart, such as a discipline just brought into scope, is added whole.
- `meta.yaml` is merged too: `source.pages` is a union keyed by `path` in which the staging
  record wins for a path it carries, `snapshot_date` takes the later of the two dates,
  `gaps` and `absences` are unioned by exact string, and a value the staging file lacks or
  leaves empty keeps its committed value. `changelog_seen` advances only under `--refresh`,
  which Refresh step 6 passes; an extraction of a discipline
  (`references/mapping-mode/01-scope-snapshot.md` § *Step 2 — Catalog snapshot*, the row
  for a snapshot missing a discipline) never passes it, because it has not read the
  changelog for the others. A staging `meta.yaml` that is empty or not a mapping, or a
  merged `changelog_seen` later than the merged `snapshot_date`, stops the merge.
- Every other scalar, such as `version`, `name`, `slug` and `snapshot_date` in a
  discipline file, follows the staging file, and each one that moves is reported under
  `scalars` with its old and new value.

A code can vanish from the documentation, but a code is never reused for a different
meaning. **A refresh therefore never deletes an entry**, except that an `unresolved` code
leaves once it is resolved; a kept entry whose code the feed no longer sends is harmless,
because nothing arrives under it, while a deleted one would turn a page that lost rows for
a day into an orphan-row failure for every specification row mapped to it. A kept in-scope
entry that no row maps stays undecided in the coverage report until a skip row settles it.

## Refresh

The change signal the documentation publishes is a dated changelog page.

1. Read `snapshot_date` and `changelog_seen` from `meta.yaml`.
2. Fetch the changelog page and take the **entries dated after** `changelog_seen`.
3. Entries that name only out-of-scope disciplines are dropped. An entry naming no
   discipline is treated as in scope, because a change to the shared codes or to a
   contract affects everything. This is what keeps refresh noise proportional to what
   the codebase carries rather than to how fast the feed grows.
4. If any entry remains, re-fetch the pages that `provides` associates with the in-scope
   disciplines and with the index, extract them into a staging directory as *Extracting*
   does, and run the merge script with `--dry-run --refresh` for its `beter-catalog-merge`
   report.
5. Report per discipline every section of the `beter-catalog-merge` report: entries
   added, renamed, changed, absent from the docs, resolved and scalars, then files added
   and files not in staging. Say which class each change is in. A code whose *name*
   changed is the same code and needs no mapping change. An entry absent from the docs is
   kept, and nothing arrives under it. An entry the report lists under `changed` keeps its
   committed value; name the field that differs. A file the report lists under
   `files_not_in_staging` was not re-fetched and is untouched.
6. Write the merged snapshot only when the developer says so, by running the merge
   script again with `--refresh` and without `--dry-run`. A snapshot replaced silently
   destroys the diff the merge request would have shown, and that review is what this
   design rests on. A write changes the bytes of `meta.yaml` and of every file whose
   entries or scalars moved, so the generated catalog digest test fails and the next
   generation run stops with `blocked_by_catalog_drift`
   (`references/generation-contract/03-emission.md` § *The catalog digest*). The Python
   and Node helpers indent and quote YAML differently, so a file one of them rewrites may
   change layout as well as data.

Refresh ends by emitting this block, whatever it found:

```beter-refresh
version: 1
snapshot_date: 2026-08-14
changelog_seen: 2026-08-14
entries_after_snapshot: 3
entries_in_scope: 0
disciplines_changed: []
absent_from_docs: 0
merge: skipped
stale: false
```

`stale` is true when at least one in-scope entry survives the filter in step 3.
`entries_after_snapshot` counts before the filter and `entries_in_scope` after it, so
the block shows both that the changelog moved and that the movement did not touch this
codebase. `absent_from_docs` counts the committed catalog entries the re-fetched pages no
longer list, never `gaps` or `absences` strings, and is 0 when step 4 did not run. `merge`
is `ok` when a merge helper exited 0, whether it wrote or ran as a dry run; `refused` when
it exited 1 and wrote nothing; `not_run` when neither helper ran or the helper file is not
there, or every helper that ran exited 2 or 3; and `skipped` when step 4 did not run.
