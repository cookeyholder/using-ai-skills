---
name: claude-handoff
description: Hand the current conversation off to a fresh background agent that picks up the work immediately.
argument-hint: "What will the next session be used for?"
disable-model-invocation: true
---

Write a handoff summary of the current conversation so a fresh agent can continue the work. Instead of saving it, launch a background agent seeded with the summary as its prompt: `claude --bg --name "<descriptive name>" "<handoff summary>"`. It starts in the current working directory and returns immediately; the user manages it with `claude agents`.

Always pass `-n`/`--name` with a descriptive name (e.g. `--name "Fix login bug"`); it sets the display name shown in the job list, session picker, and terminal title.

### Choosing between the two handoff skills

- **`claude-handoff`** (this skill): seed a fresh background agent immediately via `claude --bg`. Use when the work should continue right now without waiting for a new session.
- **`handoff`**: write the summary to a file in the OS temporary directory. Use when you want a durable artifact to pick up later.

Both apply the same rules below: suggested skills, no duplicated content, redacted secrets.

## When NOT to Use

- When you only want a durable handoff document — use `handoff`; this skill launches a background agent.
- When the conversation has no reusable context (a one-line question, a finished task) — no handoff is needed.
- When a spec, plan, or ADR already captures everything — reference that file instead of seeding an agent with a duplicate.
- When the work is mid-slice and the summary would be stale — finish the current slice first.
- When `claude` CLI is unavailable or background agents are not supported — use `handoff` instead.

Include a "suggested skills" section in the summary, naming which skills the next agent should call the Skill tool for.

Do not duplicate content already captured in other artifacts (specs, plans, ADRs, issues, commits, diffs). Reference them by path or URL instead.

Redact any sensitive information, such as API keys, passwords, or personally identifiable information, since the summary becomes the agent's prompt.

If the user passed arguments, treat them as a description of what the next session will focus on and tailor the summary accordingly.
