# local-dev-standards

Enforces standard local development practices — git worktrees, containerized package installs, Makefile start/stop targets, and hot reload.

## Primitives

### Rules

- **local-dev-standards** — always-on conventions applied to local dev work across all projects:
  - Use git worktrees for feature/task isolation instead of switching branches in place
  - Run package installs inside a Docker container, not on the host
  - Every project gets a Makefile with `start`/`stop` (and `build`/`logs`/`restart` as relevant)
  - Local dev runs use hot reload wherever the stack supports it, wired into the Makefile's `start` target

## Usage

Install the plugin and the rules apply automatically — no invocation needed.
