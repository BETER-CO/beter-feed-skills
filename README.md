# BETER feed skills

Agent skills for teams integrating the BETER sports data feed. Install them into
your AI coding agent so it answers BETER-specific questions from the official
documentation instead of guessing.

## Skills

| Skill | What it covers |
|---|---|
| `beter-feed-docs` | BETER feed documentation: connection, channels, data contracts, offsets, sandbox, API, changelog. |

## Install — Claude Code

```
/plugin marketplace add BETER-CO/beter-feed-skills
/plugin install beter-feed-docs@beter-feed-skills
```

Update later with `/plugin marketplace update beter-feed-skills`.

## Install — other agents

The skills are plain `SKILL.md` directories and work in any agent that reads the
[Agent Skills](https://agentskills.io/specification) format. Copy the skill
directory into your agent's skills folder:

```bash
git clone https://github.com/BETER-CO/beter-feed-skills
cp -r beter-feed-skills/plugins/beter-feed-docs/skills/beter-feed-docs ~/.claude/skills/
```

Cursor, Codex, and Gemini CLI read `~/.agents/skills/` as well.

## Repository layout

```
.claude-plugin/marketplace.json     marketplace catalog
plugins/<plugin>/
  .claude-plugin/plugin.json        plugin manifest
  skills/<skill>/SKILL.md           skill entry point
  skills/<skill>/references/        supporting reference files
```

## Requirements

The skills read `https://docs.beter.co/public/` at answer time, so the agent needs
a web-fetch tool and network access to that host. No credentials are required — the
documentation is public.

## Contributing

Issues and pull requests are welcome. A skill change should state which question
the agent previously answered wrongly and what it answers now.
