---
name: local-context-setup
description: Sets up the personal context management system on a new machine — creates the context directory, project index, and per-project structure, then wires CLAUDE.md to read them. Invoke explicitly; it writes a directory tree under the user's home.
---

# context-setup: local-context-setup

Set up the Inception personal context management system on this machine.

## Trigger

Invoked as `/context-setup:local-context-setup`. Do not activate unless explicitly invoked.

## Process

### Step 1: Gather Inputs

Ask these two questions one at a time. Wait for each answer before asking the next.

**Question 1 – Name:**
> "What's your name? (used as the owner field in project metadata)"

**Question 2 – Context directory:**
> "Where should your context directory live?"
> 
> This will be your **primary context store** – the directory Claude reads at the start of every session to understand your current projects and priorities. It can live anywhere on your machine.
> 
> Common choices: `~/context`, `~/.context`, `~/my-context`
> 
> Where would you like it?"

Store answers as:
- `USER_NAME` – the user's name
- `CONTEXT_DIR` – the full expanded path (resolve `~` to the real home directory path)

---

### Step 2: Check for Existing Directory

If `CONTEXT_DIR` exists and is non-empty:
- Show the user what's already there (one-level listing)
- Ask: "This directory already exists and contains files. Continue and skip any files that already exist? (y/n)"
- If the user says no, stop. Tell them they can re-run `/context-setup:local-context-setup` anytime.

If `CONTEXT_DIR` is empty or does not exist, proceed.

---

### Step 3: Create Directory Structure

Create these directories:

```
{CONTEXT_DIR}/projects/_template/notes/
{CONTEXT_DIR}/projects/inception/notes/
{CONTEXT_DIR}/projects-archived/
{CONTEXT_DIR}/team/
{CONTEXT_DIR}/integrations/
{CONTEXT_DIR}/notes/
```


### Step 4: Write Files

Write each file below. Skip any that already exist – do not overwrite.

In all content: replace `{CONTEXT_DIR}` with the actual path, `{USER_NAME}` with the user's name, and `{DATE}` with today's date in `YYYY-MM-DD` format.

#### `{CONTEXT_DIR}/README-FIRST.md`

```markdown
# Inception Context System

Your AI assistant's persistent memory store.

## What This Is

This directory gives your AI assistant organized, persistent access to your working context – across sessions, tools, and machines. Your assistant reads it at session start and knows what you're working on without you having to repeat yourself.

## Directory Map

| {CONTEXT_DIR}/ |
|---|
| README-FIRST.md | This file |
| CLAUDE.md | AI session instructions |
| _index.yaml | Generated index (do not edit by hand) |
| generate-index.sh | Rebuilds _index.yaml from project.yaml files |
| project-lifecycle.md | Status and lifecycle definitions |
| projects/ | Copy this to start a new project |
| ├─ _template/ | Copy this for new projects |
| ├─ inception/ | One folder per active project |
| projects-archived/ | Completed or abandoned projects |
| team/ | Team member profiles |
| integrations/ | How external tools are connected to this system |

## Key Workflows

| Task | What to do |
|---|---|
| New project | Copy `projects/_template/` → `projects/{slug}`, fill `project.yaml` |
| Rebuild index | Run `./generate-index.sh` from this directory |
| Session notes | Write to `projects/{slug}/notes/YYYY.MM.DD.topic.md` |
| Archive a project | Move `projects/{slug}/` → `projects-archived/{slug}/`, rebuild index |
| Update status | Edit `project.yaml`, run `./generate-index.sh` |

## About integrations.md

Each project can have an optional `integrations.md` alongside its `README.md`. Use it for links to external systems – repo URL, ticket board, chat channel, docs. Keeping these separate from `README.md` lets the `README` stay focused on goals and decisions.

## For the AI

Your context directory is `{CONTEXT_DIR}`. All project context lives here. Read it before asking the user to repeat themselves.

## Finding Projects

1. **Project index:** `{CONTEXT_DIR}/_index.yaml` – lists all active projects with status
2. **Project details:** `{CONTEXT_DIR}/projects/{slug}/project.yaml` (metadata) and `README.md` (goals, decisions)
3. **Session notes:** Write to `{CONTEXT_DIR}/projects/{slug}/notes/YYYY.MM.DD.topic.md`
4. **Archived projects:** `{CONTEXT_DIR}/projects-archived/{slug}/`

## Directory Layout

{CONTEXT_DIR}/
├─ _index.yaml
├─ generate-index.sh
├─ project-lifecycle.md
├─ projects/
│  ├─ _template/
│  │  ├─ {slug}/
│  │  │  ├─ project.yaml
│  │  │  ├─ README.md
│  │  │  ├─ integrations.md
│  │  │  └─ notes/
│  │  └─ inception/
│  │  │  ├─ project.yaml
│  │  │  ├─ README.md
│  │  │  ├─ integrations.md
│  │  │  └─ notes/
│  └─ {slug}/
│     ├─ project.yaml
│     ├─ README.md
│     ├─ integrations.md
│     └─ notes/
├─ projects-archived/
├─ team/
├─ integrations/
└─ notes/

## project.yaml Schema

Every project folder contains a `project.yaml` with this schema:

```yaml
name:           Human-readable project name
slug:           lowercase-hyphenated, matches folder name
status:         latent | idea | exploring | proposal | active | paused | done | cancelled
tags:           [freeform strings]
priority:       critical | high | medium | low | none
eisenhower:     Q1 | Q2 | Q3 | Q4
owner:          your name
created:        YYYY-MM-DD
updated:        YYYY-MM-DD
links:
  repo:         # ticket board, project management tool
  board:        # Slack, Discord, Teams, etc.
  channel:      # wiki, Notion, Confluence, etc.
  docs:         
related:        [slugs of related projects]
search_terms:   # Keywords that appear in external notes when writing about this project
  - "Project Name"
summary: >
  One paragraph description of what this project is and why it matters.

context:
  plugins:      # Claude plugins active for this project
  skills:       # Claude skills active for this project
  rules:        # Behavioral rules for this project

workspace:
  folders:      # Local paths to repos, e.g. ~/Development/my-repo
```

## The Index

`_index.yaml` is generated by `./generate-index.sh`. It contains a flat list of all active projects with their name, slug, status, tags, priority, and updated date.

Your AI reads this file first to get a project overview, then drills into individual `project.yaml` + `README.md` for whichever projects are relevant to the session.

Never edit `_index.yaml` by hand. Run `./generate-index.sh` after any project changes.

## Lifecycle

See `project-lifecycle.md` for full definitions.

| Status | Meaning |
|---|---|
| `latent` | Seed idea, not yet worth a folder. Lives in notes or a quick list. |
| `idea` | Worth tracking, not yet started. |
| `exploring` | Actively investigating – research, spikes, conversations in progress. |
| `proposal` | Formal proposal or design doc is being written or reviewed. |
| `active` | Current work. In your regular rotation. |
| `paused` | Blocked or deprioritized. Not abandoned, but not active. Note the reason. |
| `done` | Complete. Move to `projects-archived/` and rebuild the index. |
| `cancelled` | Abandoned. Move to `projects-archived/` and rebuild the index. |

## Transitions

- `latent` → `idea`: You decided it deserves a tracked folder
- `idea` → `exploring`: You started investigating
- `exploring` → `proposal`: Investigation produced a design worth proposing
- `proposal` → `active`: Proposal accepted; work begins
- `active` → `paused`: Work stopped but project is still alive
- `paused` → `active`: Work resumed
- `active` → `done`: Work is complete
- any → `cancelled`: Project is abandoned

## Archiving

When a project reaches `done` or `cancelled`:
1. Update `status` in `project.yaml`
2. Move the project folder to `projects-archived/{slug}/`
3. Run `./generate-index.sh` to update the index

Archived projects are preserved – their notes and decisions remain queryable.

---

## generate-index.sh

```bash
#!/bin/bash
# Rebuilds _index.yaml from projects/*/project.yaml (active) and
# projects-archived/*/project.yaml (archived).
# Usage: ./generate-index.sh

CONTEXT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECTS_DIR="$CONTEXT_DIR/projects"
ARCHIVED_DIR="$CONTEXT_DIR/projects-archived"
INDEX_FILE="$CONTEXT_DIR/_index.yaml"

echo "generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$INDEX_FILE"

project_count=0
entries=""

for project_yaml in "$PROJECTS_DIR"/*/project.yaml; do
  [ -f "$project_yaml" ] || continue
  dir=$(dirname "$project_yaml")
  slug=$(basename "$dir")

  name=$(grep "^name:" "$project_yaml" | head -1 | sed 's/name: //')
  status=$(grep "^status:" "$project_yaml" | head -1 | sed 's/status: //')
  priority=$(grep "^priority:" "$project_yaml" | head -1 | sed 's/priority: //')
  updated=$(grep "^updated:" "$project_yaml" | head -1 | sed 's/updated: //')
  tags_line=$(grep "^tags:" "$project_yaml" | head -1 | sed 's/tags: //')

  project_count=$((project_count + 1))
  entries="$entries
  - slug: $slug
    name: $name
    status: $status
    tags: $tags_line
    priority: $priority
    updated: $updated"
done

archived_count=0
archived_entries=""

if [ -d "$ARCHIVED_DIR" ]; then
  for project_yaml in "$ARCHIVED_DIR"/*/project.yaml; do
    [ -f "$project_yaml" ] || continue
    dir=$(dirname "$project_yaml")
    slug=$(basename "$dir")

    name=$(grep "^name:" "$project_yaml" | head -1 | sed 's/name: //')
    status=$(grep "^status:" "$project_yaml" | head -1 | sed 's/status: //')
    tags_line=$(grep "^tags:" "$project_yaml" | head -1 | sed 's/tags: //')
    priority=$(grep "^priority:" "$project_yaml" | head -1 | sed 's/priority: //')
    updated=$(grep "^updated:" "$project_yaml" | head -1 | sed 's/updated: //')

    archived_count=$((archived_count + 1))
    archived_entries="$archived_entries
  - slug: $slug
    name: $name
    status: $status
    tags: $tags_line
    priority: $priority
    updated: $updated"
  done
fi

echo "project_count: $project_count" >> "$INDEX_FILE"
echo "projects:$entries" >> "$INDEX_FILE"
echo "archived_project_count: $archived_count" >> "$INDEX_FILE"
echo "archived_projects:$archived_entries" >> "$INDEX_FILE"

echo "generated: $(date -u +%Y-%m-%dT%H:%M:%SZ)" >> "$INDEX_FILE"
echo "project_count: $project_count archived_count: $archived_count" >> "$INDEX_FILE"
```

After writing this file, make it executable: `chmod +x {CONTEXT_DIR}/generate-index.sh`

Run it to verify:

```bash
{CONTEXT_DIR}/generate-index.sh
```

---

### Step 5: Seed the Index

Write `{CONTEXT_DIR}/_index.yaml` with this content (replace `{DATE}` and `{USER_NAME}`):

```yaml
generated: "{DATE}T00:00:00Z"
project_count: 1
projects:
  - slug: inception
    name: Inception
    status: active
    tags: [meta, context-management, ai]
    priority: high
    updated: "{DATE}"

archived_project_count: 0
archived_projects:
```

Then run `{CONTEXT_DIR}/generate-index.sh` to regenerate it properly.

---

### Step 6: Finalize

Make the script executable:

```bash
chmod +x {CONTEXT_DIR}/generate-index.sh
```

Run it to verify:

```bash
{CONTEXT_DIR}/generate-index.sh
```

---

### Step 7: Print the CLAUDE.md Snippet

Tell the user:

> "Your context directory is set up at `{CONTEXT_DIR}`.
> 
> Add this section to your global `~/.claude/CLAUDE.md` so Claude reads your project context at the start of every session:
> 
> \`\`\`markdown
> ## Personal Context
> 
> \`{CONTEXT_DIR}\` is your context directory – always available in every Claude session. All project context lives here. Read it before asking the user to repeat themselves.
> 
> ### Finding Projects
> 
> 1. **Project index:** `{CONTEXT_DIR}/_index.yaml` – lists all active projects with status
> 2. **Project details:** `{CONTEXT_DIR}/projects/{slug}/project.yaml` and `README.md` (goals, decisions)
> 3. **Session notes:** Write to `{CONTEXT_DIR}/projects/{slug}/notes/YYYY.MM.DD.topic.md`
> 4. **Archived projects:** `{CONTEXT_DIR}/projects-archived/{slug}/`
> 
> @{CONTEXT_DIR}/CLAUDE.md
> \`\`\`
> 
> Then show them the directory listing of what was created.
```

#### `{CONTEXT_DIR}/projects/_template/project.yaml`

```yaml
name: "Project Name"
slug: "project-slug"       # lowercase-hyphenated, matches folder name
status: idea               # latent | idea | exploring | proposal | active | paused | done | cancelled
tags: []
priority: medium           # critical | high | medium | low | none
eisenhower: Q3             # Q1=urgent+important · Q2=important · Q3=urgent · Q4=neither
owner: {USER_NAME}
created: "{DATE}"
updated: "{DATE}"

links:
  repo:                    # ticket board, project management tool
  board:                   # Slack, Discord, Teams, etc.
  channel:                 # wiki, Notion, Confluence, etc.
  docs:

related: []                # slugs of related projects

search_terms:
  # Keywords that appear in external notes when writing about this project.
  # Used by context tools to surface relevant notes during session setup.
  - "Project Name"

summary: >
  One paragraph description of what this project is and why it matters.

context:
  plugins: []              # Claude plugins active for this project
  skills: []               # Claude skills active for this project
  rules: []                # Behavioral rules for this project

workspace:
  folders: []              # Local paths to repos, e.g. ~/Development/my-repo
```

#### `{CONTEXT_DIR}/projects/_template/README.md`

```markdown
# Project Name

One sentence description.

## Goals

-

## Context

*Background, motivation, constraints.*

## Key Decisions

| Date | Decision | Reason |
|---|---|---|
| {DATE} | | |

## Open Questions

-

## Links

-
```

#### `{CONTEXT_DIR}/projects/_template/integrations.md`

```markdown
# Integrations

External tools and resources for this project.

Add one Markdown file per integration, e.g. `github.md`, `linear.md`, `notion.md`.
```

#### `{CONTEXT_DIR}/projects/inception/project.yaml`

```yaml
name: "Inception"
slug: "inception"
status: active
tags:
  - meta
  - context-management
  - ai
priority: high
eisenhower: Q2
owner: {USER_NAME}
created: "{DATE}"
updated: "{DATE}"

links:
  repo:

related: []

search_terms:
  - inception
  - context-management
  - personal context

summary: >
  The Inception context management system itself. Structured Markdown and YAML that gives your AI assistant persistent, organized access to your working context across sessions, tools, and machines.

context:
  plugins: []
  skills: []
  rules: []

workspace:
  folders: []
```

#### `{CONTEXT_DIR}/projects/inception/README.md`

```markdown
# Inception

A personal project context management system for engineers who work with AI assistants.

## What This Is

Inception is a structured directory of Markdown and YAML files that serves as your AI assistant's persistent memory store. Each project gets a folder. Your AI reads it at session start and knows what you're working on without you having to repeat yourself.

## Directory Structure

{CONTEXT_DIR}/
├─ README-FIRST.md        → Human orientation
├─ CLAUDE.md              → AI session instructions
├─ _index.yaml            → Generated index (do not edit by hand)
├─ generate-index.sh      → Rebuilds _index.yaml from project.yaml files
├─ project-lifecycle.md   → Status and lifecycle definitions
├─ projects/
│  ├─ _template/
│  │  ├─ {slug}/
│  │  │  ├─ project.yaml           → Status, tags, links, priority
│  │  │  ├─ README.md              → Goals, decisions, context
│  │  │  ├─ integrations.md        → optional
│  │  │  └─ notes/                 → YYYY.MM.DD.topic.md
│  │  └─ inception/                → One folder per active project
│  │  │  ├─ project.yaml
│  │  │  ├─ README.md
│  │  │  ├─ integrations.md
│  │  │  └─ notes/
│  └─ {slug}/
│     ├─ project.yaml
│     ├─ README.md
│     ├─ integrations.md
│     └─ notes/
├─ projects-archived/     → Completed or abandoned projects (same structure)
├─ team/                  → Team member profiles
├─ integrations/          → How external tools are connected to this system
└─ notes/

## Key Workflows

### New project

Copy `projects/_template/` → `projects/{slug}/`, fill `project.yaml`

### Rebuild index

Run `./generate-index.sh` from this directory

### Session notes

Write to `projects/{slug}/notes/YYYY.MM.DD.topic.md`

### Archive a project

Move `projects/{slug}/` → `projects-archived/{slug}/`, rebuild index

### Update status

Edit `project.yaml`, run `./generate-index.sh`

## For the AI

Your context directory is `{CONTEXT_DIR}`. All project context lives here. Read it before asking the user to repeat themselves.

## At Session Start

1. Read `{CONTEXT_DIR}/_index.yaml` for a project overview
2. For any project you mention: read `projects/{slug}/project.yaml` and `README.md`
3. Check `projects/{slug}/integrations.md` if it exists
4. Write session insights to `projects/{slug}/notes/YYYY.MM.DD.topic.md`
5. Never ask the user to paste context – read it directly from this directory

## During the Session

- Write session insights to `projects/{slug}/notes/YYYY.MM.DD.topic.md`
- Update `project.yaml` when status or metadata changes; run `./generate-index.sh` after
- Never ask the user to paste context – read it directly from this directory

## Reference

Status values: `latent | idea | exploring | proposal | active | paused | done | cancelled`
(See `project-lifecycle.md` for full definitions.)

## About integrations.md

Each project can have an optional `integrations.md` alongside its `README.md`. Use it for links to external systems – repo URL, ticket board, chat channel, docs. Keeping these separate from `README.md` lets the `README` stay focused on goals and decisions.

## For the AI

Your context directory is `{CONTEXT_DIR}`. All project context lives here. Read it before asking the user to repeat themselves.

## Directory Layout

{CONTEXT_DIR}/
├─ _index.yaml
├─ generate-index.sh
├─ project-lifecycle.md
├─ projects/
│  ├─ _template/
│  │  ├─ {slug}/
│  │  │  ├─ project.yaml
│  │  │  ├─ README.md
│  │  │  ├─ integrations.md
│  │  │  └─ notes/
│  │  └─ inception/
│  │  │  ├─ project.yaml
│  │  │  ├─ README.md
│  │  │  ├─ integrations.md
│  │  │  └─ notes/
│  └─ {slug}/
│     ├─ project.yaml
│     ├─ README.md
│     ├─ integrations.md
│     └─ notes/
├─ projects-archived/
├─ team/
├─ integrations/
└─ notes/

## project.yaml Schema

Every project folder contains a `project.yaml` with this schema:

```yaml
name:           Human-readable project name
slug:           lowercase-hyphenated, matches folder name
status:         latent | idea | exploring | proposal | active | paused | done | cancelled
tags:           [freeform strings]
priority:       critical | high | medium | low | none
eisenhower:     Q1 | Q2 | Q3 | Q4
owner:          your name
created:        YYYY-MM-DD
updated:        YYYY-MM-DD
links:
  repo:         # ticket board, project management tool
  board:        # Slack, Discord, Teams, etc.
  channel:      # wiki, Notion, Confluence, etc.
  docs:         
related:        [slugs of related projects]
search_terms:   # Keywords that appear in external notes when writing about this project
  - "Project Name"
summary: >
  One paragraph description of what this project is and why it matters.

context:
  plugins:      # Claude plugins active for this project
  skills:       # Claude skills active for this project
  rules:        # Behavioral rules for this project

workspace:
  folders:      # Local paths to repos, e.g. ~/Development/my-repo
```

## The Index

`_index.yaml` is generated by `./generate-index.sh`. It contains a flat list of all active projects with their name, slug, status, tags, priority, and updated date.

Your AI reads this file first to get a project overview, then drills into individual `project.yaml` + `README.md` for whichever projects are relevant to the session.

Never edit `_index.yaml` by hand. Run `./generate-index.sh` after any project changes.

## Lifecycle

See `project-lifecycle.md` for full definitions.

| Status | Meaning |
|---|---|
| `latent` | Seed idea, not yet worth a folder. Lives in notes or a quick list. |
| `idea` | Worth tracking, not yet started. |
| `exploring` | Actively investigating – research, spikes, conversations in progress. |
| `proposal` | Formal proposal or design doc is being written or reviewed. |
| `active` | Current work. In your regular rotation. |
| `paused` | Blocked or deprioritized. Not abandoned, but not active. Note the reason. |
| `done` | Complete. Move to `projects-archived/` and rebuild the index. |
| `cancelled` | Abandoned. Move to `projects-archived/` and rebuild the index. |

## Transitions

- `latent` → `idea`: You decided it deserves a tracked folder
- `idea` → `exploring`: You started investigating
- `exploring` → `proposal`: Investigation produced a design worth proposing
- `proposal` → `active`: Proposal accepted; work begins
- `active` → `paused`: Work stopped but project is still alive
- `paused` → `active`: Work resumed
- `active` → `done`: Work is complete
- any → `cancelled`: Project is abandoned

## Archiving

When a project reaches `done` or `cancelled`:
1. Update `status` in `project.yaml`
2. Move the project folder to `projects-archived/{slug}/`
3. Run `./generate-index.sh` to update the index

Archived projects are preserved – their notes and decisions remain queryable.
```

#### `{CONTEXT_DIR}/project-lifecycle.md`

```markdown
# Project Lifecycle

Each project has a `status` field in its `project.yaml`. Use these definitions.

## Status Definitions

| Status | Meaning |
|---|---|
| `latent` | Seed idea, not yet worth a folder. Lives in notes or a quick list. |
| `idea` | Worth tracking, not yet started. |
| `exploring` | Actively investigating – research, spikes, conversations in progress. |
| `proposal` | Formal proposal or design doc is being written or reviewed. |
| `active` | Current work. In your regular rotation. Note the reason. |
| `paused` | Blocked or deprioritized. Not abandoned, but not active. |
| `done` | Complete. Move to `projects-archived/` and rebuild the index. |
| `cancelled` | Abandoned. Move to `projects-archived/` and rebuild the index. |

## Transitions

- `latent` → `idea`: You decided it deserves a tracked folder
- `idea` → `exploring`: You started investigating
- `exploring` → `proposal`: Investigation produced a design worth proposing
- `proposal` → `active`: Proposal accepted; work begins
- `active` → `paused`: Work stopped but project is still alive
- `paused` → `active`: Work resumed
- `active` → `done`: Work is complete
- any → `cancelled`: Project is abandoned

## Archiving

When a project reaches `done` or `cancelled`:
1. Update `status` in `project.yaml`
2. Move the project folder to `projects-archived/{slug}/`
3. Run `./generate-index.sh` to update the index

Archived projects are preserved – their notes and decisions remain queryable.
```

#### `{CONTEXT_DIR}/projects/_template/integrations.md`

```markdown
# Integrations

External tools and resources for this project.

Add one Markdown file per integration, e.g. `github.md`, `linear.md`, `notion.md`.
```

#### `{CONTEXT_DIR}/projects/inception/integrations.md`

```markdown
# Integrations

External tools and resources for this project.

Add one Markdown file per integration, e.g. `github.md`, `linear.md`, `notion.md`.
```

#### `{CONTEXT_DIR}/team/_template.md`

```markdown
# {Name}

**Role:** *Title / Role*

**Teams:** *Team names*

**Last Updated:** *{DATE}*

## What They Work On

-

## Expertise / Go-To For

-

## Working Style

*Communication preferences, timezone, anything useful to know.*

-

## Recent Context

*Current projects, recent conversations.*

-

## Links

- Chat: @handle
- Email:
```

---

That completes the implementation. Now update the marketplace registry.
