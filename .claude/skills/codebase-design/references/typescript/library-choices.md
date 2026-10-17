# TypeScript Library Choices

Prefer these defaults; record the concrete pick in the design output and justify any deviation. Keep one default per concern.

| Concern | Default | Notes |
| --- | --- | --- |
| HTTP client | `ky` | One class per API; auth, retry, and logging through ky hooks. |
| Env config | `@t3-oss/env-core` | zod-validated; required vars have no default. No manual `process.env` checks. |
| Validation | `zod` | Including custom schemas for config formats (e.g. `provider:model`). |
| Errors | `better-result` | `Result.tryPromise` / `Result.try`; retries are built in. |
| Logging | `pino` | `logger.error({ err }, "msg")`; `redact` paths instead of sanitize functions. |
| HTTP mocks in tests | `msw` | Never hand-mocked `fetch`; follow the msw setup docs. |
| URL state | `nuqs` | Debounce with TanStack Pacer. |
| Client data | TanStack Query | Queries and mutations live in `queries/`. |
| CLI | `oclif` | Class commands in `commands/`. |
| Caching | `lru-cache` | Never a hand-rolled LRU. |
| Agents | AI SDK | `ToolLoopAgent`, `createProviderRegistry`, `onFinish`/step hooks for usage and telemetry. |
| File IO (Bun) | `Bun.file` | Never `node:fs` in Bun apps. |

## Class-based client pattern (`ky`)

```ts
import ky, { type KyInstance } from "ky";

export class LatticeClient {
  private static readonly BASE_URL = "https://api.latticehq.com";
  private static readonly TIMEOUT_MS = 30_000;

  private constructor(private readonly http: KyInstance) {}

  static create({ apiKey }: { apiKey: string }): LatticeClient {
    return new LatticeClient(
      ky.create({
        baseUrl: LatticeClient.BASE_URL,
        timeout: LatticeClient.TIMEOUT_MS,
        headers: { authorization: `Bearer ${apiKey}` },
        retry: { limit: 3 },
      }),
    );
  }

  async user(id: string): Promise<User> {
    return UserSchema.parse(await this.http.get(`v1/users/${encodeURIComponent(id)}`).json());
  }
}
```

- ky 2: `baseUrl` (resolved like `new URL(input, baseUrl)`), not the removed `prefixUrl`.
- Constants are `private static readonly`.
- Construction goes through `static create()`.
- Responses are parsed with zod at the client boundary.
- Errors propagate; the app's global handler maps them.
