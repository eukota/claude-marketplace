---
name: choose-primitive
description: Helps you decide which Claude primitive to build — skill, command, rule, hook, agent, or MCP server — by asking questions about what you want to accomplish.
---

# Choosing the Right Claude Primitive

Help the user identify which primitive type best fits what they want to build. Ask one question at a time. Lead with the goal question, then narrow based on their answer.

## The Primitives

| Primitive | When to use it |
|-----------|---------------|
| **Skill** | Claude should follow a specific process or workflow when asked. Reusable, invocable on demand. |
| **Command** | A slash command shortcut in Claude Code that triggers behavior quickly. |
| **Rule** | Claude should always behave a certain way — no invocation needed, always on. |
| **Hook** | A shell command that runs automatically when a Claude Code event fires (e.g. after a tool call, before a commit). |
| **Agent** | A specialized subagent Claude can dispatch for a focused, independent task. |
| **MCP Server** | Give Claude access to an external tool, API, or data source via the Model Context Protocol. |

## Decision Flow

Start with: **"What do you want to happen, and when?"**

Then use these follow-up questions to narrow it down:

1. **Is it always-on or invoked on demand?**
   - Always on → **Rule** or **Hook**
   - On demand → continue

2. **Is it triggered by a Claude Code event (tool use, file save, session start) or by you explicitly asking?**
   - Event-triggered → **Hook**
   - You ask for it → continue

3. **Does it require Claude to reason, plan, or write — or does it call an external system?**
   - External system / tool / API → **MCP Server**
   - Claude reasoning → continue

4. **Is it a focused, isolated task Claude should hand off to a specialist?**
   - Yes → **Agent**
   - No → continue

5. **Is it a reusable workflow or process with multiple steps?**
   - Yes → **Skill**
   - It's a quick one-shot trigger → **Command**

## Process

1. Ask the opening question: what do you want to happen, and when?
2. Based on their answer, ask one follow-up from the decision flow above
3. Once you can identify the primitive, recommend it with a one-sentence explanation of why it fits
4. Offer to help scaffold it

Keep it conversational. Don't present the full decision tree — guide them through it.
