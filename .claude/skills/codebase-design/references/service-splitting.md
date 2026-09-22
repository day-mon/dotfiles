# Service Splitting

## When to split

Split a service when it has:

- independent operations with different callers;
- groups of methods using unrelated dependencies;
- multiple unrelated reasons to change;
- partial tests requiring extensive irrelevant setup;
- coordination logic mixed with low-level integration logic.

Do not split based on line count alone.

Keep a service intact when it exposes one cohesive operation, even when that operation has several internal steps.

## How to split

Use operation-oriented splits. Name files after the behavior they model:

```text
agents/
├── agent-creation.service.ts
├── agent-query.service.ts
├── agent-deletion.service.ts
├── agent-capabilities.service.ts
└── agent.repository.ts
```

## Migration

Use behavior-preserving steps:

1. Move files without changing behavior.
2. Add exports and replace cross-boundary imports.
3. Split mixed responsibilities behind existing tests.
4. Add boundary checks or lint rules.
5. Remove obsolete paths after validation passes.

Do not combine a directory rewrite with unrelated behavior changes.