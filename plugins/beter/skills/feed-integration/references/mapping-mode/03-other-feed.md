# Mapping mode: Step 3, evidence and another feed

Part of `references/mapping-mode.md`, which lists every part and when to read it.

Step 3 continues here from `references/mapping-mode/02-import-propose.md`; *the blocking question above*
and *the offer below* refer to questions in this part.

#### Where the evidence comes from

Three sources, all of them inside this environment.

| `source` | What it is |
|---|---|
| `target_catalog` | This system's own catalog: entry names, descriptions, example payloads, and the code already handling them |
| `beter_docs` | BETER's documented description of the feed entry, resolved through the `feed-docs` skill |
| `other_integration` | This team's existing integration with another feed: in this repository, or scaffolded under `beter-feed/scaffolds/` from one they point at |

The third is the strongest. A team that has already integrated another sports feed has
answered, in their own vocabulary, the questions this mapping asks: how a handicap line is
carried, how a period is named, which incidents they model and which they discard, how a
parameter value is converted. That mapping runs **from an external vocabulary into this system**,
which is the direction this one runs. It is an analogue, not an answer.

Two conditions hold on it, and neither is optional.

**Ask before reading anything outside the integration component.** That is a wider read
than the task implies and the answer belongs to the developer. Ask once, name the path,
and record it as a blocking question:

```beter-questions
version: 1
questions:
  - id: q1
    about: "permission: src/Integrations/OtherFeed"
    asked: "This repository holds an integration with another feed at src/Integrations/OtherFeed. May I read it? It maps an external vocabulary into your own, which is the direction this mapping runs, so it is the strongest evidence available for a proposal."
    blocking: true
```

If the answer is no, propose from the other two sources and say what that costs — nothing
else changes, and no row is left unproposed because permission was refused.

**A proposal grounded there names the integration it was inferred from**, so a reviewer can
**check the analogy rather than trust it**:

```yaml
    candidates:
      - id: CORRECT_SCORE
        confidence: medium
        source: other_integration
        integration: "src/Integrations/OtherFeed/MarketMap"
        evidence: "that integration maps its own exact-score market to this entry"
```

Another provider's market can carry a scope that looks identical and is not, and that is
exactly the mistake this evidence makes easy.

A row whose chosen target rests on such a candidate is a composition: it also carries the
`composed` block that *Composing through another feed's integration* gives below, because
that block is the only record that the row inherited the other feed's scope limits. A
candidate that only corroborates a target found elsewhere does not.

#### Scaffolding another feed's mappings

That integration is as often in another repository as in this one, and what it maps is
worth having either way. Where Step 1 found it in this repository, its path is known: ask
the blocking question above, naming the path, once and in place of the offer below, in the
batch rule 3 gives the offer — the two are never both asked. Neither a yes nor a no
brings the offer back: a yes permits the read and the scaffold exactly as an answer to
the offer does, a no is a decline, and a question left unanswered stays in the block as
owed. The offer is for an integration whose location is not known.
**Before the first proposal**, settle it once:

1. `beter-feed/scaffolds/` already holds a file — use it. Do not ask, and do not read its
   source again. Scaffold again, overwriting the file, only when the developer asks for a
   refresh.
2. No scaffold, and what has already been imported covers every in-scope market — the
   offer is spent, as said under the offer below. There is nothing left for a second hop to answer.
   Covered is a decided row for each in-scope market as the import states it, a target
   row or a skip row with its reason; a row's missing outcome map does not uncover it,
   and the rows discovery read count. Where nothing was imported and discovery read
   nothing, nothing is covered, and the question below is asked for the whole scope.
3. Otherwise ask once. An existing mapping — the developer's own correspondence, never
   another feed's mapping file — is on the table where the developer has named it, in the
   brief, in answer to the question about an existing mapping, or unasked, and its rows
   are not yet read. With none on the table, the offer goes in the first batch, beside the
   question about an existing mapping. With one on the table, the offer is held behind
   that import: the turn that holds it says so in prose and puts nothing in the block for
   it, because a held offer is not yet asked. The hold ends in the turn that reads the
   import's rows: the held offer goes first in that turn's batch, so the eight-question
   cap never pushes it out, naming the count and the entries still undecided at that
   turn, since the import's own questions may leave rows undecided and only decided rows
   cover; where the import covers every
   in-scope market, it is not put at all. Otherwise it is settled as for the offer in the
   first batch. A "no" to the question about an existing mapping, or a declined import,
   takes the mapping off the table, and the held offer is put in that same turn for
   everything still uncovered. Put the offer as what it is worth rather than as what it
   is: in the first batch, as below, it names the count, and no entries.

```beter-questions
version: 1
questions:
  - id: q2
    about: "another feed's integration"
    asked: "Does your system already integrate another sports feed? 34 of the 51 markets in scope are not answered by anything I have. If you point me at that integration's checkout, or at the mapping file it was built from, I can scaffold its mappings and propose those markets more precisely. I read it and write nothing into it."
    blocking: false
```

Name the uncovered count as it stands when the question is put. In the first batch, where
no existing mapping is on the table and the question about one is still open beside the
offer, that is every in-scope market discovery left undecided — the rows discovery read
cover, and put no mapping on the table: say so, and say that an existing mapping lowers
it. An offer stated as a capability is declined; an offer stated as the markets it would
answer is a decision the developer can make. Where the reply to the question about an
existing mapping names an existing mapping, the offer already put in the first batch
stands with its count as put: the offer already put is never put again, and an answer
the same reply gave the offer waits on that import as rule 3 holds an offer, and is then
taken for what the import leaves uncovered. An unanswered offer stays in the block as
owed, as any non-blocking question does, with its count as put. Where whatever was
imported or discovery read covers every in-scope market, whether the offer was put, held
or not yet due, the offer is spent: say so in a sentence and open nothing on its account.
A question already put is dropped from the block when the offer is spent. Nothing is
read on the spent offer's account; a checkout or mapping file named for one row's
evidence is still read for that row alone, as the paragraph after next says.

The developer naming a checkout or a mapping file in answer to this offer is the permission
to read it: no second question is put, and nothing under it is opened before that answer.
A developer who declines is not asked again — propose from the other two sources and say
what that costs.

A checkout or mapping file the developer names at any other point — in answer to a question
about one row's evidence, or unasked — is not that answer. Where what was imported covers
every in-scope market, read it for the row the question was about and nothing more: what
it shows is cited on that row as a candidate from another integration is, and no scaffold is
written from it, because a scaffold answers the markets nothing else covers. Where a
scaffold already stands, the scaffold is read, not its source again. Otherwise naming it
is the permission above: read it and scaffold it as for an answer to the offer. Rule 3
holds the offer only: a checkout or mapping file named here, and the row question it was
named for, are taken in the turn they arrive, whether or not an existing mapping is on
the table.

Another feed's mapping file they already have is read in preference to code: it is the same knowledge
already extracted, and reading it is cheaper and surer. A checkout with no such file is
read as code. Either way the read is **read-only** — nothing is written into that
repository, and no code is copied out of it. Only the scaffold is written, and only where
the offer calls for it.

Write what was found to `beter-feed/scaffolds/<feed-name>.yaml`, one file per other feed,
in the form `references/spec-schema/04-proposals-and-evidence.md` gives under *The scaffold*. Then report one
paragraph — how many rows, the key they are on, the scope limits found, and what could not
be resolved — and go on to the proposals. **The scaffold is evidence, not a decision.**
Nothing in it is confirmed, because the rows derived through it are confirmed like any
other row.

Where the path is unreachable or holds nothing, say so once, write no scaffold, and go on
with the other evidence. Where it holds more than one feed, ask which of them matter and
write one file per feed. Where a mapping file is in a form that cannot be read whole, take
what is readable and put the rest under `unread` with its location. Where the developer
declines, go on with the other evidence and do not ask again in this session.

**Nothing read leaves this machine.** There is no telemetry. What is read to make a
proposal is seen by the person running this and by nobody at BETER.

And no material from anywhere else is used. What this carries is **generalised naming heuristics**
— distilled patterns, not data. There is **no table taken from any client or partner**, in this
skill or behind it.

### Composing through another feed's integration

Where a mapping from another feed into this system's own vocabulary is at hand — a
scaffold under `beter-feed/scaffolds/`, or another feed's mapping held in this repository — a
correspondence can be derived in two hops — BETER to that feed, documented on both sides,
then that feed to this system, which this team already wrote — and the two
**collapsed into one direct mapping before anything is generated**.

Composition is a derivation technique and nothing more.
**The generated code makes no runtime hop**: it carries the collapsed result, and the
intermediate appears in the specification as provenance rather than in the code as a step.

```yaml
  - key: {marketType: 6, resultType: 6, interval: 1, subInterval: 0}
    status: proposed
    target: {id: CORRECT_SCORE}
    candidates:
      - {id: CORRECT_SCORE, confidence: medium, source: other_integration,
         integration: "beter-feed/scaffolds/other-feed.yaml",
         evidence: "other-feed documents this market against BETER's, and that feed's mapping lands it on CORRECT_SCORE"}
    chosen_because: "derived through other-feed, which carries interval and result kind, so neither dimension was dropped"
    composed:
      through: other-feed
      hops:
        - {from: beter, to: other-feed, source: "documented on both sides"}
        - {from: other-feed, to: target, source: "beter-feed/scaffolds/other-feed.yaml, MarketMap.cs:41"}
```

The second hop's `source` is where the row was actually read: the scaffold file and the
row's own `at:`, or the path of another feed's mapping held in this repository.

Two constraints, and neither bends.

**The intermediate must carry every dimension the target needs.** Before any row is
proposed or composed through the intermediate, read its own key — `key_shape` in a
scaffold, the own key of another feed's mapping held in this repository — and compare its arity
with the target's. Where the intermediate is flatter, say so and stop, and a developer's
invitation, encouragement, or offer to confirm rows composed through it does not lift the
refusal: taking that offer confirms a target that dropped a dimension without the
developer knowing it.

> Composition through <name> is refused. Its key carries a market and a choice only, so it
> **drops period and result kind by construction**. Composing through it cannot restore what
> the first hop discarded, and the result would be **wrong in the cases hardest to notice** —
> the rows that look right and settle the wrong period. Propose these rows from the
> documented description instead.

Substitute the intermediate's own name for `<name>`. The refusal is stated once, in those
terms, in the turn where the intermediate would otherwise have been used — also when the
outcome is that the keys it would have covered stay unmapped, and the session continues on
the other evidence sources. A key left unmapped without that sentence is a silent drop.

**Once the refusal is stated, the refused intermediate is no candidate source.** A key it
would have covered takes its candidates from the documented description
(`source: beter_docs`), this system's own enumeration (`source: target_catalog`) and any
other intermediate whose key carries every dimension (`source: other_integration`, the row
composed through that one); it cites no candidate drawn from the refused intermediate and
carries no `composed` block through it. A name the developer reads off the refused
intermediate is the developer's word in their answer, not a candidate: where the target
catalog or the documented description carries that name, the row takes that candidate and
the answer is recorded in its `chosen_because`; where neither carries it — a name their
vocabulary does not list — the key stays unmapped and the coverage report lists it among
the undecided entries.

**Where a scaffold that was not refused answers a key, its candidate is put to the
developer by name.** A question about that key names the scaffold's target beside the
vocabulary candidates — "other-feed lands this market on `Correct Score`, a name your
vocabulary does not list" — so the developer decides between readings they were shown, and
a row they then invite is composed whichever of them they choose. A question that shows
only the vocabulary rows leaves the second hop unseen: the developer declines a reading
nobody offered, and the key stays unmapped or lands flat. The mark follows the candidate,
not the memory of it: every row whose chosen candidate carries `source: other_integration`
is written with its `composed` block in the same edit, and a note listing the composed
rows is read back from the file, never kept in the head.

**A composed row is marked composed and names both hops**, exactly two of them, and the
mark survives confirmation. A row whose target was read out of a placed scaffold that was
not refused is a composed row whatever else supports it: the developer's word that the
name is real, or the target catalog listing it, adds evidence to the row and does not make
it a flat one. Write `composed` with both hops on the row itself, not the scaffold's path
inside an evidence string. A composed row carries a risk of its own — the scope decisions
it inherited are not visible on the row itself — so that is what has to reach the
developer before they answer for it:

> **A composed row is confirmed like any other row in its file.** A composition inherits
> the intermediate provider's scope decisions, so say so where the rows are put to the
> developer — name the provider, and what its scope decisions were — a scaffold records them under `scope`
> — and let them answer for the file they are reading. Say it in the turn that lists the
> rows for confirmation, in the words the scaffold uses under `scope`, one line per entry:
> a developer who confirms the file without having read those lines has answered for a
> scope they never saw. The sweep does not reach across to
> another file, so a composition reviewed in one file cannot confirm anything in a second.

That is the same risk the single-row case carries, now carried by every row the sweep
lifts at once, which is why the provider and its scope decisions are named rather than
left implicit: the developer confirming the file is answering for that inherited scope,
not only for the row's own mapping.

Name what could not be resolved in the same place, once. A scaffold's `unread` entries are
markets this evidence does not answer, and the developer reading the file is the person who
can say whether that matters.
