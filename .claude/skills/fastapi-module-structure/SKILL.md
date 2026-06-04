---
name: fastapi-module-structure
description: The vertical-slice module layout for FastAPI services — api/v<n>/<domain>/ split into routes.py, schemas.py, service.py, types.py, constants.py, __init__.py — with thin route controllers delegating to service classes and two-level router aggregation. Use when scaffolding a new FastAPI API domain or organizing endpoints, services, schemas, and internal types.
---

# FastAPI module structure

Organize the API as vertical slices: one directory per domain, each holding its own routes,
schemas, service, and types. Routes stay thin and delegate to a service class.

## Layout

```
api/
├── __init__.py            # empty; aggregation happens at the version level
└── v1/
    ├── __init__.py        # versioned router: prefix="/v1", includes domain routers
    └── <domain>/
        ├── __init__.py    # exports `router`
        ├── routes.py      # APIRouter + path operations (HTTP layer)
        ├── schemas.py     # public Pydantic request/response models
        ├── service.py     # business logic (a stateful class)
        ├── types.py       # internal dataclasses / TypedDicts (never serialized)
        └── constants.py   # domain lookup tables / constants (optional)
```

Not every domain needs every file. A trivial `health` domain may be just `routes.py` +
`schemas.py` + `__init__.py`. Add files as the domain grows.

## What each file holds

- **routes.py** — `APIRouter`, the service dependency, and thin path operations. See
  `fastapi-routing`.
- **schemas.py** — `pydantic.BaseModel` HTTP contracts (the serialized shape). Public-facing
  fields only.
- **service.py** — a class holding injected dependencies (session, clients) with `async`
  methods that do the work.
- **types.py** — internal working types (`@dataclass`, `TypedDict`) used between the service and
  external sources. Never returned directly over HTTP.
- **constants.py** — domain-local constants (lookup maps, skip lists). Keep them colocated, not
  in a global module.

### schemas.py vs types.py

`schemas.py` is the API boundary; `types.py` is internal. The service transforms external/DB
data into `types.py`, then converts to `schemas.py` at the HTTP edge. This decouples the wire
format from internal logic.

```python
# types.py — internal, with factory methods
import dataclasses

@dataclasses.dataclass(slots=True)
class RawGame:
    home: str
    away: str

    @classmethod
    def from_upstream(cls, payload: dict) -> "RawGame":
        return cls(home=payload["h"], away=payload["a"])
```

```python
# schemas.py — public contract
import pydantic

class GameOut(pydantic.BaseModel):
    """A game as returned by the API."""
    home_team: str
    away_team: str
```

## Thin controllers delegating to a service

The route extracts parameters and calls the service. The service holds the logic.

```python
# service.py
class PredictionService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, prediction_id: int) -> types.Prediction: ...
```

```python
# routes.py
import typing
import fastapi
from myapp.core.dependencies.database import Session

router = fastapi.APIRouter(prefix="/predictions", tags=["predictions"])

def get_service(session: Session) -> service.PredictionService:
    return service.PredictionService(session)

ServiceDep = typing.Annotated[service.PredictionService, fastapi.Depends(get_service)]

@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: typing.Annotated[int, fastapi.Path(ge=1)],
    svc: ServiceDep,
) -> schemas.PredictionOut:
    return await svc.get(prediction_id)
```

Services that need long-lived dependencies (HTTP clients, ML models) can instead be constructed
once in the lifespan and stored on `app.state`, then read by `get_service`. See
`fastapi-app-composition`.

## Router aggregation (two levels)

Each domain `__init__.py` exports its router:

```python
# api/v1/predictions/__init__.py
from myapp.api.v1.predictions.routes import router
__all__ = ["router"]
```

The version `__init__.py` aggregates them under the version prefix:

```python
# api/v1/__init__.py
from fastapi import APIRouter
from myapp.api.v1 import health, predictions

router = APIRouter(prefix="/v1")
router.include_router(health.router)
router.include_router(predictions.router)
__all__ = ["router"]
```

The app includes the version router (see `fastapi-app-composition`).

## Rules

- One directory per domain under `api/v<n>/`; keep routes, schemas, service, and types separate.
- `schemas.py` = Pydantic HTTP contracts; `types.py` = internal dataclasses/TypedDicts. Never
  return a `types.py` object straight to the client unless it matches a declared schema.
- Routes are thin: extract params, call the service, return.
- Services are classes that receive dependencies via injection — not module-level globals.
- Domain `__init__.py` exports `router`; aggregate with the version prefix at `v<n>/__init__.py`.
- Do NOT use relative imports in `api/**/__init__.py`.
