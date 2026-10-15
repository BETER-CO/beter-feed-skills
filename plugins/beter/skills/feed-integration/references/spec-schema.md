# The mapping specification

One YAML file per discipline per channel group, in this repository, owned by this
repository and read and written by the skill.

```
beter-feed/mapping/
  sport-2-trading.yaml       markets, each carrying its outcomes
  sport-2-scoreboard.yaml    stages and intervals
  sport-2-incidents.yaml     incident types
  sport-2-timetable.yaml     which of this system's disciplines the sport is
```

YAML rather than JSON because the file is reviewed in the normal merge-request process
and comments carry *why* a mapping decision was made. That reasoning is the part that
otherwise leaves with the developer who made it.

## Parts

Read this file and `references/spec-schema/01-file-and-keys.md` whenever a specification file is read,
written or validated. Read each other part when the rows being written need it. Generation reads every part.

| Part | Covers | Read when |
|---|---|---|
| `references/spec-schema/01-file-and-keys.md` | The schema and its copy; *Key model*; *File header*; *Row shape*; *What the schema does not check* | Always, for any specification file |
| `references/spec-schema/02-targets.md` | *The five target forms*; *The sport row*; *The nested form* and its projection; *Value rules*; incident parameter carriage | Writing a row's target or values |
| `references/spec-schema/03-cases-and-collisions.md` | *The `cases` block*; *Targets flatter than the feed*; *Collisions*; *`comment`* | Writing an incidents file, a target flatter than the feed, or a `merge` |
| `references/spec-schema/04-proposals-and-evidence.md` | *Proposal fields*; *Composed rows*; *The scaffold*; *Qualifier classes* | Proposing a row, composing through another feed, writing a scaffold, or a target with qualifiers |
