---
name: feed-integration
description: Use when working in a codebase that consumes the BETER sports data feed and the task is the integration itself — declaring which disciplines (sports) are in scope, taking or refreshing a catalog snapshot, importing or writing the mapping between BETER's markets, outcomes, intervals, scoreboard stages and incident types and the codebase's own vocabulary, reporting mapping coverage, or generating the mapping code and its tests. Also use for anything under a `beter-feed/` directory — `scope.yaml`, `catalog/`, `mapping/` — and when a sport, market or incident type is being added to a BETER integration that already runs.
---

# BETER feed integration

Builds and maintains the mapping between the BETER feed's vocabulary and the
repository's own, in the repository that holds the integration.

This file is a router. It classifies the request, loads the one reference file for
that mode, and follows it. Where the mode is not implemented, it says so and stops.

## Before anything else

**Mapping mode depends on the `feed-docs` skill.** Every numeric code and every field
meaning in the feed resolves through that skill: it carries the page map, the
fetching rules and the code-resolution rules, and this skill carries none of them.

Check whether it is available. If it is not, say so and stop:

> Mapping needs the `feed-docs` skill to resolve BETER's codes and field
> meanings, and it is not available in this session. Install the `beter` plugin, which
> carries the `feed-docs` skill, from the `beter-feed-skills` marketplace, the same place
> this skill came from, with your coding tool's own installer, or copy the `feed-docs`
> skill directory beside this one, and run this again.
>
> If this repository's configuration already lists it: **declaring a skill in
> configuration does not install it.**

Do not proceed on a promise to install it afterwards, and do not proceed by fetching
the documentation directly. A mapping built on unresolved codes is worse than no
mapping, because it looks finished.

## Numeric codes are never resolved from general knowledge

The feed identifies almost everything by number: market type, result type, interval,
sub-interval, outcome type, stage, incident type, sport.

Two properties of that numbering decide the rule. The same integer means different
things in different disciplines, and separate enumerations carry overlapping ranges —
a stage code and an interval code can be the same integer on the same page. So a
resolution taken from a plausible-sounding memory does not fail loudly. It **mislabels rather than errors**: the row is written, the code generates, the tests pass, and one
market settles against the wrong result for the rest of the integration's life.

Establish the discipline, then the field, then resolve the code through
the `feed-docs` skill against the page that lists it. A code that page does not carry is
recorded as undocumented and asked about. It is never named.

**A repository that holds a consumer of this feed and no `beter-feed/` directory enters
discovery first, whatever the request:** `references/discovery.md`, loaded from mapping
mode Step 1. Scope, specification and bindings are derived from the code and cited to it,
the developer confirms them, and only then does the requested mode's implemented part run.

## Modes

| The request is about | Mode | Status |
|---|---|---|
| Mapping BETER's markets, outcomes, intervals, stages or incidents onto this repository's vocabulary; what is still undecided | **Mapping** | Implemented — load `references/mapping-mode.md` |
| Bringing this repository's mapping code and tests in line with a confirmed specification under `beter-feed/mapping/` | **Generate** | Implemented — load `references/generation-mode.md` |
| Taking on a sport the business has decided to trade | Add a sport | Not implemented as a mode. Its mapping part is mapping mode at step 1, then generation mode — do those parts, then name what was not done, below. Where the repository has bindings, step 1 is where the sport's planned bindings are proposed |
| A sport already in scope whose feed content has changed | Refresh a sport | Not implemented as a mode. Its mapping part is the refresh procedure in `references/catalog/02-snapshot.md` — do that part, then name what was not done |
| A capability BETER has newly shipped | Adopt new feed features | Not implemented — say so and stop |
| A running integration that is failing: reconnection, recovery, missing or late messages | Diagnose a broken integration | Not implemented — say so and stop |
| An integration that works and needs modernising | Upgrade an existing integration | Not implemented — discovery is its implemented part (`references/discovery.md`); say so and stop after it |
| No integration yet: transport, connection, consumer | Initial integration | Not implemented — say so and stop |

Where the mapping part of a partly-implemented mode has been done, say which part was
done and which was not, in those words. "Sport 12's mapping and generated code are in
place. Booking the sport in the Client Console, filtering it into your timetable
consumer, and whatever your own product needs are not part of what I did."

In a repository that already integrates the feed, adding a sport usually needs work the
specification does not reach: the sport gate or supported-sports list, any per-sport
registration or per-sport behaviour the repository keys by sport outside the bound files (a
container registration, for example), and display names. These are hand work
outside the generated tree, each with its own tests, and never written into a generated
file. Name each in the list of what was not done, with the file it belongs in. That list
follows the `beter-generation` block, never precedes it.

## Stopping is the behaviour, not a failure

A mode marked *not implemented* has no procedure here. Name the mode, say this skill
does not implement it, and route it: the `feed-docs` skill answers documentation questions
about it, and `support@beter.co` takes the rest.

Do not assemble a procedure for it out of what mapping mode does. An instruction file
that tries to cover every case answers the case it has no procedure for from
invention, and an invented integration procedure is, to the reader, indistinguishable
from a designed one. That is the failure this project exists to avoid, and it is why
the unimplemented modes are listed here rather than left out — a mode that is absent
from the list gets improvised.

## What this skill writes

Everything it produces is a file in this repository, rooted at `beter-feed/`:

```
beter-feed/
  scope.yaml                        which disciplines are in scope, deferred, and on which channels
  catalog/                          the snapshot: meta, discipline index, shared codes, per-discipline enumerations
  mapping/                          one specification file per discipline per channel group
  scaffolds/                        one file per other feed whose mappings were scaffolded
  schema/                           a copy of the specification schema, for your pipeline and your editor
```

Generated mapping code and its tests go where this repository's own conventions put
them, not under `beter-feed/`.

## What this skill never does

- **Decide.** It proposes; the mapping is the repository owner's declaration.
  Confirmation is an edit in the repository, so it shows in a merge request.
- **Ask in prose alone.** Every question to the developer, at any step, is recorded in
  a `beter-questions` block (format in `references/mapping-mode/00-questions.md`). A question asked
  without the block has not been asked.
- **Add a dependency.** Mapping is data and branching. Neither the skill nor the code
  it generates takes a third-party library.
- **Read outside the integration component without asking.** Reading another feed's
  integration for evidence is a wider read than the task implies, and the answer
  belongs to the developer.
- **Search from a drive root or the home directory.** Look for files only under the
  repository root, with a bounded depth: a search from a root takes minutes and finds
  nothing the repository does not already hold.
- **Send anything anywhere.** No telemetry. What it reads is seen by the person
  running it and by nobody at BETER.
- **Resolve a code from memory.** See above.

## Checking a file against its schema

Check a written specification (`beter-feed/mapping/`), `beter-feed/bindings.yaml` or
scaffold (`beter-feed/scaffolds/`) file with the shipped helper, not a validation script
of your own. It lives in the `bin/` directory of the
`beter` plugin, which is the directory two levels above the directory
that holds this skill file.
Where your tool reports this file's location, take the directory that holds this
`SKILL.md` as `<path>`; the plugin directory is that path's grandparent, so the helper is at
`<path>/../../bin/validate.py`. Do not search the filesystem for it. Stay in the
repository you are working in and run
`python <plugin dir>/bin/validate.py beter-feed/mapping/<file>.yaml`, falling back to
`node <plugin dir>/bin/validate.mjs beter-feed/mapping/<file>.yaml` when Python is not
available or the Python run prints `MISSING`. The schema is picked from the file's
top-level shape; `--schema mapping-spec|bindings|scaffold` overrides it. It prints one
line per violation, `<json path>: <message>`, and exits 0 when the file is valid, 1 when
it is not, 3 when it could not check at all (a usage error, no such file, no schema
chosen, or a document whose top-level keys match more than one schema: pass `--schema`).
Exit 2 with a `MISSING:` line means that helper's libraries are not installed; then, or
when the helper file is not there (python prints `can't open file`, node prints
`Cannot find module`), try the other helper, and when neither runs, check the file against
the schema file under `schemas/` by hand, reading each `required`, `enum` and
`additionalProperties` rule against the rows, and say in the report that the check was by
hand. The two helpers read
YAML differently (PyYAML is YAML 1.1, js-yaml is 1.2, so an unquoted `on: yes` differs);
write keys and booleans in the schema's quoted or lowercase `true`/`false` form and they
agree on every document this skill writes. Run it once per finished edit of a file, not
after every line changed, and read its output instead of rewriting the check.

## Merging a catalog extraction

Write `beter-feed/catalog/` only through the shipped merge helper, never by editing its
files from fetched text. Like the validate helper, it lives in the plugin's `bin/`
directory; `<plugin dir>` below is the directory two levels above the directory that
holds this skill file. Do not search the filesystem for it. Run
`python <plugin dir>/bin/merge-catalog.py <staging dir> --into beter-feed/catalog [--dry-run] [--refresh]`,
with `--dry-run` to report without writing and `--refresh` when a changelog refresh runs
it, falling back to `node <plugin dir>/bin/merge-catalog.mjs` with the same arguments when
Python is not available or the Python run prints `MISSING`, or when the helper file is not
there. It prints one
`beter-catalog-merge` block and exits 0 when it merged or, with `--dry-run`, computed the
merge; 1 when a file cannot be merged, listed by file and path with nothing written; 2
with a `MISSING:` line when that helper's libraries are not installed; 3 when it could not
run at all. When neither helper ran, or every helper that ran exited 2 or 3, write
nothing. What the `merge` field of the `beter-refresh` block reports for each exit code is
in `references/catalog/02-snapshot.md` § *Refresh*. The merge rules are in
`references/catalog/02-snapshot.md` § *Merging into the committed catalog*.

## Reference files

| File | Load when |
|---|---|
| `references/mapping-mode.md` | The request is mapping. The router for mapping mode; the procedure is in its parts. |
| `references/catalog.md` | Declaring scope, taking or refreshing the snapshot, or reporting coverage. |
| `references/spec-schema.md` | Reading, writing or validating a specification file. |
| `references/generation-contract.md` | Generation mode, in the fresh context the brief opens. Mapping mode never loads it. |
| `references/generation-mode.md` | The request is generation, or mapping mode reaches Step 6. The stop, the handover and the brief. |
| `references/discovery.md` | Step 1 of mapping mode finds a consumer of this feed and no `beter-feed/` directory. The reading rules, the outputs, the report. |

Load the router the request needs, then its parts as the phase table says. They are long, and loading all six to answer a scope question spends the
context the mapping itself needs.

Four of them are routers: `mapping-mode.md`, `catalog.md`, `spec-schema.md` and
`generation-contract.md` each list their parts, kept under `references/<name>/`, what each
part covers and when to read it. The first read is this file and the router the request
needs. A part is read on entering the phase it covers, and not before:

| Phase | Read on entering it |
|---|---|
| Any step of mapping mode | `references/mapping-mode/00-questions.md`: every step asks questions |
| Step 1 — Scope and repository | `references/mapping-mode/01-scope-snapshot.md` and `references/catalog/01-scope.md`; `references/discovery.md` when Step 1 sends you there |
| Step 2 — Catalog snapshot | `references/catalog/02-snapshot.md`; the step itself is in mapping-mode part 01 |
| Step 3 — Import, or propose | `references/mapping-mode/02-import-propose.md` and `03-other-feed.md`; `04-conflicts-qualifiers.md` when an answer conflicts with the documented description, or the target uses qualifiers; `references/spec-schema.md`, its part 01, and the parts the rows need |
| Step 4 — Validate | `references/mapping-mode/05-validate-to-report.md` and `references/spec-schema/01-file-and-keys.md` |
| Step 5 — Coverage | `references/catalog/03-coverage.md` |
| Steps 6 and 7 | `references/generation-mode.md`; the generation contract and its parts only in the fresh context |
| Re-entry | Steps 2 and 4 to 7 as above; no Step 3 part |

A part holds only its phase. Where a part names a section that lives in another part, it
says which, and that part is read then.
