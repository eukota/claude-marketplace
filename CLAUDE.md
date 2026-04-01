# Claude Marketplace — Claude Instructions

This repo is a personal Claude primitives marketplace. Plugins are the unit of distribution. Each plugin bundles one or more Claude primitives.

## Structure

```
.claude-plugins/marketplace.json   # top-level plugin registry
plugins/<plugin-name>/             # one directory per plugin
docs/                              # repo-level documentation
```

## Plugin Conventions

- Directory name is the plugin's canonical name (kebab-case)
- Each plugin has a `plugin.json` with: `name`, `version` (semver), `description`, `author`, `primitives` (array of types included)
- Subdirectories only created if that primitive type is present: `skills/`, `commands/`, `rules/`, `hooks/`, `agents/`, `mcp-servers/`
- Each plugin has its own `README.md`

## Adding a New Plugin

1. Create `plugins/<plugin-name>/`
2. Add `plugin.json` with full metadata
3. Add primitive files in the appropriate subdirectory
4. Register the plugin in `.claude-plugins/marketplace.json`
5. Bump the plugin's version in both `plugin.json` and `marketplace.json` when making changes

## Versioning

Plugins version independently using semver. The top-level `marketplace.json` tracks each plugin's current version.

## Primitive Types

| Type | Directory | Purpose |
|------|-----------|---------|
| Skills | `skills/` | Reusable instructions Claude follows on demand |
| Commands | `commands/` | Slash commands for Claude Code |
| Rules | `rules/` | Always-on behavioral rules |
| Hooks | `hooks/` | Shell commands triggered by Claude Code events |
| Agents | `agents/` | Specialized subagent definitions |
| MCP Servers | `mcp-servers/` | Model Context Protocol servers |
