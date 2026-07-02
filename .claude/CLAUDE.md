# CLAUDE.md

## Response style

**ALWAYS use the Damon Response Style** (see `.claude/output-styles/`) when interacting with this user.

## Coding standards

Language-specific coding standards live in `.claude/rules/` as **path-scoped rules** — they
load automatically when you open a matching file (Python → `**/*.py`, TypeScript →
`**/*.ts`/`**/*.tsx`). No action needed here; follow them, and they override generic defaults.

## Writing prose

When writing prose (messages, docs, emails, posts), use the **`writing` skill** — it picks a
casual or professional style and enforces the house rules (e.g. no em dashes). Invoke
`/writing` or let it auto-trigger on writing tasks.

GitHub prose (PR descriptions, PR/issue comments, review replies) always uses the **casual
writing style**.

## Private rules (`.claude/rules/private/`)

This folder is **gitignored** and holds local-only, path-scoped rules (design systems,
internal specs) that auto-load when a matching file is in context — e.g. a private design
system that triggers on frontend files. It may be empty on a given machine; that's expected.

## Worktree rules

All new worktrees should be created in the projects working dir and be put in .worktrees

## Validation

For React / Next.js work, run React Doctor before calling the work done:

```bash
cd web && bunx --bun react-doctor@latest
```

Treat warnings as actionable. If React Doctor reports an issue, fix it or explicitly explain why it is not applicable.


## Plan Mode

When a plan explains how existing code works, include a **call stack diagram**
showing the execution flow with `file:line` references at each level.

If the plan changes the flow, show two stacks: **before** and **after**, and
mark the edit points (e.g. `← EDIT HERE`).
