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

## Private rules (`.claude/rules/private/`)

This folder is **gitignored** and holds local-only, path-scoped rules (design systems,
internal specs) that auto-load when a matching file is in context — e.g. a private design
system that triggers on frontend files. It may be empty on a given machine; that's expected.
