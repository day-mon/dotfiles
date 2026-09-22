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

Jira, Slack, payment providers, model providers, and other remote APIs are clients, not repositories.

Do not create a repository when no application-owned persistence exists.

Modern ORM access may remain directly in a service while queries are simple. Introduce a repository when:

- multiple services reuse a query;
- persistence mapping becomes substantial;
- transaction ownership needs clarification;
- tests need meaningful persistence substitution.

## Client

Encapsulates communication with an external system.

A client owns:

- authentication and protocol details;
- request construction;
- timeouts and retries;
- external response validation;
- mapping external failures.

Pure helpers and constants that belong to the client's responsibility (request-expression builders, header sets, user agents) travel on the class as `@staticmethod`, `@classmethod`, or `ClassVar` rather than as module-level functions or constants, so the class stays the single unit to read and test. Only helpers shared across more than one class go module-level.

Keep a trivial single-feature client inside that feature. Move it to a package-level `clients/` directory when multiple features use it or it needs real and fake implementations.

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