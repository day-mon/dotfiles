---
name: fastapi-http-clients
description: Patterns for async outbound HTTP clients in a FastAPI service — an aiohttp + aiohttp-retry client class with ExponentialRetry, a timeout, raise_for_status, create()/aclose() and async-context-manager lifecycle opened in the lifespan, and Pydantic response parsing including camelCase alias generators. Use when integrating a third-party API or building a typed async HTTP client.
---

# FastAPI outbound HTTP clients

Check for an official SDK first and wrap it if one exists. Otherwise, one class per upstream API
owns a retrying `aiohttp` session and parses responses into Pydantic models. The full class
shape (`_request`, `TypeAdapter`, request logging) lives in
`codebase-design/references/python/library-choices.md`; this skill covers the FastAPI wiring.

## Client class

```python
from typing import ClassVar, Self

import aiohttp
from aiohttp_retry import ExponentialRetry, RetryClient

from myapp.clients.actionnetwork import schemas
from myapp.core.config.actionnetwork import ActionNetworkSettings


class ActionNetworkClient:
    TIMEOUT_SECONDS: ClassVar[float] = 30
    RETRY_ATTEMPTS: ClassVar[int] = 3

    def __init__(self, *, base_url: str) -> None:
        self.session = RetryClient(
            client_session=aiohttp.ClientSession(
                base_url=base_url,
                timeout=aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS),
                raise_for_status=True,
            ),
            retry_options=ExponentialRetry(attempts=self.RETRY_ATTEMPTS),
        )

    @classmethod
    def create(cls, settings: ActionNetworkSettings) -> Self:
        return cls(base_url=settings.base_url)

    async def aclose(self) -> None:
        await self.session.close()

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.aclose()

    async def fetch_odds(self, *, date: str) -> schemas.ScoreboardResponse:
        async with self.session.get(
            "/web/v1/scoreboard/nba",
            params={"period": "game", "date": date},
        ) as response:
            data = await response.json()
        return schemas.ScoreboardResponse.model_validate(data)
```

- Constants are `ClassVar`s; no bare numbers in the constructor.
- `raise_for_status=True`, so 4xx/5xx raise `aiohttp.ClientResponseError`, which the central
  handler in `fastapi-app-composition` maps to a `424`.
- Construction from settings is `create()`; teardown is `aclose()` via `async with`.
- Return a typed model, never a raw dict.

## Typed responses

Response models live in the client's `schemas.py`. For camelCase upstreams, use a base with an
alias generator.

```python
import pydantic
from pydantic.alias_generators import to_camel


class CamelModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(alias_generator=to_camel, populate_by_name=True)


class Team(CamelModel):
    team_id: int
    team_name: str


class ScoreboardResponse(CamelModel):
    games: list[Team]
```

## Lifecycle wiring

Open clients in the lifespan's single `async with`, so they close even when startup fails
partway (see `fastapi-app-composition`).

```python
@contextlib.asynccontextmanager
async def lifecycle(app: fastapi.FastAPI) -> AsyncIterator[None]:
    async with ActionNetworkClient.create(actionnetwork_settings) as odds:
        app.state.odds_service = OddsService(client=odds)
        yield
```

A service can fan out concurrent calls with `asyncio.gather`:

```python
games, odds = await asyncio.gather(self._fetch_games(), self._fetch_odds())
```

## Rules

- Official SDK first; hand-written client only when none exists.
- One client class per upstream API; it owns a single `RetryClient` for its lifetime.
- `ExponentialRetry`, a `ClientTimeout`, and `raise_for_status=True`; constants are `ClassVar`s.
- `create(settings)` builds it; `async with` in the lifespan closes it.
- Parse every response with a Pydantic model in the client's `schemas.py`.
- camelCase upstreams use a `CamelModel` base with `alias_generator=to_camel`.
- Let `ClientResponseError` propagate to the central handler; don't catch or wrap it.
