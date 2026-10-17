---
name: coding-standards
description: Coding standards. Use whenever you are writing source code or reviewing code.
---

# Coding standards

## Process

1. Classify every source file being written or reviewed. This step is complete when each file maps to every applicable branch below.
2. Read each applicable reference before changing or judging the code. Resolve these paths from this skill's directory. This step is complete when all matching references have been read:
   - Python source: `references/python.md`
   - Rust source: `references/rust.md`
   - TypeScript source: `references/typescript.md`
   - React components or hooks: `references/react.md`, plus the TypeScript reference for `.ts` and `.tsx` files
   - Next.js 16.3+ with `cacheComponents: true`: `references/nextjs-cache-components.md`, plus the TypeScript and React references when applicable
   - Tests in any language: `references/testing.md`
3. Apply the universal rules below and every relevant rule from the loaded references. Framework rules override language rules, and language rules override universal rules. This step is complete when every relevant rule has been accounted for in the implementation or review.
4. Run the repository's checks for changed code, including any validation required by the loaded references. This step is complete when checks pass or each blocked check is reported with its exact reason.

## Keep the core pure

Prefer functions whose outputs depend only on their inputs. Return new values instead of mutating arguments or shared state.

Put required side effects such as network, disk, database, and logging work at the edges. Keep decision-making logic pure and testable.

## Behavior lives on its owner

Constants become read-only class vars. Helpers become private or static methods. Factories become `create()`. Only code shared by several classes stays at module level. This applies in Python, TypeScript, and Rust (`impl`).

## Validate in the schema

Push validation into pydantic, zod, or t3-env. No hand-written `if not x: raise ValueError`, no `typeof` chains, no regex guards on data a schema can type. Use literal types for fixed sets.

## Fail fast, no defensive code

- Missing config or client: throw at startup. Don't return `null`, and don't set state to `None` for features that are off.
- No redundant timeouts, retries, or `Promise.resolve` wrappers when the library already handles them.
- No sanitizers or redaction for data the system is allowed to send.
- Delete dead code, scratch files, and handoff docs in the same change.
- Checks that must hold at runtime are real code, not assertions. Assertions can be stripped or disabled; they belong in tests.
- Use the library's extension points (hooks, middleware, interceptors) for cross-cutting behavior instead of wrapping every call site.

## Errors go to one handler

Raise or throw typed errors from a root `AppError`. One global handler maps them. Never catch an error just to rethrow, wrap, or log it again.

## Make related writes atomic

A change and everything that must stay consistent with it (an audit record, a status row, a queued follow-up) commit together or not at all. Never split them across connections or transactions. Keep slow external calls outside the transaction, then recheck ownership under a lock when saving the result.

## Logs are data

Log a stable event name with fields, never values formatted into a message. Use the project's structured logger everywhere so every line carries the same context.

```text
log.info("tickets_dispatched", count=count, queue=queue)
```

## Guard early

Validate inputs first. Return or raise on invalid states before the main path. Keep the successful path shallow.

Never nest `if`s. Negate the condition and return. Never nest ternaries. Split any function that needs scrolling into private methods.

## Name intent

Use names that state what a value or operation is for. Prefer `pendingInvites`, `retryCount`, and `isExpired` over names based on storage or type.

Name literals that carry domain meaning.

```text
if (status === STATUS.ARCHIVED) { ... }
sleep(ONE_DAY_SECONDS)
```

## Keep functions focused

A function should have one job. Split it when its responsibility needs a paragraph or multiple unrelated verbs to explain.

## Comments

Default: no comments and no docstrings or JSDoc. Names and types carry the meaning.

A comment survives only when it records a non-obvious external fact, in one line. Longer context goes in `docs/`. Never restate the signature. When a repository requires doc comments, match its existing style.
