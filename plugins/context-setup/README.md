# context-setup

A personal project context management system for engineers who work with AI assistants.

## What It Does

The `local-context-setup` skill scaffolds a structured directory of Markdown and YAML files that gives your AI assistant persistent, organized access to your working context — across sessions, tools, and machines (if you use a shared file store).

Run it once. Your AI reads the context directory at the start of every session and knows what you're working on without you having to repeat yourself.

## Install

```
claude install context-setup
```

## Usage

```
/context-setup:local-context-setup
```

Walks you through setup interactively. Takes ~2 minutes. Creates your context directory wherever you want it.

## What Gets Created

```
{your-context-dir}/
├── README-FIRST.md
├── CLAUDE.md
├── _index.yaml
├── generate-index.sh
├── project-lifecycle.md
├── projects/
│   ├── _template/
│   └── inception/
├── projects-archived/
├── team/
└── integrations/
```

## The System

See `projects/inception/README.md` inside your context directory after bootstrapping – that is the canonical spec for how Inception works.
