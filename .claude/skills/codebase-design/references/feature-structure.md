# Feature Structure (Levels 1 & 2)

## Level 1: simple package

Use for a small application with roughly five or fewer features and no independent workspace units.

```text
src/
├── main.ts
├── config.ts
├── ticket-analysis.ts
└── jobs.ts
tests/
├── ticket-analysis.test.ts
└── jobs.test.ts
```

A route, schema, and operation may remain in one file while the file is cohesive and easy to navigate.

Do not create feature folders, repositories, interfaces, or dependency containers preemptively.

## Level 2: layered package

Use when the application has several features or one feature has multiple meaningful responsibilities.

### Placement table

Every file maps to exactly one row. If a file fits no row, the design is wrong.

| Code | Goes in |
|---|---|
| HTTP route + its schemas, service, errors | `api/v1/<domain>/` |
| Job / cron / consumer entrypoint (thin: calls one service) | `jobs/<domain>.py` |
| Talks to an external HTTP API | `clients/<name>` |
| Reads or writes a database (ours or a warehouse like StarRocks) | `repositories/` |
| Business operation not owned by a route | `services/` |
| Model agent (one per file, shared setup in a base class) | `agents/<name>.py` + `agents/base.py` |
| DI wiring for HTTP | `Depends` aliases beside the routes that use them |
| DI wiring for workers / CLI (no framework DI) | `container` + `providers/` (Dishka) |
| Config, logging, error handlers, lifecycle | `core/` or `platform/` (app-only, never a package) |
| TS formatting/parse helpers | `lib/<topic>.ts` |

```text
src/
├── api/
│   └── v1/
│       └── jobs/
│           ├── routes.py
│           ├── schemas.py
│           ├── service.py
│           └── errors.py
├── jobs/
│   └── jira_poll.py
├── services/
│   └── jira_poller.py
├── repositories/
│   └── poll_repository.py
├── clients/
│   ├── glean.py
│   └── jira/
│       ├── client.py
│       ├── schemas.py
│       └── fixture.py
├── providers/
├── container.py
├── core/
│   ├── config.py
│   ├── errors.py
│   └── logging.py
└── main.py
tests/
└── (mirrors src/)
```

- One service, client, or repository class per file.
- Keep a module's schemas together in one `schemas` file. Don't split them per class.
- Tests go in `tests/`, mirroring `src/`. They are never colocated.

### Feature contents

A feature may contain:

- `routes.ts` for HTTP delivery;
- `command.ts` for CLI delivery;
- `consumer.ts` or `worker.ts` for queued delivery;
- `service.ts` for business orchestration;
- `schemas.ts` for runtime validation;
- `repository.ts` for persistence;
- feature-specific mappers.

These are options, not mandatory slots. Create only the files the feature needs.

## Framework deference

Defer to strong framework conventions in Next.js, NestJS, tRPC, FastAPI, Rails, or Django.

If most of the repository already follows a consistent structure, recommend targeted changes instead of a full reorganization.

## Cross-feature dependencies

Features should not import another feature's internal files.

Prefer, in order:

1. Compose both features at the application root.
2. Depend on an explicit public feature API when the direction is stable.
3. Extract stable shared product behavior into a shared package.
4. Use an event when asynchronous decoupling has real value.

Do not introduce an event bus merely to avoid a direct function call.

## Grouping directories

No grab-bag `utils/`, `helpers/`, or `common/`. In TypeScript, `lib/` is fine when every file in it is named by topic (`lib/fmt.ts`, `lib/dates.ts`). Name shared code after the capability it provides.

Layers point one way, enforced by import-linter:
`container → providers → jobs → services → repositories → clients`.

## Splitting into separate apps

Split by data ownership, not role: whatever reads or writes the same database deploys
together. Stateless compute (LLM agents, rendering) can move to its own service called
over HTTP. The caller keeps orchestration (source checks, retries, persistence); the
service only computes (workflow/activity separation).

When separately built apps share contract models, one app owns the package and the other
vendors a copy. A sync script copies it, and a drift test in *both* apps fails when they
differ.

## Dependency design

Depend on concrete classes by default.

Introduce an interface when:

- real and fake implementations exist;
- multiple production implementations exist;
- a package boundary needs a stable contract;
- the dependency is volatile or externally owned;
- tests require meaningful substitution.

Do not create one interface for every class.

When a fake exists, run the same contract tests against both implementations. A fake without contract tests will drift.

## Composition

Select implementations and build the object graph in the app's DI container, never inside packages.

```python
class JiraProvider(Provider):
    @provide(scope=Scope.APP)
    async def jira(self, settings: Settings) -> AsyncIterator[JiraClient]:
        async with JiraClient.create(settings.jira) as client:
            yield client
```

Prefer constructor injection. Use the framework's DI whenever it exists (NestJS modules, FastAPI `Depends`); never add Dishka to an HTTP app. Use Dishka only where the framework's DI can't reach: job workers, CLI commands, cron entrypoints. Build objects with a `create()` classmethod or static method on the class. Do not write `build_x()`, `open_resources()`, or `createX()` free functions; the small functions `Depends` requires are the one exception.

Swap real and fake implementations by injecting them. A job never branches on "offline" mode: there is one job, and the injected dependency is either the fake or the real one.