# Component Roles

## Route or controller

Owns transport concerns:

- validates transport input;
- translates headers, parameters, and bodies;
- calls one application operation;
- maps results and errors to transport responses.

Keep business decisions out of routes and controllers.

## Service

Represents a cohesive business operation or capability.

A service may:

- coordinate repositories and clients;
- apply business rules;
- control an operation or transaction;
- return application-level results.

A service is not a miscellaneous collection of related methods.

## Repository

Owns persistence for application-controlled records.

A repository may:

- query and persist aggregates;
- map database records;
- own persistence-specific filtering;
- participate in transactions.

Jira, Slack, payment providers, model providers, and other remote APIs are clients, not repositories. A database or warehouse reader (StarRocks, a shared Postgres) is a repository, even when another team owns the database.

Do not create a repository when no application-owned persistence exists.

Modern ORM access may remain directly in a service while queries are simple. Introduce a repository when:

- multiple services reuse a query;
- persistence mapping becomes substantial;
- transaction ownership needs clarification;
- tests need meaningful persistence substitution.

## Client

Talks to an external HTTP API, and nothing else.

- Use the official SDK when one exists (Glean, Slack WebClient, jira.js). Wrap or configure it; don't reimplement it.
- Use library hooks for auth, retry, timeouts, and logging (ky hooks, aiohttp trace configs, reqwest retry) instead of hand-written wrappers.
- Missing token or config: throw at construction. Never hold `None` or `null` as a client.

A client owns:

- authentication and protocol details;
- request construction;
- timeouts and retries;
- external response validation;
- mapping external failures.

Pure helpers and constants that belong to the client's responsibility (request-expression builders, header sets, user agents) travel on the class as `@staticmethod`, `@classmethod`, or `ClassVar` rather than as module-level functions or constants, so the class stays the single unit to read and test. Only helpers shared across more than one class go module-level.

Clients always live in `clients/`, with a fake or fixture beside the real one when tests need it.

## Model

Behavior that reads only a model's data lives on the model:

- `Job.to_job_out()` instead of a `job_to_out(job)` function;
- `DocumentResult.empty()` instead of passing a pile of empty args;
- `Evidence.build(...)` instead of `build_evidence(...)`;
- `@property` for derived values.

## Errors

One root `AppError(status, message)` per app, with a subclass per case (`JobNotFoundError` with status 404). Services raise. One global handler maps every `AppError` to a shared response format. Routes never catch. Nothing catches an error just to rethrow or wrap it.

## Schema

Provides runtime validation for input, output, configuration, or external responses.

With Zod, infer TypeScript types from schemas:

```ts
export const TicketSchema = z.object({
  key: z.string(),
});

export type Ticket = z.infer<typeof TicketSchema>;
```

Create `types.ts` only for substantial internal types that are not derived from runtime schemas.

## Persistence model

Colocate persistence models with the owning feature by default.

Use a central `db/` or schema directory when the ORM requires centralized discovery, schema generation, or migrations.

## Platform

Use `platform/` for process-specific plumbing:

- lifecycle management;
- logging setup;
- middleware;
- transport error mapping;
- environment loading.

Do not put business behavior in `platform/`.