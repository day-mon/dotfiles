# typescript typing patterns

## strict null handling

model your types to make impossible states unrepresentable.

```typescript
// bad — both optional, many invalid combinations
interface User {
  name?: string;
  email?: string;
  verified?: boolean;
}

// good — states are explicit
type User =
  | { status: "anonymous" }
  | { status: "registered"; name: string; email: string; verified: boolean };
```

## branded types for primitives

avoid stringly-typed errors.

```typescript
type UserId = string & { readonly __brand: unique symbol };
type OrderId = string & { readonly __brand: unique symbol };

function makeUserId(id: string): UserId {
  return id as UserId;
}

// UserId and OrderId are not interchangeable
```

## function overloads vs unions

prefer unions for simple cases, overloads when return type depends on input.

```typescript
// union — simple
type Status = "pending" | "active" | "archived";

// overloads — return varies by input
function fetch(id: string): Promise<User>;
function fetch(ids: string[]): Promise<User[]>;
function fetch(id: string | string[]): Promise<User | User[]> {
  return Array.isArray(id) ? fetchMany(id) : fetchOne(id);
}
```

## mapped types

use for deriving types instead of duplicating.

```typescript
type Readonly<T> = { readonly [K in keyof T]: T[K] };
type Optional<T> = { [K in keyof T]?: T[K] };

type User = { id: string; name: string };
type ReadonlyUser = Readonly<User>;
```

## type guards

write explicit predicates.

```typescript
function isString(value: unknown): value is string {
  return typeof value === "string";
}

function process(data: unknown) {
  if (isString(data)) {
    // data is string here
  }
}
```

## discriminated unions

always include a discriminator.

```typescript
type Event =
  | { type: "click"; x: number; y: number }
  | { type: "keypress"; key: string }
  | { type: "scroll"; delta: number };

function handle(e: Event) {
  switch (e.type) {
    case "click":
      console.log(e.x, e.y); // narrowed
      break;
  }
}
```

## infer from implementations

use `satisfies` or `as const` to get strict inference without widening.

```typescript
// widens to string[]
const colors = ["red", "green", "blue"];

// preserves literal types
const colors = ["red", "green", "blue"] as const;
type Color = typeof colors[number]; // "red" | "green" | "blue"

// satisfies — check without widening
const config = {
  timeout: 30,
  retries: 3
} satisfies { timeout: number; retries: number };
```

## avoid index signatures

prefer explicit keys or mapped types.

```typescript
// bad
interface Dict {
  [key: string]: string;
}

// better — partial with known keys
interface Config {
  host?: string;
  port?: number;
}

// best — record for generic maps
type Cache<T> = Record<string, T | undefined>;
```
