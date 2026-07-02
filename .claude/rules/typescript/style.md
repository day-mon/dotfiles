---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "package.json"
---

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

prefer `map`, `filter`, `reduce`, `flatMap` over imperative index loops. use early returns.

```typescript
// good
function getUser(id: string): User | null {
  const u = lookup(id);
  if (!u) return null;
  return u;
}
```

### single-pass: avoid chained `.filter().map()`

a `.filter().map()` (or `.map().filter()`) chain walks the list twice and
allocates a throwaway array in between. collapse it into **one pass** with
`reduce` (preferred) or a `for...of` loop.

```typescript
// bad — two passes, intermediate array
const names = users
  .filter(u => u.status === "active")
  .map(u => u.name);

// good — one pass with reduce
const names = users.reduce<string[]>((acc, u) => {
  if (u.status === "active") acc.push(u.name);
  return acc;
}, []);
```

`flatMap` is fine when you're genuinely expanding/flattening; reach for `reduce`
when you're just filtering-and-mapping. don't force `reduce` into JSX render maps
(`items.filter(...).map(x => <Row />)`) — leave those as chains for readability.

## comments

default to **no comment**. write code that reads on its own — clear names beat a
caption. only add a comment for a genuine non-obvious *why*: a constraint, a
gotcha, a workaround, a link to context the code can't carry.

never narrate *what* the code does or *how* a line works — if it restates the
code, delete it.

```typescript
// bad — narrates the mechanics, restates the code
// w-full + justify-start makes a passed justify-end take effect (an
// intrinsic-width button can't justify its content), so the label lines up.
className={cn("-mx-2 h-7 w-full justify-start", className)}

// bad — caption a good name already gives you
// the months the selected period spans
const periodMonths = ...

// good — non-obvious why, earns its place
// RDS proxy drops idle conns at 30s; keep the pool below that.
const POOL_IDLE_MS = 25_000;
```

if you reach for a comment to explain a confusing line, rename or restructure
the line instead.

## function parameters

functions with **more than two parameters** must take a single destructured options
object, not positional args. two or fewer stay positional.

```typescript
// bad — positional, easy to mis-order at call sites
function createTicket(key: string, project: string, assignee: string, priority: number) { ... }
createTicket("DO-1", "do", "alice", 2);

// good — options object, order-independent, self-documenting
interface CreateTicketArgs {
  key: string;
  project: string;
  assignee: string;
  priority: number;
}
function createTicket({ key, project, assignee, priority }: CreateTicketArgs) { ... }
createTicket({ key: "DO-1", project: "do", assignee: "alice", priority: 2 });
```

two args stay positional — no need for an object:

```typescript
function normalizeSite(raw: string, fallback: string | null) { ... } // fine
```

exceptions: signatures you don't control — react `(prev, next)`, array callbacks
`(item, index)`, event handlers `(event)`.

## general

- prefer `===` and `!==`
- prefer destructuring
- prefer `??` for nullish defaults
- avoid nested ternaries
