# CLAUDE.md

## Response style

**ALWAYS use the Damon Response Style** (see `.claude/output-styles/`) when interacting with this user.

## Coding docs

This repo keeps language-specific coding standards under `.claude/docs/`. **Before writing or editing code in one of these languages, read the relevant doc(s) and follow them.**

### Python (`.claude/docs/python/`)
- [`style.md`](docs/python/style.md) — naming, constants/immutability, general Python style conventions.

### TypeScript (`.claude/docs/typescript/`)
- [`style.md`](docs/typescript/style.md) — strictness, `type` vs `interface`, general style.
- [`typing.md`](docs/typescript/typing.md) — typing patterns; make impossible states unrepresentable.
- [`react.md`](docs/typescript/react.md) — React component patterns (arrow components, `…Props` types).
- [`tools.md`](docs/typescript/tools.md) — tooling: prefer `bun` / `bunx --bun`, linting, formatting.

### How to apply
1. Identify the language of the code you're about to write or modify.
2. Read every doc listed for that language above.
3. Match the conventions exactly — these guides override generic defaults.
4. When a doc is silent on something, follow the closest documented pattern.
