# Mapping mode: Step 3, import or propose

Part of `references/mapping-mode.md`, which lists every part and when to read it.

Read `references/mapping-mode/03-other-feed.md` with this part: the question about another feed, and
*Scaffolding another feed's mappings*, are there, and both are settled before the first
proposal.

## Step 3 — Import, or propose

The step where the correspondence is established. Its output is a specification file per
discipline per channel group, valid against the schema, with every row either read from
what the developer already had or marked `status: proposed` with its evidence.

What arrives varies. A spreadsheet, a CSV export, a wiki table, a mapping already in
code, a catalog with no mapping at all, or another feed's integration that solved the
same problem in this system's own vocabulary. The sub-sections below cover each.

An existing mapping and another feed's integration are both optional. Before the first
proposal:

1. Ask whether the correspondence is kept anywhere already. Where it is, import it as
   written. Where discovery ran, the rows it read are already in the file, and this
   question covers what the code leaves uncovered: ask it for the remainder only, naming
   the entries still undecided. Where the developer has already named an existing mapping,
   the question names it, so its import has a question to answer.
2. Ask about another feed, below, **in the same batch as the first question**, and never
   put it off for want of an uncovered count — a question put off until more is known is a
   question that is not asked — save where an existing mapping is on the table: rule 3 of
   *Scaffolding another feed's mappings* then holds it behind that import and says what it
   names when it is put. It is left out, or takes another form, where that section says
   so: a scaffold already on disk, every in-scope market covered by what discovery read or
   an earlier import, a decline not asked again, or the permission question for an
   integration in this repository asked in its place.
3. Propose every entry still uncovered: through the scaffold where there is one, and
   otherwise from this system's own vocabulary and BETER's documented description.

Ask the first in the developer's own terms, and take no for a whole answer:

```beter-questions
version: 1
questions:
  - id: q1
    about: "an existing mapping"
    asked: "Do you already keep the correspondence between BETER's markets and your own anywhere — a spreadsheet, an export, a wiki page, a table in the code? I read one as written rather than propose over it. If there is nothing, that is fine: I propose from your own catalog instead."
    blocking: true
```

A session with neither a mapping nor another feed is a whole case rather than a thin one.
The scope is proposed from the catalog and this system's own vocabulary, every row is
reviewed as a proposal, and nothing is blocked by declining either input or by having
neither.

Cite target rows by the key their own source carries (`references/catalog/01-scope.md`, *A target
row is identified by the key its own source carries*). A `target:` naming an identifier the
developer cannot find in their own sheet is not reviewable by them, whatever else is right
about the row.

Two rules hold across all of them.

**Ask rather than choose.** Anything the source form leaves ambiguous is a question, not
a judgement call. A question asked costs a minute; an ambiguity resolved silently
produces a mapping that looks decided and was not, and nobody finds it until a market
settles wrongly.

A doubt written into a row is a question not yet asked. A row whose chosen candidate is
below `high` confidence — whatever put it there: the only candidate found, a name that
does not fit the market it lands on, several that fit — is put in the `beter-questions`
block in the turn the row is written, `blocking: false`, and its `about:` names the entry
the doubt is on by its field and code (`marketType=2`) or its catalog name with the code
beside it (`Total(2)`); a bare name anchors nothing, and this system's own term for the
target (`HGTE`) anchors nothing without the code beside it (`HGTE (marketType=38)`). A row
chosen at `high` confidence is not asked about on this rule, however many candidates it
lists: the ambiguity mark of *Ambiguity* below is the coverage report's, and this question
is the developer's. An answer given about one market's target or outcomes is evidence for
that market's row alone: another row below `high`, rated without that answer, however
alike its shape, is asked on its own code in the turn it is written. "Worth the
developer's own check" inside `evidence` or `chosen_because`, or in prose beside the row,
has asked nothing: the developer's tooling reads the block, and a doubt that lives only in
the row is a judgement call wearing a hedge.

**Never read outside the integration component without asking first.** That includes
another feed's integration, the main application, and anything else in the repository
that is not the component being worked on. It is a wider read than the task implies and
the answer belongs to the developer.

The `beter-questions` block's form, and the rules for asking in batches and for a turn
that waits on the developer, are in `references/mapping-mode/00-questions.md`.

### Reading an existing mapping

The developer already keeps the correspondence somewhere — a spreadsheet, a CSV export, a
wiki table, or a mapping already in code. Read it and produce canonical specification rows
from it.

A row read from what the developer wrote is **not** a proposal. It carries no `status`, no
candidates and no evidence, because the evidence is that they wrote it. Mark only what you
supplied.

A row written from what the developer *answered* is what you supplied. A `skip` transcribed
from a dash once they have said what it means, a `skip` written because they ruled a market
out in reply to a question, or a target they named when asked, is `status: proposed`, with
the answer as its evidence: transcribing is not reading, and the row is reviewed like any
other proposal (`references/spec-schema/04-proposals-and-evidence.md`, *Proposal fields*).
Rows and scope entries that discovery wrote are the exception: each keeps the `status`
`references/discovery.md` gives it. An answer adds a field, with a `comment` naming the
question, to such a row, or `evidence` to such a scope entry, never a `status`, and it
never removes the row: the developer takes a row out, or corrects it, at confirmation.
An answer that disowns the target a literal gives adds nothing to the row: the question
stays in the `beter-questions` block and the row stays as the code has it.
Nor does a field the code does not give and you propose yourself, such as an outcome map
from the catalog or the developer's vocabulary, go on a row discovery read from a literal:
ask for it instead, and the row stays as the code has it until the developer answers.

Source forms differ in what they can express, and the difference is where rows get lost:

| In the source | Means | Do |
|---|---|---|
| A merged cell spanning several rows | One target for several keys, or a heading | Ask which. A spreadsheet cannot say |
| A repeated key in a CSV | Either a one-to-many expansion or a duplicate | Ask. Expansion is `many`; a duplicate is a collision |
| A blank target cell | Either not carried, or not yet decided | Ask. `skip` needs a reason; undecided is an absence |
| A column with no header, or a header that names no dimension | A dimension nobody wrote down | Ask which dimension it is. Never infer it from the values |
| A dash, `n/a`, or `-` in the target column | Usually a declared absence | Ask, then write `skip`, `status: proposed`, with the reason they give |

Every one of those is a question, recorded in the `beter-questions` block. Resolving one
silently produces a row that looks read and was inferred, which is the one thing this
format exists to keep apart.

### A catalog and no mapping: proposing

Some developers arrive with their own catalog and no mapping at all, and ask which entries
correspond.

**Propose. Never decide.** A proposed row is marked, carries the evidence it was proposed
on, and **generates nothing until it is confirmed**:

```yaml
  - key: {marketType: 5, resultType: 6, interval: 1, subInterval: 0}
    status: proposed
    target: {id: TOTAL_GAMES}
    candidates:
      - id: TOTAL_GAMES
        confidence: high
        source: target_catalog
        evidence: "the result type is games, and this entry's own description says games"
      - id: TOTAL_POINTS
        confidence: low
        source: target_catalog
        evidence: "shares the word total and nothing else"
    chosen_because: "TOTAL_POINTS is scoped to points in this system's own description"
```

Step 6 **stops on any row still marked `proposed` and lists them**. Confirmation is the
developer's, and it may cover one row or the whole file: they review the proposals in as
many rounds as they need, correcting rows or saying how to correct them, and then say the
rest are right. On that word — and only on it — write `status: confirmed` to every row
carrying `status: proposed` **in this file** at that moment, and touch nothing else. Never
write `status: confirmed` on your own inference. An answer to a question about a row, an
`in_scope` entry or a binding is evidence for it; only the developer's word that it is
right confirms it.

That is the whole boundary. A proposal accepted without being read is indistinguishable
from an inference, so **accepting one is an edit rather than a silence**.

**The word and the file are compared before Step 6 stops.** A row the developer called
confirmed, decided or settled in the exchange, and that still reads `proposed` in the
file, is named back to them in the stop's question — the sentence in the exchange is not
the edit, and the edit is what the stop reads. Where their word covered the row, write
`status: confirmed` as above; where it did not — "deferred", "leave it", "later" — the row
is still proposed, and the stop says so by name rather than taking the word for the edit.

**A file is written as soon as one row can be proposed.** A row the developer has invited,
or one the evidence settles, goes into its file marked `proposed` in the turn it is
settled, whatever is still open around it. The rows still waiting on an answer are not in
the file — undecided is an absence — and Step 5 reports them. Holding a whole file back
until every market in it is answered leaves the developer nothing to review and Step 6
nothing to stop on; one proposed row and thirty open questions is a file with one row.

**A question that is BETER's to answer withholds no row.** Where the target is settled and
only a part of the row — the outcome map, a sign rule, which participant a code names —
turns on a gap in BETER's own documentation, the row goes into its file now with that part
withheld — absent from the row, as a market row written without `outcomes` is, and listed
undecided by Step 5 — and the question beside it is `blocking: false`: the developer cannot answer it,
so nothing of theirs waits on it. Where the row is put for confirmation, say that the
target is confirmable as it stands and the withheld part follows BETER's answer. A row
held out of the file for a question the developer cannot answer is a silent drop wearing a
comment: the file they review does not carry it, and the coverage report lists it as
undecided.

**A market's outcomes are proposed with the market and asked with it.** Outcome names
are rarely alike across systems — `Over` is `O` here and `12` there — so the map is the
part of a row a developer most often has to answer, and it is answered per market, never
as a sport-wide list: the same code is a different selection under a different term. Put
the market and its outcomes in one question, naming the codes the catalog lists under
that market type and the selections you found on the developer's term:

```beter-questions
version: 1
questions:
  - id: q7
    about: "sport 6 / trading / marketType=2"
    asked: "TOTAL_GOALS: is BETER outcome 12 (Over) your selection O and 13 (Under) your U? Your term lists O and U and nothing else."
    blocking: true
```

Never hand a developer an outcome code on its own. An outcome type alone means nothing to
them: it is the affirmative or negative of whichever market carries it.

A scoreboard target that carries no enumeration is a record, and its states are declared in
the file's `states` table (`references/spec-schema/02-targets.md`, *The five target forms*). Learn the
record from the repository — the record type itself, and the assignments the code already
makes — propose the whole table, and put it to the developer as **one** blocking question
before any stage row is proposed:

```beter-questions
version: 1
questions:
  - id: q1
    about: "sport 6 / scoreboard / states"
    asked: "Your match state is a record (started, ended, open_period, period_number) with no named states. I propose these five assignments as the file's states table: ... Are these the states, and are these all of the record's fields this feed should set?"
    blocking: true
```

Write the table once it is answered. Stage rows then name its labels and go through proposal
and confirmation like any other row. A system that does name its states needs no table: its
stage rows carry `target: {id: ...}`.

An incidents file carries a `cases` block (`references/spec-schema/03-cases-and-collisions.md`, *The `cases`
block*), and none of its three answers can be read from the feed. Read the repository for
each — a sort by index on the consuming side, a handler for retraction types, a match-level
field a per-incident value is written into — say what was found, and settle each case with
the developer as a blocking question before the file is written:

```beter-questions
version: 1
questions:
  - id: q1
    about: "sport 6 / incidents / cases.emission_order"
    asked: "Incidents carry an index within a match. Does your consumer need them delivered in index order by the generated code, or does it order them itself? I found no sort on the consuming side."
    blocking: true
```

Never write `applies` from inference alone: a case is what the developer said it is, and the
`why` of a case that does not apply is theirs.

*Where the evidence comes from*, the three `source` values a candidate carries, is in
`references/mapping-mode/03-other-feed.md`.

### Ambiguity

Where several of this system's entries fit one feed entry, **record every candidate**,
choose one, and **write down why**:

```yaml
  - key: {marketType: 2, resultType: 6, interval: 1, subInterval: 0}
    status: proposed
    target: {id: SET_WINNER}
    candidates:
      - {id: SET_WINNER,   confidence: high,   source: beter_docs,     evidence: "the documented interval is a set"}
      - {id: GAME_WINNER,  confidence: medium, source: target_catalog, evidence: "this system's description says period without saying which"}
      - {id: MATCH_WINNER, confidence: low,    source: target_catalog, evidence: "the only winner market with no period in its name"}
    chosen_because: "the documented interval is the set, and GAME_WINNER is used for the game elsewhere in this catalog"
```

A row carrying two or more candidates is ambiguous, and that is the whole test — nothing
else marks it. The alternative, silently keeping the best match, produces a mapping that
**looks decided and was not**.

Ambiguous resolutions are listed in **its own section of the coverage report**, so a
reviewer sees the choices that were close rather than only the ones that were wrong.

That section reports; it asks nothing. A row whose chosen candidate is below `high`
confidence is put in the `beter-questions` block in the turn the row is written, under *Ask
rather than choose* at the top of this step, and its line in the coverage report's ambiguous
section does not stand in for that question. A row chosen at `high` with several candidates
is listed there and is not asked about on that rule.

A confirmed ambiguous row **keeps its candidates after confirmation**. Deleting them once
the row is settled saves four lines and costs the next reader the knowledge that
**the decision was contested** — which is exactly what they need when the market behind
it settles oddly a year later.
