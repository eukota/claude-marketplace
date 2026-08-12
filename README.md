# Claude Marketplace

Personal marketplace of Claude primitives, bundled into installable plugins.

## What's Here

Plugins live in `plugins/<plugin-name>/`. Each plugin bundles one or more Claude primitives:

- **Skills** — reusable instructions Claude follows on demand
- **Commands** — slash commands for Claude Code
- **Rules** — always-on behavioral rules
- **Hooks** — shell commands triggered by Claude Code events
- **Agents** — specialized subagent definitions
- **MCP Servers** — Model Context Protocol servers

## Plugins

| Plugin | What it's for |
|---|---|
| [`plugin-builder`](plugins/plugin-builder/) | Choosing a primitive, scaffolding a plugin, and following the conventions in this repo. |
| [`context-setup`](plugins/context-setup/) | Personal project context management — structured Markdown + YAML giving Claude persistent memory across sessions and machines. |
| [`meldwerkes`](plugins/meldwerkes/) | Multi-agent cognitive architecture that builds a personalized decision model through PAHF loops, distillation, and multi-brain orchestration. |
| [`plan-usage`](plugins/plan-usage/) | Tracks account rate-limit usage (5-hour and 7-day windows) from the status line and reports whether your plan is the constraint on your work. |

Install any of them with:

```
/plugin install <plugin-name>@eukota-claude-marketplace
```

## Plugin Structure

```
plugins/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json           # metadata: name, version, description, author, primitives
├── README.md                 # usage docs
├── skills/<skill-name>/
│   ├── SKILL.md              # frontmatter with name + description drives selection
│   └── references/           # material the skill consults (not itself a skill)
├── commands/                 # (if applicable)
├── rules/                    # (if applicable)
├── hooks/                    # (if applicable)
├── agents/                   # (if applicable)
├── scripts/                  # supporting executables (if applicable)
└── mcp-servers/              # (if applicable)
```

Two of these are load-bearing rather than stylistic: a skill is only discovered
at `skills/<skill-name>/SKILL.md`, and it is only selected on the strength of
its frontmatter `description`. A flat `skills/<skill-name>.md`, or a `SKILL.md`
without frontmatter, is invisible.

Anything a plugin ships is referenced through `${CLAUDE_PLUGIN_ROOT}` — never an
absolute path, and never a hardcoded install location. See [CLAUDE.md](CLAUDE.md)
for the full conventions.

## Not Sure What to Build?

See the [primitive decision guide](plugins/plugin-builder/README.md#what-should-i-build) in the `plugin-builder` plugin.

## Registry

`.claude-plugin/marketplace.json` lists all available plugins with their versions and paths.

## License

MIT — see [LICENSE](LICENSE).
