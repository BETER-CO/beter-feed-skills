# Mapping mode: questions to the developer

Part of `references/mapping-mode.md`, which lists every part and when to read it.

Read at every step that asks a question. Where the rules below say 'this step', read Step 3.

Every question asked — in this step as in every other — is recorded in the block emitted
at the end of the turn that asks it:

```beter-questions
version: 1
questions:
  - id: q1
    about: "sport 2 / trading / marketType=3"
    asked: "Your TOTAL entry takes a line. Does it take one entry per line, or one entry with the line as a parameter?"
    blocking: true
  - id: q2
    about: "sport 2 / incidents / type=1001"
    asked: "This type resolves by Participant. Do you model home and away points separately?"
    blocking: false
```

`blocking: true` means no row can be written until it is answered. `blocking: false`
means a row was written and the answer would change it. Both are recorded; the block is
always emitted, with an empty list when nothing was ambiguous. A turn that ran discovery
(`references/discovery.md`) emits its `beter-discovery` block in that turn as well,
whatever it found.

**Ask in batches.** A block carries at most eight questions, grouped by what they are
about — one market, one dimension, one source form — and the rest wait for the turn after
the answers come back. Twenty questions put at once are answered worse than five put four
times: a developer who cannot see the end of the list stops reading it, and an answer given
to get through the list is not a decision. When questions are held back, say how many.

**A turn that waits on the developer ends with the block** that says what it waits for.
"I'll hold here until that comes back", with no block beneath it, is a session nobody can
resume: a reader cannot tell which answers are owed, and a developer who returns has
nothing to answer to. What is owed is a question, and it belongs in the block, `blocking:
true`, however many times it has been asked before.
