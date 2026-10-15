# Catalog: discipline scope and bindings

Part of `references/catalog.md`, which lists every part and when to read it.

## Discipline scope

A codebase carries some of the feed's disciplines and not others, and widens that set
over time. The set is declared, in `beter-feed/scope.yaml`:

```yaml
version: 1

in_scope:
  - {sport: 2,  name: "Table tennis", channels: [trading, scoreboard, incidents]}
  - {sport: 6,  name: "eFootball",    channels: [trading, scoreboard]}

deferred:
  - {sport: 11, name: "Basketball",   reason: "not traded on our site yet"}

vocabulary:
  source: src/Catalog/markets.json
  entries: 126
```

A discipline is in one of three states.

| State | Meaning |
|---|---|
| **In scope** | Mapped, measured, generated. |
| **Deferred** | Seen and declined for now, with the reason recorded. |
| **Undeclared** | Present in the feed and never considered. Nobody writes this state — it is what is left. |

Scope is read from this file and **never inferred from which specification files exist**. A discipline held back deliberately and a discipline nobody has considered are the same absence on disk, and the coverage report has to keep them apart.

**An entry discovery proposed carries two more fields.** Where the repository already
integrated the feed before this skill was installed, `references/discovery.md` proposes
`in_scope` from the code, and each such entry carries `status: proposed` and `evidence`
naming where it was read. The developer confirms by editing `status` to `confirmed` or
removing it; `deferred` is asked and never read from code, because absence in code is not
a decision.

```yaml
in_scope:
  - {sport: 6, name: "eFootball", channels: [trading],
     status: proposed, evidence: "src/Feed/TradingConsumer.cs:14 handles sportId 6"}
```

**Channels are declared per discipline.** A codebase may take trading for a discipline
whose scoreboard it does not render, and an undeclared channel is not extracted, not
measured and not generated.

**The timetable channel is not one of them.** Every in-scope discipline carries it
implicitly, so it is never listed in `channels` — a `timetable` entry there is rejected,
with the message that the channel is implied. Its file,
`beter-feed/mapping/sport-<id>-timetable.yaml`, is written for every in-scope sport and says
which of this system's own disciplines the sport lands in
(`references/spec-schema/02-targets.md`, *The sport row*). A system with no discipline to land it in
opts out in the file, with a skip row carrying the reason: no schedule means no matches,
which means nothing to map. Deferring a discipline deletes its timetable file with the
others.

`vocabulary` is optional and is written at step 3 of mapping mode, when the repository's
own catalog is read. `source` is a path in this repository or a one-line description of
where the vocabulary lives; `entries` is how many distinct target identifiers it holds.
Without this block the second coverage figure is reported as not measurable — never as
zero and never as complete.

**A target row is identified by the key its own source carries.** It is whatever columns the client's own sheet uses to tell one row from another, and those differ from sheet to sheet and from one kind of row to another; read them from the source rather than assuming them. The partner or client name is not part of the key; a developer holds one client's rows, so that dimension is constant and adding it says nothing.

Where the vocabulary already carries its own stable identifier — a database dump, an export whose ids their code already keys on — use that identifier and compose no key at all. It is theirs, it is stable, and it is what their own systems join on.

**Where two rows cannot be told apart by anything the vocabulary carries, stop and report the rows and the columns you tried.** Do not mint an identifier to separate them. A minted id makes the mapping look decided and moves the defect downstream, where it surfaces as two mappings that should differ and do not. What the report is for is the developer telling you which column distinguishes them, or that one of the two rows is a mistake in their sheet.

Scope governs extraction, coverage and generation. Every step that needs to know what
the codebase carries reads this one file, so no two of them can reach different answers.

## Bringing a discipline into scope, and deferring one

**Bringing a discipline into scope** adds it to `in_scope` with its channels, and
extracts its enumerations at that point — not before. Its index entry already exists.
Mapping mode re-enters at step 1 and runs step 3 and generation for that discipline alone.
Steps 4 and 5 still validate every specification file and report every discipline in scope
as its `{decided, total}` pair, as `references/catalog/03-coverage.md` § *Adding a
discipline changes one column* says.

**Deferring one** moves it to `deferred` with a reason, and deletes its
`sport-<id>-<slug>.yaml`. The index entry stays. The reason is not decoration: it is
what the coverage report shows instead of counting that discipline's entries as
undecided, and a deferral without one is indistinguishable from neglect six months
later.

Neither operation touches another discipline's snapshot file, specification, generated
code or coverage figure.

## Bindings

`beter-feed/bindings.yaml` names, per discipline and channel, the existing code that
realises the mapping in a repository that integrated the feed before this skill was
installed. Discovery writes it; the developer confirms it by edit; generation mode reads
it. It is validated against `schemas/beter-bindings.schema.json`, carried inside this
skill as the scaffold's schema is.

```yaml
version: 1
bindings:
  # digest elided here; a real row carries all 64 hex characters
  - {sport: 6, channel: markets, resolver: "src/Feed/MarketMap.cs#Resolve",
     failure: "MarketDecision.Unmapped", policy_site: "src/Feed/TradingConsumer.cs#OnMarket",
     digest: "sha256:3b1f…", status: proposed}
  # planned: the resolver file does not exist yet, so the row carries no digest
  - {sport: 3, channel: markets, resolver: "src/Feed/Sport3MarketMap.cs#Resolve",
     failure: "MarketDecision.Unmapped", policy_site: "src/Feed/TradingConsumer.cs#OnMarket",
     status: proposed}
```

`resolver` and `policy_site` are `<path>#<symbol>`. `digest` is the SHA-256 of the resolver
file's bytes with `\r\n` normalised to `\n` before hashing, written as `sha256:<64 hex>`;
discovery writes it, and every generation that edits the file rewrites it. A row for a
file that exists carries `digest`; a planned row does not, and generation refuses an
existing file with no digest (`references/generation-contract/03-emission.md`, *Adopting
existing code*).

**A binding's channel is the specification's row list.** Scope channel `trading` is bound
as `markets`, `scoreboard` as `stages` and `incidents` as `incidents`; the timetable, which
scope always implies, is bound as `sports`. A `sports` binding names, per discipline, the
code that resolves the feed's sport id for that discipline (the sport resolver or
timetable mapper), its failure value, its policy site, and a digest as for any row.

**A binding may name a file that does not exist yet.** In a repository with bindings,
every in-scope discipline-and-channel pair, channels named by the correspondence above,
carries a binding before generation runs: an existing one, read from the code, or a
planned one. A planned row's `resolver` names the file and symbol generation will create,
following the naming the existing bindings show; its `policy_site` is the one the existing
bindings of that channel share; where they differ, mapping mode asks the developer which
one, in one question in the next `beter-questions` block. Where the existing bindings of
that channel share one file, the new row names that file and carries its digest: it is an
existing binding, not a planned one. On a channel no discipline is
bound for, the `policy_site` is planned too: its named symbol does not exist. Once
generation has created it, it is an ordinary site, where later disciplines add only their
dispatch entries. Discovery and mapping mode Step 1 propose planned rows `status: proposed`, and the
developer confirms by edit, as for any binding. In a repository without bindings, a row
without a binding for its channel is generated as on a fresh repository. A binding that
carries a `digest` and whose file or symbol no longer exists fails generation for that
channel with the path named. Bindings are not conventions and are not re-detected;
bindings never go into `scope.yaml`.

A planned binding names the channel's resolver file and nothing beside it. For that channel
generation creates the files it creates on a fresh repository, plus the dispatch entry at the
recorded `policy_site`, and the `beter-generation` block lists every file written
(`references/generation-contract/03-emission.md`, *Adopting existing code*).
