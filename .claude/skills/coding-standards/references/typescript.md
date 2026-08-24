# TypeScript

Apply every relevant rule to TypeScript source.

## Strict code

Write code that passes with `strict: true`.

- Use interfaces for extendable object shapes.
- Use type aliases for unions, tuples, mapped types, and transformations.
- Prefer literal unions and `as const` collections to enums.
- Use `unknown` at untrusted boundaries, then validate or narrow it.
- Use `null` for a present but empty value. Use `undefined` or an optional property for an absent value.
- Add return types to exported functions and complex local logic. Let simple locals infer.
- Prefer `===`, `!==`, destructuring, and `??`.
- Keep ternaries flat.

`any` is not an escape hatch. A type assertion is a last resort after runtime evidence or a narrow boundary proves the type.

```typescript
const element = document.getElementById("profile");
if (!(element instanceof HTMLElement)) {
  throw new Error("#profile must be an HTMLElement");
}
```

## Naming

| Item | Convention |
| --- | --- |
| Types and interfaces | `PascalCase` |
| Variables and functions | `camelCase` |
| Constants | `SCREAMING_SNAKE_CASE` |
| Booleans | Verb prefix such as `isLoading` or `hasError` |

## Function boundaries

Use positional parameters for two or fewer arguments. For more than two arguments, accept one destructured object with a named interface.

```typescript
interface CreateTicketArgs {
  key: string;
  project: string;
  assignee: string;
  priority: number;
}

function createTicket({ key, project, assignee, priority }: CreateTicketArgs) {
  // ...
}
```

Keep signatures imposed by libraries unchanged.

## Collections

Prefer `map`, `filter`, `reduce`, and `flatMap` to index-driven loops.

Collapse a filter-and-map chain into one pass when the extra traversal and intermediate array matter. Use `reduce` or `for...of`. Keep a readable chain in JSX and in non-hot code where the performance difference is irrelevant.

## Model states explicitly

Use a discriminated union when fields depend on a state. Every variant should have a stable discriminator.

```typescript
type User =
  | { status: "anonymous" }
  | {
      status: "registered";
      name: string;
      email: string;
      verified: boolean;
    };
```

## Brand domain primitives

Brand primitives when mixing two values of the same runtime type would be a domain error. Create branded values at a validated boundary instead of scattering assertions.

```typescript
declare const userIdBrand: unique symbol;
type UserId = string & { readonly [userIdBrand]: true };

declare const orderIdBrand: unique symbol;
type OrderId = string & { readonly [orderIdBrand]: true };
```

## Choose unions or overloads

Use a union when inputs share one return type. Use overloads when the return type depends on the input shape.

```typescript
function fetchUser(id: string): Promise<User>;
function fetchUser(ids: string[]): Promise<User[]>;
function fetchUser(id: string | string[]): Promise<User | User[]> {
  return Array.isArray(id) ? fetchMany(id) : fetchOne(id);
}
```

## Derive instead of duplicate

Use mapped and utility types to derive related shapes. Use `as const` to preserve literals and `satisfies` to check a value without widening it.

```typescript
const COLORS = ["red", "green", "blue"] as const;
type Color = (typeof COLORS)[number];

const config = {
  retries: 3,
  timeout: 30,
} satisfies { retries: number; timeout: number };
```

## Narrow unknown values

Write explicit type predicates or parse untrusted data with a schema. Do not cast an unchecked object into the desired type.

```typescript
function isString(value: unknown): value is string {
  return typeof value === "string";
}
```

## Keep keys explicit

Prefer named properties when the key set is known. Use `Record<Key, Value>` for a genuine map. Include `undefined` when a lookup may miss.

## Comments

Default to clear code with no comment. Add a comment only for a non-obvious constraint, workaround, tradeoff, or external fact. Rename or restructure confusing code before explaining it with a comment.

## Tooling

Use the repository's existing commands first. Supplement them rather than replacing project configuration.

Use Bun for dependency and script work. Prefer `bunx --bun` for one-off TypeScript tools. Fall back to plain `bunx` when a package is incompatible with Bun's runtime.

Run Biome alongside the repository's configured formatter and linter. Scope it to changed files when a full-repository run would be slow or would rewrite unrelated code.

```bash
bunx --bun @biomejs/biome check .
bunx --bun @biomejs/biome format --write .
bunx --bun @biomejs/biome lint --write .
```

Run the repository's type-check script when one exists. Otherwise run:

```bash
bunx --bun tsc --noEmit
```

Before completing TypeScript work, verify the changed code is strict, contains no `any`, proves each assertion, models state explicitly, narrows unknown values, and passes the repository checks, Biome, and TypeScript for the changed scope. Report any blocked check and its exact reason.
