---
name: coding-standards
description: Coding standards. Use whenever you are writing source code or reviewing code.
---

# Coding standards

## Process

1. Classify every source file being written or reviewed. This step is complete when each file maps to every applicable branch below.
2. Read each applicable reference before changing or judging the code. Resolve these paths from this skill's directory. This step is complete when all matching references have been read:
   - Python source: `references/python.md`
   - TypeScript source: `references/typescript.md`
   - React components or hooks: `references/react.md`, plus the TypeScript reference for `.ts` and `.tsx` files
   - Next.js 16.3+ with `cacheComponents: true`: `references/nextjs-cache-components.md`, plus the TypeScript and React references when applicable
3. Apply the universal rules below and every relevant rule from the loaded references. Framework rules override language rules, and language rules override universal rules. This step is complete when every relevant rule has been accounted for in the implementation or review.
4. Run the repository's checks for changed code, including any validation required by the loaded references. This step is complete when checks pass or each blocked check is reported with its exact reason.

## Keep the core pure

Prefer functions whose outputs depend only on their inputs. Return new values instead of mutating arguments or shared state.

Put required side effects such as network, disk, database, and logging work at the edges. Keep decision-making logic pure and testable.

## Guard early

Validate inputs first. Return or raise on invalid states before the main path. Keep the successful path shallow.

## Name intent

Use names that state what a value or operation is for. Prefer `pendingInvites`, `retryCount`, and `isExpired` over names based on storage or type.

Name literals that carry domain meaning.

```text
if (status === STATUS.ARCHIVED) { ... }
sleep(ONE_DAY_SECONDS)
```

## Keep functions focused

A function should have one job. Split it when its responsibility needs a paragraph or multiple unrelated verbs to explain.

## Comment the reason

Let code state what it does. Comments record constraints, tradeoffs, workarounds, and facts the code cannot express.

Use the language's native documentation format:

- TypeScript and JavaScript: JSDoc
- Python: Google-style docstrings
- Go: Go doc comments
- Rust: rustdoc
- Java: Javadoc
