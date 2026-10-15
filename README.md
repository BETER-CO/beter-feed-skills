# BETER feed skills

Agent skills for teams integrating the BETER sports data feed. Install them into
your AI coding agent so it answers BETER-specific questions from the official
documentation instead of guessing.

## Skills

| Skill | What it covers |
|---|---|
| `feed-docs` | BETER feed documentation: connection, channels, data contracts, offsets, sandbox, API, changelog. |
| `feed-integration` | Building the integration: which sports are in scope, the catalog snapshot, the mapping between BETER's markets, outcomes, intervals, stages and incidents and your own vocabulary, coverage, and the generated mapping code and tests. |

## Install — Claude Code

Both skills ship in one plugin, `beter`. Install it in the repository that holds your
feed integration rather than for your whole account. `feed-integration` reads and
writes files in the repository it runs in, a feed integration is normally its own
service, and a repository-scoped install keeps the skills out of every unrelated
session.

Commit this to that repository as `.claude/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "beter-feed-skills": {
      "source": { "source": "github", "repo": "BETER-CO/beter-feed-skills" }
    }
  },
  "enabledPlugins": {
    "beter@beter-feed-skills": true
  }
}
```

Each developer working in that repository then installs the plugin, scoped to the
repository, into their own AI coding tool from this marketplace — for example, in
Claude Code:

```
claude plugin marketplace add BETER-CO/beter-feed-skills
claude plugin install beter@beter-feed-skills --scope project
```

The skills are then installed as `beter:feed-docs` and `beter:feed-integration`.
Update later with `/plugin marketplace update beter-feed-skills`.

**Committing the settings file does not install the plugin.** Current versions
report a plugin declared this way as missing and print the install command above.
A repository that commits only the settings file gets nothing. The install is also
where each developer is shown the warning that the plugin comes from a source
outside their organisation, which is a decision that belongs to them.

**Scope decides which repositories pay the cost, not whether there is one.** An
enabled skill's description loads in every session in that repository so the model
can judge whether the skill is relevant; the body and the reference files load only
when the skill is actually used. Installing per repository keeps the description out
of sessions that have nothing to do with the feed.

`feed-integration` needs `feed-docs` beside it, and the plugin carries both. Every
numeric code in the feed resolves through `feed-docs`, and mapping mode stops without it.

### Upgrading from the first release

The plugin `beter-feed-docs@beter-feed-skills` is replaced by `beter@beter-feed-skills`,
which carries the same documentation skill as `feed-docs`.

- If you installed `beter-feed-docs` for your whole account, uninstall it:

  ```
  claude plugin uninstall beter-feed-docs@beter-feed-skills
  ```

  Then install `beter` in the repository that holds your feed integration, as above.
- If you installed it in one repository, replace the
  `"beter-feed-docs@beter-feed-skills": true` key in that repository's
  `.claude/settings.json` with `"beter@beter-feed-skills": true`, and install again
  with `--scope project`, as above.

Only repository-scoped installs are offered from now on.

## Install — other agents

The skills are plain `SKILL.md` directories and work in any agent that reads the
[Agent Skills](https://agentskills.io/specification) format. Copy the skill
directories into the skills folder of the repository that holds your feed integration,
not into your home folder: the skills are for that repository alone, and a user-wide
copy loads their descriptions into every session on the machine. From the root of
that repository:

```bash
git clone https://github.com/BETER-CO/beter-feed-skills /tmp/beter-feed-skills
mkdir -p .claude/skills .claude/bin
cp -r /tmp/beter-feed-skills/plugins/beter/skills/feed-docs .claude/skills/
cp -r /tmp/beter-feed-skills/plugins/beter/skills/feed-integration .claude/skills/
cp /tmp/beter-feed-skills/plugins/beter/bin/*.py /tmp/beter-feed-skills/plugins/beter/bin/*.mjs .claude/bin/
```

Both skills run helpers from the `bin/` directory of the plugin, which is two levels
above each skill's own directory: `feed-docs` runs a documentation fetcher, and `feed-integration`
runs a schema validator and a catalog merge. Copy them into a `bin/` folder beside your
skills folder, as the last line does, so that `bin/` and `skills/` sit side by side as
they do in the plugin. That `bin/` folder then holds both skills' helpers. Without the
validator and the merge, `feed-integration` checks each file against its schema by hand
and says so in its report, and it writes nothing to `beter-feed/catalog/`, which only the
merge helper writes.

Cursor, Codex, and Gemini CLI read the repository's `.agents/skills/` as well; a skill
copied there takes its helpers in `.agents/bin/`.

Other tools do not read the marketplace manifest, so there is no install command for
them and no update command either — copying the skill directories and the helpers again
is the update.

## Repository layout

```
.claude-plugin/marketplace.json     marketplace catalog
plugins/beter/
  .claude-plugin/plugin.json        plugin manifest
  bin/                              helpers the skills run, and their tests
  skills/feed-docs/SKILL.md         documentation skill entry point
  skills/feed-docs/references/      the documentation page map
  skills/feed-integration/SKILL.md  integration skill entry point
  skills/feed-integration/references/
                                    supporting reference files
  skills/feed-integration/schemas/  JSON Schemas the skill validates against
```

## Requirements

`feed-docs` reads `https://docs.beter.co/public/` at answer time, so the agent
needs a web-fetch tool and network access to that host. No credentials are required —
the documentation is public.

The documentation is not indexed for search, so an agent cannot find it by looking.
The skill carries the page map, which is most of what it is for.

`feed-integration` fetches nothing itself. Every feed code and field meaning it
needs resolves through `feed-docs`, so keep the two together and the same network
access covers both.

`feed-integration` checks and merges files with its own helpers. The validator needs
Python with `pyyaml` and `jsonschema` (version 4 or later), or Node with `js-yaml` and
`ajv` (version 8). The catalog merge needs only `pyyaml` or `js-yaml`. Nothing is
installed for you; the Node helpers look for their libraries from the directory they run
in, then beside the helper, then through `NODE_PATH`. A helper whose libraries are missing
prints a `MISSING:` line and exits 2, and the skill then tries the other helper. When
neither validator runs, the skill checks each file against its schema by hand. When
neither merge helper runs, it writes nothing to `beter-feed/catalog/`.

## Contributing

Issues and pull requests are welcome. A skill change should state which question
the agent previously answered wrongly and what it answers now.
