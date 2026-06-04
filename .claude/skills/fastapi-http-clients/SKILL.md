---
name: fastapi-http-clients
description: Patterns for async outbound HTTP clients in a FastAPI service — an aiohttp + aiohttp-retry client class with ExponentialRetry, a timeout, raise_for_status, an async close() for lifespan teardown, and Pydantic model_validate response parsing including camelCase alias generators. Use when integrating a third-party API or building a typed async HTTP client.
---

# FastAPI outbound HTTP clients

Wrap each upstream API in a small class that owns a retrying `aiohttp` session and parses
responses into Pydantic models. Construct it in the lifespan; close it on shutdown.

## Client class

```python
import aiohttp
from aiohttp_retry import ExponentialRetry, RetryClient
from myapp.clients.actionnetwork import types

class ActionNetworkClient:
    """Client for the ActionNetwork odds API."""

    _BASE_URL = "https://api.actionnetwork.com"

    def __init__(self) -> None:
        self._session = RetryClient(
            base_url=self._BASE_URL,
            timeout=aiohttp.ClientTimeout(total=30),
            raise_for_status=True,
            retry_options=ExponentialRetry(attempts=3),
        )

    async def close(self) -> None:
        await self._session.close()

    async def fetch_odds(self, date: str) -> types.ActionNetworkResponse:
        async with self._session.get(
            url="/web/v1/scoreboard/nba",
            params={"period": "game", "date": date},
        ) as resp:
            data = await resp.json()
        return types.ActionNetworkResponse.model_validate(data)
```

- `RetryClient` with `ExponentialRetry(attempts=3)` and a total timeout.
- `raise_for_status=True` so 4xx/5xx raise `aiohttp.ClientResponseError` — caught centrally by
  the handler in `fastapi-app-composition` (map to a `424`).
- `async close()` is awaited in the lifespan teardown.
- Parse with `Model.model_validate(...)`; return a typed model, never a raw dict.

## Typed responses

Define response models in a sibling `types.py`. When the upstream uses camelCase, give the
models a base that maps to snake_case via an alias generator.

```python
import pydantic
from pydantic.alias_generators import to_camel

class _CamelModel(pydantic.BaseModel):
    """Accepts camelCase from the API; uses snake_case internally."""
    model_config = pydantic.ConfigDict(alias_generator=to_camel, populate_by_name=True)

class Team(_CamelModel):
    team_id: int
    team_name: str

class ActionNetworkResponse(pydantic.BaseModel):
    games: list[Team]
```

## Lifecycle wiring

Create clients once in the lifespan, pass them into the services that use them, and close them on
shutdown (see `fastapi-app-composition`):

```python
@contextlib.asynccontextmanager
async def lifecycle(app):
    client = ActionNetworkClient()
    app.state.odds_service = OddsService(client=client)
    yield
    await client.close()
```

A service can fan out concurrent calls with `asyncio.gather`:

```python
games, odds = await asyncio.gather(self._fetch_games(), self._fetch_odds())
```

## Rules

- One client class per upstream API; it owns a single `RetryClient` for its lifetime.
- Configure `ExponentialRetry`, a `ClientTimeout`, and `raise_for_status=True`.
- Expose `async close()` and call it in the lifespan teardown — don't leak sessions.
- Parse every response with a Pydantic model (`model_validate`); keep models in `types.py`.
- For camelCase upstreams, use a `_CamelModel` base with `alias_generator=to_camel` +
  `populate_by_name=True`.
- Let `ClientResponseError` propagate to the central error handler; don't swallow upstream errors.
