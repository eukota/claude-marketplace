---
name: scaffold-plugin
description: Scaffolds a new Claude marketplace plugin — creates the directory structure, plugin.json, README, primitive subdirectories, and registers it in marketplace.json.
---

# Scaffold a New Marketplace Plugin

## Overview

Create a complete plugin scaffold in the `claude-marketplace` repo. This means:

1. Collecting the plugin metadata from the user
2. Creating `plugins/<plugin-name>/` with the right subdirectories
3. Writing `plugin.json` with full metadata
4. Writing a starter `README.md`
5. Registering the plugin in `.claude-plugin/marketplace.json`
6. Committing the scaffold

## Repo Location

The marketplace repo is at `~/Development/claude-marketplace`. All paths below are relative to that root.

## Step 1: Gather Metadata

Ask the user for (one at a time, only what's missing):

- **Plugin name** — kebab-case, becomes the directory name. Before accepting it,
  run `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/namecheck.py <name>` and report the
  result. If it comes back TAKEN or crowded, say so and offer alternatives —
  compounds fare far better than single words, however obscure.
- **Description** — one sentence, what does this plugin do?
- **Primitives** — which types does it include? (skills, commands, rules, hooks, agents, mcp-servers). Can be one or many.

If they've already used `choose-primitive` and know what they're building, skip straight to confirming the name and description.

## Step 2: Create Directory Structure

Create `plugins/<plugin-name>/` with only the subdirectories that match the declared primitives:

```
plugins/<plugin-name>/
├── plugin.json
├── README.md
├── skills/          # only if primitives includes "skills"
├── commands/        # only if primitives includes "commands"
├── rules/           # only if primitives includes "rules"
├── hooks/           # only if primitives includes "hooks"
├── agents/          # only if primitives includes "agents"
└── mcp-servers/     # only if primitives includes "mcp-servers"
```

Each included subdirectory gets a `.gitkeep` so it's tracked by git.

## Step 3: Write plugin.json

```json
{
  "name": "<plugin-name>",
  "version": "0.1.0",
  "description": "<description>",
  "author": {
    "name": "Darrell Ross"
  },
  "license": "MIT",
  "primitives": ["<primitive1>", "<primitive2>"]
}
```

Start at `0.1.0` — `1.0.0` is reserved for when the plugin is considered stable.

## Step 4: Write README.md

```markdown
# <plugin-name>

<description>

## Primitives

<For each primitive type, a brief section explaining what's included — leave as TODO placeholders if content isn't known yet.>

## Usage

TODO
```

## Step 5: Register in marketplace.json

Add an entry to the `plugins` array in `.claude-plugin/marketplace.json`:

```json
{
  "name": "<plugin-name>",
  "version": "0.1.0",
  "source": "./plugins/<plugin-name>",
  "description": "<description>",
  "license": "MIT",
  "author": {
    "name": "Darrell Ross"
  }
}
```

## Step 6: Commit

```bash
git add plugins/<plugin-name>/ .claude-plugin/marketplace.json
git commit -m "Scaffold <plugin-name> plugin"
```

## Output

Tell the user:
- What was created (directory structure, files)
- The next step: add actual content to the primitive files
- Offer to help write the first primitive if they're ready
