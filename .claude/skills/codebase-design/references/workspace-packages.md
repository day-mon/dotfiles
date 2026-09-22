# Workspace Packages (Level 3)

Use language-native build units when the repository has independently runnable artifacts.

## Runnable package rule

Create a separate runnable package when an artifact has at least one of these:

- an independent executable or deployment;
- distinct runtime dependencies;
- separate environment configuration;
- independent testing or release lifecycle;
- a clear ownership boundary.

Do not create placeholder packages for executables that do not exist.

## TypeScript / Bun

```text
packages/
├── core/
│   ├── package.json       # @scope/core
│   └── src/
├── api/
│   ├── package.json       # @scope/api
│   └── src/
├── cli/
│   ├── package.json       # @scope/cli
│   └── src/
└── crons/
    ├── package.json       # @scope/crons
    └── src/
```

Root workspace configuration:

```json
{
  "name": "@scope/root",
  "private": true,
  "workspaces": ["packages/*"]
}
```

## Core package rule

`@scope/core` contains product-specific behavior shared by runnable packages.

Typical contents:

- business services;
- shared runtime schemas;
- domain rules and validation;
- shared errors;
- client contracts;
- shared external client implementations when all consumers use them.

### Dependency direction

```text
@scope/api ─────┐
@scope/cli ─────┼──> @scope/core
@scope/crons ───┘
```

Core must not depend on runnable packages.

### What stays in runnable packages

```text
@scope/api
  HTTP routes, queue worker, HTTP error mapping, server startup

@scope/cli
  argument parsing, terminal output, exit codes

@scope/crons
  cron expressions, scheduler registration, execution locking
```

### What does not go in core

Do not place code in core only because it is generic or used twice. Shared code belongs in core when it represents stable product behavior needed by multiple runnable packages.

## When to split core

Start with one `@scope/core`. Split another shared package only when:

- consumers need a smaller dependency surface;
- the package has an independent release lifecycle;
- code is consumed outside the product;
- unrelated domains require separate ownership;
- build weight causes a measured problem.

## Package import rule

Every package has a `package.json`, explicit dependencies, and explicit exports.

Use:

```json
{
  "name": "@scope/api",
  "dependencies": {
    "@scope/core": "workspace:*"
  }
}
```

Import through package exports:

```ts
import { TicketAnalysisService } from "@scope/core/ticket-analysis";
```

Never cross package boundaries with relative source imports:

```ts
// BAD
import { TicketAnalysisService } from "../../core/src/ticket-analysis/service";
```

## Language-native equivalents

| Ecosystem | Boundary |
|---|---|
| TypeScript | package/workspace |
| Rust | crate/workspace |
| Python | import package or separately published distribution |
| Go | internal package; separate module only for independent lifecycle |
| Java/.NET | Gradle/Maven module or .NET project |

## Reuse Levels 1 & 2 within each package

```text
workspace
└── package
    └── features
        └── feature
```

Every workspace package uses the feature-structure rules internally.

## Research anchors

- Bun workspaces: https://bun.sh/docs/install/workspaces
- Turborepo structure: https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository
- n8n: https://github.com/n8n-io/n8n (flat `packages/` layout)
- Backstage: https://github.com/backstage/backstage (flat `packages/` layout)