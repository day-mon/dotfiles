# typescript style guide

## strictness

write all code as if `strict: true` is enabled. no implicit any, strict null checks, strict function types.

## types vs interfaces

- **interfaces** for object shapes that may be extended or implemented
- **types** for unions, tuples, mapped types, or complex transformations

```typescript
// interface — extendible
interface User {
  id: string;
  name: string;
}

interface Admin extends User {
  permissions: string[];
}

// type — unions, transformations
type Status = "pending" | "active" | "archived";
type Nullable<T> = T | null;
```

## no any. ever.

`any` is banned. use `unknown` when you must accept anything, then narrow.

```typescript
// bad
function parse(data: any): any { ... }

// good
function parse(data: unknown): Parsed {
  if (typeof data === "object" && data !== null) {
    return data as Parsed; // narrowing required
  }
  throw new Error("invalid");
}
```

## null vs undefined

- `null` — property exists, explicitly empty
- `undefined` — property not present at all

```typescript
interface User {
  name: string;
  bio: string | null;      // user has no bio
  deletedAt?: Timestamp;  // user not deleted
}
```

## naming

| thing | case |
|-------|------|
| types, interfaces | `PascalCase` |
| variables, functions | `camelCase` |
| constants | `SCREAMING_SNAKE_CASE` |
| boolean vars | prefix with verb: `isLoading`, `hasError` |

## return types

annotate returns on exported functions and complex logic. locals can infer.

```typescript
// exported — explicit
export function calculateTotal(items: Item[]): number { ... }

// local — infer ok
const doubled = items.map(x => x * 2);
```

## type assertions (`as`)

last resort. you must prove it first with narrowing.

```typescript
// bad
const el = document.getElementById("foo") as HTMLElement;

// better
const el = document.getElementById("foo");
if (el instanceof HTMLElement) { ... }
```

## prefer unions over enums

```typescript
// bad
enum Color { Red, Green, Blue }

// good
type Color = "red" | "green" | "blue";
const COLORS = ["red", "green", "blue"] as const;
type Color = typeof COLORS[number];
```

## functional patterns

prefer `map`, `filter`, `reduce`, `flatMap` over loops. use early returns.

```typescript
// good
const active = users
  .filter(u => u.status === "active")
  .map(u => u.name);

// good
function getUser(id: string): User | null {
  const u = lookup(id);
  if (!u) return null;
  return u;
}
```

## general

- prefer `===` and `!==`
- prefer destructuring
- prefer `??` for nullish defaults
- avoid nested ternaries
