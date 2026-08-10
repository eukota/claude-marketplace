# Claude Primitives Guide

A reference for understanding when to use each building block in Claude's system.

## The Primitives

### Rules
- **What:** Constraints and guidelines that shape behavior
- **How it works:** Applied to Claude's reasoning and decision-making
- **When to use:** When you need Claude to follow specific policies, safety boundaries, or operational constraints
- **Example:** "Never delete files without confirmation"

### Hooks
- **What:** Trigger points in workflows that execute code at specific moments
- **How it works:** Fire on events (pre/post actions, on errors, on completion)
- **When to use:** When you need side effects or setup/teardown logic around events
- **Example:** Post-commit validation, pre-deployment checks

### Agents
- **What:** Autonomous task executors that can chain tool calls and iterate
- **How it works:** Take a goal, plan steps, execute them, adapt if needed
- **When to use:** Complex multi-step tasks requiring autonomy and decision-making
- **Example:** Research a topic across multiple sources, synthesize findings

### Skills
- **What:** Packaged expertise for specific domains (docx, xlsx, pdf, pptx, etc.)
- **How it works:** Specialized knowledge + tools bundled for a task type
- **When to use:** When Claude needs best-practice guidance for a specific file type or task
- **Example:** Creating polished Word docs with proper formatting

### Commands
- **What:** User-invoked actions triggered by `/command` syntax
- **How it works:** Explicit user request → mapped action
- **When to use:** When you want quick, intentional shortcuts for common tasks
- **Example:** `/commit` for git, `/review-pr` for code review

### MCPs (Model Context Protocol)
- **What:** Connectors to external systems (Slack, Asana, Jira, GitHub, databases, etc.)
- **How it works:** Bi-directional communication with external services
- **When to use:** When Claude needs live access to or can modify external data/systems
- **Example:** Check Asana tasks, post to Slack, query your database

## Quick Decision Matrix

| Need | Use |
| --- | --- |
| Integrate with external system | **MCP** |
| User-triggered shortcut | **Command** |
| Complex multi-step autonomous task | **Agent** |
| Specialize Claude for a task type | **Skill** |
| Enforce policy/boundary | **Rule** |
| React to workflow events | **Hook** |

## Use Case Scenarios

### Scenario: Automating a CI/CD Pipeline
- **MCPs:** Connect to GitHub, Jenkins, your deployment system
- **Agents:** Autonomous remediation when deployments fail
- **Commands:** `/deploy`, `/rollback` for quick user actions
- **Hooks:** Trigger validation after code merge
- **Rules:** "Never deploy to production without approval"

### Scenario: Building Internal Tooling
- **Skills:** Specialized knowledge for creating polished reports/docs
- **MCPs:** Connect to your internal systems (ticketing, monitoring, etc.)
- **Commands:** Domain-specific shortcuts for your team
- **Agents:** Complex investigation and remediation tasks

### Scenario: Data Processing Workflow
- **Skills:** Excel/PDF expertise for data transformation
- **Hooks:** Trigger cleanup or validation after data import
- **MCPs:** Connect to your data warehouse or storage
- **Rules:** Data handling and privacy constraints
