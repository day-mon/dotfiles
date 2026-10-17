# Vitest

Apply to TypeScript and React tests. Read `testing.md` first; this file says how to do it the Vitest way. Targets Vitest 5, MSW 3, fishery 2.

## Configuration

```ts
import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import { playwright } from "@vitest/browser-playwright";

export default defineConfig({
  plugins: [react()],
  test: {
    restoreMocks: true,
    unstubEnvs: true,
    unstubGlobals: true,
    projects: [
      {
        test: {
          name: "unit",
          environment: "node",
          include: ["tests/**/*.test.ts"],
          setupFiles: ["tests/setup.ts"],
        },
      },
      {
        test: {
          name: "browser",
          include: ["tests/**/*.test.tsx"],
          browser: { enabled: true, headless: true, provider: playwright(), instances: [{ browser: "chromium" }] },
        },
      },
    ],
  },
});
```

Browser Mode needs `@vitest/browser-playwright` and `vitest-browser-react` as dev dependencies, and `npx playwright install chromium` once.

- Vitest 5 already defaults `clearMocks: true`. Add `restoreMocks`, `unstubEnvs`, and `unstubGlobals`, so no test leaks a spy, env var, or global into the next.
- Inline projects inherit the root config in Vitest 5, so shared options live at the root once.
- No `globals: true`. Import `describe`, `expect`, `test`, `vi` from `vitest` in every file.
- Add `.vitest` to `.gitignore`; every report goes there.

## Layout

```text
tests/
├── setup.ts            msw server lifecycle
├── fixtures.ts         the extended `test` with shared fixtures
├── factories.ts        fishery factories
├── mocks/handlers.ts   default msw handlers
└── weather/get-weather.test.ts
```

Tests mirror `src/` and live in `tests/` (see `typescript.md`). Name tests after the behavior: `test("returns 404 for an unknown city")`.

## Plain tests and exact assertions

```ts
import { expect, test } from "vitest";

test("converts celsius to fahrenheit", () => {
  expect(toFahrenheit(100)).toBe(212);
});
```

- `test`, not `it`. Use `describe` only to group a unit with several behaviors, never just to repeat the file name.
- No `if`, `for`, or `try` in a test. Cases go in `test.for`; branches become two tests.
- `toStrictEqual` for objects (it checks `undefined` keys and class types); `toBe` for primitives; `toBeCloseTo` for floats.
- Await every async assertion: `await expect(p).resolves.toStrictEqual(...)`. Vitest 5 fails a test with an unawaited one.
- `await expect.poll(() => fn(), { timeout })` to wait for something eventually true. Never `setTimeout` to wait.
- `expectTypeOf` for type-level contracts, in `*.test-d.ts` files.

## Fixtures with `test.extend`

Shared setup is a fixture, not a `let` assigned in `beforeEach`. Use the builder form; it infers types and registers cleanup with `onCleanup`.

```ts
import { test as base } from "vitest";

export const test = base
  .extend("settings", () => SettingsFactory.build())
  .extend("weather", ({ settings }, { onCleanup }) => {
    const service = new WeatherService(OpenMeteoClient.create(settings));
    onCleanup(() => service.close());
    return service;
  })
  .extend("db", { scope: "file" }, async ({}, { onCleanup }) => {
    const db = await createTestDatabase();
    onCleanup(() => db.close());
    return db;
  })
  .extend("now", ({}, { onCleanup }) => {
    const now = new Date("2030-01-01T00:00:00Z");
    vi.useFakeTimers({ now });
    onCleanup(() => {
      vi.useRealTimers();
    });
    return now;
  });
```

```ts
import { expect } from "vitest";
import { test } from "../fixtures";

test("caches tracked cities", async ({ weather }) => {
  await weather.refreshTracked(["Berlin"]);

  expect(weather.cachedCities()).toStrictEqual(["Berlin"]);
});
```

- Fixtures are lazy: a test only builds what it destructures. Always destructure (`{ weather }`), never `(context) => context.weather`.
- A fixture with no dependencies still destructures: `({}, { onCleanup })`. Vitest rejects `(_, { onCleanup })` with a `FixtureParseError`.
- `onCleanup` callbacks return `void` or a promise. Wrap a call that returns something else in a block body, or `tsc` fails.
- Scope: test (default) for anything mutable, `file` or `worker` for expensive and immutable.
- Override per suite with `test.override("settings", ...)`, not by mutating a fixture. `test.scoped` is deprecated.
- Suite hooks that need fixtures are `test.beforeAll`, not the global `beforeAll`.

## Parameterize with `test.for`

```ts
test.for([
  { input: "Berlin", status: 200 },
  { input: "Atlantis", status: 404 },
])("GET /weather/$input returns $status", async ({ input, status }, { api }) => {
  const response = await api.get(`/weather/${input}`);

  expect(response.status).toBe(status);
});
```

`test.for` over `test.each`: it doesn't spread arrays, and it passes the test context (fixtures) as the second argument. The title says the case, not just the values.

## HTTP with MSW 3

Mock the network, not `fetch` or your client.

```ts
// tests/setup.ts
import { afterAll, afterEach, beforeAll } from "vitest";
import { setupServer } from "msw/node";
import { handlers } from "./mocks/handlers";

export const server = setupServer(...handlers);

beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```ts
import { http, HttpResponse } from "msw/http";

test("returns 424 when the upstream is down", async ({ api }) => {
  server.use(http.get("https://api.open-meteo.com/v1/forecast", () => new HttpResponse(null, { status: 503 })));

  const response = await api.get("/weather/Berlin");

  expect(response.status).toBe(424);
});
```

- MSW 3 imports: `http`/`HttpResponse` from `msw/http`, `setupServer` from `msw/node`, `delay` from `msw/utils/delay`.
- `onUnhandledFrame: "error"` so a request nobody mocked fails the test.
- Per-test responses go through `server.use(...)`; `resetHandlers` undoes them.

## Mocks and spies, in order of preference

1. **Inject a fake** or a real object built by a factory.
2. **MSW** for anything over HTTP.
3. **`vi.spyOn(obj, "method")`** for a boundary you don't own. Restored automatically by `restoreMocks`.
4. **`vi.mock("module")`** only for a module you can't inject. Vitest 5 throws if it isn't at the top level of the file. Use `vi.hoisted` for values the factory needs, and `vi.mocked(fn)` for types.

Type every mock: `vi.fn<typeof fetchWeather>()`. Never assert that an internal helper was called; assert what the caller sees.

## Time and environment

- Fake the clock in a fixture (the `now` fixture above): `vi.useFakeTimers({ now })`, restored in `onCleanup`. In Vitest 5 this also fakes `Temporal`.
- Advance time with `await vi.advanceTimersByTimeAsync(ms)`, not the sync version, when promises are involved.
- `vi.stubEnv("KEY", "value")`, never assign `process.env` directly; `unstubEnvs` restores it.

## Factories with fishery

```ts
import { Factory } from "fishery";

export const UserFactory = Factory.define<User>(({ sequence }) => ({
  id: `user-${sequence}`,
  name: "Ada",
  role: "member",
}));

const admin = UserFactory.build({ role: "admin" });
```

Types come from the zod schema (`z.infer`), so a factory that drifts from the contract stops compiling.

## React components

Run component tests in Browser Mode (a real browser), with `vitest-browser-react`.

```tsx
import { expect, test } from "vitest";
import { render } from "vitest-browser-react";

test("shows the temperature for a city", async () => {
  const screen = await render(<Weather city="Berlin" />);

  await screen.getByRole("button", { name: "Refresh" }).click();

  await expect.element(screen.getByRole("status")).toHaveTextContent("10.9 °C");
});
```

- Query by role and accessible name first, then label, then text. Never by class or test id unless nothing else is accessible.
- `expect.element(...)` retries until it passes; don't wrap it in `expect.poll`.
- Locators match exact text by default in Vitest 5. Use `toMatchTextContent` for partial or regex matches.
- Interact through the locator (`.click()`, `.fill()`), not by calling handlers or setting state.

## Running

- `vitest run` in CI, `vitest` while iterating; `--project unit` to run one project.
- `--repeats 20` to chase a flaky test. A flaky test is a bug; fix it or delete it, no `retry`.

## Before finishing

Every test imports from `vitest`, has a behavior name and no branches, uses fixtures instead of `beforeEach` lets, mocks HTTP with MSW, awaits every async assertion, and passes `vitest run`.
