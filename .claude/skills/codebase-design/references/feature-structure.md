# Feature Structure (Levels 1 & 2)

## Level 1: simple package

Use for a small application with roughly five or fewer features and no independent workspace units.

```text
src/
├── main.ts
├── config.ts
├── ticket-analysis.ts
├── ticket-analysis.test.ts
├── jobs.ts
└── jobs.test.ts
```

A route, schema, and operation may remain in one file while the file is cohesive and easy to navigate.

Do not create feature folders, repositories, interfaces, or dependency containers preemptively.

## Level 2: feature-driven package

Use when the application has several features or one feature has multiple meaningful responsibilities.

```text
src/
├── ticket-analysis/
│   ├── routes.ts
│   ├── service.ts
│   ├── schemas.ts
│   └── validation.ts
├── analysis-jobs/
│   ├── routes.ts
│   ├── service.ts
│   ├── schemas.ts
│   ├── queue.ts
│   └── worker.ts
├── clients/
│   ├── jira/
│   │   ├── client.ts
│   │   ├── schemas.ts
│   │   └── fake-client.ts
│   └── model/
├── platform/
│   ├── lifecycle.ts
│   ├── logging.ts
│   └── errors.ts
├── config.ts
├── app.ts
└── main.ts
```

A repository with many features may add a `features/` grouping directory:

```text
src/
└── features/
    ├── ticket-analysis/
    └── analysis-jobs/
```

Do not add the grouping directory when flat feature folders remain easy to scan.

### Feature contents

A feature may contain:

- `routes.ts` for HTTP delivery;
- `command.ts` for CLI delivery;
- `consumer.ts` or `worker.ts` for queued delivery;
- `service.ts` for business orchestration;
- `schemas.ts` for runtime validation;
- `repository.ts` for persistence;
- feature-specific clients, mappers, and tests.

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

Avoid global `utils/`, `helpers/`, or `common/` directories. Name shared code after the capability it provides.

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

Select implementations and build the object graph near the executable entrypoint.

```ts
const jira = config.useFakeJira
  ? new FakeJiraClient()
  : new JiraClient(config.jira);

const analysis = new TicketAnalysisService(jira, model);

startApi({ analysis });
```

Prefer constructor injection. Use the host framework's DI when it has one (NestJS modules, FastAPI Depends); otherwise wire with explicit factories near the entrypoint.