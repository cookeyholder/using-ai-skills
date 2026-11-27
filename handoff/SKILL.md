---
name: handoff
description: Compact the current conversation into a handoff document for another agent to pick up.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Write a handoff document summarising the current conversation so a fresh agent can continue the work. Save to the temporary directory of the user's OS - not the current workspace.

### Choosing between the two handoff skills

- **`handoff`** (this skill): write the summary to a file in the OS temporary directory. Use when you want a durable artifact to pick up in a new session later.
- **`claude-handoff`**: seed a fresh background agent with the summary immediately via `claude --bg`. Use when the work should continue right now without waiting for a new session.

Both apply the same rules below: suggested skills, no duplicated content, redacted secrets.

## When NOT to Use

- When the next agent should start immediately — use `claude-handoff`.
- When the conversation has no reusable context (a one-line question, a finished task) — no handoff is needed.
- When a spec, plan, or ADR already captures everything — reference that file instead of writing a duplicate.
- When the work is mid-slice and the summary would be stale — finish the current slice first.

Include a "suggested skills" section in the document, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the doc accordingly.
