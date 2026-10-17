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

Vitest has no `conftest.py`; the same job is split across three files.

| pytest | Vitest |
|---|---|
| root `conftest.py` fixtures | `tests/fixtures.ts`: one extended `test` every file imports |
| nested `tests/<area>/conftest.py` | `tests/<area>/fixtures.ts`: extends the root `test` |
| autouse session setup (MSW server) | `tests/setup.ts`, listed in `setupFiles` |

```text
tests/
├── setup.ts                 msw server lifecycle (setupFiles)
├── fixtures.ts              root `test`: settings, clients, services, app
├── factories.ts             fishery factories
├── mocks/
│   ├── handlers.ts          default msw handlers + upstream URLs
│   └── server.ts            `setupServer(...handlers)`, imported by setup and tests
├── clients/open-meteo.test.ts
└── weather/
    ├── fixtures.ts          area `test`: extends root with weather-only fixtures
    ├── routes.test.ts
    └── service.test.ts
```

- Tests mirror `src/` and live in `tests/` (see `typescript.md`). Name tests after the behavior: `test("returns 404 for an unknown city")`.
- A test file that uses fixtures imports `test` from the nearest `fixtures.ts`; `describe` and `expect` still come from `vitest`. Only a file of pure-function tests with no fixtures imports `test` from `vitest`.
- A fixture lives in `fixtures.ts`, not the test file. Area fixtures go in that area's `fixtures.ts`, which extends the root one.

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

Shared setup is a fixture, not a `let` assigned in `beforeEach`. Use the builder form; it infers types and registers cleanup with `onCleanup`. Each fixture builds on the ones above it, like pytest fixtures requesting each other.

```ts
// tests/fixtures.ts
import type { Hono } from "hono";
import { test as base } from "vitest";
import { createApp } from "../src/app";
import { OpenMeteoClient } from "../src/clients/open-meteo/client";
import { WeatherService } from "../src/weather/service";
import { SettingsFactory } from "./factories";

export const test = base
  .extend("settings", () => SettingsFactory.build())
  .extend("openMeteo", ({ settings }) => OpenMeteoClient.create(settings))
  .extend("weather", ({ openMeteo }) => new WeatherService(openMeteo))
  .extend("app", ({ weather }): Hono => createApp({ weather }));
```

```ts
// tests/weather/fixtures.ts
import { test as base } from "../fixtures";

export const test = base.extend("trackedWeather", async ({ weather, settings }) => {
  await weather.refreshTracked(settings.trackedCities);
  return weather;
});
```

```ts
// tests/weather/service.test.ts
import { HttpResponse, http } from "msw/http";
import { describe, expect } from "vitest";
import { CityNotFoundError } from "../../src/platform/errors";
import { SettingsFactory } from "../factories";
import { GEOCODING_URL } from "../mocks/handlers";
import { server } from "../mocks/server";
import { test } from "./fixtures";

test("caches the tracked cities", async ({ trackedWeather }) => {
  expect(trackedWeather.trackedCities()).toStrictEqual(["Berlin"]);
});

test("serves a tracked city without geocoding it again", async ({ trackedWeather }) => {
  server.use(http.get(GEOCODING_URL, () => HttpResponse.error()));

  await expect(trackedWeather.currentTemperature("berlin")).resolves.toMatchObject({ city: "Berlin" });
});

test("rejects an unknown city", async ({ weather }) => {
  await expect(weather.currentTemperature("Atlantis")).rejects.toBeInstanceOf(CityNotFoundError);
});

describe("with two tracked cities", () => {
  test.override("settings", () => SettingsFactory.build({ trackedCities: ["Berlin", "Tokyo"] }));

  test("refreshes every tracked city from settings", async ({ trackedWeather }) => {
    expect(trackedWeather.trackedCities()).toStrictEqual(["Berlin", "Tokyo"]);
  });
});
```

Fixtures that hold resources register cleanup:

```ts
export const test = base
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

- Fixtures are lazy: a test only builds what it destructures. Always destructure (`{ weather }`), never `(context) => context.weather`.
- A fixture with no dependencies still destructures: `({}, { onCleanup })`. Vitest rejects `(_, { onCleanup })` with a `FixtureParseError`.
- `onCleanup` callbacks return `void` or a promise. Wrap a call that returns something else in a block body, or `tsc` fails.
- Scope: test (default) for anything mutable, `file` or `worker` for expensive and immutable.
- Override a fixture with `test.override(...)` **inside a `describe`**. At the top level of a file it applies to every test in the file, including the ones above it. `test.scoped` is deprecated.
- Suite hooks that need fixtures are `test.beforeAll`, not the global `beforeAll`.

## Parameterize with `test.for`

```ts
test.for([
  { city: "Berlin", status: 200 },
  { city: "Tokyo", status: 200 },
  { city: "Atlantis", status: 404 },
])("$city returns $status", async ({ city, status }, { app }) => {
  const response = await app.request(`/v1/weather/${city}`);

  expect(response.status).toBe(status);
});
```

`test.for` over `test.each`: it doesn't spread arrays, and it passes the test context (fixtures) as the second argument. The title says the case, not just the values.

## HTTP with MSW 3

Mock the network, not `fetch` or your client. Keep the server in its own module so `setup.ts` and tests share one instance.

```ts
// tests/mocks/server.ts
import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
```

```ts
// tests/setup.ts
import { afterAll, afterEach, beforeAll } from "vitest";
import { server } from "./mocks/server";

beforeAll(() => server.listen({ onUnhandledFrame: "error" }));
afterEach(() => server.resetHandlers());
afterAll(() => server.close());
```

```ts
// tests/weather/routes.test.ts
import { HttpResponse, http } from "msw/http";
import { describe, expect } from "vitest";
import { test } from "../fixtures";
import { FORECAST_URL } from "../mocks/handlers";
import { server } from "../mocks/server";

describe("GET /v1/weather/:city", () => {
  test("returns 424 when the forecast upstream fails", async ({ app }) => {
    server.use(http.get(FORECAST_URL, () => new HttpResponse(null, { status: 503 })));

    const response = await app.request("/v1/weather/Berlin");

    expect(response.status).toBe(424);
  });
});
```

- Test HTTP apps without a server: Hono's `app.request(path)` returns a `Response`.
- Put upstream URLs in `tests/mocks/handlers.ts` and build settings from them in the factory, so handlers and the client can't disagree.
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

Every test that needs setup imports `test` from the nearest `fixtures.ts`, has a behavior name and no branches, gets setup from fixtures instead of `beforeEach` lets, mocks HTTP with MSW, awaits every async assertion, and passes `vitest run` and `tsc --noEmit`.
