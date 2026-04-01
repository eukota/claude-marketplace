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

## Plugin Structure

```
plugins/<plugin-name>/
├── plugin.json       # metadata: name, version, description, author, primitives
├── README.md         # usage docs
├── skills/           # (if applicable)
├── commands/         # (if applicable)
├── rules/            # (if applicable)
├── hooks/            # (if applicable)
├── agents/           # (if applicable)
└── mcp-servers/      # (if applicable)
```

## Registry

`.claude-plugins/marketplace.json` lists all available plugins with their versions and paths.

## License

MIT — see [LICENSE](LICENSE).
