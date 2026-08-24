---
name: tanstack-query
description: TanStack Query patterns and current API documentation. Use whenever writing or reviewing code that uses @tanstack/react-query, QueryClient, queries, mutations, cache invalidation, or optimistic updates.
---

# TanStack Query

## Process

1. Inspect the project's package manifest, TanStack Query imports, query client setup, and nearby query conventions. This step is complete when the installed version, framework, and local patterns are known.
2. Read `references/style.md`. This step is complete when its conventions and any project-specific exceptions have been identified.
3. Search the current TanStack documentation for every API or behavior the work depends on. This step is complete when the relevant documentation and source links have been inspected.
4. Implement or review the code using the style reference and current documentation. This step is complete when every changed query, mutation, key, and cache interaction has been accounted for.
5. Run the repository's type checks and relevant tests. This step is complete when checks pass or each blocked check is reported with its exact reason.

## Research current APIs

Use TanStack CLI instead of relying on remembered APIs. Filter documentation searches to Query and the project's framework. Request JSON so source URLs and metadata remain available.

```bash
bunx --bun @tanstack/cli search-docs "<API or task>" \
  --library query \
  --framework react \
  --json
```

Fetch a specific documentation page when a search result contains the contract needed for the change.

```bash
bunx --bun @tanstack/cli doc query <path> --json
```

Use the project's package runner when it is not Bun.
