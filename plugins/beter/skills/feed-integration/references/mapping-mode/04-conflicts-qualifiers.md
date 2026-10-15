# Mapping mode: Step 3, conflicting answers and qualifier bags

Part of `references/mapping-mode.md`, which lists every part and when to read it.

Step 3 continues here from `references/mapping-mode/02-import-propose.md`.

### An answer that conflicts with the documented description

The developer's word settles what a term means in their own system. It does not settle what
the feed sends. Where the developer names a term for a feed entry and BETER's documented
description of that entry says something else — an incident documented as the end of a set,
and a term of theirs that means a change of match status — there is a conflict, and both
sides of it can be sincerely held.

State the conflict in the turn the answer arrives, before anything else about that entry:

- the documented description, quoted, and where it was read;
- their term, and what their own vocabulary says it means;
- what writing their term would do, in one sentence — every message of that type would
  reach the code that handles that term.

Then ask which of the two is off: the term, or their reading of the entry.

```beter-questions
version: 1
questions:
  - id: q9
    about: "sport 2 / incidents / type=1010"
    asked: "BETER documents 1010 as 'Set-finished — conclusion of a set on a referee command'. You gave MATCH_STATUS, which your vocabulary describes as a change of the match's status. Writing MATCH_STATUS sends every set end to your match-status handling. Is 1010 something other than the documentation says in your experience, or is the term a different one?"
    blocking: true
```

Until they answer, the row stays `proposed` on the documented reading, with their term
recorded as a candidate and their own words as its evidence. Do not move the target to
their term because it was given with confidence, and do not demote the documented reading
to a guess: a row switched quietly reads as agreement, and the developer learns of the
mismatch in production. If they answer that their term is what they want, knowing what the
feed documents, write it — it is their system — and keep both candidates on the row. If
they say they will check and come back, the row stays as it is, `proposed`, and the
coverage report lists it among the ambiguous ones.

### A target that identifies outcomes through a bag of qualifiers

Some systems identify an outcome partly through a bag of qualifiers — a set of key and
value pairs whose keys vary from market to market — rather than through a single
identifier. Which keys exist, which markets carry which of them, and which outcome
identifiers are references to a competitor or a player rather than members of an
enumeration are properties of one system, published nowhere, and unknowable before looking
at it.

So this is not a mapping step that begins by knowing the shape. **Read the target and state
what you found**, then map around the answers. The structure is not a preliminary to the
work: **the structure is the outcome and the rows follow from it**.

#### Report what you found

Four things, all four, whether or not each one turned out to be interesting:

| Report | Read it from |
|---|---|
| **which qualifier keys exist** | Every distinct key across the target's market descriptions and its parsing code |
| **which markets carry which of them** | The per-market key set, and where it varies within one market |
| **which of them bear identity** | Whether the market description lookup uses the key, and whether two outcomes differ only in it |
| Outcomes that are **entity references rather than enumeration members** | An outcome identifier resolved against a competitor or player list rather than a fixed set |

State it plainly, as a finding rather than a conclusion: how many keys, which markets vary,
which resolve as entity references, and what each of those means for the key this
specification will use.

#### Ask about what you could not settle

**Ask about what you could not settle** rather than assuming it. A key that appears on two
markets out of forty either matters or is vestigial, and the target's code cannot say which.
Record each as its own question:

```beter-questions
version: 1
questions:
  - id: q1
    about: "qualifiers: variant"
    asked: "variant appears on three of your forty markets and never changes the outcome set. Does it distinguish two outcomes that would otherwise be the same, or is it there for display?"
    blocking: true
  - id: q2
    about: "qualifiers: presenter"
    asked: "presenter carries a competitor reference rather than a value from a fixed list. Does the outcome's identity depend on which competitor, or is it context on an outcome that is already identified?"
    blocking: true
```

#### Record the two classes separately

The **identity-bearing and context qualifiers are recorded separately** in the
specification, under `qualifiers`. See *Qualifier classes* in `references/spec-schema/04-proposals-and-evidence.md`
for the block. `qualifiers` is the only key a target adds beside `id` for such a
refinement, on an incident row as on any other — not an ad hoc field like `incident_type`.

Write the block whenever the target has a qualifier bag, however its structure became
known: read out of the target's code, settled by the developer's answers, or already
stated in the vocabulary the developer handed over. A structure the developer supplied
saves the questions, not the record: the specification is the one place the two classes
are kept apart.

Record the structure whole: every qualifier key and every entity-reference outcome you
found, including those on terms that map to nothing currently in scope. An unmapped term is
still evidence about the bag, and an entity-reference outcome cannot be re-derived from the
rows.

Every identity entry is written `confirmed: false` and asked about, however plainly the
lookup code seemed to settle it. Only the developer's answer — in the exchange, or in their
final review of the files — turns it `true`. A key that looked like identity from the code
alone is a finding to report, not a confirmation to write.

They are separated because mapping a context qualifier into the key **produces rows that
never match**: the generated resolver builds a key that includes it, the feed produces a
key that does not, and every message for that market falls through to the unmapped policy.
That failure is loud in production and invisible in review, which is the worst combination
this format can produce.

#### Nothing generates on an unsettled key

**A key the developer did not confirm generates nothing.** A qualifier whose class is still
open leaves every row that uses it marked `proposed`, and step 6 stops on it like any other
proposal. A context key the developer will not settle stays a context entry with its `note`;
moving it to `identity` to mark it open parks a key the evidence calls context in a class
awaiting confirmation, and a later `true` would generate rows that never match. The
specification and its surrounding boilerplate are produced around the answers that came
back — not around the answers that would have been convenient.
