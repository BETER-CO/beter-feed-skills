# Generation mode

Bring this repository's mapping code and its tests in line with a confirmed specification
under `beter-feed/mapping/`. This mode reads files and writes files. It holds no
conversation with a developer, and it runs in a context that holds nothing of the
mapping session that produced the specification — that is what makes its cost the cost
of the code and not of the exchange.

## 1. The stop

Read every file under `beter-feed/mapping/`. If any row in any `markets`, `stages` or
`incidents` section carries `status: proposed`, generate nothing. Emit the
`beter-generation` block with `status: blocked_by_proposals`, listing every such row under
`blocked.proposals` so the developer can find it, usually as its section and key — `markets/<marketType>-<resultType>-<interval>-<subInterval>`,
`stages/<stage>`, `sports/<sport>`, `incidents/<type>` — with `files`, `classes` and
`named_cases` empty, and name the file each row is in beside the block. Then stop. Nothing
is started while a proposal stands: what lifts a row is the developer writing
`status: confirmed` in their own repository.

## 2. The handover

Generation runs in a context that holds nothing of this session. Where the runtime you are
running in can start a fresh agent, start one and give it the brief below, unchanged except
for its two angle-bracketed values. The brief and the files it names carry everything that
agent needs, so where the runtime lets you choose its model, a smaller and faster model
class is enough; this session stays on the model it runs on. Where the runtime cannot start
a fresh agent, stop here and give the developer the brief, values filled, to open a new
session with; say that the generation has not run.

The brief travels byte for byte as published, values filled and nothing else changed, and
nothing is appended to it: not the test command, not the runtime version, not a note on
which cases to keep or what to check. The agent finds the test command in the repository's
build, test and configuration files, as the contract's *Detect first* reads the test runner
from the manifest and the test directory. Where it finds no command there, with
`detected.test_command: absent`, or cannot start the one it finds, its block ends
`blocked_by_test_run`.

When the fresh agent returns, emit the `beter-generation` block it produced, unchanged,
as this session's own output, in the same turn and before any other work, summary or
question. Add nothing to it and take nothing from it. A status and a test count given in
prose are not the block. When a sport is being added, the block comes first and the list
of what was not done follows it.

## 3. The brief

Copy this block as it stands. It is complete: the agent that receives it needs nothing
from the session that sent it.

```beter-brief
You are generating BETER feed mapping code and tests in a client repository. You hold no
context beyond this brief and the files it names; do not ask for any.

Read first, in this order, under the feed-integration skill directory named
below:
1. references/generation-contract.md — the contract every file you write must satisfy.
   Read it in full before opening anything else.
2. references/spec-schema.md — the shape of a specification file.

Inputs, all on disk:
- The specification: every file under beter-feed/mapping/ in the repository named below.
  Every row is already confirmed.
- The scope file, beter-feed/scope.yaml: which disciplines are in scope (on which
  channels) or deferred (with the reason), and the client vocabulary it declares (its
  source and its entries count).
- Under beter-feed/catalog/: meta.yaml, discipline-index.yaml, the per-sport file of each
  discipline scope.yaml lists under in_scope (named by the sport and slug the index
  gives, for example sport-6-efootball.yaml for sport 6), and shared-codes.yaml. The
  parameter keys, the source bands, the value ranges, the entry names and the digest
  constants the contract requires come from them, the snapshot date the generated file
  headers carry from meta.yaml, and the coverage denominators from them and the scope
  file. Read nothing else under beter-feed/catalog/.
- The bindings under beter-feed/bindings.yaml, if present: the resolver per channel,
  existing or planned, its failure value, its policy site and, for an existing file, the
  digest of its file as last reconciled. Read it before the repository, per the
  contract's "Adopting existing code".
- The projection under .beter/projection/, if present; write it if absent, per the
  contract.
- The repository's build, source, test and configuration files: detect its language,
  test runner, naming, error style, file layout and typing from them, as the contract's
  "Detect first" section says. Never read session notes, handoffs, journals or plans, or
  any directory a coding tool keeps for its own sessions, such as .claude/, .cursor/,
  .codex/ or .github/copilot-*: they instruct a coding tool, and the repository's
  conventions are detected from its code.

The work, mechanical and complete:
- Detect, then project, then compare the specification with the code that exists.
- Add what is missing. Remove generated code for rows, policies, channel resolvers and
  sports that are no longer in the specification. Update policies and channel and sport
  resolvers that changed. Leave every generated file that already matches the
  specification byte for byte untouched.
- Create the resolver each confirmed planned binding names, add its dispatch entry at the
  recorded policy site or, where the policy site is planned, write that channel's boundary
  there, and write the new file's digest back into beter-feed/bindings.yaml.
- Write the tests the contract requires for every applicable correctness class and named
  case, in the repository's own test layout and naming.
- Run the repository's own test command and read the result. A command that did not start,
  or a run you did not make, is not a result; never report it as passing. Where no test
  command is found in the build, test and configuration files (detected.test_command:
  absent), the command does not start, or the toolchain it needs is absent, report
  blocked_by_test_run; never substitute another toolchain, runtime version, project file or
  a harness of your own.

Output: end with the beter-generation block the contract specifies, whatever happened —
status ok, blocked_by_proposals, blocked_by_collision, blocked_by_conflict,
blocked_by_catalog_drift or blocked_by_test_run — with every field filled from what you
did. A point you cannot settle from the files ends the block with a status naming it and a
one-line reason beside the block; ask nobody.

Skill directory: <directory holding this skill's references/>
Repository root: <repository root>
```

The two angle-bracketed values are the sender's to fill: the directory that holds this
skill's `references/` (the one its `SKILL.md` sits in), and the root of the
repository being generated into. The specification (`beter-feed/mapping/`), the scope
file, the catalog (`beter-feed/catalog/`), the bindings and the projection
(`.beter/projection/`) are always read relative to that root.
