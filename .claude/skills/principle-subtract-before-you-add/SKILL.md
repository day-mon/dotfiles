---
name: principle-subtract-before-you-add
description: "Apply before every addition, refactor, or rewrite. First delete or consolidate what the change touches (dead code, duplicate logic, redundant validators, stubs), then build on the simpler base. An abstraction counts only when it removes more than it adds."
disable-model-invocation: true
---

# Subtract Before You Add

When evolving a system, remove complexity first, then build. Default to subtraction.

Make simplification a continual investment. Leave the design slightly simpler and more capable behind the same or smaller surface than you found it.

- Sequence removal before construction
- Cut before you polish (get to the minimum before investing in quality)
- Design for observed usage, not speculative edge cases
- No speculative validators, parsers, or guards beyond what the spec demands
- Simplify prompts (remove redundant instructions, excessive templates)
- When a reference has no novel content, delete it rather than leaving a stub

## Before you add anything

1. **Look for what to remove.** Read the code the change touches. List dead code, duplicate logic, one-caller wrappers, flags nobody sets, and validators the schema already covers.
2. **Look for what to merge.** If the new code would be the second or third copy of a shape, extract the shared shape first, then add the new case as one more use of it.
3. **Subtract or consolidate as its own step.** Commit it separately when the repo uses commits, so the reviewer sees a no-behavior-change diff before the feature diff.
4. **Then add.** The feature should now be smaller than it would have been.

## When an abstraction is subtraction

An abstraction earns its place when it deletes something: repeated branches, a rule written in two places, a shape assumed across files, or a state that could go invalid. Count it. If the abstraction plus its callers is more code than the copies it replaces, or it has one caller, it is addition, so don't build it (`principle-laziness-protocol`).

Good: three clients each build retry and timeout config, so move it into one base class and delete three copies.
Bad: an `ExporterProtocol` with one implementation "in case we add another."

## Report it

In the reply, say what you removed or consolidated before adding, or say "nothing to subtract" and why. If you can't name either, you skipped this step.
