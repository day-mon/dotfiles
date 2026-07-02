# next.js app router patterns (cache components era)

for next.js 16.3+ with `cacheComponents: true`. these are the rules that bite in
practice, learned the hard way.

## rendering: stream vs cache vs block

with cache components, every `await` of uncached data on the server is a choice.
pick one per route:

- **stream** — wrap the read in `<Suspense fallback={...}>`. instant shell, data
  streams into the fallback. right when the data is genuinely slow.
- **cache** — `'use cache'` + `cacheLife(...)`. the result renders into the static
  shell (no fallback). right for cacheable, non-per-request data.
- **block** — `export const instant = false` and `await` the data directly (no
  `<Suspense>`). navigation holds the current page until the read resolves, then
  swaps to the full page. **right for fast reads** — a held nav (~query time) feels
  better than a skeleton that flashes for 50ms.

```tsx
// block: fast DB read, no skeleton flash
export const instant = false

export default async function Page() {
  const data = await repo.getThing()   // no <Suspense> wrapper
  return <Thing data={data} />
}
```

`instant = false` only silences the blocking-route validation; the actual blocking
comes from awaiting without a `<Suspense>` above the read.

## loading.tsx is a coarse suspense boundary

`loading.tsx` is sugar for wrapping the whole route segment (and its children) in
one `<Suspense>`. it sits *above* per-page boundaries and fires on every nav into
the segment, so it silently overrides finer `<Suspense>`/Block choices below it.

**don't combine `loading.tsx` with per-page `<Suspense>` or Block.** pick one:
`loading.tsx` only when a single whole-segment skeleton is genuinely what you want;
otherwise delete it and place `<Suspense>` near the specific slow data (or Block).
a stray segment `loading.tsx` is the usual cause of "why is a skeleton still
flashing when I removed the per-page one".

## use `'use cache'` only if the data source exists at build

`'use cache'` renders the function into the static shell, which means it runs **at
build time**. if it reads a DB/service that isn't reachable during the build (common
for CI/containerized builds with no DB), the build fails (`ECONNREFUSED`). for
DB-backed reads with a DB-less build, don't cache into the shell — Stream or Block
and let it run at request time.

## request-time values need `connection()`

`new Date()`, `Date.now()`, `Math.random()`, `crypto.randomUUID()` are impure and
fail the build under cache components (even with `instant = false`). if you need one
on the server, gate it behind `await connection()` (from `next/server`), which marks
the render request-time and permits it. otherwise compute it on the client (in an
effect / event), never during render.

```tsx
import { connection } from 'next/server'
await connection()          // prerendering stops here
const now = new Date()      // now allowed
```

## no legacy route-segment config

under `cacheComponents`, these throw at build: `export const dynamic`,
`export const runtime`, `export const revalidate`, `export const fetchCache`.
translate them, don't set them. a constant route handler is static by default with
no config needed.

## `server-only` breaks non-next entrypoints

`import 'server-only'` throws when imported outside a react-server graph. do **not**
put it in modules that are also imported by plain node/bun scripts (cron CLIs,
seeders, migrations). keep it on leaf modules only the next app imports; the DB
driver / node deps already keep those server-side.

## searchParams / params are request-time

awaiting `searchParams` or `params` makes the route dynamic. under **Stream**,
forward the promise into the `<Suspense>`-wrapped child and await it there (don't
`await` at the top of the page, or the whole page blocks the shell). under **Block**,
await it directly in the page. drive interactive URL state with `useQueryStates`
(nuqs) + `shallow: false` so the server re-renders; use nuqs `createLoader` to parse
the same params on the server.

## mutations

use Server Actions (`'use server'`), validate input with zod, then
`revalidatePath`/`revalidateTag`. don't reach for client fetch + a query cache.

## react compiler

with `reactCompiler: true`, drop most manual `useMemo`/`useCallback` — it
auto-memoizes. it does **not** fix impurities (it bails on them) or effect misuse, so
`Math.random()` in render, setState-in-effect, etc. still need real fixes.
