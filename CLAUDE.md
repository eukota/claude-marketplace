# Claude Marketplace — Claude Instructions

This repo is a personal Claude primitives marketplace. Plugins are the unit of distribution. Each plugin bundles one or more Claude primitives.

## Structure

```
.claude-plugin/marketplace.json    # top-level plugin registry
plugins/<plugin-name>/             # one directory per plugin
  .claude-plugin/plugin.json       # plugin manifest (canonical location)
  skills/<skill-name>/SKILL.md     # one directory per skill
docs/                              # repo-level documentation
```

## Plugin Conventions

- Directory name is the plugin's canonical name (kebab-case)
- Each plugin has a manifest at `.claude-plugin/plugin.json` with: `name`, `version` (semver), `description`, `author`, `primitives` (array of types included). This location is what Claude Code discovers; a copy at the plugin root is optional and informational only.
- Skills are directories: `skills/<skill-name>/SKILL.md`, with supporting material in `skills/<skill-name>/references/`. A flat `skills/<skill-name>.md` is **not discovered** and the skill will never be selected.
- Every `SKILL.md` opens with YAML frontmatter containing `name` and `description`. The `description` is the only thing Claude matches on when deciding whether to use the skill — state the trigger condition, not just the capability. A skill without frontmatter is unselectable.
- Reference material a skill consults is **not** a skill. Put it in that skill's `references/` directory so it is not competing for selection.
- Subdirectories only created if that primitive type is present: `skills/`, `commands/`, `rules/`, `hooks/`, `agents/`, `mcp-servers/`; `scripts/` for supporting executables
- Each plugin has its own `README.md`

## Adding a New Plugin

1. Create `plugins/<plugin-name>/`
2. Add `plugin.json` with full metadata
3. Add primitive files in the appropriate subdirectory
4. Register the plugin in `.claude-plugin/marketplace.json`
5. Bump the plugin's version in both `plugin.json` and `marketplace.json` when making changes

## Git

- `git add`, `git commit`, and `git push` are all pre-approved — no need to confirm
- Never `git push --force`

## Versioning

Plugins version independently using semver. The top-level `marketplace.json` tracks each plugin's current version.

## Primitive Types

| Type | Directory | Purpose |
|------|-----------|---------|
| Skills | `skills/<name>/SKILL.md` | Reusable instructions Claude follows on demand |
| Commands | `commands/` | Slash commands for Claude Code |
| Rules | `rules/` | Always-on behavioral rules |
| Hooks | `hooks/` | Shell commands triggered by Claude Code events |
| Agents | `agents/` | Specialized subagent definitions |
| MCP Servers | `mcp-servers/` | Model Context Protocol servers |

## Portability

Plugins must run on a machine that is not yours.

- Never reference an absolute path or a personal directory. Use
  `${CLAUDE_PLUGIN_ROOT}` for anything shipped inside the plugin — scripts,
  references, assets. It is set for hooks, commands, and skills alike.
- Do not hardcode an install location. Plugins install under
  `~/.claude/plugins/cache/<marketplace>/<plugin>/<version>/`, which is a path
  no plugin should ever write down.
- Do not depend on another plugin, or on a repo that lives outside the
  marketplace. If two plugins need the same code, the code belongs in whichever
  plugin owns it, reached through that plugin.
- User data written at runtime belongs under `$HOME`, with an environment
  variable to override the location.

## Performance

Anything that runs on a hot path — status lines, `SessionStart` hooks,
`UserPromptSubmit` hooks — pays its cost on every render or every message.
Prefer one subprocess doing all the work to several doing one field each;
a status line calling `jq` per field costs several hundred milliseconds a
redraw.
