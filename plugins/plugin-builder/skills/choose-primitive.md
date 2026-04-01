---
name: choose-primitive
description: Helps you decide which Claude primitive to build — skill, command, rule, hook, agent, or MCP server — by asking questions about what you want to accomplish.
---

# Choosing the Right Claude Primitive

Use `claude-primitives.md` as the canonical reference for what each primitive is and when to use it.

## Process

Ask one question at a time. Start broad, then narrow.

**Opening question:** "What do you want to happen, and when does it need to happen?"

Then use the Quick Decision Matrix from `claude-primitives.md` to guide the conversation:

| Need | Use |
|------|-----|
| Integrate with external system | **MCP Server** |
| User-triggered shortcut | **Command** |
| Complex multi-step autonomous task | **Agent** |
| Specialize Claude for a task type | **Skill** |
| Enforce policy/boundary | **Rule** |
| React to workflow events | **Hook** |

## Follow-up Questions

If the answer isn't clear from the opening question, use these to narrow down:

1. **Always-on or invoked on demand?** → always-on suggests Rule or Hook
2. **Triggered by a Claude Code event or by explicit request?** → event = Hook
3. **Needs access to an external system or API?** → MCP Server
4. **Fully autonomous multi-step task Claude should handle independently?** → Agent
5. **Reusable process with domain expertise?** → Skill
6. **Quick one-shot user shortcut?** → Command

## Output

Once identified, recommend the primitive with one sentence explaining the fit, then offer to help scaffold it.

Keep it conversational. Don't present the full matrix — guide them through it with questions.
