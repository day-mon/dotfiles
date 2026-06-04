---
name: fastapi-routing
description: Conventions for FastAPI routers and path operations — router-level prefix/tags/dependencies, Annotated path/query/header/body parameters, declared return types and response_model for serialization, one HTTP operation per function, and choosing async def vs def. Use when adding or editing FastAPI endpoints, routers, or request/response parameters.
---

# FastAPI routing

Opinionated path-operation and router conventions. The big wins: `Annotated` everywhere,
declared return types for serialization, and one operation per function.

## Router definition

Set `prefix` and `tags` on the `APIRouter`, not on `include_router`.

```python
import fastapi

router = fastapi.APIRouter(
    prefix="/predictions",
    tags=["predictions"],
    dependencies=[fastapi.Depends(verify_api_key)],  # shared across every op
)
```

**Do NOT** pass `prefix`/`tags` to `app.include_router(router, prefix=..., tags=...)`.

## One HTTP operation per function

```python
@router.get("")
async def list_predictions() -> list[PredictionOut]: ...

@router.post("")
async def create_prediction(data: PredictionIn) -> PredictionOut: ...
```

Never use `@router.api_route("", methods=["GET", "POST"])` with `request.method` branching.

## Annotated parameters

Always use `typing.Annotated` for path, query, header, and body parameters.

```python
import typing
import fastapi

@router.get("/{prediction_id}")
async def get_prediction(
    prediction_id: typing.Annotated[int, fastapi.Path(ge=1)],
    include_history: typing.Annotated[bool, fastapi.Query()] = False,
) -> PredictionOut: ...
```

**Do NOT** write `prediction_id: int = fastapi.Path(ge=1)` (the old non-`Annotated` form).

Inject dependencies the same way — see `fastapi-dependencies` for the type-alias pattern.

## Return types and response models

Always declare a return type. FastAPI uses it to validate, filter, and serialize the response
through Pydantic (the Rust core), which is the main performance path.

```python
@router.get("/me")
async def get_current() -> UserOut:
    return UserOut.model_validate(internal_user)
```

When the value you return differs from the shape you want to serialize, set `response_model` on
the decorator and annotate the return as `typing.Any`. This is the primary way to avoid leaking
sensitive fields:

```python
@router.get("/me", response_model=UserOut)
async def get_current() -> typing.Any:
    return internal_user  # extra fields stripped by UserOut
```

Document non-200 responses with `responses=`:

```python
@router.get("/daily", responses={424: {"description": "Upstream dependency failed"}})
async def get_daily() -> list[GameOut]: ...
```

## async def vs def

Use `async def` only when the body is genuinely awaitable. For blocking work, use plain `def`
so FastAPI runs it in a threadpool instead of stalling the event loop.

```python
# Good — awaits an async client
@router.get("/items")
async def read_items() -> list[Item]:
    return await client.fetch_items()

# Good — blocking library runs in threadpool
@router.get("/report")
def build_report() -> Report:
    return blocking_lib.render()
```

**Default to `def` when uncertain.** Blocking calls inside `async def` damage throughput. The
same rule applies to dependencies.

## Request/response model rules

These models are Pydantic `BaseModel`s. Keep them shaped, not clever.

```python
import pydantic

# Good
class ItemIn(pydantic.BaseModel):
    name: str
    price: float = pydantic.Field(gt=0)

# Bad — `...` is noise
class ItemIn(pydantic.BaseModel):
    name: str = ...
    price: float = pydantic.Field(..., gt=0)
```

For a bare list body, annotate it inline rather than reaching for `RootModel`:

```python
@router.post("/items")
async def create_items(
    items: typing.Annotated[list[int], pydantic.Field(min_length=1), fastapi.Body()],
) -> list[int]:
    return items
```

## Router aggregation

A versioned parent router includes each domain router; the app includes the parent. See
`fastapi-module-structure` for the full two-level layout.

```python
# api/v1/__init__.py
from fastapi import APIRouter
from myapp.api.v1 import health, predictions

router = APIRouter(prefix="/v1")
router.include_router(health.router)
router.include_router(predictions.router)
__all__ = ["router"]
```

## Rules

- MUST set `prefix`/`tags` on `APIRouter`, never on `include_router`.
- MUST use `typing.Annotated[..., fastapi.Path()/Query()/Header()/Body()]` for every parameter.
- MUST declare a return type on every operation; use `response_model` only when the returned
  value differs from the serialized shape.
- One HTTP method per function — no `api_route` + method branching.
- Do NOT use `...` as a default for required fields or parameters.
- Do NOT use `RootModel`, `ORJSONResponse`, or `UJSONResponse` — return types handle fast
  serialization.
- Prefer `def` over `async def` for blocking code or when unsure.
- Keep operations thin; delegate logic to a service (see `fastapi-module-structure`).
