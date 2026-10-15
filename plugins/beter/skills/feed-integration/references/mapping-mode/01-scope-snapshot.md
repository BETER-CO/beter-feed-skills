# Mapping mode: Steps 1 and 2, and adding a discipline

Part of `references/mapping-mode.md`, which lists every part and when to read it.

The `beter-questions` block's form is in `references/mapping-mode/00-questions.md`.

## Step 1 — Scope and repository

Establish which disciplines and which channel groups, and write
`beter-feed/scope.yaml`. The file format, the three states and the rule that scope is
declared rather than inferred are in `references/catalog/01-scope.md`.

**A consumer of this feed already in the repository changes the order.** Where the
repository detection below finds one and no `beter-feed/` directory exists, load
`references/discovery.md` and follow it before asking anything about scope: it asks
permission, reads the integration read-only, and proposes the scope, the rows and the
bindings from the code with every row cited. Return here at Step 2 with the scope
discovery proposed; the discovery turn still ends with the `beter-discovery` block
described in `references/discovery.md`, *What discovery reports*, whatever steps follow.
Where `beter-feed/` exists, or no consumer is found, continue as written.

Where `beter-feed/bindings.yaml` exists, this step proposes a planned binding,
`status: proposed`, for every in-scope discipline-and-channel pair without one
(`references/catalog/01-scope.md`, *Bindings*).

Ask rather than infer. "Which sports do you take from BETER?" has an answer the
developer knows; guessing it from what is in the repository produces a scope file that
looks declared and was not. Ask per discipline which channels they take — a codebase
often takes trading for a sport whose scoreboard it does not render. For a discipline
discovery proposed, the developer's answer about its channels is appended to that
`in_scope` entry's `evidence`, after the code citation, and a channel the answer names
that the code does not show is added to the entry's `channels`; the entry keeps
`status: proposed` (`references/discovery.md`), and no answer makes it a declaration. A
discipline discovery did not find follows the declaration rule above.

Every question this skill asks the developer — here, and at every later step: scope,
channels, the timetable answer, an existing mapping, permission to read wider, a
proposal — is recorded in a `beter-questions` block at the end of the turn that asks it,
in the form shown under Step 2. Prose alone is not a question asked: a turn that asks in
prose and emits no block has asked nothing, and the developer's tooling has nothing to
answer.

Then, for each discipline in scope and before the repository is detected, write its
timetable file. **Ask, per sport, in this system's own terms** — "which of your
disciplines does BETER sport 6, eFootball, land in?" — and do not infer it from label
similarity: an e-prefixed name resembling the feed's is evidence for a candidate, not an
answer. A row proposed from a single strong candidate still carries `status: proposed`
and is confirmed like any other row. A system that keys nothing on sport says so, and the
row records that as a skip with the reason.

Then detect the repository:

| Detect | How | Used for |
|---|---|---|
| Language | Build and manifest files, then the source tree | Which generator idiom applies |
| Test runner | The manifest's test dependency and the existing test directory | Where generated tests go and how they run |
| Naming, error style, file layout | Read the existing integration code | Generated code that looks like the code around it |
| An existing integration with another feed | Its presence only — do not read it yet | Step 3, and only after asking |
| A consumer of this feed | The feed's key fields together on one type, a host under `beter.co`, the feed's own names (`references/discovery.md`, *The precondition*) | Whether discovery runs first |

An integration with another feed is as often in a different repository as in this one.
Nothing outside this repository is looked for here. Step 3 asks, and the developer names
the checkout or the mapping file.

Where the repository is empty and has no conventions to follow, state the conventions
you chose rather than choosing silently.

Record no conventions in `scope.yaml`: they are re-detected each run, because they change.

## Step 2 — Catalog snapshot

Ensure a snapshot exists and is current for the disciplines in scope, and that the
discipline index is complete. Extract or refresh per `references/catalog/02-snapshot.md`.

Three cases:

| State | Do |
|---|---|
| No `beter-feed/catalog/` | Extract |
| A snapshot missing a discipline that is now in scope | Extract that discipline only; leave the others alone |
| A snapshot covering everything in scope | Refresh — read the changelog entries dated after `changelog_seen` and filter by scope |

Refresh emits its `beter-refresh` block whether or not anything changed. A refresh that
prints nothing is indistinguishable from a refresh that did not run.

## Adding a discipline

**Adding a discipline re-enters at step 1**, because scope changes.

1. The discipline moves into `in_scope` in `scope.yaml`, with its channels, and its
   timetable file is written at that same step — the timetable answer is asked for the
   new discipline exactly as it was for the first ones. Where `beter-feed/bindings.yaml`
   exists, its planned bindings are proposed at that same step, as Step 1 says.
2. Its enumerations are extracted (step 2), and only its.
3. Step 3 runs **for that discipline alone**; Steps 4 and 5 cover every specification file
   and the whole scope, as their own sections and the paragraph below say; then generation
   mode, which regenerates that discipline alone.

Disciplines already in scope keep their specifications and their generated code, **are not
regenerated**, and **their `by_discipline` entry is still their `{decided, total}` pair,
counted from their own files**.
The first and third overall figures move, because the denominators grew.

This is the frequent operation. Codebases open with two or three disciplines and widen
from there, so the path that adds one has to be cheap and has to leave the rest alone.
A run that regenerates an untouched discipline produces a diff nobody can review, and an
unreviewed diff on settlement code is what this design exists to prevent.
