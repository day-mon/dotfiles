# Next.js Cache Components

Apply every relevant rule in Next.js 16.3 or later when `cacheComponents: true` is enabled.

## Choose stream, cache, or block

Every server-side await of uncached data needs one rendering choice.

- **Stream** slow data inside a local `Suspense` boundary. The shell renders first and data replaces the fallback later.
- **Cache** reusable, non-request data with `use cache` and `cacheLife`. The cached result becomes part of the static shell.
- **Block** fast request-time reads with `export const instant = false`, then await directly. Navigation keeps the current page visible until the next page is complete.

```tsx
export const instant = false;

export default async function Page() {
  const data = await repository.getThing();
  return <Thing data={data} />;
}
```

`instant = false` permits the blocking route. Awaiting without a `Suspense` boundary creates the blocking behavior.

## Keep boundaries local

`loading.tsx` is one coarse `Suspense` boundary around its route segment and descendants. Use it only when the whole segment should share one fallback.

For per-page streaming or blocking, remove the segment's `loading.tsx` and place `Suspense` around the specific slow read. A segment-level loading file overrides finer choices below it.

## Cache only build-reachable data

A `use cache` function can run during the build. Do not cache a database or service read into the static shell when that dependency is unavailable in CI or the build container. Stream or block it so the read happens at request time.

## Mark request-time values

Before using `new Date()`, `Date.now()`, `Math.random()`, or `crypto.randomUUID()` during server rendering, call `await connection()` from `next/server`.

```tsx
import { connection } from "next/server";

await connection();
const now = new Date();
```

Compute browser-only values in an effect or event handler, not during render.

## Remove legacy route configuration

With Cache Components enabled, do not export `dynamic`, `runtime`, `revalidate`, or `fetchCache`. Translate the behavior to Cache Components primitives. A constant route handler needs no config to be static.

## Keep `server-only` at Next.js leaves

Do not import `server-only` from modules shared with plain Node or Bun scripts such as seeders, migrations, cron jobs, and CLIs. Put it in leaf modules imported only by the Next.js server graph.

## Handle params at the chosen boundary

Awaiting `params` or `searchParams` makes the route request-time.

- For streaming, pass the promise into the `Suspense` child and await it there.
- For blocking, await it in the page.
- For interactive URL state, use Nuqs with `shallow: false` so the server rerenders. Parse the same values on the server with `createLoader`.

## Mutate through Server Actions

Use a `use server` action, validate input with Zod, perform the write, then call `revalidatePath` or `revalidateTag`. Prefer this to a client fetch plus a query cache for server-owned data.

## Trust the React Compiler within its limits

When `reactCompiler: true` is enabled, remove routine `useMemo` and `useCallback`. Keep manual memoization only for measured work or an API identity contract. The compiler does not fix impure rendering or effect misuse.

Before completing Next.js work, verify every uncached await has an explicit rendering choice, each fallback is at the intended boundary, cached data is reachable during builds, request-time values follow `connection()`, and no legacy route config remains.
