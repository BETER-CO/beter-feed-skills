# Mapping mode

Seven steps. Run them in order the first time. After that, most sessions re-enter part
way — see *Re-entry* at the end.

Do not start until the `feed-docs` skill is available. `SKILL.md` says what to do when it is
not.

## Parts

Read this file, then `references/mapping-mode/00-questions.md`, at the start of mapping mode. Read each
other part on entering the step it covers, and not before: a part holds one phase's
procedure, and a step that has not started needs none of it.

| Part | Covers | Read when |
|---|---|---|
| `references/mapping-mode/00-questions.md` | The `beter-questions` block, batching, and a turn that waits on the developer | Always: every step asks questions |
| `references/mapping-mode/01-scope-snapshot.md` | Step 1 — Scope and repository; Step 2 — Catalog snapshot; *Adding a discipline* | A first run, a discipline being added, or Step 2 on re-entry |
| `references/mapping-mode/02-import-propose.md` | Step 3's opening and its two rules; *Reading an existing mapping*; *A catalog and no mapping: proposing*; *Ambiguity* | Entering Step 3 |
| `references/mapping-mode/03-other-feed.md` | *Where the evidence comes from*; *Scaffolding another feed's mappings*; *Composing through another feed's integration* | Entering Step 3, with part 02: the question about another feed goes in the first batch, or after the import of an existing mapping on the table, and not at all where the import covers every in-scope market; a no or a declined import puts it in that same turn |
| `references/mapping-mode/04-conflicts-qualifiers.md` | *An answer that conflicts with the documented description*; *A target that identifies outcomes through a bag of qualifiers* | A developer's answer conflicts with BETER's documented description, or the target identifies outcomes through qualifiers |
| `references/mapping-mode/05-validate-to-report.md` | Step 4 — Validate; Step 5 — Coverage; Step 6 — Generate; Step 7 — Run and report | Step 3 is done, or on re-entry. Steps 4 and 5 run in the turn that completes Step 3, or in the re-entry turn, before the developer's review of the proposed rows; that review is Step 6's stop. |

## Re-entry

**Re-entry is steps 2 and 4 through 7**, with the specification edited rather than
imported. Adding markets later is the frequent case and it is this path: someone edits
`beter-feed/mapping/sport-2-trading.yaml`, runs the skill, and gets a refreshed
snapshot check, validation, coverage, then generation mode for the regenerated code and
its test run.

Step 3 is skipped because there is nothing to import. Step 1 is skipped because scope
has not changed.

Regeneration is deterministic: the same specification and the same snapshot produce the
same code, byte for byte. A re-entry that changes files nobody edited is a defect —
report it rather than committing it.
