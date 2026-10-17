# Workspace Packages (Level 3)

Use language-native build units when the repository has independently runnable artifacts.

## Layout

```text
apps/                    # runnables: thin, wiring + delivery only
├── api/
└── worker/
packages/                # libraries: one capability each
├── agents/
├── db/
└── queue/
```

- `apps/` holds runnables. `packages/` holds libraries. Never put everything in `packages/`.
- Name each package after its capability, e.g. `@scope/queue` or `ask-hr-queue`. Never use `core`, `common`, or `shared`. A "core" package becomes a dumping ground.
- Apps depend on packages. Packages never depend on apps.
- Each member keeps its own `tests/` folder.

## Runnable app rule

Create a separate app when an artifact has at least one of these:

- an independent executable or deployment (one per Lambda, one per worker type);
- distinct runtime dependencies;
- separate environment configuration;
- independent scaling, testing, or release lifecycle;
- a clear ownership boundary.

Do not create placeholder apps for executables that do not exist.

### What stays in apps

```text
apps/api
  HTTP routes, HTTP error mapping, server startup, DI container

apps/worker
  job/cron registration, job entrypoints, DI container

apps/cli
  command classes, terminal output, exit codes
```

## Package rule

A package exists when stable behavior is needed by more than one app, or when it is a distinct capability (queue, agents, db). Do not create a package only because code is generic or used twice.

Split a package further only when:

- consumers need a smaller dependency surface;
- the package has an independent release lifecycle;
- code is consumed outside the product;
- unrelated domains require separate ownership;
- build weight causes a measured problem.

## Boundary enforcement

Enforce the dependency direction in CI: `import-linter` (Python) or `tests/boundaries.test.ts` (TypeScript). When a boundary check fails, move the code instead of adding an exception.

## TypeScript / Bun

```json
{
  "name": "@scope/root",
  "private": true,
  "workspaces": ["apps/*", "packages/*"]
}
```

## Python / uv

```toml
[tool.uv.workspace]
members = ["apps/*", "packages/*"]
```

The root `pyproject.toml` holds no code, only shared dev tools and tool settings. Multiple processes in one image run under supervisord.

## Package import rule

Every package has a manifest, explicit dependencies, and explicit exports.

```json
{
  "name": "@scope/api",
  "dependencies": {
    "@scope/queue": "workspace:*"
  }
}
```

Import through package exports:

```ts
import { QueueService } from "@scope/queue";
```

Never cross package boundaries with relative source imports:

```ts
// BAD
import { QueueService } from "../../queue/src/service";
```

## Language-native equivalents

| Ecosystem | Boundary |
|---|---|
| TypeScript | package/workspace |
| Rust | crate/workspace |
| Python | uv workspace member |
| Go | internal package; separate module only for independent lifecycle |
| Java/.NET | Gradle/Maven module or .NET project |

## Reuse Levels 1 & 2 within each member

```text
workspace
└── app or package
    └── placement table
```

Every workspace member uses the placement rules in `feature-structure.md` internally.

## Research anchors

- Bun workspaces: https://bun.sh/docs/install/workspaces
- uv workspaces: https://docs.astral.sh/uv/concepts/projects/workspaces/
- Turborepo structure: https://turborepo.dev/docs/crafting-your-repository/structuring-a-repository
