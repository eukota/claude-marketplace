---
name: local-dev-standards
description: Standing conventions for local development work — worktrees, containerized installs, Makefile lifecycle targets, and hot reload.
---

# Local Dev Standards

Apply these automatically for local development work, across all projects and stacks, without being asked.

## Use Git Worktrees

- When starting feature/task work that touches an existing repo, use a git worktree (`git worktree add`) for isolation instead of switching branches in place on the main checkout.
- Never `git checkout`/`git switch` on the primary worktree to jump between unrelated tasks — create a new worktree instead.
- If the repo already provides its own worktree tooling or convention, use that.

## Containerize Package Installs

- Any package install (`npm install`, `pip install`, `cargo add`, `go get`, etc.) runs inside a Docker container, not directly on the host.
- Default to plain Docker unless the project already has a different containerization setup (devcontainer, docker-compose, etc.) — in that case, use what's already there.
- If no Dockerfile/container setup exists yet for the project, create a minimal one before installing packages.

## Makefile for Start/Stop

- Every project gets a `Makefile` with at minimum `start` and `stop` targets so local dev lifecycle is uniform across projects.
- Add `build`, `logs`, and `restart` targets when they make sense for the stack.
- If a Makefile already exists, extend it rather than replacing it.

## Hot Reload for Local Runs

- Local dev runs use hot reload / live reload whenever the stack supports it (e.g. `nodemon`, Vite/webpack dev server, `air` for Go, Django/Flask debug reload, `cargo watch`).
- Wire the hot-reload command into the Makefile's `start` target, not as a separate undocumented step.

## What NOT to Do

- Do not install packages directly on the host outside a container.
- Do not skip the Makefile for "quick" or throwaway projects that are otherwise being set up for real development.
- Do not silently fall back to a plain checkout instead of a worktree without saying so.
